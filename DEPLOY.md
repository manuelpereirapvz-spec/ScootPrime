# ScootPrimeWeb - Guia de Deploy no Waifyl

## Pré-requisitos

1. Conta no Waifyl (https://www.waifyl.com ou similar)
2. Git instalado
3. Python 3.11+

## Passo 1: Preparar o repositório Git

```powershell
# Navigate to project directory
cd C:\Users\Admin\Documents\ScootPrimeWeb

# Initialize git (se ainda não o fez)
git init
git add .
git commit -m "Initial commit: ScootPrimeWeb configuration for Waifyl"
```

## Passo 2: Conectar ao Waifyl

### Opção A: Via Waifyl Dashboard

1. Aceda ao Waifyl e crie uma nova aplicação
2. Selecione "Python" como linguagem
3. Conecte o repositório GitHub / GitLab
4. Configure as variáveis de ambiente

### Opção B: Via CLI (se Waifyl tiver CLI)

```powershell
# Login
waifyl login

# Deploy
waifyl deploy
```

## Passo 3: Configurar Variáveis de Ambiente

No dashboard do Waifyl, configure as seguintes variáveis:

```
FLASK_ENV=production
SCOOTPRIME_SECRET=seu-secret-key-seguro-aqui
INSTANCE_PATH=/app/instance  # ou local apropriado no Waifyl
```

**IMPORTANTE**: Gere uma SECRET_KEY segura:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Passo 4: Configurar Persistência de Dados (Importante!)

### Problema: SQLite não persiste em plataformas cloud

SQLite não é adequado para ambiente cloud porque:
- Os arquivos são perdidos quando a aplicação reinicia
- Não suporta múltiplas instâncias

### Soluções:

**OPÇÃO 1: Usar base de dados PostgreSQL (RECOMENDADO)**

1. Provisione PostgreSQL no Waifyl ou use um serviço externo (ElephantSQL, Railway, etc.)
2. Instale o driver PostgreSQL:

```bash
# Adicione ao requirements.txt:
psycopg2-binary>=2.9.0
```

3. Atualize o código para usar PostgreSQL em produção:

**OPÇÃO 2: Usar volume/storage persistente

Contacte o Waifyl para configurar um volume persistente para `/app/instance`

## Passo 5: Estrutura Esperada

Após configuração, o Waifyl espera encontrar:

```
Procfile           ← Instrui como iniciar a app
runtime.txt        ← Versão do Python
requirements.txt   ← Dependências Python
wsgi.py            ← Entry point para WSGI
scootprime_web/    ← Aplicação Flask
```

## Passo 6: Deploy

Depois de configurado:

```powershell
# Push para o repositório configurado
git push origin main

# O Waifyl detecta as mudanças e faz deploy automaticamente
# Acompanhe o processo no dashboard
```

## Passo 7: Acessar a Aplicação

Após deployment bem-sucedido:

```
https://seu-app-name.waifyl.com
```

## Troubleshooting

### Build Logs
- Verifique os logs de build no dashboard do Waifyl
- Procure por erros em `Procfile` ou `runtime.txt`

### Erros de Conexão à BD
- Verifique se as variáveis de ambiente estão configuradas
- Confirme que a porta e host estão corretos em produção

### Aplicação não arranca
- Verifique se `gunicorn` está em `requirements.txt`
- Verifique o `Procfile` (espaçamento é importante)
- Veja os logs em tempo real no dashboard

## Monitoramento em Produção

Recomenda-se adicionar logging e monitoramento:

```bash
# Adicionar ao requirements.txt:
python-dotenv>=1.0.0
```

Configure alertas no Waifyl para:
- Erros 5xx
- Performance lenta
- Consumo de memória

## Actualizar Base de Dados em Produção

Se fizer alterações à estrutura da BD:

```powershell
# Localmente, teste as migrações
python -c "from scootprime_web import create_app; app = create_app(); app.app_context().push(); from scootprime_web.storage import init_db; init_db()"

# Em produção, pode ser necessário fazer SSH e executar manualmente
# ou criar um script de inicialização
```

## Segurança

- ✅ Nunca commit SECRET_KEY para Git
- ✅ Use variáveis de ambiente para dados sensíveis
- ✅ Configure SSL/TLS (Waifyl faz automaticamente)
- ✅ Considere CORS se tiver frontend separado
- ✅ Implemente rate limiting para API

## Próximos Passos

1. Escolha solução para persistência (PostgreSQL recomendado)
2. Configure backups automáticos da BD
3. Implemente logs centralizados
4. Configure CI/CD para testes automáticos antes de deploy
