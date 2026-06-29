"""
Firebird AI Inspector
Uma ferramenta de linha de comando (CLI) arquitetada para atuar como uma interface amigável para LLMs,
simulando as funcionalidades principais do IBExpert diretamente no terminal.

Funcionalidades: Tabelas, Views, Procedures, Triggers, Índices, Generators e Execução de SQL.
"""

import argparse
import os
import sys
from dotenv import load_dotenv
import fdb
from tabulate import tabulate

# Carrega variáveis de ambiente do .env
load_dotenv()

# Carrega API client dll customizada, se definida no .env (Crucial para o Delphi/HQBird no Windows)
client_path = os.getenv('FB_CLIENT_PATH')
if client_path and client_path.strip():
    try:
        fdb.load_api(client_path.strip())
    except Exception as e:
        print(f"Erro crítico ao carregar API do Firebird ({client_path}): {e}")
        sys.exit(1)


class FirebirdInspector:
    """Classe principal que gerencia a conexão e extração de metadados do Firebird."""
    
    def __init__(self, host, port, database, user, password, charset):
        try:
            self.conn = fdb.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                charset=charset
            )
        except Exception as e:
            print(f"Falha na conexão com o banco de dados:\n{e}")
            sys.exit(1)

    def close(self):
        """Encerra a conexão com o banco de dados."""
        if self.conn:
            self.conn.close()

    def fetch_all(self, sql, params=()):
        """Executa um comando e retorna os headers e todas as linhas."""
        cur = self.conn.cursor()
        cur.execute(sql, params)
        headers = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchall()
        return headers, rows

    def fetch_one(self, sql, params=()):
        """Executa um comando e retorna uma única linha."""
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()

    def print_table(self, headers, rows, title=None):
        """Imprime os dados no terminal utilizando a biblioteca Tabulate."""
        if title:
            print(f"\n=== {title} ===")
        if not rows:
            print("Nenhum registro encontrado.")
            return
        print(tabulate(rows, headers=headers, tablefmt="grid"))

    def list_tables(self):
        sql = """
            SELECT RDB$RELATION_NAME AS TABLE_NAME
            FROM RDB$RELATIONS
            WHERE RDB$VIEW_BLR IS NULL
            AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
            ORDER BY RDB$RELATION_NAME
        """
        _, rows = self.fetch_all(sql)
        rows = [[str(r[0]).strip()] for r in rows]
        self.print_table(["Nome da Tabela"], rows, "Tabelas do Sistema")

    def list_views(self):
        sql = """
            SELECT RDB$RELATION_NAME AS VIEW_NAME
            FROM RDB$RELATIONS
            WHERE RDB$VIEW_BLR IS NOT NULL
            AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
            ORDER BY RDB$RELATION_NAME
        """
        _, rows = self.fetch_all(sql)
        rows = [[str(r[0]).strip()] for r in rows]
        self.print_table(["Nome da View"], rows, "Views do Sistema")

    def show_schema(self, table_name):
        """Mostra campos, tipos, primary keys e obrigatoriedade de tabelas ou views."""
        sql = """
            SELECT
                F.RDB$FIELD_NAME,
                T.RDB$TYPE_NAME,
                F.RDB$FIELD_LENGTH,
                F.RDB$FIELD_PRECISION,
                F.RDB$FIELD_SCALE,
                R.RDB$NULL_FLAG,
                (SELECT 1 FROM RDB$INDEX_SEGMENTS IDX_SEG
                 JOIN RDB$INDICES IDX ON IDX.RDB$INDEX_NAME = IDX_SEG.RDB$INDEX_NAME
                 JOIN RDB$RELATION_CONSTRAINTS RC ON RC.RDB$INDEX_NAME = IDX.RDB$INDEX_NAME
                 WHERE IDX_SEG.RDB$FIELD_NAME = F.RDB$FIELD_NAME
                 AND RC.RDB$RELATION_NAME = R.RDB$RELATION_NAME
                 AND RC.RDB$CONSTRAINT_TYPE = 'PRIMARY KEY') AS IS_PK
            FROM RDB$RELATION_FIELDS R
            JOIN RDB$FIELDS F ON R.RDB$FIELD_SOURCE = F.RDB$FIELD_NAME
            JOIN RDB$TYPES T ON F.RDB$FIELD_TYPE = T.RDB$TYPE AND T.RDB$FIELD_NAME = 'RDB$FIELD_TYPE'
            WHERE R.RDB$RELATION_NAME = UPPER(?)
            ORDER BY R.RDB$FIELD_POSITION
        """
        _, rows = self.fetch_all(sql, (table_name.upper(),))
        if not rows:
            print(f"Objeto '{table_name}' não encontrado no banco.")
            return

        formatted_rows = []
        for row in rows:
            fname = str(row[0]).strip()
            ftype = str(row[1]).strip()
            flen = row[2]
            fprec = row[3]
            fscale = row[4]
            not_null = "SIM" if row[5] == 1 else ""
            is_pk = "PK" if row[6] == 1 else ""
            
            # Tratamento de tipagem nativa para humanos/IA lerem com clareza
            type_str = ftype
            if ftype in ('VARYING', 'TEXT', 'CSTRING'):
                type_str = f"{ftype}({flen})"
            elif ftype in ('SHORT', 'LONG', 'INT64', 'DOUBLE', 'FLOAT') and fscale and fscale < 0:
                 type_str = f"NUMERIC/DECIMAL({fprec}, {-fscale})"
                 
            formatted_rows.append([is_pk, fname, type_str, not_null])
            
        self.print_table(["Chave", "Campo", "Tipo de Dado", "Obrigatório"], formatted_rows, f"Estrutura: {table_name.upper()}")

    def list_procedures(self):
        sql = """
            SELECT RDB$PROCEDURE_NAME
            FROM RDB$PROCEDURES
            WHERE (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
            ORDER BY RDB$PROCEDURE_NAME
        """
        _, rows = self.fetch_all(sql)
        rows = [[str(r[0]).strip()] for r in rows]
        self.print_table(["Nome da Procedure"], rows, "Stored Procedures")

    def show_procedure(self, proc_name):
        """Extrai o código fonte integral de uma Stored Procedure."""
        sql = """
            SELECT RDB$PROCEDURE_SOURCE
            FROM RDB$PROCEDURES
            WHERE RDB$PROCEDURE_NAME = UPPER(?)
        """
        row = self.fetch_one(sql, (proc_name.upper(),))
        if not row or not row[0]:
            print(f"Procedure '{proc_name}' não encontrada ou código-fonte vazio.")
            return
        
        print(f"\n=== Código Fonte da Procedure: {proc_name.upper()} ===")
        print(row[0])

    def list_triggers(self, table_name=None):
        sql = """
            SELECT RDB$TRIGGER_NAME, RDB$RELATION_NAME, RDB$TRIGGER_SEQUENCE, RDB$TRIGGER_TYPE
            FROM RDB$TRIGGERS
            WHERE (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
        """
        params = []
        if table_name:
            sql += " AND RDB$RELATION_NAME = UPPER(?)"
            params.append(table_name)
            
        sql += " ORDER BY RDB$RELATION_NAME, RDB$TRIGGER_SEQUENCE"
        
        _, rows = self.fetch_all(sql, params)
        formatted_rows = []
        for r in rows:
            trigger_name = str(r[0]).strip()
            t_name = str(r[1]).strip() if r[1] else 'DB_TRIGGER'
            formatted_rows.append([trigger_name, t_name, r[2], r[3]])
            
        self.print_table(["Trigger", "Tabela/Escopo", "Ordem", "Tipo (Num)"], formatted_rows, "Triggers")

    def show_trigger(self, trigger_name):
        """Extrai o código fonte integral de uma Trigger."""
        sql = """
            SELECT RDB$TRIGGER_SOURCE
            FROM RDB$TRIGGERS
            WHERE RDB$TRIGGER_NAME = UPPER(?)
        """
        row = self.fetch_one(sql, (trigger_name.upper(),))
        if not row or not row[0]:
            print(f"Trigger '{trigger_name}' não encontrada ou sem código-fonte.")
            return
            
        print(f"\n=== Código Fonte da Trigger: {trigger_name.upper()} ===")
        print(row[0])

    def list_generators(self):
        """Lista Generators (Sequences) e consulta seu valor atual (GEN_ID)."""
        sql = """
            SELECT RDB$GENERATOR_NAME
            FROM RDB$GENERATORS
            WHERE (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
            ORDER BY RDB$GENERATOR_NAME
        """
        _, rows = self.fetch_all(sql)
        
        formatted_rows = []
        cur = self.conn.cursor()
        for r in rows:
            gen_name = str(r[0]).strip()
            try:
                cur.execute(f"SELECT GEN_ID({gen_name}, 0) FROM RDB$DATABASE")
                val = cur.fetchone()[0]
            except:
                val = 'Erro ao ler'
            formatted_rows.append([gen_name, val])
            
        self.print_table(["Generator / Sequence", "Valor Atual"], formatted_rows, "Generators Ativos")

    def list_indices(self, table_name):
        """Exibe os índices atrelados a uma tabela e as colunas correspondentes."""
        sql = """
            SELECT 
                IDX.RDB$INDEX_NAME, 
                IDX.RDB$UNIQUE_FLAG,
                IDX_SEG.RDB$FIELD_NAME
            FROM RDB$INDICES IDX
            JOIN RDB$INDEX_SEGMENTS IDX_SEG ON IDX.RDB$INDEX_NAME = IDX_SEG.RDB$INDEX_NAME
            WHERE IDX.RDB$RELATION_NAME = UPPER(?)
            ORDER BY IDX.RDB$INDEX_NAME, IDX_SEG.RDB$FIELD_POSITION
        """
        _, rows = self.fetch_all(sql, (table_name.upper(),))
        
        idx_dict = {}
        for r in rows:
            idx_name = str(r[0]).strip()
            is_unique = "SIM" if r[1] == 1 else "NÃO"
            field = str(r[2]).strip()
            
            if idx_name not in idx_dict:
                idx_dict[idx_name] = {'unique': is_unique, 'fields': []}
            idx_dict[idx_name]['fields'].append(field)
            
        formatted_rows = []
        for name, data in idx_dict.items():
            formatted_rows.append([name, data['unique'], ", ".join(data['fields'])])
            
        self.print_table(["Nome do Índice", "Único?", "Campos Indexados"], formatted_rows, f"Índices da Tabela: {table_name.upper()}")

    def execute_query(self, sql):
        """Executa consultas livres, limitando a exibição para proteger a memória do terminal."""
        cur = self.conn.cursor()
        try:
            cur.execute(sql)
            if cur.description:
                headers = [desc[0] for desc in cur.description]
                rows = cur.fetchmany(100) # Limite seguro para output da IA e Terminal
                self.print_table(headers, rows, "Resultado da Consulta (Max 100 linhas)")
                if cur.fetchone():
                   print("\n... (mais resultados foram omitidos para não sobrecarregar o terminal)")
            else:
                self.conn.commit()
                print("Instrução executada com sucesso. (Commit realizado, nenhum dado retornado)")
        except Exception as e:
            print(f"Erro ao executar a instrução SQL:\n{e}")


def main():
    parser = argparse.ArgumentParser(description="Firebird AI Inspector - Canivete Suíço para Metadados do Firebird")
    
    # Argumentos de Conexão opcionais
    parser.add_argument('--host', help="Servidor do banco")
    parser.add_argument('--port', help="Porta do banco")
    parser.add_argument('--db', help="Caminho absoluto do banco de dados (.fdb)")
    parser.add_argument('--user', help="Usuário (Padrão: SYSDBA)")
    parser.add_argument('--password', help="Senha")
    parser.add_argument('--charset', help="Charset da conexão")
    
    subparsers = parser.add_subparsers(dest='command', required=True, help='Ações disponíveis')
    
    # Comandos Globais de Listagem
    subparsers.add_parser('tables', help="Lista todas as tabelas (User Tables)")
    subparsers.add_parser('views', help="Lista todas as views (User Views)")
    subparsers.add_parser('procedures', help="Lista todas as Stored Procedures")
    subparsers.add_parser('generators', help="Lista todos os Generators e consulta seu valor atual")
    
    # Comandos Direcionados a um Objeto
    p_schema = subparsers.add_parser('schema', help="Mostra colunas, tipos e chaves de uma tabela ou view")
    p_schema.add_argument('name', help="Nome da tabela ou view")
    
    p_proc = subparsers.add_parser('procedure', help="Imprime o código fonte de uma procedure")
    p_proc.add_argument('name', help="Nome da procedure")
    
    p_trig = subparsers.add_parser('triggers', help="Lista triggers do banco (pode ser filtrado por tabela)")
    p_trig.add_argument('--table', help="Filtra triggers por nome da tabela", default=None)

    p_strig = subparsers.add_parser('trigger', help="Imprime o código fonte de uma trigger")
    p_strig.add_argument('name', help="Nome da trigger")

    p_idx = subparsers.add_parser('indices', help="Lista os índices e campos indexados de uma tabela")
    p_idx.add_argument('table', help="Nome da tabela")
    
    # Comando de Query Livre
    p_query = subparsers.add_parser('query', help="Executa instruções DML ou DDL livres (ex: SELECT, INSERT)")
    p_query.add_argument('sql', help="A instrução SQL envolta em aspas")
    
    args = parser.parse_args()
    
    # Resolução de variáveis de conexão (.env vs argumentos de terminal)
    host = args.host or os.getenv('FB_HOST', 'localhost')
    port = int(args.port or os.getenv('FB_PORT', '3050'))
    database = args.db or os.getenv('FB_DATABASE')
    user = args.user or os.getenv('FB_USER', 'SYSDBA')
    password = args.password or os.getenv('FB_PASSWORD', 'masterkey')
    charset = args.charset or os.getenv('FB_CHARSET', 'ISO8859_1')

    if not database:
        print("Erro Crítico: Caminho do banco não definido. Verifique o .env ou use --db.")
        sys.exit(1)

    # Inicia a Classe
    inspector = FirebirdInspector(host, port, database, user, password, charset)
    
    # Roteador de Comandos
    try:
        if args.command == 'tables':
            inspector.list_tables()
        elif args.command == 'views':
            inspector.list_views()
        elif args.command == 'procedures':
            inspector.list_procedures()
        elif args.command == 'generators':
            inspector.list_generators()
        elif args.command == 'schema':
            inspector.show_schema(args.name)
        elif args.command == 'procedure':
            inspector.show_procedure(args.name)
        elif args.command == 'triggers':
            inspector.list_triggers(args.table)
        elif args.command == 'trigger':
            inspector.show_trigger(args.name)
        elif args.command == 'indices':
            inspector.list_indices(args.table)
        elif args.command == 'query':
            inspector.execute_query(args.sql)
    finally:
        inspector.close()

if __name__ == '__main__':
    main()
