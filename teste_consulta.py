import pandas as pd
from database import engine

query = '''
    SELECT
        v.id_loja AS "ID Loja",
        l.nome AS "Loja",
        v.data_venda AS "Data",
        v.codigo_venda AS "Código Venda",
        v.produto AS "Produto",
        v.quantidade AS "Quantidade",
        v.valor_final AS "Valor Final"
    FROM vendas AS v
    INNER JOIN lojas AS l
        ON l.id_loja = v.id_loja
'''

vendas = pd.read_sql(query, engine)

print(vendas.head())