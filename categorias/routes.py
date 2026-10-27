from flask import Blueprint, flash, redirect, render_template, request, url_for
import mysql.connector

from database import get_connection

categorias_bp = Blueprint('categorias', __name__, template_folder='templates')


@categorias_bp.route('/categorias')
def listar():
    conn = None
    cursor = None
    categorias = []
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, nome, descricao FROM categorias ORDER BY nome')
        categorias = cursor.fetchall()
    except mysql.connector.Error:
        flash('Não foi possível carregar as categorias. Verifique a conexão com o banco de dados.', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()

    return render_template('lista_categorias.html', categorias=categorias)


@categorias_bp.route('/categorias/nova', methods=['GET', 'POST'])
def nova():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        if not nome:
            flash('Informe o nome da categoria.', 'warning')
            return render_template('form_categoria.html', categoria=None)

        conn = None
        cursor = None
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO categorias (nome, descricao) VALUES (%s, %s)',
                (nome, descricao or None),
            )
            conn.commit()
            flash('Categoria cadastrada com sucesso!', 'success')
            return redirect(url_for('categorias.listar'))
        except mysql.connector.Error:
            if conn and conn.is_connected():
                conn.rollback()
            flash('Não foi possível cadastrar a categoria. Verifique os dados e tente novamente.', 'danger')
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    return render_template('form_categoria.html', categoria=None)


@categorias_bp.route('/categorias/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            nome = request.form.get('nome', '').strip()
            descricao = request.form.get('descricao', '').strip()
            if not nome:
                flash('Informe o nome da categoria.', 'warning')
                cursor.execute('SELECT id, nome, descricao FROM categorias WHERE id = %s', (id,))
                categoria = cursor.fetchone()
                if not categoria:
                    flash('Categoria não encontrada.', 'danger')
                    return redirect(url_for('categorias.listar'))
                return render_template('form_categoria.html', categoria=categoria)

            cursor.execute(
                'UPDATE categorias SET nome = %s, descricao = %s WHERE id = %s',
                (nome, descricao or None, id),
            )
            conn.commit()
            if cursor.rowcount:
                flash('Categoria atualizada com sucesso!', 'success')
            else:
                flash('Categoria não encontrada ou nenhum dado foi alterado.', 'info')
            return redirect(url_for('categorias.listar'))

        cursor.execute('SELECT id, nome, descricao FROM categorias WHERE id = %s', (id,))
        categoria = cursor.fetchone()
        if not categoria:
            flash('Categoria não encontrada.', 'warning')
            return redirect(url_for('categorias.listar'))
        return render_template('form_categoria.html', categoria=categoria)

    except mysql.connector.Error:
        if conn and conn.is_connected():
            conn.rollback()
        flash('Não foi possível processar a categoria. Tente novamente.', 'danger')
        return redirect(url_for('categorias.listar'))
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@categorias_bp.route('/categorias/<int:id>/excluir', methods=['POST'])
def excluir(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM categorias WHERE id = %s', (id,))
        conn.commit()
        if cursor.rowcount:
            flash('Categoria excluída com sucesso!', 'success')
        else:
            flash('Categoria não encontrada.', 'warning')
    except mysql.connector.IntegrityError:
        if conn and conn.is_connected():
            conn.rollback()
        flash('Esta categoria não pode ser excluída porque está vinculada a um ou mais produtos.', 'warning')
    except mysql.connector.Error:
        if conn and conn.is_connected():
            conn.rollback()
        flash('Não foi possível excluir a categoria. Tente novamente.', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return redirect(url_for('categorias.listar'))
