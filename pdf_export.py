"""
Generazione del PDF di riepilogo di un allenamento (pagina "Crea Allenamento"):
una prima pagina con il recap (data, ora, durata, assenti con motivazione,
elenco esercizi svolti) seguita da una pagina per ciascun esercizio con la
sua immagine, se disponibile.
"""
from __future__ import annotations

import datetime as dt
import io

from PIL import Image as PILImage
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image as RLImage,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from helpers import exercise_image_source


def _fit_image(img_source, max_width: float, max_height: float):
    """Apre l'immagine (bytes o percorso file) e restituisce un'Image di reportlab
    scalata per stare dentro max_width x max_height mantenendo le proporzioni.
    Restituisce None se l'immagine non può essere letta."""
    try:
        if isinstance(img_source, (bytes, bytearray)):
            pil_img = PILImage.open(io.BytesIO(img_source))
            source_for_rl = io.BytesIO(img_source)
        else:
            pil_img = PILImage.open(img_source)
            source_for_rl = img_source
        iw, ih = pil_img.size
        if not iw or not ih:
            return None
        scale = min(max_width / iw, max_height / ih)
        return RLImage(source_for_rl, width=iw * scale, height=ih * scale)
    except Exception:
        return None


def _format_data(data_iso: str) -> str:
    try:
        return dt.date.fromisoformat(data_iso).strftime("%d/%m/%Y")
    except Exception:
        return data_iso or ""


def build_training_pdf(
    team_name: str | None,
    training: dict,
    assenti: list[dict],
    esercizi: list[dict],
) -> bytes:
    """Costruisce il PDF di un allenamento e restituisce i byte del file.

    - training: riga della tabella trainings (data, ora, durata_minuti, note)
    - assenti: lista di dict con 'nome_completo' e 'motivo' (può essere vuoto/None)
    - esercizi: righe della tabella exercises usate in quell'allenamento
      (servono categoria, nome, immagine_path/immagine_dati per le immagini)
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story = []

    if team_name:
        story.append(Paragraph(team_name, styles["Heading2"]))
    story.append(Paragraph(f"Allenamento del {_format_data(training.get('data'))}", styles["Title"]))

    dettagli = []
    if training.get("ora"):
        dettagli.append(f"Ora: {training['ora']}")
    if training.get("durata_minuti"):
        dettagli.append(f"Durata: {training['durata_minuti']} minuti")
    if dettagli:
        story.append(Paragraph(" &nbsp;&nbsp;|&nbsp;&nbsp; ".join(dettagli), styles["Normal"]))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph("Assenti", styles["Heading2"]))
    if assenti:
        items = [
            ListItem(
                Paragraph(
                    a["nome_completo"] + (f" — {a['motivo']}" if a.get("motivo") else " — motivo non indicato"),
                    styles["Normal"],
                )
            )
            for a in assenti
        ]
        story.append(ListFlowable(items, bulletType="bullet", leftIndent=12))
    else:
        story.append(Paragraph("Nessun assente: presenti tutti i convocati.", styles["Normal"]))
    story.append(Spacer(1, 0.6 * cm))

    story.append(Paragraph(f"Esercizi svolti ({len(esercizi)})", styles["Heading2"]))
    if esercizi:
        items = [
            ListItem(Paragraph(f"[{e['categoria']}] {e['nome']}", styles["Normal"]))
            for e in esercizi
        ]
        story.append(ListFlowable(items, bulletType="bullet", leftIndent=12))
    else:
        story.append(Paragraph("Nessun esercizio registrato.", styles["Normal"]))

    if training.get("note"):
        story.append(Spacer(1, 0.6 * cm))
        story.append(Paragraph("Note", styles["Heading2"]))
        story.append(Paragraph(training["note"], styles["Normal"]))

    max_w = doc.width
    max_h = doc.height - 2.5 * cm  # spazio riservato al titolo dell'esercizio
    for e in esercizi:
        story.append(PageBreak())
        story.append(Paragraph(f"[{e['categoria']}] {e['nome']}", styles["Heading2"]))
        story.append(Spacer(1, 0.4 * cm))
        img_source = exercise_image_source(e)
        rl_img = _fit_image(img_source, max_w, max_h) if img_source else None
        if rl_img:
            story.append(rl_img)
        else:
            story.append(Paragraph("Nessuna immagine disponibile per questo esercizio.", styles["Normal"]))

    doc.build(story)
    return buffer.getvalue()
