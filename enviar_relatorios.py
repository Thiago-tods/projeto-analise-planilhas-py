import os
import time
import logging
import pathlib
import smtplib
import mimetypes
from email.message import EmailMessage

import pandas as pd
from dotenv import load_dotenv
from database import engine
# ---------- configurações ----------
load_dotenv()

EMAIL_REMETENTE = (os.getenv('EMAIL_REMETENTE') or '').strip()
SENHA_APP = (os.getenv('SENHA_APP') or '').replace(' ', '').strip()
ENVIAR_EMAILS = os.getenv('ENVIAR_EMAILS', 'false').strip().lower() == 'true'
EMAIL_TESTE = (os.getenv('EMAIL_TESTE') or '').strip()

if ENVIAR_EMAILS and (not EMAIL_REMETENTE or not SENHA_APP):
    raise RuntimeError(
        'Para enviar e-mails, defina EMAIL_REMETENTE e SENHA_APP no arquivo .env'
    )
if ENVIAR_EMAILS and (not EMAIL_TESTE or '@' not in EMAIL_TESTE):
    raise RuntimeError(
        'Para o teste controlado, defina EMAIL_TESTE com seu próprio endereço de e-mail no .env'
    )

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('relatorio.log', encoding='utf-8'),
        logging.StreamHandler(),
    ],
)

pasta_bases = pathlib.Path(os.getenv('PASTA_BASES', 'Bases de Dados'))
caminho_backup = pathlib.Path('Backup Arquivos Lojas')

meta_faturamento_dia = 1000
meta_faturamento_ano = 1650000
meta_qtdeprodutos_dia = 4
meta_qtdeprodutos_ano = 120
meta_ticketmedio_dia = 500
meta_ticketmedio_ano = 500


# ---------- envio de e-mail ----------
def enviar_email(destino, assunto, corpo, anexos=(), html=False, tentativas=3):
    if not ENVIAR_EMAILS:
        logging.info(
            '[MODO DE TESTE] E-mail não enviado. '
            f'Destinatário original: {destino} | Assunto: {assunto} | '
            f'Anexos: {", ".join(pathlib.Path(a).name for a in anexos)}'
        )
        return False

    # Teste controlado: todas as mensagens vão somente para EMAIL_TESTE.
    destinatario_original = destino
    destino = EMAIL_TESTE
    assunto = f'[TESTE] {assunto}'
    if html:
        corpo = (
            '<div style="padding:12px;border:2px solid #d97706;margin-bottom:16px;">'
            '<strong>EMAIL DE TESTE</strong><br>'
            f'Destinatário que receberia este relatório: {destinatario_original}'
            '</div>' + corpo
        )
    else:
        corpo = (
            'EMAIL DE TESTE\n'
            f'Destinatário original previsto: {destinatario_original}\n'
            '--- início da mensagem original ---\n\n'
            + corpo
        )

    logging.info(
        f'[TESTE CONTROLADO] Redirecionando mensagem de {destinatario_original} '
        f'para {destino}. Assunto: {assunto}'
    )

    msg = EmailMessage()
    msg['From'] = EMAIL_REMETENTE
    msg['To'] = destino
    msg['Subject'] = assunto

    if html:
        msg.set_content(
            'EMAIL DE TESTE. Destinatário original previsto: '
            f'{destinatario_original}. Este relatório foi redirecionado para teste.'
        )
        msg.add_alternative(corpo, subtype='html')
    else:
        msg.set_content(corpo)

    for anexo in anexos:
        anexo = pathlib.Path(anexo)
        tipo, _ = mimetypes.guess_type(str(anexo))
        maintype, subtype = (tipo or 'application/octet-stream').split('/')
        with open(anexo, 'rb') as f:
            msg.add_attachment(f.read(), maintype=maintype, subtype=subtype, filename=anexo.name)

    for tentativa in range(1, tentativas + 1):
        try:
            with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as servidor:
                servidor.ehlo()
                servidor.starttls()
                servidor.ehlo()
                servidor.login(EMAIL_REMETENTE, SENHA_APP)
                servidor.send_message(msg)
            return True
        except smtplib.SMTPAuthenticationError:
            # senha errada não adianta tentar de novo
            logging.error('Falha de autenticação no Gmail. Confira EMAIL_REMETENTE e SENHA_APP.')
            raise
        except (smtplib.SMTPServerDisconnected, ConnectionError, TimeoutError) as erro:
            # atenção: se a conexão cair depois que o servidor aceitou a mensagem,
            # uma nova tentativa pode gerar e-mail duplicado
            if tentativa == tentativas:
                raise
            logging.warning(f'Conexão caiu ({erro}), tentando de novo ({tentativa}/{tentativas})...')
            time.sleep(5)


def verificar_login():
    # testa o login uma vez antes de processar qualquer dado,
    # para não perder tempo se as credenciais estiverem erradas
    try:
        with smtplib.SMTP('smtp.gmail.com', 587, timeout=30) as servidor:
            servidor.ehlo()
            servidor.starttls()
            servidor.ehlo()
            servidor.login(EMAIL_REMETENTE, SENHA_APP)
    except (smtplib.SMTPAuthenticationError, smtplib.SMTPServerDisconnected):
        # quando o Gmail recusa a senha, o Python às vezes mostra só "Connection unexpectedly closed"
        logging.error(
            'O Gmail recusou o login. Confira se EMAIL_REMETENTE é o e-mail exato da conta '
            'e se SENHA_APP é uma senha de app válida (16 letras, gerada nessa mesma conta).'
        )
        raise SystemExit(1)
    except OSError as erro:
        logging.error(f'Não foi possível conectar ao servidor do Gmail: {erro}')
        raise SystemExit(1)
    logging.info(f'Login verificado com sucesso ({EMAIL_REMETENTE})')


if ENVIAR_EMAILS:
    verificar_login()
else:
    logging.info(
        'Modo de simulação ativado: nenhum e-mail será enviado. '
        'Para enviar apenas para seu endereço de teste, configure ENVIAR_EMAILS=true '
        'e EMAIL_TESTE no .env.'
    )


# ---------- formatação do e-mail ----------
def cor_cenario(valor, meta):
    # verde se bateu a meta, vermelho se não
    return '#00b050' if valor >= meta else '#e53935'


def fmt_moeda(v):
    return f'R$ {v:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def fmt_num(v):
    return f'{v:,.0f}'.replace(',', '.')


def linha(nome_ind, valor, meta, formato):
    cor = cor_cenario(valor, meta)
    return f'''
    <tr>
      <td style='padding:6px 20px 6px 0;'>{nome_ind}</td>
      <td align='right' style='padding:6px 12px;'>{formato(valor)}</td>
      <td align='right' style='padding:6px 12px;'>{formato(meta)}</td>
      <td align='center'><span style='color:{cor}; font-size:20px;'>&#9679;</span></td>
    </tr>'''


def tabela(titulo_valor, titulo_meta, titulo_cenario, linhas):
    return f'''
    <table cellpadding='6' cellspacing='0' border='0' style='border-collapse:collapse; font-size:14px; margin-bottom:24px;'>
      <tr>
        <td></td>
        <td align='center' style='padding:6px 12px;'>{titulo_valor}</td>
        <td align='center' style='padding:6px 12px;'>{titulo_meta}</td>
        <td align='center' style='padding:6px 12px;'>{titulo_cenario}</td>
      </tr>
      {linhas}
    </table>'''


# ---------- leitura e validação dos dados ----------
def ler_arquivo(caminho, colunas_obrigatorias, **kwargs):
    if not caminho.exists():
        raise FileNotFoundError(f'Arquivo não encontrado: {caminho}')

    if caminho.suffix == '.csv':
        tabela_lida = pd.read_csv(caminho, **kwargs)
    else:
        tabela_lida = pd.read_excel(caminho, **kwargs)

    faltando = [col for col in colunas_obrigatorias if col not in tabela_lida.columns]
    if faltando:
        raise ValueError(f'Colunas ausentes em {caminho.name}: {faltando}')

    return tabela_lida

def main():
    # ---------- leitura dos dados ----------
    emails = ler_arquivo(
        pasta_bases / 'Emails.xlsx',
        ['Loja', 'Gerente', 'E-mail']
    )

    query_vendas = '''
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
    # Verifica se existem vendas associadas a lojas inexistentes.
    query_lojas_invalidas = '''
        SELECT DISTINCT v.id_loja
        FROM vendas AS v
        LEFT JOIN lojas AS l
            ON l.id_loja = v.id_loja
        WHERE l.id_loja IS NULL
    '''

    lojas_invalidas = pd.read_sql(
        query_lojas_invalidas,
        engine,
    )

    if not lojas_invalidas.empty:
        ids_invalidos = lojas_invalidas['id_loja'].tolist()

        raise ValueError(
            f'Existem vendas associadas a lojas não cadastradas: {ids_invalidos}'
        )
    vendas = pd.read_sql(query_vendas, engine)

    if vendas.empty:
        raise ValueError('O PostgreSQL não retornou nenhuma venda.')

    logging.info(
        f'{len(vendas)} registros de vendas carregados do PostgreSQL.'
    )

    vendas['Data'] = pd.to_datetime(vendas['Data'], errors='raise').dt.normalize()
    vendas['Valor Final'] = pd.to_numeric(vendas['Valor Final'], errors='raise')
    vendas['Quantidade'] = pd.to_numeric(vendas['Quantidade'], errors='raise')
    if vendas[['Data', 'Código Venda', 'Produto', 'Quantidade', 'Valor Final']].isna().any().any():
        raise ValueError('A base Vendas.xlsx contém valores vazios em colunas obrigatórias.')
    if (vendas['Quantidade'] <= 0).any():
        raise ValueError('A coluna Quantidade contém valores menores ou iguais a zero.')

    # Identifica vendas com ID de loja que não existe no cadastro, em vez de descartá-las silenciosamente.

    dia_indicador = vendas['Data'].max().normalize()
    logging.info(
        f'Data mais recente encontrada nos dados: {dia_indicador:%d/%m/%Y}. '
        'Os indicadores serão calculados com base nessa data.'
    )

    # o "ano" dos indicadores é o ano do dia analisado
    vendas_ano = vendas.loc[vendas['Data'].dt.year == dia_indicador.year, :]

    # uma loja sem nenhuma venda continua no dicionário, só com a tabela vazia
    # Agrupa as vendas por loja
    grupos_lojas = dict(tuple(vendas_ano.groupby('Loja')))

    # Obtém as lojas presentes nos dados vindos do PostgreSQL
    todas_lojas = vendas['Loja'].dropna().unique()

    # Mantém uma entrada para cada loja, mesmo sem vendas no ano analisado
    dicionario_lojas = {
        loja: grupos_lojas.get(loja, vendas_ano.iloc[0:0])
        for loja in todas_lojas
    }
    # garante que só existe um e-mail por loja
    if emails['Loja'].duplicated().any():
        duplicadas = emails.loc[emails['Loja'].duplicated(), 'Loja'].tolist()
        logging.warning(f'Lojas com mais de um e-mail cadastrado (usando o primeiro): {duplicadas}')
    emails = emails.drop_duplicates(subset='Loja', keep='first').set_index('Loja')


    # ---------- backup dos arquivos de cada loja ----------
    caminho_backup.mkdir(parents=True, exist_ok=True)

    data_texto = f'{dia_indicador:%Y-%m-%d}'

    for loja in dicionario_lojas:
        pasta_loja = caminho_backup / loja
        pasta_loja.mkdir(exist_ok=True)

        nome_arquivo = f'{data_texto}_{loja}.xlsx'
        local_arquivo = pasta_loja / nome_arquivo
        dicionario_lojas[loja].to_excel(local_arquivo, index=False)


    # ---------- e-mail de cada loja ----------
    falhas = []

    for loja in dicionario_lojas:
        try:
            if loja not in emails.index:
                logging.warning(f'Loja {loja} sem e-mail cadastrado, pulando.')
                falhas.append(loja)
                continue

            destino = str(emails.loc[loja, 'E-mail']).strip()
            if not destino or '@' not in destino:
                logging.warning(f'Loja {loja} possui e-mail inválido, pulando: {destino!r}')
                falhas.append(loja)
                continue

            vendas_loja = dicionario_lojas[loja]
            vendas_loja_dia = vendas_loja.loc[vendas_loja['Data'] == dia_indicador, :]

            faturamento_ano = vendas_loja['Valor Final'].sum()
            faturamento_dia = vendas_loja_dia['Valor Final'].sum()

            qtde_produtos_ano = vendas_loja['Produto'].nunique()
            qtde_produtos_dia = vendas_loja_dia['Produto'].nunique()

            # Cada código de venda é considerado um pedido dentro da loja.
            valor_venda = vendas_loja.groupby(['Data', 'Código Venda'])['Valor Final'].sum()
            ticket_medio_ano = valor_venda.mean() if not valor_venda.empty else 0

            valor_venda_dia = vendas_loja_dia.groupby('Código Venda')['Valor Final'].sum()
            ticket_medio_dia = valor_venda_dia.mean() if not valor_venda_dia.empty else 0

            linhas_dia = (
                linha('Faturamento', faturamento_dia, meta_faturamento_dia, fmt_moeda) +
                linha('Diversidade de Produtos', qtde_produtos_dia, meta_qtdeprodutos_dia, fmt_num) +
                linha('Ticket Médio', ticket_medio_dia, meta_ticketmedio_dia, fmt_moeda)
            )
            linhas_ano = (
                linha('Faturamento', faturamento_ano, meta_faturamento_ano, fmt_moeda) +
                linha('Diversidade de Produtos', qtde_produtos_ano, meta_qtdeprodutos_ano, fmt_num) +
                linha('Ticket Médio', ticket_medio_ano, meta_ticketmedio_ano, fmt_moeda)
            )

            tabela_dia = tabela('Valor Dia', 'Meta Dia', 'Cenário Dia', linhas_dia)
            tabela_ano = tabela('Valor Ano', 'Meta Ano', 'Cenário Ano', linhas_ano)

            nome = emails.loc[loja, 'Gerente']

            corpo_html = f'''
            <div style='font-family:Arial, Helvetica, sans-serif; font-size:14px; color:#202124;'>
            <p>Bom dia, {nome}</p>
            <p>Os resultados da data de referência {dia_indicador:%d/%m/%Y} da Loja {loja} foram:</p>

            {tabela_dia}
            {tabela_ano}

            <p>Segue em anexo a planilha com todos os dados para mais detalhes.<br>
            Qualquer dúvida, estou à disposição.</p>

            <p>Att.,<br>Thiago</p>
            </div>
            '''

            attachment = caminho_backup / loja / f'{data_texto}_{loja}.xlsx'

            enviado = enviar_email(
                destino=destino,
                assunto=f'OnePage Dia {dia_indicador.day}/{dia_indicador.month} - Loja {loja}',
                corpo=corpo_html,
                anexos=[attachment],
                html=True,
            )
            if enviado:
                logging.info(f'E-mail da loja {loja} enviado com sucesso')
            else:
                logging.info(f'[MODO DE TESTE] E-mail da loja {loja} preparado; não enviado.')

        except smtplib.SMTPAuthenticationError:
            # sem login não adianta continuar com as outras lojas
            raise
        except Exception as erro:
            logging.error(f'Falha ao processar a loja {loja}: {erro}')
            falhas.append(loja)


    # ---------- rankings ----------
    # todas as lojas entram no ranking, mesmo as que não venderam (faturamento 0)
    # Todas as lojas que possuem vendas ou cadastro no banco
    todas_lojas = vendas['Loja'].dropna().unique()

    faturamento_lojas = (
        vendas_ano.groupby('Loja')['Valor Final'].sum()
        .reindex(todas_lojas, fill_value=0)
        .to_frame()
        .sort_values(by='Valor Final', ascending=False)
    )

    nome_arquivo = f'{data_texto}_Ranking anual.xlsx'
    caminho_ranking_ano = caminho_backup / nome_arquivo
    faturamento_lojas.to_excel(caminho_ranking_ano)

    vendas_dia = vendas.loc[vendas['Data'] == dia_indicador, :]
    faturamento_lojas_dia = (
        vendas_dia.groupby('Loja')['Valor Final'].sum()
        .reindex(todas_lojas, fill_value=0)
        .to_frame()
        .sort_values(by='Valor Final', ascending=False)
    )

    nome_arquivo = f'{data_texto}_Ranking dia.xlsx'
    caminho_ranking_dia = caminho_backup / nome_arquivo
    faturamento_lojas_dia.to_excel(caminho_ranking_dia)


    # ---------- e-mail da Diretoria ----------
    corpo_diretoria = f'''Prezados, bom dia

    Este relatório considera os dados até {dia_indicador:%d/%m/%Y}.

    Melhor loja do dia em faturamento: Loja {faturamento_lojas_dia.index[0]} com faturamento {fmt_moeda(faturamento_lojas_dia.iloc[0, 0])}
    Pior loja do dia em faturamento: Loja {faturamento_lojas_dia.index[-1]} com faturamento {fmt_moeda(faturamento_lojas_dia.iloc[-1, 0])}

    Melhor loja do ano em faturamento: Loja {faturamento_lojas.index[0]} com faturamento {fmt_moeda(faturamento_lojas.iloc[0, 0])}
    Pior loja do ano em faturamento: Loja {faturamento_lojas.index[-1]} com faturamento {fmt_moeda(faturamento_lojas.iloc[-1, 0])}

    Segue em anexo o ranking do ano e do dia de todas as lojas.

    Qualquer dúvida, estou à disposição.

    Att.,
    Thiago'''

    try:
        if 'Diretoria' not in emails.index:
            raise ValueError('Diretoria sem e-mail cadastrado')

        destino_diretoria = str(emails.loc['Diretoria', 'E-mail']).strip()
        if not destino_diretoria or '@' not in destino_diretoria:
            raise ValueError(f'E-mail da Diretoria inválido: {destino_diretoria!r}')

        enviado = enviar_email(
            destino=destino_diretoria,
            assunto=f'Ranking dia {dia_indicador.day}/{dia_indicador.month}',
            corpo=corpo_diretoria,
            anexos=[caminho_ranking_ano, caminho_ranking_dia],
        )
        if enviado:
            logging.info('E-mail da Diretoria enviado com sucesso')
        else:
            logging.info('[MODO DE TESTE] E-mail da Diretoria preparado; não enviado.')
    except Exception as erro:
        logging.error(f'Falha ao enviar o e-mail da Diretoria: {erro}')
        falhas.append('Diretoria')


    # ---------- resumo ----------
    if falhas:
        logging.warning(f'Execução concluída com falhas em: {falhas}')
    else:
        logging.info('Execução concluída sem falhas')
if __name__ == '__main__':
    main()