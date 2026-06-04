# 🎯 Checklist Final - Deploy ScootPrimeWeb no Waifyl

## ✅ Fase 1: Preparação Local

### Instalar dependências
```powershell
cd C:\Users\Admin\Documents\ScootPrimeWeb
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Testar localmente
```powershell
python run.py
# Visitar http://127.0.0.1:5000
```

Verificações:
- [ ] Aplicação carrega
- [ ] Dashboard mostra (pode pedir login)
- [ ] Criar utilizador funciona
- [ ] Nenhum erro na consola

---

## ✅ Fase 2: Preparar Repositório Git

### Criar repositório
```powershell
# Se não tem Git inicializado
git init

# Adicionar todos os arquivos
git add .

# Commit inicial
git commit -m "ScootPrimeWeb configured for Waifyl deployment"
```

### Criar repositório online
1. Aceda a https://github.com (ou seu Git provider)
2. Clique "New Repository"
3. Nome: `scootprimeweb`
4. Descrição: "Web version of ScootPrime for Waifyl"
5. Crie o repositório (NÃO adicione README ainda)

### Push para online
```powershell
git remote add origin https://github.com/SEU-USERNAME/scootprimeweb.git
git branch -M main
git push -u origin main
```

Verificações:
- [ ] Todos os arquivos aparecem no GitHub
- [ ] `Procfile`, `runtime.txt`, `requirements.txt` estão lá
- [ ] Sem arquivo `.venv` ou `instance/` (bloqueados por `.gitignore`)

---

## ✅ Fase 3: Criar Aplicação no Waifyl

### Aceder a Waifyl
1. Aceda a https://www.waifyl.com
2. Faça login (ou crie conta)
3. Dashboard → "New Application" ou "Create App"

### Configurar aplicação
1. **Name:** `scootprimeweb` (ou similar)
2. **Language:** Python
3. **Repository:** Conecte seu GitHub
4. **Branch:** `main`
5. **Build Command:** (deixe em branco ou padrão)
6. **Start Command:** (Waifyl lerá do `Procfile`)

Verificações:
- [ ] Repositório conectado
- [ ] Branch selecionado
- [ ] Waifyl lê arquivo `Procfile` automaticamente

---

## ✅ Fase 4: Criar Volume Persistente

### Contactar Waifyl (se necessário)
Se o Waifyl não tiver interface visual para volumes:
- Envie email ao suporte Waifyl
- Peça: "Criar volume persistente em `/app/instance` com 2-5 GB"
- Guarde o ID ou nome do volume

### Via Dashboard Waifyl (se disponível)
1. Settings → Volumes/Storage
2. "Add Volume" ou "Create"
3. **Mount Path:** `/app/instance`
4. **Size:** `2 GB` (inicial)
5. Confirmar

Verificações:
- [ ] Volume criado
- [ ] Mount path é `/app/instance`
- [ ] Tamanho apropriado

---

## ✅ Fase 5: Configurar Variáveis de Ambiente

### No Dashboard Waifyl
1. Settings → Environment Variables
2. Adicione:

```
FLASK_ENV = production
INSTANCE_PATH = /app/instance
SCOOTPRIME_SECRET = [copie aqui a chave gerada abaixo]
```

### Gerar SECRET_KEY segura
Execute uma única vez:
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copie o output (ex: `WvJ_K7xN...`) para `SCOOTPRIME_SECRET` no Waifyl

Verificações:
- [ ] `FLASK_ENV = production`
- [ ] `INSTANCE_PATH = /app/instance`
- [ ] `SCOOTPRIME_SECRET` preenchido com chave segura

---

## ✅ Fase 6: Deploy

### Método 1: Automático (Recomendado)
```powershell
# Fazer pequeno commit para triggerar deploy
git commit --allow-empty -m "Trigger deploy"
git push origin main

# Ou edite um arquivo, commit e push
# Waifyl detecta automaticamente e inicia deploy
```

### Método 2: Manual (se Waifyl tiver botão)
1. Dashboard → sua app → "Deploy" ou "Redeploy"
2. Clique em Deploy

### Monitorar deploy
1. Vá para "Deployments" ou "Logs"
2. Veja o progresso:
   - Build: Instala Python, dependências
   - Release: Prepara aplicação
   - Runtime: Inicia Gunicorn

Esperado levar 2-5 minutos

Verificações:
- [ ] Build completa sem erros
- [ ] Applicação inicia
- [ ] URL gerada (ex: `https://scootprimeweb.waifyl.com`)

---

## ✅ Fase 7: Testar em Produção

### Aceder à aplicação
1. Abra o URL gerado (ex: `https://scootprimeweb.waifyl.com`)
2. Deve mostrar a página de login

### Teste completo
- [ ] Carrega página (sem erros 502/503)
- [ ] Criar primeiro utilizador
- [ ] Fazer login
- [ ] Dashboard carrega
- [ ] Navegar em menus (clientes, orcamentos, stock, etc)
- [ ] Upload imagem de marca (em Manutenção)
- [ ] Gerar PDF (teste)

### Teste de persistência
1. Feche browser completamente
2. Abra novamente o URL Waifyl
3. Utilize-se (deve estar logado, logo deve aparecer)
4. No dashboard Waifyl, clique "Restart" app
5. Recarregue browser (F5)
6. Dados devem estar lá (BD persistiu)

Verificações:
- [ ] Tudo funciona igual a local
- [ ] Dados persistem após restart

---

## ✅ Fase 8: Futuras Atualizações

### Para atualizar a aplicação em produção:

```powershell
# 1. Faça mudanças locais
# ... editar arquivos ...

# 2. Teste localmente
python run.py

# 3. Commit e push
git add .
git commit -m "Descrição da mudança"
git push origin main

# 4. Waifyl detecta e faz redeploy automático
# Acompanhe em Dashboard → Deployments
```

---

## 🆘 Se Algo der Errado

### Build falha
- Veja "Build Logs"
- Procure por erro em `Procfile` ou `requirements.txt`
- Comum: espaços incorretos em `Procfile`

### Aplicação não arranca (erro 502/503)
- Verifique variáveis de ambiente
- Verifique se volume `/app/instance` está montado
- Veja "Runtime Logs"

### Dados não persistem
- Confirme volume está montado em `/app/instance`
- Confirme `INSTANCE_PATH=/app/instance` está configurado
- Contacte Waifyl suporte

### Contactar Suporte
- Email: suporte@waifyl.com (ou similar)
- Forneça: nome app, erro específico, logs
- Referência: "ScootPrimeWeb Flask app with SQLite on persistent volume"

---

## 📊 Estrutura Final em Produção

```
Waifyl Server
├── /app/scootprimeweb/          ← Código da aplicação
├── /app/instance/               ← Volume Persistente (seus dados)
│   ├── scootprime.db           ← Base de dados SQLite
│   ├── backups/                ← Backups criados
│   └── brand/                  ← Logo da marca
└── Gunicorn (porta 80/443)      ← Servidor web
```

---

## 📝 Resumo de Arquivos Importantes

| Arquivo | Propósito |
|---------|-----------|
| `Procfile` | Diz ao Waifyl como iniciar (Gunicorn) |
| `runtime.txt` | Versão Python (3.11.9) |
| `requirements.txt` | Dependências Python |
| `wsgi.py` | Entry point para Gunicorn |
| `config.py` | Configurações por ambiente |
| `.env.example` | Template variáveis locais |
| `.gitignore` | Arquivos não fazer commit |
| `VOLUME_PERSISTENTE.md` | Guia detalhe do volume |
| `DEPLOY.md` | Guia completo deploy |
| `DEPLOY_RÁPIDO.md` | Guia rápido deploy |

---

## ✨ Parabéns!

Se chegou aqui e tudo funciona:
- ✅ Aplicação em produção
- ✅ Dados persistentes
- ✅ HTTPS automático (Waifyl)
- ✅ Deploy automático com Git
- ✅ Pronto para usar!

🚀 **Seu ScootPrimeWeb está vivo!**

Para dúvidas futuras, consulte:
1. `VOLUME_PERSISTENTE.md` - storage
2. `DEPLOY.md` - deployment
3. Documentação Waifyl
4. Documentação Flask
