
# app.py
from flask import Flask
from clientes.routes import clientes_bp
from dashboard.routes import dashboard_bp
from categorias.routes import categorias_bp

app = Flask(__name__)
app.secret_key = 'ministore-secret-key-2026'

# Registrar os Blueprints
app.register_blueprint(clientes_bp)
app.register_blueprint(dashboard_bp)
app.register_blueprint(categorias_bp)

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host="0.0.0.0", port=80, debug=True)
