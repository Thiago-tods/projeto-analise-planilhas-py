import pandas as pd


def calcular_faturamento(vendas):
    """Calcula o faturamento total das vendas."""
    return vendas["Valor Final"].sum()


def contar_pedidos(vendas):
    """Conta os pedidos distintos por loja, data e código da venda."""
    colunas_pedido = ["ID Loja", "Data", "Código Venda"]

    return vendas[colunas_pedido].drop_duplicates().shape[0]


def calcular_ticket_medio(vendas):
    """Calcula o faturamento total dividido pelos pedidos distintos."""
    quantidade_pedidos = contar_pedidos(vendas)

    if quantidade_pedidos == 0:
        return 0

    faturamento = calcular_faturamento(vendas)

    return faturamento / quantidade_pedidos


def calcular_faturamento_por_loja(vendas):
    """Calcula o faturamento total de cada loja."""
    return (
        vendas.groupby("Loja")["Valor Final"]
        .sum()
        .sort_values(ascending=False)
    )