/**
 * Stock Movement JavaScript
 * Gerencia a funcionalidade de movimentações de estoque
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elementos do formulário
    const movementType = document.getElementById('id_movement_type');
    const quantity = document.getElementById('id_quantity');
    const preview = document.getElementById('operation-preview');
    const previewOperation = document.getElementById('preview-operation');
    const previewNewStock = document.getElementById('preview-new-stock');
    
    // Obter estoque atual do elemento HTML
    const stockElement = document.querySelector('.current-stock .amount');
    const currentStock = stockElement ? parseInt(stockElement.textContent.trim()) || 0 : 0;
    
    // Verificar se os elementos existem
    if (!movementType || !quantity) {
        console.warn('Elementos do formulário de movimentação não encontrados');
        return;
    }
    
    /**
     * Atualiza o preview da operação
     */
    function updatePreview() {
        const type = movementType.value;
        const qty = parseInt(quantity.value) || 0;
        
        if (type && qty > 0) {
            let newStock = currentStock;
            let operation = '';
            
            switch(type) {
                case 'IN':
                    newStock = currentStock + qty;
                    operation = '+' + qty + ' (Entrada)';
                    break;
                case 'OUT':
                    newStock = currentStock - qty;
                    operation = '-' + qty + ' (Saída)';
                    break;
                case 'ADJUSTMENT':
                    newStock = qty;
                    operation = '=' + qty + ' (Ajuste)';
                    break;
            }
            
            if (previewOperation) {
                previewOperation.textContent = operation;
            }
            if (previewNewStock) {
                previewNewStock.textContent = newStock;
            }
            if (preview) {
                preview.style.display = 'block';
            }
        } else {
            if (preview) {
                preview.style.display = 'none';
            }
        }
    }
    
    /**
     * Valida a quantidade baseada no tipo de movimento
     */
    function validateQuantity() {
        const qty = parseInt(this.value) || 0;
        const type = movementType.value;
        
        if (type === 'OUT' && qty > currentStock) {
            this.setCustomValidity('Estoque insuficiente. Estoque atual: ' + currentStock);
        } else {
            this.setCustomValidity('');
        }
    }
    
    // Event listeners
    movementType.addEventListener('change', updatePreview);
    quantity.addEventListener('input', updatePreview);
    quantity.addEventListener('input', validateQuantity);
    
    // Inicializar preview
    updatePreview();
}); 