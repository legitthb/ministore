from decimal import Decimal, InvalidOperation

from flask import Blueprint, flash, redirect, render_template, request, url_for
import mysql.connector

from database import get_connection

produtos_bp = Blueprint('produtos', __name__, template_folder='templates')


def _buscar_categorias(cursor):
    cursor.execute('SELECT id, nome FROM categorias ORDER BY nome')
    return cursor.fetchall()


def _validar_produto(form, cursor):
    codigo = form.get('codigo', '').strip()
    nome = form.get('nome', '').strip()
    descricao = form.get('descricao', '').strip()
    categoria_raw = form.get('id_categoria', '').strip()
    preco_raw = form.get('preco', '').strip().replace(',', '.')

    if not codigo or not nome or not preco_raw:
        raise ValueError('Preencha o código, o nome e o preço do produto.')

    try:
        preco = Decimal(preco_raw)
    except InvalidOperation:
        raise ValueError('Informe um preço válido.')
    if not preco.is_finite() or preco <= 0:
        raise ValueError('O preço deve ser maior que zero.')

    id_categoria = None
    if categoria_raw:
        try:
            id_categoria = int(categoria_raw)
        except ValueError:
            raise ValueError('Selecione uma categoria válida.')
        cursor.execute('SELECT id FROM categorias WHERE id = %s', (id_categoria,))
        if not cursor.fetchone():
            raise ValueError('A categoria selecionada não existe.')

    return codigo, nome, descricao or None, preco, id_categoria


@produtos_bp.route('/produtos')
def listar():
    conn = None
    cursor = None
    produtos = []
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT p.id, p.codigo, p.nome, p.descricao, p.preco,
                   p.id_categoria, c.nome AS categoria_nome
            FROM produtos p
            LEFT JOIN categorias c ON c.id = p.id_categoria
            ORDER BY p.nome
        ''')
        produtos = cursor.fetchall()
    except mysql.connector.Error:
        flash('Não foi possível carregar os produtos. Verifique a conexão com o banco de dados.', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return render_template('lista_produtos.html', produtos=produtos)


@produtos_bp.route('/produtos/novo', methods=['GET', 'POST'])
def novo():
    conn = None
    cursor = None
    categorias = []
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        categorias = _buscar_categorias(cursor)

        if request.method == 'POST':
            try:
                codigo, nome, descricao, preco, id_categoria = _validar_produto(request.form, cursor)
                cursor.execute('''
                    INSERT INTO produtos (codigo, nome, descricao, preco, id_categoria)
                    VALUES (%s, %s, %s, %s, %s)
                ''', (codigo, nome, descricao, preco, id_categoria))
                conn.commit()
                flash('Produto cadastrado com sucesso!', 'success')
                return redirect(url_for('produtos.listar'))
            except ValueError as e:
                flash(str(e), 'warning')
            except mysql.connector.IntegrityError:
                conn.rollback()
                flash('Não foi possível cadastrar o produto. Verifique os dados informados.', 'danger')
            except mysql.connector.Error:
                conn.rollback()
                flash('Ocorreu um erro ao cadastrar o produto.', 'danger')
            return render_template('form_produto.html', produto=dict(request.form), categorias=categorias)

    except mysql.connector.Error:
        flash('Não foi possível carregar o formulário de produto.', 'danger')
        return redirect(url_for('produtos.listar'))
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return render_template('form_produto.html', produto=None, categorias=categorias)


@produtos_bp.route('/produtos/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        categorias = _buscar_categorias(cursor)

        if request.method == 'POST':
            try:
                codigo, nome, descricao, preco, id_categoria = _validar_produto(request.form, cursor)
                cursor.execute('''
                    UPDATE produtos
                    SET codigo = %s, nome = %s, descricao = %s, preco = %s, id_categoria = %s
                    WHERE id = %s
                ''', (codigo, nome, descricao, preco, id_categoria, id))
                conn.commit()
                if cursor.rowcount:
                    flash('Produto atualizado com sucesso!', 'success')
                else:
                    flash('Produto salvo. Nenhuma alteração foi detectada.', 'info')
                return redirect(url_for('produtos.listar'))
            except ValueError as e:
                flash(str(e), 'warning')
                produto = dict(request.form)
                produto['id'] = id
                return render_template('form_produto.html', produto=produto, categorias=categorias)
            except mysql.connector.Error:
                conn.rollback()
                flash('Não foi possível atualizar o produto. Verifique os dados e tente novamente.', 'danger')
                produto = dict(request.form)
                produto['id'] = id
                return render_template('form_produto.html', produto=produto, categorias=categorias)

        cursor.execute('''
            SELECT id, codigo, nome, descricao, preco, id_categoria
            FROM produtos WHERE id = %s
        ''', (id,))
        produto = cursor.fetchone()
        if not produto:
            flash('Produto não encontrado.', 'warning')
            return redirect(url_for('produtos.listar'))
        return render_template('form_produto.html', produto=produto, categorias=categorias)
    except mysql.connector.Error:
        if conn and conn.is_connected():
            conn.rollback()
        flash('Não foi possível processar o produto.', 'danger')
        return redirect(url_for('produtos.listar'))
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@produtos_bp.route('/produtos/<int:id>/excluir', methods=['POST'])
def excluir(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM produtos WHERE id = %s', (id,))
        conn.commit()
        if cursor.rowcount:
            flash('Produto excluído com sucesso!', 'success')
        else:
            flash('Produto não encontrado.', 'warning')
    except mysql.connector.IntegrityError:
        if conn and conn.is_connected():
            conn.rollback()
        flash('Este produto não pode ser excluído porque faz parte de uma venda registrada.', 'warning')
    except mysql.connector.Error:
        if conn and conn.is_connected():
            conn.rollback()
        flash('Não foi possível excluir o produto.', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return redirect(url_for('produtos.listar'))
