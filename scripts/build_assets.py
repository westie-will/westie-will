#!/usr/bin/env python3
"""Generate the profile SVGs in assets/. Styled after d6sc.com: black, grid, HUD chrome.

Run from the repo root:  python3 scripts/build_assets.py
Fonts (Chakra Petch, JetBrains Mono, Inter) are subset per SVG from Google Fonts and inlined, since
GitHub renders SVGs as <img> and they can't load external fonts. Pass --no-fonts to skip that.
"""
import os
import random
from xml.sax.saxutils import escape

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

MONO = "'JetBrains Mono',ui-monospace,'SF Mono',SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"
DISP = "'Chakra Petch','Segoe UI','Helvetica Neue',Arial,sans-serif"
SANS = "Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

WHITE = "#FFFFFF"
INK = "#F2F4F7"
MUTED = "#8B8F96"
BLUE = "#1F6FEB"
BLUE2 = "#4D92FF"
GREEN = "#2ECC8A"

BASE_CSS = f"""
.m{{font-family:{MONO}}}
.d{{font-family:{DISP}}}
.s{{font-family:{SANS}}}
"""

KATA = "アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲン0123456789"


def svg(w, h, body, label, css=""):
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" '
        f'role="img" aria-label="{escape(label)}"><title>{escape(label)}</title>'
        f"<style>{BASE_CSS}{css}</style>{body}</svg>\n"
    )


def grid_bg(w, h, pid="g", size=40, op=0.045):
    return (
        f'<defs><pattern id="{pid}" width="{size}" height="{size}" patternUnits="userSpaceOnUse">'
        f'<path d="M{size} 0H0V{size}" fill="none" stroke="#fff" stroke-opacity="{op}"/></pattern></defs>'
        f'<rect width="{w}" height="{h}" fill="#000"/><rect width="{w}" height="{h}" fill="url(#{pid})"/>'
    )


def ticks(x, y, w, h, ln=12, off=6, op=0.9, sw=1.5):
    """Corner brackets outside the top-left and bottom-right corners, like d6sc.com panels."""
    tl = f"M{x - off} {y - off + ln}V{y - off}H{x - off + ln}"
    br = f"M{x + w + off} {y + h + off - ln}V{y + h + off}H{x + w + off - ln}"
    return f'<path d="{tl} {br}" fill="none" stroke="#fff" stroke-opacity="{op}" stroke-width="{sw}"/>'


def panel(x, y, w, h, left_num, left_label, right_label, strip=36):
    """Bordered panel with a numbered header strip: '01  LABEL ........ RIGHT'."""
    ty = y + strip / 2 + 4
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#000" fill-opacity=".55" '
        f'stroke="#fff" stroke-opacity=".22"/>'
        f'<line x1="{x}" y1="{y + strip}" x2="{x + w}" y2="{y + strip}" stroke="#fff" stroke-opacity=".1"/>'
        f'<text class="m" x="{x + 18}" y="{ty}" font-size="11" font-weight="700" fill="{WHITE}" '
        f'letter-spacing="1">{left_num}</text>'
        f'<text class="m" x="{x + 44}" y="{ty}" font-size="11" fill="{MUTED}" letter-spacing="3">{escape(left_label)}</text>'
        f'<text class="m" x="{x + w - 18}" y="{ty}" font-size="11" fill="{MUTED}" letter-spacing="3" '
        f'text-anchor="end">{escape(right_label)}</text>'
        + ticks(x, y, w, h)
    )


def rain(x, y, w, h, cid, cols=46, size=12, seed=6, op_range=(0.12, 0.45)):
    """Falling katakana columns clipped to a band, like the strip in d6sc.com's contact panel."""
    rnd = random.Random(seed)
    step = w / cols
    out = [f'<clipPath id="{cid}"><rect x="{x}" y="{y}" width="{w}" height="{h}"/></clipPath><g clip-path="url(#{cid})">']
    for c in range(cols):
        if rnd.random() < 0.28:
            continue
        cx = x + step * c + step / 2
        n = rnd.randint(3, 8)
        glyphs = rnd.choices(KATA, k=n)
        lh = size + 2
        dur = rnd.uniform(3.2, 8.5)
        begin = -rnd.uniform(0, dur)
        op = rnd.uniform(*op_range)
        spans = "".join(
            f'<tspan x="{cx:.1f}" dy="{lh}"{" fill-opacity=\"1\" fill=\"#fff\"" if i == n - 1 else ""}>{g}</tspan>'
            for i, g in enumerate(glyphs)
        )
        out.append(
            f'<text class="m" font-size="{size}" fill="#C9CDD3" fill-opacity="{op:.2f}" text-anchor="middle" '
            f'y="{y - n * lh}">{spans}'
            f'<animateTransform attributeName="transform" type="translate" from="0 0" to="0 {h + n * lh}" '
            f'dur="{dur:.2f}s" begin="{begin:.2f}s" repeatCount="indefinite"/></text>'
        )
    out.append("</g>")
    return "".join(out)


def timeline(points, total):
    """[(t_seconds, value)] -> (keyTimes, values) strings for a discrete SMIL animation."""
    merged = {}
    for t, v in sorted(points, key=lambda p: p[0]):
        merged[round(min(max(t, 0), total) / total, 5)] = v
    if 0 not in merged:
        merged[0.0] = points[0][1]
    if 1.0 not in merged:
        merged[1.0] = merged[max(merged)]
    keys = sorted(merged)
    return ";".join(f"{k:g}" for k in keys), ";".join(f"{merged[k]:g}" for k in keys)


def anim(attr, points, total):
    kt, vals = timeline(points, total)
    return (
        f'<animate attributeName="{attr}" dur="{total}s" repeatCount="indefinite" calcMode="discrete" '
        f'keyTimes="{kt}" values="{vals}"/>'
    )


# ---------------------------------------------------------------------------- header


def header():
    W, H = 1000, 500
    b = [grid_bg(W, H)]
    b.append(
        '<defs><radialGradient id="glow" cx="50%" cy="34%" r="45%">'
        '<stop offset="0" stop-color="#fff" stop-opacity=".09"/><stop offset="1" stop-color="#fff" stop-opacity="0"/>'
        '</radialGradient>'
        '<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#4D92FF" stop-opacity="0"/><stop offset=".5" stop-color="#4D92FF" stop-opacity=".07"/>'
        '<stop offset="1" stop-color="#4D92FF" stop-opacity="0"/></linearGradient>'
        '<linearGradient id="fade" x1="0" y1="0" x2="0" y2="1">'
        '<stop offset="0" stop-color="#fff" stop-opacity="0"/><stop offset=".35" stop-color="#fff" stop-opacity="1"/>'
        '<stop offset="1" stop-color="#fff" stop-opacity=".2"/></linearGradient>'
        '<mask id="rainmask"><rect x="0" y="430" width="1000" height="70" fill="url(#fade)"/></mask>'
        '<filter id="soft" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="14"/></filter>'
        "</defs>"
        f'<rect width="{W}" height="{H}" fill="url(#glow)"/>'
    )

    # HUD top bar
    b.append(
        f'<rect x="40" y="21" width="8" height="8" fill="{BLUE2}">'
        '<animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></rect>'
        f'<text class="m" x="58" y="29" font-size="11" fill="{WHITE}" letter-spacing="2.5">SYSTEM ONLINE</text>'
        f'<text class="m" x="500" y="29" font-size="11" fill="{MUTED}" letter-spacing="3" text-anchor="middle">EST. DEEP SIX · SC</text>'
        f'<text class="m" x="960" y="29" font-size="11" fill="{MUTED}" letter-spacing="2.5" text-anchor="end">NODE · WESTIE-WILL</text>'
        '<line x1="40" y1="46" x2="960" y2="46" stroke="#fff" stroke-opacity=".12"/>'
    )

    # Wordmark block: white letters on a black plate, soft glow, corner brackets
    bx, by, bw, bh = 220, 84, 560, 150
    b.append(
        f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="#fff" opacity=".10" filter="url(#soft)"/>'
        f'<rect x="{bx}" y="{by}" width="{bw}" height="{bh}" fill="#000"/>'
        f'<text class="d" x="500" y="{by + 118}" font-size="122" font-weight="700" fill="{WHITE}" '
        f'text-anchor="middle" letter-spacing="0">WESTIE</text>'
        + ticks(bx, by, bw, bh, ln=24, off=14, op=0.85, sw=2)
    )

    b.append(
        f'<text class="d" x="503" y="296" font-size="25" font-weight="600" fill="{WHITE}" '
        f'text-anchor="middle" letter-spacing="7">FULL STACK · WEB3 · MACHINE LEARNING</text>'
        f'<text class="s" x="500" y="336" font-size="17" font-weight="300" fill="{MUTED}" text-anchor="middle">'
        "Quantitative sports models, prediction-market execution and real-time data platforms.</text>"
        f'<text class="s" x="500" y="361" font-size="17" font-weight="300" fill="{MUTED}" text-anchor="middle">'
        "I build the systems the edge runs on.</text>"
    )

    # Typed command line, cycling
    lines = [
        "pricing every prop on the board",
        "live odds -> models -> edges, in real time",
        "shipping data, models and product end to end",
        "the house has math. so do i.",
    ]
    size, cw = 15, 9.0
    prefix = "will@d6sc:~$ "
    longest = max(len(prefix + l) for l in lines)
    x0 = 500 - (longest * cw) / 2
    tx = x0 + len(prefix) * cw
    y = 408
    slot = 4.5
    total = slot * len(lines)
    b.append(
        f'<text class="m" x="{x0:.1f}" y="{y}" font-size="{size}" fill="{BLUE2}">will@d6sc'
        f'<tspan fill="{MUTED}">:~$</tspan></text>'
    )
    cursor_pts = []
    for i, line in enumerate(lines):
        t0 = i * slot
        n = len(line)
        tdur = min(1.9, n * 0.05)
        pts = [(0, 0)]
        for k in range(n + 1):
            t = t0 + tdur * k / n
            pts.append((t, k * cw + (cw if k == n else 0)))
            cursor_pts.append((t, tx + k * cw))
        pts.append((t0 + slot - 0.35, 0))
        cursor_pts.append((t0 + slot - 0.35, tx))
        b.append(
            f'<clipPath id="tc{i}"><rect x="{tx:.1f}" y="{y - size}" height="{size * 1.6}" width="0">'
            + anim("width", pts, total)
            + "</rect></clipPath>"
            f'<text class="m" x="{tx:.1f}" y="{y}" font-size="{size}" fill="{INK}" clip-path="url(#tc{i})">'
            f"{escape(line)}</text>"
        )
    cursor_pts.insert(0, (0, tx))
    b.append(
        f'<rect x="{tx:.1f}" y="{y - size + 2}" width="{cw:.1f}" height="{size + 2}" fill="{BLUE2}">'
        + anim("x", cursor_pts, total)
        + '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" repeatCount="indefinite"/>'
        "</rect>"
    )

    # Rain band + slow scanline
    b.append('<line x1="40" y1="438" x2="960" y2="438" stroke="#fff" stroke-opacity=".08"/>')
    b.append(f'<g mask="url(#rainmask)">{rain(0, 438, W, 62, "rc", cols=60, seed=82)}</g>')
    b.append(
        f'<rect x="0" y="-120" width="{W}" height="120" fill="url(#scan)">'
        f'<animate attributeName="y" values="-120;{H}" dur="7s" repeatCount="indefinite"/></rect>'
    )
    return svg(W, H, "".join(b), "WESTIE · Full Stack · Web3 · Machine Learning")


# ---------------------------------------------------------------------------- whoami terminal


def whoami():
    W, H = 1000, 406
    b = [grid_bg(W, H, op=0.03)]
    px, py, pw, ph = 20, 16, 960, 372
    b.append(panel(px, py, pw, ph, "01", "OPERATOR PROFILE", "STATUS · SHIPPING"))

    size, cw, lh = 15, 9.0, 27
    x = 48
    y0 = py + 36 + 40
    host = "will@d6sc"
    script = [
        ("cmd", "whoami"),
        ("out", "westie · full-stack developer · web3 · machine learning"),
        ("cmd", "cat roles.txt"),
        ("out", "ceo / coo @ d6sc · ceo / coo @ openturn · lead dev / partner @ betalytics"),
        ("cmd", "cat focus.txt"),
        ("out", "sports betting models · prediction markets · real-time sports data"),
        ("cmd", "ls ./leagues"),
        ("out", "MLB · NBA · NFL · NHL · WNBA · NCAAF · NCAAB · FIFA"),
        ("cmd", "./edge --scan today --books all"),
        ("edge", "scanning lines across the sportsbooks ........"),
        ("prompt", ""),
    ]
    total = 20.0
    t = 0.6
    plen = len(host) + 4  # "will@d6sc:~$ "
    cursor_pts = [(0, x + plen * cw)]
    cursor_y_pts = [(0, y0)]
    for i, (kind, text) in enumerate(script):
        y = y0 + i * lh
        show = [(0, 0), (t, 1), (total - 0.4, 0)]
        if kind in ("cmd", "prompt"):
            b.append(
                f'<text class="m" x="{x}" y="{y}" font-size="{size}" fill="{BLUE2}" opacity="0">{host}'
                f'<tspan fill="{MUTED}">:~$</tspan>' + anim("opacity", show, total) + "</text>"
            )
            tx = x + plen * cw
            cursor_y_pts.append((t, y))
            if kind == "cmd":
                n = len(text)
                tdur = n * 0.055
                pts = [(0, 0)]
                for k in range(n + 1):
                    tk = t + 0.25 + tdur * k / n
                    pts.append((tk, k * cw + (cw if k == n else 0)))
                    cursor_pts.append((tk, tx + k * cw))
                pts.append((total - 0.4, 0))
                b.append(
                    f'<clipPath id="wc{i}"><rect x="{tx:.1f}" y="{y - size}" height="{size * 1.6}" width="0">'
                    + anim("width", pts, total)
                    + "</rect></clipPath>"
                    f'<text class="m" x="{tx:.1f}" y="{y}" font-size="{size}" fill="{WHITE}" clip-path="url(#wc{i})">'
                    f"{escape(text)}</text>"
                )
                t += 0.25 + tdur + 0.35
            else:
                cursor_pts.append((t, tx))
        else:
            cursor_y_pts.append((t, -100))  # hide cursor while output prints
            body = escape(text)
            extra = ""
            if kind == "edge":
                extra = (
                    f'<tspan fill="{GREEN}" font-weight="700"> [ EDGE FOUND ]'
                    '<animate attributeName="fill-opacity" values="1;1;.25;1" keyTimes="0;.6;.8;1" dur="1.2s" '
                    'repeatCount="indefinite"/></tspan>'
                )
            b.append(
                f'<text class="m" x="{x}" y="{y}" font-size="{size}" fill="#C9CDD3" opacity="0">'
                f'<tspan fill="{MUTED}">› </tspan>{body}{extra}' + anim("opacity", show, total) + "</text>"
            )
            t += 0.5
    cursor_pts.append((total - 0.4, x + plen * cw))
    cursor_y_pts.append((total - 0.4, y0))
    # The cursor's y follows the active prompt line
    cy_pts = [(tt, (yy - size + 2) if yy > 0 else -100) for tt, yy in cursor_y_pts]
    b.append(
        f'<rect x="{x + plen * cw:.1f}" y="{y0 - size + 2}" width="{cw:.1f}" height="{size + 2}" fill="{BLUE2}">'
        + anim("x", cursor_pts, total)
        + anim("y", cy_pts, total)
        + '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" repeatCount="indefinite"/>'
        "</rect>"
    )
    return svg(W, H, "".join(b), "whoami: Westie, CEO/COO of D6SC and OpenTurn, lead developer and partner at Betalytics")


# ---------------------------------------------------------------------------- stats strip


def stats():
    W, H = 1000, 128
    b = [grid_bg(W, H, op=0.03)]
    px, py, pw, ph = 20, 14, 960, 98
    b.append(
        f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="#000" stroke="#fff" stroke-opacity=".22"/>'
        + ticks(px, py, pw, ph)
    )
    cells = [
        ("11K+", "CONTRIBUTIONS · LAST 12 MO", BLUE2),
        ("50+", "REPOSITORIES", WHITE),
        ("08", "LEAGUES MODELED", WHITE),
        ("10", "PRODUCTS SHIPPED", WHITE),
    ]
    cw = pw / len(cells)
    for i, (num, label, color) in enumerate(cells):
        cx = px + cw * i + cw / 2
        if i:
            b.append(
                f'<line x1="{px + cw * i}" y1="{py + 18}" x2="{px + cw * i}" y2="{py + ph - 18}" '
                'stroke="#fff" stroke-opacity=".1"/>'
            )
        b.append(
            f'<text class="d" x="{cx}" y="{py + 54}" font-size="38" font-weight="600" fill="{color}" '
            f'text-anchor="middle" letter-spacing="2">{num}</text>'
            f'<text class="m" x="{cx + 1}" y="{py + 78}" font-size="10.5" fill="{MUTED}" text-anchor="middle" '
            f'letter-spacing="2.5">{label}</text>'
        )
    return svg(W, H, "".join(b), "11K+ contributions in the last 12 months · 50+ repositories · 8 leagues · 10 products shipped")


# ---------------------------------------------------------------------------- family of companies


def logo_d6sc(cx, ly):
    return (
        f'<text class="d" x="{cx}" y="{ly + 12}" font-size="40" font-weight="700" fill="{WHITE}" '
        'text-anchor="middle" letter-spacing="1">D6SC</text>'
    )


def logo_betalytics(cx, ly):
    # amber "Bet" + blue "alytics", as on betalytics.com
    return (
        f'<text class="s" x="{cx}" y="{ly + 10}" font-size="30" font-weight="700" text-anchor="middle" '
        'letter-spacing="-0.5"><tspan fill="#FBBF24">Bet</tspan><tspan fill="#5DADE2">alytics</tspan></text>'
    )


def logo_openturn(cx, ly):
    # ring + turn mark from openturn.ca, then the wordmark
    ox = cx - 78
    return (
        f'<svg x="{ox}" y="{ly - 18}" width="32" height="32" viewBox="18 18 72 72" fill="none" stroke-linecap="round">'
        '<path d="M76.16,57.91 A22.5,22.5 0 1,1 50.09,31.84" stroke="#48B0AA" stroke-width="11.4"/>'
        '<path d="M64.56,34.13 A22.5,22.5 0 0,1 73.87,43.44" stroke="#F2A462" stroke-width="9.6"/></svg>'
        f'<text class="s" x="{ox + 42}" y="{ly + 8}" font-size="25" font-weight="700" fill="{WHITE}" '
        'letter-spacing="-0.6">OpenTurn</text>'
    )


def logo_algobets(cx, ly):
    # blue-bordered badge, ALGO in blue, BETS in white
    return (
        f'<rect x="{cx - 76}" y="{ly - 24}" width="152" height="46" fill="#000" stroke="{BLUE}" stroke-width="2"/>'
        f'<text class="d" x="{cx}" y="{ly + 8}" font-size="23" font-weight="700" text-anchor="middle" '
        f'letter-spacing="0.5"><tspan fill="{BLUE}">ALGO</tspan><tspan fill="{WHITE}">BETS</tspan></text>'
    )


def logo_adblade(cx, ly):
    # blade chevron + wordmark
    ax = cx - 78
    return (
        f'<g transform="translate({ax},{ly - 16})" fill="none" stroke="#C9CDD3" stroke-width="2.4" '
        'stroke-linejoin="miter"><path d="M0 30 L15 2 L30 30"/><path d="M9 30 L15 18 L21 30" stroke="#fff"/></g>'
        f'<text class="s" x="{ax + 40}" y="{ly + 13}" font-size="23" font-weight="600" fill="{WHITE}" '
        f'letter-spacing="-0.3">AdBlade<tspan font-size="15" font-weight="600" fill="#C9CDD3">.AI</tspan></text>'
    )


def logo_datastreak(cx, ly):
    # logomark from datastreak.com + wordmark + dot
    dx = cx - 84
    return (
        f'<g transform="translate({dx},{ly - 14}) scale(.9)" fill="none" stroke="{GREEN}" stroke-width="2.2">'
        '<rect x="2" y="2" width="28" height="28" rx="6"/>'
        '<path d="M8 22L12 14L16 18L20 10L24 16" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<circle cx="12" cy="14" r="2" fill="{GREEN}"/><circle cx="16" cy="18" r="2" fill="{GREEN}"/>'
        f'<circle cx="20" cy="10" r="2" fill="{GREEN}"/></g>'
        f'<text class="s" x="{dx + 38}" y="{ly + 9}" font-size="21" font-weight="700" fill="{WHITE}" '
        'letter-spacing="-0.4">DataStreak</text>'
        f'<circle cx="{dx + 160}" cy="{ly + 6}" r="3" fill="{GREEN}"/>'
    )


def family():
    W, H = 1000, 366
    b = [grid_bg(W, H, op=0.03)]
    px, py, pw, ph = 20, 16, 960, 330
    b.append(panel(px, py, pw, ph, "02", "FAMILY OF COMPANIES", "06 ACTIVE"))
    cols = [200, 500, 800]
    rows = [
        # (label y, logo y, divider top, divider bottom, cells)
        (py + 80, py + 124, py + 56, py + 194, [
            ("QUANT SPORTS · AD TECH", logo_d6sc, "CEO · COO"),
            ("SPORTS BETTING INTELLIGENCE", logo_betalytics, "LEAD DEVELOPER · PARTNER"),
            ("DEAF-LED CALLING · CANADA", logo_openturn, "CEO · COO"),
        ]),
        (py + 244, py + 290, py + 220, py + ph - 16, [
            ("SPORTS BETTING MODELS", logo_algobets, None),
            ("ADVERTISING INTELLIGENCE", logo_adblade, None),
            ("SPORTS ANALYTICS PLATFORM", logo_datastreak, None),
        ]),
    ]
    b.append(f'<line x1="{px}" y1="{py + 206}" x2="{px + pw}" y2="{py + 206}" stroke="#fff" stroke-opacity=".1"/>')
    for label_y, logo_y, top, bottom, cells in rows:
        for i in (1, 2):
            x = px + pw / 3 * i
            b.append(f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bottom}" stroke="#fff" stroke-opacity=".1"/>')
        for cx, (label, logo, role) in zip(cols, cells):
            b.append(
                f'<text class="m" x="{cx + 1}" y="{label_y}" font-size="10" fill="{MUTED}" text-anchor="middle" '
                f'letter-spacing="2.5">{label}</text>'
            )
            b.append(logo(cx, logo_y))
            if role:
                rw = len(role) * 8.4 + 34
                b.append(
                    f'<rect x="{cx - rw / 2:.1f}" y="{logo_y + 32}" width="{rw:.1f}" height="28" fill="{BLUE}" '
                    f'fill-opacity=".14" stroke="{BLUE2}" stroke-opacity=".7"/>'
                    f'<text class="m" x="{cx + 1}" y="{logo_y + 50}" font-size="11" font-weight="700" fill="{BLUE2}" '
                    f'text-anchor="middle" letter-spacing="2.5">{escape(role)}</text>'
                )
    return svg(
        W, H, "".join(b),
        "Family of companies: D6SC (CEO/COO) · Betalytics (lead developer, partner) · OpenTurn (CEO/COO) · "
        "AlgoBets · AdBlade AI · DataStreak",
    )


# ---------------------------------------------------------------------------- section bar


def section(num, label, right):
    W, H = 1000, 60
    b = [
        f'<rect width="{W}" height="{H}" fill="#000"/>',
        f'<rect x="20" y="12" width="960" height="36" fill="#000" stroke="#fff" stroke-opacity=".22"/>',
        ticks(20, 12, 960, 36, ln=10, off=5),
        f'<rect x="38" y="27" width="6" height="6" fill="{BLUE2}"/>',
        f'<text class="m" x="54" y="34" font-size="11" font-weight="700" fill="{WHITE}" letter-spacing="1">{num}</text>',
        f'<text class="m" x="80" y="34" font-size="11" fill="{MUTED}" letter-spacing="3">{escape(label)}</text>',
        f'<text class="m" x="962" y="34" font-size="11" fill="{MUTED}" letter-spacing="3" text-anchor="end">{escape(right)}</text>',
    ]
    return svg(W, H, "".join(b), f"{num} {label}")


# ---------------------------------------------------------------------------- contact panel


def transmit():
    W, H = 1000, 268
    b = [grid_bg(W, H, op=0.03)]
    px, py, pw, ph = 20, 16, 960, 232
    b.append(panel(px, py, pw, ph, "06", "SECURE CHANNEL", "CONTACT"))
    fy = py + 72
    b.append(
        f'<text class="m" x="48" y="{fy}" font-size="10" fill="{MUTED}" letter-spacing="2.5">CHANNEL</text>'
        f'<rect x="48" y="{fy + 10}" width="440" height="42" fill="#000" stroke="#fff" stroke-opacity=".22"/>'
        f'<text class="m" x="64" y="{fy + 36}" font-size="15" fill="{WHITE}">will@d6sc.com</text>'
        f'<rect x="{64 + 13 * 9.0 + 3}" y="{fy + 22}" width="2" height="18" fill="{BLUE2}">'
        '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;.5;.5;1" dur="1s" repeatCount="indefinite"/></rect>'
        f'<text class="m" x="508" y="{fy}" font-size="10" fill="{MUTED}" letter-spacing="2.5">SUBJECT</text>'
        f'<rect x="508" y="{fy + 10}" width="270" height="42" fill="#000" stroke="#fff" stroke-opacity=".22"/>'
        f'<text class="m" x="524" y="{fy + 36}" font-size="14" font-weight="700" fill="{WHITE}">Models · Builds · Deals</text>'
        f'<path d="M754 {fy + 28} l5 5 l5 -5" fill="none" stroke="{MUTED}" stroke-width="1.5"/>'
        f'<rect x="798" y="{fy + 10}" width="154" height="42" fill="#000" stroke="#fff" stroke-width="1.5"/>'
        f'<text class="d" x="876" y="{fy + 37}" font-size="15" font-weight="700" fill="{WHITE}" text-anchor="middle" '
        'letter-spacing="3.5">TRANSMIT</text>'
    )
    ry = fy + 74
    b.append(
        f'<line x1="{px}" y1="{ry}" x2="{px + pw}" y2="{ry}" stroke="#fff" stroke-opacity=".1"/>'
        + rain(px, ry, pw, 50, "rt", cols=64, seed=6, size=11)
        + f'<line x1="{px}" y1="{ry + 50}" x2="{px + pw}" y2="{ry + 50}" stroke="#fff" stroke-opacity=".1"/>'
    )
    by = ry + 50 + 22
    b.append(
        f'<text class="m" x="40" y="{by}" font-size="10" fill="{MUTED}" letter-spacing="2.5">'
        f'<tspan fill="{WHITE}" font-weight="700">CH-82</tspan> · ENCRYPTED</text>'
        f'<circle cx="826" cy="{by - 4}" r="3" fill="{BLUE2}">'
        '<animate attributeName="opacity" values="1;.2;1" dur="1.6s" repeatCount="indefinite"/></circle>'
        f'<text class="m" x="960" y="{by}" font-size="10" fill="{BLUE2}" letter-spacing="2.5" text-anchor="end">LINK SECURE</text>'
    )
    return svg(W, H, "".join(b), "Secure channel: will@d6sc.com")


def footer():
    W, H = 1000, 56
    b = [
        f'<rect width="{W}" height="{H}" fill="#000"/>',
        '<line x1="20" y1="18" x2="980" y2="18" stroke="#fff" stroke-opacity=".12"/>',
        f'<text class="m" x="20" y="42" font-size="10" fill="{MUTED}" letter-spacing="2.5">© 2026 WESTIE · DEEP SIX SPORTS CONSULTING</text>',
        f'<text class="m" x="980" y="42" font-size="10" fill="{MUTED}" letter-spacing="2.5" text-anchor="end">ALL INQUIRIES VIA SECURE CHANNEL</text>',
    ]
    return svg(W, H, "".join(b), "© 2026 Westie · Deep Six Sports Consulting")


# ---------------------------------------------------------------------------- font embedding

FAMILIES = {"m": "JetBrains Mono", "d": "Chakra Petch", "s": "Inter"}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"


def glyph_usage(content):
    """{(family, weight): chars} for every class="m|d|s" text run in the SVG."""
    import xml.etree.ElementTree as ET

    usage = {}

    def walk(el, cls, weight):
        cls = el.get("class", cls)
        weight = el.get("font-weight", weight)
        if cls in FAMILIES and el.text:
            usage.setdefault((FAMILIES[cls], weight), set()).update(el.text)
        for child in el:
            walk(child, cls, weight)
            if cls in FAMILIES and child.tail:
                usage.setdefault((FAMILIES[cls], weight), set()).update(child.tail)

    walk(ET.fromstring(content), None, "400")
    return usage


def font_face(family, weight, chars):
    """Fetch a Google Fonts subset holding only `chars` and return an @font-face rule with it inlined."""
    import base64
    import re
    import subprocess
    import urllib.parse

    def get(u):
        return subprocess.run(["curl", "-fsSL", "-m", "30", "-A", UA, u], capture_output=True, check=True).stdout

    text = "".join(sorted(c for c in chars if c.isprintable() and ord(c) < 0x3000))
    if not text.strip():
        return ""
    url = (
        "https://fonts.googleapis.com/css2?family="
        + urllib.parse.quote(family).replace("%20", "+")
        + f":wght@{weight}&text="
        + urllib.parse.quote(text)
    )
    css = get(url).decode()
    src = re.search(r"url\((https://[^)]+)\)\s*format\('woff2'\)", css)
    if not src:
        raise RuntimeError(f"no woff2 for {family} {weight}")
    data = get(src.group(1))
    return (
        f"@font-face{{font-family:'{family}';font-weight:{weight};font-style:normal;"
        f"src:url(data:font/woff2;base64,{base64.b64encode(data).decode()}) format('woff2')}}"
    )


def embed_fonts(content):
    rules = "".join(font_face(fam, w, chars) for (fam, w), chars in sorted(glyph_usage(content).items()))
    return content.replace("<style>", "<style>" + rules, 1)


def main():
    import sys

    os.makedirs(OUT, exist_ok=True)
    files = {
        "header.svg": header(),
        "whoami.svg": whoami(),
        "stats.svg": stats(),
        "family.svg": family(),
        "sec-03.svg": section("03", "DEPLOYED SYSTEMS", "LIVE IN PRODUCTION"),
        "sec-04.svg": section("04", "ARSENAL", "FULL STACK · DATA · ML"),
        "sec-05.svg": section("05", "TELEMETRY", "LAST 12 MONTHS"),
        "transmit.svg": transmit(),
        "footer.svg": footer(),
    }
    for name, content in files.items():
        if "--no-fonts" not in sys.argv:
            content = embed_fonts(content)
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as f:
            f.write(content)
        print(f"{name:14} {len(content.encode()) / 1024:6.1f} KB")


if __name__ == "__main__":
    main()
