#!/usr/bin/env python3
"""Generative moire banner for the profile README.

Two fine vertical line gratings with almost equal periods are combined with a
logical AND: white appears only where their lines coincide, so the beat
frequency carves drifting zones of lines out of a black field. Both gratings
drift by an integer number of periods per loop, so the GIF loops seamlessly.

Usage: python3 scripts/banner.py assets/banner.gif
Requires numpy and Pillow.
"""

import sys

import numpy as np
from PIL import Image

W, H = 1600, 260
FRAMES = 96
FPS = 24
SS = 3

P1, P2 = 6.0, 6.18
D1, D2 = 0.42, 0.42
FM_DEPTH, FM_PERIOD = 1.5, 800
DRIFT1, DRIFT2 = 2, 1


def frame(t):
    ys, xs = np.mgrid[0:H * SS, 0:W * SS].astype(np.float32) / SS
    tau = 2 * np.pi
    f1 = xs / P1 + DRIFT1 * t
    f2 = xs / P2 + FM_DEPTH * np.sin(tau * (xs / FM_PERIOD + 2 * t)) - DRIFT2 * t
    g = ((f1 % 1.0) < D1) & ((f2 % 1.0) < D2)
    g = g.reshape(H, SS, W, SS).mean(axis=(1, 3))
    return Image.fromarray(np.where(g >= 0.5, 255, 0).astype(np.uint8), 'L').convert('1')


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else 'assets/banner.gif'
    frames = [frame(i / FRAMES) for i in range(FRAMES)]
    frames[0].save(out, save_all=True, append_images=frames[1:],
                   duration=1000 // FPS, loop=0, optimize=True, disposal=1)
    print(out)


if __name__ == '__main__':
    main()
