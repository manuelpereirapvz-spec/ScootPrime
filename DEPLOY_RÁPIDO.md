# 🚀 ScootPrimeWeb - Guia Rápido de Deploy

## 1️⃣ Preparar Localmente

```powershell
# Criar venv
python -m venv .venv
.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r requirements.txt

# Testar localmente
python run.py

# Visitar: http://127.0.0.1:5000
```

## 2️⃣ Preparar para Git

```powershell
# Inicializar git (primeira vez)
git init
git remote add origin https://github.com/SEU-USER/scootprimeweb.git

# Adicionar arquivos
git add .
git commit -m "Configurar para Waifyl"

# Push
git push -u origin main
```

## 3️⃣ Deploy no Waifyl

### Via Dashboard:

1. Aceda a https://www.waifyl.com (ou seu domínio)
2. Clique "New Application"
3. Selecione "Python"
4. Conecte seu repositório GitHub
5. Waifyl detecta automaticamente:
   - ✅ `Procfile` → Como iniciar
   - ✅ `runtime.txt` → Versão Python
   - ✅ `requirements.txt` → Dependências

### Configurar Variáveis de Ambiente:

No dashboard → Settings → Environment Variables

```
FLASK_ENV = production
SCOOTPRIME_SECRET = seu-secret-key-aqui-muito-seguro
```

**Gerar SECRET_KEY segura:**
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## 4️⃣ Primeira Inicialização em Produção

Waifyl executa automaticamente:
1. Instala dependências de `requirements.txt`
2. Executa comando do `Procfile`: `gunicorn -w 4 -b 0.0.0.0:$PORT "scootprime_web:create_app()"`
3. A aplicação inicia no URL fornecido

## 5️⃣ ⚠️ Problema Crítico: Persistência de Dados

**SQLite NÃO persiste em plataformas cloud!**

### Solução: Migrar para PostgreSQL

#### Opção A: PostgreSQL Gerido (Recomendado)

Serviços como:
- Railway (railway.app)
- Render (render.com)
- ElephantSQL (elephantsql.com)

1. Crie conta e uma base de dados PostgreSQL
2. Copie o connection string
3. Adicione ao requirements.txt:
   ```
   psycopg2-binary>=2.9.0
   SQLAlchemy>=2.0.0
   Flask-SQLAlchemy>=3.0.0
   ```

4. Contacte suporte Waifyl para integração

#### Opção B: Volume Persistente Waifyl

Contacte Waifyl para configurar um volume persistente em `/app/instance`

## 6️⃣ Atualizar Código

Após deploying:

```powershell
# Fazer mudanças locais
# ... editar arquivos ...

# Commit e push
git add .
git commit -m "Descrição da mudança"
git push origin main

# Waifyl detecta e faz redeploy automaticamente
```

## 7️⃣ Monitorar

No dashboard Waifyl:
- 📊 Logs em tempo real
- 💾 Uso de memória/CPU
- 🔄 Histórico de deployments
- ⚠️ Alertas de erro

## 🐛 Troubleshooting

| Problema | Solução |
|----------|---------|
| Build falha | Verifique `Procfile` e `runtime.txt` |
| Aplicação não arranca | Veja logs, verifique `requirements.txt` |
| 502 Bad Gateway | Reinicie, verifique memória |
| Dados desaparecem após restart | Migre para PostgreSQL |

## 📝 Checklist Final

- [ ] Repositório Git criado
- [ ] `Procfile` presente
- [ ] `runtime.txt` presente
- [ ] `requirements.txt` atualizado
- [ ] Variáveis de ambiente configuradas em Waifyl
- [ ] Primeira versão deployed
- [ ] Testado em https://seu-app-name.waifyl.com
- [ ] Solução de persistência definida
- [ ] Backups configurados (se aplicável)

## 📞 Suporte

Para dúvidas:
1. Veja `DEPLOY.md` para guia detalhado
2. Contacte Waifyl support
3. Consulte Flask documentation: https://flask.palletsprojects.com/
