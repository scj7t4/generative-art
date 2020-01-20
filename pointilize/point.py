import math
import random

import svgwrite
from svgwrite.extensions import Inkscape

MAX_SQUARE_SIZE = 50

GRID_WIDTH = 870
GRID_HEIGHT = 695


def distance_fst(pt1, pt2):
    return (pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2


def optimize_lines(lines: list):
    endpt = (0, 0)
    sort_lines = []
    to_sort = lines[:]
    while len(to_sort):
        if len(to_sort) % 100 == 0:
            print("{} to optimize".format(len(to_sort)))
        min_idx = min(range(len(to_sort)), key=lambda x: distance_fst(endpt, to_sort[x][0]))
        to_sort[-1], to_sort[min_idx] = to_sort[min_idx], to_sort[-1]
        closest = to_sort.pop()
        sort_lines.append(closest)
        endpt = closest[1]
    return sort_lines


def optimize_circles(circles: list):
    endpt = (0, 0)
    sort_circles = []
    to_sort = circles[:]
    while len(to_sort):
        if len(to_sort) % 100 == 0:
            print("{} to optimize".format(len(to_sort)))
        min_idx = min(range(len(to_sort)), key=lambda x: distance_fst(endpt, to_sort[x]))
        to_sort[-1], to_sort[min_idx] = to_sort[min_idx], to_sort[-1]
        closest = to_sort.pop()
        sort_circles.append(closest)
        endpt = closest
    return sort_circles


def main():
    grid = {(x, y): None for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)}

    squares_filled = 0
    sq_counter = 0
    iters = 0

    lines = []
    circles = []

    while squares_filled < GRID_WIDTH * GRID_HEIGHT:
        iters += 1

        if iters == 1000000:
            break

        print("iter {} filled {} / {} squares  {}".format(iters, squares_filled, GRID_HEIGHT * GRID_WIDTH, sq_counter))

        size = random.randint(50, 125)
        x1 = random.randint(0, GRID_WIDTH - 1)
        y1 = random.randint(0, GRID_HEIGHT - 1)
        if x1 + size >= GRID_WIDTH or y1 + size >= GRID_HEIGHT:
            continue
        all_free = all(grid[(x1 + x, y1 + y)] is None for x in range(size - 1) for y in range(size - 1))
        if not all_free:
            continue
        squares_filled += size * size
        for x in range(size - 1):
            for y in range(size - 1):
                grid[(x1 + x, y1 + y)] = sq_counter
        sq_counter += 1
        # if x1 == 0:
        #    lines.append(((x1, y1), (x1 + size, y1)))
        # if y1 == 0:
        #    lines.append(((x1, y1), (x1, y1 + size)))
        lines.append(((x1, y1 + size), (x1 + size, y1 + size)))
        lines.append(((x1 + size, y1), (x1 + size, y1 + size)))
        circles.append((x1 + size / 2, y1 + size / 2, size / 2))

    drawing = svgwrite.Drawing(size=(1056, 816), filename='grid.svg')
    inkscape = Inkscape(drawing)
    layer = inkscape.layer("0 squares")
    layer2 = inkscape.layer("1 circles")

    opt = lines
    # opt = optimize_lines(lines)
    offset = (93, 61)

    for line in opt:
        start_pt = line[0][0] + offset[0], line[0][1] + offset[1]
        end_pt = line[1][0] + offset[0], line[1][1] + offset[1]
        layer.add(drawing.line(start_pt, end_pt, stroke_width=1, stroke=svgwrite.rgb(0, 0, 0)))

    circles = optimize_circles(circles)

    for circle in circles:
        layer2.add(
            drawing.circle(center=(circle[0] + offset[0], circle[1] + offset[1]), r=circle[2] - 1, stroke_width=1,
                           stroke=svgwrite.rgb(0, 0, 0), fill='none'))

    # drawing.add(layer)
    drawing.add(layer2)
    drawing.save(pretty=True, indent=2)


if __name__ == "__main__":
    main()
