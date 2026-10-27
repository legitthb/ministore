from flask import Blueprint, flash, render_template
import mysql.connector

from database import get_connection

dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')


@dashboard_bp.route('/')
def index():
    conn = None
    cursor = None
    totais = {'clientes': 0, 'categorias': 0, 'produtos': 0, 'vendas': 0}
    try:
        conn = get_connection()
        cursor = conn.cursor()
        for tabela in totais:
            cursor.execute(f'SELECT COUNT(*) FROM {tabela}')
            totais[tabela] = cursor.fetchone()[0]
    except mysql.connector.Error:
        flash('Não foi possível carregar todos os dados do painel. Verifique a conexão com o banco de dados.', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    return render_template('index.html', totais=totais)
