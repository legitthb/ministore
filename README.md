# MiniStore

Sistema web didático de gerenciamento de loja desenvolvido com Flask e MySQL/MariaDB.

## Pré-requisitos

- Python 3.x
- MySQL ou MariaDB em execução
- Usuário do banco configurado no arquivo `database.py`

## Instalação

1. Crie e ative um ambiente virtual:

   ```bash
   python -m venv venv
   # Windows: venv\Scripts\activate
   # Linux/macOS: source venv/bin/activate
   ```

2. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

3. Confira as credenciais de conexão em `database.py` e `setup.py`. O usuário configurado precisa ter permissão para criar tabelas e, na primeira configuração, o banco de dados.

4. Crie as tabelas:

   ```bash
   python setup.py
   ```

5. Inicie o sistema:

   ```bash
   python app.py
   ```

6. Acesse `http://127.0.0.1:5000`.

## Módulos

| Módulo | Funcionalidades |
| --- | --- |
| Dashboard | Totais de clientes, categorias, produtos e vendas e atalhos para cadastros |
| Clientes | Listagem, cadastro, edição e exclusão |
| Categorias | Listagem, cadastro, edição e exclusão, com aviso quando a categoria estiver vinculada a produtos |
| Produtos | Listagem, cadastro, edição e exclusão, com categoria opcional |
| Vendas | Registro com vários produtos, cálculo automático do total, consulta de detalhes, edição e exclusão |

## Estrutura principal

```text
ministore-main/
├── app.py
├── database.py
├── setup.py
├── categorias/
├── clientes/
├── dashboard/
├── produtos/
├── vendas/
├── templates/
└── static/
    ├── css/style.css
    └── js/main.js
```
