# Deploy no PythonAnywhere

Este projeto já tem o `wsgi.py` e `requirements.txt` necessários para rodar no PythonAnywhere.
Use este guia para configurar a web app passo a passo.

---

## 1. Criar conta e web app

1. Aceda a https://www.pythonanywhere.com
2. Registe-se ou faça login
3. Vá a **Web** → **Add a new web app**
4. Escolha **Manual configuration**
5. Escolha a versão de Python suportada (recomendado: Python 3.11 se 3.14 não estiver disponível)

---

## 2. Colocar o código no PythonAnywhere

### Opção A: Git

No **Consoles** crie um bash console e execute:

```bash
cd ~
git clone https://github.com/manuelpereirapvz-spec/ScootPrime.git
cd ScootPrime
```

### Opção B: Upload ZIP

1. Faça upload do ficheiro zip com o projeto
2. Extraia-o em `~/ScootPrime`

---

## 3. Definir virtualenv

No website PythonAnywhere, em **Web**:

1. Em **Virtualenv** clique em **Enter path to a virtualenv**
2. Use algo como:
   ```bash
   /home/yourusername/.virtualenvs/scootprime
   ```
3. Crie o virtualenv em um console:
   ```bash
   python3.11 -m venv ~/.virtualenvs/scootprime
   source ~/.virtualenvs/scootprime/bin/activate
   pip install -r ~/ScootPrime/requirements.txt
   ```

> Substitua `python3.11` pela versão disponível no PythonAnywhere.

---

## 4. Configurar o ficheiro WSGI

Na aba **Web**, clique em **WSGI configuration file**.
Substitua o conteúdo pelo seguinte, ajustando `yourusername`:

```python
import os
import sys

path = '/home/yourusername/ScootPrime'
if path not in sys.path:
    sys.path.insert(0, path)

os.environ['INSTANCE_PATH'] = '/home/yourusername/instance'
os.environ['SCOOTPRIME_SECRET'] = os.environ.get('SCOOTPRIME_SECRET', 'replace-this-secret')

from wsgi import app as application
```

### Observações:
- `INSTANCE_PATH` deve apontar para uma pasta dentro do seu home no PythonAnywhere
- `SCOOTPRIME_SECRET` deve ser uma chave segura

---

## 5. Configurar variáveis de ambiente

Ainda na aba **Web**, defina as variáveis:

```
INSTANCE_PATH = /home/yourusername/instance
SCOOTPRIME_SECRET = sua_chave_secreta_segura
```

> Se preferir, pode definir `SCOOTPRIME_SECRET` no WSGI config file ou no bash profile.

---

## 6. Criar o diretório `instance`

No terminal do PythonAnywhere, execute:

```bash
mkdir -p ~/instance
```

O projeto faz a inicialização automática dos subdiretórios e da base de dados.

---

## 7. Reiniciar a app

Depois de configurar o WSGI e as variáveis, clique em **Reload** na aba Web.

---

## 8. Testar

Aceda ao URL fornecido pelo PythonAnywhere. Deve abrir a página de login do ScootPrime.

Se der erro, veja o ficheiro de logs na aba **Web**:
- `error log`
- `server log`

---

## 9. Backup / persistência

O SQLite guarda-se em `~/instance/scootprime.db`.
Use a pasta `instance` dentro do seu home para garantir que ela persiste entre reloads.

---

## 10. Nota final

Se a app não arrancar, confirme:
- o caminho em `sys.path` no WSGI
- o `INSTANCE_PATH`
- o `SECRET_KEY`
- a estrutura do projeto com `wsgi.py`, `requirements.txt`, e `scootprime_web/`
