import sys
import fdb
import logging
import os

# 1. Configuração do log de erros críticos (Modo Append)
error_logger = logging.getLogger("error_logger")
error_logger.setLevel(logging.ERROR)
eh = logging.FileHandler("inspector_errors.log", encoding="utf-8")
eh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
error_logger.addHandler(eh)

# 2. Configuração do log de auditoria / histórico de SQL (Modo Append)
audit_logger = logging.getLogger("audit_logger")
audit_logger.setLevel(logging.INFO)
ah = logging.FileHandler("sql_history.log", encoding="utf-8")
ah.setFormatter(logging.Formatter("%(asctime)s - [AUDITORIA] - %(message)s"))
audit_logger.addHandler(ah)


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
            audit_logger.info(f"Conexão estabelecida: {database} (Usuário: {user})")
        except Exception as e:
            error_logger.error(f"Falha na conexão: {e}")
            print(
                f"Erro Crítico: Falha na conexão com o banco de dados. (Veja inspector_errors.log para detalhes)"
            )
            sys.exit(1)

    def close(self):
        if self.conn:
            self.conn.close()
            audit_logger.info("Conexão encerrada.")

    def log_sql(self, sql, params=(), error=None, rows_affected=None):
        """Salva o histórico exato do comando executado."""
        # Remove quebras de linha gigantes para manter o log limpo
        sql_clean = " ".join(sql.split())
        param_str = f" | Parametros: {params}" if params else ""

        if error:
            audit_logger.error(f"FALHA SQL: {sql_clean}{param_str} | Erro: {error}")
        else:
            rows_str = (
                f" | Linhas retornadas/afetadas: {rows_affected}"
                if rows_affected is not None
                else ""
            )
            audit_logger.info(f"EXECUCAO SQL: {sql_clean}{param_str}{rows_str}")

    def fetch_all(self, sql, params=()):
        cur = self.conn.cursor()
        try:
            cur.execute(sql, params)
            headers = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
            self.log_sql(sql, params, rows_affected=len(rows))
            return headers, rows
        except Exception as e:
            self.log_sql(sql, params, error=str(e))
            raise

    def fetch_one(self, sql, params=()):
        cur = self.conn.cursor()
        try:
            cur.execute(sql, params)
            row = cur.fetchone()
            self.log_sql(sql, params, rows_affected=1 if row else 0)
            return row
        except Exception as e:
            self.log_sql(sql, params, error=str(e))
            raise

    def get_raw_connection(self):
        return self.conn
