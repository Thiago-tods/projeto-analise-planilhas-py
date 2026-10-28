import pandas as pd
from sqlalchemy import text
import pytest
import enviar_relatorios



def test_fluxo_completo(
    engine_teste,
    limpar_tabelas,
    tmp_path,
    monkeypatch,
):
    # Arrange: preparar os dados de teste
    with engine_teste.begin() as conexao:
        conexao.execute(
            text('''
                INSERT INTO lojas (id_loja, nome, gerente, email)
                VALUES ('1', 'Loja A', 'Maria', 'maria@exemplo.com')
            ''')
        )

        conexao.execute(
            text('''
                INSERT INTO vendas (
                    id_loja,
                    data_venda,
                    codigo_venda,
                    produto,
                    quantidade,
                    valor_final
                )
                VALUES
                    ('1', '2026-01-15', '100', 'Produto A', 2, 100.00),
                    ('1', '2026-01-15', '100', 'Produto B', 1, 50.00)
            ''')
        )

    # Criar uma base temporária de e-mails
    pasta_bases_teste = tmp_path / 'Bases de Dados'
    pasta_bases_teste.mkdir()

    emails_teste = pd.DataFrame({
        'Loja': ['Loja A', 'Diretoria'],
        'Gerente': ['Maria', 'Diretoria'],
        'E-mail': ['maria@exemplo.com', 'diretoria@exemplo.com'],
    })

    emails_teste.to_excel(
        pasta_bases_teste / 'Emails.xlsx',
        index=False,
    )

    # Substituir os caminhos e o banco de produção pelos de teste
    monkeypatch.setattr(enviar_relatorios, 'engine', engine_teste)
    monkeypatch.setattr(enviar_relatorios, 'pasta_bases', pasta_bases_teste)
    monkeypatch.setattr(
        enviar_relatorios,
        'caminho_backup',
        tmp_path / 'Backup Arquivos Lojas',
    )

    # Substituir o envio real por uma função que registra as chamadas
    emails_enviados = []

    def simular_envio(destino, assunto, corpo, anexos=(), html=False, **kwargs):
        emails_enviados.append({
            'destino': destino,
            'assunto': assunto,
            'corpo': corpo,
            'anexos': list(anexos),
            'html': html,
        })
        return False

    monkeypatch.setattr(
        enviar_relatorios,
        'enviar_email',
        simular_envio,
    )

    # Act: executar o processamento
    enviar_relatorios.main()

    # Assert: verificar os resultados
    assert len(emails_enviados) == 2

    destinos = [email['destino'] for email in emails_enviados]

    assert 'maria@exemplo.com' in destinos
    assert 'diretoria@exemplo.com' in destinos

    # Verificar se os arquivos de relatório foram gerados
    pasta_backup = tmp_path / 'Backup Arquivos Lojas'

    arquivo_loja = (
        pasta_backup
        / 'Loja A'
        / '2026-01-15_Loja A.xlsx'
    )

    arquivo_ranking_ano = pasta_backup / '2026-01-15_Ranking anual.xlsx'
    arquivo_ranking_dia = pasta_backup / '2026-01-15_Ranking dia.xlsx'

    assert arquivo_loja.exists()
    assert arquivo_ranking_ano.exists()
    assert arquivo_ranking_dia.exists()

    # Verificar se os e-mails contêm anexos existentes
    for email in emails_enviados:
        assert email['anexos']

        for anexo in email['anexos']:
            assert anexo.exists()
def test_fluxo_rejeita_venda_com_loja_inexistente(
    engine_teste,
    limpar_tabelas,
    tmp_path,
    monkeypatch,
):
    # Cria uma venda cuja loja não está cadastrada.
    with engine_teste.begin() as conexao:
        conexao.execute(
            text('''
                INSERT INTO vendas (
                    id_loja,
                    data_venda,
                    codigo_venda,
                    produto,
                    quantidade,
                    valor_final
                )
                VALUES (
                    '999',
                    '2026-01-15',
                    '100',
                    'Produto A',
                    1,
                    50.00
                )
            ''')
        )

    # Cria o arquivo de e-mails necessário para iniciar o processamento.
    pasta_bases_teste = tmp_path / 'Bases de Dados'
    pasta_bases_teste.mkdir()

    emails_teste = pd.DataFrame({
        'Loja': ['Diretoria'],
        'Gerente': ['Diretoria'],
        'E-mail': ['diretoria@exemplo.com'],
    })

    emails_teste.to_excel(
        pasta_bases_teste / 'Emails.xlsx',
        index=False,
    )

    # Redireciona a aplicação para o ambiente de testes.
    monkeypatch.setattr(
        enviar_relatorios,
        'engine',
        engine_teste,
    )
    monkeypatch.setattr(
        enviar_relatorios,
        'pasta_bases',
        pasta_bases_teste,
    )

    # Verifica se a aplicação identifica a loja inexistente.
    with pytest.raises(
        ValueError,
        match='lojas não cadastradas',
    ):
        enviar_relatorios.main()
def test_fluxo_ignora_loja_sem_email(
    engine_teste,
    limpar_tabelas,
    tmp_path,
    monkeypatch,
):
    # Arrange: cadastrar duas lojas e vendas para ambas.
    with engine_teste.begin() as conexao:
        conexao.execute(
            text('''
                INSERT INTO lojas (id_loja, nome, gerente, email)
                VALUES
                    ('1', 'Loja A', 'Maria', 'maria@exemplo.com'),
                    ('2', 'Loja B', 'João', NULL)
            ''')
        )

        conexao.execute(
            text('''
                INSERT INTO vendas (
                    id_loja,
                    data_venda,
                    codigo_venda,
                    produto,
                    quantidade,
                    valor_final
                )
                VALUES
                    ('1', '2026-01-15', '100', 'Produto A', 2, 100.00),
                    ('2', '2026-01-15', '200', 'Produto B', 1, 50.00)
            ''')
        )

    # Criar o arquivo temporário de e-mails.
    pasta_bases_teste = tmp_path / 'Bases de Dados'
    pasta_bases_teste.mkdir()

    pd.DataFrame({
        'Loja': ['Loja A', 'Diretoria'],
        'Gerente': ['Maria', 'Diretoria'],
        'E-mail': ['maria@exemplo.com', 'diretoria@exemplo.com'],
    }).to_excel(
        pasta_bases_teste / 'Emails.xlsx',
        index=False,
    )

    # Redirecionar a aplicação para o ambiente de testes.
    monkeypatch.setattr(
        enviar_relatorios,
        'engine',
        engine_teste,
    )
    monkeypatch.setattr(
        enviar_relatorios,
        'pasta_bases',
        pasta_bases_teste,
    )
    monkeypatch.setattr(
        enviar_relatorios,
        'caminho_backup',
        tmp_path / 'Backup Arquivos Lojas',
    )

    # Registrar os e-mails preparados.
    destinos = []

    def simular_envio(
        destino,
        assunto,
        corpo,
        anexos=(),
        html=False,
        **kwargs,
    ):
        destinos.append(destino)
        return False

    monkeypatch.setattr(
        enviar_relatorios,
        'enviar_email',
        simular_envio,
    )

    # Act: executar o processamento.
    enviar_relatorios.main()

    # Assert: a loja válida e a diretoria devem ser processadas.
    assert 'maria@exemplo.com' in destinos
    assert 'diretoria@exemplo.com' in destinos

    # A loja sem e-mail não deve receber uma tentativa de envio.
    assert len(destinos) == 2
    assert 'None' not in destinos
    assert '' not in destinos
def test_fluxo_ignora_email_invalido_da_loja(
    engine_teste,
    limpar_tabelas,
    tmp_path,
    monkeypatch,
):
    # Arrange: cadastrar uma loja com uma venda.
    with engine_teste.begin() as conexao:
        conexao.execute(
            text('''
                INSERT INTO lojas (id_loja, nome, gerente, email)
                VALUES ('1', 'Loja A', 'Maria', 'maria-invalido')
            ''')
        )

        conexao.execute(
            text('''
                INSERT INTO vendas (
                    id_loja,
                    data_venda,
                    codigo_venda,
                    produto,
                    quantidade,
                    valor_final
                )
                VALUES (
                    '1',
                    '2026-01-15',
                    '100',
                    'Produto A',
                    2,
                    100.00
                )
            ''')
        )

    # Criar a planilha de e-mails.
    pasta_bases_teste = tmp_path / 'Bases de Dados'
    pasta_bases_teste.mkdir()

    pd.DataFrame({
        'Loja': ['Loja A', 'Diretoria'],
        'Gerente': ['Maria', 'Diretoria'],
        'E-mail': ['maria-invalido', 'diretoria@exemplo.com'],
    }).to_excel(
        pasta_bases_teste / 'Emails.xlsx',
        index=False,
    )

    # Redirecionar a aplicação para o ambiente de testes.
    monkeypatch.setattr(
        enviar_relatorios,
        'engine',
        engine_teste,
    )
    monkeypatch.setattr(
        enviar_relatorios,
        'pasta_bases',
        pasta_bases_teste,
    )
    monkeypatch.setattr(
        enviar_relatorios,
        'caminho_backup',
        tmp_path / 'Backup Arquivos Lojas',
    )

    # Registrar os destinatários que recebem tentativas de envio.
    destinos = []

    def simular_envio(
        destino,
        assunto,
        corpo,
        anexos=(),
        html=False,
        **kwargs,
    ):
        destinos.append(destino)
        return False

    monkeypatch.setattr(
        enviar_relatorios,
        'enviar_email',
        simular_envio,
    )

    # Act: executar o processamento.
    enviar_relatorios.main()

    # Assert: o endereço inválido não deve receber tentativa de envio.
    assert 'maria-invalido' not in destinos

    # A diretoria deve continuar sendo processada.
    assert 'diretoria@exemplo.com' in destinos

    assert len(destinos) == 1
def test_fluxo_registra_falha_no_envio_de_email(
    engine_teste,
    limpar_tabelas,
    tmp_path,
    monkeypatch,
    caplog,
):
    import logging

    # Prepara uma loja e uma venda no banco de testes.
    with engine_teste.begin() as conexao:
        conexao.execute(
            text('''
                INSERT INTO lojas (id_loja, nome, gerente, email)
                VALUES ('1', 'Loja A', 'Maria', 'maria@exemplo.com')
            ''')
        )

        conexao.execute(
            text('''
                INSERT INTO vendas (
                    id_loja,
                    data_venda,
                    codigo_venda,
                    produto,
                    quantidade,
                    valor_final
                )
                VALUES (
                    '1',
                    '2026-01-15',
                    '100',
                    'Produto A',
                    2,
                    100.00
                )
            ''')
        )

    # Cria o arquivo de e-mails temporário.
    pasta_bases_teste = tmp_path / 'Bases de Dados'
    pasta_bases_teste.mkdir()

    emails_teste = pd.DataFrame({
        'Loja': ['Loja A', 'Diretoria'],
        'Gerente': ['Maria', 'Diretoria'],
        'E-mail': [
            'maria@exemplo.com',
            'diretoria@exemplo.com',
        ],
    })

    emails_teste.to_excel(
        pasta_bases_teste / 'Emails.xlsx',
        index=False,
    )

    # Redireciona o processamento para os recursos de teste.
    monkeypatch.setattr(
        enviar_relatorios,
        'engine',
        engine_teste,
    )
    monkeypatch.setattr(
        enviar_relatorios,
        'pasta_bases',
        pasta_bases_teste,
    )
    monkeypatch.setattr(
        enviar_relatorios,
        'caminho_backup',
        tmp_path / 'Backup Arquivos Lojas',
    )

    chamadas = []

    def simular_envio(destino, assunto, corpo, anexos=(), html=False, **kwargs):
        chamadas.append(destino)

        if destino == 'maria@exemplo.com':
            raise RuntimeError('Falha simulada no envio')

        return False

    monkeypatch.setattr(
        enviar_relatorios,
        'enviar_email',
        simular_envio,
    )

    with caplog.at_level(logging.ERROR):
        enviar_relatorios.main()

    # A falha de uma loja deve ser registrada.
    assert any(
        'Falha ao processar a loja Loja A' in registro.message
        for registro in caplog.records
    )

    # O processamento deve continuar até a Diretoria.
    assert 'maria@exemplo.com' in chamadas
    assert 'diretoria@exemplo.com' in chamadas
def test_fluxo_registra_falha_no_email_da_diretoria(
    engine_teste,
    limpar_tabelas,
    tmp_path,
    monkeypatch,
    caplog,
):
    import logging

    # Prepara a loja e a venda.
    with engine_teste.begin() as conexao:
        conexao.execute(
            text('''
                INSERT INTO lojas (id_loja, nome, gerente, email)
                VALUES ('1', 'Loja A', 'Maria', 'maria@exemplo.com')
            ''')
        )

        conexao.execute(
            text('''
                INSERT INTO vendas (
                    id_loja,
                    data_venda,
                    codigo_venda,
                    produto,
                    quantidade,
                    valor_final
                )
                VALUES (
                    '1',
                    '2026-01-15',
                    '100',
                    'Produto A',
                    2,
                    100.00
                )
            ''')
        )

    # Cria os e-mails temporários.
    pasta_bases_teste = tmp_path / 'Bases de Dados'
    pasta_bases_teste.mkdir()

    pd.DataFrame({
        'Loja': ['Loja A', 'Diretoria'],
        'Gerente': ['Maria', 'Diretoria'],
        'E-mail': [
            'maria@exemplo.com',
            'diretoria@exemplo.com',
        ],
    }).to_excel(
        pasta_bases_teste / 'Emails.xlsx',
        index=False,
    )

    # Direciona o programa para os recursos de teste.
    monkeypatch.setattr(
        enviar_relatorios,
        'engine',
        engine_teste,
    )
    monkeypatch.setattr(
        enviar_relatorios,
        'pasta_bases',
        pasta_bases_teste,
    )
    monkeypatch.setattr(
        enviar_relatorios,
        'caminho_backup',
        tmp_path / 'Backup Arquivos Lojas',
    )

    chamadas = []

    def simular_envio(destino, assunto, corpo, anexos=(), html=False, **kwargs):
        chamadas.append(destino)

        if destino == 'diretoria@exemplo.com':
            raise RuntimeError('Falha simulada na Diretoria')

        return False

    monkeypatch.setattr(
        enviar_relatorios,
        'enviar_email',
        simular_envio,
    )

    with caplog.at_level(logging.ERROR):
        enviar_relatorios.main()

    # Confirma que os dois destinatários foram processados.
    assert 'maria@exemplo.com' in chamadas
    assert 'diretoria@exemplo.com' in chamadas

    # Confirma que a falha da Diretoria foi registrada.
    assert any(
        'Falha ao enviar o e-mail da Diretoria' in registro.message
        for registro in caplog.records
    )
def test_fluxo_rejeita_diretoria_sem_email(
    engine_teste,
    limpar_tabelas,
    tmp_path,
    monkeypatch,
    caplog,
):
    import logging
    import pandas as pd
    from sqlalchemy import text
    import enviar_relatorios

    with engine_teste.begin() as conexao:
        conexao.execute(
            text("""
                INSERT INTO lojas (id_loja, nome, gerente, email)
                VALUES ('1', 'Loja A', 'Maria', 'maria@exemplo.com')
            """)
        )

        conexao.execute(
            text("""
                INSERT INTO vendas (
                    id_loja, data_venda, codigo_venda,
                    produto, quantidade, valor_final
                )
                VALUES (
                    '1', '2026-01-15', '100',
                    'Produto A', 2, 100.00
                )
            """)
        )

    pasta_bases_teste = tmp_path / "Bases de Dados"
    pasta_bases_teste.mkdir()

    pd.DataFrame({
        "Loja": ["Diretoria"],
        "Gerente": ["Diretor"],
        "E-mail": [""],
    }).to_excel(pasta_bases_teste / "Emails.xlsx", index=False)

    monkeypatch.setattr(enviar_relatorios, "engine", engine_teste)
    monkeypatch.setattr(
        enviar_relatorios,
        "pasta_bases",
        pasta_bases_teste,
    )

    with caplog.at_level(logging.ERROR):
        enviar_relatorios.main()

    assert (
        "E-mail da Diretoria inválido" in caplog.text
        or "Diretoria sem e-mail cadastrado" in caplog.text
    )
def test_fluxo_rejeita_email_invalido_da_diretoria(
    engine_teste,
    limpar_tabelas,
    tmp_path,
    monkeypatch,
    caplog,
):
    import logging
    import pandas as pd
    from sqlalchemy import text
    import enviar_relatorios

    with engine_teste.begin() as conexao:
        conexao.execute(
            text("""
                INSERT INTO lojas (id_loja, nome, gerente, email)
                VALUES ('1', 'Loja A', 'Maria', 'maria@exemplo.com')
            """)
        )

        conexao.execute(
            text("""
                INSERT INTO vendas (
                    id_loja, data_venda, codigo_venda,
                    produto, quantidade, valor_final
                )
                VALUES (
                    '1', '2026-01-15', '100',
                    'Produto A', 2, 100.00
                )
            """)
        )

    pasta_bases_teste = tmp_path / "Bases de Dados"
    pasta_bases_teste.mkdir()

    pd.DataFrame({
        "Loja": ["Diretoria"],
        "Gerente": ["Diretor"],
        "E-mail": ["endereco-invalido"],
    }).to_excel(pasta_bases_teste / "Emails.xlsx", index=False)

    monkeypatch.setattr(enviar_relatorios, "engine", engine_teste)
    monkeypatch.setattr(
        enviar_relatorios,
        "pasta_bases",
        pasta_bases_teste,
    )

    with caplog.at_level(logging.ERROR):
        enviar_relatorios.main()

    assert "E-mail da Diretoria inválido" in caplog.text
    assert "endereco-invalido" in caplog.text
def test_fluxo_usa_primeiro_email_quando_loja_duplicada(
    engine_teste,
    limpar_tabelas,
    tmp_path,
    monkeypatch,
    caplog,
):
    import logging
    import pandas as pd
    from sqlalchemy import text
    import enviar_relatorios

    # Prepara os dados do banco de teste.
    with engine_teste.begin() as conexao:
        conexao.execute(
            text("""
                INSERT INTO lojas (id_loja, nome, gerente, email)
                VALUES ('1', 'Loja A', 'Maria', 'maria@exemplo.com')
            """)
        )

        conexao.execute(
            text("""
                INSERT INTO vendas (
                    id_loja,
                    data_venda,
                    codigo_venda,
                    produto,
                    quantidade,
                    valor_final
                )
                VALUES (
                    '1',
                    '2026-01-15',
                    '100',
                    'Produto A',
                    2,
                    100.00
                )
            """)
        )

    # Cria o arquivo com dois e-mails para a mesma loja.
    pasta_bases_teste = tmp_path / "Bases de Dados"
    pasta_bases_teste.mkdir()

    pd.DataFrame({
        "Loja": ["Loja A", "Loja A", "Diretoria"],
        "Gerente": ["Maria", "Maria", "Diretor"],
        "E-mail": [
            "primeiro@exemplo.com",
            "segundo@exemplo.com",
            "diretoria@exemplo.com",
        ],
    }).to_excel(pasta_bases_teste / "Emails.xlsx", index=False)

    # Redireciona o fluxo para os recursos de teste.
    monkeypatch.setattr(enviar_relatorios, "engine", engine_teste)
    monkeypatch.setattr(
        enviar_relatorios,
        "pasta_bases",
        pasta_bases_teste,
    )
    monkeypatch.setattr(
        enviar_relatorios,
        "caminho_backup",
        tmp_path / "Backup",
    )

    # Registra os destinatários das mensagens preparadas.
    destinatarios = []

    def email_falso(destino, assunto, corpo, anexos=(), html=False, tentativas=3):
        destinatarios.append(destino)
        return True

    monkeypatch.setattr(enviar_relatorios, "enviar_email", email_falso)

    # Executa o fluxo e verifica o aviso de duplicidade.
    with caplog.at_level(logging.WARNING):
        enviar_relatorios.main()

    assert "Lojas com mais de um e-mail cadastrado" in caplog.text
    assert "Loja A" in caplog.text

    # A loja deve utilizar o primeiro endereço cadastrado.
    assert "primeiro@exemplo.com" in destinatarios
    assert "segundo@exemplo.com" not in destinatarios
def test_fluxo_rejeita_quantidade_zero(
    engine_teste,
    limpar_tabelas,
    tmp_path,
    monkeypatch,
):
    import pandas as pd
    import pytest
    from sqlalchemy import text
    import enviar_relatorios

    # Prepara uma loja e uma venda com quantidade inválida.
    with engine_teste.begin() as conexao:
        conexao.execute(
            text("""
                INSERT INTO lojas (id_loja, nome, gerente, email)
                VALUES ('1', 'Loja A', 'Maria', 'maria@exemplo.com')
            """)
        )

        conexao.execute(
            text("""
                INSERT INTO vendas (
                    id_loja,
                    data_venda,
                    codigo_venda,
                    produto,
                    quantidade,
                    valor_final
                )
                VALUES (
                    '1',
                    '2026-01-15',
                    '100',
                    'Produto A',
                    0,
                    100.00
                )
            """)
        )

    # Cria o arquivo de e-mails obrigatório.
    pasta_bases_teste = tmp_path / 'Bases de Dados'
    pasta_bases_teste.mkdir()

    pd.DataFrame({
        'Loja': ['Loja A', 'Diretoria'],
        'Gerente': ['Maria', 'Diretor'],
        'E-mail': ['maria@exemplo.com', 'diretoria@exemplo.com'],
    }).to_excel(pasta_bases_teste / 'Emails.xlsx', index=False)

    monkeypatch.setattr(enviar_relatorios, 'engine', engine_teste)
    monkeypatch.setattr(
        enviar_relatorios,
        'pasta_bases',
        pasta_bases_teste,
    )

    with pytest.raises(
        ValueError,
        match='Quantidade contém valores menores ou iguais a zero',
    ):
        enviar_relatorios.main()