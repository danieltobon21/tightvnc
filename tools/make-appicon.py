#!/usr/bin/env python3
"""Genera el icono de la aplicación TobonVNC Viewer.

Lenguaje visual de la familia Tobon (tomado de tobonframes.ico / tobonmouse.ico):
  * squircle plano (sin degradados ni sombras) con radio ~23% del ancho,
  * contorno claro grueso y uniforme (~7% del ancho),
  * un único acento sólido naranja,
  * esquinas redondeadas en todo, espacio negativo generoso,
  * arte simplificado para 16/24/32 px.

Se dibuja en 4x y se reduce con LANCZOS.

Uso:
    python3 tools/make-appicon.py --out tvnviewer/res/appicon.ico
    python3 tools/make-appicon.py --preview-big /tmp/big.png    # cada variante a 256
    python3 tools/make-appicon.py --preview-small /tmp/sm.png  # cada variante a 32/24/16
"""
import argparse
from PIL import Image, ImageDraw

BASE = (24, 26, 31)        # #181A1F
LIGHT = (236, 238, 242)    # #ECEEF2
ACCENT = (255, 90, 31)     # #FF5A1F

SIZES = [256, 128, 64, 48, 32, 24, 16]
SS = 4                     # supersampling


def squircle(size, radius_ratio=0.235, color=BASE):
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, size - 1, size - 1), radius=int(size * radius_ratio), fill=color)
    return img


def monitor(d, size, *, small):
    """Pantalla con peana. Devuelve el rectángulo de la pantalla."""
    s = size
    sw = int(s * (0.60 if not small else 0.68))
    sh = int(s * (0.40 if not small else 0.48))
    x0 = (s - sw) // 2
    y0 = int(s * (0.17 if not small else 0.13))
    stroke = max(2, int(s * (0.070 if not small else 0.095)))
    d.rounded_rectangle((x0, y0, x0 + sw, y0 + sh),
                        radius=int(sw * 0.16), outline=LIGHT, width=stroke)
    if not small:
        neck_w = int(sw * 0.14)
        neck_h = int(s * 0.055)
        cx = s // 2
        d.rectangle((cx - neck_w // 2, y0 + sh, cx + neck_w // 2, y0 + sh + neck_h), fill=LIGHT)
        base_w = int(sw * 0.44)
        base_h = int(s * 0.045)
        d.rounded_rectangle((cx - base_w // 2, y0 + sh + neck_h - base_h // 2,
                             cx + base_w // 2, y0 + sh + neck_h + base_h // 2),
                            radius=max(1, base_h // 2), fill=LIGHT)
    return (x0, y0, x0 + sw, y0 + sh)


def padlock(d, size, cx, cy, w, *, small, halo=None):
    """Candado sólido en color de acento; ojo de la cerradura en color de fondo.

    `halo` = contorno de separación en color de fondo, para que el candado no se
    funda con el contorno claro de la pantalla.
    """
    body_w = w
    body_h = int(w * 0.80)
    x0 = cx - body_w // 2
    y0 = cy - body_h // 2 + int(w * 0.13)
    r = max(1, int(body_w * (0.22 if not small else 0.26)))
    arc_w = int(body_w * 0.58)
    arc_h = int(body_w * 0.58)
    ax0 = cx - arc_w // 2
    ay0 = y0 - int(arc_h * 0.48)
    stroke = max(2, int(body_w * (0.19 if not small else 0.26)))

    if halo is not None:
        hw = max(1, int(w * 0.10))
        d.rounded_rectangle((x0 - hw, y0 - hw, x0 + body_w + hw, y0 + body_h + hw),
                            radius=r + hw, fill=halo)
        d.arc((ax0 - hw, ay0 - hw, ax0 + arc_w + hw, ay0 + arc_h + hw),
              start=180, end=360, fill=halo, width=stroke + hw * 2)

    d.rounded_rectangle((x0, y0, x0 + body_w, y0 + body_h), radius=r, fill=ACCENT)
    d.arc((ax0, ay0, ax0 + arc_w, ay0 + arc_h), start=180, end=360, fill=ACCENT, width=stroke)

    k = max(2, int(body_w * (0.22 if not small else 0.28)))
    kx = cx - k // 2
    ky = y0 + int(body_h * 0.26)
    d.ellipse((kx, ky, kx + k, ky + k), fill=BASE)
    d.rectangle((cx - max(1, k // 4), ky + k - 1, cx + max(1, k // 4), y0 + int(body_h * 0.76)),
                fill=BASE)


def micro(size):
    """Dibujo dedicado a 16 px: nada de peana, trazo grueso y candado grande.
    A ese tamaño un monitor con detalles se convierte en mancha."""
    img = squircle(size)
    d = ImageDraw.Draw(img)
    stroke = max(2, int(size * 0.11))
    x0, y0 = int(size * 0.10), int(size * 0.26)
    x1, y1 = int(size * 0.90), int(size * 0.64)
    d.rounded_rectangle((x0, y0, x1, y1), radius=int((x1 - x0) * 0.20),
                        outline=LIGHT, width=stroke)
    cx = size // 2
    body_w = int(size * 0.40)
    body_h = int(body_w * 0.76)
    by0 = size - int(size * 0.30) - body_h
    r = max(1, int(body_w * 0.24))
    arc_w = int(body_w * 0.56)
    d.arc((cx - arc_w // 2, by0 - int(arc_w * 0.46), cx + arc_w // 2, by0 + int(arc_w * 0.54)),
          start=180, end=360, fill=ACCENT, width=max(2, int(body_w * 0.26)))
    d.rounded_rectangle((cx - body_w // 2, by0, cx + body_w // 2, by0 + body_h),
                        radius=r, fill=ACCENT)
    k = max(2, int(body_w * 0.26))
    ky = by0 + int(body_h * 0.28)
    d.ellipse((cx - k // 2, ky, cx + k // 2, ky + k), fill=BASE)
    return img


def icon(variant, size, *, small):
    img = squircle(size)
    d = ImageDraw.Draw(img)
    if variant == 'A1':          # candado naranja DENTRO de la pantalla (estilo familia)
        box = monitor(d, size, small=small)
        padlock(d, size, (box[0] + box[2]) // 2,
                (box[1] + box[3]) // 2 + int(size * 0.01),
                int(size * (0.29 if not small else 0.355)), small=small)
    elif variant == 'A2':        # monitor + candado como insignia en la esquina
        monitor(d, size, small=small)
        padlock(d, size, int(size * 0.735), int(size * 0.735),
                int(size * (0.36 if not small else 0.40)), small=small, halo=BASE)
    elif variant == 'A3':        # monitor + candado grande delante, separado por halo
        monitor(d, size, small=small)
        padlock(d, size, int(size * 0.50), int(size * 0.60),
                int(size * (0.42 if not small else 0.46)), small=small, halo=BASE)
    else:
        raise ValueError(variant)
    return img


def sizes_for(variant):
    """Cada tamaño, dibujado en 4x y reducido. Arte simplificado por debajo de 48."""
    out = {}
    for s in SIZES:
        if s <= 16:
            out[s] = micro(s * SS).resize((s, s), Image.LANCZOS)
        else:
            out[s] = icon(variant, s * SS, small=(s <= 32)).resize((s, s), Image.LANCZOS)
    return out


def strip(variant, scale_sizes, zoom, bg=(228, 231, 236)):
    icons = sizes_for(variant)
    h = max(s * zoom for s in scale_sizes)
    w = sum(s * zoom + 16 for s in scale_sizes) + 16
    img = Image.new('RGB', (w, h + 32), bg)
    x = 16
    for s in scale_sizes:
        ic = icons[s].resize((s * zoom, s * zoom), Image.NEAREST).convert('RGB')
        img.paste(ic, (x, 16 + (h - ic.size[1])))
        x += s * zoom + 16
    return img


def stack(rows, path):
    W = max(r.size[0] for r in rows)
    sheet = Image.new('RGB', (W, sum(r.size[1] for r in rows)), (228, 231, 236))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y)); y += r.size[1]
    sheet.save(path)
    print('%s %s' % (path, sheet.size))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out')
    ap.add_argument('--variant', default='A1')
    ap.add_argument('--preview-big')
    ap.add_argument('--preview-small')
    args = ap.parse_args()

    if args.preview_big:
        variants = ['A1', 'A2', 'A3']
        sheet = Image.new('RGB', (len(variants) * (256 + 20) + 20, 256 + 40), (228, 231, 236))
        x = 20
        for v in variants:
            sheet.paste(icon(v, 1024, small=False).resize((256, 256), Image.LANCZOS).convert('RGB'),
                        (x, 20))
            x += 256 + 20
        sheet.save(args.preview_big)
        print('preview-big:', args.preview_big, sheet.size)
    if args.preview_small:
        stack([strip(v, (32, 24, 16), 6) for v in ['A1', 'A2', 'A3']], args.preview_small)
    if args.out:
        icons = sizes_for(args.variant)
        icons[256].save(args.out, format='ICO', sizes=[(s, s) for s in SIZES])
        print('escrito %s (%s) tamaños %s' % (args.out, args.variant, SIZES))


if __name__ == '__main__':
    main()
