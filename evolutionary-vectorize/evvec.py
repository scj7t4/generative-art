import heapq
import random
import os
import uuid

import cairosvg
import numpy
import svgwrite
from PIL import Image
from svgwrite.extensions import Inkscape

PAPER_WIDTH = 550
PAPER_HEIGHT = 425
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

MAX_INITIAL_GENES = 2000


def open_as_array(fname):
    i = Image.open(fname)
    return numpy.asarray(i)


TARGET_ARRAY = open_as_array('bobross.png')


def population_size(gen):
    return 4000


def allowed_to_recombine(gen):
    return 200


def parent_tournament_size(gen):
    return 128


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
        ex = max(min(0, self.start[0] + random.randint(-VECTOR_MANHATTAN_MAX, VECTOR_MANHATTAN_MAX)), PAPER_WIDTH)
        ey = max(min(0, self.start[1] + random.randint(-VECTOR_MANHATTAN_MAX, VECTOR_MANHATTAN_MAX)), PAPER_HEIGHT)
        self.end = (ex, ey)
        self.color = random.choice(COLORS)


def compute_fitness(representation):
    drawing = svgwrite.Drawing(size=(PAPER_WIDTH, PAPER_HEIGHT))
    inkscape = Inkscape(drawing)

    layers = {}
    color_counter = 0

    for allele in representation:
        color = allele.color
        if color not in layers:
            layers[color] = inkscape.layer("{}".format(color_counter))
            color_counter += 1
        layer = layers[allele.color]
        svg_color = svgwrite.rgb(color[0], color[1], color[2])
        layer.add(drawing.line(allele.start, allele.end, stroke_width=5, stroke=svg_color))

    xml = drawing.tostring()

    fname = "./temp/" + uuid.uuid4().hex + ".png"
    cairosvg.surface.PNGSurface.convert(xml, write_to=fname)
    arr = open_as_array(fname)

    diff = numpy.abs(TARGET_ARRAY - arr)
    print(diff)
    print(diff.shape)
    diff = numpy.reshape((1, ))

    return numpy.average(diff)


class Unit:
    representation = []
    _fitness = None

    def __init__(self, representation=None):
        if representation is None:
            self.representation = [Allele() for _ in range(random.randint(0, 2000))]
        else:
            self.representation = representation

    def recombine(self, other):
        crossovers = random.randint(1, 4)
        a, b = k_crossover(crossovers, self.representation, other.represenation)
        return Unit(a), Unit(b)

    def mutate(self):
        return Unit(mutate(self.representation))

    @property
    def fitness(self):
        if self._fitness is None:
            self._fitness = compute_fitness(self.representation)

        return self._fitness

    def __str__(self):
        return "{} Genes, {} Fitness".format(len(self.representation), self.fitness)


def survivor_selection(pool_size, pool):
    return top_k_selection(pool, pool_size)


class Population:
    pool = []
    generation = 0

    def __init__(self, generation=0, pool=None):
        self.generation = generation
        pool_size = population_size(self.generation)
        if pool is None:
            self.pool = [Unit() for _ in range(pool_size)]
        else:
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


def main():
    pass


if __name__ == "__main__":
    os.makedirs("./tmp", exist_ok=True)
    compute_fitness([])