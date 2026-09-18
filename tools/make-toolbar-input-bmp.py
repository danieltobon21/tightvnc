#!/usr/bin/env python3
"""
TobonVNC fork: generate res/toolbar_input.bmp.

Two 16x16 images in one 32x16 4bpp bitmap, using the same 16-colour palette as
res/toolbar.bmp (colour 8 = (192,192,192) is the transparency key used by the
common controls toolbar):

  image 0: closed padlock with a red keyhole  -> remote input BLOCKED
  image 1: open padlock with a green keyhole  -> remote input ENABLED

Written by hand (no image library needed) so the bit depth and the palette are
exactly what the toolbar control expects.
"""
import os
import struct

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, "tvnviewer", "res", "toolbar_input.bmp")

# VGA-like palette of the original toolbar.bmp
PALETTE = [
    (0, 0, 0), (128, 0, 0), (0, 128, 0), (128, 128, 0),
    (0, 0, 128), (128, 0, 128), (0, 128, 128), (128, 128, 128),
    (192, 192, 192), (255, 0, 0), (0, 255, 0), (255, 255, 0),
    (0, 0, 255), (255, 0, 255), (0, 255, 255), (255, 255, 255),
]

BG = 8    # background / transparent colour
BLACK = 0
WHITE = 15
RED = 9
GREEN = 10

LOCKED = [
    "................",
    "......0000......",
    ".....00..00.....",
    ".....0....0.....",
    ".....0....0.....",
    ".....0....0.....",
    "..000000000000..",
    "..0FFFFFFFFFF0..",
    "..0FFFFFFFFFF0..",
    "..0FFFFAAFFFF0..",
    "..0FFFFAFFFFF0..",
    "..0FFFFAFFFFF0..",
    "..0FFFFAAFFFF0..",
    "..0FFFFFFFFFF0..",
    "..000000000000..",
    "................",
]

UNLOCKED = [
    "................",
    ".........0000...",
    "........00..00..",
    "........0....0..",
    "........0....00.",
    "........0.......",
    "..000000000000..",
    "..0FFFFFFFFFF0..",
    "..0FFFFFFFFFF0..",
    "..0FFFFBBFFFF0..",
    "..0FFFFBFFFFF0..",
    "..0FFFFBFFFFF0..",
    "..0FFFFBBFFFF0..",
    "..0FFFFFFFFFF0..",
    "..000000000000..",
    "................",
]

DIGITS = {'.': BG, '0': BLACK, 'F': WHITE, 'A': RED, 'B': GREEN}


def build_image(art):
    assert len(art) == 16, "each image must have 16 rows"
    rows = []
    for line in art:
        assert len(line) == 16, "each image row must have 16 pixels: %r" % line
        rows.append([DIGITS[c] for c in line])
    return rows


def write_bmp(path, images):
    width = 16 * len(images)
    height = 16
    row_bytes = ((width * 4 + 31) // 32) * 4
    pixel_data = bytearray()

    # BMP rows are stored bottom-up
    for y in range(height - 1, -1, -1):
        row = bytearray(row_bytes)
        for img_index, img in enumerate(images):
            for x in range(16):
                value = img[y][x]
                pos = img_index * 16 + x
                byte = pos // 2
                if pos % 2 == 0:
                    row[byte] |= (value & 0x0F) << 4
                else:
                    row[byte] |= (value & 0x0F)
        pixel_data += row

    file_header = struct.pack("<2sIHHI", b"BM", 14 + 40 + 4 * 16 + len(pixel_data), 0, 0,
                              14 + 40 + 4 * 16)
    info_header = struct.pack("<IiiHHIIiiII", 40, width, height, 1, 4, 0,
                              len(pixel_data), 2834, 2834, 16, 0)
    palette = b"".join(struct.pack("<BBBB", b, g, r, 0) for (r, g, b) in PALETTE)

    with open(path, "wb") as f:
        f.write(file_header)
        f.write(info_header)
        f.write(palette)
        f.write(bytes(pixel_data))


def main():
    write_bmp(OUT, [build_image(LOCKED), build_image(UNLOCKED)])
    print("wrote %s (%d bytes)" % (os.path.relpath(OUT, REPO), os.path.getsize(OUT)))


if __name__ == "__main__":
    main()