import os
import psycopg2
from dotenv import load_dotenv


load_dotenv()


def conectar():
    conexao = psycopg2.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )
    return conexao


def criar_banco_dados():
    conexao = conectar()
    cursor = conexao.cursor()

    script_db = """
    CREATE TABLE IF NOT EXISTS grupos (
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL UNIQUE,
        slug TEXT NOT NULL UNIQUE
    );

    CREATE TABLE IF NOT EXISTS historicos (
        id SERIAL PRIMARY KEY,
        data DATE NOT NULL,
        grupo_id INTEGER NOT NULL REFERENCES grupos (id) ON DELETE CASCADE,
        descricao TEXT NOT NULL
    );
"""
    cursor.execute(script_db)
    conexao.commit()
    cursor.close()
    conexao.close()

def inserir_dados_iniciais():
    conexao = conectar()
    cursor = conexao.cursor()
    script_db = """
    INSERT INTO grupos (nome, slug) VALUES
        ('RH', 'rh'),
        ('Financeiro', 'financeiro'),
        ('Marketing', 'marketing'),
        ('Produção', 'producao')
    ON CONFLICT (nome) DO NOTHING;
    """

    cursor.execute(script_db)
    conexao.commit()
    cursor.close()
    conexao.close()
