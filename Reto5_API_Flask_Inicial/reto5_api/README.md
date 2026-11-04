# Reto 5 - API REST de préstamos (Verde Claro)

## Descripción

En este proyecto hemos creado una API REST con Python y Flask para consultar información sobre préstamos.

Los datos proceden del archivo `Prestamos_Data_Alumnos_v5.xlsx` y se almacenan en una base de datos SQLite.

La API permite consultar préstamos, buscar uno por su identificador, añadir nuevos registros y obtener estadísticas generales. También se conecta a una API externa para consultar tipos de cambio.

Además, hemos añadido una ruta que exporta los préstamos en formato CSV para poder utilizarlos en Power BI.

## Estructura del proyecto

- `app/__init__.py`: configuración de Flask.
- `app/db.py`: conexión con la base de datos SQLite.
- `app/routes.py`: rutas y funciones de la API.
- `importar_prestamos_rapido.py`: importa los datos del Excel a SQLite.
- `run.py`: permite iniciar la API.
- `tests/test_api.py`: pruebas para comprobar el funcionamiento.
- `requirements.txt`: librerías necesarias.
- `.gitignore`: archivos y carpetas que no se deben subir a GitHub.

## Cómo ejecutar la API

Primero hay que instalar las librerías necesarias:

```bash
pip install -r requirements.txt
```

Después se inicia la API:

```bash
python run.py
```

Para comprobar que funciona, se puede abrir esta dirección en el navegador:

`http://127.0.0.1:5000/api/v1/salud`

## Importación de los datos

Para importar los préstamos, se coloca el archivo `Prestamos_Data_Alumnos_v5.xlsx` dentro de la carpeta `data`.

Después se ejecuta:

```bash
python importar_prestamos_rapido.py
```

Este programa lee los datos del Excel y los guarda en SQLite.

## Rutas de la API

| Método | Ruta | Función |
|---|---|---|
| GET | `/api/v1/salud` | Comprueba que la API funciona |
| GET | `/api/v1/prestamos` | Consulta la lista de préstamos |
| GET | `/api/v1/prestamos/<id>` | Busca un préstamo por su identificador |
| POST | `/api/v1/prestamos` | Añade un préstamo |
| GET | `/api/v1/estadisticas` | Muestra estadísticas generales |
| GET | `/api/v1/tipos-cambio` | Consulta tipos de cambio mediante una API externa |
| GET | `/api/v1/prestamos/exportar` | Exporta los préstamos en CSV para Power BI |

La ruta de listado permite limitar el número de resultados y aplicar un filtro de impago.

## Conexión con Power BI

Para realizar el dashboard hemos conectado Power BI con esta dirección:

`http://127.0.0.1:5000/api/v1/prestamos/exportar`

De esta forma hemos podido cargar los préstamos, analizar los datos y crear las visualizaciones.

Para actualizar los datos desde Power BI, la API debe estar ejecutándose.

## Pruebas

Para ejecutar las pruebas del proyecto se utiliza:

```bash
pytest -q
```

## Archivos de datos

La carpeta `data` y los archivos de la base de datos no se incluyen en el repositorio de GitHub. El proyecto contiene el código necesario para trabajar con ellos.
