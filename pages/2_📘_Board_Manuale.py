"""
Board Manuale: catalogo degli esercizi di allenamento, organizzati per categoria.
"""
from __future__ import annotations

import os
import uuid

import streamlit as st

import db
from helpers import ensure_db_ready, asset_path, confirm_action, ASSETS_DIR

st.set_page_config(page_title="Board Manuale", page_icon="📘", layout="wide")
ensure_db_ready()

st.title("📘 Board Manuale - Catalogo Esercizi")

CUSTOM_IMG_DIR = os.path.join(ASSETS_DIR, "manuale", "custom")


def get_categories() -> list[str]:
    from_table = [c["nome"] for c in db.query_all("SELECT nome FROM exercise_categories ORDER BY nome")]
    from_exercises = [
        e["categoria"] for e in db.query_all("SELECT DISTINCT categoria FROM exercises")
    ]
    all_cats = sorted(set(from_table) | set(from_exercises))
    return all_cats


# ---------------------------------------------------------------------------
# Gestione categorie
# ---------------------------------------------------------------------------
with st.expander("➕ Gestisci categorie"):
    cats_now = get_categories()
    st.write("Categorie attuali:", ", ".join(cats_now) if cats_now else "nessuna")
    nuova_cat = st.text_input("Nuova categoria", key="nuova_categoria_input")
    if st.button("Aggiungi categoria"):
        if nuova_cat.strip():
            db.execute("INSERT OR IGNORE INTO exercise_categories (nome) VALUES (?)", [nuova_cat.strip()])
            st.success(f"Categoria '{nuova_cat.strip()}' aggiunta.")
            st.rerun()
        else:
            st.error("Inserisci un nome di categoria.")

st.divider()

# ---------------------------------------------------------------------------
# Aggiungi nuovo esercizio
# ---------------------------------------------------------------------------
with st.expander("➕ Aggiungi nuovo esercizio"):
    categorie = get_categories()
    with st.form("form_new_exercise", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            if categorie:
                categoria_sel = st.selectbox("Categoria", categorie)
            else:
                categoria_sel = None
                st.info("Nessuna categoria esistente: creane una qui sopra prima di aggiungere un esercizio.")
            nome_ex = st.text_input("Nome esercizio")
            num_giocatori = st.text_input("Numero giocatori (facoltativo)")
            num_colori = st.text_input("Numero colori casacche (facoltativo)")
        with c2:
            obiettivo = st.text_area("Obiettivo (facoltativo)", height=80)
            dimensioni = st.text_input("Dimensioni campo (facoltativo)")
            regole = st.text_area("Regole (facoltativo)", height=80)
        immagine_upload = st.file_uploader("Immagine (facoltativa)", type=["png", "jpg", "jpeg"])
        submitted_ex = st.form_submit_button("Aggiungi esercizio", type="primary")

    if submitted_ex:
        if not categoria_sel:
            st.error("Devi selezionare (o creare) una categoria.")
        elif not nome_ex.strip():
            st.error("Il nome dell'esercizio è obbligatorio.")
        else:
            immagine_rel = None
            if immagine_upload is not None:
                os.makedirs(CUSTOM_IMG_DIR, exist_ok=True)
                ext = os.path.splitext(immagine_upload.name)[1] or ".png"
                fname = f"{uuid.uuid4().hex}{ext}"
                with open(os.path.join(CUSTOM_IMG_DIR, fname), "wb") as f:
                    f.write(immagine_upload.getbuffer())
                immagine_rel = f"manuale/custom/{fname}"
            db.execute(
                """INSERT INTO exercises
                   (categoria, nome, immagine_path, num_giocatori, obiettivo, dimensioni_campo,
                    num_colori_casacche, regole, fonte)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    categoria_sel, nome_ex.strip(), immagine_rel, num_giocatori.strip(),
                    obiettivo.strip(), dimensioni.strip(), num_colori.strip(), regole.strip(),
                    "Inserito manualmente",
                ],
            )
            st.success(f"Esercizio '{nome_ex}' aggiunto.")
            st.rerun()

st.divider()

# ---------------------------------------------------------------------------
# Filtri
# ---------------------------------------------------------------------------
st.header("Catalogo")

categorie_disponibili = get_categories()
fc1, fc2 = st.columns([2, 3])
with fc1:
    categorie_filtro = st.multiselect("Filtra per categoria", categorie_disponibili, default=[])
with fc2:
    testo_filtro = st.text_input("Cerca per nome esercizio")

query = "SELECT * FROM exercises WHERE 1=1"
params: list = []
if categorie_filtro:
    placeholders = ",".join("?" for _ in categorie_filtro)
    query += f" AND categoria IN ({placeholders})"
    params.extend(categorie_filtro)
if testo_filtro.strip():
    query += " AND LOWER(nome) LIKE ?"
    params.append(f"%{testo_filtro.strip().lower()}%")
query += " ORDER BY categoria, nome"

esercizi = db.query_all(query, params)
st.caption(f"{len(esercizi)} esercizi trovati.")

esercizi_per_categoria: dict[str, list[dict]] = {}
for e in esercizi:
    esercizi_per_categoria.setdefault(e["categoria"], []).append(e)

for categoria, lista in esercizi_per_categoria.items():
    st.subheader(categoria)
    for ex in lista:
        with st.expander(ex["nome"]):
            img_path = asset_path(ex.get("immagine_path"))
            colimg, colform = st.columns([1, 2])
            with colimg:
                if img_path:
                    st.image(img_path, width='stretch')
                else:
                    st.caption("Nessuna immagine disponibile.")
            with colform:
                with st.form(f"edit_ex_{ex['id']}"):
                    e_num_giocatori = st.text_input("Numero giocatori", value=ex.get("num_giocatori") or "")
                    e_obiettivo = st.text_area("Obiettivo", value=ex.get("obiettivo") or "", height=70)
                    e_dimensioni = st.text_input("Dimensioni campo", value=ex.get("dimensioni_campo") or "")
                    e_num_colori = st.text_input("Numero colori casacche", value=ex.get("num_colori_casacche") or "")
                    e_regole = st.text_area("Regole", value=ex.get("regole") or "", height=100)
                    if ex.get("fonte"):
                        st.caption(f"Fonte: {ex['fonte']}")
                    salva = st.form_submit_button("Salva modifiche")
                if salva:
                    db.execute(
                        """UPDATE exercises SET num_giocatori=?, obiettivo=?, dimensioni_campo=?,
                           num_colori_casacche=?, regole=? WHERE id=?""",
                        [e_num_giocatori, e_obiettivo, e_dimensioni, e_num_colori, e_regole, ex["id"]],
                    )
                    st.success("Modifiche salvate.")
                    st.rerun()

                n_usi = db.query_one(
                    "SELECT COUNT(*) AS c FROM training_exercises WHERE exercise_id = ?", [ex["id"]]
                )["c"]
                confirm_action(
                    key=f"delete_ex_{ex['id']}",
                    button_label="🗑️ Elimina esercizio",
                    warning_text=(
                        f"Stai per eliminare definitivamente l'esercizio **{ex['nome']}** dal Manuale. "
                        + (
                            f"È stato usato in {n_usi} allenamenti registrati: resterà nello storico di "
                            "quegli allenamenti, ma non sarà più selezionabile per i nuovi. "
                            if n_usi > 0
                            else "Non è mai stato usato in nessun allenamento registrato. "
                        )
                        + "Confermi l'eliminazione?"
                    ),
                    on_confirm=lambda ex_id=ex["id"]: db.execute("DELETE FROM exercises WHERE id = ?", [ex_id]),
                )

if not esercizi:
    st.info("Nessun esercizio corrisponde ai filtri selezionati.")
