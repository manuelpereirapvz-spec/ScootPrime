# Exemplo de ficheiro WSGI para PythonAnywhere.
# Copie este conteúdo para o ficheiro WSGI do PythonAnywhere, ajustando o caminho e o username.

import os
import sys

path = '/home/yourusername/ScootPrime'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ.setdefault('INSTANCE_PATH', '/home/yourusername/instance')
os.environ.setdefault('SCOOTPRIME_SECRET', 'replace-with-a-secure-key')

from wsgi import app as application
