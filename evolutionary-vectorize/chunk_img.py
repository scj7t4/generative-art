from math import ceil

from PIL import Image

CHUNK_X = 25
CHUNK_Y = CHUNK_X

if __name__ == '__main__':
    img = Image.open('bobross.png').convert('RGB')
    width = 550
    height = 425
    xs = ceil(width / CHUNK_X)
    ys = ceil(height / CHUNK_Y)

    ctr = 0
    for i in range(xs):
        for j in range(ys):
            c = img.crop((i * CHUNK_X, j * CHUNK_Y, i * CHUNK_X + CHUNK_X, j * CHUNK_Y + CHUNK_Y)).save('bobross-{}.png'.format(ctr))
            ctr += 1
