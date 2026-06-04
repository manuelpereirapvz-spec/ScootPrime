"""WSGI entry point for the application."""
import os
import sys
from pathlib import Path

# Carrega variáveis de ambiente se existir arquivo .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from scootprime_web import create_app

# Factory que Gunicorn vai usar
app = create_app()

if __name__ == "__main__":
    # Para testes locais
    app.run()
