from core.formatter import OutputFormatter


class InspectorService:
    """Concentra todas as queries de sistema (metadados) do Firebird."""

    def __init__(self, db_connection):
        self.db = db_connection
        self.formatter = OutputFormatter()

    def list_tables(self):
        sql = """
            SELECT RDB$RELATION_NAME AS TABLE_NAME
            FROM RDB$RELATIONS
            WHERE RDB$VIEW_BLR IS NULL
            AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
            ORDER BY RDB$RELATION_NAME
        """
        _, rows = self.db.fetch_all(sql)
        rows = [[str(r[0]).strip()] for r in rows]
        self.formatter.print_table(["Nome da Tabela"], rows, "Tabelas do Sistema")

    def list_views(self):
        sql = """
            SELECT RDB$RELATION_NAME AS VIEW_NAME
            FROM RDB$RELATIONS
            WHERE RDB$VIEW_BLR IS NOT NULL
            AND (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
            ORDER BY RDB$RELATION_NAME
        """
        _, rows = self.db.fetch_all(sql)
        rows = [[str(r[0]).strip()] for r in rows]
        self.formatter.print_table(["Nome da View"], rows, "Views do Sistema")

    def show_schema(self, table_name):
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
        _, rows = self.db.fetch_all(sql, (table_name.upper(),))
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

            type_str = ftype
            if ftype in ("VARYING", "TEXT", "CSTRING"):
                type_str = f"{ftype}({flen})"
            elif ftype in ("SHORT", "LONG", "INT64", "DOUBLE", "FLOAT") and fscale and fscale < 0:
                type_str = f"NUMERIC/DECIMAL({fprec}, {-fscale})"

            formatted_rows.append([is_pk, fname, type_str, not_null])

        self.formatter.print_table(
            ["Chave", "Campo", "Tipo de Dado", "Obrigatório"],
            formatted_rows,
            f"Estrutura: {table_name.upper()}",
        )

    def list_procedures(self):
        sql = """
            SELECT RDB$PROCEDURE_NAME
            FROM RDB$PROCEDURES
            WHERE (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
            ORDER BY RDB$PROCEDURE_NAME
        """
        _, rows = self.db.fetch_all(sql)
        rows = [[str(r[0]).strip()] for r in rows]
        self.formatter.print_table(["Nome da Procedure"], rows, "Stored Procedures")

    def show_procedure(self, proc_name):
        sql = """
            SELECT RDB$PROCEDURE_SOURCE
            FROM RDB$PROCEDURES
            WHERE RDB$PROCEDURE_NAME = UPPER(?)
        """
        row = self.db.fetch_one(sql, (proc_name.upper(),))
        if not row or not row[0]:
            print(f"Procedure '{proc_name}' não encontrada ou código-fonte vazio.")
            return
        self.formatter.print_text(row[0], f"Código Fonte da Procedure: {proc_name.upper()}")

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

        _, rows = self.db.fetch_all(sql, params)
        formatted_rows = []
        for r in rows:
            trigger_name = str(r[0]).strip()
            t_name = str(r[1]).strip() if r[1] else "DB_TRIGGER"
            formatted_rows.append([trigger_name, t_name, r[2], r[3]])

        self.formatter.print_table(
            ["Trigger", "Tabela/Escopo", "Ordem", "Tipo (Num)"], formatted_rows, "Triggers"
        )

    def show_trigger(self, trigger_name):
        sql = """
            SELECT RDB$TRIGGER_SOURCE
            FROM RDB$TRIGGERS
            WHERE RDB$TRIGGER_NAME = UPPER(?)
        """
        row = self.db.fetch_one(sql, (trigger_name.upper(),))
        if not row or not row[0]:
            print(f"Trigger '{trigger_name}' não encontrada ou sem código-fonte.")
            return
        self.formatter.print_text(row[0], f"Código Fonte da Trigger: {trigger_name.upper()}")

    def list_generators(self):
        sql = """
            SELECT RDB$GENERATOR_NAME
            FROM RDB$GENERATORS
            WHERE (RDB$SYSTEM_FLAG IS NULL OR RDB$SYSTEM_FLAG = 0)
            ORDER BY RDB$GENERATOR_NAME
        """
        _, rows = self.db.fetch_all(sql)

        formatted_rows = []
        cur = self.db.get_raw_connection().cursor()
        for r in rows:
            gen_name = str(r[0]).strip()
            try:
                # Dispara GEN_ID internamente
                cur.execute(f"SELECT GEN_ID({gen_name}, 0) FROM RDB$DATABASE")
                val = cur.fetchone()[0]
                self.db.log_sql(f"SELECT GEN_ID({gen_name}, 0) FROM RDB$DATABASE", rows_affected=1)
            except Exception as e:
                self.db.log_sql(f"SELECT GEN_ID({gen_name}, 0) FROM RDB$DATABASE", error=str(e))
                val = "Erro ao ler"
            formatted_rows.append([gen_name, val])

        self.formatter.print_table(
            ["Generator / Sequence", "Valor Atual"], formatted_rows, "Generators Ativos"
        )

    def list_indices(self, table_name):
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
        _, rows = self.db.fetch_all(sql, (table_name.upper(),))

        idx_dict = {}
        for r in rows:
            idx_name = str(r[0]).strip()
            is_unique = "SIM" if r[1] == 1 else "NÃO"
            field = str(r[2]).strip()

            if idx_name not in idx_dict:
                idx_dict[idx_name] = {"unique": is_unique, "fields": []}
            idx_dict[idx_name]["fields"].append(field)

        formatted_rows = []
        for name, data in idx_dict.items():
            formatted_rows.append([name, data["unique"], ", ".join(data["fields"])])

        self.formatter.print_table(
            ["Nome do Índice", "Único?", "Campos Indexados"],
            formatted_rows,
            f"Índices da Tabela: {table_name.upper()}",
        )

    def execute_query(self, sql):
        cur = self.db.get_raw_connection().cursor()
        try:
            cur.execute(sql)
            if cur.description:
                headers = [desc[0] for desc in cur.description]
                rows = cur.fetchmany(100)
                self.db.log_sql(sql, rows_affected=len(rows))
                self.formatter.print_table(headers, rows, "Resultado da Consulta (Max 100 linhas)")
                if cur.fetchone():
                    print(
                        "\n... (mais resultados foram omitidos para não sobrecarregar o terminal)"
                    )
            else:
                self.db.get_raw_connection().commit()
                self.db.log_sql(sql, rows_affected=cur.rowcount)
                print("Instrução executada com sucesso. (Commit realizado, nenhum dado retornado)")
        except Exception as e:
            self.db.log_sql(sql, error=str(e))
            print(f"Erro ao executar a instrução SQL:\n{e}")
