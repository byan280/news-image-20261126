"""One image that sums up the world news of Thursday 26 November 2026.

The program renders a 1600x900 PNG news poster using only the Python
standard library: a built-in 5x7 bitmap font, a hand-written PNG encoder,
and fixed story data chosen from the day's reporting. No network, no
clock, no randomness and no third-party packages, so two runs produce
byte-identical output. The image is written to MAKEFUN_OUTPUT_DIR (or a
local ./output directory when the variable is not set).
"""

import binascii
import hashlib
import os
import struct
import sys
import zlib

WIDTH = 1600
HEIGHT = 900
OUTPUT_NAME = "news-image-20261126.png"

NAVY_TOP = (16, 35, 59)
NAVY_BOTTOM = (8, 19, 34)
PANEL = (248, 247, 243)
PANEL_EDGE = (219, 216, 208)
INK = (14, 27, 46)
GOLD = (245, 179, 1)
WHITE = (255, 255, 255)
MUTED = (122, 133, 150)
FAINT = (168, 178, 192)

# 5x7 bitmap font. Each glyph is seven rows of five bits, "1" set, "0" clear.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11100", "10010", "10001", "10001", "10001", "10010", "11100"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "*": ("00000", "10101", "01110", "11111", "01110", "10101", "00000"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "01010", "00000", "00000", "00000", "00000"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "@": ("01110", "10001", "10111", "10101", "10110", "10000", "01110"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
    "<": ("00010", "00100", "01000", "10000", "01000", "00100", "00010"),
    ">": ("01000", "00100", "00010", "00001", "00010", "00100", "01000"),
}


def text_width(text, scale):
    if not text:
        return 0
    return len(text) * 6 * scale - scale


def draw_text(canvas, text, x, y, scale, color):
    cursor = x
    for ch in text:
        rows = FONT.get(ch.upper(), FONT["?"])
        for row_index, row in enumerate(rows):
            for col_index, bit in enumerate(row):
                if bit == "1":
                    canvas.fill_rect(
                        cursor + col_index * scale,
                        y + row_index * scale,
                        scale,
                        scale,
                        color,
                    )
        cursor += 6 * scale
    return cursor


def draw_centered(canvas, text, y, scale, color):
    draw_text(canvas, text, (WIDTH - text_width(text, scale)) // 2, y, scale, color)


def wrap_text(text, max_width, scale):
    lines = []
    current = ""
    for word in text.split(" "):
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width or not current:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


class Canvas:
    """An RGB canvas backed by one bytearray, filled row by row."""

    def __init__(self, width, height, top, bottom):
        self.width = width
        self.height = height
        self.pixels = bytearray(width * height * 3)
        for y in range(height):
            t = y / max(1, height - 1)
            red = round(top[0] + (bottom[0] - top[0]) * t)
            green = round(top[1] + (bottom[1] - top[1]) * t)
            blue = round(top[2] + (bottom[2] - top[2]) * t)
            row = bytes((red, green, blue)) * width
            start = y * width * 3
            self.pixels[start:start + width * 3] = row

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.width, x + w)
        y1 = min(self.height, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            start = (yy * self.width + x0) * 3
            self.pixels[start:start + len(row)] = row

    def fill_disc(self, cx, cy, radius, color):
        for dy in range(-radius, radius + 1):
            dx = int((radius * radius - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def frame_rect(self, x, y, w, h, thickness, color):
        self.fill_rect(x, y, w, thickness, color)
        self.fill_rect(x, y + h - thickness, w, thickness, color)
        self.fill_rect(x, y, thickness, h, color)
        self.fill_rect(x + w - thickness, y, thickness, h, color)


def encode_png(width, height, rgb):
    """Encode RGB bytes as a PNG (8-bit, colour type 2, fixed settings)."""
    raw = bytearray()
    stride = width * 3
    for y in range(height):
        raw.append(0)
        raw += rgb[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        out = struct.pack(">I", len(data)) + tag + data
        return out + struct.pack(">I", binascii.crc32(tag + data) & 0xFFFFFFFF)

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


# Six stories from Thursday 26 November 2026, each corroborated by
# reporting dated that day (BBC, Dow Jones, France 24, The Hindu,
# 10 Things, Open Chronicle). Text is uppercase: the built-in font
# covers capitals, digits and common punctuation.
STORIES = [
    {
        "kicker": "TRADE",
        "color": (29, 111, 184),
        "headline": "US PROPOSES NEW TARIFFS ON 14 ECONOMIES",
        "body": "Up to 20% duties on the EU, China and India. Hearing in January.",
        "source": "BBC / DOW JONES",
    },
    {
        "kicker": "EGYPT",
        "color": (196, 62, 48),
        "headline": "FUEL TANKER FIRE KILLS 31 NEAR CAIRO",
        "body": "Ring Road fire destroys 27 vehicles; driver held.",
        "source": "BBC / 10 THINGS",
    },
    {
        "kicker": "SPACE",
        "color": (46, 125, 91),
        "headline": "SPACEX CLEARED FOR 1 MILLION SATELLITES",
        "body": "Approval covers orbital data centres in the largest plan yet.",
        "source": "DOW JONES / FRANCE 24",
    },
    {
        "kicker": "ASIA",
        "color": (122, 79, 163),
        "headline": "NORTH KOREA TO WIDEN NUCLEAR DEPLOYMENT",
        "body": "Kim Jong Un signals more tactical nuclear weapons, alarming Asia.",
        "source": "OPEN CHRONICLE",
    },
    {
        "kicker": "UKRAINE",
        "color": (179, 103, 0),
        "headline": "UKRAINE HITS TWO RUSSIAN REFINERIES",
        "body": "Two Samara refineries hit as Moscow approves record war budget.",
        "source": "10 THINGS",
    },
    {
        "kicker": "HEALTH",
        "color": (14, 124, 134),
        "headline": "CHEAPER HIV PREVENTION JAB REACHES AFRICA",
        "body": "First generic twice-yearly lenacapavir shipments arrive in Zambia.",
        "source": "BBC / IQMIA",
    },
]


def draw_masthead(canvas):
    canvas.fill_rect(0, 0, WIDTH, 10, GOLD)
    kicker = "THE WORLD IN ONE IMAGE"
    draw_centered(canvas, kicker, 34, 3, GOLD)
    half = text_width(kicker, 3) // 2
    canvas.fill_disc(WIDTH // 2 - half - 30, 44, 6, GOLD)
    canvas.fill_disc(WIDTH // 2 + half + 30, 44, 6, GOLD)
    canvas.fill_rect(48, 168, WIDTH - 96, 2, FAINT)
    draw_centered(canvas, "26 NOVEMBER 2026", 66, 9, WHITE)
    draw_centered(canvas, "THURSDAY - SIX STORIES FROM AROUND THE GLOBE", 142, 3, FAINT)
    canvas.fill_rect(48, 176, WIDTH - 96, 3, GOLD)


def draw_panels(canvas):
    margin = 48
    gap = 24
    panel_w = (WIDTH - 2 * margin - gap) // 2
    panel_h = 208
    top = 196
    for index, story in enumerate(STORIES):
        col = index % 2
        row = index // 2
        px = margin + col * (panel_w + gap)
        py = top + row * (panel_h + 18)
        draw_panel(canvas, px, py, panel_w, panel_h, story, index)


def draw_panel(canvas, px, py, panel_w, panel_h, story, index):
    canvas.fill_rect(px, py, panel_w, panel_h, PANEL)
    canvas.frame_rect(px, py, panel_w, panel_h, 1, PANEL_EDGE)
    canvas.fill_rect(px, py, 8, panel_h, story["color"])
    tag = story["kicker"]
    tag_w = text_width(tag, 2) + 16
    canvas.fill_rect(px + 24, py + 16, tag_w, 24, story["color"])
    draw_text(canvas, tag, px + 32, py + 20, 2, WHITE)
    number = "%02d" % (index + 1)
    draw_text(
        canvas,
        number,
        px + panel_w - 24 - text_width(number, 3),
        py + 18,
        3,
        FAINT,
    )
    lines = wrap_text(story["headline"], panel_w - 48, 4)[:2]
    for i, line in enumerate(lines):
        draw_text(canvas, line, px + 24, py + 52 + i * 34, 4, INK)
    body = wrap_text(story["body"], panel_w - 48, 3)[:2]
    for i, line in enumerate(body):
        draw_text(canvas, line, px + 24, py + 126 + i * 25, 3, INK)
    draw_text(canvas, story["source"], px + 24, py + 182, 2, MUTED)


def draw_footer(canvas):
    draw_centered(
        canvas,
        "RENDERED BY CODE - NO PHOTOGRAPHS - SOURCES: BBC, DOW JONES, FRANCE 24, THE HINDU, 10 THINGS, OPEN CHRONICLE",
        868,
        2,
        MUTED,
    )


def render():
    canvas = Canvas(WIDTH, HEIGHT, NAVY_TOP, NAVY_BOTTOM)
    draw_masthead(canvas)
    draw_panels(canvas)
    draw_footer(canvas)
    return encode_png(WIDTH, HEIGHT, canvas.pixels)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or os.path.join(
        os.getcwd(), "output"
    )
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, OUTPUT_NAME)
    png = render()
    with open(path, "wb") as handle:
        handle.write(png)
    digest = hashlib.sha256(png).hexdigest()
    print("WROTE " + OUTPUT_NAME)
    print("SIZE %dx%d" % (WIDTH, HEIGHT))
    print("SHA256 " + digest)
    print("STORIES %d" % len(STORIES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
