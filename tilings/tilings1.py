import math
import random

import svgwrite
from svgwrite.mixins import Transform

page_width = 1100
page_height = 850


def recursive_tiling(ts, dwg, max_depth, prev_tile, depth=1):
    if depth > max_depth:
        return prev_tile

    tx_n90_def = dwg.defs.add(dwg.g(id='t{}_n90'.format(depth)))
    tmp = dwg.use(prev_tile, insert=(0, 0))
    tmp.rotate(90, (ts, ts))
    tmp.scale((-1, -1))
    tmp.translate((-2 * ts, -2 * ts))
    tx_n90_def.add(tmp)

    tx_90_def = dwg.defs.add(dwg.g(id='t{}_90'.format(depth)))
    tmp = dwg.use(prev_tile, insert=(0, 0))
    tmp.rotate(-90, (ts, ts))
    tmp.scale((-1, -1))
    tmp.translate((-2 * ts, -2 * ts))
    tx_90_def.add(tmp)

    next_depth = depth + 1
    tnxt_def = dwg.defs.add(dwg.g(id='t{}'.format(next_depth)))
    tnxt_def.add(dwg.use(prev_tile, insert=(0, 0)))
    tnxt_def.add(dwg.use(prev_tile, insert=(ts, ts)))
    tnxt_def.add(dwg.use(tx_n90_def, insert=(0, ts * 2)))
    tnxt_def.add(dwg.use(tx_90_def, insert=(ts * 2, 0)))
    return recursive_tiling(ts * 2, dwg, max_depth, tnxt_def, next_depth)


def main():
    dwg = svgwrite.Drawing(filename='tilings1.svg', size=(page_width, page_height))
    dwg.add(dwg.rect((0, 0), ('100%', '100%'), fill=svgwrite.rgb(0, 0, 0)))

    ts = 40
    tile_poly = [(0, 0), (ts * 2, 0), (ts * 2, ts), (ts, ts), (ts, ts * 2), (0, ts * 2)]

    tile_clip = dwg.defs.add(dwg.clipPath(id='tile_clip'))
    tile_clip.add(dwg.polygon(tile_poly))

    t1_def = dwg.defs.add(dwg.g(id='t1', clip_path='url(#tile_clip)'))

    t1_def.add(dwg.polygon(tile_poly, fill='#FAF3DD', stroke=svgwrite.rgb(0, 0, 0), stroke_width=2))
    t1_def.add(dwg.polygon([(0, 0), (0.5 * ts, 2 * ts), (2 * ts, 2 * ts), (2 * ts, 0.5 * ts)],
                           fill='#C9D5B9', stroke=svgwrite.rgb(0, 0, 0), stroke_width=2))
    t1_def.add(dwg.polygon([(ts, ts), (0, 0.5 * ts), (0, 0), (0.5 * ts, 0 * ts)],
                           fill='#8FC0A9', stroke=svgwrite.rgb(0, 0, 0), stroke_width=2))
    t1_def.add(dwg.polygon([(2 * ts, 2 * ts), (0.5 * ts, 2 * ts), (0.5 * ts, 0.5 * ts), (2.0 * ts, 0.5 * ts)],
                           fill='#696D7D', stroke=svgwrite.rgb(0, 0, 0), stroke_width=2))
    t1_def.add(dwg.polygon([(0, 2 * ts), (0.5 * ts, 1.5 * ts), (ts, 2.0 * ts)],
                           fill='#68B0AB', stroke=svgwrite.rgb(0, 0, 0), stroke_width=2))
    t1_def.add(dwg.polygon([(2 * ts, 0), (1.5 * ts, 0.5 * ts), (2.0 * ts, ts)],
                           fill='#68B0AB', stroke=svgwrite.rgb(0, 0, 0), stroke_width=2))

    t1_def.add(dwg.polygon(tile_poly, fill='#FAF3DD'))
    t1_def.add(dwg.polygon([(0, 0), (0.5 * ts, 2 * ts), (2 * ts, 2 * ts), (2 * ts, 0.5 * ts)],
                           fill='#C9D5B9'))
    t1_def.add(dwg.polygon([(ts, ts), (0, 0.5 * ts), (0, 0), (0.5 * ts, 0 * ts)],
                           fill='#8FC0A9'))
    t1_def.add(dwg.polygon([(2 * ts, 2 * ts), (0.5 * ts, 2 * ts), (0.5 * ts, 0.5 * ts), (2.0 * ts, 0.5 * ts)],
                           fill='#696D7D'))
    t1_def.add(dwg.polygon([(0, 2 * ts), (0.5 * ts, 1.5 * ts), (ts, 2.0 * ts)],
                           fill='#68B0AB'))
    t1_def.add(dwg.polygon([(2 * ts, 0), (1.5 * ts, 0.5 * ts), (2.0 * ts, ts)],
                           fill='#68B0AB'))

    ft = recursive_tiling(ts, dwg, 5, t1_def)

    dwg.add(dwg.use(ft, insert=(0, 0)))
    dwg.save(pretty=True, indent=2)


if __name__ == "__main__":
    main()
