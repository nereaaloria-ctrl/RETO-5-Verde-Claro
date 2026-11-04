import os
import re
import unicodedata
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, inspect, text

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://clase:clase123@db:3306/creditos",
)

DATA_FILE = Path(os.getenv("DATA_FILE", "/datos/datos.xlsx"))
TABLE_NAME = "clientes_credito"

FORCE_RELOAD = (
    os.getenv("FORCE_RELOAD", "false").lower()
    in {"1", "true", "yes", "si"}
)


def normalize_column(name: str) -> str:
    """
    Normaliza únicamente los nombres de las columnas.
    """
    value = unicodedata.normalize(
        "NFKD", str(name)
    ).encode("ascii", "ignore").decode("ascii")

    value = value.strip().lower().replace(" ", "_")
    value = re.sub(r"[^a-z0-9_]+", "", value)
    value = re.sub(r"_+", "_", value)

    return value.strip("_")


def read_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(
            f"No existe el fichero de datos: {path}"
        )

    suffix = path.suffix.lower()

    if suffix in {".xlsx", ".xls"}:
        # dtype=object para evitar conversiones innecesarias
        return pd.read_excel(path, dtype=object)

    if suffix == ".csv":
        return pd.read_csv(
            path,
            sep=None,
            engine="python",
            dtype=object,
        )

    raise ValueError(
        "Formato no soportado. Usa .xlsx, .xls o .csv"
    )


def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara únicamente la estructura.
    """
    df = df.copy()

    df.columns = [
        normalize_column(column)
        for column in df.columns
    ]

    required = {
        "id",
        "edad",
        "ingresos",
        "monto_inicial",
        "scoring_crediticio",
        "meses_empleo",
        "num_creditos",
        "ratio_interes",
        "duracion",
        "ratio_deuda_ingresos",
        "estudios",
        "tipo_jornada_laboral",
        "estado_civil",
        "posesion_hipoteca",
        "personas_cargo",
        "proposito",
        "fiador",
        "impago",
        "prima",
    }

    missing = sorted(required - set(df.columns))

    if missing:
        raise ValueError(
            "Faltan columnas obligatorias: "
            + ", ".join(missing)
        )

    print("\n--- INFORMACIÓN SOBRE LOS DATOS ---")

    for col in df.columns:
        nulos = int(df[col].isna().sum())

        if nulos > 0:
            print(
                f"AVISO: '{col}' contiene "
                f"{nulos} valores nulos."
            )

    if df["id"].duplicated().any():
        duplicados = int(df["id"].duplicated().sum())

        print(
            f"AVISO: existen {duplicados} IDs duplicados."
        )

    print("---------------------------------\n")

    return df


def table_has_data(engine) -> bool:
    inspector = inspect(engine)

    if not inspector.has_table(TABLE_NAME):
        return False

    with engine.connect() as conn:
        count = conn.execute(
            text(
                f"SELECT COUNT(*) "
                f"FROM {TABLE_NAME}"
            )
        ).scalar_one()

    return count > 0


def main() -> None:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )

    if table_has_data(engine) and not FORCE_RELOAD:

        with engine.connect() as conn:
            count = conn.execute(
                text(
                    f"SELECT COUNT(*) "
                    f"FROM {TABLE_NAME}"
                )
            ).scalar_one()

        print(
            f"La tabla '{TABLE_NAME}' ya contiene "
            f"{count} filas."
        )
        print(
            "Los datos se conservan gracias "
            "al volumen persistente."
        )
        return

    print(
        f"Leyendo datos desde {DATA_FILE}..."
    )

    df = prepare_data(
        read_data(DATA_FILE)
    )

    print(
        f"Cargando {len(df)} registros "
        "sin limpiar..."
    )

    # Pandas enviará los NaN como NULL.
    df.to_sql(
        TABLE_NAME,
        engine,
        if_exists="replace",
        index=False,
    )

    # El ID original NO es primary key porque puede
    # estar duplicado.
    
    # Creamos una clave técnica independiente.
    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                ALTER TABLE {TABLE_NAME}
                ADD COLUMN row_id BIGINT
                NOT NULL AUTO_INCREMENT
                PRIMARY KEY FIRST
                """
            )
        )

    print(
        f"Carga completada: {len(df)} filas "
        f"en '{TABLE_NAME}'."
    )
    print(
        "Los datos se han almacenado SIN LIMPIAR."
    )


if __name__ == "__main__":
    main()