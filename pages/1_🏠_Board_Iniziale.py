"""
Board Iniziale: nome squadra, colori sociali e gestione rosa (import Excel + inserimento manuale).
"""
from __future__ import annotations

import io
import unicodedata

import pandas as pd
import streamlit as st

import db
from helpers import ensure_db_ready, get_team, get_players, player_label, confirm_action, apply_team_theme

st.set_page_config(page_title="Board Iniziale", page_icon="🏠", layout="wide")
ensure_db_ready()
apply_team_theme(get_team())

st.title("🏠 Board Iniziale")

if st.session_state.get("_flash_message"):
    st.success(st.session_state.pop("_flash_message"))

# ---------------------------------------------------------------------------
# 1) Configurazione squadra
# ---------------------------------------------------------------------------
st.header("Squadra")

team = get_team() or {}

with st.form("form_team"):
    nome_squadra = st.text_input("Nome squadra", value=team.get("nome_squadra") or "")
    c1, c2 = st.columns(2)
    with c1:
        colore_primario = st.color_picker(
            "Colore primario", value=team.get("colore_primario") or "#1E3A8A"
        )
    with c2:
        colore_secondario = st.color_picker(
            "Colore secondario", value=team.get("colore_secondario") or "#FFFFFF"
        )
    salva_team = st.form_submit_button("Salva dati squadra", type="primary")

if salva_team:
    db.execute(
        "UPDATE team SET nome_squadra = ?, colore_primario = ?, colore_secondario = ? WHERE id = 1",
        [nome_squadra, colore_primario, colore_secondario],
    )
    st.success("Dati squadra salvati.")
    st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# 2) Import rosa da Excel
# ---------------------------------------------------------------------------
st.header("Importa rosa da Excel")
st.caption("Colonne attese: nome, cognome, ruolo, data di nascita, numero di maglia (i nomi delle colonne possono variare, li mappi tu sotto).")

uploaded = st.file_uploader("Carica file Excel (.xlsx)", type=["xlsx", "xls"], key="excel_upload")


def _norm(s: str) -> str:
    s = str(s).strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return s


def _guess_column(columns: list[str], keywords: list[str]) -> str | None:
    norm_cols = {c: _norm(c) for c in columns}
    for col, nc in norm_cols.items():
        for kw in keywords:
            if kw in nc:
                return col
    return None


if uploaded is not None:
    try:
        df_raw = pd.read_excel(uploaded)
    except Exception as e:
        st.error(f"Non sono riuscito a leggere il file: {e}")
        df_raw = None

    if df_raw is not None and len(df_raw) > 0:
        st.caption("Anteprima file caricato:")
        st.dataframe(df_raw.head(10), width='stretch')

        cols = list(df_raw.columns)
        guess_nome = _guess_column(cols, ["nome"])
        guess_cognome = _guess_column(cols, ["cognome"])
        guess_ruolo = _guess_column(cols, ["ruolo", "posizione"])
        guess_nascita = _guess_column(cols, ["nascita", "dob", "data di nascita"])
        guess_numero = _guess_column(cols, ["numero", "maglia", "n."])

        st.markdown("**Fai corrispondere le colonne del file ai campi del giocatore:**")
        opts_required = cols
        opts_optional = ["-- nessuna --"] + cols

        mc1, mc2, mc3, mc4, mc5 = st.columns(5)
        with mc1:
            col_nome = st.selectbox(
                "Nome", opts_required, index=opts_required.index(guess_nome) if guess_nome in opts_required else 0
            )
        with mc2:
            col_cognome = st.selectbox(
                "Cognome", opts_required, index=opts_required.index(guess_cognome) if guess_cognome in opts_required else 0
            )
        with mc3:
            col_ruolo = st.selectbox(
                "Ruolo", opts_optional, index=opts_optional.index(guess_ruolo) if guess_ruolo in opts_optional else 0
            )
        with mc4:
            col_nascita = st.selectbox(
                "Data di nascita", opts_optional, index=opts_optional.index(guess_nascita) if guess_nascita in opts_optional else 0
            )
        with mc5:
            col_numero = st.selectbox(
                "Numero maglia", opts_optional, index=opts_optional.index(guess_numero) if guess_numero in opts_optional else 0
            )

        # Costruisco la tabella mappata
        mapped = pd.DataFrame()
        mapped["nome"] = df_raw[col_nome].astype(str).str.strip()
        mapped["cognome"] = df_raw[col_cognome].astype(str).str.strip()
        mapped["ruolo"] = df_raw[col_ruolo].astype(str).str.strip() if col_ruolo != "-- nessuna --" else ""
        if col_nascita != "-- nessuna --":
            parsed = pd.to_datetime(df_raw[col_nascita], dayfirst=True, errors="coerce")
            mapped["data_nascita"] = parsed.dt.strftime("%Y-%m-%d")
            mapped["data_nascita"] = mapped["data_nascita"].where(
                parsed.notna(), df_raw[col_nascita].astype(str)
            )
        else:
            mapped["data_nascita"] = ""
        mapped["numero_maglia"] = df_raw[col_numero] if col_numero != "-- nessuna --" else ""

        # Confronto con rosa esistente (per nome+cognome, case-insensitive) per capire nuovi vs aggiornamenti
        existing = get_players(only_active=False)
        existing_map = {(_norm(p["nome"]), _norm(p["cognome"])): p for p in existing}

        def stato_riga(row):
            key = (_norm(row["nome"]), _norm(row["cognome"]))
            return "Aggiornerà giocatore esistente" if key in existing_map else "Nuovo giocatore"

        mapped["stato"] = mapped.apply(stato_riga, axis=1)

        st.markdown("**Anteprima dati che verranno importati (puoi correggere le celle prima di confermare):**")
        edited = st.data_editor(
            mapped,
            width='stretch',
            num_rows="fixed",
            disabled=["stato"],
            key="import_preview_editor",
        )

        n_nuovi = (edited["stato"] == "Nuovo giocatore").sum()
        n_agg = (edited["stato"] == "Aggiornerà giocatore esistente").sum()

        def _do_import():
            for _, row in edited.iterrows():
                key = (_norm(row["nome"]), _norm(row["cognome"]))
                numero = row["numero_maglia"]
                numero_val = int(numero) if str(numero).strip() not in ("", "nan", "None") else None
                if key in existing_map:
                    pid = existing_map[key]["id"]
                    db.execute(
                        "UPDATE players SET ruolo=?, data_nascita=?, numero_maglia=? WHERE id=?",
                        [row["ruolo"], row["data_nascita"], numero_val, pid],
                    )
                else:
                    db.execute(
                        "INSERT INTO players (nome, cognome, ruolo, data_nascita, numero_maglia) VALUES (?, ?, ?, ?, ?)",
                        [row["nome"], row["cognome"], row["ruolo"], row["data_nascita"], numero_val],
                    )
            st.session_state["_flash_message"] = f"Importazione completata: {n_nuovi} nuovi giocatori, {n_agg} aggiornati."

        confirm_action(
            key="import_excel",
            button_label=f"Conferma importazione ({n_nuovi} nuovi, {n_agg} da aggiornare)",
            warning_text=(
                f"Stai per importare {len(edited)} righe: **{n_nuovi} nuovi giocatori** verranno creati e "
                f"**{n_agg} giocatori già in rosa** verranno aggiornati (ruolo, data di nascita, numero maglia "
                "sovrascritti con i valori del file). Confermi?"
            ),
            on_confirm=_do_import,
        )

st.divider()

# ---------------------------------------------------------------------------
# 3) Inserimento manuale singolo giocatore
# ---------------------------------------------------------------------------
st.header("Aggiungi un giocatore manualmente")

with st.form("form_add_player", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        nome = st.text_input("Nome")
        ruolo = st.text_input("Ruolo (es. Portiere, Difensore, Centrocampista, Attaccante)")
    with c2:
        cognome = st.text_input("Cognome")
        numero_maglia = st.number_input("Numero maglia", min_value=0, max_value=999, step=1, value=0)
    ha_data_nascita = st.checkbox("Inserisci data di nascita", value=False)
    data_nascita = None
    if ha_data_nascita:
        data_nascita = st.date_input("Data di nascita", value=None, format="DD/MM/YYYY")
    submitted = st.form_submit_button("Aggiungi giocatore", type="primary")

if submitted:
    if not nome.strip() or not cognome.strip():
        st.error("Nome e cognome sono obbligatori.")
    else:
        db.execute(
            "INSERT INTO players (nome, cognome, ruolo, data_nascita, numero_maglia) VALUES (?, ?, ?, ?, ?)",
            [
                nome.strip(),
                cognome.strip(),
                ruolo.strip(),
                data_nascita.isoformat() if data_nascita else None,
                int(numero_maglia) if numero_maglia else None,
            ],
        )
        st.success(f"Giocatore {nome} {cognome} aggiunto.")
        st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# 4) Rosa attuale: modifica inline + disattivazione/eliminazione
# ---------------------------------------------------------------------------
st.header("Rosa attuale")

mostra_inattivi = st.checkbox("Mostra anche i giocatori disattivati", value=False)
players = get_players(only_active=not mostra_inattivi)

if not players:
    st.info("Nessun giocatore in rosa. Importa un file Excel o aggiungine uno manualmente qui sopra.")
else:
    df_players = pd.DataFrame(players)[["id", "nome", "cognome", "ruolo", "data_nascita", "numero_maglia", "attivo"]]
    st.caption("Puoi modificare direttamente le celle e poi premere \"Salva modifiche rosa\".")
    edited_players = st.data_editor(
        df_players,
        width='stretch',
        num_rows="fixed",
        disabled=["id", "attivo"],
        key="players_editor",
        column_config={
            "attivo": st.column_config.CheckboxColumn("Attivo", disabled=True),
        },
    )

    if st.button("Salva modifiche rosa", type="primary"):
        for _, row in edited_players.iterrows():
            db.execute(
                "UPDATE players SET nome=?, cognome=?, ruolo=?, data_nascita=?, numero_maglia=? WHERE id=?",
                [
                    row["nome"], row["cognome"], row["ruolo"], row["data_nascita"],
                    int(row["numero_maglia"]) if pd.notna(row["numero_maglia"]) and str(row["numero_maglia"]).strip() != "" else None,
                    int(row["id"]),
                ],
            )
        st.success("Modifiche salvate.")
        st.rerun()

    st.subheader("Disattiva / riattiva / elimina un giocatore")
    all_players = get_players(only_active=False)
    sel = st.selectbox(
        "Seleziona giocatore",
        options=all_players,
        format_func=lambda p: f"{player_label(p)} {'(disattivato)' if not p['attivo'] else ''}",
        key="player_manage_select",
    )

    if sel:
        colA, colB = st.columns(2)
        with colA:
            if sel["attivo"]:
                confirm_action(
                    key=f"deactivate_{sel['id']}",
                    button_label="Disattiva giocatore (non più in rosa attiva)",
                    warning_text=(
                        f"Stai per disattivare **{player_label(sel)}**. Non comparirà più tra i giocatori attivi "
                        "(es. nelle presenze allenamento), ma tutte le sue statistiche storiche (presenze, partite, gol) "
                        "resteranno salvate. Confermi?"
                    ),
                    on_confirm=lambda: db.execute("UPDATE players SET attivo = 0 WHERE id = ?", [sel["id"]]),
                )
            else:
                if st.button("Riattiva giocatore"):
                    db.execute("UPDATE players SET attivo = 1 WHERE id = ?", [sel["id"]])
                    st.rerun()
        with colB:
            n_train = db.query_one(
                "SELECT COUNT(*) AS c FROM training_attendance WHERE player_id = ?", [sel["id"]]
            )["c"]
            n_match = db.query_one(
                "SELECT COUNT(*) AS c FROM match_lineup WHERE player_id = ?", [sel["id"]]
            )["c"]
            confirm_action(
                key=f"delete_{sel['id']}",
                button_label="🗑️ Elimina definitivamente",
                warning_text=(
                    f"**Attenzione**: eliminando definitivamente **{player_label(sel)}** verranno cancellati "
                    f"per sempre anche i suoi dati collegati: {n_train} presenze/assenze agli allenamenti, "
                    f"{n_match} presenze in distinta partita (con relativi gol/cartellini/minutaggio), eventuali "
                    "infortuni e note. Questa azione NON è reversibile. Usa invece \"Disattiva\" se vuoi solo "
                    "toglierlo dalla rosa attiva mantenendo lo storico. Confermi l'eliminazione definitiva?"
                ),
                on_confirm=lambda: db.execute("DELETE FROM players WHERE id = ?", [sel["id"]]),
                button_type="secondary",
            )
