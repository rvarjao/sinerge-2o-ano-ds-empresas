"""
=====================================================
SERVIDOR FLASK - Sinerge
Backend em Python que conecta o frontend ao PostgreSQL
=====================================================
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import traceback

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuração do banco de dados
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'sinerge'),
    'user': os.getenv('DB_USER', 'sinerge'),
    'password': os.getenv('DB_PASSWORD', 'password')
}

# =====================================================
# HELPER: Conexão com banco
# =====================================================

def get_db():
    """Abre conexão com PostgreSQL"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Erro de conexão: {e}")
        return None

def execute_query(sql, params=None, fetch_one=False, fetch_all=True):
    """
    Executa query e retorna resultado
    fetch_one: retorna apenas um registro
    fetch_all: retorna todos os registros
    """
    try:
        conn = get_db()
        if not conn:
            return None, "Erro de conexão com banco"

        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(sql, params or ())

        if 'SELECT' in sql.upper():
            if fetch_one:
                result = cursor.fetchone()
            else:
                result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.rowcount

        cursor.close()
        conn.close()

        return result, None
    except Exception as e:
        print(f"Query Error: {e}")
        print(f"SQL: {sql}")
        print(f"Params: {params}")
        return None, str(e)

# =====================================================
# MIDDLEWARE: Validar grupo
# =====================================================

def validar_grupo(grupo_id):
    """Verifica se grupo existe"""
    try:
        grupo_id = int(grupo_id)
    except:
        return None, "ID de grupo inválido"

    sql = "SELECT id FROM grupos WHERE id = %s"
    resultado, erro = execute_query(sql, [grupo_id], fetch_one=True)

    if erro:
        return None, erro
    if not resultado:
        return None, "Grupo não encontrado"

    return grupo_id, None

# =====================================================
# ROTAS: GRUPOS
# =====================================================

@app.route('/api/grupos', methods=['GET'])
def listar_grupos():
    """Lista todos os grupos"""
    sql = "SELECT * FROM grupos ORDER BY criado_em DESC;"
    grupos, erro = execute_query(sql)

    if erro:
        return jsonify({'error': erro}), 500

    # Converter RealDictRow para dict normal
    grupos = [dict(g) for g in grupos] if grupos else []
    return jsonify(grupos), 200

@app.route('/api/grupos/<int:grupo_id>', methods=['GET'])
def obter_grupo(grupo_id):
    """Obter um grupo específico"""
    sql = "SELECT * FROM grupos WHERE id = %s;"
    resultado, erro = execute_query(sql, [grupo_id], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 500
    if not resultado:
        return jsonify({'error': 'Grupo não encontrado'}), 404

    return jsonify(dict(resultado)), 200

@app.route('/api/grupos', methods=['POST'])
def criar_grupo():
    """Criar novo grupo"""
    data = request.get_json()
    nome = data.get('nome')
    codigo = data.get('codigo')

    if not nome or not codigo:
        return jsonify({'error': 'Nome e código são obrigatórios'}), 400

    sql = """
        INSERT INTO grupos (nome, codigo)
        VALUES (%s, %s)
        RETURNING *;
    """
    resultado, erro = execute_query(sql, [nome, codigo], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 400

    return jsonify(dict(resultado)), 201

# =====================================================
# ROTAS: PESSOAS
# =====================================================

@app.route('/api/pessoas/<int:grupo_id>', methods=['GET'])
def listar_pessoas(grupo_id):
    """Listar pessoas de um grupo"""
    grupo_id, erro = validar_grupo(grupo_id)
    if erro:
        return jsonify({'error': erro}), 400 if "inválido" in erro else 404

    sql = """
        SELECT p.*
        FROM pessoas p
        WHERE p.grupo_id = %s
        ORDER BY p.criado_em DESC;
    """
    pessoas, erro = execute_query(sql, [grupo_id])

    if erro:
        return jsonify({'error': erro}), 500

    # Carregar extras para cada pessoa
    pessoas_com_extras = []
    for p in pessoas:
        p_dict = dict(p)

        sql_extras = "SELECT chave, valor FROM pessoas_extras WHERE pessoa_id = %s"
        extras, _ = execute_query(sql_extras, [p['id']])

        extras_obj = {}
        if extras:
            for e in extras:
                extras_obj[e['chave']] = e['valor']

        p_dict['extras'] = extras_obj
        pessoas_com_extras.append(p_dict)

    return jsonify(pessoas_com_extras), 200

@app.route('/api/pessoas/<int:grupo_id>/<int:pessoa_id>', methods=['GET'])
def obter_pessoa(grupo_id, pessoa_id):
    """Obter uma pessoa específica"""
    grupo_id, erro = validar_grupo(grupo_id)
    if erro:
        return jsonify({'error': erro}), 400 if "inválido" in erro else 404

    sql = "SELECT * FROM pessoas WHERE id = %s AND grupo_id = %s;"
    resultado, erro = execute_query(sql, [pessoa_id, grupo_id], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 500
    if not resultado:
        return jsonify({'error': 'Pessoa não encontrada'}), 404

    pessoa = dict(resultado)

    # Carregar extras
    sql_extras = "SELECT chave, valor FROM pessoas_extras WHERE pessoa_id = %s"
    extras, _ = execute_query(sql_extras, [pessoa_id])

    extras_obj = {}
    if extras:
        for e in extras:
            extras_obj[e['chave']] = e['valor']

    pessoa['extras'] = extras_obj

    return jsonify(pessoa), 200

@app.route('/api/pessoas/<int:grupo_id>', methods=['POST'])
def criar_pessoa(grupo_id):
    """Criar nova pessoa"""
    grupo_id, erro = validar_grupo(grupo_id)
    if erro:
        return jsonify({'error': erro}), 400 if "inválido" in erro else 404

    data = request.get_json()
    nome = data.get('nome')

    if not nome:
        return jsonify({'error': 'Nome é obrigatório'}), 400

    sql = """
        INSERT INTO pessoas (grupo_id, nome, idade, cargo, setor, situacao, risco, epi, observacoes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING *;
    """

    resultado, erro = execute_query(sql, [
        grupo_id,
        nome,
        data.get('idade'),
        data.get('cargo'),
        data.get('setor'),
        data.get('situacao'),
        data.get('risco'),
        data.get('epi'),
        data.get('observacoes')
    ], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 400

    pessoa = dict(resultado)

    # Inserir extras
    extras = data.get('extras', {})
    if extras:
        for chave, valor in extras.items():
            sql_extra = """
                INSERT INTO pessoas_extras (pessoa_id, chave, valor)
                VALUES (%s, %s, %s)
            """
            execute_query(sql_extra, [pessoa['id'], chave, valor])
        pessoa['extras'] = extras
    else:
        pessoa['extras'] = {}

    return jsonify(pessoa), 201

@app.route('/api/pessoas/<int:grupo_id>/<int:pessoa_id>', methods=['PUT'])
def atualizar_pessoa(grupo_id, pessoa_id):
    """Atualizar uma pessoa"""
    grupo_id, erro = validar_grupo(grupo_id)
    if erro:
        return jsonify({'error': erro}), 400 if "inválido" in erro else 404

    # Validar que pessoa pertence ao grupo
    sql_verificar = "SELECT id FROM pessoas WHERE id = %s AND grupo_id = %s"
    verificar, erro = execute_query(sql_verificar, [pessoa_id, grupo_id], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 500
    if not verificar:
        return jsonify({'error': 'Pessoa não encontrada'}), 404

    data = request.get_json()

    sql = """
        UPDATE pessoas
        SET
            nome = COALESCE(%s, nome),
            idade = COALESCE(%s, idade),
            cargo = COALESCE(%s, cargo),
            setor = COALESCE(%s, setor),
            situacao = COALESCE(%s, situacao),
            risco = COALESCE(%s, risco),
            epi = COALESCE(%s, epi),
            observacoes = COALESCE(%s, observacoes),
            atualizado_em = NOW()
        WHERE id = %s AND grupo_id = %s
        RETURNING *;
    """

    resultado, erro = execute_query(sql, [
        data.get('nome'),
        data.get('idade'),
        data.get('cargo'),
        data.get('setor'),
        data.get('situacao'),
        data.get('risco'),
        data.get('epi'),
        data.get('observacoes'),
        pessoa_id,
        grupo_id
    ], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 400

    pessoa = dict(resultado)

    # Atualizar extras
    if 'extras' in data:
        # Deletar extras antigos
        execute_query("DELETE FROM pessoas_extras WHERE pessoa_id = %s", [pessoa_id])

        # Inserir novos
        extras = data['extras']
        if extras:
            for chave, valor in extras.items():
                sql_extra = """
                    INSERT INTO pessoas_extras (pessoa_id, chave, valor)
                    VALUES (%s, %s, %s)
                """
                execute_query(sql_extra, [pessoa_id, chave, valor])

        pessoa['extras'] = extras

    return jsonify(pessoa), 200

@app.route('/api/pessoas/<int:grupo_id>/<int:pessoa_id>', methods=['DELETE'])
def deletar_pessoa(grupo_id, pessoa_id):
    """Deletar uma pessoa"""
    grupo_id, erro = validar_grupo(grupo_id)
    if erro:
        return jsonify({'error': erro}), 400 if "inválido" in erro else 404

    sql = "DELETE FROM pessoas WHERE id = %s AND grupo_id = %s RETURNING id;"
    resultado, erro = execute_query(sql, [pessoa_id, grupo_id], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 500
    if not resultado:
        return jsonify({'error': 'Pessoa não encontrada'}), 404

    return jsonify({'success': True, 'id': resultado['id']}), 200

# =====================================================
# ROTAS: LANÇAMENTOS DIÁRIOS
# =====================================================

@app.route('/api/lancamentos/<int:grupo_id>', methods=['GET'])
def listar_lancamentos(grupo_id):
    """Listar lançamentos de um grupo"""
    grupo_id, erro = validar_grupo(grupo_id)
    if erro:
        return jsonify({'error': erro}), 400 if "inválido" in erro else 404

    pessoa_id = request.args.get('pessoaId')

    if pessoa_id:
        sql = """
            SELECT * FROM lancamento_diario
            WHERE grupo_id = %s AND pessoa_id = %s
            ORDER BY criado_em DESC;
        """
        lancamentos, erro = execute_query(sql, [grupo_id, int(pessoa_id)])
    else:
        sql = """
            SELECT * FROM lancamento_diario
            WHERE grupo_id = %s
            ORDER BY criado_em DESC;
        """
        lancamentos, erro = execute_query(sql, [grupo_id])

    if erro:
        return jsonify({'error': erro}), 500

    lancamentos = [dict(l) for l in lancamentos] if lancamentos else []
    return jsonify(lancamentos), 200

@app.route('/api/lancamentos/<int:grupo_id>/<int:lancamento_id>', methods=['GET'])
def obter_lancamento(grupo_id, lancamento_id):
    """Obter um lançamento específico"""
    grupo_id, erro = validar_grupo(grupo_id)
    if erro:
        return jsonify({'error': erro}), 400 if "inválido" in erro else 404

    sql = "SELECT * FROM lancamento_diario WHERE id = %s AND grupo_id = %s;"
    resultado, erro = execute_query(sql, [lancamento_id, grupo_id], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 500
    if not resultado:
        return jsonify({'error': 'Lançamento não encontrado'}), 404

    return jsonify(dict(resultado)), 200

@app.route('/api/lancamentos/<int:grupo_id>', methods=['POST'])
def criar_lancamento(grupo_id):
    """Criar novo lançamento"""
    grupo_id, erro = validar_grupo(grupo_id)
    if erro:
        return jsonify({'error': erro}), 400 if "inválido" in erro else 404

    data = request.get_json()
    texto = data.get('texto')

    if not texto:
        return jsonify({'error': 'Texto é obrigatório'}), 400

    pessoa_id = data.get('pessoaId')

    # Se pessoa_id foi fornecido, validar que pertence ao grupo
    if pessoa_id:
        sql_verificar = "SELECT id FROM pessoas WHERE id = %s AND grupo_id = %s"
        verificar, erro = execute_query(sql_verificar, [pessoa_id, grupo_id], fetch_one=True)
        if not verificar:
            return jsonify({'error': 'Pessoa não pertence ao grupo'}), 400

    sql = """
        INSERT INTO lancamento_diario (grupo_id, pessoa_id, titulo, texto)
        VALUES (%s, %s, %s, %s)
        RETURNING *;
    """

    resultado, erro = execute_query(sql, [
        grupo_id,
        pessoa_id or None,
        data.get('titulo'),
        texto
    ], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 400

    return jsonify(dict(resultado)), 201

@app.route('/api/lancamentos/<int:grupo_id>/<int:lancamento_id>', methods=['DELETE'])
def deletar_lancamento(grupo_id, lancamento_id):
    """Deletar um lançamento"""
    grupo_id, erro = validar_grupo(grupo_id)
    if erro:
        return jsonify({'error': erro}), 400 if "inválido" in erro else 404

    sql = "DELETE FROM lancamento_diario WHERE id = %s AND grupo_id = %s RETURNING id;"
    resultado, erro = execute_query(sql, [lancamento_id, grupo_id], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 500
    if not resultado:
        return jsonify({'error': 'Lançamento não encontrado'}), 404

    return jsonify({'success': True}), 200

# =====================================================
# ROTAS: REGRAS
# =====================================================

@app.route('/api/regras/<int:grupo_id>', methods=['GET'])
def obter_regras(grupo_id):
    """Obter regras de um grupo"""
    grupo_id, erro = validar_grupo(grupo_id)
    if erro:
        return jsonify({'error': erro}), 400 if "inválido" in erro else 404

    sql = "SELECT codigo_regras FROM regras_julgamento WHERE grupo_id = %s;"
    resultado, erro = execute_query(sql, [grupo_id], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 500

    regras = resultado['codigo_regras'] if resultado else ''
    return jsonify({'regras': regras}), 200

@app.route('/api/regras/<int:grupo_id>', methods=['POST'])
def salvar_regras(grupo_id):
    """Salvar regras de um grupo"""
    grupo_id, erro = validar_grupo(grupo_id)
    if erro:
        return jsonify({'error': erro}), 400 if "inválido" in erro else 404

    data = request.get_json()
    regras = data.get('regras')

    if not regras:
        return jsonify({'error': 'Código de regras é obrigatório'}), 400

    sql = """
        INSERT INTO regras_julgamento (grupo_id, codigo_regras)
        VALUES (%s, %s)
        ON CONFLICT (grupo_id) DO UPDATE SET
            codigo_regras = %s,
            atualizado_em = NOW()
        RETURNING *;
    """

    resultado, erro = execute_query(sql, [grupo_id, regras, regras], fetch_one=True)

    if erro:
        return jsonify({'error': erro}), 400

    return jsonify(dict(resultado)), 200

# =====================================================
# ERROR HANDLING
# =====================================================

@app.errorhandler(404)
def nao_encontrado(e):
    return jsonify({'error': 'Recurso não encontrado'}), 404

@app.errorhandler(500)
def erro_servidor(e):
    print(traceback.format_exc())
    return jsonify({'error': 'Erro interno do servidor'}), 500

# =====================================================
# HEALTH CHECK
# =====================================================

@app.route('/health', methods=['GET'])
def health():
    """Verificar saúde do servidor"""
    sql = "SELECT 1"
    _, erro = execute_query(sql)

    if erro:
        return jsonify({'status': 'error', 'message': erro}), 500

    return jsonify({'status': 'ok'}), 200

# =====================================================
# INICIAR SERVIDOR
# =====================================================

if __name__ == '__main__':
    PORT = int(os.getenv('PORT', 3000))
    DEBUG = os.getenv('NODE_ENV', 'development') == 'development'

    print(f"✓ Servidor rodando em http://localhost:{PORT}")
    print(f"  Banco de dados: postgresql://{DB_CONFIG['user']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")

    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
