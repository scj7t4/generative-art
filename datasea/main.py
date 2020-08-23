import cmath
import math

import svgwrite
from svgwrite.extensions import Inkscape


def quadratic_eq(a, b, c):
    v1_n = -b + cmath.sqrt(b ** 2 - 4 * a * c)
    v2_n = -b - cmath.sqrt(b ** 2 - 4 * a * c)
    d = 2 * a
    return [v1_n / d, v2_n / d]


def real_nums(nums):
    return [x.real for x in nums if (x + 0j).imag == 0]


def mid_pt(start, end):
    sx, sy = start
    ex, ey = end
    return sx + (ex - sx) / 2, sy + (ey - sy) / 2


def main():
    drawing = svgwrite.Drawing(size=(1056, 816), filename='grid.svg')
    inkscape = Inkscape(drawing)
    layer = inkscape.layer("0 main")
    cns = inkscape.layer("999 construction")
    # layer.add(drawing.line(start_pt, end_pt, stroke_width=1, stroke=svgwrite.rgb(0, 0, 0)))

    center_pt = 400, 400

    def rel_pt(pt):
        x, y = pt
        return x + center_pt[0], y + center_pt[1]

    out_circle_rad = 150

    d = drawing.circle(center=center_pt, r=out_circle_rad, stroke_width=1, stroke=svgwrite.rgb(0, 0, 0), fill='none')
    layer.add(d)

    inner_circles_rad = [150 - (20 * i) for i in range(1, 7)]
    circle_arm = (-3/4) * math.pi

    cumu = -out_circle_rad

    for c, icr in enumerate(inner_circles_rad):
        m = 4
        if c % 2 == 0:
            m = -4

        cumu -= icr * m
        cy = math.sin(circle_arm) * (cumu)
        cx = math.cos(circle_arm) * (cumu)
        center = rel_pt((cx, cy))
        c = drawing.circle(center=center, r=icr, stroke_width=1, stroke=svgwrite.rgb(0, 0, 0),
                           fill='none')
        layer.add(c)

        cns.add(drawing.line(center_pt, center, stroke_width=1, stroke=svgwrite.rgb(0, 0, 255)))

        # Calculate a line perpindicular to the ray that this inner circle is on
        perp_rad = circle_arm - 1 * math.pi/2
        run = math.cos(perp_rad)
        rise = math.sin(perp_rad)
        ie_x = run * icr + center[0]
        ie_y = rise * icr + center[1]

        cns.add(drawing.line(center, (ie_x, ie_y), stroke_width=1, stroke=svgwrite.rgb(0, 0, 255)))
        cns.add(drawing.circle((ie_x, ie_y), r=5, stroke_width=1, stroke=svgwrite.rgb(0, 0, 255), fill='none'))

        # x^2 + y^2 = (out_circle_rad)^2
        # -(rise / run) x + q = y
        # -(rise / run) (ie_x) + q = (ie_y)
        perp_rad = perp_rad - math.pi / 2
        run = math.cos(perp_rad)
        rise = math.sin(perp_rad)
        slope = rise / run
        q = ie_y - slope * ie_x

        t1 = (ie_x, slope * ie_x + q)
        t2 = (ie_x + 10, slope * (ie_x + 10) + q)
        cns.add(drawing.line(t1, t2, stroke_width=1, stroke=svgwrite.rgb(0, 0, 255)))

        q = (ie_y - center[1]) - slope * (ie_x - center[0])

        a = (slope ** 2 + 1)
        b = 2 * q * slope
        c = q ** 2 - out_circle_rad ** 2

        for x in real_nums(quadratic_eq(a, b, c)):
            y = math.sqrt(out_circle_rad ** 2 - x ** 2) + center_pt[1]
            x += center_pt[0]
            delta = abs(slope * x + q - y)
            print(delta)
            if delta < 1:
                break
        print(x, y)

        mx, my = mid_pt((ie_x, ie_y), (x, y))
        cns.add(drawing.circle((mx, my), r=5, stroke_width=1, stroke=svgwrite.rgb(0, 0, 255), fill='none'))

        ln = drawing.line((ie_x, ie_y), (x, y), stroke_width=1, stroke=svgwrite.rgb(0, 0, 0))
        layer.add(ln)

        # Now draw a vertical line to the edge of the circle
        dy = y - center_pt[1]
        uy = center_pt[1] - dy
        ln = drawing.line((x, y), (x, uy), stroke_width=1, stroke=svgwrite.rgb(0, 0, 0))
        layer.add(ln)

        #cumu -= icr * m

    drawing.add(layer)
    drawing.add(cns)
    drawing.save(pretty=True, indent=2)


if __name__ == "__main__":
    main()
