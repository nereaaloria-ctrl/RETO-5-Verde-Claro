"""Carga por lotes el dataset del Reto 5 en la SQLite de la API.

Dataset entrada: data/Prestamos_Data_Alumnos_v5.xlsx (NO subir a Git).
Ejecutar desde la carpeta reto5_api: python importar_prestamos_rapido.py
"""
from pathlib import Path
from openpyxl import load_workbook
from app import create_app
from app.db import FIELDS, get_db

DATASET = Path('data/Prestamos_Data_Alumnos_v5.xlsx')
CHUNK = 2000
INTEGER_FIELDS = {'edad', 'meses_empleo', 'num_creditos', 'duracion', 'impago'}
REAL_FIELDS = {'ingresos', 'monto_inicial', 'scoring_crediticio', 'ratio_interes', 'ratio_deuda_ingresos', 'prima'}


def convert(field, value):
    if value is None or value == '':
        return None
    if field == 'id':
        return str(value).strip()
    if field in INTEGER_FIELDS:
        return int(value)
    if field in REAL_FIELDS:
        return float(value)
    return str(value)


def main():
    if not DATASET.exists():
        raise SystemExit(f'No encuentro {DATASET.resolve()}')
    wb = load_workbook(DATASET, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    header = [str(cell).strip().lower().replace(' ', '_') for cell in next(rows)]
    missing = set(FIELDS) - set(header)
    if missing:
        raise SystemExit(f'Faltan columnas: {sorted(missing)}')
    indices = [header.index(field) for field in FIELDS]
    placeholders = ','.join('?' for _ in FIELDS)
    columns = ','.join(FIELDS)
    sql = f'INSERT OR IGNORE INTO prestamos ({columns}) VALUES ({placeholders})'
    app = create_app()
    attempted = 0
    invalid = 0
    with app.app_context():
        db = get_db()
        before = db.execute('SELECT COUNT(*) FROM prestamos').fetchone()[0]
        batch = []
        for row in rows:
            try:
                values = tuple(convert(field, row[idx]) for field, idx in zip(FIELDS, indices))
                if not values[0] or (values[17] is not None and values[17] not in (0, 1)):
                    invalid += 1
                    continue
                batch.append(values)
                attempted += 1
            except (ValueError, TypeError, IndexError):
                invalid += 1
                continue
            if len(batch) >= CHUNK:
                db.executemany(sql, batch)
                db.commit()
                batch.clear()
                if attempted % 100000 < CHUNK:
                    print(f'Filas procesadas: {attempted:,}', flush=True)
        if batch:
            db.executemany(sql, batch)
            db.commit()
        after = db.execute('SELECT COUNT(*) FROM prestamos').fetchone()[0]
        print(f'Registros nuevos: {after-before:,}; total en BD: {after:,}; filas omitidas por error: {invalid:,}')
    wb.close()


if __name__ == '__main__':
    main()
