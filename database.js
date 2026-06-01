// =====================================================
// DATABASE ACCESS LAYER (DAL)
// Camada única de acesso ao banco PostgreSQL
// Todas as funções recebem grupo_id para isolamento de dados
// =====================================================

const DB_URL = process.env.DATABASE_URL || 'postgresql://user:password@localhost:5432/sinerge';

// Função utilitária para executar queries
async function query(sql, params = []) {
    try {
        // Usar fetch com API REST ou Pool de conexão
        // Ajuste conforme sua implementação (Express + pg, Supabase, etc)
        const result = await fetch('/api/db', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql, params })
        });
        const data = await result.json();
        if (data.error) throw new Error(data.error);
        return data.rows || [];
    } catch (err) {
        console.error('Database Error:', err);
        throw err;
    }
}

// =====================================================
// GRUPOS
// =====================================================

async function criarGrupo(nome, codigo) {
    const sql = `
        INSERT INTO grupos (nome, codigo)
        VALUES ($1, $2)
        RETURNING *;
    `;
    const result = await query(sql, [nome, codigo]);
    return result[0] || null;
}

async function listarGrupos() {
    const sql = `SELECT * FROM grupos ORDER BY criado_em DESC;`;
    return await query(sql);
}

async function obterGrupo(id) {
    const sql = `SELECT * FROM grupos WHERE id = $1;`;
    const result = await query(sql, [id]);
    return result[0] || null;
}

async function obterGrupoPorCodigo(codigo) {
    const sql = `SELECT * FROM grupos WHERE codigo = $1;`;
    const result = await query(sql, [codigo]);
    return result[0] || null;
}

// =====================================================
// PESSOAS
// =====================================================

async function criarPessoa(grupoId, dados) {
    // Validar grupo
    const grupo = await obterGrupo(grupoId);
    if (!grupo) throw new Error(`Grupo ${grupoId} não existe`);

    const {
        nome,
        idade,
        cargo,
        setor,
        situacao,
        risco,
        epi,
        observacoes,
        extras // objeto com chave: valor
    } = dados;

    const sql = `
        INSERT INTO pessoas (grupo_id, nome, idade, cargo, setor, situacao, risco, epi, observacoes)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        RETURNING *;
    `;

    const result = await query(sql, [grupoId, nome, idade, cargo, setor, situacao, risco, epi, observacoes]);
    const pessoa = result[0];

    // Inserir campos extras, se houver
    if (extras && Object.keys(extras).length > 0) {
        for (const [chave, valor] of Object.entries(extras)) {
            await query(
                `INSERT INTO pessoas_extras (pessoa_id, chave, valor) VALUES ($1, $2, $3)`,
                [pessoa.id, chave, valor]
            );
        }
    }

    return pessoa;
}

async function listarPessoas(grupoId, filtro = {}) {
    // Sempre filtrar por grupo_id - OBRIGATÓRIO
    let sql = `SELECT * FROM pessoas WHERE grupo_id = $1`;
    const params = [grupoId];
    let paramIndex = 2;

    // Filtros opcionais
    if (filtro.nome) {
        sql += ` AND nome ILIKE $${paramIndex}`;
        params.push(`%${filtro.nome}%`);
        paramIndex++;
    }
    if (filtro.setor) {
        sql += ` AND setor = $${paramIndex}`;
        params.push(filtro.setor);
        paramIndex++;
    }
    if (filtro.situacao) {
        sql += ` AND situacao = $${paramIndex}`;
        params.push(filtro.situacao);
        paramIndex++;
    }
    if (filtro.risco) {
        sql += ` AND risco = $${paramIndex}`;
        params.push(filtro.risco);
        paramIndex++;
    }

    sql += ` ORDER BY criado_em DESC;`;

    return await query(sql, params);
}

async function obterPessoa(id, grupoId) {
    // Validar que a pessoa pertence ao grupo
    const sql = `SELECT * FROM pessoas WHERE id = $1 AND grupo_id = $2;`;
    const result = await query(sql, [id, grupoId]);
    return result[0] || null;
}

async function atualizarPessoa(id, grupoId, dados) {
    // Validar propriedade do grupo
    const pessoa = await obterPessoa(id, grupoId);
    if (!pessoa) throw new Error(`Pessoa ${id} não encontrada no grupo ${grupoId}`);

    const {
        nome,
        idade,
        cargo,
        setor,
        situacao,
        risco,
        epi,
        observacoes,
        extras
    } = dados;

    const sql = `
        UPDATE pessoas
        SET nome = COALESCE($1, nome),
            idade = COALESCE($2, idade),
            cargo = COALESCE($3, cargo),
            setor = COALESCE($4, setor),
            situacao = COALESCE($5, situacao),
            risco = COALESCE($6, risco),
            epi = COALESCE($7, epi),
            observacoes = COALESCE($8, observacoes),
            atualizado_em = NOW()
        WHERE id = $9 AND grupo_id = $10
        RETURNING *;
    `;

    const result = await query(sql, [
        nome, idade, cargo, setor, situacao, risco, epi, observacoes, id, grupoId
    ]);

    // Atualizar extras se fornecidos
    if (extras) {
        // Limpar extras antigos
        await query(`DELETE FROM pessoas_extras WHERE pessoa_id = $1`, [id]);
        // Inserir novos
        for (const [chave, valor] of Object.entries(extras)) {
            await query(
                `INSERT INTO pessoas_extras (pessoa_id, chave, valor) VALUES ($1, $2, $3)`,
                [id, chave, valor]
            );
        }
    }

    return result[0] || null;
}

async function deletarPessoa(id, grupoId) {
    const sql = `DELETE FROM pessoas WHERE id = $1 AND grupo_id = $2 RETURNING id;`;
    const result = await query(sql, [id, grupoId]);
    return result.length > 0;
}

async function obterPessoaComExtras(id, grupoId) {
    const pessoa = await obterPessoa(id, grupoId);
    if (!pessoa) return null;

    const extras = await query(
        `SELECT chave, valor FROM pessoas_extras WHERE pessoa_id = $1`,
        [id]
    );

    const extrasObj = {};
    extras.forEach(e => {
        extrasObj[e.chave] = e.valor;
    });

    return { ...pessoa, extras: extrasObj };
}

// =====================================================
// LANÇAMENTOS DIÁRIOS
// =====================================================

async function criarLancamento(grupoId, dados) {
    // Validar grupo
    const grupo = await obterGrupo(grupoId);
    if (!grupo) throw new Error(`Grupo ${grupoId} não existe`);

    const { pessoaId, titulo, texto } = dados;

    // Se pessoaId foi fornecido, validar que pertence ao grupo
    if (pessoaId) {
        const pessoa = await obterPessoa(pessoaId, grupoId);
        if (!pessoa) throw new Error(`Pessoa ${pessoaId} não pertence ao grupo ${grupoId}`);
    }

    const sql = `
        INSERT INTO lancamento_diario (grupo_id, pessoa_id, titulo, texto)
        VALUES ($1, $2, $3, $4)
        RETURNING *;
    `;

    const result = await query(sql, [grupoId, pessoaId || null, titulo, texto]);
    return result[0] || null;
}

async function listarLancamentos(grupoId, pessoaId = null) {
    // Sempre filtrar por grupo_id
    let sql = `SELECT * FROM lancamento_diario WHERE grupo_id = $1`;
    const params = [grupoId];

    if (pessoaId) {
        sql += ` AND pessoa_id = $2`;
        params.push(pessoaId);
    }

    sql += ` ORDER BY criado_em DESC;`;

    return await query(sql, params);
}

async function obterLancamento(id, grupoId) {
    const sql = `SELECT * FROM lancamento_diario WHERE id = $1 AND grupo_id = $2;`;
    const result = await query(sql, [id, grupoId]);
    return result[0] || null;
}

async function atualizarLancamento(id, grupoId, dados) {
    const lancamento = await obterLancamento(id, grupoId);
    if (!lancamento) throw new Error(`Lançamento ${id} não encontrado no grupo ${grupoId}`);

    const { titulo, texto } = dados;

    const sql = `
        UPDATE lancamento_diario
        SET titulo = COALESCE($1, titulo),
            texto = COALESCE($2, texto),
            atualizado_em = NOW()
        WHERE id = $3 AND grupo_id = $4
        RETURNING *;
    `;

    const result = await query(sql, [titulo, texto, id, grupoId]);
    return result[0] || null;
}

async function deletarLancamento(id, grupoId) {
    const sql = `DELETE FROM lancamento_diario WHERE id = $1 AND grupo_id = $2 RETURNING id;`;
    const result = await query(sql, [id, grupoId]);
    return result.length > 0;
}

// =====================================================
// REGRAS DE JULGAMENTO
// =====================================================

async function obterRegras(grupoId) {
    const sql = `SELECT codigo_regras FROM regras_julgamento WHERE grupo_id = $1;`;
    const result = await query(sql, [grupoId]);
    return result[0]?.codigo_regras || null;
}

async function salvarRegras(grupoId, codigoRegras) {
    const sql = `
        INSERT INTO regras_julgamento (grupo_id, codigo_regras)
        VALUES ($1, $2)
        ON CONFLICT (grupo_id) DO UPDATE SET
            codigo_regras = $2,
            atualizado_em = NOW()
        RETURNING *;
    `;

    const result = await query(sql, [grupoId, codigoRegras]);
    return result[0] || null;
}

// =====================================================
// EXPORTS
// =====================================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        // Grupos
        criarGrupo,
        listarGrupos,
        obterGrupo,
        obterGrupoPorCodigo,
        // Pessoas
        criarPessoa,
        listarPessoas,
        obterPessoa,
        atualizarPessoa,
        deletarPessoa,
        obterPessoaComExtras,
        // Lançamentos
        criarLancamento,
        listarLancamentos,
        obterLancamento,
        atualizarLancamento,
        deletarLancamento,
        // Regras
        obterRegras,
        salvarRegras
    };
}
