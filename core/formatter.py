from tabulate import tabulate


class OutputFormatter:
    """Separa a camada visual/apresentação do resto do sistema."""

    @staticmethod
    def print_table(headers, rows, title=None):
        if title:
            print(f"\n=== {title} ===")
        if not rows:
            print("Nenhum registro encontrado.")
            return
        print(tabulate(rows, headers=headers, tablefmt="grid"))

    @staticmethod
    def print_text(text, title=None):
        if title:
            print(f"\n=== {title} ===")
        print(text)
