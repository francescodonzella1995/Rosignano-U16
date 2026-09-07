"""
Livello di accesso dati per l'app.

Usa libsql_client per parlare sia con:
- un database Turso (cloud, persistente) quando sono presenti i secrets
  TURSO_DATABASE_URL e TURSO_AUTH_TOKEN, oppure le variabili d'ambiente omonime;
- un file SQLite locale (data/app.db) come fallback per lo sviluppo in locale
  o se Turso non è configurato.

Espone funzioni semplici (non un ORM) pensate per essere chiamate dalle pagine Streamlit.
"""
from __future__ import annotations

import datetime as dt
import json
import os
from typing import Any, Optional

import libsql_client

LOCAL_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "app.db")


def _get_secret(name: str) -> Optional[str]:
    # Prova prima st.secrets (quando gira dentro Streamlit), poi le variabili d'ambiente.
    try:
        import streamlit as st

        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass
    return os.environ.get(name)


def _make_client():
    url = _get_secret("TURSO_DATABASE_URL")
    token = _get_secret("TURSO_AUTH_TOKEN")
    if url:
        return libsql_client.create_client_sync(url=url, auth_token=token or None)
    os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
    return libsql_client.create_client_sync(url=f"file:{LOCAL_DB_PATH}")


_client = None


def get_client():
    global _client
    if _client is None:
        _client = _make_client()
    return _client


def is_using_turso() -> bool:
    return bool(_get_secret("TURSO_DATABASE_URL"))


def execute(sql: str, args: list | tuple = ()) -> libsql_client.ResultSet:
    return get_client().execute(sql, list(args))


def executemany(sql: str, rows: list[list]) -> None:
    client = get_client()
    for row in rows:
        client.execute(sql, row)


def insert_and_get_id(sql: str, args: list | tuple = ()) -> int:
    """Esegue un INSERT e restituisce l'id della riga appena creata.

    NB: non usare `SELECT last_insert_rowid()` in una query separata: con
    libsql_client questo valore è legato alla connessione/statement e una
    SELECT successiva può non vedere il valore corretto. Il modo affidabile
    è leggere `last_insert_rowid` direttamente dal ResultSet restituito
    dall'INSERT stesso.
    """
    rs = execute(sql, args)
    if rs.last_insert_rowid is None:
        raise RuntimeError("Impossibile determinare l'id della riga inserita.")
    return rs.last_insert_rowid


def query_all(sql: str, args: list | tuple = ()) -> list[dict]:
    rs = execute(sql, args)
    cols = rs.columns
    return [dict(zip(cols, row)) for row in rs.rows]


def query_one(sql: str, args: list | tuple = ()) -> Optional[dict]:
    rows = query_all(sql, args)
    return rows[0] if rows else None


SCHEMA = """
CREATE TABLE IF NOT EXISTS team (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    nome_squadra TEXT,
    colore_primario TEXT,
    colore_secondario TEXT
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    cognome TEXT NOT NULL,
    ruolo TEXT,
    data_nascita TEXT,
    numero_maglia INTEGER,
    note TEXT,
    attivo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS exercise_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria TEXT NOT NULL,
    nome TEXT NOT NULL,
    immagine_path TEXT,
    num_giocatori TEXT,
    obiettivo TEXT,
    dimensioni_campo TEXT,
    num_colori_casacche TEXT,
    regole TEXT,
    fonte TEXT
);

CREATE TABLE IF NOT EXISTS trainings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    ora TEXT,
    durata_minuti INTEGER,
    note TEXT
);

CREATE TABLE IF NOT EXISTS training_attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    training_id INTEGER NOT NULL REFERENCES trainings(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    presente INTEGER NOT NULL DEFAULT 1,
    UNIQUE(training_id, player_id)
);

CREATE TABLE IF NOT EXISTS training_exercises (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    training_id INTEGER NOT NULL REFERENCES trainings(id) ON DELETE CASCADE,
    exercise_id INTEGER NOT NULL REFERENCES exercises(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    avversario TEXT NOT NULL,
    casa_trasferta TEXT,
    modulo TEXT,
    durata_minuti INTEGER,
    gol_fatti INTEGER,
    gol_subiti INTEGER,
    eventi_salienti TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS match_lineup (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    titolare INTEGER NOT NULL DEFAULT 0,
    minuto_ingresso INTEGER,
    minuto_uscita INTEGER,
    ruolo_in_campo TEXT,
    UNIQUE(match_id, player_id)
);

CREATE TABLE IF NOT EXISTS match_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL REFERENCES matches(id) ON DELETE CASCADE,
    player_id INTEGER REFERENCES players(id) ON DELETE SET NULL,
    tipo TEXT NOT NULL,
    minuto INTEGER,
    descrizione TEXT
);

CREATE TABLE IF NOT EXISTS injuries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    data_inizio TEXT NOT NULL,
    data_fine_prevista TEXT,
    descrizione TEXT,
    note TEXT
);

CREATE TABLE IF NOT EXISTS player_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id) ON DELETE CASCADE,
    data TEXT NOT NULL,
    testo TEXT NOT NULL
);
"""


def init_db() -> None:
    client = get_client()
    for statement in SCHEMA.split(";"):
        s = statement.strip()
        if s:
            client.execute(s)
    if not query_one("SELECT id FROM team WHERE id = 1"):
        client.execute(
            "INSERT INTO team (id, nome_squadra, colore_primario, colore_secondario) VALUES (1, '', '', '')"
        )


# ---------------------------------------------------------------------------
# Seed del Manuale esercizi (idempotente: non duplica se già presenti)
# ---------------------------------------------------------------------------
def seed_exercises_if_empty(seed_files: list[str]) -> int:
    existing = query_one("SELECT COUNT(*) AS c FROM exercises")
    if existing and existing["c"] > 0:
        return 0
    inserted = 0
    categories = set()
    for path in seed_files:
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as f:
            items = json.load(f)
        for it in items:
            categories.add(it["categoria"])
            execute(
                """INSERT INTO exercises
                   (categoria, nome, immagine_path, num_giocatori, obiettivo,
                    dimensioni_campo, num_colori_casacche, regole, fonte)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    it["categoria"], it["nome"], it["immagine"], it.get("num_giocatori", ""),
                    it.get("obiettivo", ""), it.get("dimensioni_campo", ""),
                    it.get("num_colori_casacche", ""), it.get("regole", ""), it.get("fonte", ""),
                ],
            )
            inserted += 1
    for cat in categories:
        try:
            execute("INSERT OR IGNORE INTO exercise_categories (nome) VALUES (?)", [cat])
        except Exception:
            pass
    return inserted


# ---------------------------------------------------------------------------
# Export / Import di backup (per non perdere dati tra un redeploy e l'altro,
# o come rete di sicurezza indipendente da Turso)
# ---------------------------------------------------------------------------
BACKUP_TABLES = [
    "team", "players", "exercise_categories", "exercises",
    "trainings", "training_attendance", "training_exercises",
    "matches", "match_lineup", "match_events", "injuries", "player_notes",
]


def export_backup_dict() -> dict:
    backup = {"exported_at": dt.datetime.now().isoformat(), "tables": {}}
    for table in BACKUP_TABLES:
        backup["tables"][table] = query_all(f"SELECT * FROM {table}")
    return backup


def import_backup_dict(backup: dict, wipe_existing: bool = True) -> None:
    client = get_client()
    if wipe_existing:
        for table in reversed(BACKUP_TABLES):
            client.execute(f"DELETE FROM {table}")
    for table in BACKUP_TABLES:
        rows = backup.get("tables", {}).get(table, [])
        for row in rows:
            cols = list(row.keys())
            placeholders = ", ".join("?" for _ in cols)
            col_list = ", ".join(cols)
            client.execute(
                f"INSERT OR REPLACE INTO {table} ({col_list}) VALUES ({placeholders})",
                [row[c] for c in cols],
            )
