# Reto 5 — API REST de préstamos (prototipo educativo)

Una base de partida para la parte de **Gestión y Gobierno del Dato II**: Flask + base de datos local SQLite + conexión de ejemplo a API externa. Se puede ampliar al modelo de base de datos que elija el equipo. **No contiene datos reales ni modelos predictivos entrenados**.

## Requisitos
- Python 3.10+
- PowerShell, Terminal o consola

## Instalación
```bash
python -m venv .venv
# Windows (PowerShell):
.venv\\Scripts\\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
python run.py
```
Visita `http://127.0.0.1:5000/api/v1/salud`. Debería responder `{"estado":"ok"}`.

## Rutas (contrato REST)
| Método | URL | Uso | Respuestas |
| --- | --- | --- | --- |
| GET | `/api/v1/salud` | Salud del servicio | 200 |
| GET | `/api/v1/prestamos?limit=20&offset=0&impago=1` | Lista paginada y filtro opcional | 200, 400 |
| GET | `/api/v1/prestamos/<id>` | Busca por ID | 200, 404 |
| POST | `/api/v1/prestamos` | Inserta un préstamo de prueba | 201, 400, 409 |
| GET | `/api/v1/estadisticas` | Conteo, media monto y número de impagos | 200 |
| GET | `/api/v1/tipos-cambio?base=EUR&destino=USD` | Consulta Frankfurter (API externa) | 200, 400, 502 |

### Crear registro de prueba (PowerShell)
```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/v1/prestamos -Method Post -ContentType 'application/json' -Body '{"id":"DEMO-001","edad":28,"ingresos":28000,"monto_inicial":12000,"impago":0}'
```
Consulta: `http://127.0.0.1:5000/api/v1/prestamos/DEMO-001`.

### Ejemplo de respuesta parcial
La respuesta de `GET /api/v1/prestamos/DEMO-001` incluirá, entre otros, los campos `id`, `edad`, `ingresos`, `monto_inicial` e `impago`.
La API devuelve además el resto de campos con valor `null` si no se proporcionaron.

## Importar el Excel de clase
1. Coloca `Prestamos_Data_Alumnos_v5.xlsx` en `data/` (carpeta excluida de Git).
2. Desde la raíz del proyecto: `python -m scripts.importar_excel data/Prestamos_Data_Alumnos_v5.xlsx`
3. Si la importación falla por encabezados/tipos, inspecciona el Excel y adapta las conversiones (se incluyen las columnas indicadas en el enunciado, pero no se dispone del archivo real).

**Nota:** sin el Excel real no se puede garantizar la conversión de todas las columnas categóricas, el formato de tasas o la calidad de datos. El script es un primer importador que hay que comprobar.

## Tests
`pytest -q`

## Estructura
```
reto5_api/
  app/__init__.py      configuración de Flask y registro de rutas
  app/db.py            operaciones SQLite y esquema de datos
  app/routes.py        endpoints REST y API externa
  scripts/importar_excel.py  importación desde data/
  tests/test_api.py    pruebas automatizadas
  run.py               ejecución local
  requirements.txt     dependencias
  .gitignore           exclusiones de datos y modelos
```

## Siguientes decisiones que corresponden al equipo
- Acordar qué **base de datos** emplear (SQLite solo para empezar; la asignatura de Bases de Datos II exige justificar una propuesta NoSQL).
- Decidir si la API externa de tipos de cambio encaja con el caso de negocio; sustituirla si el equipo necesita una integración más relevante.
- Añadir control de acceso y protección de datos antes de utilizar información real. **No ejecutar el servidor de desarrollo con `debug=True` en producción.**
- Valorar endpoints calculados para amortización francesa/alemana, riesgo, primas y predicciones cuando estén definidos y validados los modelos.
- No subir `data/`, `instance/` ni modelos entrenados al repositorio privado de GitHub.
