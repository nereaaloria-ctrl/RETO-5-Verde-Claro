"""Versioned REST endpoints for loans and external currency conversion."""
import sqlite3
import csv
import io
import requests
from flask import Blueprint, Response, jsonify, request, stream_with_context
from .db import FIELDS, get_db, get_loan, insert_loan, list_loans

bp = Blueprint("api", __name__, url_prefix="/api/v1")


def error(message, status):
    return jsonify({"error": message}), status


@bp.get("/salud")
def health():
    return jsonify({"estado": "ok"})


@bp.get("/prestamos")
def loans():
    try:
        limit = int(request.args.get("limit", 20))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        return error("limit y offset deben ser enteros", 400)
    if not 1 <= limit <= 100 or offset < 0:
        return error("limit debe estar entre 1 y 100 y offset debe ser >= 0", 400)
    impago_text = request.args.get("impago")
    if impago_text not in (None, "0", "1"):
        return error("impago debe ser 0 o 1", 400)
    impago = int(impago_text) if impago_text is not None else None
    return jsonify({"datos": list_loans(limit, offset, impago), "limit": limit, "offset": offset})


@bp.get("/prestamos/exportar")
def export_loans():
    """Stream the full loan table to Power BI as UTF-8 CSV."""
    impago_text = request.args.get("impago")
    if impago_text not in (None, "0", "1"):
        return error("impago debe ser 0 o 1", 400)

    def generate():
        db = get_db()
        sql = "SELECT " + ", ".join(FIELDS) + " FROM prestamos"
        params = ()
        if impago_text is not None:
            sql += " WHERE impago = ?"
            params = (int(impago_text),)
        sql += " ORDER BY id"
        cursor = db.execute(sql, params)
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        writer.writerow(FIELDS)
        yield buffer.getvalue()
        buffer.seek(0)
        buffer.truncate(0)
        while True:
            rows = cursor.fetchmany(2000)
            if not rows:
                break
            for row in rows:
                writer.writerow(tuple(row))
                yield buffer.getvalue()
                buffer.seek(0)
                buffer.truncate(0)

    response = Response(stream_with_context(generate()), mimetype="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = 'attachment; filename="prestamos_powerbi.csv"'
    response.headers["Cache-Control"] = "no-store"
    return response


@bp.get("/prestamos/<loan_id>")
def loan(loan_id):
    record = get_loan(loan_id)
    if not record:
        return error("Préstamo no encontrado", 404)
    return jsonify(record)


@bp.post("/prestamos")
def create_loan():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return error("El cuerpo debe ser JSON", 400)
    if not isinstance(payload.get("id"), str) or not payload["id"].strip():
        return error("El campo id es obligatorio y debe ser texto", 400)
    allowed = {"id", "edad", "ingresos", "monto_inicial", "scoring_crediticio", "meses_empleo", "num_creditos", "ratio_interes", "duracion", "ratio_deuda_ingresos", "estudios", "tipo_jornada_laboral", "estado_civil", "posesion_hipoteca", "personas_cargo", "proposito", "fiador", "impago", "prima"}
    extra = set(payload) - allowed
    if extra:
        return error(f"Campos no permitidos: {', '.join(sorted(extra))}", 400)
    for field in ("edad", "meses_empleo", "num_creditos", "duracion"):
        if field in payload and (type(payload[field]) is not int or payload[field] < 0):
            return error(f"{field} debe ser entero no negativo", 400)
    for field in ("ingresos", "monto_inicial", "scoring_crediticio", "ratio_interes", "ratio_deuda_ingresos", "prima"):
        if field in payload and (type(payload[field]) not in (float, int) or payload[field] < 0):
            return error(f"{field} debe ser numérico no negativo", 400)
    if "impago" in payload and (type(payload["impago"]) is not int or payload["impago"] not in (0, 1)):
        return error("impago debe ser 0 o 1", 400)
    try:
        insert_loan(payload)
    except sqlite3.IntegrityError:
        return error("Ya existe un préstamo con ese ID", 409)
    response = jsonify(get_loan(payload["id"]))
    response.status_code = 201
    response.headers["Location"] = f"/api/v1/prestamos/{payload['id']}"
    return response


@bp.get("/estadisticas")
def stats():
    row = get_db().execute("""SELECT COUNT(*) AS total_prestamos,
         ROUND(AVG(monto_inicial), 2) AS monto_promedio,
         SUM(CASE WHEN impago = 1 THEN 1 ELSE 0 END) AS total_impagos
         FROM prestamos""").fetchone()
    return jsonify(dict(row))


@bp.get("/tipos-cambio")
def exchange_rate():
    """Example external API integration; separate from the original loan dataset."""
    base = request.args.get("base", "EUR").upper()
    destino = request.args.get("destino", "USD").upper()
    if not (len(base) == len(destino) == 3 and base.isalpha() and destino.isalpha()):
        return error("base y destino deben ser códigos ISO de tres letras", 400)
    if base == destino:
        return jsonify({"base": base, "destino": destino, "tipo_cambio": 1.0})
    try:
        result = requests.get("https://api.frankfurter.dev/v1/latest", params={"base": base, "symbols": destino}, timeout=5)
        result.raise_for_status()
        data = result.json()
        rate = data.get("rates", {}).get(destino)
        if rate is None:
            return error("Moneda no disponible en el proveedor externo", 502)
        return jsonify({"base": base, "destino": destino, "fecha": data.get("date"), "tipo_cambio": rate, "fuente": "Frankfurter"})
    except (requests.RequestException, ValueError):
        return error("No se pudo consultar la API externa", 502)
