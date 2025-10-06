from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from loguru import logger
from urllib.parse import quote_plus
import config

DATABASE_URL = f"mysql+aiomysql://{quote_plus(config.DB_USER)}:{quote_plus(config.DB_PASSWORD)}@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}"

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()

async def init_database():
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.success("Database tables created/verified")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        raise

async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session