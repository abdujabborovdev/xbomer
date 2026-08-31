from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, BigInteger, DateTime, Column
from data.config import *
DB_KEY = DB_KEY

class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    hisob: Mapped[int] = mapped_column(Integer, nullable=True, default=0)
    username: Mapped[str] = mapped_column(String(115), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)

class Transaction(Base):
    __tablename__ = 'transactions'

    order_id = Column(String, primary_key=True, unique=True, nullable=False, index=True)
    telegram_id = Column(BigInteger, nullable=False)
    summa = Column(BigInteger, nullable=False)
    holat = Column(String, default="pending")
    vaqti = Column(DateTime, default=datetime.now)

class Numbers_list(Base):
    __tablename__ = 'number_list'
    id = Column(Integer, primary_key=True)
    country = Column(String, nullable=False)
    price = Column(BigInteger, nullable=False)

class Order_numbers(Base):
    __tablename__ = 'orders_number'
    id = Column(Integer, primary_key=True)
    country = Column(String, nullable=False)
    owner_number = Column(BigInteger, nullable=False)
    number = Column(String)
    status = Column(String, default="WAITING")
    kod = Column(BigInteger, default=0)
    pas2 = Column(String, default='None')

class SecretApiKey(Base):
    __tablename__ = 'secret_api_key'
    id = Column(Integer, primary_key=True)
    user_telegram_id = Column(BigInteger, nullable=False)
    secret_api_key = Column(String(115), unique=True, nullable=False, index=True)

engine = create_async_engine(DB_KEY, echo=True)

async_session = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with async_session() as session:
        yield session