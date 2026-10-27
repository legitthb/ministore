// Funcionalidades comuns da MiniStore.
document.addEventListener('DOMContentLoaded', function () {
    // Destaca a seção correspondente à rota atual.
    const currentPath = window.location.pathname.replace(/\/$/, '') || '/';
    document.querySelectorAll('nav a').forEach(function (link) {
        const linkPath = new URL(link.href, window.location.origin).pathname.replace(/\/$/, '') || '/';
        if (linkPath === currentPath || (linkPath !== '/' && currentPath.startsWith(linkPath + '/'))) {
            link.classList.add('ativo');
            link.setAttribute('aria-current', 'page');
        }
    });

    // Permite adicionar/remover produtos no formulário de venda.
    const addButton = document.getElementById('adicionar-item');
    const itemsContainer = document.getElementById('itens-venda');
    const itemTemplate = document.getElementById('modelo-item-venda');

    if (addButton && itemsContainer && itemTemplate) {
        addButton.addEventListener('click', function () {
            itemsContainer.appendChild(itemTemplate.content.cloneNode(true));
            const selects = itemsContainer.querySelectorAll('.produto-select');
            if (selects.length) selects[selects.length - 1].focus();
        });

        itemsContainer.addEventListener('click', function (event) {
            const removeButton = event.target.closest('.remover-item');
            if (!removeButton) return;

            const rows = itemsContainer.querySelectorAll('.sale-item-row');
            const row = removeButton.closest('.sale-item-row');
            if (rows.length <= 1) {
                const select = row.querySelector('.produto-select');
                const quantity = row.querySelector('.quantidade-input');
                if (select) select.value = '';
                if (quantity) quantity.value = '1';
            } else if (row) {
                row.remove();
            }
        });
    }
});
