import math
import random

import svgwrite
from svgwrite.extensions import Inkscape

page_width = 800
page_height = 800
circle_radius = 300


def in_circle(radius, pt):
    cx, cy = (page_width / 2, page_width / 2)
    x, y = pt
    d = distance4(cx, cy, x, y)
    return d < radius


def distance4(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def distance(p1, p2):
    return distance4(p1[0], p1[1], p2[0], p2[1])


def mid_point(p1, p2):
    return (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2


def make_lines(layer, drawing: svgwrite.Drawing, inpts):
    usage = {k: 0 for k in inpts}
    conn = 9
    preferred_dist = 5
    used_pairs = set([])
    inpts.sort(key=lambda x: distance((page_width / 2, page_height / 2), x))
    while len([True for k in inpts if usage[k] < conn]) > 1:
        available = [k for k in inpts if usage[k] < conn]
        startpt = available[0]
        endpts = [k for k in available if k != startpt and (startpt, k) not in used_pairs and k[0] != startpt[0] and k[1] != startpt[1]]
        if len(endpts) == 0:
            usage[startpt] += 1
            continue
        endpt = min(endpts, key=lambda x: abs(preferred_dist - distance(x, startpt)))
        usage[startpt] += 1
        usage[endpt] += 1
        preferred_dist = preferred_dist
        used_pairs.add((endpt, startpt))
        used_pairs.add((startpt, endpt))
        if distance(startpt, endpt) < 100:
            layer.add(drawing.line(
                startpt,
                endpt,
                stroke=svgwrite.rgb(10, 10, 16, '%'),
                stroke_width=5,
                stroke_linecap='round',
                stroke_opacity=1.0
            ))


def make_lines2(layer, drawing: svgwrite.Drawing, inpts):
    tail = inpts

    while len(tail) > 1:
        head, *tail = tail

        minpt = min(tail, key=lambda x: distance(x, head))
        if not in_circle(circle_radius, mid_point(head, minpt)) and distance(minpt, head) < 15:
            layer.add(drawing.line(
                head,
                minpt,
                stroke=svgwrite.rgb(255, 10, 16, '%'),
                stroke_width=8,
                stroke_linecap='round'
            ))


def main():
    drawing = svgwrite.Drawing(filename='montecarlo1.svg', size=(page_width, page_height))
    inkscape = Inkscape(drawing)
    inpts = []
    outpts = []

    for i in range(75):
        for j in range(75):
            pt = (i / 75.0 * page_width, j / 75.0 * page_height)
            inside = in_circle(circle_radius, pt)
            if inside:
                while 1:
                    r = (random.random() * page_width, random.random() * page_height)
                    if in_circle(circle_radius, r):
                        break
                inpts.append(r)
            else:
                outpts.append(pt)

    random.shuffle(inpts)
    random.shuffle(outpts)

    # inpts.sort(key=lambda x: -distance((page_width/2, page_height/2), x))
    # outpts.sort(key=lambda x: distance((page_width/2, page_height/2), x))
    in_layer = inkscape.layer(label='inside circle')
    out_layer = inkscape.layer(label='outside circle')

    drawing.add(in_layer)
    drawing.add(out_layer)

    make_lines(in_layer, drawing, inpts)
    make_lines2(out_layer, drawing, outpts)
    drawing.save()


if __name__ == "__main__":
    main()
