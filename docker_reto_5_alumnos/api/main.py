
import os
import csv
import io

import requests
from flask import Flask, jsonify, request, Response
from sqlalchemy import create_engine, text

app = Flask(__name__)

# La direccion de MySQL la proporciona docker-compose.yml.
DATABASE_URL = os.environ["DATABASE_URL"]
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Nombre de la tabla que crea load_data.py.
TABLA = "clientes_credito"


# Ruta inicial para comprobar que funciona la API.
@app.get("/")
def inicio():
    return {"mensaje": "API Flask funcionando"}


# Comprueba que la API puede conectarse a MySQL.
@app.get("/api/v1/salud")
def salud():
    try:
        with engine.connect() as conexion:
            conexion.execute(text("SELECT 1"))

        return {"estado": "ok", "base_datos": "conectada"}

    except Exception:
        return jsonify({"estado": "error", "base_datos": "sin conexion"}), 503


# Consulta los prestamos por paginas.
@app.get("/api/v1/prestamos")
def consultar_prestamos():
    try:
        limite = int(request.args.get("limit", 20))
        inicio = int(request.args.get("offset", 0))

        if limite < 1 or limite > 100 or inicio < 0:
            return jsonify({"error": "Limite u offset incorrecto"}), 400

        impago = request.args.get("impago")

        if impago not in (None, "0", "1"):
            return jsonify({"error": "Impago debe ser 0 o 1"}), 400

        condiciones = ""
        parametros = {"limite": limite, "inicio": inicio}

        if impago is not None:
            condiciones = "WHERE impago = :impago"
            parametros["impago"] = int(impago)

        consulta = text(f"""
            SELECT *
            FROM {TABLA}
            {condiciones}
            ORDER BY row_id
            LIMIT :limite OFFSET :inicio
        """)

        with engine.connect() as conexion:
            resultado = conexion.execute(consulta, parametros)
            prestamos = [dict(fila) for fila in resultado.mappings()]

        return jsonify({
            "datos": prestamos,
            "limit": limite,
            "offset": inicio
        })

    except ValueError:
        return jsonify({"error": "Limit y offset deben ser numeros enteros"}), 400


# Exporta todos los prestamos a CSV para Power BI.
@app.get("/api/v1/prestamos/exportar")
def exportar_prestamos():

    # No exportamos row_id porque no pertenece al Excel original.
    columnas = [
        "id", "edad", "ingresos", "monto_inicial",
        "scoring_crediticio", "meses_empleo", "num_creditos",
        "ratio_interes", "duracion", "ratio_deuda_ingresos",
        "estudios", "tipo_jornada_laboral", "estado_civil",
        "posesion_hipoteca", "personas_cargo", "proposito",
        "fiador", "impago", "prima"
    ]

    consulta = text(
        f"SELECT {', '.join(columnas)} FROM {TABLA} ORDER BY row_id"
    )

    def generar_csv():
        archivo = io.StringIO()
        escritor = csv.writer(archivo)

        escritor.writerow(columnas)
        yield archivo.getvalue()

        archivo.seek(0)
        archivo.truncate(0)

        with engine.connect() as conexion:
            resultado = conexion.execution_options(
                stream_results=True
            ).execute(consulta)

            while True:
                filas = resultado.fetchmany(2000)

                if not filas:
                    break

                escritor.writerows(filas)
                yield archivo.getvalue()

                archivo.seek(0)
                archivo.truncate(0)

    return Response(
        generar_csv(),
        mimetype="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=prestamos.csv"
        }
    )


# Busca los prestamos que tienen un ID concreto.
@app.get("/api/v1/prestamos/<identificador>")
def buscar_prestamo(identificador):

    consulta = text(f"""
        SELECT *
        FROM {TABLA}
        WHERE id = :identificador
        ORDER BY row_id
    """)

    with engine.connect() as conexion:
        resultado = conexion.execute(
            consulta, {"identificador": identificador}
        )
        prestamos = [dict(fila) for fila in resultado.mappings()]

    if not prestamos:
        return jsonify({"error": "Prestamo no encontrado"}), 404

    # Puede haber varios prestamos con el mismo ID.
    return jsonify({"datos": prestamos})


# Permite crear un prestamo nuevo.
@app.post("/api/v1/prestamos")
def crear_prestamo():

    datos = request.get_json(silent=True)

    if not isinstance(datos, dict) or not datos:
        return jsonify({"error": "Debes enviar los datos en JSON"}), 400

    # Obtenemos los nombres de las columnas desde MySQL.
    # Asi no repetimos las 19 columnas de load_data.py.
    with engine.connect() as conexion:
        resultado = conexion.execute(
            text(f"SHOW COLUMNS FROM {TABLA}")
        )
        columnas = [fila[0] for fila in resultado]

    columnas_permitidas = set(columnas) - {"row_id"}

    if "id" not in datos or datos["id"] is None:
        return jsonify({"error": "El campo id es obligatorio"}), 400

    if set(datos) - columnas_permitidas:
        return jsonify({"error": "Hay columnas no permitidas"}), 400

    campos = list(datos.keys())
    nombres = ", ".join(campos)
    valores = ", ".join(":" + campo for campo in campos)

    consulta = text(
        f"INSERT INTO {TABLA} ({nombres}) VALUES ({valores})"
    )

    with engine.begin() as conexion:
        resultado = conexion.execute(consulta, datos)
        nuevo_id = resultado.lastrowid

    return jsonify({
        "mensaje": "Prestamo creado correctamente",
        "row_id": nuevo_id
    }), 201


# Estadisticas generales de los prestamos.
@app.get("/api/v1/estadisticas")
def estadisticas():

    consulta = text(f"""
        SELECT
            COUNT(*) AS total_prestamos,
            ROUND(AVG(monto_inicial), 2) AS monto_medio,
            SUM(CASE WHEN impago = 1 THEN 1 ELSE 0 END) AS impagos
        FROM {TABLA}
    """)

    with engine.connect() as conexion:
        datos = conexion.execute(consulta).mappings().first()

    total = datos["total_prestamos"]
    impagos = int(datos["impagos"] or 0)

    tasa = round(impagos * 100 / total, 2) if total else 0

    return jsonify({
        "total_prestamos": total,
        "monto_medio": float(datos["monto_medio"] or 0),
        "total_impagos": impagos,
        "tasa_impago": tasa
    })


# Consulta una API externa para obtener tipos de cambio.
@app.get("/api/v1/tipos-cambio")
def tipos_cambio():

    base = request.args.get("base", "EUR").upper()
    destino = request.args.get("destino", "USD").upper()

    if (
        len(base) != 3 or len(destino) != 3
        or not base.isalpha() or not destino.isalpha()
    ):
        return jsonify({"error": "Codigo de moneda incorrecto"}), 400

    try:
        respuesta = requests.get(
            "https://api.frankfurter.dev/v1/latest",
            params={"base": base, "symbols": destino},
            timeout=10
        )

        respuesta.raise_for_status()
        datos = respuesta.json()

        return jsonify(datos)

    except requests.RequestException:
        return jsonify({
            "error": "No se pudo consultar la API externa"
        }), 502


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=8000,
        debug=True
    )
