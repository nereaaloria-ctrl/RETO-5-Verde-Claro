# Reto 5 · API REST de préstamos

**Equipo:** Verde Claro  
**Proyecto:** Reto 5 — Business Data Analytics  
**Tecnologías:** Python 3.12, Flask 3.1.2, MySQL 8.4 y Docker Compose

## 1. Descripción

Este proyecto implementa una **API REST para consultar y gestionar información de préstamos** almacenada en MySQL. El entorno se ejecuta mediante Docker Compose y parte del archivo `datos/Prestamos_Data_Alumnos_v5.xlsx`.

La aplicación permite consultar préstamos de forma paginada, filtrarlos por impago, buscar registros por identificador, insertar préstamos, obtener estadísticas, consultar tipos de cambio a través de la API externa de Frankfurter y exportar todos los datos originales a CSV para su análisis en Power BI.

El entorno distingue tres servicios:

- **`db`**: servidor MySQL 8.4, con almacenamiento persistente.
- **`cargar_datos`**: proceso de Python que carga el archivo de préstamos en MySQL.
- **`api`**: servidor Flask que expone los endpoints HTTP.

## 2. Requisitos y puesta en marcha

Se necesita **Docker Desktop** con Docker Compose habilitado. No es necesario instalar MySQL ni las bibliotecas de Python por separado en el equipo anfitrión.

Desde una terminal situada en el directorio del proyecto, donde se encuentra `docker-compose.yml`, ejecutar:

```bash
docker compose up --build
```

Para ejecutar los servicios en segundo plano:

```bash
docker compose up -d --build
```

Para comprobar el estado y consultar los registros de ejecución:

```bash
docker compose ps
docker compose logs api
docker compose logs cargar_datos
```

El servicio `cargar_datos` está diseñado para finalizar después de completar la carga; que figure como **`exited (0)`** es normal. El servicio `api` espera a que dicho proceso termine correctamente. MySQL debe superar previamente su comprobación de salud.

Una vez iniciado el entorno, la API está disponible en **http://localhost:8000**.

Para comprobar su funcionamiento:

```text
http://localhost:8000/api/v1/salud
```

Respuesta esperada cuando la conexión con MySQL funciona:

```json
{
  "estado": "ok",
  "base_datos": "conectada"
}
```

## 3. Estructura del proyecto

```text
docker_reto_5_alumnos/
├── api/
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
├── datos/
│   ├── Prestamos_Data_Alumnos_v5.xlsx
│   └── datos.xlsx
├── loader/
│   ├── .dockerignore
│   ├── Dockerfile
│   ├── load_data.py
│   └── requirements.txt
├── docker-compose.yml
└── README.md
```

**Nota:** la carpeta incluye dos archivos Excel, pero la configuración actual de `docker-compose.yml` utiliza exclusivamente `Prestamos_Data_Alumnos_v5.xlsx`. El archivo `datos.xlsx` no es el origen configurado para la carga.

Los archivos principales tienen las siguientes funciones:

| Archivo | Función |
|---|---|
| `api/main.py` | Implementación de Flask y de los endpoints REST. |
| `api/requirements.txt` | Dependencias de la API: Flask, SQLAlchemy, PyMySQL y Requests. |
| `loader/load_data.py` | Lectura del Excel, comprobaciones informativas y carga en MySQL. |
| `loader/requirements.txt` | Dependencias para la carga: pandas, openpyxl, SQLAlchemy y PyMySQL. |
| `docker-compose.yml` | Configuración de los tres servicios, dependencias, volumen y puerto HTTP. |
| `datos/Prestamos_Data_Alumnos_v5.xlsx` | Archivo de datos seleccionado para la carga. |

## 4. Configuración de MySQL y persistencia

La configuración actual incluida en `docker-compose.yml` es:

| Parámetro | Valor |
|---|---|
| Servicio Docker | `db` |
| Motor | MySQL 8.4 |
| Base de datos | `creditos` |
| Usuario | `clase` |
| Contraseña | `clase123` |
| Tabla | `clientes_credito` |
| Puerto interno de MySQL | `3306` |
| Puerto de la API publicado en el equipo | `8000` |
| Volumen de MySQL | `mysql_data` |

La dirección utilizada **dentro de la red de Docker** es:

```text
mysql+pymysql://clase:clase123@db:3306/creditos
```

**Importante:** el puerto `3306` de MySQL **no está publicado en `localhost`** en esta versión de `docker-compose.yml`. Los contenedores se comunican usando el nombre del servicio `db`. En el equipo anfitrión se publica únicamente la API Flask, en el puerto `8000`.

El volumen `mysql_data` permite mantener la base de datos entre arranques normales:

```bash
# Detener y retirar los contenedores sin borrar los datos
docker compose down

# Volver a iniciar el entorno
docker compose up
```

Para eliminar también los volúmenes del proyecto:

```bash
docker compose down -v
```

**Precaución:** este último comando elimina los datos persistentes, incluidos los préstamos introducidos después de la carga inicial. En el siguiente arranque, el cargador podrá reconstruir la tabla a partir del Excel si el fichero sigue disponible.

Las contraseñas incluidas en la configuración corresponden a un entorno académico y **no deben reutilizarse en producción**.

## 5. Carga y preparación de datos

El servicio `cargar_datos` ejecuta `loader/load_data.py`, con estas variables de entorno:

```text
DATA_FILE=/datos/Prestamos_Data_Alumnos_v5.xlsx
FORCE_RELOAD=false
```

El archivo puede ser Excel (`.xlsx` o `.xls`) o CSV si se cambia adecuadamente `DATA_FILE`; en la configuración entregada se utiliza el `.xlsx` indicado.

El proceso de carga realiza estas operaciones:

1. Comprueba que existe el archivo de entrada y lo lee mediante pandas.
2. Normaliza **los nombres de las columnas**: los pasa a minúsculas, elimina tildes y caracteres especiales y sustituye espacios por guiones bajos.
3. Comprueba la presencia de las **19 columnas obligatorias**.
4. Muestra avisos en la consola cuando encuentra **valores nulos** o **identificadores `id` repetidos**.
5. Carga los registros en la tabla `clientes_credito` de MySQL.
6. Añade una clave técnica `row_id` autoincremental como **clave primaria**, independiente del identificador original `id`.

**Criterio aplicado:** la carga conserva los datos del archivo original. **No elimina duplicados, no imputa valores faltantes y no modifica los valores de las variables**, salvo la normalización de los nombres de las columnas. Los valores faltantes se almacenan como `NULL` cuando corresponde.

El campo original `id` **no se define como clave primaria**, ya que pueden existir identificadores repetidos. La clave `row_id` permite distinguir todas las filas.

Si `clientes_credito` ya existe y tiene registros, el cargador no realiza una nueva importación mientras `FORCE_RELOAD` sea `false`. Para forzar la recarga se puede establecer:

```yaml
FORCE_RELOAD: "true"
```

Después debe volver a ejecutarse el servicio de carga. **Atención:** la recarga utiliza `if_exists="replace"`; por tanto, sustituye la tabla y elimina los registros que se hubieran añadido posteriormente. Devolver `FORCE_RELOAD` a `"false"` después de usarlo evita recargas accidentales.

## 6. Endpoints de la API

La API expone las siguientes rutas:

| Método | Endpoint | Descripción |
|---|---|---|
| `GET` | `/` | Comprueba que Flask está respondiendo. |
| `GET` | `/api/v1/salud` | Comprueba la conexión entre Flask y MySQL. |
| `GET` | `/api/v1/prestamos` | Devuelve préstamos paginados, con filtro opcional por impago. |
| `GET` | `/api/v1/prestamos/<identificador>` | Busca todas las filas cuyo `id` coincide con el identificador. |
| `POST` | `/api/v1/prestamos` | Inserta un préstamo mediante JSON. |
| `GET` | `/api/v1/estadisticas` | Devuelve indicadores agregados sobre los préstamos. |
| `GET` | `/api/v1/tipos-cambio` | Consulta tipos de cambio en la API externa Frankfurter. |
| `GET` | `/api/v1/prestamos/exportar` | Descarga todos los préstamos en CSV para Power BI. |

### 6.1. Ruta inicial

**Solicitud:** `GET /`

**Respuesta:**

```json
{"mensaje": "API Flask funcionando"}
```

### 6.2. Estado de la conexión

**Solicitud:** `GET /api/v1/salud`

- **`200 OK`** si la consulta de comprobación a MySQL funciona.
- **`503 Service Unavailable`** si no se puede establecer esa conexión; devuelve `{"estado":"error","base_datos":"sin conexion"}`.

### 6.3. Consultar préstamos con paginación y filtro

**Solicitud:** `GET /api/v1/prestamos`

Parámetros opcionales:

| Parámetro | Valor por defecto | Reglas |
|---|---|---|
| `limit` | `20` | Entero entre `1` y `100`. |
| `offset` | `0` | Entero mayor o igual que `0`. |
| `impago` | Sin filtro | Solamente `0` o `1`. |

Ejemplos:

```text
GET http://localhost:8000/api/v1/prestamos
GET http://localhost:8000/api/v1/prestamos?limit=10&offset=20
GET http://localhost:8000/api/v1/prestamos?impago=1&limit=10
```

La respuesta tiene esta estructura:

```json
{
  "datos": [
    {"row_id": 1, "id": "<identificador>", "edad": 35}
  ],
  "limit": 10,
  "offset": 0
}
```

*El objeto anterior es ilustrativo: en una consulta real, cada préstamo incluye las columnas almacenadas y sus valores correspondientes.*

La consulta está ordenada por `row_id`. Los valores incorrectos de `limit`, `offset` o `impago` producen una respuesta `400 Bad Request`.

### 6.4. Buscar un préstamo por identificador

**Solicitud:** `GET /api/v1/prestamos/<identificador>`

Ejemplo de formato:

```text
GET http://localhost:8000/api/v1/prestamos/123
```

La respuesta contiene `{"datos": [...]}`. **Se devuelve una lista**, no un único objeto, porque un mismo valor de `id` podría repetirse en el Excel. Si no existe ningún préstamo con ese identificador, el servidor devuelve **`404 Not Found`**.

### 6.5. Crear un préstamo

**Solicitud:** `POST /api/v1/prestamos`  
**Cabecera:** `Content-Type: application/json`

Ejemplo de llamada con `curl`:

```bash
curl -X POST http://localhost:8000/api/v1/prestamos \
  -H "Content-Type: application/json" \
  -d '{"id":"PRUEBA-001","edad":30,"ingresos":25000,"monto_inicial":10000,"impago":0}'
```

El ejemplo contiene los campos enviados para ilustrar el formato; el código permite un conjunto de campos correspondiente a las columnas existentes en MySQL, siempre que se incluya `id`.

Cuando la operación se completa, la respuesta tiene código **`201 Created`** y devuelve, por ejemplo:

```json
{
  "mensaje": "Prestamo creado correctamente",
  "row_id": 510705
}
```

El número `row_id` es **ilustrativo**: dependerá del estado de la base de datos. Si no se envía un objeto JSON válido, falta `id` o se incluyen columnas desconocidas, la API devuelve un error `400` con un mensaje explicativo.

**Limitación actual:** la implementación no incorpora una validación exhaustiva de los tipos, rangos ni obligatoriedad de todas las variables; algunas comprobaciones dependen de las restricciones de MySQL. Las inserciones modifican los datos persistentes y pueden alterar los totales estadísticos.

### 6.6. Consultar estadísticas

**Solicitud:** `GET /api/v1/estadisticas`

La respuesta utiliza estas claves:

```json
{
  "total_prestamos": 510704,
  "monto_medio": 45045.78,
  "total_impagos": 59307,
  "tasa_impago": 11.61
}
```

**Los valores mostrados corresponden a la carga original comprobada durante el desarrollo.** Si se insertan préstamos o se recarga otro fichero, los resultados pueden variar. La tasa de impago se devuelve como porcentaje y se redondea a dos decimales.

### 6.7. Consultar tipos de cambio externos

**Solicitud:** `GET /api/v1/tipos-cambio`

La API consulta `https://api.frankfurter.dev/v1/latest` mediante la biblioteca Requests.

Parámetros opcionales:

| Parámetro | Por defecto | Significado |
|---|---|---|
| `base` | `EUR` | Moneda de origen. |
| `destino` | `USD` | Moneda de destino. |

Ejemplo:

```text
GET http://localhost:8000/api/v1/tipos-cambio?base=EUR&destino=GBP
```

Los códigos deben contener exactamente **tres letras**. Si no cumplen el formato, la API devuelve `400`. Si falla la petición HTTP al servicio externo, devuelve `502 Bad Gateway`. La respuesta normal es el JSON proporcionado por Frankfurter y depende de su disponibilidad y de los códigos solicitados.

### 6.8. Exportación completa a CSV

**Solicitud:** `GET /api/v1/prestamos/exportar`

```text
http://localhost:8000/api/v1/prestamos/exportar
```

El servidor genera una descarga denominada **`prestamos.csv`** con las **19 columnas del Excel original**, normalizadas como nombres de campo. La clave técnica `row_id` queda excluida.

La exportación consulta los registros en orden de `row_id` y utiliza lectura por lotes de **2.000 filas**, enviando el CSV progresivamente en lugar de construir un único JSON con todos los registros. Esta ruta se creó para facilitar la conexión con Power BI.

En la carga original, la exportación contiene **510.704 registros**. Si posteriormente se insertan préstamos, también aparecerán en futuras exportaciones.

## 7. Integración con Power BI

El dashboard puede utilizar como origen web la dirección:

```text
http://localhost:8000/api/v1/prestamos/exportar
```

Power BI obtiene los datos en CSV y permite realizar su tratamiento posterior mediante Power Query, crear agrupaciones y dimensiones, definir medidas DAX y construir las visualizaciones.

La **actualización** de los datos requiere que el servicio Docker y la API estén en funcionamiento y que la URL sea accesible desde el ordenador que realiza la actualización. El archivo `.pbix` puede conservar datos ya cargados aunque la API no esté disponible en ese momento.

## 8. Comprobaciones recomendadas

Para verificar el entorno de forma básica:

1. Ejecutar `docker compose ps` y comprobar el estado de los servicios.
2. Consultar `http://localhost:8000/` y comprobar el mensaje de Flask.
3. Consultar `/api/v1/salud` y verificar `"base_datos": "conectada"`.
4. Consultar `/api/v1/estadisticas` y verificar los totales de la carga original.
5. Consultar `/api/v1/prestamos?limit=5` y comprobar que se reciben registros.
6. Descargar `/api/v1/prestamos/exportar` y comprobar que se obtiene `prestamos.csv`.
7. Si se desea probar la API externa, consultar `/api/v1/tipos-cambio`; se necesita acceso a Internet.

**Observación:** el ZIP revisado no contiene una carpeta de pruebas automatizadas ni archivos `test_*.py`. Por tanto, este README documenta las comprobaciones manuales posibles, pero no afirma que esta entrega incluya una batería de tests.

## 9. Resolución de problemas

**La API no responde en el puerto 8000.** Comprobar que Docker Desktop está funcionando y ejecutar `docker compose ps` y `docker compose logs api`. También conviene verificar que otro programa no esté utilizando el puerto `8000`.

**No se puede conectar con MySQL.** Revisar `docker compose logs db` y `/api/v1/salud`. MySQL dispone de una comprobación de salud y el cargador espera a que esté listo.

**El cargador no encuentra el Excel.** Verificar que existe `datos/Prestamos_Data_Alumnos_v5.xlsx`. La ruta usada dentro del contenedor es `/datos/Prestamos_Data_Alumnos_v5.xlsx`.

**La base de datos no se actualiza después de cambiar el Excel.** Con `FORCE_RELOAD=false`, el cargador evita sobrescribir una tabla que ya contiene filas. Para una importación nueva hay que forzar la recarga deliberadamente o regenerar el volumen, teniendo en cuenta la pérdida de datos añadidos.

**Conflicto de MySQL en `localhost:3306`.** El proyecto no publica ese puerto y se conecta mediante `db:3306` dentro de Docker. No es necesario configurar un puerto externo para MySQL.

**Power BI no actualiza los gráficos.** Verificar primero que `/api/v1/prestamos/exportar` responde. Después revisar los permisos del origen web y los pasos de Power Query. En el desarrollo del proyecto también se ajustó la carga paralela de tablas en Power BI para completar la actualización.

**Error en la API externa de tipos de cambio.** Comprobar la conexión a Internet y los parámetros `base` y `destino`. La ruta depende de la disponibilidad del servicio Frankfurter.

## 10. Limitaciones y posibles mejoras

El proyecto está orientado a un entorno académico y de desarrollo. La versión entregada ejecuta Flask en **modo depuración** (`--debug`) y utiliza credenciales definidas en Docker Compose; no está configurada para exposición pública.

Como posibles mejoras futuras se plantean la gestión de secretos mediante variables de entorno, la desactivación del modo depuración en producción, autenticación de usuarios, validaciones más completas de datos, tratamiento uniforme de errores de base de datos, pruebas automatizadas de endpoints y documentación interactiva con OpenAPI.

## 11. Conclusión

Con esta solución hemos integrado una base de datos MySQL, un proceso de carga desde Excel y una API REST desarrollada con Flask dentro de un mismo entorno Docker. La API permite consultar, incorporar y exportar información de préstamos, obtener estadísticas y consumir un servicio externo. Su ruta de exportación CSV facilita además el uso de los datos en Power BI.

La separación entre los servicios de base de datos, carga y API simplifica la organización del proyecto y permite conservar los registros entre ejecuciones mediante un volumen persistente.
