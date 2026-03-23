import os
import sys
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, MetaData
from alembic import context
from dotenv import load_dotenv

# Load .env from backend directory
load_dotenv(os.path.join(os.path.dirname(__file__), "../.env"))

# Add backend to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Get DATABASE_URL first before any app imports
raw_url = os.environ.get("DATABASE_URL", "")
if not raw_url:
    raise ValueError("DATABASE_URL not found in .env file")

# Convert asyncpg -> psycopg2 for Alembic sync driver
database_url = raw_url.replace(
    "postgresql+asyncpg://", "postgresql://"
)

# Now safe to import Base
# database.py will NOT create engine because init_db() not called
from app.core.database import Base

# Import all models so Alembic detects all tables
import app.models.models  # noqa: F401

target_metadata = Base.metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

config.set_main_option("sqlalchemy.url", database_url)

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
