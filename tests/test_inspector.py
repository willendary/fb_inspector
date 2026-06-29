import unittest
from unittest.mock import MagicMock
from services.inspector import InspectorService
from core.formatter import OutputFormatter


class TestInspectorService(unittest.TestCase):

    def setUp(self):
        # Cria um Mock da conexão com o banco
        self.mock_db = MagicMock()
        self.inspector = InspectorService(self.mock_db)

        # Oculta os prints do formatter para não sujar o log de testes
        self.inspector.formatter.print_table = MagicMock()
        self.inspector.formatter.print_text = MagicMock()

    def test_list_tables(self):
        # Simula o retorno de tabelas do Firebird
        self.mock_db.fetch_all.return_value = (["TABLE_NAME"], [("CLIENTES",), ("PRODUTOS",)])

        self.inspector.list_tables()

        # Verifica se a query foi executada
        self.assertTrue(self.mock_db.fetch_all.called)

        # Verifica se o formatter foi chamado com a estrutura correta (sem o tuple)
        self.inspector.formatter.print_table.assert_called_once_with(
            ["Nome da Tabela"], [["CLIENTES"], ["PRODUTOS"]], "Tabelas do Sistema"
        )

    def test_list_procedures(self):
        # Simula procedures
        self.mock_db.fetch_all.return_value = (["RDB$PROCEDURE_NAME"], [("SP_CALCULA_TOTAL",)])
        self.inspector.list_procedures()

        self.inspector.formatter.print_table.assert_called_once_with(
            ["Nome da Procedure"], [["SP_CALCULA_TOTAL"]], "Stored Procedures"
        )


if __name__ == "__main__":
    unittest.main()
