import logging
import re
from typing import Tuple
from urllib.parse import urlparse, unquote, quote_plus
import pandas as pd
from sqlalchemy import create_engine, text, Engine

logger = logging.getLogger("pqrs.ingestion.repository")


class DynamicDatabaseRepository:
    def __init__(self, db_url: str):
        self.db_url = self._format_db_url(db_url)
        # Usamos psycopg v3 de forma explícita
        self.engine: Engine = create_engine(
            self.db_url,
            pool_pre_ping=True,
            pool_recycle=3600
        )

    def _format_db_url(self, raw_url: str) -> str:
        if not raw_url:
            raise ValueError("DATABASE_URL no puede estar vacía.")

        if raw_url.startswith("postgres://"):
            raw_url = raw_url.replace("postgres://", "postgresql+psycopg://", 1)
        elif raw_url.startswith("postgresql://") and "+psycopg" not in raw_url:
            raw_url = raw_url.replace("postgresql://", "postgresql+psycopg://", 1)

        try:
            parsed = urlparse(raw_url)
            scheme = parsed.scheme or "postgresql+psycopg"
            username = quote_plus(unquote(parsed.username)) if parsed.username else ""
            password = quote_plus(unquote(parsed.password)) if parsed.password else ""
            hostname = parsed.hostname or "localhost"
            port = f":{parsed.port}" if parsed.port else ""
            database = parsed.path.lstrip("/")

            auth = f"{username}:{password}@" if username or password else ""
            return f"{scheme}://{auth}{hostname}{port}/{database}"
        except Exception:
            return raw_url

    @staticmethod
    def _clean_identifier(identifier: str) -> str:
        identifier = str(identifier).strip().lower()
        replacements = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'ñ': 'n'}
        for char, repl in replacements.items():
            identifier = identifier.replace(char, repl)
        cleaned = re.sub(r'[^a-z0-9_]', '_', identifier)
        return re.sub(r'_+', '_', cleaned).strip('_') or "tabla_ingestion"

    def _detect_schema_columns(self, df: pd.DataFrame) -> Tuple[str, str]:
        """
        Analiza las columnas del DataFrame recién limpiado para deducir
        cuál corresponde al texto/descripción y cuál a la categoría.
        """
        cols = [col.lower() for col in df.columns]

        text_keywords = ['description', 'descripcion', 'texto', 'detalle', 'peticion', 'mensaje', 'asunto',
                         'observacion']
        category_keywords = ['category', 'categoria', 'tipo', 'clase', 'label', 'tag', 'rideable_type',
                             'tipo_bicicleta', 'motivo']

        text_col = next((c for c in text_keywords if c in cols), None)
        cat_col = next((c for c in category_keywords if c in cols), None)

        # Si no coinciden palabras clave, tomar por posición o tipo
        if not text_col:
            text_col = cols[0] if len(cols) > 0 else "description"
        if not cat_col:
            remaining = [c for c in cols if c != text_col]
            cat_col = remaining[0] if remaining else "category"

        return text_col, cat_col

    def save(self, df: pd.DataFrame, table_name: str, source_type: str = "MANUAL") -> tuple[str, str, str]:
        if df is None or df.empty:
            raise ValueError("El DataFrame provisto está vacío.")

        clean_table_name = self._clean_identifier(table_name)
        df_clean = df.copy()
        df_clean.columns = [self._clean_identifier(col) for col in df_clean.columns]

        # Detección automática de columnas de metadatos
        text_col, cat_col = self._detect_schema_columns(df_clean)

        logger.info(
            f"Guardando {len(df_clean)} registros en '{clean_table_name}'. "
            f"Campos detectados: texto='{text_col}', categoria='{cat_col}'"
        )

        with self.engine.begin() as connection:
            df_clean.to_sql(
                name=clean_table_name,
                con=connection,
                if_exists="replace",
                index=False
            )

            self._register_catalog_entry(
                connection=connection,
                table_name=clean_table_name,
                source_type=source_type,
                row_count=len(df_clean),
                text_column=text_col,
                category_column=cat_col
            )

        logger.info(f"Persistencia exitosa y registro actualizado en el catálogo para '{clean_table_name}'.")

        return clean_table_name, text_col, cat_col

    def _register_catalog_entry(
            self,
            connection,
            table_name: str,
            source_type: str,
            row_count: int,
            text_column: str,
            category_column: str
    ) -> None:

        # 1. Crear la tabla del catálogo incluyendo metadatos de esquema
        create_catalog_sql = text("""
            CREATE TABLE IF NOT EXISTS data_sources_catalog (
                id SERIAL PRIMARY KEY,
                table_name VARCHAR(255) UNIQUE NOT NULL,
                source_type VARCHAR(100) NOT NULL,
                row_count INT NOT NULL,
                text_column VARCHAR(100) DEFAULT 'description',
                category_column VARCHAR(100) DEFAULT 'category',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        connection.execute(create_catalog_sql)

        # Migración al vuelo por si la tabla existía previamente sin las columnas
        connection.execute(text("""
            ALTER TABLE data_sources_catalog 
            ADD COLUMN IF NOT EXISTS text_column VARCHAR(100) DEFAULT 'description',
            ADD COLUMN IF NOT EXISTS category_column VARCHAR(100) DEFAULT 'category';
        """))

        # 2. Upsert con la actualización de las columnas detectadas
        upsert_catalog_sql = text("""
            INSERT INTO data_sources_catalog (
                table_name, source_type, row_count, text_column, category_column, created_at
            )
            VALUES (
                :table_name, :source_type, :row_count, :text_column, :category_column, CURRENT_TIMESTAMP
            )
            ON CONFLICT (table_name) 
            DO UPDATE SET 
                source_type = EXCLUDED.source_type,
                row_count = EXCLUDED.row_count,
                text_column = EXCLUDED.text_column,
                category_column = EXCLUDED.category_column,
                created_at = CURRENT_TIMESTAMP;
        """)

        connection.execute(
            upsert_catalog_sql,
            {
                "table_name": table_name,
                "source_type": source_type,
                "row_count": row_count,
                "text_column": text_column,
                "category_column": category_column
            }
        )