"""
cv_pdf_generator.py
- Consomme directement un dict conforme au schéma CVData (voir cv_schema.py)
- Layout 2 colonnes fidèle au template
- Auto-scaling pour remplir toute la page A4
"""

import io
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab

# ── Polices embarquées ───────────────────────────────────────────────────────
# On utilise les polices Vera (Bitstream Vera Sans) fournies avec reportlab
# lui-même, plutôt que les polices standard F_REGULAR non embarquées.
# Raison : les polices standard PDF ne sont pas intégrées au fichier — leur
# rendu dépend des polices installées sur la machine qui ouvre le PDF, ce qui
# peut faire disparaître le texte (notamment les caractères accentués
# français) sur certains lecteurs. Vera est embarquée directement dans le PDF,
# donc le rendu est identique partout.
_FONT_DIR = os.path.join(os.path.dirname(reportlab.__file__), "fonts")
pdfmetrics.registerFont(TTFont("Vera", os.path.join(_FONT_DIR, "Vera.ttf")))
pdfmetrics.registerFont(TTFont("Vera-Bold", os.path.join(_FONT_DIR, "VeraBd.ttf")))
pdfmetrics.registerFont(TTFont("Vera-Italic", os.path.join(_FONT_DIR, "VeraIt.ttf")))
pdfmetrics.registerFont(TTFont("Vera-BoldItalic", os.path.join(_FONT_DIR, "VeraBI.ttf")))

F_REGULAR      = "Vera"
F_BOLD         = "Vera-Bold"
F_ITALIC       = "Vera-Italic"
F_BOLD_ITALIC  = "Vera-BoldItalic"

C_BG      = colors.white
C_ACCENT  = colors.HexColor("#2c3e6b")
C_LINE    = colors.HexColor("#2c3e6b")
C_BULLET  = colors.HexColor("#2c3e6b")
C_TITLE   = colors.HexColor("#1a1a2e")
C_BODY    = colors.HexColor("#2d2d2d")
C_MUTED   = colors.HexColor("#666680")
C_LIGHT   = colors.HexColor("#f0f0f6")
C_CONTACT = colors.HexColor("#333355")
C_WARN    = colors.HexColor("#b5442e")

PW, PH = A4
MIN_FS = 8.0  # plancher de police lisible — en dessous, on tronque plutôt que de continuer à rétrécir


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
    c.setFont(F_REGULAR, 7)
    c.drawCentredString(x + d/2, y + d/2 - 3, "Photo")


def _exp_title_line(exp: dict) -> str:
    """Combine poste + entreprise en une ligne, pour l'affichage et l'estimation de hauteur."""
    poste = exp.get("poste", "")
    entreprise = exp.get("entreprise")
    return f"{poste} — {entreprise}" if entreprise else poste


# ══════════════════════════════════════════════════════════════════════════════
# HEIGHT ESTIMATORS  (utilisés pour l'auto-scaling)
# ══════════════════════════════════════════════════════════════════════════════
def _sec_title_h(FS):
    return (FS + 1) + 9 + 1 + 21

def _bullet_h(text, max_w, FS, line_h=None):
    line_h = line_h if line_h is not None else (FS + 3.5)
    n = len(wrap(text, max_w - 12, F_REGULAR, FS))
    return n * line_h + 1

def _text_h(text, max_w, font, FS, lh):
    n = len(wrap(text, max_w, font, FS))
    return n * lh

def estimate_left(data, W, FS, LH, SEC_GAP):
    h = 0
    if data.get("experiences"):
        h += _sec_title_h(FS)
        for exp in data["experiences"]:
            h += _text_h(_exp_title_line(exp), W, F_BOLD, FS + 0.5, LH + 2)
            for b in exp.get("bullets", []):
                h += _bullet_h(b, W, FS, line_h=LH)
            h += SEC_GAP
    return h

def estimate_right(data, W, FS, LH, SEC_GAP):
    h = 0
    if data.get("savoir_etre"):
        h += _sec_title_h(FS)
        for item in data["savoir_etre"]:
            h += _bullet_h(item, W, FS, line_h=LH)
        h += SEC_GAP
    if data.get("competences"):
        h += _sec_title_h(FS)
        for cat in data["competences"]:
            h += _text_h(cat.get("categorie", ""), W, F_BOLD, FS, LH - 1) + 2
            items_line = ", ".join(cat.get("items", []))
            h += _text_h(items_line, W, F_REGULAR, FS, LH) + 5
        h += SEC_GAP
    if data.get("langues"):
        h += _sec_title_h(FS)
        for item in data["langues"]:
            h += _text_h(item, W, F_REGULAR, FS, LH)
    return h

def estimate_profil(data, W, FS, LH):
    if not data.get("profil"): return 0
    return _sec_title_h(FS) + _text_h(data["profil"], W, F_REGULAR, FS, LH) + 10

def estimate_formation_full(data, W, FS, LH):
    if not data.get("formation"): return 0
    h = _sec_title_h(FS)
    for item in data["formation"]:
        h += _text_h(item.get("diplome", ""), W, F_BOLD, FS, LH - 1) + 3
        sub = item.get("etablissement") or ""
        if item.get("date"):
            sub = f"{sub} | {item['date']}" if sub else item["date"]
        if sub:
            h += _text_h(sub, W, F_ITALIC, FS - 0.5, LH - 1) + 3
        h += 6
    return h


# ══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATOR
# ══════════════════════════════════════════════════════════════════════════════
def generate_pdf(cv_data: dict, photo_bytes: bytes = None) -> bytes:
    """
    cv_data : dict conforme au schéma CVData (typiquement cv_data_obj.model_dump()).
    """
    buf = io.BytesIO()
    c   = rl_canvas.Canvas(buf, pagesize=A4)
    data = cv_data

    # ── Constantes layout ─────────────────────────────────────────────────────
    MARGIN    = 22
    HEADER_H  = 100
    CONTACT_H = 22
    PHOTO_D   = 88
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
        fh = estimate_formation_full(data, FULL_W, fs, lh)
        return ph + max(lh_, rh_) + fh

    lo, hi = MIN_FS, 11.5
    for _ in range(40):
        mid = (lo + hi) / 2
        if total_h(mid) < available_h:
            lo = mid
        else:
            hi = mid
    FS      = lo * 0.975

    # ── Étirement des espacements pour remplir la page ─────────────────────────
    # La recherche ci-dessus choisit la plus grande police qui TIENT, mais si
    # le contenu est plus court que la page (CV avec peu de rubriques), il
    # reste un vide en bas plutôt que d'utiliser tout l'espace. On étire donc
    # l'interligne et les espaces entre sections (jamais la police elle-même,
    # pour ne pas casser l'équilibre visuel du texte) jusqu'à occuper l'espace
    # disponible, avec un plafond pour éviter des espacements grotesques.
    def total_h_stretched(fs, stretch):
        lh      = (fs + 3.5) * stretch
        sec_gap = fs * 1.1 * stretch
        ph  = estimate_profil(data, FULL_W, fs, lh)
        lh_ = estimate_left(data, COL_L_W, fs, lh, sec_gap)
        rh_ = estimate_right(data, COL_R_W, fs, lh, sec_gap)
        fh  = estimate_formation_full(data, FULL_W, fs, lh)
        return ph + max(lh_, rh_) + fh

    slo, shi = 1.0, 1.6
    for _ in range(30):
        smid = (slo + shi) / 2
        if total_h_stretched(FS, smid) < available_h:
            slo = smid
        else:
            shi = smid
    STRETCH = slo

    LH      = (FS + 3.5) * STRETCH
    SEC_GAP = FS * 1.1 * STRETCH

    # ── Équilibrage gauche/droite ────────────────────────────────────────────
    # STRETCH ci-dessus est calé sur la colonne la PLUS LONGUE (celle qui
    # détermine le remplissage de la page). Mais si une colonne est bien plus
    # courte que l'autre (ex: peu d'expériences, beaucoup de compétences),
    # elle se termine très haut sur la page, laissant un grand vide avant la
    # section Formation qui doit attendre la fin des DEUX colonnes. On calcule
    # donc un étirement supplémentaire, propre à la colonne la plus courte,
    # pour que les deux colonnes se terminent à peu près à la même hauteur.
    base_lh      = FS + 3.5
    base_sec_gap = FS * 1.1
    lh_est = estimate_left(data, COL_L_W, FS, base_lh, base_sec_gap)
    rh_est = estimate_right(data, COL_R_W, FS, base_lh, base_sec_gap)
    target_col_h = max(lh_est, rh_est) * STRETCH

    def _col_stretch(est):
        if est <= 1:
            return STRETCH
        s = target_col_h / est
        return max(STRETCH, min(s, 2.2))  # jamais moins que l'étirement global, plafonné pour rester lisible

    STRETCH_L = _col_stretch(lh_est)
    STRETCH_R = _col_stretch(rh_est)
    LH_L      = (FS + 3.5) * STRETCH_L
    SEC_GAP_L = FS * 1.1 * STRETCH_L
    LH_R      = (FS + 3.5) * STRETCH_R
    SEC_GAP_R = FS * 1.1 * STRETCH_R

    # ── Fond ──────────────────────────────────────────────────────────────────
    c.setFillColor(C_BG)
    c.rect(0, 0, PW, PH, fill=1, stroke=0)

    # ── Header ────────────────────────────────────────────────────────────────
    header_bot = PH - HEADER_H
    c.setStrokeColor(C_LINE)
    c.setLineWidth(1)
    c.line(MARGIN, header_bot, PW - MARGIN, header_bot)

    px = MARGIN
    py = PH - MARGIN - PHOTO_D
    photo_drawn = False
    if photo_bytes:
        c.saveState()
        try:
            # IMPORTANT : on passe par ImageReader plutôt qu'un io.BytesIO brut.
            # Avec mask='auto', reportlab a besoin de déterminer le format de
            # l'image (pour gérer la transparence), et sa logique interne
            # attend un objet avec un nom de fichier/extension exploitable.
            # Un BytesIO nu fait planter drawImage avec :
            # "TypeError: expected str, bytes or os.PathLike object, not BytesIO"
            # ImageReader encapsule proprement n'importe quelle source d'image.
            pb = ImageReader(io.BytesIO(photo_bytes))
            path = c.beginPath()
            path.circle(px + PHOTO_D/2, py + PHOTO_D/2, PHOTO_D/2)
            c.clipPath(path, stroke=0, fill=0)
            c.drawImage(pb, px, py, PHOTO_D, PHOTO_D, preserveAspectRatio=True, mask='auto')
            photo_drawn = True
        except Exception as e:
            print(f"[PDF] Échec du dessin de la photo : {type(e).__name__}: {e}")
            photo_drawn = False
        finally:
            # CRITIQUE : on restaure TOUJOURS l'état du canvas (referme le clip
            # circulaire), que le dessin de la photo ait réussi ou échoué.
            # Sans ce finally, une exception dans drawImage laissait le clip
            # actif pour tout le reste de la page -> tout le contenu suivant
            # devenait invisible (visible uniquement dans le petit cercle).
            c.restoreState()
    if not photo_drawn:
        _placeholder(c, px, py, PHOTO_D)

    c.setStrokeColor(C_MUTED)
    c.setLineWidth(1)
    c.circle(px + PHOTO_D/2, py + PHOTO_D/2, PHOTO_D/2, fill=0, stroke=1)

    nx = px + PHOTO_D + 20
    nw = PW - nx - MARGIN
    ny = PH - MARGIN - 8

    c.setFillColor(C_TITLE)
    c.setFont(F_BOLD, 24)
    name_lines = wrap((data.get("name") or "").upper(), nw, F_BOLD, 24)
    for i, nl in enumerate(name_lines):
        c.drawString(nx, ny, nl)
        ny -= 26
    ny += 9  # réduit l'écart avant le sous-titre : les 26pt de retrait sont
             # calibrés pour enchaîner deux lignes de nom, pas pour l'espace
             # qui précède le sous-titre — sans ce correctif l'écart paraît trop grand

    if data.get("title"):
        c.setFillColor(C_MUTED)
        c.setFont(F_REGULAR, 11)
        for tl in wrap(data["title"].upper(), nw, F_REGULAR, 11):
            c.drawString(nx, ny, tl)
            ny -= 14

    # ── Contact ───────────────────────────────────────────────────────────────
    cy_top = header_bot
    c.setFillColor(C_LIGHT)
    c.rect(0, cy_top - CONTACT_H, PW, CONTACT_H, fill=1, stroke=0)
    c.setStrokeColor(colors.HexColor("#ccccdd"))
    c.setLineWidth(0.5)
    c.line(0, cy_top - CONTACT_H, PW, cy_top - CONTACT_H)

    if data.get("contact"):
        c.setFillColor(C_CONTACT)
        c.setFont(F_REGULAR, 8)
        cs = "  |  ".join(data["contact"])
        tw = stringWidth(cs, F_REGULAR, 8)
        c.drawString((PW - tw) / 2, cy_top - CONTACT_H + 7, cs)

    # ── Helpers de dessin ─────────────────────────────────────────────────────
    def draw_sec_title(title, x, y, w):
        c.setFillColor(C_ACCENT)
        c.setFont(F_BOLD, FS + 1)
        c.drawString(x, y, title.upper())
        y -= 9
        c.setStrokeColor(C_LINE)
        c.setLineWidth(0.8)
        c.line(x, y, x + w, y)
        y -= 21
        return y

    def draw_bullet(text, x, y, max_w, fsize=None, line_h=None):
        fsize = fsize or FS
        line_h = line_h if line_h is not None else (fsize + 3.5)
        if y < FOOTER_H + 4: return y
        c.setFillColor(C_BULLET)
        c.setFont(F_BOLD, fsize)
        c.drawString(x, y, "•")
        c.setFillColor(C_BODY)
        c.setFont(F_REGULAR, fsize)
        for ln in wrap(text, max_w - 12, F_REGULAR, fsize):
            if y < FOOTER_H + 4: break
            c.drawString(x + 10, y, ln)
            y -= line_h
        return y - 1

    # ── Corps ─────────────────────────────────────────────────────────────────
    my = body_top

    if data.get("profil"):
        my = draw_sec_title("Profil", MARGIN, my, FULL_W)
        c.setFillColor(C_BODY)
        c.setFont(F_REGULAR, FS)
        for pl in wrap(data["profil"], FULL_W, F_REGULAR, FS):
            if my < FOOTER_H + 4: break
            c.drawString(MARGIN, my, pl)
            my -= LH
        my -= 10

    left_y  = my
    right_y = my
    # Suit si du contenu a dû être coupé faute de place, colonne par colonne,
    # pour pouvoir afficher un avertissement visible plutôt que de perdre
    # l'info silencieusement.
    truncated = {"left": False, "right": False, "bottom": False}

    # ── COL GAUCHE : Expériences ───────────────────────────────────────────────
    if data.get("experiences"):
        left_y = draw_sec_title("Expériences", COL_L_X, left_y, COL_L_W)
        for exp in data["experiences"]:
            if left_y < FOOTER_H + 4:
                truncated["left"] = True
                break
            title_str = exp.get("poste", "")
            entreprise = exp.get("entreprise")
            dates = exp.get("dates")

            c.setFillColor(C_TITLE)
            c.setFont(F_BOLD, FS + 0.5)
            pos_t = f"{title_str} — {entreprise}" if entreprise else title_str
            if dates:
                dw = stringWidth(dates, F_BOLD, FS + 0.5)
                # Si le poste+entreprise est trop long pour laisser la place à la date, on wrap le poste seul
                if stringWidth(pos_t, F_BOLD, FS + 0.5) > COL_L_W - dw - 8:
                    for el in wrap(pos_t, COL_L_W, F_BOLD, FS + 0.5):
                        if left_y < FOOTER_H + 4:
                            truncated["left"] = True
                            break
                        c.drawString(COL_L_X, left_y, el)
                        left_y -= LH_L + 2
                    c.drawString(COL_L_X + COL_L_W - dw, left_y + LH_L + 2, dates)
                else:
                    c.drawString(COL_L_X, left_y, pos_t)
                    c.drawString(COL_L_X + COL_L_W - dw, left_y, dates)
                    left_y -= LH_L + 2
            else:
                for el in wrap(pos_t, COL_L_W, F_BOLD, FS + 0.5):
                    if left_y < FOOTER_H + 4:
                        truncated["left"] = True
                        break
                    c.drawString(COL_L_X, left_y, el)
                    left_y -= LH_L + 2

            for b in exp.get("bullets", []):
                if left_y < FOOTER_H + 4:
                    truncated["left"] = True
                    break
                left_y = draw_bullet(b, COL_L_X + 2, left_y, COL_L_W - 4, line_h=LH_L)
            left_y -= SEC_GAP_L

    # (Formation déplacée en pleine largeur en bas de page — voir plus loin)

    # ── COL DROITE : Savoir-être ───────────────────────────────────────────────
    if data.get("savoir_etre"):
        right_y = draw_sec_title("Savoir-Être", COL_R_X, right_y, COL_R_W)
        for item in data["savoir_etre"]:
            if right_y < FOOTER_H + 4:
                truncated["right"] = True
                break
            right_y = draw_bullet(item, COL_R_X, right_y, COL_R_W, line_h=LH_R)
        right_y -= SEC_GAP_R

    # ── COL DROITE : Compétences (par catégorie) ────────────────────────────────
    if data.get("competences"):
        right_y = draw_sec_title("Compétences", COL_R_X, right_y, COL_R_W)
        for cat in data["competences"]:
            if right_y < FOOTER_H + 4:
                truncated["right"] = True
                break
            c.setFillColor(C_TITLE)
            c.setFont(F_BOLD, FS)
            for cl in wrap(cat.get("categorie", ""), COL_R_W, F_BOLD, FS):
                if right_y < FOOTER_H + 4:
                    truncated["right"] = True
                    break
                c.drawString(COL_R_X, right_y, cl)
                right_y -= LH_R - 1
            right_y -= 1
            items_line = ", ".join(cat.get("items", []))
            c.setFillColor(C_BODY)
            c.setFont(F_REGULAR, FS)
            for il in wrap(items_line, COL_R_W, F_REGULAR, FS):
                if right_y < FOOTER_H + 4:
                    truncated["right"] = True
                    break
                c.drawString(COL_R_X, right_y, il)
                right_y -= LH_R
            right_y -= 5
        right_y -= SEC_GAP_R

    # ── COL DROITE : Langues ───────────────────────────────────────────────────
    if data.get("langues"):
        right_y = draw_sec_title("Langues", COL_R_X, right_y, COL_R_W)
        for item in data["langues"]:
            if right_y < FOOTER_H + 4:
                truncated["right"] = True
                break
            c.setFillColor(C_BODY)
            c.setFont(F_REGULAR, FS)
            for ll in wrap(item, COL_R_W, F_REGULAR, FS):
                c.drawString(COL_R_X, right_y, ll)
                right_y -= LH_R

    # ── Séparateur vertical (s'arrête avant Formation, qui est pleine largeur) ──
    col_bottom = min(left_y, right_y)
    sep_bot = col_bottom - 8
    c.setStrokeColor(colors.HexColor("#ddddee"))
    c.setLineWidth(0.5)
    c.line(COL_R_X - 7, my, COL_R_X - 7, sep_bot)

    # ── Formation (pleine largeur, en bas de page, comme le CV de référence) ───
    bottom_y = col_bottom - 16
    if data.get("formation"):
        bottom_y = draw_sec_title("Formation", MARGIN, bottom_y, FULL_W)
        for item in data["formation"]:
            if bottom_y < FOOTER_H + 4:
                truncated["bottom"] = True
                break
            c.setFillColor(C_TITLE)
            c.setFont(F_BOLD, FS)
            for fl in wrap(item.get("diplome", ""), FULL_W, F_BOLD, FS):
                if bottom_y < FOOTER_H + 4:
                    truncated["bottom"] = True
                    break
                c.drawString(MARGIN, bottom_y, fl)
                bottom_y -= LH - 1
            bottom_y -= 2

            sub = item.get("etablissement") or ""
            if item.get("date"):
                sub = f"{sub} | {item['date']}" if sub else item["date"]
            if sub:
                c.setFillColor(C_MUTED)
                c.setFont(F_ITALIC, FS - 0.5)
                for sl in wrap(sub, FULL_W, F_ITALIC, FS - 0.5):
                    if bottom_y < FOOTER_H + 4:
                        truncated["bottom"] = True
                        break
                    c.drawString(MARGIN, bottom_y, sl)
                    bottom_y -= LH - 1
            bottom_y -= 6

    # ── Avertissement de troncature (visible plutôt que silencieux) ────────────
    if truncated["left"]:
        c.setFillColor(C_WARN)
        c.setFont(F_ITALIC, 6.5)
        c.drawString(COL_L_X, FOOTER_H + 3, "⚠ contenu tronqué — page trop dense")
    if truncated["right"]:
        c.setFillColor(C_WARN)
        c.setFont(F_ITALIC, 6.5)
        c.drawString(COL_R_X, FOOTER_H + 3, "⚠ contenu tronqué — page trop dense")
    if truncated["bottom"]:
        c.setFillColor(C_WARN)
        c.setFont(F_ITALIC, 6.5)
        c.drawString(MARGIN, FOOTER_H + 3, "⚠ formation tronquée — page trop dense")

    # ── Footer ────────────────────────────────────────────────────────────────
    c.setFillColor(C_MUTED)
    c.setFont(F_REGULAR, 6)
    c.drawCentredString(PW / 2, 8, "CV généré par CV.AI — Expert Optimizer")

    c.save()
    buf.seek(0)
    return buf.read()