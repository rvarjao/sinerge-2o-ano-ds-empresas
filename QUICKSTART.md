# ⚡ Quick Start - Implementação em 30 minutos

## Pré-requisitos

- PostgreSQL instalado
- Python 3.8+
- Git

---

## 1️⃣ Banco de Dados (5 min)

```bash
# Criar usuário e banco
sudo -u postgres psql << EOF
CREATE USER sinerge WITH PASSWORD 'senha123';
CREATE DATABASE sinerge OWNER sinerge;
\q
EOF

# Executar schema
psql -U sinerge -d sinerge -f database_schema.sql

# Verificar
psql -U sinerge -d sinerge -c "SELECT * FROM grupos;"
```

✅ Deve listar 4 grupos de exemplo

---

## 2️⃣ Backend (5 min)

```bash
# Copiar configuração
cp .env.example .env

# Editar .env (trocar senha se necessário)
nano .env
# DB_PASSWORD=senha123

# Instalar dependências
pip install -r requirements.txt

# Testar servidor
python server.py
```

✅ Mensagem: "Servidor rodando em http://localhost:3000"

---

## 3️⃣ Testar API (2 min)

Em outro terminal:

```bash
# Listar grupos
curl http://localhost:3000/api/grupos

# Health check
curl http://localhost:3000/health
```

✅ Deve retornar JSON com grupos

---

## 4️⃣ Adaptar Frontend (15 min)

**Arquivo:** `2oANO-ADM/MARKETING/diario-entrevistados.html`

### 4.1 Adicionar Seletor no Header (~linha 475)

Localizar:
```html
<header>
  <h1>Diário de Bordo</h1>
  <span>Controle de Entrevistados</span>
  <div class="header-actions">
```

Trocar por:
```html
<header>
  <h1>Diário de Bordo</h1>
  <span>Controle de Entrevistados</span>
  
  <div style="margin-left: auto; display: flex; gap: 20px; align-items: center;">
    <select id="grupoSelect" onchange="selecionarGrupo()" style="
      background: var(--bg); border: 1px solid var(--border);
      color: var(--text); padding: 10px 14px; border-radius: 2px;
    ">
      <option value="">Carregando grupos...</option>
    </select>
    <div class="header-actions">
```

### 4.2 No Script, Substituir ~3 funções

**Encontrar e DELETAR:**
```javascript
const KEY_DATA  = 'db_entrevistados';
const KEY_RULES = 'db_regras';

function loadData()  { return JSON.parse(localStorage.getItem(KEY_DATA)  || '[]'); }
function saveData(d) { localStorage.setItem(KEY_DATA, JSON.stringify(d)); updateNavCount(); }
```

**Substituir por:**
```javascript
let grupoAtual = null;

async function carregarGrupos() {
    try {
        const response = await fetch('/api/grupos');
        const grupos = await response.json();
        const select = document.getElementById('grupoSelect');
        select.innerHTML = grupos.map(g => `<option value="${g.id}">${g.nome}</option>`).join('');
        if (grupos.length > 0) {
            select.value = grupos[0].id;
            selecionarGrupo();
        }
    } catch (err) {
        console.error('Erro:', err);
        toast('Erro ao carregar grupos');
    }
}

function selecionarGrupo() {
    grupoAtual = parseInt(document.getElementById('grupoSelect').value);
    if (grupoAtual) {
        renderLista();
        renderCategorias();
        updateNavCount();
    }
}

async function loadData() {
    if (!grupoAtual) return [];
    try {
        const response = await fetch(`/api/pessoas/${grupoAtual}`);
        return await response.json();
    } catch (err) {
        console.error('Erro:', err);
        return [];
    }
}
```

### 4.3 Modificar `salvarEntrevistado()` (~linha 782)

**DELETAR:** Todo código que faz `saveData(db)` e array push

**SUBSTITUIR por:**
```javascript
async function salvarEntrevistado() {
  if (!grupoAtual) { toast('Selecione um grupo'); return; }

  const nome  = document.getElementById('f-nome').value.trim();
  const idade = document.getElementById('f-idade').value;
  const cargo = document.getElementById('f-cargo').value.trim();
  const setor = document.getElementById('f-setor').value.trim();
  const data  = document.getElementById('f-data').value;
  const sit   = document.getElementById('f-situacao').value;
  const risco = document.getElementById('f-risco').value;
  const epi   = document.getElementById('f-epi').value;
  const obs   = document.getElementById('f-obs').value.trim();
  const extraRaw = document.getElementById('f-extra').value.trim();
  const editId = document.getElementById('f-editId').value;

  if (!nome) { toast('Nome é obrigatório'); return; }

  const extras = {};
  if (extraRaw) {
    extraRaw.split(',').forEach(p => {
      const [k, ...v] = p.split(':');
      if (k && v.length) extras[k.trim().toLowerCase()] = v.join(':').trim();
    });
  }

  const dados = { nome, idade, cargo, setor, data, situacao: sit, risco, epi, observacoes: obs, extras };

  try {
    if (editId) {
      const response = await fetch(`/api/pessoas/${grupoAtual}/${editId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      });
      if (!response.ok) throw new Error('Erro ao atualizar');
      toast('Entrevistado atualizado!');
    } else {
      const response = await fetch(`/api/pessoas/${grupoAtual}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      });
      if (!response.ok) throw new Error('Erro ao salvar');
      toast('Entrevistado cadastrado!');
    }
    limparForm();
    renderLista();
  } catch (err) {
    toast(`Erro: ${err.message}`);
  }
}
```

### 4.4 Modificar `deletarEntrevistado()` (~linha 1085)

**Trocar por:**
```javascript
async function deletarEntrevistado(id) {
  if (!grupoAtual) return;
  if (!confirm('Tem certeza que deseja excluir?')) return;

  try {
    const response = await fetch(`/api/pessoas/${grupoAtual}/${id}`, {
      method: 'DELETE'
    });
    if (!response.ok) throw new Error('Erro ao deletar');
    renderLista();
    toast('Entrevistado removido.');
  } catch (err) {
    toast(`Erro: ${err.message}`);
  }
}
```

### 4.5 Modificar `editarEntrevistado()` (~linha 1066)

**Trocar por:**
```javascript
async function editarEntrevistado(id) {
  if (!grupoAtual) return;

  try {
    const response = await fetch(`/api/pessoas/${grupoAtual}/${id}`);
    if (!response.ok) throw new Error('Erro ao carregar');
    const e = await response.json();

    document.getElementById('f-nome').value = e.nome || '';
    document.getElementById('f-idade').value = e.idade || '';
    document.getElementById('f-cargo').value = e.cargo || '';
    document.getElementById('f-setor').value = e.setor || '';
    document.getElementById('f-data').value = e.data || '';
    document.getElementById('f-situacao').value = e.situacao || '';
    document.getElementById('f-risco').value = e.risco || '';
    document.getElementById('f-epi').value = e.epi || '';
    document.getElementById('f-obs').value = e.observacoes || '';
    if (e.extras) {
      document.getElementById('f-extra').value = Object.entries(e.extras)
        .map(([k,v]) => `${k}: ${v}`).join(', ');
    }
    document.getElementById('f-editId').value = e.id;
    document.getElementById('formTitle').textContent = 'Editar: ' + e.nome;
    showTab('cadastro');
    window.scrollTo(0, 0);
  } catch (err) {
    toast(`Erro: ${err.message}`);
  }
}
```

### 4.6 Adicionar Inicialização (~final do script, linha ~1145)

**Trocar:**
```javascript
// INIT
updateNavCount();
```

**Por:**
```javascript
// INIT
document.addEventListener('DOMContentLoaded', async () => {
  await carregarGrupos();
  updateNavCount();
});
```

---

## 5️⃣ Testar Frontend (3 min)

1. Abrir navegador em `file:///path/to/diario-entrevistados.html`
   OU servir com um servidor simples:
   ```bash
   cd 2oANO-ADM/MARKETING
   python -m http.server 8000
   # Abrir http://localhost:8000/diario-entrevistados.html
   ```

2. Seletor de grupo deve aparecer
3. Clicar em "Novo Entrevistado"
4. Preencher formulário e salvar
5. Verificar que dados aparecem na tabela
6. Trocar de grupo → dados mudam

✅ Pronto!

---

## ⚠️ Troubleshooting Rápido

| Problema | Solução |
|----------|---------|
| "Erro de conexão" | Verificar if PostgreSQL rodando: `sudo systemctl status postgresql` |
| "Porta 3000 em uso" | `lsof -i :3000` e `kill -9 <PID>` ou usar `PORT=3001 python server.py` |
| "ModuleNotFoundError" | `pip install -r requirements.txt` |
| Select vazio | Verificar console (F12) do navegador para erros |
| Dados não salvam | Verificar se servidor está rodando (`curl http://localhost:3000/health`) |

---

## 📚 Próximos Passos

Para mais detalhes:

- **Estrutura de BD:** `DATABASE_GUIDE.md`
- **Migração completa:** `MIGRATION_EXAMPLE.md`
- **Checklist detalhado:** `IMPLEMENTATION_CHECKLIST.md`
- **README geral:** `README_POSTGRES.md`

---

**Tempo total estimado:** 30 minutos ⏱️

**Status:** ✅ Sistema funcional com PostgreSQL

