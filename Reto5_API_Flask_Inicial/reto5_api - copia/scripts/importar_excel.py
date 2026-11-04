"""Import Prestamos_Data_Alumnos_v5.xlsx from data/ (never commit this file)."""
from pathlib import Path
import sys
from openpyxl import load_workbook
from app import create_app
from app.db import FIELDS, insert_loan
import sqlite3

# Dataset esperado: data/Prestamos_Data_Alumnos_v5.xlsx
# El archivo no se proporciona con este proyecto.
NORMALIZE = {"id": "id", "edad": "edad", "ingresos": "ingresos",
 "monto_inicial": "monto_inicial", "scoring_crediticio": "scoring_crediticio",
 "meses_empleo": "meses_empleo", "num_creditos": "num_creditos",
 "ratio_interes": "ratio_interes", "duracion": "duracion",
 "ratio_deuda_ingresos": "ratio_deuda_ingresos", "estudios": "estudios",
 "tipo_jornada_laboral": "tipo_jornada_laboral", "estado_civil": "estado_civil",
 "posesion_hipoteca": "posesion_hipoteca", "personas_cargo": "personas_cargo",
 "proposito": "proposito", "fiador": "fiador", "impago": "impago", "prima": "prima"}


def main():
    path = Path(sys.argv[1] if len(sys.argv) > 1 else "data/Prestamos_Data_Alumnos_v5.xlsx")
    if not path.exists():
        raise SystemExit(f"No encuentro el dataset: {path}")
    workbook = load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    rows = sheet.iter_rows(values_only=True)
    headers = [str(x).strip().lower().replace(" ", "_") for x in next(rows)]
    # Se asume que los encabezados corresponden al diccionario del enunciado.
    if "id" not in headers:
        raise SystemExit("No se encontró la columna ID. Revisa la hoja/encabezados.")
    app = create_app()
    created = duplicated = 0
    with app.app_context():
        for values in rows:
            item = {NORMALIZE[h]: v for h, v in zip(headers, values) if h in NORMALIZE and v is not None}
            if not item.get("id"):
                continue
            item["id"] = str(item["id"])
            try:
                insert_loan(item)
                created += 1
            except sqlite3.IntegrityError:
                duplicated += 1
    print(f"Importados: {created}. IDs duplicados omitidos: {duplicated}.")
    print("Revisa tipos, nulos y distribuciones tras importar: este es un importador inicial.")


if __name__ == "__main__":
    main()
