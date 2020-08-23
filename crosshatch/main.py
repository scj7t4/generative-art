import numpy
import svgwrite
from PIL import Image
from svgwrite.extensions import Inkscape


def open_as_array(fname):
    i = Image.open(fname).convert('L')
    return numpy.asarray(i)


def cross(x, y, level):
    (left, top) = x * 7, y * 7
    out = []

    if level >= 5 or level < 0:
        return []
    if 5 > level >= 4 and x % 2 == y % 2:
        out.append(((3, 1), (3, 5)))
    elif 5 > level >= 4:
        out.append(((1, 3), (5, 3)))
    if 4 > level >= 3 and x % 2 == y % 2:
        out.append(((2, 1), (2, 5)))
        out.append(((4, 1), (4, 5)))
    elif 4 > level >= 3:
        out.append(((1, 2), (5, 2)))
        out.append(((1, 4), (5, 4)))
    if 3 > level >= 2 and x % 2 == y % 2:
        out.append(((1, 1), (1, 5)))
        out.append(((3, 1), (3, 5)))
        out.append(((5, 1), (5, 5)))
    elif 3 > level >= 2:
        out.append(((1, 1), (5, 1)))
        out.append(((1, 3), (5, 3)))
        out.append(((1, 5), (5, 5)))
    if 2 > level >= 1 and x % 2 == y % 2:
        out.append(((1, 1), (1, 5)))
        out.append(((2.333, 1), (2.333, 5)))
        out.append(((3.667, 1), (3.667, 5)))
        out.append(((5, 1), (5, 5)))
    elif 2 > level >= 1:
        out.append(((1, 1), (5, 1)))
        out.append(((1, 2.333), (5, 2.333)))
        out.append(((1, 3.667), (5, 3.667)))
        out.append(((1, 5), (5, 5)))
    if 1 > level >= 0 and x % 2 == y % 2:
        out.append(((1, 1), (1, 5)))
        out.append(((2, 1), (2, 5)))
        out.append(((3, 1), (3, 5)))
        out.append(((4, 1), (4, 5)))
        out.append(((5, 1), (5, 5)))
    elif 1 > level >= 0:
        out.append(((1, 1), (5, 1)))
        out.append(((1, 2), (5, 2)))
        out.append(((1, 3), (5, 3)))
        out.append(((1, 4), (5, 4)))
        out.append(((1, 5), (5, 5)))

    return [((x1 + left, y1 + top), (x2 + left, y2 + top)) for ((x1, y1), (x2, y2)) in out]


def main():
    img = open_as_array('bobross.png')
    img = numpy.where(img == numpy.max(img), -10000000, img)
    img = img / numpy.max(img)
    img *= 10
    img = numpy.round(img)

    (width, height) = img.shape
    print(img)
    print(img.shape)

    drawing = svgwrite.Drawing(filename='cross.svg', size=(width * 7, height * 7))
    inkscape = Inkscape(drawing)

    layer = inkscape.layer(label='drawing')
    drawing.add(layer)

    for x in range(width):
        for y in range(height):
            cell = img[x, y]

            tmp = cell
            if cell >= 5:
                tmp -= 5

            pts = cross(x, y, tmp)
            for (startpt, endpt) in pts:
                layer.add(drawing.line(
                    startpt,
                    endpt,
                    stroke=svgwrite.rgb(0, 0, 0, '%'),
                    stroke_width=1,
                    stroke_linecap='round',
                    stroke_opacity=1.0
                ))

            if 0 <= cell < 5:
                layer.add(drawing.circle(
                    center=(7 * x + 3, 7 * y + 3),
                    r=2.5,
                    stroke=svgwrite.rgb(0, 0, 0, '%'),
                    stroke_width=1,
                    stroke_linecap='round',
                    stroke_opacity=1.0,
                    fill='none'
                ))

    drawing.save()


if __name__ == "__main__":
    main()
