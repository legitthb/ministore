from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, request, url_for
import mysql.connector

from database import get_connection

vendas_bp = Blueprint('vendas', __name__, template_folder='templates')


def _buscar_opcoes(cursor):
    cursor.execute('SELECT id, nome FROM clientes ORDER BY nome')
    clientes = cursor.fetchall()
    cursor.execute('SELECT id, codigo, nome, preco FROM produtos ORDER BY nome')
    produtos = cursor.fetchall()
    return clientes, produtos


def _ler_dados_venda(cursor, form):
    cliente_raw = form.get('id_cliente', '').strip()
    try:
        id_cliente = int(cliente_raw)
    except (TypeError, ValueError):
        raise ValueError('Selecione um cliente para a venda.')

    cursor.execute('SELECT id FROM clientes WHERE id = %s', (id_cliente,))
    if not cursor.fetchone():
        raise ValueError('O cliente selecionado não foi encontrado.')

    ids_enviados = form.getlist('produto_id[]')
    quantidades_enviadas = form.getlist('quantidade[]')
    if len(ids_enviados) != len(quantidades_enviadas):
        raise ValueError('Confira os produtos e as quantidades informadas.')

    quantidades_por_produto = {}
    for produto_raw, quantidade_raw in zip(ids_enviados, quantidades_enviadas):
        produto_raw = produto_raw.strip()
        quantidade_raw = quantidade_raw.strip()
        if not produto_raw and not quantidade_raw:
            continue
        try:
            id_produto = int(produto_raw)
            quantidade = int(quantidade_raw)
        except (TypeError, ValueError):
            raise ValueError('Selecione um produto e informe uma quantidade inteira.')
        if quantidade <= 0:
            raise ValueError('A quantidade de cada produto deve ser maior que zero.')
        quantidades_por_produto[id_produto] = quantidades_por_produto.get(id_produto, 0) + quantidade

    if not quantidades_por_produto:
        raise ValueError('Adicione pelo menos um produto à venda.')

    placeholders = ', '.join(['%s'] * len(quantidades_por_produto))
    cursor.execute(
        f'SELECT id, codigo, nome, preco FROM produtos WHERE id IN ({placeholders})',
        tuple(quantidades_por_produto.keys()),
    )
    produtos_encontrados = {produto['id']: produto for produto in cursor.fetchall()}
    if len(produtos_encontrados) != len(quantidades_por_produto):
        raise ValueError('Um dos produtos selecionados não foi encontrado. Atualize a página e tente novamente.')

    itens = []
    total = Decimal('0.00')
    for id_produto, quantidade in quantidades_por_produto.items():
        produto = produtos_encontrados[id_produto]
        preco = Decimal(str(produto['preco']))
        subtotal = preco * quantidade
        itens.append({
            'id_produto': id_produto,
            'codigo': produto['codigo'],
            'nome': produto['nome'],
            'quantidade': quantidade,
            'preco_unitario': preco,
            'subtotal': subtotal,
        })
        total += subtotal

    return id_cliente, itens, total


def _itens_do_formulario(form):
    produtos = form.getlist('produto_id[]')
    quantidades = form.getlist('quantidade[]')
    return [
        {'produto_id': produto_id, 'quantidade': quantidade}
        for produto_id, quantidade in zip(produtos, quantidades)
    ]


def _gravar_itens(cursor, id_venda, itens):
    cursor.executemany(
        '''INSERT INTO itens_venda (id_venda, id_produto, quantidade, preco_unitario)
           VALUES (%s, %s, %s, %s)''',
        [
            (id_venda, item['id_produto'], item['quantidade'], item['preco_unitario'])
            for item in itens
        ],
    )


@vendas_bp.route('/vendas')
def listar():
    conn = None
    cursor = None
    vendas = []
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT v.id, v.data_venda, v.total, c.nome AS cliente_nome,
                   (SELECT COUNT(*) FROM itens_venda iv WHERE iv.id_venda = v.id) AS quantidade_itens
            FROM vendas v
            INNER JOIN clientes c ON c.id = v.id_cliente
            ORDER BY v.data_venda DESC, v.id DESC
        ''')
        vendas = cursor.fetchall()
    except mysql.connector.Error:
        flash('Não foi possível carregar as vendas. Verifique a conexão com o banco de dados.', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return render_template('lista_vendas.html', vendas=vendas)


@vendas_bp.route('/vendas/nova', methods=['GET', 'POST'])
def nova():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        clientes, produtos = _buscar_opcoes(cursor)

        if request.method == 'POST':
            try:
                id_cliente, itens, total = _ler_dados_venda(cursor, request.form)
                cursor.execute(
                    'INSERT INTO vendas (id_cliente, total) VALUES (%s, %s)',
                    (id_cliente, total),
                )
                id_venda = cursor.lastrowid
                _gravar_itens(cursor, id_venda, itens)
                conn.commit()
                flash('Venda registrada com sucesso!', 'success')
                return redirect(url_for('vendas.detalhes', id=id_venda))
            except ValueError as e:
                conn.rollback()
                flash(str(e), 'warning')
                form_data = request.form
                return render_template(
                    'form_venda.html', venda=None, itens_form=_itens_do_formulario(form_data),
                    clientes=clientes, produtos=produtos, form_data=form_data,
                )
            except mysql.connector.Error:
                conn.rollback()
                flash('Não foi possível registrar a venda. Confira os dados e tente novamente.', 'danger')
                return render_template('form_venda.html', venda=None, itens_form=[], clientes=clientes, produtos=produtos, form_data=request.form)

        if not clientes:
            flash('Cadastre pelo menos um cliente antes de registrar uma venda.', 'warning')
        if not produtos:
            flash('Cadastre pelo menos um produto antes de registrar uma venda.', 'warning')
        return render_template('form_venda.html', venda=None, itens_form=[], clientes=clientes, produtos=produtos, form_data={})
    except mysql.connector.Error:
        flash('Não foi possível abrir o formulário de venda.', 'danger')
        return redirect(url_for('vendas.listar'))
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@vendas_bp.route('/vendas/<int:id>')
def detalhes(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT v.id, v.id_cliente, v.data_venda, v.total, c.nome AS cliente_nome,
                   c.email AS cliente_email, c.telefone AS cliente_telefone
            FROM vendas v
            INNER JOIN clientes c ON c.id = v.id_cliente
            WHERE v.id = %s
        ''', (id,))
        venda = cursor.fetchone()
        if not venda:
            flash('Venda não encontrada.', 'warning')
            return redirect(url_for('vendas.listar'))

        cursor.execute('''
            SELECT iv.id, iv.id_produto, iv.quantidade, iv.preco_unitario,
                   (iv.quantidade * iv.preco_unitario) AS subtotal,
                   p.codigo AS produto_codigo, p.nome AS produto_nome
            FROM itens_venda iv
            INNER JOIN produtos p ON p.id = iv.id_produto
            WHERE iv.id_venda = %s
            ORDER BY p.nome
        ''', (id,))
        itens = cursor.fetchall()
        return render_template('detalhes_venda.html', venda=venda, itens=itens)
    except mysql.connector.Error:
        flash('Não foi possível carregar os detalhes da venda.', 'danger')
        return redirect(url_for('vendas.listar'))
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@vendas_bp.route('/vendas/<int:id>/editar', methods=['GET', 'POST'])
def editar(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('SELECT id, id_cliente, data_venda, total FROM vendas WHERE id = %s', (id,))
        venda = cursor.fetchone()
        if not venda:
            flash('Venda não encontrada.', 'warning')
            return redirect(url_for('vendas.listar'))

        cursor.execute('''
            SELECT id_produto, quantidade FROM itens_venda
            WHERE id_venda = %s ORDER BY id
        ''', (id,))
        itens_existentes = cursor.fetchall()
        clientes, produtos = _buscar_opcoes(cursor)

        if request.method == 'POST':
            try:
                id_cliente, itens, total = _ler_dados_venda(cursor, request.form)
                cursor.execute('UPDATE vendas SET id_cliente = %s, total = %s WHERE id = %s', (id_cliente, total, id))
                cursor.execute('DELETE FROM itens_venda WHERE id_venda = %s', (id,))
                _gravar_itens(cursor, id, itens)
                conn.commit()
                flash('Venda atualizada com sucesso!', 'success')
                return redirect(url_for('vendas.detalhes', id=id))
            except ValueError as e:
                conn.rollback()
                flash(str(e), 'warning')
                itens_form = _itens_do_formulario(request.form)
                venda['id_cliente'] = request.form.get('id_cliente', venda['id_cliente'])
                return render_template('form_venda.html', venda=venda, itens_form=itens_form, clientes=clientes, produtos=produtos, form_data=request.form)
            except mysql.connector.Error:
                conn.rollback()
                flash('Não foi possível atualizar a venda. Confira os dados e tente novamente.', 'danger')
                return render_template('form_venda.html', venda=venda, itens_form=itens_existentes, clientes=clientes, produtos=produtos, form_data={})

        return render_template('form_venda.html', venda=venda, itens_form=itens_existentes, clientes=clientes, produtos=produtos, form_data={})
    except mysql.connector.Error:
        if conn and conn.is_connected():
            conn.rollback()
        flash('Não foi possível carregar a venda para edição.', 'danger')
        return redirect(url_for('vendas.listar'))
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


@vendas_bp.route('/vendas/<int:id>/excluir', methods=['POST'])
def excluir(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM vendas WHERE id = %s', (id,))
        if not cursor.fetchone():
            flash('Venda não encontrada.', 'warning')
            return redirect(url_for('vendas.listar'))
        cursor.execute('DELETE FROM itens_venda WHERE id_venda = %s', (id,))
        cursor.execute('DELETE FROM vendas WHERE id = %s', (id,))
        conn.commit()
        flash('Venda excluída com sucesso!', 'success')
    except mysql.connector.Error:
        if conn and conn.is_connected():
            conn.rollback()
        flash('Não foi possível excluir a venda.', 'danger')
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
    return redirect(url_for('vendas.listar'))
