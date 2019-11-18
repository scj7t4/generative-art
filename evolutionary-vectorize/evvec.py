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
from stopwatch import Stopwatch
from svgwrite.extensions import Inkscape

THREAD_POOL = ProcessPoolExecutor(max_workers=4)

PAPER_WIDTH = 550
PAPER_HEIGHT = 425
VECTOR_MANHATTAN_MAX = 25

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

MAX_INITIAL_GENES = 2000


def open_as_array(fname):
    i = Image.open(fname).convert('RGB')
    return numpy.asarray(i)


TARGET_ARRAY = open_as_array('bobross.png')


def population_size(gen):
    return 100


def allowed_to_recombine(gen):
    return 100


def parent_tournament_size(gen):
    return 16


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

    if action == 'REPLACE':
        res[idx] = Allele()
    elif action == 'DELETE':
        res.pop(idx)
    else:
        res.insert(idx, Allele())


def k_tournament_selection(candidates, k):
    tournament = random.sample(candidates, k)
    return max(tournament, key=lambda x: x.fitness)


def roulette_selection(candidates):
    return random.choices(candidates, [min(0.0, x.fitness) for x in candidates])


def top_k_selection(candidates, k):
    return heapq.nlargest(k, candidates, key=lambda x: x.fitness)


class Allele:
    color = None
    start = None
    end = None

    def __init__(self):
        self.start = (random.randint(0, PAPER_WIDTH), random.randint(0, PAPER_HEIGHT))
        ex = max(min(PAPER_WIDTH, self.start[0] + random.randint(-VECTOR_MANHATTAN_MAX, VECTOR_MANHATTAN_MAX)), 0)
        ey = max(min(PAPER_HEIGHT, self.start[1] + random.randint(-VECTOR_MANHATTAN_MAX, VECTOR_MANHATTAN_MAX)), 0)
        self.end = (ex, ey)
        self.color = random.choice(COLORS)


def compute_fitness(representation):
    sw = Stopwatch()
    sw.start()
    drawing = unit_to_svg(representation)

    # print("Adding all vectors took {}".format(sw.reset()))

    xml = drawing.tostring()

    # print("To xml took {}".format(sw.reset()))

    image_data = cairosvg.surface.PNGSurface.convert(xml)
    arr = open_as_array(BytesIO(image_data))

    # print("Convert to png took {}".format(sw.reset()))

    diff = numpy.abs(TARGET_ARRAY - arr)
    diff = numpy.reshape(diff, PAPER_WIDTH * PAPER_HEIGHT * 3)
    diff = diff * -1
    # os.remove(fname)
    avg = numpy.average(diff)

    # print("Compute diff took {}".format(sw.reset()))

    return avg


def unit_to_svg(representation):
    drawing = svgwrite.Drawing(size=(PAPER_WIDTH, PAPER_HEIGHT))
    inkscape = Inkscape(drawing)
    layers = {}
    color_counter = 0
    for allele in representation:
        color = allele.color
        if color not in layers:
            layers[color] = inkscape.layer("{}".format(color_counter))
            color_counter += 1
            drawing.add(layers[color])
        layer = layers[allele.color]
        svg_color = svgwrite.rgb(color[0], color[1], color[2])
        layer.add(drawing.line(allele.start, allele.end, stroke_width=5, stroke=svg_color))
    return drawing


class Unit:
    representation = []
    _fitness = None

    def __init__(self, representation=None):
        if representation is None:
            self.representation = [Allele() for _ in range(random.randint(0, 2000))]
        else:
            self.representation = representation
        self.representation.sort(key=lambda x: x.start[0] + x.start[1])
        self._fitness = THREAD_POOL.submit(compute_fitness, self.representation)

    def recombine(self, other):
        crossovers = random.randint(1, 4)
        a, b = k_crossover(crossovers, self.representation, other.representation)
        return Unit(a), Unit(b)

    def mutate(self):
        return Unit(mutate(self.representation))

    @property
    def fitness(self):
        return self._fitness.result()

    def __str__(self):
        return "{} Genes, {} Fitness".format(len(self.representation), self.fitness)

    def to_svg(self):
        return unit_to_svg(self.representation)


def make_unit():
    return Unit()


def survivor_selection(pool_size, pool):
    return top_k_selection(pool, pool_size)


class Population:
    pool = []
    generation = 0

    def __init__(self, generation=0, pool=None):
        self.generation = generation
        pool_size = population_size(self.generation)
        if pool is None:
            print("Generating Population...")
            self.pool = [Unit() for _ in range(pool_size)]
        else:
            print("Survivor Selection...")
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

        return Population(self.generation + 1, next_pool)

    def __str__(self):
        return "Generation {} [ Best {} ]".format(self.generation, max(self.pool, key=lambda x: x.fitness))

    def save_best(self):
        best = max(self.pool, key=lambda x: x.fitness)
        drawing = best.to_svg()
        drawing.saveas('./tmp/gen-{}.svg'.format(self.generation))


def main():
    pass


if __name__ == "__main__":
    sw = Stopwatch()
    sw.start()
    try:
        os.makedirs("./tmp", exist_ok=True)
        pop = Population()
        print("Gen 0 took {} to init".format(sw.reset()))
        for i in range(100):
            print(pop)
            pop.save_best()
            pop = pop.next_generation()
            print("Next gen took {}".format(sw.reset()))
    finally:
        THREAD_POOL.shutdown(wait=False)
