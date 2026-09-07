"""
Backup: esporta/importa una copia completa dei dati (rete di sicurezza indipendente da Turso).
"""
from __future__ import annotations

import datetime as dt
import json

import streamlit as st

import db
from helpers import ensure_db_ready, confirm_action

st.set_page_config(page_title="Backup", page_icon="💾", layout="wide")
ensure_db_ready()

st.title("💾 Backup dei dati")

st.caption(
    f"Storage attuale: **{'Turso (cloud, persistente)' if db.is_using_turso() else 'SQLite locale (solo per test/sviluppo)'}**. "
    "L'export/import qui sotto è una copia di sicurezza indipendente, utile per non perdere dati "
    "in caso di problemi o per spostare i dati su un altro ambiente."
)

st.divider()

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------
st.header("Esporta backup")

if st.button("Genera backup", type="primary"):
    backup = db.export_backup_dict()
    st.session_state["_backup_generato"] = backup

if "_backup_generato" in st.session_state:
    backup = st.session_state["_backup_generato"]
    conteggi = {t: len(rows) for t, rows in backup["tables"].items()}
    st.write("Riepilogo del backup generato:")
    st.json(conteggi, expanded=False)
    fname = f"backup_rosignano_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    st.download_button(
        "Scarica file di backup (.json)",
        data=json.dumps(backup, ensure_ascii=False, indent=2),
        file_name=fname,
        mime="application/json",
    )

st.divider()

# ---------------------------------------------------------------------------
# Import / Restore
# ---------------------------------------------------------------------------
st.header("Importa / Ripristina da backup")
st.warning(
    "⚠️ Il ripristino da backup **sostituisce completamente** tutti i dati attualmente presenti "
    "(squadra, rosa, manuale esercizi, allenamenti, partite, statistiche) con quelli contenuti nel file. "
    "Non è un'unione: i dati attuali non presenti nel backup andranno persi."
)

uploaded_backup = st.file_uploader("Carica file di backup (.json)", type=["json"], key="backup_upload")

if uploaded_backup is not None:
    try:
        backup_data = json.load(uploaded_backup)
    except Exception as e:
        st.error(f"File non valido: {e}")
        backup_data = None

    if backup_data is not None and "tables" in backup_data:
        conteggi_backup = {t: len(rows) for t, rows in backup_data["tables"].items()}
        conteggi_attuali = {t: len(db.query_all(f"SELECT id FROM {t}")) for t in db.BACKUP_TABLES}

        st.write(f"**Backup generato il:** {backup_data.get('exported_at', 'data sconosciuta')}")
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Dati attuali (verranno eliminati):**")
            st.json(conteggi_attuali, expanded=False)
        with c2:
            st.write("**Dati nel backup (verranno ripristinati):**")
            st.json(conteggi_backup, expanded=False)

        def _do_restore():
            db.import_backup_dict(backup_data, wipe_existing=True)

        confirm_action(
            key="restore_backup",
            button_label="Ripristina questo backup (sostituisce tutti i dati attuali)",
            warning_text=(
                "Confermi il ripristino? Tutti i dati attuali elencati sopra verranno **eliminati definitivamente** "
                "e sostituiti con quelli del backup. Questa azione non è reversibile (a meno di avere un altro backup più recente)."
            ),
            on_confirm=_do_restore,
        )
    elif backup_data is not None:
        st.error("Il file non sembra un backup valido generato da questa app (manca la chiave 'tables').")
