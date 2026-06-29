# Firebird AI Inspector (`fb_inspector`)

Uma ferramenta de linha de comando (CLI) arquitetada para atuar como uma interface amigável para Agentes de Inteligência Artificial (LLMs) inspecionarem bancos de dados Firebird.

Ao invés de copiar e colar DDLs gigantes no chat da sua IA, você simplesmente pede para ela rodar essa ferramenta no terminal e ela extrairá a estrutura do banco perfeitamente formatada em tempo real. Funciona como um "IBExpert de Terminal".

## 🚀 Por que este projeto existe?
Sistemas legados como Delphi/Firebird não possuem ferramentas nativas de CLI que retornam dados formatados de maneira inteligível para uma IA (em formato Markdown/Grid). O `fb_inspector` resolve isso gerando tabelas perfeitas que impedem as LLMs de alucinarem nomes de colunas e constraints.

## ✨ Funcionalidades
- **Tabelas e Views:** Listagem rápida de objetos.
- **Schemas Detalhados:** Mostra colunas, tipos de dados, nulidade e sinaliza Chaves Primárias (PK).
- **Procedures e Triggers:** Extrai o código-fonte integral direto do terminal.
- **Generators/Sequences:** Lista e consulta os valores atuais em tempo real (`GEN_ID`).
- **Query Livre:** Executa DML/DDL de forma segura (limitado a 100 linhas no output para proteger o terminal).

## 🛠️ Instalação

Como o projeto segue o padrão profissional de pacotes Python (`pyproject.toml`), a instalação global é muito simples:

1. Clone o repositório:
```bash
git clone https://github.com/willendary/fb_inspector.git
cd fb_inspector
```

2. Instale as dependências e a ferramenta de forma global (Modo Editável):
```bash
pip install -e .
```

3. Crie e configure o arquivo `.env` na raiz do projeto (use o `.env.example` como base).

## 🔧 Configuração (.env)
Este script resolve automaticamente o problema da dll `fbclient.dll` (comum em ambientes com múltiplas versões como HQBird). Configure seu arquivo `.env`:

```env
FB_HOST=localhost
FB_PORT=3055
FB_DATABASE=D:\Dados\sky\Dados\porto 9 fb40\FINANCEIRO.GDB
FB_USER=SYSDBA
FB_PASSWORD=masterkey
FB_CHARSET=ISO8859_1
FB_CLIENT_PATH=C:\Program Files (x86)\IBSurgeon\HQBird Firebird Admin 2024\ClientLibs\64\4.0\fbclient.dll
```

## 📖 Como Usar (Comandos)

Uma vez instalado via `pip install`, você (ou sua IA) pode rodar o comando `fb-inspector` de qualquer lugar do terminal:

| Comando | Descrição |
|---------|-----------|
| `fb-inspector tables` | Lista todas as tabelas (User Tables) |
| `fb-inspector views` | Lista todas as views |
| `fb-inspector schema <tabela>` | Mostra os campos, tipos e PKs de uma tabela/view |
| `fb-inspector procedures` | Lista todas as Stored Procedures |
| `fb-inspector procedure <nome>`| Extrai o código-fonte SQL de uma procedure |
| `fb-inspector triggers` | Lista todas as Triggers |
| `fb-inspector triggers --table <tabela>` | Filtra as Triggers de uma tabela específica |
| `fb-inspector trigger <nome>` | Extrai o código-fonte de uma Trigger |
| `fb-inspector indices <tabela>` | Lista os índices e os campos indexados de uma tabela |
| `fb-inspector generators` | Lista os generators e mostra o valor atual |
| `fb-inspector query "<sql>"` | Executa uma consulta livre (limitada a 100 resultados) |

*(Você também pode sobrescrever as credenciais do .env passando flags no comando: `--db`, `--user`, `--password`, etc).*

## 🏗️ Arquitetura e Engenharia
Este projeto utiliza:
- **SOLID & Orientação a Objetos**: Lógica de banco isolada da camada de apresentação.
- **Testes Unitários**: Garantia de integridade com `unittest` e `mock`.
- **CI/CD**: Automação com GitHub Actions para Linting (`black`) e Testes.
- **Logging**: Erros críticos são salvos silenciosamente no arquivo `inspector.log`.

## 📄 Licença
Distribuído sob a licença MIT. Sinta-se livre para usar, modificar e contribuir!
