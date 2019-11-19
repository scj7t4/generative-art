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
from stopwatch import Stopwatch
from svgwrite.extensions import Inkscape

THREAD_POOL = ProcessPoolExecutor(max_workers=4)

PAPER_WIDTH = 25
PAPER_HEIGHT = 25
VECTOR_MANHATTAN_MAX = 5

COLORS = [
    (255, 255, 255),
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

MAX_INITIAL_GENES = 1


def open_as_array(fname):
    i = Image.open(fname).convert('RGB')
    return numpy.asarray(i)


TARGET_ARRAY = [open_as_array('chunks/bobross-{}.png'.format(i)) for i in range(374)]


def population_size(gen):
    return 10


def allowed_to_recombine(gen):
    return 10


def parent_tournament_size(gen):
    return 4


def mutation_rate(gen):
    return 0.05


def k_crossover(k, sequence1, sequence2):
    if k == 0:
        return sequence1, sequence2

    split_s1 = random.randint(0, len(sequence1))
    split_s2 = random.randint(0, len(sequence2))

    p0, p1 = sequence1[0:split_s1], sequence1[split_s1:]
    q0, q1 = sequence2[0:split_s2], sequence2[split_s2:]

    return k_crossover(k - 1, p0 + q1, q0 + p1)


def mutate(sequence):
    res = sequence[:]
    types = ['REPLACE', 'DELETE', 'ADD']
    action = random.choice(types)
    idx = random.randint(0, len(sequence))

    if action == 'REPLACE' and idx < len(res):
        res[idx] = Allele()
    elif action == 'DELETE' and idx < len(res):
        res.pop(idx)
    else:
        res.insert(idx, Allele())
    return res


def k_tournament_selection(candidates, k):
    tournament = random.sample(candidates, k)
    return max(tournament, key=lambda x: x.fitness)


def roulette_selection(candidates):
    return random.choices(candidates, [min(0.0, x.fitness) for x in candidates])


def top_k_selection(candidates, k):
    return heapq.nlargest(k, candidates, key=lambda x: x.fitness)


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

    def __init__(self):
        self.start = (random.randint(0, PAPER_WIDTH - 1), random.randint(0, PAPER_HEIGHT - 1))
        ex = max(min(PAPER_WIDTH - 1, self.start[0] + random.randint(-VECTOR_MANHATTAN_MAX, VECTOR_MANHATTAN_MAX)), 0)
        ey = max(min(PAPER_HEIGHT - 1, self.start[1] + random.randint(-VECTOR_MANHATTAN_MAX, VECTOR_MANHATTAN_MAX)), 0)
        self.end = (ex, ey)

    def allele_pts(self):
        return set(pts_recursive(self.start, self.end))


def to_lab_color(c1):
    color1_rgb = sRGBColor(c1[0], c1[1], c1[2], True)
    return convert_color(color1_rgb, LabColor)


def color_distance(c1, c2):
    # Find the color difference
    return delta_e_cie2000(c1, c2)


def compute_fitness(representation, chunk):
    sw = Stopwatch()
    sw.start()
    score = 0
    gene_ct = 0
    covered_pts = set([])
    for color in representation.keys():
        lab_c1 = to_lab_color(color)
        sw2 = Stopwatch()

        sw2.start()
        for allele in representation[color]:
            gene_ct += 1
            pts = allele.allele_pts()
            for pt in pts:
                pt_color = to_lab_color(TARGET_ARRAY[chunk][pt[0], pt[1]])
                dist = color_distance(lab_c1, pt_color)
                # print("pt {} draw {} dist {}".format(color, pt_color, dist))
                score += 50 - dist
                if pt in covered_pts:
                    score -= 1000
                covered_pts.add(pt)
        # print("color {}".format(sw2.reset()))
    # score -= gene_ct ** 2
    score -= (PAPER_WIDTH * PAPER_HEIGHT - len(covered_pts))
    #print("fitness in {}".format(sw.reset()))
    if gene_ct > 0:
        return score
    return -1e128


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


def chunk_position(chunk_num):
    return (chunk_num // 22) * 25, (chunk_num % 22) * 25


class MockFuture:
    def __init__(self, res):
        self.res = res

    def result(self):
        return self.res


class Unit:
    representation = {}
    _fitness = None
    chunk = None

    def __init__(self, chunk, representation=None):
        self.chunk = chunk
        if representation is None:
            self.representation = {color: [Allele() for _ in range(random.randint(0, MAX_INITIAL_GENES))] for color in
                                   COLORS}
        else:
            self.representation = representation
        # self._fitness = MockFuture(compute_fitness(self.representation, self.chunk))
        self._fitness = THREAD_POOL.submit(compute_fitness, self.representation, self.chunk)

    def recombine(self, other):
        a_dict = {}
        b_dict = {}
        crossovers = random.randint(1, 4)
        for color in self.representation.keys():
            a_dict[color], b_dict[color] = k_crossover(crossovers, self.representation[color],
                                                       other.representation[color])
            a_dict[color] = list(set(a_dict[color]))
            b_dict[color] = list(set(b_dict[color]))
        return Unit(self.chunk, a_dict), Unit(self.chunk, b_dict)

    def mutate(self):
        mutated = {}
        for color in self.representation.keys():
            mutated[color] = mutate(self.representation[color])
        return Unit(self.chunk, mutated)

    @property
    def fitness(self):
        return self._fitness.result()

    def __str__(self):
        all_alleles = 0
        for color in self.representation.keys():
            all_alleles += len(self.representation[color])
        return "{} Genes, {} Fitness".format(all_alleles, self.fitness)

    def __repr__(self):
        return self.__str__()

    def to_svg(self):
        return unit_to_svg(self.representation)

    def add_to_drawing(self, drawing, inkscape, layers):
        chunk_pos = chunk_position(self.chunk)
        return add_to_drawing(drawing, inkscape, layers, self.representation, offset=chunk_pos)


def survivor_selection(pool_size, pool):
    return top_k_selection(pool, pool_size)


class Population:
    pool = []
    generation = 0
    chunk = 0

    def __init__(self, chunk, generation=0, pool=None):
        self.chunk = chunk
        self.generation = generation
        pool_size = population_size(self.generation)
        if pool is None:
            print("Generating Population {}...".format(chunk))
            self.pool = [Unit(self.chunk) for _ in range(pool_size)]
        else:
            print("Survivor Selection {}...".format(chunk))
            self.pool = survivor_selection(pool_size, pool)

    def next_generation(self):
        next_pool = self.pool[:]
        k = parent_tournament_size(self.generation)
        for _ in range(allowed_to_recombine(self.generation)):
            p1 = k_tournament_selection(self.pool, k)
            p2 = k_tournament_selection(self.pool, k)
            c1, c2 = p1.recombine(p2)
            next_pool.append(c1)
            next_pool.append(c2)

        rate = mutation_rate(self.generation)
        for u in self.pool:
            roll = random.random()
            if roll <= rate:
                next_pool.append(u.mutate())

        return Population(self.chunk, generation=self.generation + 1, pool=next_pool)

    def __str__(self):
        return "Generation {} (Chunk #{}) [ Best {} ]".format(self.generation, self.chunk,
                                                              max(self.pool, key=lambda x: x.fitness))

    def __repr__(self):
        return self.__str__()

    def add_best_to_drawing(self, drawing, inkscape, layers):
        best = max(self.pool, key=lambda x: x.fitness)
        best.add_to_drawing(drawing, inkscape, layers)


def main():
    sw = Stopwatch()
    sw.start()
    try:
        os.makedirs("./tmp", exist_ok=True)
        pops = [Population(i) for i in range(374)]
        print("Gen 0 took {} to init".format(sw.reset()))
        for i in range(100):
            print(pops)

            drawing = svgwrite.Drawing(size=(550, 425), filename='tmp/gen-{}.svg'.format(i))
            inkscape = Inkscape(drawing)
            layers = {}
            [pop.add_best_to_drawing(drawing, inkscape, layers) for pop in pops]
            drawing.save(pretty=True, indent=2)

            pops = [pop.next_generation() for pop in pops]
            print("Next gen took {}".format(sw.reset()))
    finally:
        THREAD_POOL.shutdown()


if __name__ == "__main__":
    main()
