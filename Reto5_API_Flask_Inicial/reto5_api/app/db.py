#Funciones para trabajar con la base de datos SQLite
import os
import sqlite3
from flask import current_app, g

FIELDS = [
    "id", "edad", "ingresos", "monto_inicial", "scoring_crediticio",
    "meses_empleo", "num_creditos", "ratio_interes", "duracion",
    "ratio_deuda_ingresos", "estudios", "tipo_jornada_laboral",
    "estado_civil", "posesion_hipoteca", "personas_cargo",
    "proposito", "fiador", "impago", "prima",
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def initialize_db():
    os.makedirs(os.path.dirname(current_app.config["DATABASE"]), exist_ok=True)
    db = get_db()
    db.execute("""
      CREATE TABLE IF NOT EXISTS prestamos (
        id TEXT PRIMARY KEY,
        edad INTEGER,
        ingresos REAL,
        monto_inicial REAL,
        scoring_crediticio REAL,
        meses_empleo INTEGER,
        num_creditos INTEGER,
        ratio_interes REAL,
        duracion INTEGER,
        ratio_deuda_ingresos REAL,
        estudios TEXT,
        tipo_jornada_laboral TEXT,
        estado_civil TEXT,
        posesion_hipoteca TEXT,
        personas_cargo TEXT,
        proposito TEXT,
        fiador TEXT,
        impago INTEGER CHECK (impago IN (0,1) OR impago IS NULL),
        prima REAL
      )
    """)
    db.commit()


def insert_loan(payload):
    db = get_db()
    keys = [field for field in FIELDS if field in payload]
    placeholders = ",".join("?" for _ in keys)
    columns = ",".join(keys)
    db.execute(
        f"INSERT INTO prestamos ({columns}) VALUES ({placeholders})",
        [payload[key] for key in keys],
    )
    db.commit()


def get_loan(loan_id):
    row = get_db().execute("SELECT * FROM prestamos WHERE id = ?", (loan_id,)).fetchone()
    return dict(row) if row else None


def list_loans(limit, offset, impago=None):
    sql = "SELECT * FROM prestamos"
    params = []
    if impago is not None:
        sql += " WHERE impago = ?"
        params.append(impago)
    sql += " ORDER BY id LIMIT ? OFFSET ?"
    rows = get_db().execute(sql, (*params, limit, offset)).fetchall()
    return [dict(row) for row in rows]
