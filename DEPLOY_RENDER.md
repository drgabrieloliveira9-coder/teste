# Deploy no Render - Meatz Burger

Este guia explica como fazer deploy do sistema Meatz Burger no Render usando **SQLite3 com Persistent Disk**.

## 💡 Banco de Dados

O sistema usa **SQLite3 puro** (sem ORM) em produção, que é:
- ✅ Simples e sem configuração externa
- ✅ Zero dependências extras (SQLite3 nativo do Python)
- ✅ Perfeito para pequenas e médias aplicações
- ✅ Persistente através de Render Persistent Disk

## 💰 Requisitos de Plano

⚠️ **IMPORTANTE**: Para usar SQLite3 com dados persistentes no Render, você precisa:

- **Plano Mínimo**: Starter ($7 USD/mês)
- **Motivo**: Persistent Disk NÃO funciona no plano Free
- **O que acontece no Free**: Dados são perdidos a cada redeploy/restart

**Alternativas gratuitas**:
- Usar PostgreSQL gratuito do Render (mas precisa reescrever o código)
- Migrar para Fly.io ou Railway (suportam persistent disk gratuito)

## 📋 Pré-requisitos

1. Conta no [Render](https://render.com)
2. Conta no [GitHub](https://github.com) ou [GitLab](https://gitlab.com)
3. Código do projeto em um repositório Git
4. **Plano Starter ou superior** ($7/mês mínimo)

## 🚀 Opção 1: Deploy Automático via render.yaml

### Passo 1: Conectar Repositório
1. Acesse [Render Dashboard](https://dashboard.render.com)
2. Clique em "New +" e selecione "Blueprint"
3. Conecte seu repositório do GitHub/GitLab
4. Selecione o repositório do Meatz Burger

### Passo 2: Configuração Automática
O Render detectará automaticamente o arquivo `render.yaml` e criará:
- **Web Service** (meatz-burger) no plano Starter
- **Persistent Disk** (1GB) montado em `/opt/render/project/src/data`
- **Banco SQLite** em `data/meatz.db` (persistente)

Variáveis configuradas automaticamente:
- `SECRET_KEY`: Gerado automaticamente
- `SESSION_SECRET`: Gerado automaticamente  
- `ADMIN_DEFAULT_PASSWORD`: MudeEstaSenha123! (⚠️ **MUDE APÓS DEPLOY**)

### Passo 3: Configurar API do Gemini (Opcional)
Se quiser usar o chatbot com IA:
1. Obtenha uma chave API no [Google AI Studio](https://makersuite.google.com/app/apikey)
2. No Render Dashboard, vá em "Environment"
3. Adicione a variável `GEMINI_API_KEY` com sua chave

### Passo 4: Deploy
1. Clique em "Apply"
2. Aguarde o build completar (3-5 minutos)
3. Acesse a URL fornecida pelo Render

---

## 🔧 Opção 2: Deploy Manual

### Passo 1: Criar Web Service
1. No Render Dashboard, clique em "New +" → "Web Service"
2. Conecte seu repositório
3. Configure:
   - **Name**: meatz-burger
   - **Runtime**: Python 3
   - **Build Command**: `chmod +x build.sh && ./build.sh`
   - **Start Command**: `gunicorn -c gunicorn_config.py run:app`
   - **Plan**: Starter ($7/mês)

### Passo 2: Adicionar Persistent Disk
1. Na página de configuração do Web Service, role até **"Disk"**
2. Clique em "Add Disk"
3. Configure:
   - **Name**: meatz-data
   - **Mount Path**: `/opt/render/project/src/data`
   - **Size**: 1 GB
4. Clique em "Save"

### Passo 3: Adicionar Variáveis de Ambiente
Clique em "Environment" e adicione:

```
SECRET_KEY=<gere-uma-chave-aleatória>
SESSION_SECRET=<gere-outra-chave-aleatória>
ADMIN_DEFAULT_PASSWORD=MudeEstaSenha123!
GEMINI_API_KEY=<sua-chave-opcional>
```

Para gerar chaves secretas seguras, use:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Passo 4: Deploy
1. Clique em "Create Web Service"
2. Aguarde o build completar
3. Acesse a URL fornecida

---

## ⚙️ Configuração Otimizada para Render

O sistema foi otimizado para funcionar eficientemente no Render:

### Características do Plano Starter
- ✅ **512MB RAM**: Gunicorn configurado com 2 workers
- ✅ **Persistent Disk**: Suporte a discos persistentes (cobrado separadamente)
- ✅ **Sempre ativo**: Sem sleep (diferente do Free)
- ✅ **Dados persistentes**: SQLite nunca é perdido

### Otimizações Implementadas

1. **Gunicorn otimizado** (`gunicorn_config.py`):
   - 2 workers (ideal para 512MB RAM)
   - Timeout de 120s
   - Worker temp dir em /dev/shm (memória)
   - Max 500 requests por worker
   - Preload app ativado

2. **SQLite3 puro** (sem ORM):
   - Context managers para conexões seguras
   - Transações automáticas com rollback
   - Zero dependências extras
   - Row factory para dicts

3. **Cache de arquivos estáticos**:
   - Cache de 1 ano para imagens/CSS/JS
   - Servidos diretamente pelo Flask

4. **Limite de upload**: 16MB máximo

---

## 🔐 Segurança Pós-Deploy

### ⚠️ IMPORTANTE - Primeiros Passos

1. **Mude a senha do admin imediatamente**:
   - Acesse: `https://seu-app.onrender.com/auth/login`
   - Login: `admin`
   - Senha padrão: `MudeEstaSenha123!`
   - Vá em Admin → Usuários → Editar Admin
   - Defina uma senha forte

2. **Verifique as variáveis de ambiente**:
   - Certifique-se que `SECRET_KEY` foi gerado
   - Certifique-se que `SESSION_SECRET` foi gerado

3. **Configure o Gemini API (opcional)**:
   - Adicione `GEMINI_API_KEY` se quiser chatbot IA

---

## 💾 Backup e Restauração

### Backups Automáticos (Render)
- Render cria snapshots diários do Persistent Disk
- Retenção: 7 dias
- Restauração via Dashboard → Disks → Restore Snapshot

### Backup Manual (Recomendado)

Via SSH no Render Shell:
```bash
# Fazer backup do banco SQLite
sqlite3 /opt/render/project/src/data/meatz.db ".backup '/tmp/backup.db'"

# Transferir usando magic-wormhole (pré-instalado)
wormhole send /tmp/backup.db
```

Para restaurar:
```bash
# Receber arquivo
wormhole receive

# Substituir banco (CUIDADO!)
cp backup.db /opt/render/project/src/data/meatz.db
```

---

## 📊 Monitoramento

### Logs
Acesse logs em tempo real:
1. Render Dashboard → Seu Web Service
2. Aba "Logs"

### Métricas
Monitore uso de recursos:
1. Render Dashboard → Seu Web Service
2. Aba "Metrics"

### Health Check
O Render verifica automaticamente a rota `/` a cada 30 segundos.

---

## 🆘 Solução de Problemas

### ❌ Erro: "Failed to find attribute 'app' in 'gunicorn_config'"

**Causa**: O comando Start está incorreto.

**Solução**:
1. Acesse Settings no Render Dashboard
2. Altere **Start Command** para: `gunicorn -c gunicorn_config.py run:app`
3. Salve e aguarde redeploy automático

### ❌ Banco de dados não persiste após redeploy

**Causa**: Persistent Disk não está configurado corretamente.

**Solução**:
1. Verifique se o disco está montado em `/opt/render/project/src/data`
2. Confirme que o plano é Starter ou superior (não Free)
3. Verifique logs do build para erros de criação do banco

### ❌ App não inicia

**Soluções**:
1. Verifique logs no Render Dashboard
2. Confirme que `build.sh` tem permissão de execução
3. Verifique se o Start Command está correto
4. Confirme que todas as variáveis de ambiente estão configuradas

### ❌ Erro de permissão no diretório data/

**Causa**: Diretório não existe ou sem permissão.

**Solução**: O código já cria o diretório automaticamente em `app/database.py`:
```python
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
```

### ❌ Erro 502/504 Gateway Timeout

**Causas comuns**:
1. Timeout muito curto (já configurado para 120s)
2. Workers do Gunicorn travados
3. Falta de memória RAM

**Solução**:
1. Verifique logs para erros específicos
2. Confirme que workers estão rodando
3. Considere reduzir workers para 1 se necessário

---

## 💡 Dicas Importantes

### 1. Custo Mensal
- **Plano Starter**: $7 USD/mês (instance)
- **Persistent Disk**: ~$0.25/GB/mês (cobrado separadamente, ~$0.25 para 1GB)
- **Custo Total Estimado**: ~$7.25-7.30/mês (Starter + 1GB disk)
- **HTTPS**: Gratuito (Let's Encrypt)
- **Custom Domain**: Gratuito

### 2. Manutenção de Disco
- **Downtime durante deploys**: ~30-60 segundos (para evitar corrupção do SQLite)
- **Limite de tamanho**: Disco só pode crescer, nunca diminuir
- **Crescimento**: Comece com 1GB, aumente conforme necessário

### 3. Quando considerar migração para PostgreSQL
- Mais de 100 pedidos simultâneos
- Múltiplas instâncias do app (scaling horizontal)
- Alta concorrência de escritas
- Necessidade de zero-downtime deploys

### 4. Custom Domain
Adicionar domínio próprio (gratuito):
1. Settings → Custom Domain → Add Domain
2. Configure DNS conforme instruções
3. HTTPS automático após propagação

### 5. Manter app ativo
- Plano Starter não dorme (diferente do Free)
- App sempre disponível 24/7
- Sem necessidade de keep-alive ping

---

## 📞 Recursos de Suporte

- [Documentação Oficial Render](https://render.com/docs)
- [Community Forum](https://community.render.com)
- [Status Page](https://status.render.com)
- [Persistent Disks Docs](https://render.com/docs/disks)

---

## ✅ Checklist de Deploy

Antes de colocar em produção, confirme:

- [ ] Plano Starter ou superior configurado
- [ ] Persistent Disk montado em `/opt/render/project/src/data`
- [ ] Variáveis de ambiente configuradas (SECRET_KEY, SESSION_SECRET)
- [ ] Senha do admin alterada após primeiro login
- [ ] GEMINI_API_KEY configurado (se usar chatbot)
- [ ] Testado criar pedido → redeploy → dados ainda existem
- [ ] Backup manual configurado (via SSH)
- [ ] Custom domain configurado (opcional)
- [ ] HTTPS funcionando corretamente

---

## 🎉 Pronto!

Seu sistema Meatz Burger está no ar! 🍔

Acesse: `https://meatz-burger.onrender.com` (substitua pelo seu domínio)

**Não esqueça de mudar a senha do admin imediatamente!**
