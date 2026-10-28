# Sistema Automatizado de Relatórios de Vendas

Projeto desenvolvido em Python para automatizar a geração de relatórios gerenciais de vendas. A aplicação consulta dados no PostgreSQL, calcula indicadores de desempenho, gera planilhas Excel e prepara relatórios personalizados para gerentes de lojas e diretoria.

O projeto também conta com testes automatizados para validar os cálculos, a importação de dados, a integração com o banco de dados e o fluxo de geração dos relatórios.

## Funcionalidades

- Importação e validação de arquivos Excel e CSV.
- Consulta de dados de vendas armazenados no PostgreSQL.
- Validação de registros e identificação de vendas associadas a lojas não cadastradas.
- Cálculo de indicadores de desempenho por loja.
- Análise do dia mais recente dos dados e do respectivo ano.
- Comparação dos resultados com metas predefinidas.
- Geração de planilhas Excel individuais por loja.
- Criação de rankings de faturamento diário e anual.
- Geração de e-mails personalizados em HTML com anexos.
- Envio de relatórios para gerentes e diretoria.
- Registro de eventos e falhas em arquivos de log.
- Tratamento de falhas no processamento e no envio de e-mails.
- Modo de simulação para testar o fluxo sem enviar mensagens.
- Modo de envio controlado, com redirecionamento para um endereço de teste.

## Indicadores

A aplicação calcula os seguintes indicadores:

| Indicador | Descrição |
|---|---|
| Faturamento | Soma dos valores das vendas |
| Diversidade de produtos | Quantidade de produtos distintos vendidos |
| Ticket médio | Valor médio dos pedidos, considerando os códigos de venda |

Os indicadores são calculados para o dia mais recente encontrado na base e para o ano correspondente.

Os resultados são comparados com metas configuráveis no código. Os relatórios apresentam indicadores visuais para facilitar a identificação de resultados acima ou abaixo das metas.

## Tecnologias utilizadas

- **Python** — linguagem principal.
- **pandas** — manipulação, validação e análise dos dados.
- **openpyxl** — leitura e geração de planilhas Excel.
- **PostgreSQL** — armazenamento dos dados de vendas e lojas.
- **SQLAlchemy** — conexão e execução de consultas ao banco de dados.
- **psycopg** — driver de conexão com PostgreSQL.
- **python-dotenv** — gerenciamento de variáveis de ambiente.
- **smtplib e email.message** — envio e composição de mensagens de e-mail.
- **pathlib** — manipulação de caminhos e arquivos.
- **logging** — registro de eventos e erros.
- **pytest** — execução de testes automatizados.
- **pytest-cov** — análise da cobertura de testes.

## Estrutura do projeto

```text
projeto-analise-planilhas-py/
├── tests/
│   ├── conftest.py
│   ├── test_calculos.py
│   ├── test_enviar_relatorios.py
│   ├── test_fluxo_completo.py
│   ├── test_importar_excel.py
│   ├── test_integracao_postgres.py
│   └── test_relatorios.py
├── .env.example
├── .gitignore
├── calculos.py
├── database.py
├── enviar_relatorios.py
├── gerar_relatorios.py
├── importar_excel.py
├── requirements.txt
├── README.md
└── teste_consulta.py
```

Os nomes dos arquivos de teste acima correspondem à estrutura atual do projeto. Arquivos de dados, relatórios gerados, logs e ambientes virtuais não devem ser versionados quando forem arquivos locais ou contiverem informações sensíveis.

## Pré-requisitos

- Python instalado.
- PostgreSQL instalado e em execução.
- Um banco de dados PostgreSQL configurado para a aplicação.
- Git, caso queira clonar ou versionar o projeto.

## Instalação

Clone o repositório:

```bash
git clone <URL_DO_REPOSITORIO>
cd projeto-analise-planilhas-py
```

Crie um ambiente virtual:

```bash
python -m venv .venv
```

Ative o ambiente virtual no Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

Instale as dependências:

```bash
python -m pip install -r requirements.txt
```

## Configuração

Crie uma cópia do arquivo de exemplo:

```powershell
Copy-Item .env.example .env
```

Configure as variáveis de ambiente no arquivo `.env`:

```dotenv
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
DB_HOST=localhost
DB_PORT=5432
DB_NAME=seu_banco

EMAIL_REMETENTE=seu_email@gmail.com
SENHA_APP=sua_senha_de_app

ENVIAR_EMAILS=false
EMAIL_TESTE=seu_email_de_teste@gmail.com

PASTA_BASES=Bases de Dados
```

Ajuste os valores conforme o ambiente local. O nome do banco deve corresponder a um banco existente no PostgreSQL.

**Segurança:** nunca publique o arquivo `.env`, senhas, credenciais reais ou dados comerciais confidenciais. O arquivo `.env.example` deve conter apenas valores fictícios.

### Configuração de e-mail

Para utilizar o Gmail, configure uma senha de app válida, em vez da senha normal da conta.

Com `ENVIAR_EMAILS=false`, a aplicação opera em modo de simulação.

Antes de habilitar o envio, configure `EMAIL_REMETENTE`, `SENHA_APP` e `EMAIL_TESTE`. O modo de teste controlado redireciona as mensagens para o endereço definido em `EMAIL_TESTE`.

Faça testes com dados fictícios antes de utilizar informações reais.

## Banco de dados

A aplicação utiliza PostgreSQL para consultar as informações de lojas e vendas.

O módulo `database.py` configura a conexão utilizando SQLAlchemy e as variáveis de ambiente.

Certifique-se de que:
- O PostgreSQL esteja em execução.
- O banco configurado exista.
- O usuário tenha as permissões necessárias.
- As tabelas e os dados estejam preparados conforme as consultas utilizadas pela aplicação.

O módulo de conexão também contém uma função para verificar a conectividade com o banco.

## Execução

Com o ambiente virtual ativado e as configurações definidas, execute os módulos conforme a rotina desejada.

Para gerar e preparar os relatórios:

```powershell
python enviar_relatorios.py
```

Para importar planilhas para o banco:

```powershell
python importar_excel.py
```

Para gerar relatórios pelo módulo específico:

```powershell
python gerar_relatorios.py
```

A execução de cada módulo depende dos arquivos, das tabelas e das configurações exigidas por sua implementação.

## Testes automatizados

Execute todos os testes:

```powershell
python -m pytest
```

Para executar os testes de um módulo específico:

```powershell
python -m pytest tests/test_enviar_relatorios.py -v
```

Para medir a cobertura de `enviar_relatorios.py`:

```powershell
python -m pytest --cov=enviar_relatorios --cov-report=term-missing
```

A última execução registrada durante o desenvolvimento apresentou **70 testes aprovados e 95% de cobertura** para `enviar_relatorios.py`. Esses números podem mudar conforme o código e os testes forem atualizados.

Os testes abrangem cálculos, validação de arquivos, integração com PostgreSQL e o fluxo de geração dos relatórios.

## Logs e arquivos gerados

A aplicação utiliza `logging` para registrar eventos, resultados e falhas de processamento.

Os relatórios e arquivos de backup são gravados nos diretórios definidos na configuração do projeto. O arquivo `relatorio.log` registra informações da execução.

Esses arquivos podem conter dados operacionais e devem ser avaliados antes de qualquer compartilhamento.

## Próximas melhorias

- Aumentar a cobertura de testes dos trechos ainda não exercitados.
- Aprimorar a separação entre regras de negócio, acesso a dados e envio de e-mails.
- Adicionar integração contínua para executar os testes automaticamente.
- Implementar relatórios adicionais e indicadores configuráveis.
- Melhorar o tratamento de falhas e a observabilidade da aplicação.
- Documentar o esquema do banco e os procedimentos de implantação.

## Autor

Projeto desenvolvido como parte dos estudos em Engenharia de Software, com foco em Python, automação, análise de dados, bancos de dados e testes automatizados.
