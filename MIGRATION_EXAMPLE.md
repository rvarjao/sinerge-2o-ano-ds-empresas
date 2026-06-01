# Exemplo Prático: Migração do Diário de Entrevistados para PostgreSQL

## Visão Geral

Aqui mostramos como adaptar o arquivo `diario-entrevistados.html` de `localStorage` para usar a API PostgreSQL.

---

## Passo 1: Adicionar Seletor de Grupo

### HTML: Adicionar Select no Header

**Arquivo:** `2oANO-ADM/MARKETING/diario-entrevistados.html`

Localizar a seção `<header>` (linha ~469) e adicionar o seletor:

```html
<header>
  <h1>Diário de Bordo</h1>
  <span>Controle de Entrevistados</span>
  
  <!-- NOVO: Seletor de Grupo -->
  <div style="margin-left: auto; display: flex; gap: 20px; align-items: center;">
    <select id="grupoSelect" onchange="selecionarGrupo()" style="
      background: var(--bg);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 10px 14px;
      border-radius: 2px;
      font-family: var(--sans);
      font-size: 13px;
    ">
      <option value="">Carregando grupos...</option>
    </select>
    
    <div class="header-actions">
      <button class="btn btn-secondary" onclick="exportJSON()">↓ Exportar JSON</button>
      <button class="btn btn-primary" onclick="showTab('cadastro')">+ Novo Entrevistado</button>
    </div>
  </div>
</header>
```

---

## Passo 2: Adaptar o JavaScript

### Seção 1: Variáveis Globais

**Antes (localStorage):**

```javascript
const KEY_DATA  = 'db_entrevistados';
const KEY_RULES = 'db_regras';

function loadData()  { return JSON.parse(localStorage.getItem(KEY_DATA)  || '[]'); }
function saveData(d) { localStorage.setItem(KEY_DATA, JSON.stringify(d)); updateNavCount(); }
```

**Depois (PostgreSQL):**

```javascript
// Variável global para armazenar o grupo atual
let grupoAtual = null;

// Funções para chamadas de API
async function loadData() {
    if (!grupoAtual) {
        console.warn('Nenhum grupo selecionado');
        return [];
    }
    try {
        const response = await fetch(`/api/pessoas/${grupoAtual}`);
        return await response.json();
    } catch (err) {
        console.error('Erro ao carregar dados:', err);
        return [];
    }
}

async function saveData(d) {
    // Nota: saveData é descontinuado. Use criarPessoa() ou atualizarPessoa()
    console.warn('Use criarPessoa() ou atualizarPessoa()');
}

// Carregar grupos no select
async function carregarGrupos() {
    try {
        const response = await fetch('/api/grupos');
        const grupos = await response.json();
        
        const select = document.getElementById('grupoSelect');
        select.innerHTML = grupos.map(g => 
            `<option value="${g.id}">${g.nome} (${g.codigo})</option>`
        ).join('');
        
        // Selecionar o primeiro grupo por padrão
        if (grupos.length > 0) {
            select.value = grupos[0].id;
            selecionarGrupo();
        }
    } catch (err) {
        console.error('Erro ao carregar grupos:', err);
    }
}

function selecionarGrupo() {
    grupoAtual = parseInt(document.getElementById('grupoSelect').value);
    if (grupoAtual) {
        renderLista();
        renderCategorias();
        updateNavCount();
        toast(`Grupo ${grupoAtual} selecionado`);
    }
}
```

---

### Seção 2: Função `salvarEntrevistado()`

**Antes (localStorage):**

```javascript
function salvarEntrevistado() {
  const nome  = document.getElementById('f-nome').value.trim();
  const idade = document.getElementById('f-idade').value;
  // ... mais campos ...
  const editId = document.getElementById('f-editId').value;

  if (!nome) { toast('Nome é obrigatório'); return; }

  const extra = {};
  if (extraRaw) {
    extraRaw.split(',').forEach(p => {
      const [k, ...v] = p.split(':');
      if (k && v.length) extra[k.trim().toLowerCase()] = v.join(':').trim();
    });
  }

  const db = loadData();
  if (editId) {
    const idx = db.findIndex(x => x.id === editId);
    if (idx >= 0) {
      db[idx] = { ...db[idx], nome, idade, cargo, setor, data, situacao: sit, risco, epi, obs, extra };
      saveData(db);
      toast('Entrevistado atualizado!');
    }
  } else {
    db.push({
      id: Date.now().toString(),
      nome, idade, cargo, setor, data,
      situacao: sit, risco, epi, obs, extra,
      criadoEm: new Date().toISOString()
    });
    saveData(db);
    toast('Entrevistado cadastrado!');
  }
  limparForm();
}
```

**Depois (PostgreSQL):**

```javascript
async function salvarEntrevistado() {
  if (!grupoAtual) {
    toast('Selecione um grupo primeiro');
    return;
  }

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
  const editId   = document.getElementById('f-editId').value;

  if (!nome) { toast('Nome é obrigatório'); return; }

  // Parse campos extras
  const extras = {};
  if (extraRaw) {
    extraRaw.split(',').forEach(p => {
      const [k, ...v] = p.split(':');
      if (k && v.length) extras[k.trim().toLowerCase()] = v.join(':').trim();
    });
  }

  const dados = {
    nome, idade, cargo, setor, data,
    situacao: sit, risco, epi, observacoes: obs, extras
  };

  try {
    if (editId) {
      // Atualizar pessoa existente
      const response = await fetch(`/api/pessoas/${grupoAtual}/${editId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(dados)
      });
      if (!response.ok) throw new Error('Erro ao atualizar');
      toast('Entrevistado atualizado!');
    } else {
      // Criar nova pessoa
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
    renderCategorias();
  } catch (err) {
    toast(`Erro: ${err.message}`);
    console.error(err);
  }
}
```

---

### Seção 3: Função `renderLista()`

**Antes (localStorage):**

```javascript
function renderLista() {
  const db    = loadData();
  const q     = (document.getElementById('searchInput').value || '').toLowerCase();
  const fStat = document.getElementById('filterStatus').value;

  let filtered = db.filter(e => {
    const match = [e.nome, e.cargo, e.setor, e.situacao].join(' ').toLowerCase().includes(q);
    if (!match) return false;
    if (fStat) {
      const v = executarJulgamento(e);
      if (statusGeral(v) !== fStat) return false;
    }
    return true;
  });
  // ... renderizar ...
}
```

**Depois (PostgreSQL):**

```javascript
async function renderLista() {
  if (!grupoAtual) {
    document.getElementById('listaBody').innerHTML = '';
    return;
  }

  try {
    const db = await loadData(); // Fetch da API
    const q     = (document.getElementById('searchInput').value || '').toLowerCase();
    const fStat = document.getElementById('filterStatus').value;

    let filtered = db.filter(e => {
      const match = [e.nome, e.cargo, e.setor, e.situacao]
        .join(' ')
        .toLowerCase()
        .includes(q);
      if (!match) return false;
      if (fStat) {
        const v = executarJulgamento(e);
        if (statusGeral(v) !== fStat) return false;
      }
      return true;
    });

    document.getElementById('listCount').textContent = db.length;
    const tbody = document.getElementById('listaBody');
    document.getElementById('emptyList').style.display = 
      filtered.length === 0 ? 'block' : 'none';

    tbody.innerHTML = filtered.map(e => {
      const v = executarJulgamento(e);
      const s = statusGeral(v);
      const riscoPill = e.risco ?
        `<span class="pill ${e.risco==='Alto'||e.risco==='Crítico'?'pill-bad':e.risco==='Médio'?'pill-warn':'pill-ok'}">${e.risco}</span>` : '—';
      return `<tr>
        <td><a href="#" onclick="abrirModal('${e.id}');return false;" style="color:var(--accent);text-decoration:none;">${e.nome||'—'}</a></td>
        <td>${e.idade||'—'}</td>
        <td>${e.cargo||'—'}</td>
        <td>${e.setor||'—'}</td>
        <td style="font-family:var(--mono);font-size:11px;">${formatDate(e.data)}</td>
        <td>${e.situacao||'—'}</td>
        <td>${riscoPill}</td>
        <td>${statusLabel(s)}</td>
        <td>
          <button class="btn btn-ok" onclick="editarEntrevistado('${e.id}')">Editar</button>
          <button class="btn btn-danger" style="margin-left:4px" onclick="deletarEntrevistado('${e.id}')">Del</button>
        </td>
      </tr>`;
    }).join('');
  } catch (err) {
    toast(`Erro ao carregar lista: ${err.message}`);
    console.error(err);
  }
}
```

---

### Seção 4: Funções `deletarEntrevistado()`

**Antes (localStorage):**

```javascript
function deletarEntrevistado(id) {
  if (!confirm('Tem certeza que deseja excluir?')) return;
  const db = loadData().filter(x => x.id !== id);
  saveData(db);
  renderLista();
  toast('Entrevistado removido.');
}
```

**Depois (PostgreSQL):**

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
    console.error(err);
  }
}
```

---

### Seção 5: Função `editarEntrevistado()`

**Antes (localStorage):**

```javascript
function editarEntrevistado(id) {
  const e = loadData().find(x => x.id === id);
  if (!e) return;
  document.getElementById('f-nome').value     = e.nome    || '';
  // ... mais campos ...
  document.getElementById('f-editId').value   = e.id;
  showTab('cadastro');
}
```

**Depois (PostgreSQL):**

```javascript
async function editarEntrevistado(id) {
  if (!grupoAtual) return;

  try {
    const response = await fetch(`/api/pessoas/${grupoAtual}/${id}`);
    if (!response.ok) throw new Error('Erro ao carregar');
    const e = await response.json();

    document.getElementById('f-nome').value     = e.nome    || '';
    document.getElementById('f-idade').value    = e.idade   || '';
    document.getElementById('f-cargo').value    = e.cargo   || '';
    document.getElementById('f-setor').value    = e.setor   || '';
    document.getElementById('f-data').value     = e.data    || '';
    document.getElementById('f-situacao').value = e.situacao || '';
    document.getElementById('f-risco').value    = e.risco   || '';
    document.getElementById('f-epi').value      = e.epi     || '';
    document.getElementById('f-obs').value      = e.observacoes || '';
    
    // Carregar extras se existem
    if (e.extras) {
      const extraStr = Object.entries(e.extras)
        .map(([k, v]) => `${k}: ${v}`)
        .join(', ');
      document.getElementById('f-extra').value = extraStr;
    }
    
    document.getElementById('f-editId').value   = e.id;
    document.getElementById('formTitle').textContent = 'Editar: ' + e.nome;
    showTab('cadastro');
    window.scrollTo(0, 0);
  } catch (err) {
    toast(`Erro: ${err.message}`);
    console.error(err);
  }
}
```

---

### Seção 6: Função `obterRegras()` e `salvarRegras()`

**Antes (localStorage):**

```javascript
function loadRules() {
  return localStorage.getItem(KEY_RULES) || DEFAULT_RULES;
}
function saveRulesStr(str) {
  localStorage.setItem(KEY_RULES, str);
}
```

**Depois (PostgreSQL):**

```javascript
async function loadRules() {
  if (!grupoAtual) return DEFAULT_RULES;
  
  try {
    const response = await fetch(`/api/regras/${grupoAtual}`);
    const data = await response.json();
    return data.regras || DEFAULT_RULES;
  } catch (err) {
    console.warn('Usando regras padrão:', err);
    return DEFAULT_RULES;
  }
}

async function salvarRegras() {
  if (!grupoAtual) {
    toast('Selecione um grupo primeiro');
    return;
  }

  const codigoRegras = document.getElementById('rulesEditor').value;

  try {
    const response = await fetch(`/api/regras/${grupoAtual}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ regras: codigoRegras })
    });
    if (!response.ok) throw new Error('Erro ao salvar');
    toast('Regras salvas!');
  } catch (err) {
    toast(`Erro: ${err.message}`);
    console.error(err);
  }
}

async function carregarRulesEditor() {
  const regras = await loadRules();
  document.getElementById('rulesEditor').value = regras;
}
```

---

### Seção 7: INIT (carregar dados ao abrir página)

**Antes (localStorage):**

```javascript
// INIT
updateNavCount();
```

**Depois (PostgreSQL):**

```javascript
// INIT
async function initPage() {
  await carregarGrupos();
  updateNavCount();
}

document.addEventListener('DOMContentLoaded', initPage);
```

---

## Passo 3: Endpoints Backend (Node.js + Express)

Crie um arquivo `server.js` com os seguintes endpoints:

```javascript
const express = require('express');
const db = require('./database.js');

const app = express();
app.use(express.json());

// =====================================================
// GRUPOS
// =====================================================

app.get('/api/grupos', async (req, res) => {
  try {
    const grupos = await db.listarGrupos();
    res.json(grupos);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// =====================================================
// PESSOAS
// =====================================================

app.get('/api/pessoas/:grupoId', async (req, res) => {
  try {
    const { grupoId } = req.params;
    const pessoas = await db.listarPessoas(parseInt(grupoId));
    
    // Carregar extras para cada pessoa
    const pessoasComExtras = await Promise.all(
      pessoas.map(p => db.obterPessoaComExtras(p.id, parseInt(grupoId)))
    );
    
    res.json(pessoasComExtras);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.get('/api/pessoas/:grupoId/:id', async (req, res) => {
  try {
    const { grupoId, id } = req.params;
    const pessoa = await db.obterPessoaComExtras(parseInt(id), parseInt(grupoId));
    if (!pessoa) {
      return res.status(404).json({ error: 'Pessoa não encontrada' });
    }
    res.json(pessoa);
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/pessoas/:grupoId', async (req, res) => {
  try {
    const { grupoId } = req.params;
    const pessoa = await db.criarPessoa(parseInt(grupoId), req.body);
    res.status(201).json(pessoa);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.put('/api/pessoas/:grupoId/:id', async (req, res) => {
  try {
    const { grupoId, id } = req.params;
    const pessoa = await db.atualizarPessoa(parseInt(id), parseInt(grupoId), req.body);
    res.json(pessoa);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

app.delete('/api/pessoas/:grupoId/:id', async (req, res) => {
  try {
    const { grupoId, id } = req.params;
    const deletado = await db.deletarPessoa(parseInt(id), parseInt(grupoId));
    if (!deletado) {
      return res.status(404).json({ error: 'Pessoa não encontrada' });
    }
    res.json({ success: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

// =====================================================
// REGRAS
// =====================================================

app.get('/api/regras/:grupoId', async (req, res) => {
  try {
    const { grupoId } = req.params;
    const regras = await db.obterRegras(parseInt(grupoId));
    res.json({ regras: regras || '' });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/regras/:grupoId', async (req, res) => {
  try {
    const { grupoId } = req.params;
    const { regras } = req.body;
    const resultado = await db.salvarRegras(parseInt(grupoId), regras);
    res.json(resultado);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// =====================================================
// Iniciar servidor
// =====================================================

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  console.log(`Servidor rodando em http://localhost:${PORT}`);
});
```

---

## Resumo das Mudanças

| Operação | Antes | Depois |
|----------|-------|--------|
| Carregar pessoas | `loadData()` local | `fetch('/api/pessoas/:grupoId')` |
| Salvar pessoa | `saveData(db)` | `fetch('/api/pessoas/:grupoId', POST)` |
| Atualizar pessoa | Buscar em array | `fetch('/api/pessoas/:grupoId/:id', PUT)` |
| Deletar pessoa | Filtrar array | `fetch('/api/pessoas/:grupoId/:id', DELETE)` |
| Selecionar grupo | Fixo/URL | Select dropdown com `selecionarGrupo()` |
| Regras | `localStorage` | `fetch('/api/regras/:grupoId')` |
| Isolamento | Nenhum | Automático (filtro `grupo_id`) |

---

**Próximos Passos:**
1. Implementar endpoints no backend
2. Testar com Postman ou curl
3. Ajustar errors handling conforme necessário
4. Deploy com PostgreSQL real
