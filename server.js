// =====================================================
// SERVIDOR EXPRESS - Sinerge
// Backend que conecta o frontend ao PostgreSQL
// =====================================================

const express = require('express');
const { Pool } = require('pg');
const cors = require('cors');
require('dotenv').config();

const app = express();

// =====================================================
// CONFIGURAÇÃO
// =====================================================

const pool = new Pool({
    connectionString: process.env.DATABASE_URL ||
        'postgresql://sinerge:password@localhost:5432/sinerge'
});

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// =====================================================
// HELPER: Executar query
// =====================================================

async function query(sql, params = []) {
    try {
        const result = await pool.query(sql, params);
        return result.rows || [];
    } catch (err) {
        console.error('Query Error:', sql, params, err);
        throw err;
    }
}

// =====================================================
// MIDDLEWARE: Validar grupo
// =====================================================

async function validarGrupo(req, res, next) {
    const grupoId = parseInt(req.params.grupoId);
    if (isNaN(grupoId)) {
        return res.status(400).json({ error: 'ID de grupo inválido' });
    }

    try {
        const resultado = await query('SELECT id FROM grupos WHERE id = $1', [grupoId]);
        if (resultado.length === 0) {
            return res.status(404).json({ error: 'Grupo não encontrado' });
        }
        req.grupoId = grupoId;
        next();
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
}

// =====================================================
// ROTAS: GRUPOS
// =====================================================

app.get('/api/grupos', async (req, res) => {
    try {
        const sql = 'SELECT * FROM grupos ORDER BY criado_em DESC;';
        const grupos = await query(sql);
        res.json(grupos);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/grupos/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const sql = 'SELECT * FROM grupos WHERE id = $1;';
        const resultado = await query(sql, [parseInt(id)]);

        if (resultado.length === 0) {
            return res.status(404).json({ error: 'Grupo não encontrado' });
        }
        res.json(resultado[0]);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/api/grupos', async (req, res) => {
    try {
        const { nome, codigo } = req.body;

        if (!nome || !codigo) {
            return res.status(400).json({ error: 'Nome e código são obrigatórios' });
        }

        const sql = `
            INSERT INTO grupos (nome, codigo)
            VALUES ($1, $2)
            RETURNING *;
        `;
        const resultado = await query(sql, [nome, codigo]);
        res.status(201).json(resultado[0]);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

// =====================================================
// ROTAS: PESSOAS
// =====================================================

app.get('/api/pessoas/:grupoId', validarGrupo, async (req, res) => {
    try {
        const sql = `
            SELECT p.*
            FROM pessoas p
            WHERE p.grupo_id = $1
            ORDER BY p.criado_em DESC;
        `;
        const pessoas = await query(sql, [req.grupoId]);

        // Carregar extras para cada pessoa
        const pessoasComExtras = await Promise.all(
            pessoas.map(async (p) => {
                const extrasSql = `
                    SELECT chave, valor FROM pessoas_extras WHERE pessoa_id = $1
                `;
                const extras = await query(extrasSql, [p.id]);
                const extrasObj = {};
                extras.forEach(e => {
                    extrasObj[e.chave] = e.valor;
                });
                return { ...p, extras: extrasObj };
            })
        );

        res.json(pessoasComExtras);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/pessoas/:grupoId/:id', validarGrupo, async (req, res) => {
    try {
        const { id } = req.params;

        const sql = `SELECT * FROM pessoas WHERE id = $1 AND grupo_id = $2;`;
        const resultado = await query(sql, [parseInt(id), req.grupoId]);

        if (resultado.length === 0) {
            return res.status(404).json({ error: 'Pessoa não encontrada' });
        }

        const pessoa = resultado[0];

        // Carregar extras
        const extrasSql = `SELECT chave, valor FROM pessoas_extras WHERE pessoa_id = $1`;
        const extras = await query(extrasSql, [pessoa.id]);
        const extrasObj = {};
        extras.forEach(e => {
            extrasObj[e.chave] = e.valor;
        });
        pessoa.extras = extrasObj;

        res.json(pessoa);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/api/pessoas/:grupoId', validarGrupo, async (req, res) => {
    const client = await pool.connect();
    try {
        await client.query('BEGIN');

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
        } = req.body;

        if (!nome) {
            await client.query('ROLLBACK');
            return res.status(400).json({ error: 'Nome é obrigatório' });
        }

        const sql = `
            INSERT INTO pessoas (grupo_id, nome, idade, cargo, setor, situacao, risco, epi, observacoes)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            RETURNING *;
        `;

        const resultado = await client.query(sql, [
            req.grupoId,
            nome,
            idade || null,
            cargo || null,
            setor || null,
            situacao || null,
            risco || null,
            epi || null,
            observacoes || null
        ]);

        const pessoa = resultado.rows[0];

        // Inserir extras
        if (extras && Object.keys(extras).length > 0) {
            for (const [chave, valor] of Object.entries(extras)) {
                const extraSql = `
                    INSERT INTO pessoas_extras (pessoa_id, chave, valor)
                    VALUES ($1, $2, $3)
                `;
                await client.query(extraSql, [pessoa.id, chave, valor]);
            }
            pessoa.extras = extras;
        } else {
            pessoa.extras = {};
        }

        await client.query('COMMIT');
        res.status(201).json(pessoa);
    } catch (err) {
        await client.query('ROLLBACK');
        res.status(400).json({ error: err.message });
    } finally {
        client.release();
    }
});

app.put('/api/pessoas/:grupoId/:id', validarGrupo, async (req, res) => {
    const client = await pool.connect();
    try {
        await client.query('BEGIN');

        const { id } = req.params;
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
        } = req.body;

        // Validar que pessoa pertence ao grupo
        const verificarSql = `SELECT id FROM pessoas WHERE id = $1 AND grupo_id = $2`;
        const verificar = await client.query(verificarSql, [parseInt(id), req.grupoId]);

        if (verificar.rows.length === 0) {
            await client.query('ROLLBACK');
            return res.status(404).json({ error: 'Pessoa não encontrada' });
        }

        const sql = `
            UPDATE pessoas
            SET
                nome = COALESCE($1, nome),
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

        const resultado = await client.query(sql, [
            nome || null,
            idade || null,
            cargo || null,
            setor || null,
            situacao || null,
            risco || null,
            epi || null,
            observacoes || null,
            parseInt(id),
            req.grupoId
        ]);

        const pessoa = resultado.rows[0];

        // Atualizar extras
        if (extras !== undefined) {
            // Deletar extras antigos
            await client.query('DELETE FROM pessoas_extras WHERE pessoa_id = $1', [pessoa.id]);

            // Inserir novos
            if (Object.keys(extras).length > 0) {
                for (const [chave, valor] of Object.entries(extras)) {
                    const extraSql = `
                        INSERT INTO pessoas_extras (pessoa_id, chave, valor)
                        VALUES ($1, $2, $3)
                    `;
                    await client.query(extraSql, [pessoa.id, chave, valor]);
                }
            }
            pessoa.extras = extras;
        }

        await client.query('COMMIT');
        res.json(pessoa);
    } catch (err) {
        await client.query('ROLLBACK');
        res.status(400).json({ error: err.message });
    } finally {
        client.release();
    }
});

app.delete('/api/pessoas/:grupoId/:id', validarGrupo, async (req, res) => {
    try {
        const { id } = req.params;

        const sql = `DELETE FROM pessoas WHERE id = $1 AND grupo_id = $2 RETURNING id;`;
        const resultado = await query(sql, [parseInt(id), req.grupoId]);

        if (resultado.length === 0) {
            return res.status(404).json({ error: 'Pessoa não encontrada' });
        }

        res.json({ success: true, id: resultado[0].id });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// =====================================================
// ROTAS: LANÇAMENTOS DIÁRIOS
// =====================================================

app.get('/api/lancamentos/:grupoId', validarGrupo, async (req, res) => {
    try {
        const { pessoaId } = req.query;
        let sql = `
            SELECT * FROM lancamento_diario
            WHERE grupo_id = $1
        `;
        const params = [req.grupoId];

        if (pessoaId) {
            sql += ` AND pessoa_id = $2`;
            params.push(parseInt(pessoaId));
        }

        sql += ` ORDER BY criado_em DESC;`;

        const lancamentos = await query(sql, params);
        res.json(lancamentos);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/lancamentos/:grupoId/:id', validarGrupo, async (req, res) => {
    try {
        const { id } = req.params;

        const sql = `
            SELECT * FROM lancamento_diario
            WHERE id = $1 AND grupo_id = $2;
        `;
        const resultado = await query(sql, [parseInt(id), req.grupoId]);

        if (resultado.length === 0) {
            return res.status(404).json({ error: 'Lançamento não encontrado' });
        }

        res.json(resultado[0]);
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/api/lancamentos/:grupoId', validarGrupo, async (req, res) => {
    try {
        const { pessoaId, titulo, texto } = req.body;

        if (!texto) {
            return res.status(400).json({ error: 'Texto é obrigatório' });
        }

        // Se pessoaId foi fornecido, validar que pertence ao grupo
        if (pessoaId) {
            const verificarSql = `SELECT id FROM pessoas WHERE id = $1 AND grupo_id = $2`;
            const verificar = await query(verificarSql, [pessoaId, req.grupoId]);
            if (verificar.length === 0) {
                return res.status(400).json({ error: 'Pessoa não pertence ao grupo' });
            }
        }

        const sql = `
            INSERT INTO lancamento_diario (grupo_id, pessoa_id, titulo, texto)
            VALUES ($1, $2, $3, $4)
            RETURNING *;
        `;

        const resultado = await query(sql, [
            req.grupoId,
            pessoaId || null,
            titulo || null,
            texto
        ]);

        res.status(201).json(resultado[0]);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

app.delete('/api/lancamentos/:grupoId/:id', validarGrupo, async (req, res) => {
    try {
        const { id } = req.params;

        const sql = `DELETE FROM lancamento_diario WHERE id = $1 AND grupo_id = $2 RETURNING id;`;
        const resultado = await query(sql, [parseInt(id), req.grupoId]);

        if (resultado.length === 0) {
            return res.status(404).json({ error: 'Lançamento não encontrado' });
        }

        res.json({ success: true });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

// =====================================================
// ROTAS: REGRAS
// =====================================================

app.get('/api/regras/:grupoId', validarGrupo, async (req, res) => {
    try {
        const sql = `SELECT codigo_regras FROM regras_julgamento WHERE grupo_id = $1;`;
        const resultado = await query(sql, [req.grupoId]);

        const regras = resultado.length > 0 ? resultado[0].codigo_regras : null;
        res.json({ regras: regras || '' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.post('/api/regras/:grupoId', validarGrupo, async (req, res) => {
    try {
        const { regras } = req.body;

        if (!regras) {
            return res.status(400).json({ error: 'Código de regras é obrigatório' });
        }

        const sql = `
            INSERT INTO regras_julgamento (grupo_id, codigo_regras)
            VALUES ($1, $2)
            ON CONFLICT (grupo_id) DO UPDATE SET
                codigo_regras = $2,
                atualizado_em = NOW()
            RETURNING *;
        `;

        const resultado = await query(sql, [req.grupoId, regras]);
        res.json(resultado[0]);
    } catch (err) {
        res.status(400).json({ error: err.message });
    }
});

// =====================================================
// ERROR HANDLING
// =====================================================

app.use((err, req, res, next) => {
    console.error(err);
    res.status(500).json({ error: 'Erro interno do servidor' });
});

// =====================================================
// INICIAR SERVIDOR
// =====================================================

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`✓ Servidor rodando em http://localhost:${PORT}`);
    console.log(`  Banco de dados: ${process.env.DATABASE_URL || 'postgresql://localhost:5432/sinerge'}`);
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\nEncerrando servidor...');
    await pool.end();
    process.exit(0);
});
