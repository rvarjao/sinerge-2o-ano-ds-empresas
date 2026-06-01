# Sinerge - Sistema de Simulação Empresarial com PostgreSQL

## 📋 Visão Geral

Este projeto migra o sistema "Diário de Bordo" de **localStorage** para um **banco de dados PostgreSQL** com suporte a **múltiplos grupos de alunos**.

### Arquitetura

```
Frontend (HTML/JavaScript)
         ↓ (Fetch API)
Backend (Python + Flask)
         ↓ (psycopg2)
PostgreSQL Database
```

### Princípios

✅ **Uma única tabela** `pessoas` com `grupo_id` (sem tabelas duplicadas)  
✅ **Uma única tabela** `lancamento_diario` com `grupo_id` (sem schemas por grupo)  
✅ **Isolamento automático** de dados entre grupos  
✅ **Segurança** validada em todas as operações  
✅ **Performance** otimizada com índices apropriados  

---

## 📁 Estrutura de Arquivos

```
sinerge-2o-ano-ds-empresas/
├── database_schema.sql                 # Schema PostgreSQL com todas as tabelas
├── server.py                           # Backend Flask em Python
├── requirements.txt                    # Dependências Python
├── .env.example                        # Template de configuração
├── package.json                        # (Legado Node.js - ignorar)
├── server.js                           # (Legado Node.js - ignorar)
├── DATABASE_GUIDE.md                   # Guia detalhado de operações com BD
├── MIGRATION_EXAMPLE.md                # Exemplo prático de como adaptar o frontend
├── IMPLEMENTATION_CHECKLIST.md         # Checklist completo de implementação
├── README_POSTGRES.md                  # Este arquivo
└── 2oANO-ADM/
    ├── MARKETING/
    │   └── diario-entrevistados.html  # Frontend principal (a adaptar)
    ├── FINANCEIRO/
    ├── PRODUCAO/
    └── RH/
```

---

## 🚀 Quick Start (5 minutos)

### 1. Criar Banco de Dados

```bash
# Conectar como admin
sudo -u postgres psql

# Dentro do psql
CREATE USER sinerge WITH PASSWORD 'sua_senha';
CREATE DATABASE sinerge OWNER sinerge;
\q
```

### 2. Executar Schema

```bash
psql -U sinerge -d sinerge -f database_schema.sql
```

### 3. Instalar Dependências Python

```bash
pip install -r requirements.txt
```

### 4. Configurar .env

```bash
cp .env.example .env
# Editar .env com suas credenciais PostgreSQL
```

### 5. Iniciar Servidor

```bash
python server.py
```

Pronto! Servidor rodando em `http://localhost:3000`

---

## 📊 Modelo de Dados

### Tabelas Principais

#### `grupos`
```sql
id       | nome                    | codigo           | criado_em
---------|-------------------------|------------------|------------------
1        | Turma A - 2º Ano ADM    | turma-a-2023     | 2024-06-01 10:00
2        | Turma B - 2º Ano ADM    | turma-b-2023     | 2024-06-01 10:00
```

#### `pessoas`
```sql
id | grupo_id | nome         | idade | cargo    | setor      | situacao | risco | epi | observacoes | criado_em
---|----------|--------------|-------|----------|------------|----------|-------|-----|-------------|-----------
1  | 1        | João Silva   | 34    | Operário | Produção   | Ativo    | Médio | Sim | ...         | 2024-06-01
2  | 1        | Maria Santos | 28    | Gerente  | RH         | Ativo    | Baixo | Sim | ...         | 2024-06-01
```

#### `lancamento_diario`
```sql
id | grupo_id | pessoa_id | titulo       | texto                 | criado_em
---|----------|-----------|--------------|--------------------|-----------
1  | 1        | 1         | Entrevista   | Entrevista realizada | 2024-06-01
2  | 1        | 2         | Observação   | Nota importante      | 2024-06-01
```

#### `pessoas_extras` (campos customizáveis)
```sql
id | pessoa_id | chave      | valor   | criado_em
---|-----------|------------|---------|----------
1  | 1         | turno      | noturno | 2024-06-01
2  | 1         | matrícula  | 12345   | 2024-06-01
```

#### `regras_julgamento` (por grupo)
```sql
id | grupo_id | codigo_regras                      | criado_em
---|----------|------------------------------------|-----------
1  | 1        | function julgar(e) { ... }        | 2024-06-01
2  | 2        | function julgar(e) { ... }        | 2024-06-01
```

---

## 🔌 API Endpoints

### Grupos

```
GET    /api/grupos              → Lista todos os grupos
GET    /api/grupos/:id          → Obtém um grupo
POST   /api/grupos              → Cria novo grupo
```

### Pessoas

```
GET    /api/pessoas/:grupoId                → Lista pessoas do grupo
GET    /api/pessoas/:grupoId/:id            → Obtém uma pessoa
POST   /api/pessoas/:grupoId                → Cria nova pessoa
PUT    /api/pessoas/:grupoId/:id            → Atualiza pessoa
DELETE /api/pessoas/:grupoId/:id            → Deleta pessoa
```

### Lançamentos Diários

```
GET    /api/lancamentos/:grupoId             → Lista lançamentos do grupo
GET    /api/lancamentos/:grupoId/:id         → Obtém um lançamento
POST   /api/lancamentos/:grupoId             → Cria novo lançamento
DELETE /api/lancamentos/:grupoId/:id         → Deleta lançamento
```

### Regras

```
GET    /api/regras/:grupoId     → Obtém regras do grupo
POST   /api/regras/:grupoId     → Salva/atualiza regras
```

### Health

```
GET    /health                   → Verifica saúde do servidor
```

---

## 💻 Como Adaptar o Frontend

### Passo 1: Adicionar Seletor de Grupo

No header de `diario-entrevistados.html`, adicione:

```html
<select id="grupoSelect" onchange="selecionarGrupo()">
    <option value="">Carregando grupos...</option>
</select>
```

### Passo 2: Adicionar Variável Global

No início do `<script>`:

```javascript
let grupoAtual = null;
```

### Passo 3: Implementar Funções

```javascript
async function carregarGrupos() {
    const response = await fetch('/api/grupos');
    const grupos = await response.json();
    
    const select = document.getElementById('grupoSelect');
    select.innerHTML = grupos.map(g => 
        `<option value="${g.id}">${g.nome}</option>`
    ).join('');
    
    if (grupos.length > 0) {
        select.value = grupos[0].id;
        selecionarGrupo();
    }
}

function selecionarGrupo() {
    grupoAtual = parseInt(document.getElementById('grupoSelect').value);
    if (grupoAtual) {
        renderLista();
        updateNavCount();
    }
}
```

### Passo 4: Mudar `loadData()` para API

**Antes:**
```javascript
function loadData() { 
    return JSON.parse(localStorage.getItem('db_entrevistados') || '[]'); 
}
```

**Depois:**
```javascript
async function loadData() {
    if (!grupoAtual) return [];
    const response = await fetch(`/api/pessoas/${grupoAtual}`);
    return await response.json();
}
```

### Passo 5: Mudar `salvarEntrevistado()` para POST

**Antes:**
```javascript
const db = loadData();
db.push({ nome, idade, ... });
saveData(db);
```

**Depois:**
```javascript
const response = await fetch(`/api/pessoas/${grupoAtual}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nome, idade, ... })
});
const pessoa = await response.json();
```

### Passo 6: Inicializar Página

No final do script:

```javascript
document.addEventListener('DOMContentLoaded', async () => {
    await carregarGrupos();
    updateNavCount();
});
```

📚 **Veja `MIGRATION_EXAMPLE.md` para detalhes completos!**

---

## ✅ Checklist de Implementação

### Banco de Dados
- [ ] PostgreSQL instalado
- [ ] Banco `sinerge` criado
- [ ] Schema executado: `database_schema.sql`
- [ ] Grupos de exemplo inseridos

### Backend Python
- [ ] `server.py` configurado
- [ ] `requirements.txt` instalado
- [ ] `.env` criado com credenciais
- [ ] Servidor inicia sem erros

### Frontend
- [ ] Seletor de grupo adicionado
- [ ] `loadData()` modificada para API
- [ ] `salvarEntrevistado()` modificada para POST
- [ ] Página inicializa com `carregarGrupos()`
- [ ] Testes manuais passam

### Validação
- [ ] Cada grupo vê apenas seus dados
- [ ] Dados persistem entre requisições
- [ ] Sem erros de conexão

📋 **Veja `IMPLEMENTATION_CHECKLIST.md` para lista completa!**

---

## 🧪 Testes Manuais

### 1. Testar Seletor de Grupo
```bash
curl http://localhost:3000/api/grupos
# Deve retornar 4 grupos
```

### 2. Testar Criar Pessoa
```bash
curl -X POST http://localhost:3000/api/pessoas/1 \
  -H "Content-Type: application/json" \
  -d '{"nome":"João","idade":34,"cargo":"Operário"}'
```

### 3. Testar Isolamento entre Grupos
```bash
# Grupo 1
curl http://localhost:3000/api/pessoas/1

# Grupo 2 (dados separados)
curl http://localhost:3000/api/pessoas/2
```

### 4. Testar Deleção
```bash
curl -X DELETE http://localhost:3000/api/pessoas/1/1
```

---

## 🔒 Segurança

### Implementado

✅ Prepared statements (contra SQL injection)  
✅ Validação de `grupo_id` em todas as operações  
✅ Isolamento automático entre grupos  
✅ Sem permissão para acessar dados de outro grupo  
✅ CORS configurado  

### Recomendações

- [ ] Usar HTTPS em produção
- [ ] Autenticação/login por grupo
- [ ] Rate limiting para APIs
- [ ] Logs de auditoria para operações sensíveis

---

## 📈 Performance

### Índices Criados

```sql
CREATE INDEX idx_pessoas_grupo_id ON pessoas(grupo_id);
CREATE INDEX idx_pessoas_nome ON pessoas(nome);
CREATE INDEX idx_lancamento_grupo_id ON lancamento_diario(grupo_id);
```

### Otimizações

- Queries usar índices (não table scans)
- Foreign keys com ON DELETE CASCADE
- Campos extras em tabela separada (normalizado)

### Monitorar

```bash
# Ver plano de execução
psql -U sinerge -d sinerge
EXPLAIN ANALYZE SELECT * FROM pessoas WHERE grupo_id = 1;
```

---

## 🐛 Troubleshooting

### Erro: "Porta 3000 já está em uso"
```bash
# Encontrar processo
lsof -i :3000

# Matar processo
kill -9 <PID>

# Ou usar outra porta
PORT=3001 python server.py
```

### Erro: "Erro de conexão com banco"
```bash
# Verificar se PostgreSQL está rodando
sudo systemctl status postgresql

# Verificar credenciais em .env
cat .env

# Testar conexão manualmente
psql -U sinerge -d sinerge -h localhost
```

### Erro: "ModuleNotFoundError: No module named 'flask'"
```bash
# Instalar dependências
pip install -r requirements.txt

# Ou em ambiente virtual
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Grupo não aparece no select
- Verificar se servidor está rodando: `curl http://localhost:3000/health`
- Verificar se banco tem grupos: `psql -U sinerge -d sinerge -c "SELECT * FROM grupos"`
- Verificar console do navegador (F12) para erros de JavaScript

---

## 📚 Documentação

| Arquivo | Descrição |
|---------|-----------|
| `DATABASE_GUIDE.md` | Guia detalhado de operações com BD e estrutura |
| `MIGRATION_EXAMPLE.md` | Exemplo prático de migração do frontend |
| `IMPLEMENTATION_CHECKLIST.md` | Checklist completo de implementação |
| `server.py` | Servidor Flask com todos os endpoints |
| `database_schema.sql` | Schema PostgreSQL com todas as tabelas |

---

## 🚀 Deploy em Produção

### Preparação

```bash
# Criar ambiente virtual
python -m venv venv_prod
source venv_prod/bin/activate
pip install -r requirements.txt

# Configurar .env com credenciais seguras
cp .env.example .env
# Editar .env com dados reais

# Iniciar servidor em background
nohup python server.py > server.log 2>&1 &
```

### Com Gunicorn (WSGI)

```bash
pip install gunicorn

# Iniciar com 4 workers
gunicorn -w 4 -b 0.0.0.0:3000 server:app
```

### Com Supervisor (systemd)

```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/sinerge.service

[Unit]
Description=Sinerge Backend
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/sinerge-2o-ano-ds-empresas
ExecStart=/usr/bin/python server.py
Restart=always

[Install]
WantedBy=multi-user.target

# Ativar serviço
sudo systemctl daemon-reload
sudo systemctl enable sinerge
sudo systemctl start sinerge
```

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Consulte `DATABASE_GUIDE.md` para operações específicas
2. Verifique `IMPLEMENTATION_CHECKLIST.md` para implementação
3. Veja `MIGRATION_EXAMPLE.md` para adaptar frontend
4. Revise arquivo `server.py` para entender endpoints

---

## 📝 Licença

MIT - Livre para uso educacional e comercial

---

## 👤 Autor

Ricardo Varjão - Sistema de Simulação Empresarial Sinerge

**Versão:** 2.0 (Python + PostgreSQL)  
**Data:** Junho 2024

