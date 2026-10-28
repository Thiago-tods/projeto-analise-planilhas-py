from unittest.mock import MagicMock

import pandas as pd
import pytest

import importar_excel


def criar_venda():
    """Cria uma venda válida para os testes."""
    return pd.DataFrame({
        'ID Loja': ['1'],
        'Data': ['2026-01-15'],
        'Código Venda': [100],
        'Produto': ['Produto A'],
        'Quantidade': [2],
        'Valor Final': [100.00],
    })


def simular_conexao(monkeypatch):
    """Simula a conexão com o banco de dados."""
    conexao = MagicMock()
    transacao = MagicMock()
    transacao.__enter__.return_value = conexao

    monkeypatch.setattr(
        importar_excel.engine,
        'begin',
        lambda: transacao,
    )

    return conexao


def test_importar_vendas_rejeita_quantidade_zero(monkeypatch):
    vendas = criar_venda()
    vendas.loc[0, 'Quantidade'] = 0

    simular_conexao(monkeypatch)

    with pytest.raises(ValueError, match='quantidade'):
        importar_excel.importar_vendas(vendas)


def test_importar_vendas_rejeita_campo_obrigatorio_vazio(monkeypatch):
    vendas = criar_venda()
    vendas.loc[0, 'Produto'] = None

    simular_conexao(monkeypatch)

    with pytest.raises(ValueError, match='campos obrigatórios'):
        importar_excel.importar_vendas(vendas)



def test_importar_vendas_rejeita_valor_numerico_invalido(monkeypatch):
    vendas = criar_venda()

    # Converte a coluna para texto antes de inserir um valor inválido.
    vendas['Quantidade'] = vendas['Quantidade'].astype(str)
    vendas.loc[0, 'Quantidade'] = 'inválido'

    simular_conexao(monkeypatch)

    with pytest.raises((ValueError, TypeError)):
        importar_excel.importar_vendas(vendas)



def test_importar_vendas_remove_duplicatas(monkeypatch):
    vendas = criar_venda()

    # Duplica a linha para simular registros repetidos no arquivo.
    vendas = pd.concat(
        [vendas, vendas],
        ignore_index=True,
    )

    conexao = simular_conexao(monkeypatch)

    importar_excel.importar_vendas(vendas)

    # Recupera os registros enviados para a execução do SQL.
    registros = conexao.execute.call_args.args[1]

    assert len(registros) == 1
    assert registros[0]['produto'] == 'Produto A'
    assert registros[0]['quantidade'] == 2
def test_ler_bases_rejeita_arquivo_inexistente(monkeypatch):
    monkeypatch.setattr(
        importar_excel,
        'ARQUIVO_EMAILS',
        importar_excel.Path('arquivo_inexistente.xlsx'),
    )

    with pytest.raises(FileNotFoundError):
        importar_excel.ler_bases()


def test_ler_bases_rejeita_colunas_invalidas_em_lojas(monkeypatch):
    monkeypatch.setattr(
        importar_excel.Path,
        'exists',
        lambda self: True,
    )

    monkeypatch.setattr(
        importar_excel.pd,
        'read_excel',
        lambda arquivo: pd.DataFrame({
            'Coluna Errada': ['Loja A'],
        }),
    )

    monkeypatch.setattr(
        importar_excel.pd,
        'read_csv',
        lambda *args, **kwargs: pd.DataFrame({
            'Coluna Errada': ['1'],
        }),
    )

    with pytest.raises(ValueError, match='Lojas.csv'):
        importar_excel.ler_bases()


def test_ler_bases_rejeita_colunas_invalidas_em_emails(monkeypatch):
    monkeypatch.setattr(
        importar_excel.Path,
        'exists',
        lambda self: True,
    )

    monkeypatch.setattr(
        importar_excel.pd,
        'read_excel',
        lambda arquivo: pd.DataFrame({
            'Coluna Errada': ['Valor'],
        }),
    )

    monkeypatch.setattr(
        importar_excel.pd,
        'read_csv',
        lambda *args, **kwargs: pd.DataFrame({
            'ID Loja': ['1'],
            'Loja': ['Loja A'],
        }),
    )

    with pytest.raises(ValueError, match='Emails.xlsx'):
        importar_excel.ler_bases()
def test_ler_bases_rejeita_colunas_invalidas_em_vendas(monkeypatch):
    monkeypatch.setattr(
        importar_excel.Path,
        'exists',
        lambda self: True,
    )

    def ler_excel_simulado(arquivo):
        if arquivo == importar_excel.ARQUIVO_EMAILS:
            return pd.DataFrame({
                'Loja': ['Loja A'],
                'Gerente': ['Gerente A'],
                'E-mail': ['gerente@exemplo.com'],
            })

        return pd.DataFrame({
            'ID Loja': ['1'],
            'Produto': ['Produto A'],
        })

    monkeypatch.setattr(
        importar_excel.pd,
        'read_excel',
        ler_excel_simulado,
    )

    monkeypatch.setattr(
        importar_excel.pd,
        'read_csv',
        lambda *args, **kwargs: pd.DataFrame({
            'ID Loja': ['1'],
            'Loja': ['Loja A'],
        }),
    )

    with pytest.raises(ValueError, match='Vendas.xlsx'):
        importar_excel.ler_bases()
def test_main_executa_etapas_da_importacao(monkeypatch):
    import importar_excel

    chamadas = []

    emails_teste = pd.DataFrame()
    lojas_teste = pd.DataFrame()
    vendas_teste = pd.DataFrame()

    def ler_bases_simulado():
        chamadas.append('ler_bases')
        return emails_teste, lojas_teste, vendas_teste

    def preparar_tabelas_simulado():
        chamadas.append('preparar_tabelas')

    def importar_lojas_simulado(emails, lojas):
        chamadas.append('importar_lojas')
        assert emails is emails_teste
        assert lojas is lojas_teste

    def importar_vendas_simulado(vendas):
        chamadas.append('importar_vendas')
        assert vendas is vendas_teste

    monkeypatch.setattr(importar_excel, 'ler_bases', ler_bases_simulado)
    monkeypatch.setattr(
        importar_excel,
        'preparar_tabelas',
        preparar_tabelas_simulado,
    )
    monkeypatch.setattr(
        importar_excel,
        'importar_lojas',
        importar_lojas_simulado,
    )
    monkeypatch.setattr(
        importar_excel,
        'importar_vendas',
        importar_vendas_simulado,
    )

    importar_excel.main()

    assert chamadas == [
        'ler_bases',
        'preparar_tabelas',
        'importar_lojas',
        'importar_vendas',
    ]
def test_ler_bases_retorna_dataframes_validos(monkeypatch):
    emails_teste = pd.DataFrame({
        'Loja': ['Loja A'],
        'Gerente': ['Gerente A'],
        'E-mail': ['gerente@exemplo.com'],
    })

    lojas_teste = pd.DataFrame({
        'ID Loja': ['001'],
        'Loja': ['Loja A'],
    })

    vendas_teste = criar_venda()

    monkeypatch.setattr(
        importar_excel.Path,
        'exists',
        lambda self: True,
    )

    def ler_excel_simulado(arquivo):
        if arquivo == importar_excel.ARQUIVO_EMAILS:
            return emails_teste

        return vendas_teste

    def ler_csv_simulado(*args, **kwargs):
        assert kwargs['sep'] == ';'
        assert kwargs['encoding'] == 'latin1'
        assert kwargs['dtype'] == {'ID Loja': str}

        return lojas_teste

    monkeypatch.setattr(
        importar_excel.pd,
        'read_excel',
        ler_excel_simulado,
    )

    monkeypatch.setattr(
        importar_excel.pd,
        'read_csv',
        ler_csv_simulado,
    )

    emails, lojas, vendas = importar_excel.ler_bases()

    assert emails.equals(emails_teste)
    assert lojas.equals(lojas_teste)
    assert vendas.equals(vendas_teste)
    assert lojas.loc[0, 'ID Loja'] == '001'