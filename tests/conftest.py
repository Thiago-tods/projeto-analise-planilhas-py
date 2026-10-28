import os

import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL


@pytest.fixture(scope='session')
def engine_teste():
    # Carrega as configurações exclusivas dos testes.
    load_dotenv('.env.test', override=True)

    url = URL.create(
        'postgresql+psycopg',
        username=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME'),
    )

    if url.database != 'relatorios_vendas_testes':
        pytest.fail(
            'Os testes devem utilizar exclusivamente '
            'o banco relatorios_vendas_testes.'
        )

    engine = create_engine(url, pool_pre_ping=True)

    with engine.begin() as conexao:
        conexao.execute(text("""
            CREATE TABLE IF NOT EXISTS lojas (
                id_loja VARCHAR PRIMARY KEY,
                nome VARCHAR NOT NULL,
                gerente VARCHAR,
                email VARCHAR
            )
        """))

        conexao.execute(text("""
            CREATE TABLE IF NOT EXISTS vendas (
                id SERIAL PRIMARY KEY,
                id_loja VARCHAR NOT NULL,
                data_venda TIMESTAMP NOT NULL,
                codigo_venda VARCHAR NOT NULL,
                produto VARCHAR NOT NULL,
                quantidade INTEGER NOT NULL,
                valor_final NUMERIC(12, 2) NOT NULL
            )
        """))

    yield engine

    engine.dispose()


@pytest.fixture
def limpar_tabelas(engine_teste):
    # Limpa os dados antes de cada teste.
    with engine_teste.begin() as conexao:
        conexao.execute(
            text('TRUNCATE TABLE vendas, lojas RESTART IDENTITY')
        )

    yield

    # Limpa novamente após o teste.
    with engine_teste.begin() as conexao:
        conexao.execute(
            text('TRUNCATE TABLE vendas, lojas RESTART IDENTITY')
        )