"""Generates public/assets/32x32robots.png, the robot sprite sheet.

The sheet uses the same layout as 32x32folk.png so the existing spritesheet
definitions (f1..f8) keep working: 4x2 characters, each a 96x128 block with
rows down/left/right/up and 3 animation frames per row (stand, step, step).

Usage: python3 scripts/generate-robot-sprites.py
"""

import colorsys
from pathlib import Path

from PIL import Image

S = 32
OUTLINE = (22, 20, 34, 255)


def hex_rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def shift(rgb, dl, dh=0.0, ds=0.0):
    r, g, b = (c / 255 for c in rgb)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    h = (h + dh) % 1.0
    l = min(1.0, max(0.0, l + dl))
    s = min(1.0, max(0.0, s + ds))
    return tuple(round(c * 255) for c in colorsys.hls_to_rgb(h, l, s)) + (255,)


def ramp(h):
    """Four-tone ramp: highlight, base, shade, dark. Shades drift toward blue, highlights toward warm."""
    rgb = hex_rgb(h)
    return (
        shift(rgb, 0.14, -0.02, 0.05),
        rgb + (255,),
        shift(rgb, -0.14, 0.03, 0.02),
        shift(rgb, -0.27, 0.05, 0.0),
    )


def rrect(x0, y0, x1, y1, rt=0, rb=0):
    """Rounded rectangle mask, inclusive coords, separate top/bottom corner radii."""
    m = set()
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            ok = True
            for r, cy0 in ((rt, y - y0), (rb, y1 - y)):
                if r <= 0:
                    continue
                for cx0 in (x - x0, x1 - x):
                    dx, dy = r - cx0 - 0.5, r - cy0 - 0.5
                    if dx > 0 and dy > 0 and dx * dx + dy * dy > (r - 0.5) ** 2:
                        ok = False
            if ok:
                m.add((x, y))
    return m


def ellipse(cx, cy, rx, ry):
    return {
        (x, y)
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2)
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2)
        if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1
    }


class Canvas:
    def __init__(self):
        self.im = Image.new('RGBA', (S, S), (0, 0, 0, 0))
        self.px = self.im.load()

    def put(self, x, y, c):
        if 0 <= x < S and 0 <= y < S:
            if len(c) == 3:
                c = c + (255,)
            if c[3] < 255:
                base = self.px[x, y]
                a = c[3] / 255
                if base[3] == 0:
                    self.px[x, y] = c
                    return
                c = tuple(round(c[i] * a + base[i] * (1 - a)) for i in range(3)) + (255,)
            self.px[x, y] = c

    def fill(self, mask, c):
        for x, y in mask:
            self.put(x, y, c)

    def blob(self, mask, pal, outline=True, spec=None):
        """Draws a shaded, outlined shape lit from the top-left."""
        hi, base, sh, dk = pal
        if outline:
            for x, y in mask:
                for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                    if (nx, ny) not in mask:
                        self.put(nx, ny, OUTLINE)
        for x, y in mask:
            if (x, y + 1) not in mask:
                c = dk
            elif (x, y - 1) not in mask:
                c = hi
            elif (x + 1, y) not in mask or (x, y + 2) not in mask:
                c = sh
            elif (x - 1, y) not in mask:
                c = hi
            else:
                c = base
            self.put(x, y, c)
        if spec:
            for p in spec:
                self.put(*p, (255, 255, 255, 220))


def glow(cv, x, y, c, w=2, h=2):
    """Bright pixel cluster with a soft halo and a hot white core."""
    for gx in range(x - 1, x + w + 1):
        for gy in range(y - 1, y + h + 1):
            if not (x <= gx < x + w and y <= gy < y + h):
                cv.put(gx, gy, c[:3] + (90,))
    for gx in range(x, x + w):
        for gy in range(y, y + h):
            cv.put(gx, gy, c)
    cv.put(x, y, shift(c[:3], 0.25))


# --- Robot definitions --------------------------------------------------------

ROBOTS = [
    # f1 Lucky: cheerful space explorer
    dict(body='#5d9eea', trim='#dfe6f0', screen='#14203a', eye='#7ff3ff', accent='#ff9a3c',
         antenna='bulb', head='box', eyes='dots', legs='legs', chest='star'),
    # f2 Kurt: secretive, red scanner eye
    dict(body='#535a6b', trim='#30343f', screen='#0d080c', eye='#ff3b4a', accent='#ff3b4a',
         antenna='fin', head='box', eyes='scanner', legs='legs', chest='lock'),
    # f3 Alice: brilliant scientist, glass dome brain
    dict(body='#9277dc', trim='#4b4374', screen='#1b1430', eye='#7dfcd4', accent='#ffd166',
         antenna='dish', head='dome', eyes='big', legs='legs', chest='atom'),
    # f4 Bob: grumpy gardener on treads
    dict(body='#7f9a4a', trim='#6b5238', screen='#151a10', eye='#ffd84a', accent='#8fe05a',
         antenna='sprout', head='box', eyes='grumpy', legs='treads', chest='vent'),
    # f5 Alex: painter with a beret
    dict(body='#f0b445', trim='#3d4b6e', screen='#161d2c', eye='#6ff0ff', accent='#e8505b',
         antenna='beret', head='round', eyes='dots', legs='legs', chest='paint'),
    # f6 Stella: charming, heart eyes
    dict(body='#ef7fb0', trim='#7a3b6e', screen='#26101f', eye='#ff4f8b', accent='#ffe066',
         antenna='bow', head='round', eyes='heart', legs='legs', chest='gem'),
    # f7 Pete: devout, ivory and gold with a halo
    dict(body='#ece2c8', trim='#c39126', screen='#221a0c', eye='#ffe27a', accent='#ffd34d',
         antenna='halo', head='dome', eyes='calm', legs='legs', chest='cross'),
    # f8 Kira: smiling hover-bot hiding a tear
    dict(body='#68cfc2', trim='#2f6c8a', screen='#0d2230', eye='#c4f8ff', accent='#7ad7ff',
         antenna='ears', head='round', eyes='happy', legs='hover', chest='light'),
]


def head_mask(r, y0, view):
    x0, x1, y1 = 8, 23, y0 + 12
    if r['head'] == 'dome':
        return rrect(x0, y0, x1, y1, 5, 2)
    if r['head'] == 'round':
        return rrect(x0, y0, x1, y1, 4, 3)
    return rrect(x0, y0, x1, y1, 2, 2)


def draw_antenna(cv, r, view, y0, P):
    a = r['antenna']
    acc = hex_rgb(r['accent']) + (255,)
    tr = P['trim']
    cx = 15 if view != 'left' else 16
    if a == 'bulb':
        cv.blob({(cx, y0 - 1), (cx, y0 - 2)}, tr)
        cv.blob(rrect(cx - 1, y0 - 5, cx + 1, y0 - 3, 1, 1), ramp(r['accent']))
        cv.put(cx - 1 + (view == 'left'), y0 - 4, (255, 255, 255, 230))
    elif a == 'fin':
        fin = rrect(cx - 1, y0 - 3, cx + 2, y0, 1, 0) if view != 'left' else rrect(cx - 3, y0 - 3, cx + 3, y0, 2, 0)
        cv.blob(fin, P['trim'])
        for x, y in fin:
            if y == y0 - 2 and x % 2 == 0:
                cv.put(x, y, acc[:3] + (200,))
    elif a == 'dish':
        side = [(6, 7), (24, 25)] if view != 'left' else [(18, 20)]
        for xa, xb in side:
            cv.blob(rrect(xa, y0 + 4, xb, y0 + 7, 1, 1), P['trim'])
            cv.put(xa if xa < 15 else xb, y0 + 5, acc)
        cv.blob({(cx, y0 - 1), (cx, y0 - 2)}, P['trim'])
        glow(cv, cx, y0 - 3, acc, 1, 1)
    elif a == 'sprout':
        leaf = ramp('#6fd04a')
        cv.blob({(cx + 1, y0 - 1), (cx + 1, y0 - 2)}, ramp('#4a8a2e'))
        cv.blob({(cx - 1, y0 - 3), (cx, y0 - 3), (cx, y0 - 2)}, leaf)
        cv.blob({(cx + 2, y0 - 4), (cx + 3, y0 - 4), (cx + 2, y0 - 3)}, leaf)
    elif a == 'beret':
        beret = ramp('#c8363f')
        if view == 'left':
            m = rrect(10, y0 - 2, 22, y0 + 1, 2, 1)
        else:
            m = rrect(9, y0 - 2, 21, y0 + 1, 2, 1)
        cv.blob(m, beret)
        cv.blob({(15, y0 - 3)}, beret)
    elif a == 'bow':
        bow = ramp(r['accent'])
        bx = 19 if view != 'up' else 11
        cv.blob({(bx, y0), (bx, y0 - 1), (bx + 1, y0 - 2), (bx - 1, y0 - 2), (bx + 1, y0 + 1), (bx - 1, y0 + 1),
                 (bx + 2, y0 - 2), (bx - 2, y0 - 2), (bx + 2, y0 + 1), (bx - 2, y0 + 1),
                 (bx + 2, y0 - 1), (bx - 2, y0 - 1), (bx + 2, y0), (bx - 2, y0)} - {(bx, y0 - 1)} | {(bx, y0 - 1)}, bow)
        cv.put(bx, y0 - 1, bow[3])
    elif a == 'halo':
        gold = hex_rgb(r['accent'])
        ring = ellipse(15.5 if view != 'left' else 16.5, y0 - 2.5, 6, 1.6) - ellipse(15.5 if view != 'left' else 16.5, y0 - 2.5, 4.2, 0.7)
        for x, y in ring:
            cv.put(x, y, gold + (255,))
        for x, y in ellipse(15.5 if view != 'left' else 16.5, y0 - 2.5, 7.2, 2.6) - ring:
            if cv.px[x, y][3] == 0:
                cv.put(x, y, gold + (70,))
    elif a == 'ears':
        xs = [(8, 10), (21, 23)] if view != 'left' else [(18, 20)]
        for xa, xb in xs:
            cv.blob({(x, y0 - 1) for x in range(xa, xb + 1)} | {((xa + xb) // 2, y0 - 2)}, P['body'])


def draw_face(cv, r, view, y0, P):
    scr = hex_rgb(r['screen']) + (255,)
    eye = hex_rgb(r['eye']) + (255,)
    scr_hi = shift(scr[:3], 0.12)
    if view == 'up':
        # Back of head: maintenance panel with vents and a status light.
        for x, y in rrect(11, y0 + 4, 20, y0 + 9, 1, 1):
            cv.put(x, y, P['body'][2])
        for y in (y0 + 5, y0 + 7):
            for x in range(13, 19):
                cv.put(x, y, P['body'][3])
        cv.put(12, y0 + 9, P['body'][3])
        cv.put(19, y0 + 9, P['body'][3])
        glow(cv, 15, y0 + 9, hex_rgb(r['accent']) + (255,), 2, 1)
        return
    if view == 'down':
        sx0, sx1 = 10, 21
    else:
        sx0, sx1 = 8, 15
    screen = rrect(sx0, y0 + 3, sx1, y0 + 9, 1, 1)
    for x, y in screen:
        cv.put(x, y, scr)
    # Bezel shading + glass reflection.
    for x, y in screen:
        if (x, y - 1) not in screen:
            cv.put(x, y, P['body'][3])
    cv.put(sx1 - 1, y0 + 4, scr_hi)
    cv.put(sx1 - 2, y0 + 4, scr_hi)
    cv.put(sx1 - 1, y0 + 5, scr_hi)

    eyes = [(12, 18)] if view == 'down' else [(9,)]
    ex = eyes[0]
    ey = y0 + 5
    style = r['eyes']
    for x in ex:
        if style == 'dots':
            glow(cv, x, ey, eye)
        elif style == 'big':
            glow(cv, x, ey - 1, eye, 2, 3)
        elif style == 'grumpy':
            glow(cv, x, ey + 1, eye, 2, 1)
            # Angry brow slanting toward the middle.
            inner = x + 1 if (view == 'left' or x < 15) else x
            outer = x if inner == x + 1 else x + 1
            cv.put(outer, ey - 1, P['trim'][1])
            cv.put(inner, ey, P['trim'][1])
        elif style == 'heart':
            for dx, dy in ((0, 0), (2, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
                cv.put(x - 1 + dx + (view == 'left'), ey + dy - 1 + 1, eye)
            cv.put(x - 1 + (view == 'left'), ey, shift(eye[:3], 0.25))
        elif style == 'calm':
            cv.put(x, ey + 1, eye)
            cv.put(x + 1, ey + 1, eye)
            cv.put(x - 1, ey, eye[:3] + (140,))
            cv.put(x + 2, ey, eye[:3] + (140,))
        elif style == 'happy':
            cv.put(x - 1 + (view == 'left'), ey + 1, eye)
            cv.put(x + (view == 'left'), ey, eye)
            cv.put(x + 1 + (view == 'left'), ey, eye)
            cv.put(x + 2, ey + 1, eye) if view == 'down' else cv.put(x + 2, ey + 1, eye)
    if style == 'scanner':
        x0, x1 = (sx0 + 1, sx1 - 1)
        for x in range(x0, x1 + 1):
            cv.put(x, ey + 1, eye[:3] + (110,))
        cx = 16 if view == 'down' else 10
        glow(cv, cx - 1, ey + 1, eye, 3 if view == 'down' else 2, 1)
    if style == 'happy':
        # A single tear she can't quite hide.
        tx = ex[0] + (1 if view == 'down' else 1)
        cv.put(tx, ey + 3, (150, 230, 255, 255))
    # Mouth grille.
    if style not in ('scanner',):
        mx = 14 if view == 'down' else 9
        mw = 4 if view == 'down' else 2
        mouth = scr_hi if style != 'grumpy' else shift(scr[:3], 0.06)
        for x in range(mx, mx + mw):
            cv.put(x, y0 + 8, mouth)
        if style in ('dots', 'big', 'heart', 'happy', 'calm') and view == 'down':
            cv.put(mx - 1, y0 + 7, mouth)
            cv.put(mx + mw, y0 + 7, mouth)


def draw_chest(cv, r, view, ty, P):
    acc = hex_rgb(r['accent']) + (255,)
    if view == 'left':
        glow(cv, 12, ty + 3, acc, 1, 1)
        return
    if view == 'up':
        # Battery pack.
        cv.blob(rrect(12, ty + 1, 19, ty + 5, 1, 1), P['trim'])
        for i, x in enumerate(range(13, 19, 2)):
            cv.put(x, ty + 3, acc if i < 2 else P['trim'][3])
        return
    panel = rrect(13, ty + 2, 18, ty + 5, 1, 1)
    for x, y in panel:
        cv.put(x, y, P['trim'][3])
    kind = r['chest']
    if kind == 'star':
        for dx, dy in ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
            cv.put(14 + dx, ty + 2 + dy, acc)
        cv.put(15, ty + 3, shift(acc[:3], 0.25))
        cv.put(17, ty + 4, (120, 255, 160, 255))
    elif kind == 'lock':
        cv.put(15, ty + 2, acc)
        cv.put(16, ty + 2, acc)
        for x in range(14, 18):
            cv.put(x, ty + 3, acc[:3] + (180,))
            cv.put(x, ty + 4, acc[:3] + (180,))
    elif kind == 'atom':
        for dx, dy in ((0, 1), (1, 0), (2, 1), (1, 2), (3, 1), (1, 1)):
            cv.put(14 + dx, ty + 2 + dy, acc)
        cv.put(15, ty + 3, (255, 255, 255, 255))
    elif kind == 'vent':
        for y in (ty + 2, ty + 4):
            for x in range(14, 18):
                cv.put(x, y, P['body'][2])
        cv.put(17, ty + 3, acc)
    elif kind == 'paint':
        glow(cv, 15, ty + 3, acc, 2, 1)
        for (x, y), c in (((11, ty + 2), '#4fa3ff'), ((20, ty + 4), '#7be07a'), ((12, ty + 5), '#e8505b')):
            cv.put(x, y, hex_rgb(c))
    elif kind == 'gem':
        for dx, dy in ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)):
            cv.put(14 + dx, ty + 2 + dy, hex_rgb('#ff4f8b'))
        cv.put(15, ty + 3, (255, 220, 235, 255))
    elif kind == 'cross':
        for dx, dy in ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2), (1, 3)):
            cv.put(14 + dx, ty + 2 + dy, acc)
    else:
        glow(cv, 15, ty + 3, acc, 2, 1)


def draw_robot(r, view, frame):
    cv = Canvas()
    P = {k: ramp(r[k]) for k in ('body', 'trim')}
    loco = r['legs']
    step = frame  # 0 stand, 1 step A, 2 step B

    bob = 1 if (loco == 'legs' and step) else 0
    if loco == 'hover':
        bob = [-1, -2, -1][step]
    head_y = 5 + bob
    torso_y = 18 + bob

    # Ground shadow.
    sw = 5.5 if loco != 'hover' else 4.0
    for x, y in ellipse(15.5, 29.5, sw, 1.6):
        cv.put(x, y, (20, 16, 40, 70))

    # Locomotion.
    if loco == 'legs':
        legc = P['trim']
        if view == 'left':
            front, back = [(14, 0), (11, 0), (17, 0)][step], [(14, 0), (17, 0), (11, 0)][step]
            for lx, _ in (back, front):
                dark = (lx, _) is back and step != 0
                pal = (legc[2], legc[2], legc[3], legc[3]) if dark else legc
                cv.blob(rrect(lx, 25 + bob - 1, lx + 2, 28, 0, 0), pal)
                cv.blob(rrect(lx - 1, 28, lx + 2, 29, 1, 0), (P['body'][1], P['body'][2], P['body'][3], P['body'][3]))
        else:
            lifts = [(0, 0), (1, 0), (0, 1)][step]
            for (lx, lift) in ((11, lifts[0]), (17, lifts[1])):
                cv.blob(rrect(lx + 1, 24 + bob, lx + 2, 28 - lift, 0, 0), legc)
                cv.blob(rrect(lx, 27 - lift, lx + 3, 29 - lift, 1, 0), P['body'])
    elif loco == 'treads':
        tread = ramp('#3a3a44')
        if view == 'left':
            m = rrect(8, 25, 23, 29, 2, 2)
            cv.blob(m, tread)
            for i, wx in enumerate((10, 15, 20)):
                cv.blob(rrect(wx, 26, wx + 2, 28, 1, 1), ramp('#8a8a96'))
            for x in range(9, 23):
                if (x + step) % 3 == 0:
                    cv.put(x, 25, tread[3])
                    cv.put(x, 29, tread[3])
        else:
            for tx in (9, 18):
                m = rrect(tx, 24, tx + 4, 29, 1, 1)
                cv.blob(m, tread)
                for y in range(25, 29):
                    if (y + step) % 2 == 0:
                        cv.put(tx + 1, y, tread[3])
                        cv.put(tx + 3, y, tread[3])
    elif loco == 'hover':
        acc = hex_rgb(r['accent'])
        cv.blob(rrect(12, 24 + bob, 19, 25 + bob, 0, 2), P['trim'])
        flame = [3, 4, 2][step]
        for i in range(flame):
            a = 230 - i * 55
            w = 2 if i < flame - 1 else 1
            for x in range(16 - w, 16 + w):
                cv.put(x, 26 + bob + i, (shift(acc, 0.2 - i * 0.05)[:3]) + (a,))

    # Back arm (side view) and torso.
    swing = [0, -2, 2][step] if loco != 'hover' else 0
    if view == 'left':
        cv.blob(rrect(15 - swing, torso_y + 1, 17 - swing, torso_y + 5, 1, 1), (P['trim'][2], P['trim'][2], P['trim'][3], P['trim'][3]))
        cv.blob(rrect(11, torso_y, 20, torso_y + 6, 2, 2), P['body'])
    else:
        cv.blob(rrect(10, torso_y, 21, torso_y + 6, 2, 2), P['body'])
    draw_chest(cv, r, view, torso_y, P)

    # Arms.
    if view == 'left':
        ax = 14 + swing
        cv.blob(rrect(ax, torso_y + 1, ax + 2, torso_y + 5, 1, 0), P['trim'])
        cv.blob(rrect(ax, torso_y + 5, ax + 2, torso_y + 6, 0, 1), P['body'], spec=None)
    else:
        ls, rs = [(0, 0), (-1, 1), (1, -1)][step] if loco != 'hover' else (0, 0)
        for ax, s in ((7, ls), (22, rs)):
            cv.blob(rrect(ax, torso_y + 1 + s, ax + 2, torso_y + 4 + s, 1, 0), P['trim'])
            cv.blob(rrect(ax, torso_y + 5 + s, ax + 2, torso_y + 6 + s, 0, 1), P['body'])

    # Head.
    hm = head_mask(r, head_y, view)
    spec = [(10, head_y + 1), (11, head_y + 1), (10, head_y + 2)] if view != 'up' else [(10, head_y + 1)]
    cv.blob(hm, P['body'], spec=spec)
    if r['head'] == 'dome':
        # Glass cap over the top of the head.
        glass = {(x, y) for x, y in hm if y <= head_y + 3 and (x, y - 1) in hm and (x - 1, y) in hm and (x + 1, y) in hm}
        for x, y in glass:
            cv.put(x, y, (190, 240, 255, 150))
        if r['eyes'] == 'big':
            for x, y in ((13, head_y + 2), (14, head_y + 3), (15, head_y + 2), (16, head_y + 3), (17, head_y + 2), (18, head_y + 3)):
                cv.put(x, y, (255, 140, 200, 220))
        cv.put(11, head_y + 1, (255, 255, 255, 255))
        cv.put(12, head_y + 1, (255, 255, 255, 200))
    # Side bolts / ear caps.
    if view == 'down' or view == 'up':
        for bx in (7, 24):
            cv.blob(rrect(bx, head_y + 5, bx, head_y + 8, 0, 0), P['trim'])
    else:
        cv.blob(rrect(18, head_y + 5, 20, head_y + 8, 1, 1), P['trim'])
        cv.put(19, head_y + 6, P['trim'][3])
        cv.put(19, head_y + 7, P['trim'][3])
    draw_face(cv, r, view, head_y, P)
    draw_antenna(cv, r, view, head_y, P)
    return cv.im


def main():
    sheet = Image.new('RGBA', (384, 256), (0, 0, 0, 0))
    for i, r in enumerate(ROBOTS):
        bx, by = (i % 4) * 96, (i // 4) * 128
        for f in range(3):
            down = draw_robot(r, 'down', f)
            left = draw_robot(r, 'left', f)
            up = draw_robot(r, 'up', f)
            right = left.transpose(Image.FLIP_LEFT_RIGHT)
            for row, img in enumerate((down, left, right, up)):
                sheet.paste(img, (bx + f * 32, by + row * 32))
    out = Path(__file__).resolve().parent.parent / 'public' / 'assets' / '32x32robots.png'
    sheet.save(out)
    print(f'wrote {out}')


if __name__ == '__main__':
    main()
