import os
from datetime import datetime

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
from flask import Flask, abort, flash, redirect, render_template, request, url_for

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "chave-secreta-de-desenvolvimento")


# ---------------------------------------------------------------------------
# Configuração dos grupos
# ---------------------------------------------------------------------------

GRUPOS = {
    "grupo-1": {
        "nome": "Grupo 1",
        "turma": "1º Ano de Administração",
        "empresa": "Empresa Simulada 1",
        "database_env": "DATABASE_URL_GRUPO_1",
        "descricao": "Análise da empresa simulada desenvolvida pelo 1º Ano de Administração.",
    },
    "grupo-2": {
        "nome": "Grupo 2",
        "turma": "1º Ano de Administração",
        "empresa": "Empresa Simulada 2",
        "database_env": "DATABASE_URL_GRUPO_2",
        "descricao": "Análise da empresa simulada desenvolvida pelo 1º Ano de Administração.",
    },
    "grupo-3": {
        "nome": "Grupo 3",
        "turma": "2º Ano de Administração",
        "empresa": "Empresa Simulada 3",
        "database_env": "DATABASE_URL_GRUPO_3",
        "descricao": "Análise da empresa simulada desenvolvida pelo 2º Ano de Administração.",
    },
    "grupo-4": {
        "nome": "Grupo 4",
        "turma": "2º Ano de Administração",
        "empresa": "Empresa Simulada 4",
        "database_env": "DATABASE_URL_GRUPO_4",
        "descricao": "Análise da empresa simulada desenvolvida pelo 2º Ano de Administração.",
    },
}

SETORES = ["RH", "Marketing", "Finanças", "Produção"]

GRAUS_ORGANIZACAO = ["Excelente", "Bom", "Regular", "Precisa melhorar"]

PROFESSORES = [
    {"nome": "Rodrigo Gomes", "area": "Administração"},
    {"nome": "Murilo Mendes", "area": "Empreendedorismo"},
    {"nome": "Ricardo Varjão", "area": "Desenvolvimento de Sistemas"},
]


# ---------------------------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------------------------

def obter_grupo_ou_404(slug):
    grupo_config = GRUPOS.get(slug)
    if grupo_config is None:
        abort(404)
    return grupo_config


def obter_database_url(grupo_config):
    return os.getenv(grupo_config["database_env"])


def conectar_banco(database_url):
    return psycopg2.connect(database_url)


def criar_tabela_se_nao_existir(database_url):
    script_sql = """
    CREATE TABLE IF NOT EXISTS historicos (
        id SERIAL PRIMARY KEY,
        grupo VARCHAR(100) NOT NULL,
        turma_analisada VARCHAR(150) NOT NULL,
        empresa_simulada VARCHAR(150) NOT NULL,
        nome_estudante VARCHAR(150) NOT NULL,
        setor VARCHAR(50) NOT NULL,
        data_observacao DATE NOT NULL,
        descricao TEXT NOT NULL,
        pontos_positivos TEXT,
        pontos_melhoria TEXT,
        grau_organizacao VARCHAR(50) NOT NULL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    conexao = conectar_banco(database_url)
    try:
        with conexao.cursor() as cursor:
            cursor.execute(script_sql)
        conexao.commit()
    finally:
        conexao.close()


def salvar_historico(database_url, grupo_config, dados):
    script_sql = """
        INSERT INTO historicos (
            grupo, turma_analisada, empresa_simulada, nome_estudante, setor,
            data_observacao, descricao, pontos_positivos, pontos_melhoria,
            grau_organizacao
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    valores = (
        grupo_config["nome"],
        grupo_config["turma"],
        grupo_config["empresa"],
        dados["nome_estudante"],
        dados["setor"],
        dados["data_observacao"],
        dados["descricao"],
        dados["pontos_positivos"],
        dados["pontos_melhoria"],
        dados["grau_organizacao"],
    )

    conexao = conectar_banco(database_url)
    try:
        with conexao.cursor() as cursor:
            cursor.execute(script_sql, valores)
        conexao.commit()
    finally:
        conexao.close()


def listar_historicos(database_url):
    script_sql = """
        SELECT
            id, grupo, turma_analisada, empresa_simulada, nome_estudante,
            setor, data_observacao, descricao, pontos_positivos,
            pontos_melhoria, grau_organizacao, criado_em
        FROM historicos
        ORDER BY criado_em DESC
    """
    conexao = conectar_banco(database_url)
    try:
        with conexao.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute(script_sql)
            return cursor.fetchall()
    finally:
        conexao.close()


def validar_dados_formulario(form):
    campos_obrigatorios = {
        "nome_estudante": "Nome do estudante",
        "setor": "Setor analisado",
        "data_observacao": "Data da observação",
        "descricao": "Descrição da observação",
        "grau_organizacao": "Grau de organização",
    }

    erros = []
    dados = {}

    for campo, rotulo in campos_obrigatorios.items():
        valor = (form.get(campo) or "").strip()
        if not valor:
            erros.append(f"O campo '{rotulo}' é obrigatório.")
        dados[campo] = valor

    if dados["setor"] and dados["setor"] not in SETORES:
        erros.append("Setor analisado inválido.")

    if dados["grau_organizacao"] and dados["grau_organizacao"] not in GRAUS_ORGANIZACAO:
        erros.append("Grau de organização inválido.")

    if dados["data_observacao"]:
        try:
            datetime.strptime(dados["data_observacao"], "%Y-%m-%d")
        except ValueError:
            erros.append("Data da observação inválida.")

    dados["pontos_positivos"] = (form.get("pontos_positivos") or "").strip()
    dados["pontos_melhoria"] = (form.get("pontos_melhoria") or "").strip()

    return dados, erros


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        grupos=GRUPOS,
        setores=SETORES,
        professores=PROFESSORES,
    )


@app.route("/<grupo>")
def grupo_detalhe(grupo):
    grupo_config = obter_grupo_ou_404(grupo)
    return render_template(
        "grupo.html",
        slug=grupo,
        grupo=grupo_config,
        setores=SETORES,
    )


@app.route("/<grupo>/diario", methods=["GET", "POST"])
def diario(grupo):
    grupo_config = obter_grupo_ou_404(grupo)
    database_url = obter_database_url(grupo_config)

    if not database_url:
        flash(
            f"O banco de dados do {grupo_config['nome']} ainda não foi configurado. "
            "Verifique a variável correspondente no arquivo .env.",
            "erro",
        )
        return render_template(
            "diario.html",
            slug=grupo,
            grupo=grupo_config,
            setores=SETORES,
            graus=GRAUS_ORGANIZACAO,
            dados={},
        )

    if request.method == "POST":
        dados, erros = validar_dados_formulario(request.form)

        if erros:
            for erro in erros:
                flash(erro, "erro")
            return render_template(
                "diario.html",
                slug=grupo,
                grupo=grupo_config,
                setores=SETORES,
                graus=GRAUS_ORGANIZACAO,
                dados=dados,
            )

        try:
            criar_tabela_se_nao_existir(database_url)
            salvar_historico(database_url, grupo_config, dados)
        except psycopg2.OperationalError:
            flash(
                "Não foi possível conectar ao banco de dados deste grupo. "
                "Tente novamente mais tarde ou avise o professor responsável.",
                "erro",
            )
            return render_template(
                "diario.html",
                slug=grupo,
                grupo=grupo_config,
                setores=SETORES,
                graus=GRAUS_ORGANIZACAO,
                dados=dados,
            )
        except Exception:
            flash(
                "Ocorreu um erro ao salvar o registro. Tente novamente.",
                "erro",
            )
            return render_template(
                "diario.html",
                slug=grupo,
                grupo=grupo_config,
                setores=SETORES,
                graus=GRAUS_ORGANIZACAO,
                dados=dados,
            )

        flash("Registro salvo com sucesso na missão de análise!", "sucesso")
        return redirect(url_for("registros", grupo=grupo))

    return render_template(
        "diario.html",
        slug=grupo,
        grupo=grupo_config,
        setores=SETORES,
        graus=GRAUS_ORGANIZACAO,
        dados={},
    )


@app.route("/<grupo>/registros")
def registros(grupo):
    grupo_config = obter_grupo_ou_404(grupo)
    database_url = obter_database_url(grupo_config)

    historicos = []

    if not database_url:
        flash(
            f"O banco de dados do {grupo_config['nome']} ainda não foi configurado. "
            "Verifique a variável correspondente no arquivo .env.",
            "erro",
        )
    else:
        try:
            criar_tabela_se_nao_existir(database_url)
            historicos = listar_historicos(database_url)
        except psycopg2.OperationalError:
            flash(
                "Não foi possível conectar ao banco de dados deste grupo. "
                "Tente novamente mais tarde ou avise o professor responsável.",
                "erro",
            )
        except Exception:
            flash("Ocorreu um erro ao buscar os registros.", "erro")

    return render_template(
        "registros.html",
        slug=grupo,
        grupo=grupo_config,
        historicos=historicos,
    )


if __name__ == "__main__":
    app.run(debug=True)
