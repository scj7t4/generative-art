import svgwrite
from svgwrite import mm

page_width = 200 * mm
page_height = 200 * mm


def main():
    drawing = svgwrite.Drawing(filename='tower.svg', size=(page_width, page_height))

    drawing.add(drawing.circle(
        (100 * mm, 100 * mm),
        r=30 * mm,
        stroke=svgwrite.rgb(255, 255, 255, '%'),
        stroke_width=1 * mm))
    drawing.add(drawing.circle(
        (100 * mm, 70 * mm),
        r=15 * mm,
        stroke=svgwrite.rgb(255, 255, 255, '%'),
        stroke_width=1 * mm))
    drawing.add(drawing.circle(
        (100 * mm, 45 * mm),
        r=7.5 * mm,
        stroke=svgwrite.rgb(255, 255, 255, '%'),
        stroke_width=1*mm))
    drawing.save()


if __name__ == "__main__":
    main()
