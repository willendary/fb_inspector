import os
import sys
from dotenv import load_dotenv

def load_configuration():
    """Carrega as configurações do arquivo .env."""
    load_dotenv()

def setup_firebird_api():
    """Configura o caminho customizado da dll do Firebird, se fornecido no .env."""
    client_path = os.getenv('FB_CLIENT_PATH')
    if client_path and client_path.strip():
        import fdb
        try:
            fdb.load_api(client_path.strip())
        except Exception as e:
            print(f"Erro crítico ao carregar API do Firebird ({client_path}): {e}")
            sys.exit(1)

def get_connection_params(args):
    """Resolve as credenciais de banco (Terminal vs .env)."""
    host = args.host or os.getenv('FB_HOST', 'localhost')
    port = int(args.port or os.getenv('FB_PORT', '3050'))
    database = args.db or os.getenv('FB_DATABASE')
    user = args.user or os.getenv('FB_USER', 'SYSDBA')
    password = args.password or os.getenv('FB_PASSWORD', 'masterkey')
    charset = args.charset or os.getenv('FB_CHARSET', 'ISO8859_1')
    
    if not database:
        print("Erro Crítico: Caminho do banco não definido. Verifique o .env ou use --db.")
        sys.exit(1)
        
    return host, port, database, user, password, charset
