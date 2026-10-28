from pathlib import Path

import pandas as pd
from sqlalchemy import text

from database import engine


# Pasta que contém os arquivos originais.
PASTA_BASES = Path("Bases de Dados")

ARQUIVO_EMAILS = PASTA_BASES / "Emails.xlsx"
ARQUIVO_LOJAS = PASTA_BASES / "Lojas.csv"
ARQUIVO_VENDAS = PASTA_BASES / "Vendas.xlsx"


def ler_bases():
    """Lê e valida os arquivos de origem."""

    for arquivo in [ARQUIVO_EMAILS, ARQUIVO_LOJAS, ARQUIVO_VENDAS]:
        if not arquivo.exists():
            raise FileNotFoundError(
                f"Arquivo não encontrado: {arquivo.resolve()}"
            )

    emails = pd.read_excel(ARQUIVO_EMAILS)

    lojas = pd.read_csv(
        ARQUIVO_LOJAS,
        sep=";",
        encoding="latin1",
        dtype={"ID Loja": str},
    )

    vendas = pd.read_excel(ARQUIVO_VENDAS)

    colunas_lojas = {"ID Loja", "Loja"}
    colunas_emails = {"Loja", "Gerente", "E-mail"}
    colunas_vendas = {
        "ID Loja",
        "Data",
        "Código Venda",
        "Produto",
        "Quantidade",
        "Valor Final",
    }

    if not colunas_lojas.issubset(lojas.columns):
        raise ValueError("O arquivo Lojas.csv não contém as colunas esperadas.")

    if not colunas_emails.issubset(emails.columns):
        raise ValueError("O arquivo Emails.xlsx não contém as colunas esperadas.")

    if not colunas_vendas.issubset(vendas.columns):
        raise ValueError("O arquivo Vendas.xlsx não contém todas as colunas esperadas.")

    return emails, lojas, vendas


def preparar_tabelas():
    """Cria uma restrição para impedir a duplicação das vendas."""

    with engine.begin() as conexao:
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


def importar_lojas(emails, lojas):
    """Insere lojas novas e atualiza os dados das lojas existentes."""

    emails = emails.drop_duplicates(subset="Loja", keep="first")

    dados_lojas = lojas.merge(
        emails[["Loja", "Gerente", "E-mail"]],
        on="Loja",
        how="left",
    )

    dados_lojas = dados_lojas.rename(columns={
        "ID Loja": "id_loja",
        "Loja": "nome",
        "Gerente": "gerente",
        "E-mail": "email",
    })

    dados_lojas["id_loja"] = dados_lojas["id_loja"].astype(str)

    dados = dados_lojas[
        ['id_loja', 'nome', 'gerente', 'email']
    ].astype(object)

    dados = dados.where(pd.notna(dados), None)


    comando = text("""
        INSERT INTO lojas (id_loja, nome, gerente, email)
        VALUES (:id_loja, :nome, :gerente, :email)
        ON CONFLICT (id_loja)
        DO UPDATE SET
            nome = EXCLUDED.nome,
            gerente = EXCLUDED.gerente,
            email = EXCLUDED.email
    """)

    with engine.begin() as conexao:
        conexao.execute(comando, dados.to_dict(orient="records"))

    print(f"Lojas processadas: {len(dados)}")


def importar_vendas(vendas):
    """Insere vendas sem repetir registros já importados."""

    vendas = vendas.rename(columns={
        "ID Loja": "id_loja",
        "Data": "data_venda",
        "Código Venda": "codigo_venda",
        "Produto": "produto",
        "Quantidade": "quantidade",
        "Valor Final": "valor_final",
    }).copy()

    vendas["id_loja"] = vendas["id_loja"].astype(str)
    vendas["data_venda"] = pd.to_datetime(
        vendas["data_venda"],
        errors="raise",
    )

    vendas["quantidade"] = pd.to_numeric(
        vendas["quantidade"],
        errors="raise",
    )

    vendas["valor_final"] = pd.to_numeric(
        vendas["valor_final"],
        errors="raise",
    )

    if vendas[
        ["id_loja", "data_venda", "codigo_venda",
         "produto", "quantidade", "valor_final"]
    ].isna().any().any():
        raise ValueError("Existem campos obrigatórios vazios nas vendas.")

    if (vendas["quantidade"] <= 0).any():
        raise ValueError("Existem vendas com quantidade menor ou igual a zero.")

    # Remove duplicatas que já existam dentro do próprio arquivo.
    vendas = vendas.drop_duplicates(
        subset=[
            "id_loja",
            "data_venda",
            "codigo_venda",
            "produto",
            "quantidade",
            "valor_final",
        ]
    )

    registros = vendas[
        [
            "id_loja",
            "data_venda",
            "codigo_venda",
            "produto",
            "quantidade",
            "valor_final",
        ]
    ].to_dict(orient="records")

    comando = text("""
        INSERT INTO vendas (
            id_loja,
            data_venda,
            codigo_venda,
            produto,
            quantidade,
            valor_final
        )
        VALUES (
            :id_loja,
            :data_venda,
            :codigo_venda,
            :produto,
            :quantidade,
            :valor_final
        )
        ON CONFLICT DO NOTHING
    """)

    # Confirma tudo junto: se houver erro, a transação é revertida.
    with engine.begin() as conexao:
        conexao.execute(comando, registros)

    print(f"Registros de vendas analisados: {len(registros)}")


def main():
    print("Lendo arquivos de origem...")

    emails, lojas, vendas = ler_bases()

    print("Preparando proteção contra duplicatas...")
    preparar_tabelas()

    print("Importando lojas...")
    importar_lojas(emails, lojas)

    print("Importando vendas...")
    importar_vendas(vendas)

    print("Importação concluída!")


if __name__ == "__main__":
    main()
