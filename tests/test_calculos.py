import pandas as pd
import pytest

from calculos import (
    calcular_faturamento,
    contar_pedidos,
    calcular_ticket_medio,
    calcular_faturamento_por_loja,
)


@pytest.fixture
def vendas_exemplo():
    """Cria dados fictícios para os testes."""
    return pd.DataFrame({
        "ID Loja": ["1", "1", "1", "2"],
        "Data": pd.to_datetime([
            "2026-01-01",
            "2026-01-01",
            "2026-01-01",
            "2026-01-01",
        ]),
        "Código Venda": ["1001", "1001", "1002", "2001"],
        "Loja": [
            "Loja A",
            "Loja A",
            "Loja A",
            "Loja B",
        ],
        "Produto": [
            "Teclado",
            "Mouse",
            "Monitor",
            "Teclado",
        ],
        "Quantidade": [1, 1, 1, 1],
        "Valor Final": [200.00, 100.00, 700.00, 300.00],
    })


def test_calcular_faturamento(vendas_exemplo):
    resultado = calcular_faturamento(vendas_exemplo)

    assert resultado == pytest.approx(1300.00)


def test_contar_pedidos(vendas_exemplo):
    resultado = contar_pedidos(vendas_exemplo)

    assert resultado == 3


def test_calcular_ticket_medio(vendas_exemplo):
    resultado = calcular_ticket_medio(vendas_exemplo)

    assert resultado == pytest.approx(1300.00 / 3)


def test_calcular_faturamento_por_loja(vendas_exemplo):
    resultado = calcular_faturamento_por_loja(vendas_exemplo)

    assert resultado["Loja A"] == pytest.approx(1000.00)
    assert resultado["Loja B"] == pytest.approx(300.00)
def test_calcular_faturamento_com_tabela_vazia():
    vendas = pd.DataFrame({
        "Valor Final": []
    })

    resultado = calcular_faturamento(vendas)

    assert resultado == 0
def test_contar_pedidos_em_datas_diferentes():
    vendas = pd.DataFrame({
        "ID Loja": ["1", "1"],
        "Data": pd.to_datetime(["2026-01-01", "2026-01-02"]),
        "Código Venda": ["1001", "1001"],
    })

    resultado = contar_pedidos(vendas)

    assert resultado == 2
def test_calcular_ticket_medio_sem_vendas():
    vendas = pd.DataFrame({
        "ID Loja": [],
        "Data": [],
        "Código Venda": [],
        "Valor Final": [],
    })

    resultado = calcular_ticket_medio(vendas)

    assert resultado == 0
def test_calcular_faturamento_sem_coluna_necessaria():
    vendas = pd.DataFrame({
        "Produto": ["Teclado", "Mouse"],
    })

    with pytest.raises(KeyError):
        calcular_faturamento(vendas)