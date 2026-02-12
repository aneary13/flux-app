import os
from logging.config import fileConfig

from dotenv import load_dotenv
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context
from sqlmodel import SQLModel

# Load environment variables from .env file
load_dotenv()

# Import all models to ensure they are registered with SQLModel.metadata
from src.db.models import (  # noqa: E402, F401
    ConditioningBenchmark,
    ConditioningProgress,
    ConditioningProtocol,
    DailyReadiness,
    Exercise,
    PatternHistory,
    User,
    WorkoutSession,
    WorkoutSet,
)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target_metadata to SQLModel.metadata for autogenerate support
# This allows Alembic to detect all SQLModel tables
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Get DATABASE_URL from environment variable
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError("DATABASE_URL environment variable is not set")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode with async support.

    In this scenario we need to create an AsyncEngine
    and associate a connection with the context.

    """
    # Get DATABASE_URL from environment variable
    url = os.getenv("DATABASE_URL")
    if not url:
        raise ValueError(
            "DATABASE_URL environment variable is not set. "
            "Please create a .env file in the backend/ directory with your database connection string. "
            "Example: DATABASE_URL=postgresql+asyncpg://user:password@host:port/database"
        )

    # Validate URL format
    if not url.startswith("postgresql+asyncpg://"):
        raise ValueError(
            f"Invalid DATABASE_URL format. Expected 'postgresql+asyncpg://...' but got: {url[:50]}..."
            if len(url) > 50
            else f"Invalid DATABASE_URL format. Expected 'postgresql+asyncpg://...' but got: {url}"
        )

    # Create async engine for asyncpg
    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    async def run_async_migrations() -> None:
        """Run migrations in async context."""
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

    def do_run_migrations(connection) -> None:
        """Execute migrations using the connection."""
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    # Run async migrations
    import asyncio

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
