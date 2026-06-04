# 📦 Configuração do Volume Persistente no Waifyl

## O que é Volume Persistente?

Um volume persistente é um armazenamento em disco que:
- ✅ Persiste após reinícios da aplicação
- ✅ Não é perdido ao fazer deploy
- ✅ Partilhável entre instâncias (se escalar)
- ✅ Pode fazer backup

---

## 🔧 Passos para Configurar no Waifyl

### 1. No Dashboard Waifyl

1. Aceda à sua aplicação
2. Vá para **Settings** → **Volumes** (ou **Storage**)
3. Clique em **Add Volume** ou **Create Volume**
4. Configure:
   - **Mount Path:** `/app/instance`
   - **Size:** Comece com 1-5 GB (ajuste conforme necessidade)
   - **Name:** `scootprime-storage` (ou similar)

### 2. Waifyl Monta Automaticamente

Após criar o volume:
- Waifyl monta automaticamente em `/app/instance`
- Seu código acede aos arquivos normalmente
- SQLite, backups, imagens de marca - tudo fica lá

---

## 📝 Variáveis de Ambiente

Configure no Waifyl:

```
FLASK_ENV = production
SCOOTPRIME_SECRET = [seu-secret-key-seguro]
INSTANCE_PATH = /app/instance
```

---

## 🔍 Como Funciona com Seu Código

O projeto já está configurado! Veja em [config.py](config.py):

```python
INSTANCE_PATH = Path(os.environ.get("INSTANCE_PATH", "instance"))
```

Em produção (Waifyl com volume):
```
/app/instance/scootprime.db       # Base de dados
/app/instance/backups/             # Backups
/app/instance/brand/               # Logo da marca
```

---

## ✅ Checklist de Deploy com Volume Persistente

- [ ] Criar volume `/app/instance` no Waifyl
- [ ] Configurar `INSTANCE_PATH=/app/instance` em Waifyl
- [ ] Fazer push para Git
- [ ] Waifyl detecta e faz deploy
- [ ] Acessar a aplicação
- [ ] Criar utilizador (primeira vez)
- [ ] Upload logo da marca (em Manutenção)
- [ ] Fazer alguns testes
- [ ] Verificar que BD persiste após restart

---

## 🔄 Fazer Backup do Volume

### Via Dashboard Waifyl
- Procure opção "Snapshots" ou "Backups"
- Clique em "Create Snapshot"
- Waifyl gera backup automático

### Via SSH/Linha de Comando (se disponível)
```bash
# Contacte Waifyl para acesso SSH
ssh user@your-app.waifyl.app

# Ver conteúdo do volume
ls -la /app/instance/

# Download de backup
scp user@your-app.waifyl.app:/app/instance/scootprime.db ./backup/
```

---

## 🆘 Troubleshooting

| Problema | Solução |
|----------|---------|
| Aplicação não consegue escrever | Volume não foi montado - verifique no dashboard |
| Dados desaparecem | Verificar permissões do volume |
| Espaço insuficiente | Aumentar tamanho do volume em Waifyl |
| Performance lenta | Considerar volume SSD se disponível |

---

## 📈 Próximos Passos

1. **Contactar Suporte Waifyl** - confirmar como criar volume
2. **Criar volume** `/app/instance`
3. **Fazer Deploy** - Git push
4. **Testar** - criar utilizador, upload logo, fazer testes
5. **Configurar Backups** - snapshots automáticos (se disponível)

---

## 💡 Dica: Desenvolvimento Local

Para simular ambiente Waifyl localmente:

```powershell
# Definir variáveis de ambiente
$env:FLASK_ENV = "production"
$env:INSTANCE_PATH = "instance"
$env:SCOOTPRIME_SECRET = "seu-secret-key-aqui"

# Correr aplicação
python run.py
```

Os dados ficarão em `./instance/` igual a Waifyl.
