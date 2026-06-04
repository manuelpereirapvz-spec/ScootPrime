"""Development server runner."""
import os
from dotenv import load_dotenv

from scootprime_web import create_app


# Carrega variáveis de ambiente do arquivo .env se existir
load_dotenv()

app = create_app()


if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    host = os.environ.get("FLASK_HOST", "127.0.0.1")
    port = int(os.environ.get("FLASK_PORT", "5000"))
    
    print(f"🚀 Iniciando ScootPrimeWeb")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Debug: {debug}")
    print(f"   URL: http://{host}:{port}")
    
    app.run(host=host, port=port, debug=debug, use_reloader=debug)
