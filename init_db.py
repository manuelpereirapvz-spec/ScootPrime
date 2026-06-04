#!/usr/bin/env python
"""Initialize production database and directories."""
import os
import sys
from pathlib import Path

# Adicione o diretório do projeto ao path
sys.path.insert(0, os.path.dirname(__file__))

from scootprime_web import create_app

if __name__ == "__main__":
    app = create_app()
    
    with app.app_context():
        # As diretórias e base de dados são inicializadas em create_app
        print("✓ Aplicação inicializada com sucesso")
        print(f"  - Database: {app.config['DATABASE']}")
        print(f"  - Backup Dir: {app.config['BACKUP_DIR']}")
        print(f"  - Brand Dir: {app.config['BRAND_DIR']}")
