# ScootPrimeWeb num Portatil como Servidor

Este guia foi pensado para correr o projeto de forma seria usando apenas software gratuito.

## Recomendacao base

Para um setup "profissional" num portatil, a melhor base e:

- Ubuntu Server LTS dedicado ao servidor
- Nginx como reverse proxy
- Gunicorn para correr a app Flask
- systemd para arrancar automaticamente no boot
- UFW como firewall
- fail2ban para proteger SSH
- Certbot + Let's Encrypt para HTTPS
- DuckDNS ou dominio proprio para chegar ao servidor a partir da Internet

## Antes de comecar

Um portatil pode servir bem para arrancar, mas ha limites:

- Use cabo de rede, nao Wi-Fi, sempre que possivel.
- Deixe o portatil ligado a corrente e com boa ventilacao.
- Desative sleep, hibernacao e fecho da tampa.
- Defina IP fixo para o portatil na rede local.
- Se o ISP usar CGNAT ou bloquear portas 80/443, o acesso publico fica bastante mais dificil.

Se quer acesso publico com HTTPS, o router precisa de encaminhar:

- porta 80 -> portatil
- porta 443 -> portatil

## Arquitetura recomendada

Internet -> Router -> Nginx -> Gunicorn -> Flask -> SQLite

Dados persistentes:

- `/opt/scootprime/instance/scootprime.db`
- `/opt/scootprime/instance/backups`
- `/opt/scootprime/instance/brand`

## 1. Instalar Ubuntu Server

Instale Ubuntu Server LTS no portatil.

Em maio de 2026, a documentacao oficial do Ubuntu Server aponta para a linha LTS mais recente. Se o teu hardware for muito recente, usa a LTS atual; se houver problema de drivers, 24.04 LTS continua a ser uma base segura.

Durante a instalacao:

- instale `OpenSSH server`
- crie um utilizador administrador
- configure o hostname, por exemplo `scootprime-server`

## 2. Instalar os pacotes gratuitos

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y git python3 python3-venv python3-pip nginx ufw fail2ban snapd
```

## 3. Criar utilizador e pastas da app

```bash
sudo adduser --system --group --home /opt/scootprime --shell /usr/sbin/nologin scootprime
sudo mkdir -p /opt/scootprime/app
sudo mkdir -p /opt/scootprime/instance
sudo chown -R scootprime:scootprime /opt/scootprime
```

## 4. Copiar o projeto para o servidor

Opcao A, com Git:

```bash
cd /opt/scootprime
sudo -u scootprime git clone /caminho/do/repositorio app
```

Opcao B, copiar os ficheiros manualmente para `/opt/scootprime/app`.

## 5. Criar o ambiente Python

```bash
cd /opt/scootprime/app
sudo -u scootprime python3 -m venv .venv
sudo -u scootprime .venv/bin/pip install --upgrade pip
sudo -u scootprime .venv/bin/pip install -r requirements.txt
```

## 6. Configurar variaveis de ambiente

Crie o ficheiro `/etc/scootprime.env`:

```bash
sudo nano /etc/scootprime.env
```

Conteudo sugerido:

```env
FLASK_ENV=production
SCOOTPRIME_SECRET=troque-por-uma-chave-longa-e-aleatoria
INSTANCE_PATH=/opt/scootprime/instance
SESSION_COOKIE_SECURE=1
TRUST_PROXY=1
```

Gerar uma chave segura:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 7. Criar o servico systemd

Usa o exemplo em `deploy/linux/scootprime.service.example`.

Instalacao:

```bash
sudo cp /opt/scootprime/app/deploy/linux/scootprime.service.example /etc/systemd/system/scootprime.service
sudo systemctl daemon-reload
sudo systemctl enable --now scootprime
sudo systemctl status scootprime
```

## 8. Configurar Nginx

Usa o exemplo em `deploy/linux/nginx-scootprime.conf.example`.

Instalacao:

```bash
sudo cp /opt/scootprime/app/deploy/linux/nginx-scootprime.conf.example /etc/nginx/sites-available/scootprime
sudo ln -s /etc/nginx/sites-available/scootprime /etc/nginx/sites-enabled/scootprime
sudo nginx -t
sudo systemctl reload nginx
```

Antes disso, troca `server_name` pelo teu dominio.

## 9. Firewall e protecao base

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo systemctl enable --now fail2ban
```

O Ubuntu tambem suporta atualizacoes de seguranca automaticas com `unattended-upgrades`.

## 10. DNS dinamico e HTTPS

### Se tiveres dominio proprio

- aponta o registo `A` para o IP publico da tua casa
- se o IP mudar com frequencia, usa um atualizador DDNS do teu fornecedor DNS

### Se quiseres uma opcao gratuita

DuckDNS continua a apresentar-se como servico gratuito de DNS dinamico.

Instalacao recomendada do Certbot:

```bash
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/local/bin/certbot
```

Depois de o nome apontar para a tua casa e o router encaminhar portas 80/443:

```bash
sudo certbot --nginx -d teu-dominio.duckdns.org
```

Se a porta 80 nao estiver acessivel a partir da Internet, a validacao HTTP-01 do Let's Encrypt nao vai funcionar.

## 11. Backups

Mesmo com SQLite, nao corras sem backup.

Minimo recomendado:

- backup diario da pasta `/opt/scootprime/instance`
- copia para disco externo ou outro computador
- teste de restauracao 1 vez por mes

## 12. Atualizar a aplicacao

```bash
cd /opt/scootprime/app
sudo -u scootprime git pull
sudo -u scootprime .venv/bin/pip install -r requirements.txt
sudo systemctl restart scootprime
```

## 13. Quando este setup deixa de ser boa ideia

Convem sair do portatil e ir para um mini-PC, NAS ou VPS quando acontecer um destes casos:

- varios utilizadores ao mesmo tempo
- precisas de alta disponibilidade
- precisas de IP fixo publico
- queres garantir uptime comercial
- queres crescer para PostgreSQL ou mais do que uma instancia

## Nota importante sobre este projeto

Fiz um ajuste na app para ela respeitar `INSTANCE_PATH` em producao e para confiar corretamente nos headers do proxy quando `TRUST_PROXY=1`.

Isso e importante para o setup `Nginx -> Gunicorn -> Flask`, porque os dados passam a ficar exatamente na pasta de producao definida em `/etc/scootprime.env`.
