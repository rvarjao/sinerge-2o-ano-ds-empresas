# Guia de Implementação - PostgreSQL com Separação por Grupo

## Visão Geral

Este guia explica como migrar o sistema de "Diário de Bordo" de uma armazenagem em `localStorage` para um banco de dados PostgreSQL com suporte a múltiplos grupos de alunos.

### Princípios Principais

✅ **Uma única tabela `pessoas`** com `grupo_id` para separar os dados
✅ **Uma única tabela `lancamento_diario`** com `grupo_id` para separar os comentários
✅ **Sem schemas diferentes** (`PUBLIC` schema apenas)
✅ **Sem tabelas duplicadas** com prefixos (`pessoas`, não `grupo_1_pessoas`)
✅ **Validação de grupo** em todas as queries (segurança)
✅ **Índices de performance** para buscas rápidas

---

## 1. Setup do Banco de Dados

### 1.1 Criar Banco PostgreSQL Vazio

```bash
# Conectar ao PostgreSQL (como admin)
psql -U postgres

# Criar banco
CREATE DATABASE sinerge;

# Conectar ao novo banco
\c sinerge

# Copiar o arquivo de schema
```

### 1.2 Executar Script de Schema

```bash
# Via psql (recomendado)
psql -U user -d sinerge -f database_schema.sql

# Ou no PostgreSQL CLI
psql -U postgres
\c sinerge
\i database_schema.sql
```

### 1.3 Verificar Tabelas Criadas

```sql
-- Lista tabelas
\dt

-- Verifica estrutura de uma tabela
\d grupos
\d pessoas
\d lancamento_diario
```

**Saída esperada:**
```
          List of relations
 Schema |       Name       | Type  | Owner
--------+------------------+-------+-------
 public | grupos           | table | user
 public | lancamento_diario | table | user
 public | pessoas          | table | user
 public | pessoas_extras   | table | user
 public | regras_julgamento | table | user
```

---

## 2. Estrutura de Tabelas

### Tabela: `grupos`

```sql
SELECT * FROM grupos;
```

| id | nome | codigo | criado_em | atualizado_em |
|----|------|--------|-----------|---------------|
| 1 | Turma A - 2º Ano ADM | turma-a-2023 | 2024-06-01 10:00:00 | 2024-06-01 10:00:00 |
| 2 | Turma B - 2º Ano ADM | turma-b-2023 | 2024-06-01 10:00:00 | 2024-06-01 10:00:00 |

**Como usar:** Cada grupo tem um `id` que deve ser passado para todas as operações.

### Tabela: `pessoas`

```sql
SELECT * FROM pessoas WHERE grupo_id = 1;
```

| id | grupo_id | nome | idade | cargo | setor | situacao | risco | epi | observacoes | criado_em | atualizado_em |
|----|----------|------|-------|-------|-------|----------|-------|-----|-------------|-----------|---------------|
| 1 | 1 | João Silva | 34 | Operário | Produção | Ativo | Médio | Sim | — | 2024-06-01 | 2024-06-01 |

**Constraints:**
- `grupo_id` é obrigatório (referencia `grupos.id`)
- Deletar grupo deleta automaticamente todas as pessoas do grupo (CASCADE)

### Tabela: `lancamento_diario`

```sql
SELECT * FROM lancamento_diario WHERE grupo_id = 1;
```

| id | grupo_id | pessoa_id | titulo | texto | criado_em | atualizado_em |
|----|----------|-----------|--------|-------|-----------|---------------|
| 1 | 1 | 1 | Entrevista | Entrevista realizada com sucesso... | 2024-06-01 | 2024-06-01 |

**Constraints:**
- `grupo_id` é obrigatório (referencia `grupos.id`)
- `pessoa_id` é opcional (pode ser NULL para lançamentos genéricos)
- Deletar grupo deleta automaticamente todos os lançamentos do grupo

### Tabela: `pessoas_extras`

Para armazenar campos customizáveis (turno, matrícula, etc):

```sql
SELECT * FROM pessoas_extras WHERE pessoa_id = 1;
```

| id | pessoa_id | chave | valor | criado_em |
|----|-----------|-------|-------|-----------|
| 1 | 1 | turno | noturno | 2024-06-01 |
| 2 | 1 | matrícula | 12345 | 2024-06-01 |

### Tabela: `regras_julgamento`

Cada grupo pode ter suas próprias regras de validação:

```sql
SELECT * FROM regras_julgamento WHERE grupo_id = 1;
```

| id | grupo_id | codigo_regras | criado_em | atualizado_em |
|----|----------|---------------|-----------|---------------|
| 1 | 1 | function julgar(e) { ... } | 2024-06-01 | 2024-06-01 |

---

## 3. Documentação da Camada de Dados (`database.js`)

### Imports

```javascript
// No seu arquivo de backend (Node.js/Express)
const db = require('./database.js');
```

### Operações com Grupos

#### Listar todos os grupos

```javascript
const grupos = await db.listarGrupos();
// Retorna: Array de grupos
```

#### Obter grupo por ID

```javascript
const grupo = await db.obterGrupo(1);
// Retorna: { id: 1, nome: "Turma A", codigo: "turma-a-2023", ... }
```

#### Obter grupo por código

```javascript
const grupo = await db.obterGrupoPorCodigo('turma-a-2023');
```

#### Criar novo grupo

```javascript
const novoGrupo = await db.criarGrupo('Turma E', 'turma-e-2023');
// Retorna: { id: 5, nome: "Turma E", ... }
```

---

### Operações com Pessoas

#### Criar pessoa

```javascript
const novaPessoa = await db.criarPessoa(1, {
    nome: "João Silva",
    idade: 34,
    cargo: "Operário",
    setor: "Produção",
    situacao: "Ativo",
    risco: "Médio",
    epi: "Sim",
    observacoes: "Entrevista realizada...",
    extras: {
        turno: "noturno",
        matrícula: "12345"
    }
});
// Retorna: { id: 1, grupo_id: 1, nome: "João Silva", ... }
```

**⚠️ Obrigatório:** Sempre passar `grupo_id` como primeiro parâmetro!

#### Listar pessoas de um grupo

```javascript
// Listar todas
const pessoas = await db.listarPessoas(1);

// Com filtros
const pessoas = await db.listarPessoas(1, {
    nome: "João",       // busca parcial (ILIKE)
    setor: "Produção",  // exato
    situacao: "Ativo",  // exato
    risco: "Médio"      // exato
});
```

#### Obter pessoa específica

```javascript
const pessoa = await db.obterPessoa(1, 1); // id=1, grupo_id=1
// Retorna: { id: 1, grupo_id: 1, nome: "João Silva", ... }
```

#### Obter pessoa com campos extras

```javascript
const pessoaComExtras = await db.obterPessoaComExtras(1, 1);
// Retorna:
// {
//   id: 1,
//   grupo_id: 1,
//   nome: "João Silva",
//   extras: {
//     turno: "noturno",
//     matrícula: "12345"
//   }
// }
```

#### Atualizar pessoa

```javascript
const pessoaAtualizada = await db.atualizarPessoa(1, 1, {
    nome: "João da Silva",
    idade: 35,
    extras: {
        turno: "diurno"
    }
});
// Só atualiza campos fornecidos (merge)
```

#### Deletar pessoa

```javascript
const deletado = await db.deletarPessoa(1, 1); // id=1, grupo_id=1
// Retorna: true se deletado, false se não encontrado
```

**⚠️ Validação Automática:**
- Sempre valida se `pessoa_id` pertence a `grupo_id`
- Nunca permite acessar dados de outro grupo
- Lança erro se grupo ou pessoa não existem

---

### Operações com Lançamentos Diários

#### Criar lançamento

```javascript
const novoLancamento = await db.criarLancamento(1, {
    pessoaId: 1,           // opcional
    titulo: "Entrevista",
    texto: "Conteúdo do lançamento..."
});
// Retorna: { id: 1, grupo_id: 1, pessoa_id: 1, ... }
```

#### Listar lançamentos

```javascript
// De um grupo
const lancamentos = await db.listarLancamentos(1);

// De uma pessoa específica do grupo
const lancamentos = await db.listarLancamentos(1, 5); // grupo_id=1, pessoa_id=5
```

#### Obter lançamento específico

```javascript
const lancamento = await db.obterLancamento(1, 1); // id=1, grupo_id=1
```

#### Atualizar lançamento

```javascript
const lancamentoAtualizado = await db.atualizarLancamento(1, 1, {
    titulo: "Entrevista Atualizada",
    texto: "Novo conteúdo..."
});
```

#### Deletar lançamento

```javascript
const deletado = await db.deletarLancamento(1, 1); // id=1, grupo_id=1
```

---

### Operações com Regras

#### Obter regras de um grupo

```javascript
const regras = await db.obterRegras(1);
// Retorna: código JavaScript como string (ou null se não existem)
```

#### Salvar/atualizar regras

```javascript
const codigoRegras = `
function julgar(e) {
    const v = [];
    if (!e.nome) v.push({ tipo: 'bad', msg: 'Nome não informado' });
    return v;
}
`;

const regrasSalvas = await db.salvarRegras(1, codigoRegras);
// Retorna: { id: 1, grupo_id: 1, codigo_regras: "...", ... }
```

---

## 4. Exemplo Prático: Migração do Diário de Entrevistados

### Antes (localStorage)

```javascript
let comentarios = JSON.parse(localStorage.getItem('forum_comments')) || [];

comentarios.push({
    author: "João",
    text: "Novo comentário",
    date: "01/06/2024 10:00"
});

localStorage.setItem('forum_comments', JSON.stringify(comentarios));
```

### Depois (PostgreSQL)

```javascript
const db = require('./database.js');

// 1. Selecionar grupo (via URL, session, select na interface)
const grupoId = 1; // Obtido de query param ou sessão

// 2. Criar lançamento
const novoLancamento = await db.criarLancamento(grupoId, {
    pessoaId: null,  // ou um ID de pessoa
    titulo: "Novo Comentário",
    texto: "Conteúdo do comentário..."
});

// 3. Listar lançamentos do grupo
const lancamentos = await db.listarLancamentos(grupoId);

// 4. Deletar lançamento
await db.deletarLancamento(novoLancamento.id, grupoId);
```

---

## 5. Segurança & Validação

### Princípios Implementados

✅ **Isolamento de Grupo:** Toda query filtra automaticamente por `grupo_id`
✅ **Validação de Propriedade:** Verifica se recurso pertence ao grupo antes de operar
✅ **Prepared Statements:** Usa placeholders ($1, $2...) contra SQL injection
✅ **Constraints do BD:** Referências com FOREIGN KEY e ON DELETE CASCADE

### Checklist de Segurança

- [ ] Nunca confiar em `grupo_id` enviado pelo cliente sem validação
- [ ] Sempre validar se usuário tem permissão para acessar o grupo
- [ ] Usar sessão ou token para armazenar `grupo_id` do usuário logado
- [ ] Nunca expor `grupo_id` em URLs de produção sem autenticação
- [ ] Log de operações sensíveis (delete, update)

---

## 6. Integração com Interface (Frontend)

### Seletor de Grupo

Adicione um select no topo da página para escolher o grupo:

```html
<select id="grupoSelect" onchange="selecionarGrupo()">
    <option value="">Carregando grupos...</option>
</select>

<script>
async function carregarGrupos() {
    const response = await fetch('/api/grupos');
    const grupos = await response.json();
    
    const select = document.getElementById('grupoSelect');
    select.innerHTML = grupos.map(g => 
        `<option value="${g.id}">${g.nome}</option>`
    ).join('');
}

function selecionarGrupo() {
    const grupoId = document.getElementById('grupoSelect').value;
    localStorage.setItem('grupoAtual', grupoId);
    location.reload(); // Ou renderizar com novo grupoId
}

carregarGrupos();
</script>
```

### Chamadas de API

```javascript
// No seu servidor (Node.js + Express)
const db = require('./database.js');

app.get('/api/grupos', async (req, res) => {
    const grupos = await db.listarGrupos();
    res.json(grupos);
});

app.get('/api/pessoas/:grupoId', async (req, res) => {
    const { grupoId } = req.params;
    const pessoas = await db.listarPessoas(parseInt(grupoId));
    res.json(pessoas);
});

app.post('/api/pessoas/:grupoId', async (req, res) => {
    const { grupoId } = req.params;
    const pessoa = await db.criarPessoa(parseInt(grupoId), req.body);
    res.json(pessoa);
});

app.post('/api/lancamentos/:grupoId', async (req, res) => {
    const { grupoId } = req.params;
    const lancamento = await db.criarLancamento(parseInt(grupoId), req.body);
    res.json(lancamento);
});
```

---

## 7. Testes Manuais

### Script SQL para Testes

```sql
-- 1. Verificar grupos criados
SELECT * FROM grupos;

-- 2. Inserir teste de pessoa
INSERT INTO pessoas (grupo_id, nome, idade, cargo, setor)
VALUES (1, 'Maria Santos', 28, 'Gerente', 'RH');

-- 3. Listar pessoas do grupo 1
SELECT * FROM pessoas WHERE grupo_id = 1;

-- 4. Inserir lançamento
INSERT INTO lancamento_diario (grupo_id, pessoa_id, titulo, texto)
VALUES (1, 1, 'Primeira Entrevista', 'Conteúdo da entrevista...');

-- 5. Verificar isolamento entre grupos
SELECT * FROM pessoas WHERE grupo_id = 1;  -- Grupo 1
SELECT * FROM pessoas WHERE grupo_id = 2;  -- Grupo 2 (separado)

-- 6. Verificar integridade referencial
DELETE FROM grupos WHERE id = 1;  -- Deleta grupo, pessoas e lançamentos em cascade

-- 7. Ver índices criados
SELECT tablename, indexname FROM pg_indexes WHERE schemaname = 'public';
```

---

## 8. Performance

### Índices Criados

```sql
-- Buscar rápido por grupo
CREATE INDEX idx_pessoas_grupo_id ON pessoas(grupo_id);
CREATE INDEX idx_lancamento_grupo_id ON lancamento_diario(grupo_id);

-- Buscar por nome dentro de um grupo
CREATE INDEX idx_pessoas_nome ON pessoas(nome);
CREATE INDEX idx_pessoas_grupo_nome ON pessoas(grupo_id, nome);

-- Buscar lançamentos de uma pessoa em um grupo
CREATE INDEX idx_lancamento_grupo_pessoa ON lancamento_diario(grupo_id, pessoa_id);
```

### Análise de Performance

```sql
EXPLAIN ANALYZE
SELECT * FROM pessoas WHERE grupo_id = 1 AND nome ILIKE '%João%';
```

---

## 9. Monitoramento & Manutenção

### Contar dados por grupo

```sql
SELECT 
    g.id,
    g.nome,
    COUNT(DISTINCT p.id) as pessoas,
    COUNT(DISTINCT ld.id) as lancamentos
FROM grupos g
LEFT JOIN pessoas p ON g.id = p.grupo_id
LEFT JOIN lancamento_diario ld ON g.id = ld.grupo_id
GROUP BY g.id, g.nome;
```

### Limpar dados antigos (exemplo: > 1 ano)

```sql
DELETE FROM lancamento_diario
WHERE criado_em < NOW() - INTERVAL '1 year'
AND grupo_id = $1;
```

---

## 10. Troubleshooting

| Problema | Solução |
|----------|---------|
| "Grupo não existe" | Verificar ID do grupo em `SELECT * FROM grupos` |
| "Pessoa não pertence ao grupo" | Validar `grupo_id` da pessoa: `SELECT grupo_id FROM pessoas WHERE id = X` |
| "Lançamento não encontrado" | Verificar: `SELECT * FROM lancamento_diario WHERE id = X AND grupo_id = Y` |
| Queries lentas | Rodar `ANALYZE` e verificar índices com `EXPLAIN` |
| Acesso negado ao banco | Verificar credenciais em `DATABASE_URL` |

---

## Resumo: Checklist de Implementação

- [ ] Criar banco PostgreSQL `sinerge`
- [ ] Executar `database_schema.sql`
- [ ] Verificar tabelas: `\dt` no psql
- [ ] Implementar servidor backend com `database.js`
- [ ] Criar endpoints `/api/grupos`, `/api/pessoas/:grupoId`, etc.
- [ ] Adicionar seletor de grupo na interface
- [ ] Testar CRUD de pessoas
- [ ] Testar CRUD de lançamentos
- [ ] Testar isolamento entre grupos (grupo 1 não vê dados do grupo 2)
- [ ] Validar segurança (grupo_id sempre filtrado)
- [ ] Deploy em produção

---

**Versão:** 1.0  
**Data:** Junho 2024  
**Mantido por:** Ricardo Varjão
