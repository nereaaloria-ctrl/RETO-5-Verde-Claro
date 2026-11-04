
# Importamos los préstamos del Excel a la base de datos SQLite
# Dataset de entrada: data/Prestamos_Data_Alumnos_v5.xlsx

from pathlib import Path
from openpyxl import load_workbook
from app import create_app
from app.db import FIELDS, get_db

ARCHIVO_DATOS = Path("data/Prestamos_Data_Alumnos_v5.xlsx")
TAMANO_LOTE = 2000

CAMPOS_ENTEROS = {"edad", "meses_empleo", "num_creditos", "duracion", "impago"}
CAMPOS_DECIMALES = {
    "ingresos", "monto_inicial", "scoring_crediticio",
    "ratio_interes", "ratio_deuda_ingresos", "prima"
}


def convertir_valor(campo, valor):
    if valor is None or valor == "":
        return None

    if campo == "id":
        return str(valor).strip()

    if campo in CAMPOS_ENTEROS:
        return int(valor)

    if campo in CAMPOS_DECIMALES:
        return float(valor)

    return str(valor)


def importar_prestamos():
    if not ARCHIVO_DATOS.exists():
        raise SystemExit(f"No encuentro {ARCHIVO_DATOS.resolve()}")

    archivo_excel = load_workbook(
        ARCHIVO_DATOS, read_only=True, data_only=True
    )

    hoja_excel = archivo_excel.active
    filas_excel = hoja_excel.iter_rows(values_only=True)

    encabezados = [
        str(celda).strip().lower().replace(" ", "_")
        for celda in next(filas_excel)
    ]

    campos_faltantes = set(FIELDS) - set(encabezados)

    if campos_faltantes:
        raise SystemExit(f"Faltan columnas: {sorted(campos_faltantes)}")

    posiciones = [encabezados.index(campo) for campo in FIELDS]
    interrogaciones = ",".join("?" for _ in FIELDS)
    columnas = ",".join(FIELDS)

    consulta_sql = (
        f"INSERT OR IGNORE INTO prestamos "
        f"({columnas}) VALUES ({interrogaciones})"
    )

    aplicacion = create_app()
    procesados = 0
    invalidos = 0

    with aplicacion.app_context():
        base_datos = get_db()

        total_antes = base_datos.execute(
            "SELECT COUNT(*) FROM prestamos"
        ).fetchone()[0]

        lote = []

        for fila in filas_excel:
            try:
                valores = tuple(
                    convertir_valor(campo, fila[posicion])
                    for campo, posicion in zip(FIELDS, posiciones)
                )

                if not valores[0] or (
                    valores[17] is not None
                    and valores[17] not in (0, 1)
                ):
                    invalidos += 1
                    continue

                lote.append(valores)
                procesados += 1

            except (ValueError, TypeError, IndexError):
                invalidos += 1
                continue

            if len(lote) >= TAMANO_LOTE:
                base_datos.executemany(consulta_sql, lote)
                base_datos.commit()
                lote.clear()

                if procesados % 100000 < TAMANO_LOTE:
                    print(f"Filas procesadas: {procesados:,}", flush=True)

        if lote:
            base_datos.executemany(consulta_sql, lote)
            base_datos.commit()

        total_despues = base_datos.execute(
            "SELECT COUNT(*) FROM prestamos"
        ).fetchone()[0]

        print(
            f"Registros nuevos: {total_despues - total_antes:,}; "
            f"total en BD: {total_despues:,}; "
            f"filas omitidas por error: {invalidos:,}"
        )

    archivo_excel.close()


if __name__ == "__main__":
    importar_prestamos()
