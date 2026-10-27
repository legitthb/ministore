from decimal import Decimal, InvalidOperation

from flask import Flask

from categorias.routes import categorias_bp
from clientes.routes import clientes_bp
from dashboard.routes import dashboard_bp
from produtos.routes import produtos_bp
from vendas.routes import vendas_bp

app = Flask(__name__)
app.secret_key = 'ministore-secret-key-2026'

app.register_blueprint(dashboard_bp)
app.register_blueprint(clientes_bp)
app.register_blueprint(categorias_bp)
app.register_blueprint(produtos_bp)
app.register_blueprint(vendas_bp)


@app.template_filter('brl')
def formatar_brl(valor):
    """Formata valores monetários no padrão brasileiro."""
    try:
        valor_decimal = Decimal(str(valor if valor is not None else 0))
    except (InvalidOperation, ValueError, TypeError):
        valor_decimal = Decimal('0.00')
    formatado = f'{valor_decimal:,.2f}'
    return formatado.replace(',', 'X').replace('.', ',').replace('X', '.')


if __name__ == '__main__':
    app.run(debug=True)
