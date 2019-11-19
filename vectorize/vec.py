import datetime
import heapq
import random
import os
import uuid
from concurrent.futures.process import ProcessPoolExecutor
from concurrent.futures.thread import ThreadPoolExecutor
from io import BytesIO

import cairosvg
import numpy
import svgwrite
from PIL import Image
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie2000
from colormath.color_objects import sRGBColor, LabColor
from svgwrite.extensions import Inkscape

THREAD_POOL = ProcessPoolExecutor(max_workers=4)

PAPER_WIDTH = 425
PAPER_HEIGHT = 550
VECTOR_MANHATTAN_MAX = 10

COLORS = [
    (23, 20, 15),
    (42, 39, 32),
    (31, 64, 99),
    (92, 128, 114),
    (44, 101, 82),
    (90, 127, 76),
    (137, 154, 119),
    (197, 180, 41),
    (164, 83, 36),
    (178, 140, 128),
    (144, 35, 66),
    (109, 48, 30),
    (74, 42, 45),
    (80, 64, 100),
    (36, 29, 19),
    # NEONS:
    (157, 79, 33),
    (116, 134, 48),
    (176, 170, 50),
    (151, 51, 79),
    (90, 114, 143),
]


def open_as_array(fname):
    i = Image.open(fname).convert('RGB')
    return numpy.asarray(i)


TARGET_ARRAY = open_as_array('bobross.png')


def pts_recursive(pt1, pt2):
    mx = round((pt1[0] + pt2[0]) / 2)
    my = round((pt1[1] + pt2[1]) / 2)
    mp = (mx, my)

    if mp == pt1:
        return [pt1]
    if mp == pt2:
        return [pt2]

    return pts_recursive(pt1, mp) + [mp] + pts_recursive(mp, pt2)


class Allele:
    start = None
    end = None
    _pts = []

    def __init__(self):
        self.start = (random.randint(0, PAPER_WIDTH - 1), random.randint(0, PAPER_HEIGHT - 1))
        ex = max(min(PAPER_WIDTH - 1, self.start[0] + random.randint(-VECTOR_MANHATTAN_MAX, VECTOR_MANHATTAN_MAX)), 0)
        ey = max(min(PAPER_HEIGHT - 1, self.start[1] + random.randint(-VECTOR_MANHATTAN_MAX, VECTOR_MANHATTAN_MAX)), 0)
        self.end = (ex, ey)
        self._pts = set(pts_recursive(self.start, self.end))


    @property
    def allele_pts(self):
        return self._pts


def to_lab_color(c1):
    color1_rgb = sRGBColor(c1[0], c1[1], c1[2], True)
    return convert_color(color1_rgb, LabColor)


def color_distance(c1, c2):
    # Find the color difference
    return delta_e_cie2000(c1, c2)


def unit_to_svg(representation):
    drawing = svgwrite.Drawing(size=(PAPER_WIDTH, PAPER_HEIGHT))
    inkscape = Inkscape(drawing)
    layers = {}
    return add_to_drawing(drawing, inkscape, layers, representation)


def add_to_drawing(drawing, inkscape, layers, representation, offset=(0, 0)):
    ox, oy = offset
    color_counter = 0
    for color in representation.keys():
        if color not in layers:
            layers[color] = inkscape.layer("{}".format(color_counter))
            color_counter += 1
            drawing.add(layers[color])
        svg_color = svgwrite.rgb(color[0], color[1], color[2])
        for allele in representation[color]:
            layer = layers[color]
            start_pt = allele.start[0] + ox, allele.start[1] + oy
            end_pt = allele.end[0] + ox, allele.end[1] + oy
            layer.add(drawing.line(start_pt, end_pt, stroke_width=1, stroke=svg_color))
    return drawing


def main():
    miss_cnt = 0
    covered_pts = set([])
    alleles = []
    goal_coverage = PAPER_HEIGHT * PAPER_WIDTH * 0.25
    while len(covered_pts) < goal_coverage:
        if len(alleles) % 100 == 0:
            print("Generated {} alleles ({} misses, {}/{} covered)...".format(len(alleles), miss_cnt, len(covered_pts), goal_coverage))

        gen = Allele()
        if any([pt in covered_pts for pt in gen.allele_pts]):
            miss_cnt += 1
            continue
        covered_pts |= set(gen.allele_pts)
        alleles.append(gen)

    print("Generated {} alleles".format(len(alleles)))

    rep = {}
    for color in COLORS:
        rep[color] = []

    processed = 0
    for allele in alleles:
        if processed % 100 == 0:
            print("Colored {} alleles...".format(processed))
        pts = allele.allele_pts
        colors = [to_lab_color(TARGET_ARRAY[pt]) for pt in pts]
        color_dists = {}
        for color in COLORS:
            lab_color = to_lab_color(color)
            distance = sum([color_distance(lab_color, pt_color) for pt_color in colors]) * random.gauss(1.0, 0.1)
            color_dists[color] = distance
        best_color = min(COLORS, key=lambda x: color_dists[x])
        rep[best_color].append(allele)
        processed += 1

    drawing = svgwrite.Drawing(size=(870, 695), filename='generated.svg')
    inkscape = Inkscape(drawing)
    layers = {}
    scale = 1.58096

    for color in rep:
        alleles = rep[color]
        for allele in alleles:
            allele.start = allele.start[0] * scale, allele.start[1] * scale
            allele.end = allele.end[0] * scale, allele.end[1] * scale

    add_to_drawing(drawing, inkscape, layers, rep, offset=(93, 61))
    drawing.save()


if __name__ == "__main__":
    main()
