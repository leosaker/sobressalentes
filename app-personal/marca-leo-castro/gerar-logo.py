"""Logo Leo Castro Personal — proposta "Ascensão".
Gera todos os SVGs da marca. Uso: python3 gerar-logo.py <pasta-de-saída>
Precisa de: fonttools e uharfbuzz (pip install fonttools uharfbuzz) e a fonte Inter Display."""
import math, sys
import uharfbuzz as hb
from fontTools.ttLib import TTFont
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
OUT = sys.argv[1]
INK, BLUE, BLUE_D, WHITE = '#111827', '#2f6bff', '#4d82ff', '#ffffff'
FONTS = {'blackit': '/usr/share/fonts/opentype/inter/InterDisplay-BlackItalic.otf', 'semi': '/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf'}
_c = {}
def text_path(text, w, size, track=0.0):
    p = FONTS[w]
    if p not in _c: _c[p] = (TTFont(p), hb.Font(hb.Face(open(p, 'rb').read())))
    tt, f = _c[p]; s = size / tt['head'].unitsPerEm
    buf = hb.Buffer(); buf.add_str(text); buf.guess_segment_properties(); hb.shape(f, buf, {'kern': True})
    gs = tt.getGlyphSet(); order = tt.getGlyphOrder(); pen = SVGPathPen(gs); x = 0
    for i, pos in zip(buf.glyph_infos, buf.glyph_positions):
        gs[order[i.codepoint]].draw(TransformPen(pen, (s, 0, 0, -s, x + pos.x_offset * s, 0))); x += pos.x_advance * s + track * size
    return pen.getCommands(), x - track * size, tt['OS/2'].sCapHeight * s

def symbol(c_l, c_arrow):
    """'L' inclinado (12°, como o itálico do nome) + seta de progresso subindo — no quadrado 512."""
    k = math.tan(math.radians(12))
    sk = lambda x, y: (x + (400 - y) * k, y)
    path = lambda pts: 'M' + ' L'.join(f'{x:.1f},{y:.1f}' for x, y in pts) + ' Z'
    L = path([sk(118, 104), sk(186, 104), sk(186, 336), sk(352, 336), sk(338, 400), sk(118, 400)])
    # seta: haste grossa a 45° com ponta triangular
    u, n = (math.sqrt(.5), -math.sqrt(.5)), (math.sqrt(.5), math.sqrt(.5))
    P0, P1, h, H, T = (262, 302), (352, 212), 31, 74, 82
    add = lambda p, v, s: (p[0] + v[0] * s, p[1] + v[1] * s)
    tip = add(P1, u, T)
    A = path([add(P0, n, h), add(P1, n, h), add(P1, n, H), tip, add(P1, n, -H), add(P1, n, -h), add(P0, n, -h)])
    return f'<path d="{L}" fill="{c_l}"/><path d="{A}" fill="{c_arrow}"/>'

def svg(w, h, body, bg=None):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w:.0f} {h:.0f}" width="{w:.0f}" height="{h:.0f}">'
            + (f'<rect width="{w:.0f}" height="{h:.0f}" fill="{bg}"/>' if bg else '') + body + '</svg>')

NAME = text_path('LEO CASTRO', 'blackit', 150, 0.0)
def horizontal(txt, sym_l, arrow, tagc):
    name, nw, ncap = NAME; tag, tw, tcap = text_path('PERSONAL TRAINER', 'semi', 46, 0.30)
    sym = 330; s = sym / 512; gx = sym + 18
    top = (sym - (ncap + 40 + tcap)) / 2
    W = gx + max(nw, tw + 12) + 6
    body = (f'<g transform="scale({s})">{symbol(sym_l, arrow)}</g>'
            f'<path transform="translate({gx},{top + ncap:.1f})" d="{name}" fill="{txt}"/>'
            f'<path transform="translate({gx + 12},{top + ncap + 40 + tcap:.1f})" d="{tag}" fill="{tagc}"/>')
    return svg(W, sym, body)
def vertical(txt, sym_l, arrow, tagc):
    name, nw, ncap = NAME; tag, tw, tcap = text_path('PERSONAL TRAINER', 'semi', 44, 0.32)
    W = max(nw, tw) + 40; sym = 360; s = sym / 512
    H = sym + 26 + ncap + 36 + tcap + 10
    body = (f'<g transform="translate({(W - sym) / 2:.1f},0) scale({s})">{symbol(sym_l, arrow)}</g>'
            f'<path transform="translate({(W - nw) / 2:.1f},{sym + 26 + ncap:.1f})" d="{name}" fill="{txt}"/>'
            f'<path transform="translate({(W - tw) / 2:.1f},{sym + 26 + ncap + 36 + tcap:.1f})" d="{tag}" fill="{tagc}"/>')
    return svg(W, H, body)
icon = lambda sc, bg, l, a: svg(512, 512, f'<g transform="translate(256,256) scale({sc}) translate(-256,-256)">{symbol(l, a)}</g>', bg)
files = {
  'leo-castro-simbolo.svg': svg(512, 512, symbol(INK, BLUE)),
  'leo-castro-simbolo-negativo.svg': svg(512, 512, symbol(WHITE, BLUE_D)),
  'leo-castro-icone-app.svg': icon(.78, INK, WHITE, BLUE_D),
  'leo-castro-horizontal.svg': horizontal(INK, INK, BLUE, BLUE),
  'leo-castro-horizontal-negativo.svg': horizontal(WHITE, WHITE, BLUE_D, '#9db8ff'),
  'leo-castro-vertical.svg': vertical(INK, INK, BLUE, BLUE),
  'leo-castro-vertical-negativo.svg': vertical(WHITE, WHITE, BLUE_D, '#9db8ff'),
  'leo-castro-badge.svg': icon(.9, None, WHITE, WHITE),
}
for n, c in files.items(): open(f'{OUT}/{n}', 'w').write(c)
print('ok:', ', '.join(files))
