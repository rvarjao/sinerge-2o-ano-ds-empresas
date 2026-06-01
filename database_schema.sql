-- =====================================================
-- SCHEMA DO BANCO DE DADOS - Sinerge
-- Separação por grupo_id (sem schemas nem tabelas duplicadas)
-- =====================================================

-- 1. TABELA GRUPOS
-- Armazena os grupos de alunos
CREATE TABLE IF NOT EXISTS grupos (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Índice para buscas rápidas por código
CREATE INDEX IF NOT EXISTS idx_grupos_codigo ON grupos(codigo);

-- =====================================================
-- 2. TABELA PESSOAS
-- Armazena os entrevistados/pessoas do projeto
-- Cada pessoa pertence a um grupo
CREATE TABLE IF NOT EXISTS pessoas (
    id SERIAL PRIMARY KEY,
    grupo_id INTEGER NOT NULL REFERENCES grupos(id) ON DELETE CASCADE,
    nome VARCHAR(100) NOT NULL,
    idade INTEGER,
    cargo VARCHAR(100),
    setor VARCHAR(100),
    situacao VARCHAR(50),
    risco VARCHAR(50),
    epi VARCHAR(50),
    observacoes TEXT,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Índices para buscas rápidas
CREATE INDEX IF NOT EXISTS idx_pessoas_grupo_id ON pessoas(grupo_id);
CREATE INDEX IF NOT EXISTS idx_pessoas_nome ON pessoas(nome);
CREATE INDEX IF NOT EXISTS idx_pessoas_grupo_nome ON pessoas(grupo_id, nome);

-- =====================================================
-- 3. TABELA LANCAMENTO_DIARIO
-- Armazena os comentários/lançamentos dos entrevistados
-- Cada lançamento pertence a um grupo e pode estar associado a uma pessoa
CREATE TABLE IF NOT EXISTS lancamento_diario (
    id SERIAL PRIMARY KEY,
    grupo_id INTEGER NOT NULL REFERENCES grupos(id) ON DELETE CASCADE,
    pessoa_id INTEGER REFERENCES pessoas(id) ON DELETE SET NULL,
    titulo VARCHAR(150),
    texto TEXT NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

-- Índices para buscas rápidas
CREATE INDEX IF NOT EXISTS idx_lancamento_grupo_id ON lancamento_diario(grupo_id);
CREATE INDEX IF NOT EXISTS idx_lancamento_pessoa_id ON lancamento_diario(pessoa_id);
CREATE INDEX IF NOT EXISTS idx_lancamento_grupo_pessoa ON lancamento_diario(grupo_id, pessoa_id);

-- =====================================================
-- 4. TABELA EXTRAS
-- Armazena campos adicionais customizáveis para pessoas
-- (flexibilidade para dados como turno, matrícula, etc.)
CREATE TABLE IF NOT EXISTS pessoas_extras (
    id SERIAL PRIMARY KEY,
    pessoa_id INTEGER NOT NULL REFERENCES pessoas(id) ON DELETE CASCADE,
    chave VARCHAR(100) NOT NULL,
    valor TEXT,
    criado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_pessoas_extras_pessoa_id ON pessoas_extras(pessoa_id);

-- =====================================================
-- 5. TABELA REGRAS
-- Armazena as regras de julgamento customizadas por grupo
CREATE TABLE IF NOT EXISTS regras_julgamento (
    id SERIAL PRIMARY KEY,
    grupo_id INTEGER NOT NULL UNIQUE REFERENCES grupos(id) ON DELETE CASCADE,
    codigo_regras TEXT NOT NULL,
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_regras_grupo_id ON regras_julgamento(grupo_id);

-- =====================================================
-- DADOS INICIAIS - GRUPOS DE EXEMPLO
-- =====================================================

-- Inserir grupos de exemplo (se não existirem)
INSERT INTO grupos (nome, codigo) VALUES
    ('Turma A - 2º Ano ADM', 'turma-a-2023'),
    ('Turma B - 2º Ano ADM', 'turma-b-2023'),
    ('Turma C - 2º Ano ADM', 'turma-c-2023'),
    ('Turma D - 2º Ano ADM', 'turma-d-2023')
ON CONFLICT (codigo) DO NOTHING;

-- =====================================================
-- VIEWS ÚTEIS (OPCIONAL)
-- =====================================================

-- View: Contagem de pessoas por grupo
CREATE OR REPLACE VIEW v_pessoas_por_grupo AS
SELECT
    g.id,
    g.nome,
    g.codigo,
    COUNT(p.id) as total_pessoas
FROM grupos g
LEFT JOIN pessoas p ON g.id = p.grupo_id
GROUP BY g.id, g.nome, g.codigo;

-- View: Contagem de lançamentos por grupo
CREATE OR REPLACE VIEW v_lancamentos_por_grupo AS
SELECT
    g.id,
    g.nome,
    COUNT(ld.id) as total_lancamentos
FROM grupos g
LEFT JOIN lancamento_diario ld ON g.id = ld.grupo_id
GROUP BY g.id, g.nome;
