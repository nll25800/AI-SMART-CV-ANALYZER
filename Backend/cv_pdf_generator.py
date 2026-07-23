"""
cv_pdf_generator.py
- Layout 2 colonnes fidèle au template
- Auto-scaling pour remplir toute la page A4
- Espacement augmenté entre traits de section et texte
"""

import io, re
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase.pdfmetrics import stringWidth

C_BG      = colors.white
C_ACCENT  = colors.HexColor("#2c3e6b")
C_LINE    = colors.HexColor("#2c3e6b")
C_BULLET  = colors.HexColor("#2c3e6b")
C_TITLE   = colors.HexColor("#1a1a2e")
C_BODY    = colors.HexColor("#2d2d2d")
C_MUTED   = colors.HexColor("#666680")
C_LIGHT   = colors.HexColor("#f0f0f6")
C_CONTACT = colors.HexColor("#333355")

PW, PH = A4


# ══════════════════════════════════════════════════════════════════════════════
# PARSER
# ══════════════════════════════════════════════════════════════════════════════
def parse_cv(md: str) -> dict:
    data = {
        "name": "", "title": "", "contact": [],
        "profil": "", "savoir_etre": [], "competences": [],
        "langues": [], "experiences": [], "formation": []
    }

    def clean(s):
        return re.sub(r'\*{1,3}', '', s).strip(" #-•·▪➤►→✦▸")

    lines = md.strip().split("\n")
    section = None
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1

        if re.match(r'^# ', line) and not data["name"]:
            data["name"] = clean(line)
            if i < len(lines):
                nxt = lines[i].strip()
                if nxt and not re.search(r'[@|:]', nxt) and not nxt.startswith('#'):
                    data["title"] = clean(nxt)
                    i += 1
            continue

        if re.search(r'(e.?mail|tel[: ]|ville|@|\+33|linkedin)', line, re.I) \
                and not re.match(r'^#{1,3} ', line):
            parts = [clean(p) for p in re.split(r'\|', line) if clean(p)]
            data["contact"].extend(parts)
            continue

        m = re.match(r'^#{1,3} (.+)', line)
        if m:
            sec = clean(m.group(1)).lower()
            if   "profil"    in sec:                               section = "profil"
            elif "savoir"    in sec:                               section = "savoir_etre"
            elif "compét"    in sec or "competence" in sec:        section = "competences"
            elif "langue"    in sec:                               section = "langues"
            elif "expér"     in sec or "experience" in sec:        section = "experiences"
            elif "format"    in sec or "éducation"  in sec \
                 or "education" in sec:                             section = "formation"
            elif not data["title"]:
                data["title"] = clean(m.group(1))
            continue

        if not line: continue
        val = clean(line)
        if not val: continue

        if section == "profil":
            data["profil"] += (" " if data["profil"] else "") + val
        elif section == "savoir_etre":
            data["savoir_etre"].append(val)
        elif section == "competences":
            data["competences"].append(val)
        elif section == "langues":
            data["langues"].append(val)
        elif section == "experiences":
            is_title = (
                re.search(r'(20\d{2}|stage|alternance|cdd|cdi|présent|aujourd|today|mai\.|juin\.|juil\.|août\.)', line, re.I)
                or line.startswith("**") or re.match(r'#{1,4} ', line)
            )
            if is_title:
                data["experiences"].append({"title": val, "bullets": []})
            elif data["experiences"]:
                data["experiences"][-1]["bullets"].append(val)
        elif section == "formation":
            data["formation"].append(val)

    return data


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def wrap(text, max_w, font, size):
    words = str(text).split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if stringWidth(test, font, size) <= max_w:
            cur = test
        else:
            if cur: lines.append(cur)
            cur = w
    if cur: lines.append(cur)
    return lines or [""]


def _placeholder(c, x, y, d):
    c.setFillColor(colors.HexColor("#e0e0ee"))
    c.circle(x + d/2, y + d/2, d/2, fill=1, stroke=0)
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 7)
    c.drawCentredString(x + d/2, y + d/2 - 3, "Photo")


# ══════════════════════════════════════════════════════════════════════════════
# HEIGHT ESTIMATORS  (utilisés pour l'auto-scaling)
# ══════════════════════════════════════════════════════════════════════════════
def _sec_title_h(FS):
    """Hauteur d'un titre de section : texte + gap avant trait + trait + gap après trait."""
    return (FS + 1) + 5 + 1 + 11   # ~18 pt pour FS=8

def _bullet_h(text, max_w, FS):
    n = len(wrap(text, max_w - 12, "Helvetica", FS))
    return n * (FS + 3.5) + 1

def _text_h(text, max_w, font, FS, lh):
    n = len(wrap(text, max_w, font, FS))
    return n * lh

def estimate_left(data, W, FS, LH, SEC_GAP):
    h = 0
    if data["experiences"]:
        h += _sec_title_h(FS)
        for exp in data["experiences"]:
            h += _text_h(exp["title"], W, "Helvetica-Bold", FS + 0.5, LH + 2)
            for b in exp["bullets"]:
                h += _bullet_h(b, W, FS)
            h += SEC_GAP
    if data["formation"]:
        h += _sec_title_h(FS)
        for item in data["formation"]:
            is_d = bool(re.search(r'(master|licence|bachelor|bac\+|ingénieur|doctorat|\d{4})', item, re.I))
            fnt  = "Helvetica-Bold" if is_d else "Helvetica-Oblique"
            fszz = FS if is_d else FS - 0.5
            h += _text_h(item, W, fnt, fszz, LH - 1) + 3
    return h

def estimate_right(data, W, FS, LH, SEC_GAP):
    h = 0
    for key in ["savoir_etre", "competences"]:
        items = data[key]
        if items:
            h += _sec_title_h(FS)
            for item in items:
                h += _bullet_h(item, W, FS)
            h += SEC_GAP
    if data["langues"]:
        h += _sec_title_h(FS)
        for item in data["langues"]:
            h += _text_h(item, W, "Helvetica", FS, LH)
    return h

def estimate_profil(data, W, FS, LH):
    if not data["profil"]: return 0
    return _sec_title_h(FS) + _text_h(data["profil"], W, "Helvetica", FS, LH) + 10


# ══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
def generate_pdf(cv_markdown: str, photo_bytes: bytes = None) -> bytes:
    buf = io.BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)
    data = parse_cv(cv_markdown)

    # ── Constantes layout ─────────────────────────────────────────────────────
    MARGIN    = 22
    HEADER_H  = 88
    CONTACT_H = 22
    PHOTO_D   = 70
    FOOTER_H  = 16
    COL_L_W   = 335
    COL_GAP   = 14
    COL_R_W   = PW - MARGIN * 2 - COL_L_W - COL_GAP
    COL_L_X   = MARGIN
    COL_R_X   = COL_L_X + COL_L_W + COL_GAP
    FULL_W    = PW - MARGIN * 2

    body_top    = PH - HEADER_H - CONTACT_H - 14
    available_h = body_top - FOOTER_H

    # ── Auto-scaling : cherche FS optimal ─────────────────────────────────────
    def total_h(fs):
        lh      = fs + 3.5
        sec_gap = fs * 1.1
        ph = estimate_profil(data, FULL_W, fs, lh)
        lh_ = estimate_left(data, COL_L_W, fs, lh, sec_gap)
        rh_ = estimate_right(data, COL_R_W, fs, lh, sec_gap)
        return ph + max(lh_, rh_)

    lo, hi = 6.5, 11.5
    for _ in range(40):
        mid = (lo + hi) / 2
        if total_h(mid) < available_h:
            lo = mid
        else:
            hi = mid
    FS      = lo * 0.975        # légère marge
    LH      = FS + 3.5
    SEC_GAP = FS * 1.1

    # ── Fond ──────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)

    # ── Header ────────────────────────────────────────────────────────────────
    header_bot = PH - HEADER_H
    c.setStrokeColor(C_LINE)
    c.setLineWidth(1)
    c.line(MARGIN, header_bot, PW - MARGIN, header_bot)

    # Photo
    px = MARGIN
    py = PH - MARGIN - PHOTO_D
    if photo_bytes:
        try:
            pb = io.BytesIO(photo_bytes)
            c.saveState()
            path = c.beginPath()
            path.circle(px + PHOTO_D/2, py + PHOTO_D/2, PHOTO_D/2)
            c.clipPath(path, stroke=0, fill=0)
            c.drawImage(pb, px, py, PHOTO_D, PHOTO_D, preserveAspectRatio=True, mask='auto')
            c.restoreState()
        except Exception:
            _placeholder(c, px, py, PHOTO_D)
    else:
        _placeholder(c, px, py, PHOTO_D)

    c.setStrokeColor(C_MUTED)
    c.setLineWidth(1)
    c.circle(px + PHOTO_D/2, py + PHOTO_D/2, PHOTO_D/2, fill=0, stroke=1)

    # Nom + Titre
    nx = px + PHOTO_D + 16
    nw = PW - nx - MARGIN
    ny = PH - MARGIN - 6

    c.setFillColor(C_TITLE)
    c.setFont("Helvetica-Bold", 24)
    for nl in wrap(data["name"].upper(), nw, "Helvetica-Bold", 24):
        c.drawString(nx, ny, nl)
        ny -= 28

    if data["title"]:
        c.setFillColor(C_MUTED)
        c.setFont("Helvetica", 11)
        for tl in wrap(data["title"].upper(), nw, "Helvetica", 11):
            c.drawString(nx, ny, tl)
            ny -= 14

    # ── Contact ───────────────────────────────────────────────────────────────
    cy_top = header_bot
    c.setFillColor(C_LIGHT)
    c.rect(0, cy_top - CONTACT_H, PW, CONTACT_H, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#ccccdd"))
    c.setLineWidth(0.5)
    c.line(0, cy_top - CONTACT_H, PW, cy_top - CONTACT_H)

    if data["contact"]:
        c.setFillColor(C_CONTACT)
        c.setFont("Helvetica", 8)
        cs = "  |  ".join(data["contact"])
        tw = stringWidth(cs, "Helvetica", 8)
        c.drawString((PW - tw) / 2, cy_top - CONTACT_H + 7, cs)

    # ── Helpers de dessin ─────────────────────────────────────────────────────
    def draw_sec_title(title, x, y, w):
        """Titre section : texte, puis espace, puis trait, puis espace avant contenu."""
        c.setFillColor(C_ACCENT)
        c.setFont("Helvetica-Bold", FS + 1)
        c.drawString(x, y, title.upper())
        y -= 5                          # espace entre texte et trait
        c.setStrokeColor(C_LINE)
        c.setLineWidth(0.8)
        c.line(x, y, x + w, y)
        y -= 11                         # espace entre trait et premier élément
        return y

    def draw_bullet(text, x, y, max_w, fsize=None):
        fsize = fsize or FS
        if y < FOOTER_H + 4: return y
        c.setFillColor(C_BULLET)
        c.setFont("Helvetica-Bold", fsize)
        c.drawString(x, y, "•")
        c.setFillColor(C_BODY)
        c.setFont("Helvetica", fsize)
        for ln in wrap(text, max_w - 12, "Helvetica", fsize):
            if y < FOOTER_H + 4: break
            c.drawString(x + 10, y, ln)
            y -= (fsize + 3.5)
        return y - 1

    # ── Corps ─────────────────────────────────────────────────────────────────
    my = body_top

    # Profil (pleine largeur)
    if data["profil"]:
        my = draw_sec_title("Profil", MARGIN, my, FULL_W)
        c.setFillColor(C_BODY)
        c.setFont("Helvetica", FS)
        for pl in wrap(data["profil"], FULL_W, "Helvetica", FS):
            if my < FOOTER_H + 4: break
            c.drawString(MARGIN, my, pl)
            my -= LH
        my -= 10

    left_y  = my
    right_y = my

    # ── COL GAUCHE : Expériences ───────────────────────────────────────────────
    if data["experiences"]:
        left_y = draw_sec_title("Expériences", COL_L_X, left_y, COL_L_W)
        for exp in data["experiences"]:
            if left_y < FOOTER_H + 4: break
            title_str = exp["title"]
            c.setFillColor(C_TITLE)
            c.setFont("Helvetica-Bold", FS + 0.5)
            date_m = re.search(r'(\d{4}.+)$', title_str)
            if date_m:
                pos_t  = title_str[:date_m.start()].strip(" –-")
                date_t = date_m.group(1).strip()
                c.drawString(COL_L_X, left_y, pos_t)
                dw = stringWidth(date_t, "Helvetica-Bold", FS + 0.5)
                c.drawString(COL_L_X + COL_L_W - dw, left_y, date_t)
                left_y -= LH + 2
            else:
                for el in wrap(title_str, COL_L_W, "Helvetica-Bold", FS + 0.5):
                    if left_y < FOOTER_H + 4: break
                    c.drawString(COL_L_X, left_y, el)
                    left_y -= LH + 2
            for b in exp["bullets"]:
                if left_y < FOOTER_H + 4: break
                left_y = draw_bullet(b, COL_L_X + 2, left_y, COL_L_W - 4)
            left_y -= SEC_GAP

    # ── COL GAUCHE : Formation ─────────────────────────────────────────────────
    if data["formation"]:
        left_y = draw_sec_title("Formation", COL_L_X, left_y, COL_L_W)
        for item in data["formation"]:
            if left_y < FOOTER_H + 4: break
            is_d  = bool(re.search(r'(master|licence|bachelor|bac\+|ingénieur|doctorat|\d{4})', item, re.I))
            fname = "Helvetica-Bold" if is_d else "Helvetica-Oblique"
            fsize = FS if is_d else FS - 0.5
            c.setFillColor(C_TITLE if is_d else C_MUTED)
            c.setFont(fname, fsize)
            for fl in wrap(item, COL_L_W, fname, fsize):
                if left_y < FOOTER_H + 4: break
                c.drawString(COL_L_X, left_y, fl)
                left_y -= LH - 1
            left_y -= 3

    # ── COL DROITE : Savoir-être ───────────────────────────────────────────────
    if data["savoir_etre"]:
        right_y = draw_sec_title("Savoir-Être", COL_R_X, right_y, COL_R_W)
        for item in data["savoir_etre"]:
            if right_y < FOOTER_H + 4: break
            right_y = draw_bullet(item, COL_R_X, right_y, COL_R_W)
        right_y -= SEC_GAP

    # ── COL DROITE : Compétences ───────────────────────────────────────────────
    if data["competences"]:
        right_y = draw_sec_title("Compétences", COL_R_X, right_y, COL_R_W)
        for item in data["competences"]:
            if right_y < FOOTER_H + 4: break
            right_y = draw_bullet(item, COL_R_X, right_y, COL_R_W)
        right_y -= SEC_GAP

    # ── COL DROITE : Langues ───────────────────────────────────────────────────
    if data["langues"]:
        right_y = draw_sec_title("Langues", COL_R_X, right_y, COL_R_W)
        for item in data["langues"]:
            if right_y < FOOTER_H + 4: break
            c.setFillColor(C_BODY)
            c.setFont("Helvetica", FS)
            for ll in wrap(item, COL_R_W, "Helvetica", FS):
                c.drawString(COL_R_X, right_y, ll)
                right_y -= LH

    # ── Séparateur vertical ───────────────────────────────────────────────────
    sep_bot = min(left_y, right_y) - 8
    c.setStrokeColor(colors.HexColor("#ddddee"))
    c.setLineWidth(0.5)
    c.line(COL_R_X - 7, my, COL_R_X - 7, sep_bot)

    # ── Footer ────────────────────────────────────────────────────────────────
    c.setFillColor(C_MUTED)
    c.setFont("Helvetica", 6)
    c.drawCentredString(PW / 2, 8, "CV généré par CV.AI — Expert Optimizer")

    c.save()
    buf.seek(0)
    return buf.read()