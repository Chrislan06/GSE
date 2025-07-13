/**
 * Product Form JavaScript
 * Gerencia a funcionalidade do formulário de produtos
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elementos do formulário
    const stockInput = document.getElementById('id_stock');
    const minStockInput = document.getElementById('id_min_stock');
    const preview = document.getElementById('stock-preview');
    const previewCurrentStock = document.getElementById('preview-current-stock');
    const previewMinStock = document.getElementById('preview-min-stock');
    const previewStatus = document.getElementById('preview-status');
    
    // Verificar se os elementos existem
    if (!stockInput || !minStockInput) {
        console.warn('Elementos do formulário de estoque não encontrados');
        return;
    }
    
    /**
     * Atualiza o preview do status de estoque
     */
    function updatePreview() {
        const stock = parseInt(stockInput.value) || 0;
        const minStock = parseInt(minStockInput.value) || 0;
        
        if (stock > 0 || minStock > 0) {
            previewCurrentStock.textContent = stock;
            previewMinStock.textContent = minStock;
            
            let status = 'Normal';
            let statusClass = 'normal';
            
            if (stock === 0) {
                status = 'Sem Estoque';
                statusClass = 'zero';
            } else if (stock <= minStock) {
                status = 'Estoque Baixo';
                statusClass = 'low';
            }
            
            previewStatus.textContent = status;
            previewStatus.className = `value ${statusClass}`;
            preview.style.display = 'block';
        } else {
            preview.style.display = 'none';
        }
    }
    
    /**
     * Valida o campo de estoque
     */
    function validateStock() {
        const stock = parseInt(this.value) || 0;
        if (stock < 0) {
            this.setCustomValidity('O estoque não pode ser negativo');
        } else {
            this.setCustomValidity('');
        }
    }
    
    /**
     * Valida o campo de estoque mínimo
     */
    function validateMinStock() {
        const minStock = parseInt(this.value) || 0;
        if (minStock < 0) {
            this.setCustomValidity('O estoque mínimo não pode ser negativo');
        } else {
            this.setCustomValidity('');
        }
    }
    
    // Event listeners
    stockInput.addEventListener('input', updatePreview);
    minStockInput.addEventListener('input', updatePreview);
    stockInput.addEventListener('input', validateStock);
    minStockInput.addEventListener('input', validateMinStock);
    
    // Inicializar preview
    updatePreview();
}); 