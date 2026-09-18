#!/usr/bin/env python3
"""Genera la tira de iconos de la barra de herramientas de TobonVNC Viewer.

Salida: res/toolbar.bmp — tira de 18 imágenes de 24x24 en 32bpp **con canal alfa**,
en una sola fila (432x24). La carga el visor como ImageList ILC_COLOR32.

Orden de las imágenes (el índice = comando IDS_TB_NEWCONNECTION + i):

    0  New connection (200)      6  Ctrl+Alt+Del (206)     12  Zoom out    (212)
    1  Save session (201)        7  Ctrl+Esc     (207)     13  100 %       (213)
    2  Connection options (202)  8  Ctrl         (208)     14  Fit / auto  (214)
    3  Connection info (203)     9  Alt          (209)     15  Fullscreen  (215)
    4  Pause (204)              10  File transfer(210)     16  Padlock closed (blocked)
    5  Refresh (205)            11  Zoom in      (211)     17  Padlock open   (allowed)

Estilo: el de la familia Tobon (trazos gruesos, esquinas redondeadas), pero en
tinta oscura `#2F3339` sobre transparente porque la barra con tema claro de
Windows 11 es gris claro; el único color es el acento `#FF5A1F`.

Uso:
    python3 tools/make-toolbar-icons.py --out tvnviewer/res/toolbar.bmp
    python3 tools/make-toolbar-icons.py --preview /tmp/toolbar_preview.png
"""
import argparse
import math
from PIL import Image, ImageDraw, ImageFont

S = 24                     # tamaño de cada icono
N = 18                     # imágenes en la tira
SS = 4                     # supersampling
INK = (47, 51, 57)         # #2F3339
ACCENT = (255, 90, 31)     # #FF5A1F
FONT_PATH = '/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf'
W = S * SS                 # lienzo de trabajo


def font(px):
    try:
        return ImageFont.truetype(FONT_PATH, px * SS)
    except Exception:
        return ImageFont.load_default()


def canvas():
    img = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def line(d, pts, w=2.6, color=INK):
    d.line([(x * SS, y * SS) for x, y in pts], fill=color, width=max(1, int(w * SS)), joint='curve')


def circle_outline(d, cx, cy, r, w=2.6, color=INK):
    d.ellipse(((cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS),
              outline=color, width=max(1, int(w * SS)))


def circle_fill(d, cx, cy, r, color=INK):
    d.ellipse(((cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS), fill=color)


def rrect(d, x0, y0, x1, y1, r=3, w=2.6, color=INK, fill=None):
    d.rounded_rectangle((x0 * SS, y0 * SS, x1 * SS, y1 * SS), radius=r * SS,
                        outline=color, width=max(1, int(w * SS)), fill=fill)


def text(d, s, cx, cy, px=11, color=INK, anchor='mm'):
    d.text((cx * SS, cy * SS), s, font=font(px), fill=color, anchor=anchor)


def arc(d, cx, cy, r, start, end, w=2.6, color=INK):
    d.arc(((cx - r) * SS, (cy - r) * SS, (cx + r) * SS, (cy + r) * SS),
          start=start, end=end, fill=color, width=max(1, int(w * SS)))



def cap(d, cx, cy, w=7.0, h=10.0, color=INK, r=1.6, sw=2.2):
    """Tecla centrada en (cx, cy)."""
    rrect(d, cx - w / 2.0, cy - h / 2.0, cx + w / 2.0, cy + h / 2.0, r, w=sw, color=color)


def lens(d, sign=None, color=ACCENT):
    """Lupa con cuadricula fija: lente en (10,10) r=6 y mango a 45 grados."""
    circle_outline(d, 10, 10, 6.0, w=2.6)
    line(d, [(14.4, 14.4), (20.8, 20.8)], w=3.0)
    if sign == '+':
        line(d, [(10, 6.8), (10, 13.2)], w=2.4, color=color)
        line(d, [(6.8, 10), (13.2, 10)], w=2.4, color=color)
    elif sign == '-':
        line(d, [(6.8, 10), (13.2, 10)], w=2.4, color=color)
    elif sign == '1:1':
        text(d, '1:1', 10, 10.1, px=7, color=color)


# ---------------------------------------------------------------- iconos
def g_new_connection(d):
    rrect(d, 2, 4.5, 14.5, 15, 2.5)
    line(d, [(8.2, 15), (8.2, 18.6)]); line(d, [(5.8, 19.2), (10.6, 19.2)])
    # "+" grande en la esquina superior derecha
    line(d, [(18.6, 3.6), (18.6, 12.4)], w=3.0, color=ACCENT)
    line(d, [(14.2, 8), (23, 8)], w=3.0, color=ACCENT)

def g_save(d):
    rrect(d, 3, 3, 21, 21, 3)
    rrect(d, 8, 3, 16, 9, 1.2, w=2.2, fill=(255, 255, 255, 0))
    line(d, [(8, 14), (16, 14)]); line(d, [(8, 17.5), (16, 17.5)])


def g_options(d):
    """Engranaje: anillo grueso + 8 dientes cortos."""
    circle_outline(d, 12, 12, 6.6, w=3.0)
    circle_outline(d, 12, 12, 2.4, w=2.4)
    for i in range(8):
        a = i * math.pi / 4 + math.pi / 8
        x0, y0 = 12 + 6.2 * math.cos(a), 12 + 6.2 * math.sin(a)
        x1, y1 = 12 + 9.4 * math.cos(a), 12 + 9.4 * math.sin(a)
        line(d, [(x0, y0), (x1, y1)], w=4.2)

def g_info(d):
    circle_outline(d, 12, 12, 9)
    circle_fill(d, 12, 7.6, 1.5)
    line(d, [(12, 11), (12, 16.5)], w=2.8)


def g_pause(d):
    d.rounded_rectangle((7 * SS, 5 * SS, 10.6 * SS, 19 * SS), radius=1.2 * SS, fill=INK)
    d.rounded_rectangle((13.4 * SS, 5 * SS, 17 * SS, 19 * SS), radius=1.2 * SS, fill=INK)


def g_refresh(d):
    """Flecha circular: arco amplio con la punta apoyada en su extremo."""
    cx = cy = 12.0
    r = 6.9
    arc(d, cx, cy, r, 55, 335, w=2.8)
    a = math.radians(335)
    px, py = cx + r * math.cos(a), cy + r * math.sin(a)
    tx, ty = -math.sin(a), math.cos(a)          # sentido de giro (horario)
    nx, ny = math.cos(a), math.sin(a)
    L, w2 = 5.2, 4.2
    # la base del triangulo se solapa con el arco para que no parezca un punto suelto
    d.polygon([((px + tx * L) * SS, (py + ty * L) * SS),
               ((px + nx * w2) * SS, (py + ny * w2) * SS),
               ((px - nx * w2) * SS, (py - ny * w2) * SS)], fill=INK)

def g_ctrl_alt_del(d):
    """Tres teclas iguales y alineadas; la del medio en acento = combo de tres."""
    for i, cx in enumerate((3.7, 12.0, 20.3)):
        cap(d, cx, 12, w=6.6, h=11, color=ACCENT if i == 1 else INK)

def g_ctrl_esc(d):
    """Dos teclas iguales y separadas; la segunda en acento."""
    for i, cx in enumerate((6.3, 17.7)):
        cap(d, cx, 12, w=9.0, h=11, color=INK if i == 0 else ACCENT)

def g_ctrl(d):
    """Tecla ancha con el simbolo de Ctrl (^), centrado y con margen interior."""
    cap(d, 12, 12, w=17, h=13.5, r=2.0, sw=2.2)
    line(d, [(12, 8.6), (9.1, 14.4)], w=2.4, color=ACCENT)
    line(d, [(12, 8.6), (14.9, 14.4)], w=2.4, color=ACCENT)

def g_alt(d):
    """Tecla ancha con la letra A (Alt): a 24 px el texto entero no se lee."""
    cap(d, 12, 12, w=17, h=13.5, r=2.0, sw=2.2)
    text(d, 'A', 12, 12.3, px=9.5, color=ACCENT)

def g_transfer(d):
    """Dos bloques alineados con dos flechas finas opuestas (intercambio)."""
    rrect(d, 1.5, 5, 8, 19, 1.8, w=2.2)
    rrect(d, 16, 5, 22.5, 19, 1.8, w=2.2)
    # arriba: hacia la derecha
    line(d, [(9.6, 10), (13.4, 10)], w=1.8, color=ACCENT)
    d.polygon([(14.8 * SS, 10 * SS), (12.4 * SS, 8.5 * SS), (12.4 * SS, 11.5 * SS)], fill=ACCENT)
    # abajo: hacia la izquierda
    line(d, [(14.4, 14), (10.6, 14)], w=1.8, color=ACCENT)
    d.polygon([(9.2 * SS, 14 * SS), (11.6 * SS, 12.5 * SS), (11.6 * SS, 15.5 * SS)], fill=ACCENT)

def g_zoom_in(d):
    lens(d, '+')

def g_zoom_out(d):
    lens(d, '-')

def g_zoom_100(d):
    lens(d, '1:1')

def g_zoom_fit(d):
    """Ajustar a la ventana: corchetes de esquina hacia dentro + punto central."""
    line(d, [(2.5, 8), (2.5, 2.5), (8, 2.5)])
    line(d, [(21.5, 8), (21.5, 2.5), (16, 2.5)])
    line(d, [(2.5, 16), (2.5, 21.5), (8, 21.5)])
    line(d, [(21.5, 16), (21.5, 21.5), (16, 21.5)])
    circle_fill(d, 12, 12, 1.7, ACCENT)

def g_fullscreen(d):
    line(d, [(4, 9), (4, 4), (9, 4)]); line(d, [(20, 9), (20, 4), (15, 4)])
    line(d, [(4, 15), (4, 20), (9, 20)]); line(d, [(20, 15), (20, 20), (15, 20)])


def padlock(d, unlocked):
    body = (5.5, 11, 18.5, 21)
    d.rounded_rectangle((body[0] * SS, body[1] * SS, body[2] * SS, body[3] * SS),
                        radius=2.6 * SS, fill=ACCENT if not unlocked else INK)
    bx0, by0 = 5.5, 11
    r = 4.4
    cx = 12
    # el arco: centrado (cerrado) o desplazado y abierto (permitido)
    top = by0 - r - 0.4
    if unlocked:
        d.arc(((cx - r + 3.2) * SS, top * SS, (cx + r + 3.2) * SS, (by0 + r) * SS),
              start=185, end=345, fill=INK, width=max(1, int(2.8 * SS)))
    else:
        d.arc(((cx - r) * SS, top * SS, (cx + r) * SS, (by0 + r) * SS),
              start=180, end=360, fill=(255, 90, 31), width=max(1, int(2.8 * SS)))
    # ojo de la cerradura (recortado en el color de la barra: blanco casi)
    hole = (255, 255, 255, 0)
    circle_fill(d, cx, by0 + 3.6, 1.7, hole)
    d.rectangle((cx * SS - 1 * SS, (by0 + 4.4) * SS, cx * SS + 1 * SS, (by0 + 7.4) * SS), fill=hole)


GLYPHS = [g_new_connection, g_save, g_options, g_info, g_pause, g_refresh,
          g_ctrl_alt_del, g_ctrl_esc, g_ctrl, g_alt, g_transfer,
          g_zoom_in, g_zoom_out, g_zoom_100, g_zoom_fit, g_fullscreen]


def build():
    strip = Image.new('RGBA', (N * S * SS, S * SS), (0, 0, 0, 0))
    for i, fn in enumerate(GLYPHS):
        img, d = canvas()
        fn(d)
        strip.paste(img, (i * S * SS, 0))
    for k, unlocked in enumerate((False, True)):     # 16: bloqueado, 17: permitido
        img, d = canvas()
        padlock(d, unlocked)
        strip.paste(img, ((16 + k) * S * SS, 0))
    return strip.resize((N * S, S), Image.LANCZOS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    ap.add_argument('--preview')
    ap.add_argument('--zoom', type=int, default=6)
    args = ap.parse_args()

    strip = build()
    if args.preview:
        z = args.zoom
        bg = Image.new('RGB', (strip.size[0] * z, strip.size[1] * z + 20), (243, 243, 243))
        bg.paste(strip.resize((strip.size[0] * z, strip.size[1] * z), Image.NEAREST),
                 (0, 10), strip.resize((strip.size[0] * z, strip.size[1] * z), Image.NEAREST))
        bg.save(args.preview)
        print('preview:', args.preview, bg.size)
    if args.out:
        # BMP de 32bpp con alfa: PIL guarda BMP sin alfa, asi que lo construyo a mano
        px = strip.load()
        w, h = strip.size
        stride = w * 4
        rows = []
        for y in range(h - 1, -1, -1):              # BMP: de abajo arriba
            row = bytearray()
            for x in range(w):
                r, g, b, a = px[x, y]
                row += bytes((b, g, r, a))
            rows.append(bytes(row))
        pixels = b''.join(rows)
        file_header = b'BM' + (14 + 40 + len(pixels)).to_bytes(4, 'little') + b'\0\0\0\0' + (54).to_bytes(4, 'little')
        info = (40).to_bytes(4, 'little') + w.to_bytes(4, 'little') + h.to_bytes(4, 'little') + \
               (1).to_bytes(2, 'little') + (32).to_bytes(2, 'little') + (0).to_bytes(4, 'little') + \
               len(pixels).to_bytes(4, 'little') + (2835).to_bytes(4, 'little') + (2835).to_bytes(4, 'little') + \
               (0).to_bytes(4, 'little') + (0).to_bytes(4, 'little')
        with open(args.out, 'wb') as f:
            f.write(file_header + info + pixels)
        print('escrito %s  %dx%d  32bpp con alfa  %d bytes' % (args.out, w, h, 54 + len(pixels)))


if __name__ == '__main__':
    main()
