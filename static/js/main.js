// main.js

// confirmação de exclusão — já está nos templates via onsubmit
// este arquivo é reservado para funcionalidades futuras

// destacar item do menu ativo
document.addEventListener('DOMContentLoaded', function() {
    const links = document.querySelectorAll('nav a');
    links.forEach(link => {
        if (link.href === window.location.href) {
            link.classList.add('ativo');
        }
    });

    // formulário de venda: adicionar/remover produtos
    const addButton = document.getElementById('adicionar-item');
    const itemsContainer = document.getElementById('itens-venda');
    const itemTemplate = document.getElementById('modelo-item-venda');

    if (addButton && itemsContainer && itemTemplate) {
        addButton.addEventListener('click', function() {
            itemsContainer.appendChild(itemTemplate.content.cloneNode(true));
        });

        itemsContainer.addEventListener('click', function(event) {
            const removeButton = event.target.closest('.remover-item');
            if (!removeButton) return;
            const rows = itemsContainer.querySelectorAll('.item-venda');
            const row = removeButton.closest('.item-venda');
            if (rows.length <= 1) {
                row.querySelector('select').value = '';
                row.querySelector('input').value = '1';
            } else {
                row.remove();
            }
        });
    }
});
