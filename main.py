import sys
from PyQt5.QtWidgets import QApplication
from interface import MainWindow

def main():
    """Função principal para iniciar a aplicação."""
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Ocorreu um erro: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()