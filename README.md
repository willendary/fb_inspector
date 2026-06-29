# Firebird AI Inspector

Uma ferramenta de linha de comando (CLI) desenvolvida em Python para atuar como uma ponte direta entre a sua Inteligência Artificial (como o Antigravity / Gemini) e o seu banco de dados Firebird.

O objetivo deste projeto é permitir que a IA consulte em tempo real a estrutura do seu banco de dados (tabelas, colunas, tipos) e execute consultas para entender o modelo de dados, sem que você precise enviar arquivos DDL manualmente durante as conversas.

## 🚀 Como funciona?

O script utiliza a biblioteca `fdb` oficial para se conectar ao banco Firebird e extrai metadados essenciais. Ele foi desenhado para cuspir os resultados em formato de tabelas de texto puro (`tabulate`), o que torna a leitura extremamente fácil para LLMs (Large Language Models).

## 📦 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/SEU_USUARIO/fb_inspector.git
cd fb_inspector
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure o ambiente:
Copie o arquivo `.env.example` para `.env` e preencha com as informações do seu banco de dados Firebird.
```bash
cp .env.example .env
```
*(No Windows, basta duplicar o arquivo e renomeá-lo para `.env`)*

## 🛠️ Como Integrar com a sua IA

Para que a sua IA comece a usar a ferramenta automaticamente, crie um arquivo chamado `.agents/AGENTS.md` na raiz do seu projeto de desenvolvimento (onde você conversa com a IA) e adicione a seguinte regra:

```markdown
- **Firebird AI Inspector**: Sempre que precisar de informações sobre a estrutura do banco de dados Firebird, NÃO TENTE ADIVINHAR. 
  - Utilize sua ferramenta de terminal (run_command) para executar o script: `python C:\Caminho\Para\fb_inspector.py schema NOME_DA_TABELA`
  - Para listar tabelas, use `python C:\Caminho\Para\fb_inspector.py tables`.
```

## 💻 Uso Manual (Linha de Comando)

Você também pode usar a ferramenta manualmente no terminal:

**Listar todas as tabelas:**
```bash
python fb_inspector.py tables
```

**Ver a estrutura de uma tabela:**
```bash
python fb_inspector.py schema NOME_DA_TABELA
```

**Executar uma query:**
```bash
python fb_inspector.py query "SELECT FIRST 5 * FROM CLIENTES"
```

**Sobrescrever configurações do `.env` temporariamente:**
```bash
python fb_inspector.py --host 192.168.0.100 --db "C:\outro_banco.fdb" tables
```

## ⚠️ Atenção (Segurança)
Nunca combe o seu arquivo `.env` com senhas reais no GitHub. O arquivo `.gitignore` já está configurado para ignorá-lo.
