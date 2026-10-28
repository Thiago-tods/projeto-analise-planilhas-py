import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

url = URL.create(
    "postgresql+psycopg",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
)

engine = create_engine(url, pool_pre_ping=True)


def testar_conexao():
    with engine.connect() as conexao:
        resultado = conexao.execute(
            text("SELECT current_database()")
        )

        print("Conexão estabelecida!")
        print(f"Banco conectado: {resultado.scalar()}")


if __name__ == "__main__":
    testar_conexao()