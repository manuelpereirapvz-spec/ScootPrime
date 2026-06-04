# ScootPrimeWeb

Versao web local do ScootPrime, pensada para correr no browser com SQLite.

## Como arrancar

```powershell
cd C:\Users\Admin\Documents\Trotinetes\ScootPrimeWeb
python -m pip install -r requirements.txt
python run.py
```

Depois abra:

```text
http://127.0.0.1:5000
```

## Base de dados

A base SQLite fica por defeito em:

```text
ScootPrimeWeb\instance\scootprime.db
```

As copias de seguranca ficam em:

```text
ScootPrimeWeb\instance\backups
```

## Estrutura principal

- `scootprime_web/storage.py`: ligacao SQLite, tabelas e operacoes da base de dados.
- `scootprime_web/routes.py`: paginas e acoes do browser.
- `scootprime_web/templates`: HTML das abas.
- `scootprime_web/static/css/app.css`: estilo visual.
- `scootprime_web/static/js/app.js`: automatismos da interface.

## Automatismos incluidos

- Menu inicial com utilizador/password e criacao do primeiro acesso na primeira abertura.
- Upload da imagem da marca em Manutencao, usada no menu, login e PDFs de orcamento.
- Dados da loja personalizaveis em Manutencao para cabecalho dos PDFs.
- PDF profissional para ocorrencias, com referencia propria e descricao do registo.
- PDFs profissionais para stock existente e stock em falta/reposicao.
- Copias de seguranca podem ser descarregadas para o computador e eliminadas depois.
- Painel inicial com indicadores, valores em aberto, alertas de stock baixo e atividade recente.
- Pesquisa global na barra superior e atalho `Ctrl+K`.
- Pesquisa automatica em clientes, stock e pesquisa global enquanto escreve.
- Calculo automatico de IVA, total e valor em aberto nos orcamentos.
- Baixa automatica de stock ao criar orcamentos, com validacao de stock disponivel.
- Historico dos materiais usados em cada orcamento e reposicao de stock ao eliminar o orcamento.
- Controlo rapido de stock com botoes `+` e `-`.
- Janela moderna para adicionar produtos ao stock.
- Layout responsivo para monitores grandes, portateis e tablets.

## Validacao rapida

```powershell
python -m unittest discover
```

## Servidor no portatil

Se quiser correr isto num portatil como servidor com software gratuito, veja:

- `SERVIDOR_PORTATIL.md`
- `deploy/linux/scootprime.service.example`
- `deploy/linux/nginx-scootprime.conf.example`
