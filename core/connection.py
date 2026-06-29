import sys
import fdb
import logging

logging.basicConfig(
    filename="inspector.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s",
)


class DatabaseConnection:
    """Gerencia a conexão com o Firebird."""

    def __init__(self, host, port, database, user, password, charset):
        try:
            self.conn = fdb.connect(
                host=host,
                port=port,
                database=database,
                user=user,
                password=password,
                charset=charset,
            )
        except Exception as e:
            logging.error(f"Falha na conexão: {e}")
            print(
                f"Erro Crítico: Falha na conexão com o banco de dados. (Veja inspector.log para detalhes)"
            )
            sys.exit(1)

    def close(self):
        if self.conn:
            self.conn.close()

    def fetch_all(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        headers = [desc[0] for desc in cur.description] if cur.description else []
        rows = cur.fetchall()
        return headers, rows

    def fetch_one(self, sql, params=()):
        cur = self.conn.cursor()
        cur.execute(sql, params)
        return cur.fetchone()

    def get_raw_connection(self):
        return self.conn
