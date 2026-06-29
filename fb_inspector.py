"""
Firebird AI Inspector - Entry Point
Este script inicializa o CLI delegando as responsabilidades para a arquitetura core/services.
"""

import argparse
from core.config import load_configuration, setup_firebird_api, get_connection_params
from core.connection import DatabaseConnection
from services.inspector import InspectorService

def main():
    parser = argparse.ArgumentParser(description="Firebird AI Inspector - Arquitetura Profissional")
    
    parser.add_argument('--host', help="Servidor do banco")
    parser.add_argument('--port', help="Porta do banco")
    parser.add_argument('--db', help="Caminho absoluto do banco de dados (.fdb)")
    parser.add_argument('--user', help="Usuário")
    parser.add_argument('--password', help="Senha")
    parser.add_argument('--charset', help="Charset")
    
    subparsers = parser.add_subparsers(dest='command', required=True, help='Ações disponíveis')
    
    subparsers.add_parser('tables', help="Lista todas as tabelas")
    subparsers.add_parser('views', help="Lista todas as views")
    subparsers.add_parser('procedures', help="Lista todas as Stored Procedures")
    subparsers.add_parser('generators', help="Lista Generators e valores atuais")
    
    p_schema = subparsers.add_parser('schema', help="Colunas e chaves de tabela/view")
    p_schema.add_argument('name', help="Nome da tabela ou view")
    
    p_proc = subparsers.add_parser('procedure', help="Código fonte de uma procedure")
    p_proc.add_argument('name', help="Nome da procedure")
    
    p_trig = subparsers.add_parser('triggers', help="Lista triggers")
    p_trig.add_argument('--table', help="Filtra por tabela", default=None)

    p_strig = subparsers.add_parser('trigger', help="Código fonte de uma trigger")
    p_strig.add_argument('name', help="Nome da trigger")

    p_idx = subparsers.add_parser('indices', help="Índices de uma tabela")
    p_idx.add_argument('table', help="Nome da tabela")
    
    p_query = subparsers.add_parser('query', help="Executa SQL livre")
    p_query.add_argument('sql', help="Instrução SQL")
    
    args = parser.parse_args()
    
    # Passos de Inicialização (Injeção de Dependência Básica)
    load_configuration()
    setup_firebird_api()
    host, port, database, user, password, charset = get_connection_params(args)

    db_connection = DatabaseConnection(host, port, database, user, password, charset)
    inspector = InspectorService(db_connection)
    
    # Roteador
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
        db_connection.close()

if __name__ == '__main__':
    main()
