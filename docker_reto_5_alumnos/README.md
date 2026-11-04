
Este proyecto proporciona un entorno Docker con una base de datos MySQL ya preparada y cargada a partir de los datos disponibles en `datos/datos.xlsx`.

La base de datos utiliza almacenamiento persistente mediante un volumen Docker.

## Arranque

```bash
docker compose up --build
```

Servicios disponibles:

* API Flask: `http://localhost:8000`
* MySQL: `localhost:3306`
* Base de datos: `creditos`
* Usuario: `clase`
* Contraseña: `clase123`
* Tabla: `clientes_credito`

## Estructura

```text
.
├── api/
│   ├── Dockerfile
│   ├── main.py
│   └── requirements.txt
│
├── datos/
│   └── datos.xlsx
│
├── loader/
│   ├── Dockerfile
│   ├── load_data.py
│   └── requirements.txt
│
├── docker-compose.yml
└── README.md
```

El trabajo sobre la API se realizará principalmente en:

```text
api/main.py
```

## Persistencia

Los datos de MySQL se almacenan en un volumen Docker y se mantienen aunque se detengan los contenedores:

```bash
docker compose down
```

Para volver a levantar el entorno:

```bash
docker compose up
```

Si se elimina el volumen:

```bash
docker compose down -v
```

la base de datos se volverá a generar a partir del fichero de datos en el siguiente arranque.
