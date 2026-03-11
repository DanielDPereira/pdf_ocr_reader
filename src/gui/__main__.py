"""Ponto de entrada para rodar a GUI como módulo: python -m src.gui"""
from src.gui.app import PDFOcrApp

if __name__ == "__main__":
    app = PDFOcrApp()
    app.mainloop()
