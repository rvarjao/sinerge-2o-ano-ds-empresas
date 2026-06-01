# Checklist Completo de Implementação - PostgreSQL + Múltiplos Grupos

## 📋 Visão Geral

Este checklist acompanha a migração do sistema "Diário de Bordo" de `localStorage` para PostgreSQL com suporte a múltiplos grupos de alunos.

---

## Fase 1: Preparação do Banco de Dados

### 1.1 Instalação do PostgreSQL

- [ ] PostgreSQL instalado no servidor ou máquina local
- [ ] Versão >= 12 confirmada: `psql --version`
- [ ] Serviço PostgreSQL ativo: `sudo systemctl status postgresql`

**Instalação (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
```

### 1.2 Criar Banco de Dados

```bash
# Conectar como admin
sudo -u postgres psql

# Criar usuário e banco
CREATE USER sinerge WITH PASSWORD 'sua_senha_segura';
CREATE DATABASE sinerge OWNER sinerge;
ALTER ROLE sinerge WITH CREATEDB;

# Sair
\q
```

- [ ] Usuário `sinerge` criado
- [ ] Banco `sinerge` criado
- [ ] Permissões concedidas

### 1.3 Executar Schema do Banco

```bash
# Via psql (melhor opção)
psql -U sinerge -d sinerge -f database_schema.sql

# Ou manualmente
psql -U sinerge
\c sinerge
\i database_schema.sql
```

- [ ] Arquivo `database_schema.sql` copiado para o diretório do projeto
- [ ] Script executado sem erros
- [ ] Tabelas criadas: `grupos`, `pessoas`, `lancamento_diario`, `pessoas_extras`, `regras_julgamento`
- [ ] Índices criados
- [ ] Dados iniciais (4 grupos de exemplo) inseridos

### 1.4 Verificar Instalação

```sql
-- Conectar ao banco
psql -U sinerge -d sinerge

-- Listar tabelas
\dt

-- Verificar grupos inseridos
SELECT * FROM grupos;

-- Sair
\q
```

- [ ] Todas as 5 tabelas aparecem com `\dt`
- [ ] 4 grupos aparecem com `SELECT * FROM grupos`
- [ ] Índices listados com `\di`

---

## Fase 2: Preparação do Backend (Python + Flask)

### 2.1 Instalação de Dependências

```bash
# No diretório do projeto
pip install -r requirements.txt

# Verificar instalação
pip list

# Dependências esperadas:
# - Flask
# - Flask-CORS
# - psycopg2-binary
# - python-dotenv
```

- [ ] Python >= 3.8 instalado: `python --version`
- [ ] pip instalado: `pip --version`
- [ ] requirements.txt presente
- [ ] Dependências instaladas sem erros

### 2.2 Configurar Arquivo .env

```bash
# Copiar template
cp .env.example .env

# Editar arquivo
nano .env
```

**Conteúdo esperado:**
```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=sinerge
DB_USER=sinerge
DB_PASSWORD=sua_senha_segura
PORT=3000
NODE_ENV=development
```

- [ ] Arquivo `.env` criado na raiz do projeto
- [ ] DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD ajustados
- [ ] Arquivo `.env` adicionado ao `.gitignore` (não commitado)
- [ ] Senha alterada para valor seguro

### 2.3 Testar Conexão com BD

```bash
# Teste rápido com Python
python -c "
import psycopg2
conn = psycopg2.connect('dbname=sinerge user=sinerge password=sua_senha host=localhost port=5432')
cursor = conn.cursor()
cursor.execute('SELECT * FROM grupos')
print('Conexão OK:', cursor.fetchall())
cursor.close()
conn.close()
"
```

- [ ] Conexão estabelecida sem erro
- [ ] Grupos retornados da query

---

## Fase 3: Servidor Backend (Python + Flask)

### 3.1 Arquivo server.py

- [ ] Arquivo `server.py` presente na raiz do projeto
- [ ] Contém endpoints:
  - `GET /api/grupos`
  - `GET /api/pessoas/:grupoId`
  - `POST /api/pessoas/:grupoId`
  - `PUT /api/pessoas/:grupoId/:id`
  - `DELETE /api/pessoas/:grupoId/:id`
  - `GET /api/lancamentos/:grupoId`
  - `POST /api/lancamentos/:grupoId`
  - `GET /api/regras/:grupoId`
  - `POST /api/regras/:grupoId`
- [ ] Arquivo `requirements.txt` contém dependências Flask

### 3.2 Iniciar Servidor em Desenvolvimento

```bash
# Diretamente
python server.py

# Ou com auto-reload e debug
FLASK_ENV=development FLASK_DEBUG=1 python server.py

# Ou no Windows
set FLASK_ENV=development
set FLASK_DEBUG=1
python server.py
```

**Saída esperada:**
```
✓ Servidor rodando em http://localhost:3000
  Banco de dados: postgresql://sinerge@localhost:5432/sinerge
```

- [ ] Servidor inicia sem erros
- [ ] Mensagem "Servidor rodando" aparece
- [ ] Porta 3000 acessível

### 3.3 Testar Endpoints com Curl

```bash
# Listar grupos
curl http://localhost:3000/api/grupos

# Deve retornar:
# [{"id":1,"nome":"Turma A..."}...]

# Listar pessoas do grupo 1
curl http://localhost:3000/api/pessoas/1

# Deve retornar array vazio [] ou pessoas cadastradas

# Health check
curl http://localhost:3000/health
```

- [ ] `GET /api/grupos` retorna 200 com array de grupos
- [ ] `GET /api/pessoas/1` retorna 200 com array de pessoas
- [ ] `GET /api/pessoas/999` retorna 404 (grupo inexistente)
- [ ] `GET /health` retorna 200 com status "ok"

---

## Fase 4: Frontend - Preparação

### 4.1 Copiar e Ajustar Arquivo HTML

```bash
# Backup do arquivo original
cp 2oANO-ADM/MARKETING/diario-entrevistados.html \
   2oANO-ADM/MARKETING/diario-entrevistados.html.backup
```

- [ ] Backup criado do arquivo original
- [ ] Arquivo original preservado em .backup

### 4.2 Adicionar Seletor de Grupo no Header

**Localizar:** `<header>` section (por volta da linha 469)

**Antes:**
```html
<header>
  <h1>Diário de Bordo</h1>
  <span>Controle de Entrevistados</span>
  <div class="header-actions">
    <button class="btn btn-secondary" onclick="exportJSON()">↓ Exportar JSON</button>
    <button class="btn btn-primary" onclick="showTab('cadastro')">+ Novo Entrevistado</button>
  </div>
</header>
```

**Depois:**
```html
<header>
  <h1>Diário de Bordo</h1>
  <span>Controle de Entrevistados</span>
  
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

- [ ] Seletor adicionado no header
- [ ] Styling aplicado
- [ ] onchange aponta para `selecionarGrupo()`

### 4.3 Adicionar Variável Global de Grupo

**Localizar:** Seção `<script>` (por volta da linha 665)

**Adicionar no início:**
```javascript
// Variável global para armazenar o grupo atual
let grupoAtual = null;
```

- [ ] Variável `grupoAtual` declarada no início do script

### 4.4 Implementar Funções de Grupo

**Adicionar após a seção de variáveis globais:**

```javascript
// Carregar grupos no select
async function carregarGrupos() {
    try {
        const response = await fetch('/api/grupos');
        const grupos = await response.json();
        
        const select = document.getElementById('grupoSelect');
        select.innerHTML = grupos.map(g => 
            `<option value="${g.id}">${g.nome} (${g.codigo})</option>`
        ).join('');
        
        if (grupos.length > 0) {
            select.value = grupos[0].id;
            selecionarGrupo();
        }
    } catch (err) {
        console.error('Erro ao carregar grupos:', err);
        toast('Erro ao carregar grupos');
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

- [ ] Função `carregarGrupos()` implementada
- [ ] Função `selecionarGrupo()` implementada
- [ ] Ambas chamam `renderLista()` e `renderCategorias()`

### 4.5 Modificar `loadData()` para Usar API

**Antes:**
```javascript
function loadData()  { return JSON.parse(localStorage.getItem(KEY_DATA)  || '[]'); }
```

**Depois:**
```javascript
async function loadData() {
    if (!grupoAtual) {
        console.warn('Nenhum grupo selecionado');
        return [];
    }
    try {
        const response = await fetch(`/api/pessoas/${grupoAtual}`);
        if (!response.ok) throw new Error('Erro ao carregar pessoas');
        return await response.json();
    } catch (err) {
        console.error('Erro ao carregar dados:', err);
        toast('Erro ao carregar dados');
        return [];
    }
}
```

- [ ] `loadData()` modificada para async
- [ ] Retorna dados da API, não do localStorage
- [ ] Filtra por `grupoAtual`
- [ ] Trata erros com toast

### 4.6 Modificar `salvarEntrevistado()` para Usar API

**Mudar de `saveData(db)` para chamadas HTTP POST/PUT**

Ver arquivo `MIGRATION_EXAMPLE.md` para detalhes completos.

- [ ] `salvarEntrevistado()` usa `POST /api/pessoas/:grupoId`
- [ ] Valida se `grupoAtual` existe
- [ ] Envia objeto `dados` com campos corretos
- [ ] Trata resposta com `.json()`
- [ ] Mostra toast de sucesso/erro

### 4.7 Modificar `deletarEntrevistado()` para Usar API

**Mudar de filtro de array para DELETE HTTP**

- [ ] `deletarEntrevistado()` usa `DELETE /api/pessoas/:grupoId/:id`
- [ ] Confirma com `confirm()`
- [ ] Mostra toast de sucesso
- [ ] Chama `renderLista()` após deletar

### 4.8 Modificar `editarEntrevistado()` para Usar API

**Mudar de busca em array para GET HTTP**

- [ ] `editarEntrevistado()` usa `GET /api/pessoas/:grupoId/:id`
- [ ] Carrega dados da pessoa no formulário
- [ ] Mantém `f-editId` para saber que está editando
- [ ] Valida se pessoa pertence ao grupo

### 4.9 Inicializar Página com `carregarGrupos()`

**Adicionar no final do script:**

```javascript
// INIT
async function initPage() {
    await carregarGrupos();
    updateNavCount();
}

document.addEventListener('DOMContentLoaded', initPage);
```

Ou substituir a última linha:
```javascript
// INIT
updateNavCount();
```

Por:
```javascript
// INIT
document.addEventListener('DOMContentLoaded', async () => {
    await carregarGrupos();
    updateNavCount();
});
```

- [ ] Página chama `carregarGrupos()` ao carregar
- [ ] Seletor de grupo fica preenchido
- [ ] Primeiro grupo é selecionado automaticamente

---

## Fase 5: Testes Manuais

### 5.1 Testar Seletor de Grupo

- [ ] Select aparece no header
- [ ] Lista os 4 grupos de exemplo
- [ ] Mudar de grupo atualiza a página

### 5.2 Testar Cadastro de Pessoa

```
1. Selecionar um grupo
2. Ir para "Cadastro"
3. Preencher formulário:
   - Nome: João Silva
   - Idade: 34
   - Cargo: Operário
   - Setor: Produção
4. Clicar "Salvar Entrevistado"
```

- [ ] Toast "Entrevistado cadastrado!" aparece
- [ ] Formulário limpa
- [ ] Pessoa aparece na aba "Lista"

### 5.3 Testar Isolamento de Grupos

```
1. No Grupo 1, cadastre João Silva
2. Mude para Grupo 2
3. Verifique que João Silva NÃO aparece
4. Mude de volta para Grupo 1
5. Verifique que João Silva aparece novamente
```

- [ ] Cada grupo vê apenas suas próprias pessoas
- [ ] Grupo 2 começa vazio (sem dados do Grupo 1)
- [ ] Retornar ao Grupo 1 mostra os dados salvos

### 5.4 Testar Edição

```
1. Na lista, clicar "Editar" em uma pessoa
2. Modificar alguns campos
3. Clicar "Salvar Entrevistado"
4. Verificar que alterações aparecem na lista
```

- [ ] Campo `f-editId` é preenchido
- [ ] Formulário mostra dados atuais
- [ ] Título muda para "Editar: [nome]"
- [ ] Mudanças são salvas e refletem na lista

### 5.5 Testar Deleção

```
1. Na lista, clicar "Del" em uma pessoa
2. Confirmar deleção
3. Verificar que pessoa desapareceu
4. Mudar para outro grupo e de volta
5. Verificar que pessoa ainda foi deletada
```

- [ ] Confirmação aparece
- [ ] Pessoa removida da lista
- [ ] Dados persistem (não volta ao recarregar)

### 5.6 Testar Pesquisa e Filtro

```
1. Na aba "Lista", digitar nome na busca
2. Lista filtra dinamicamente
3. Usar dropdown de "Status" para filtrar
```

- [ ] Busca por nome funciona
- [ ] Filtro por status funciona
- [ ] Combinações funcionam (busca + filtro)

### 5.7 Testar Categorias e Relatório

- [ ] Aba "Categorias" carrega sem erro
- [ ] Mostra categorizações (faixa etária, setor, etc)
- [ ] Aba "Relatório" gera relatório correto
- [ ] Status (Adequado/Atenção/Irregular) calcula corretamente

### 5.8 Testar Regras

```
1. Na aba "Regras", editar código JavaScript
2. Adicionar uma validação simples
3. Clicar "Salvar Regras"
4. Ir para "Relatório" e regenerar
5. Verificar que nova regra é aplicada
```

- [ ] Regras carregam do banco (não do localStorage)
- [ ] Mudanças são persistidas
- [ ] Cada grupo pode ter regras diferentes

---

## Fase 6: Testes de Banco de Dados

### 6.1 Validar Dados no PostgreSQL

```sql
-- Conectar ao banco
psql -U sinerge -d sinerge

-- Verificar pessoas criadas
SELECT id, grupo_id, nome FROM pessoas;

-- Verificar lançamentos
SELECT id, grupo_id, pessoa_id, titulo FROM lancamento_diario;

-- Verificar isolamento de grupos
SELECT COUNT(*) FROM pessoas WHERE grupo_id = 1;
SELECT COUNT(*) FROM pessoas WHERE grupo_id = 2;

-- Verificar extras
SELECT * FROM pessoas_extras;

-- Sair
\q
```

- [ ] Pessoas aparecem com `grupo_id` correto
- [ ] Cada grupo tem seus próprios dados
- [ ] Extras estão armazenados corretamente
- [ ] Dados persistem entre consultas

### 6.2 Testar Integridade Referencial

```sql
-- Tentar deletar um grupo (em caso de necessidade futura)
DELETE FROM grupos WHERE id = 99;

-- Verificar que pessoas do grupo 1 seriam deletadas em cascade
-- (não teste de verdade em produção!)

-- Criar novo grupo de teste
INSERT INTO grupos (nome, codigo) VALUES ('Teste', 'teste-2024');

-- Deletar o grupo de teste
DELETE FROM grupos WHERE codigo = 'teste-2024';
```

- [ ] Cascade funciona (deletar grupo deleta pessoas/lançamentos)
- [ ] Foreign keys funcionam
- [ ] Dados órfãos não são permitidos

### 6.3 Analisar Performance

```sql
-- Ver planos de execução
EXPLAIN ANALYZE SELECT * FROM pessoas WHERE grupo_id = 1;

-- Verificar índices
SELECT * FROM pg_indexes WHERE schemaname = 'public';
```

- [ ] Índices estão criados
- [ ] Queries usam índices (Index Scan, não Seq Scan)

---

## Fase 7: Documentação & Deployment

### 7.1 Atualizar Documentação

- [ ] `DATABASE_GUIDE.md` lido e entendido
- [ ] `MIGRATION_EXAMPLE.md` consultado durante implementação
- [ ] Comentários adicionados no código onde necessário

### 7.2 Criar Arquivo de Instruções de Uso

**Criar `USAGE.md` para usuários finais:**

```markdown
# Como Usar o Diário de Bordo

1. Selecione seu grupo no dropdown no topo da página
2. Acesse a aba "Cadastro" para adicionar entrevistados
3. Use "Lista" para visualizar e editar
4. Customize as "Regras" de julgamento conforme necessário
5. Veja "Relatório" para análise consolidada
```

- [ ] Instruções de uso criadas para alunos/professores

### 7.3 Preparar para Produção

```bash
# Verificar .gitignore
echo ".env" >> .gitignore
echo "__pycache__/" >> .gitignore
echo "*.pyc" >> .gitignore
echo ".backup" >> .gitignore
echo "venv/" >> .gitignore

# Criar ambiente virtual (opcional mas recomendado)
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
pip install -r requirements.txt

# Testar servidor
python server.py
```

- [ ] `.env` adicionado ao `.gitignore`
- [ ] `__pycache__/` não commitado
- [ ] `venv/` não commitado
- [ ] Arquivo `.backup` ignorado
- [ ] `requirements.txt` commited

### 7.4 Configurar Variáveis de Produção

- [ ] Senha do banco alterada para valor seguro
- [ ] `NODE_ENV=production` configurado
- [ ] URL de produção correta em `DATABASE_URL`
- [ ] Porta apropriada (`3000` ou outra)

---

## Fase 8: Monitoramento Pós-Deploy

### 8.1 Verificar Logs

```bash
# Em desenvolvimento (Flask debug mode)
FLASK_ENV=development FLASK_DEBUG=1 python server.py

# Em produção (com logs salvos)
python server.py > app.log 2>&1 &

# Monitorar logs
tail -f app.log

# Em Windows, usar PowerShell
Get-Content app.log -Tail 50 -Wait
```

- [ ] Servidor inicia sem erros
- [ ] Logs não mostram avisos críticos
- [ ] Conexão com BD estabelecida

### 8.2 Validar Integridade de Dados

```sql
-- Contagem total
SELECT 
    (SELECT COUNT(*) FROM grupos) as grupos,
    (SELECT COUNT(*) FROM pessoas) as pessoas,
    (SELECT COUNT(*) FROM lancamento_diario) as lancamentos;
```

- [ ] Contagens consistentes
- [ ] Sem dados órfãos

### 8.3 Testes de Carga (Opcional)

```bash
# Com Apache Bench
ab -n 100 -c 10 http://localhost:3000/api/grupos

# Com curl em loop (Bash)
for i in {1..50}; do
  curl http://localhost:3000/api/grupos > /dev/null
done

# Com curl em loop (Windows PowerShell)
1..50 | ForEach-Object { curl http://localhost:3000/api/grupos | Out-Null }
```

- [ ] Servidor aguenta múltiplas requisições
- [ ] Nenhum erro 500
- [ ] Tempo de resposta aceitável
- [ ] Verificar `/health` endpoint

---

## Checklist Final

- [ ] Todas as fases completadas
- [ ] Testes manuais passaram
- [ ] Dados persistem no PostgreSQL
- [ ] Isolamento de grupos funciona
- [ ] Servidor em produção estável
- [ ] Documentação atualizada
- [ ] Backup do código feito
- [ ] Backup do banco feito (opcional):
  ```bash
  pg_dump -U sinerge sinerge > sinerge_backup_$(date +%Y%m%d).sql
  ```

---

## Suporte & Troubleshooting

### Erro: "Grupo não existe"
```sql
SELECT * FROM grupos;
-- Verificar se ID passado existe
```

### Erro: "Cannot read property 'value' of null"
- Verificar se seletor de grupo foi adicionado ao HTML
- Confirmar ID é `grupoSelect`

### Erro: "Pessoa não pertence ao grupo"
- Validar se `pessoa_id` está associado a `grupo_id` correto
```sql
SELECT * FROM pessoas WHERE id = X;
```

### Servidor não inicia
- Verificar credenciais em `.env`
- Confirmar banco PostgreSQL está rodando
- Verificar porta 3000 está disponível

### Performance lenta
- Executar `ANALYZE` no banco
```sql
ANALYZE;
```
- Verificar índices com `EXPLAIN ANALYZE`

---

**Data de Conclusão:** ___________  
**Responsável:** ___________  
**Observações:** ___________

