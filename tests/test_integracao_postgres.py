from unittest.mock import MagicMock
import pytest
import database
import pandas as pd
from sqlalchemy import text

from importar_excel import importar_lojas, importar_vendas


def test_conexao_com_postgresql(engine_teste, limpar_tabelas):
    with engine_teste.connect() as conexao:
        banco = conexao.execute(
            text('SELECT current_database()')
        ).scalar()

        quantidade_lojas = conexao.execute(
            text('SELECT COUNT(*) FROM lojas')
        ).scalar()

        quantidade_vendas = conexao.execute(
            text('SELECT COUNT(*) FROM vendas')
        ).scalar()

    assert banco == 'relatorios_vendas_testes'
    assert quantidade_lojas == 0
    assert quantidade_vendas == 0


def test_importar_loja_no_postgresql(engine_teste, limpar_tabelas, monkeypatch):
    emails = pd.DataFrame({
        'Loja': ['Loja A'],
        'Gerente': ['Maria'],
        'E-mail': ['maria@exemplo.com'],
    })

    lojas = pd.DataFrame({
        'ID Loja': ['1'],
        'Loja': ['Loja A'],
    })

    # Redireciona a função para o banco de testes.
    monkeypatch.setattr('importar_excel.engine', engine_teste)

    importar_lojas(emails, lojas)

    with engine_teste.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT id_loja, nome, gerente, email
                FROM lojas
                WHERE id_loja = '1'
            """)
        ).mappings().one()

    assert resultado['id_loja'] == '1'
    assert resultado['nome'] == 'Loja A'
    assert resultado['gerente'] == 'Maria'
    assert resultado['email'] == 'maria@exemplo.com'


def test_reimportar_loja_atualiza_dados(
    engine_teste,
    limpar_tabelas,
    monkeypatch,
):
    monkeypatch.setattr('importar_excel.engine', engine_teste)

    lojas = pd.DataFrame({
        'ID Loja': ['1'],
        'Loja': ['Loja A'],
    })

    emails_antigos = pd.DataFrame({
        'Loja': ['Loja A'],
        'Gerente': ['Maria'],
        'E-mail': ['maria@exemplo.com'],
    })

    emails_novos = pd.DataFrame({
        'Loja': ['Loja A'],
        'Gerente': ['João'],
        'E-mail': ['joao@exemplo.com'],
    })

    importar_lojas(emails_antigos, lojas)
    importar_lojas(emails_novos, lojas)

    with engine_teste.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT gerente, email
                FROM lojas
                WHERE id_loja = '1'
            """)
        ).mappings().one()

        quantidade = conexao.execute(
            text("""
                SELECT COUNT(*)
                FROM lojas
                WHERE id_loja = '1'
            """)
        ).scalar_one()

    assert resultado['gerente'] == 'João'
    assert resultado['email'] == 'joao@exemplo.com'
    assert quantidade == 1
def test_importar_venda_no_postgresql(
    engine_teste,
    limpar_tabelas,
    monkeypatch,
):
    monkeypatch.setattr('importar_excel.engine', engine_teste)

    vendas = pd.DataFrame({
        'ID Loja': ['1'],
        'Data': ['2026-01-15'],
        'Código Venda': [100],
        'Produto': ['Produto A'],
        'Quantidade': [2],
        'Valor Final': [100.00],
    })

    importar_vendas(vendas)

    with engine_teste.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT
                    id_loja,
                    codigo_venda,
                    produto,
                    quantidade,
                    valor_final
                FROM vendas
                WHERE id_loja = '1'
            """)
        ).mappings().one()

    assert resultado['id_loja'] == '1'
    assert resultado['codigo_venda'] == '100'
    assert resultado['produto'] == 'Produto A'
    assert resultado['quantidade'] == 2
    assert float(resultado['valor_final']) == 100.00
def test_importar_venda_duplicada_nao_duplica_registro(
    engine_teste,
    limpar_tabelas,
    monkeypatch,
):
    monkeypatch.setattr('importar_excel.engine', engine_teste)

    # Cria um índice único para impedir duplicatas.
    with engine_teste.begin() as conexao:
        conexao.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS uq_vendas_importacao
            ON vendas (
                id_loja,
                data_venda,
                codigo_venda,
                produto,
                quantidade,
                valor_final
            )
        """))

    vendas = pd.DataFrame({
        'ID Loja': ['1'],
        'Data': ['2026-01-15'],
        'Código Venda': [100],
        'Produto': ['Produto A'],
        'Quantidade': [2],
        'Valor Final': [100.00],
    })

    importar_vendas(vendas)
    importar_vendas(vendas)

    with engine_teste.connect() as conexao:
        quantidade = conexao.execute(
            text("""
                SELECT COUNT(*)
                FROM vendas
                WHERE id_loja = '1'
                  AND codigo_venda = '100'
                  AND produto = 'Produto A'
            """)
        ).scalar_one()

    assert quantidade == 1
def test_testar_conexao_com_sucesso(monkeypatch, capsys):
    conexao_simulada = MagicMock()
    resultado_simulado = MagicMock()

    resultado_simulado.scalar.return_value = 'relatorios_vendas_testes'

    conexao_simulada.execute.return_value = resultado_simulado

    gerenciador_conexao = MagicMock()
    gerenciador_conexao.__enter__.return_value = conexao_simulada

    monkeypatch.setattr(
        database.engine,
        'connect',
        lambda: gerenciador_conexao,
    )

    database.testar_conexao()

    saida = capsys.readouterr().out

    assert 'Conexão estabelecida!' in saida
    assert 'relatorios_vendas_testes' in saida
    conexao_simulada.execute.assert_called_once()
def test_testar_conexao_propaga_erro(monkeypatch):
    def falhar_conexao():
        raise RuntimeError('Falha simulada de conexão')

    monkeypatch.setattr(
        database.engine,
        'connect',
        falhar_conexao,
    )

    with pytest.raises(
        RuntimeError,
        match='Falha simulada de conexão',
    ):
        database.testar_conexao()
def test_importar_loja_utiliza_primeiro_email_duplicado(
    engine_teste,
    limpar_tabelas,
    monkeypatch,
):
    monkeypatch.setattr('importar_excel.engine', engine_teste)

    lojas = pd.DataFrame({
        'ID Loja': ['1'],
        'Loja': ['Loja A'],
    })

    emails = pd.DataFrame({
        'Loja': ['Loja A', 'Loja A'],
        'Gerente': ['Maria', 'João'],
        'E-mail': ['maria@exemplo.com', 'joao@exemplo.com'],
    })

    importar_lojas(emails, lojas)

    with engine_teste.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT gerente, email
                FROM lojas
                WHERE id_loja = '1'
            """)
        ).mappings().one()

    assert resultado['gerente'] == 'Maria'
    assert resultado['email'] == 'maria@exemplo.com'
def test_importar_loja_sem_gerente_ou_email(
    engine_teste,
    limpar_tabelas,
    monkeypatch,
):
    monkeypatch.setattr('importar_excel.engine', engine_teste)

    lojas = pd.DataFrame({
        'ID Loja': ['2'],
        'Loja': ['Loja B'],
    })

    emails = pd.DataFrame({
        'Loja': ['Outra Loja'],
        'Gerente': ['Outro Gerente'],
        'E-mail': ['outro@exemplo.com'],
    })

    importar_lojas(emails, lojas)

    with engine_teste.connect() as conexao:
        resultado = conexao.execute(
            text("""
                SELECT id_loja, nome, gerente, email
                FROM lojas
                WHERE id_loja = '2'
            """)
        ).mappings().one()

    assert resultado['id_loja'] == '2'
    assert resultado['nome'] == 'Loja B'
    assert resultado['gerente'] is None
    assert resultado['email'] is None