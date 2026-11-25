import math, sys, uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
OUT = sys.argv[1]
NAVY, ORANGE, WHITE = '#0f2742', '#ff6b1a', '#ffffff'
FONTS = {'black': '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf', 'semi': '/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf'}
_cache = {}
def text_path(text, weight, size, tracking=0.0):
    """Texto → caminho SVG (com kerning via HarfBuzz). Retorna (d, largura, altura das maiúsculas)."""
    path = FONTS[weight]
    if path not in _cache:
        data = open(path, 'rb').read(); _cache[path] = (TTFont(path), hb.Font(hb.Face(data)))
    tt, f = _cache[path]
    upm = tt['head'].unitsPerEm; s = size / upm
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(f, buf, {'kern': True, 'liga': False})
    gs = tt.getGlyphSet(); order = tt.getGlyphOrder()
    pen = SVGPathPen(gs); x = 0
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        g = order[info.codepoint]
        gs[g].draw(TransformPen(pen, (s, 0, 0, -s, x + pos.x_offset * s, -pos.y_offset * s)))
        x += pos.x_advance * s + tracking * size
    cap = tt['OS/2'].sCapHeight * s
    return pen.getCommands(), x - tracking * size, cap

def symbol(c_color, l_color, cx=256, cy=256, scale=1.0):
    """Símbolo LC no quadrado 512: C laranja aberto à direita + L cuja base atravessa a abertura."""
    k = scale
    R, W = 172 * k, 62 * k                     # raio médio e espessura do C
    a0, a1 = math.radians(47), math.radians(313) # abertura de 94° à direita
    ro, ri = R + W / 2, R - W / 2
    P = lambda r, a: (cx + r * math.cos(a), cy - r * math.sin(a))
    o0, o1, i1, i0 = P(ro, a0), P(ro, a1), P(ri, a1), P(ri, a0)
    c = (f'M{o0[0]:.1f},{o0[1]:.1f} A{ro:.1f},{ro:.1f} 0 1 0 {o1[0]:.1f},{o1[1]:.1f} '
         f'L{i1[0]:.1f},{i1[1]:.1f} A{ri:.1f},{ri:.1f} 0 1 1 {i0[0]:.1f},{i0[1]:.1f} Z')
    # L: haste vertical + base que sai pela abertura com corte inclinado (movimento)
    x0, x1 = cx - 82 * k, cx - 14 * k           # haste
    yt, yb = cy - 124 * k, cy + 84 * k          # topo e base
    fy = yb - 62 * k                            # topo da base
    fx = cx + 204 * k                           # ponta da base (passa do C)
    l = (f'M{x0:.1f},{yt:.1f} L{x1:.1f},{yt - 14*k:.1f} L{x1:.1f},{fy:.1f} L{fx:.1f},{fy:.1f} '
         f'L{fx - 26*k:.1f},{yb:.1f} L{x0:.1f},{yb:.1f} Z')
    return f'<path d="{c}" fill="{c_color}"/><path d="{l}" fill="{l_color}"/>'

def svg(w, h, body, bg=None):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">'
            + (f'<rect width="{w}" height="{h}" fill="{bg}"/>' if bg else '') + body + '</svg>')

def horizontal(text_color, l_color, tag_color, bg=None):
    name, nw, ncap = text_path('LEO CASTRO', 'black', 150, 0.01)
    tag, tw, tcap = text_path('PERSONAL TRAINER', 'semi', 58, 0.28)
    sym_h = 360; sx = 0; s = sym_h / 512
    gx = sym_h + 40                                   # texto começa depois do símbolo
    H = sym_h; top = (H - (ncap + 46 + tcap)) / 2
    W = gx + max(nw, tw) + 8
    body = (f'<g transform="translate({sx},0) scale({s})">{symbol(ORANGE, l_color)}</g>'
            f'<path transform="translate({gx},{top + ncap:.1f})" d="{name}" fill="{text_color}"/>'
            f'<rect x="{gx + 2}" y="{top + ncap + 46 + tcap / 2 - 3.5:.1f}" width="56" height="7" rx="3.5" fill="{ORANGE}"/>'
            f'<path transform="translate({gx + 82},{top + ncap + 46 + tcap:.1f})" d="{tag}" fill="{tag_color}"/>')
    return svg(round(W), H, body, bg)

def stacked(text_color, l_color, tag_color, bg=None):
    name, nw, ncap = text_path('LEO CASTRO', 'black', 130, 0.01)
    tag, tw, tcap = text_path('PERSONAL TRAINER', 'semi', 46, 0.3)
    W = max(nw, tw, 420) + 80; sym = 380; s = sym / 512
    H = sym + 40 + ncap + 34 + tcap + 30
    body = (f'<g transform="translate({(W - sym) / 2:.1f},0) scale({s})">{symbol(ORANGE, l_color)}</g>'
            f'<path transform="translate({(W - nw) / 2:.1f},{sym + 40 + ncap:.1f})" d="{name}" fill="{text_color}"/>'
            f'<path transform="translate({(W - tw) / 2:.1f},{sym + 40 + ncap + 34 + tcap:.1f})" d="{tag}" fill="{tag_color}"/>')
    return svg(round(W), round(H), body, bg)

files = {
  'leo-castro-simbolo.svg': svg(512, 512, symbol(ORANGE, NAVY)),
  'leo-castro-simbolo-negativo.svg': svg(512, 512, symbol(ORANGE, WHITE)),
  'leo-castro-icone-app.svg': svg(512, 512, f'<g transform="translate(256,256) scale(.72) translate(-256,-256)">{symbol(ORANGE, WHITE)}</g>', NAVY),
  'leo-castro-horizontal.svg': horizontal(NAVY, NAVY, NAVY),
  'leo-castro-horizontal-negativo.svg': horizontal(WHITE, WHITE, '#c9d6e8'),
  'leo-castro-vertical.svg': stacked(NAVY, NAVY, NAVY),
  'leo-castro-vertical-negativo.svg': stacked(WHITE, WHITE, '#c9d6e8'),
  'leo-castro-badge.svg': svg(512, 512, f'<g transform="translate(256,256) scale(.86) translate(-256,-256)">{symbol(WHITE, WHITE)}</g>'),
}
for n, c in files.items(): open(f'{OUT}/{n}', 'w').write(c)
print('ok', list(files))
