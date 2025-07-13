/**
 * ============================================================================
 * FUNCIONALIDADES ESPECÍFICAS PARA PRODUTOS
 * ============================================================================
 */

// Módulo de Produtos
const ProductsModule = {
    // Inicialização
    init: function() {
        this.setupEventListeners();
        this.initializeFeatures();
    },

    // Configurar event listeners
    setupEventListeners: function() {
        // Busca em tempo real
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.addEventListener('input', GSE.debounce(this.handleSearch.bind(this), 300));
        }

        // Filtros
        const filterSelects = document.querySelectorAll('.filter-select');
        filterSelects.forEach(select => {
            select.addEventListener('change', this.handleFilter.bind(this));
        });

        // Preview de movimentação de estoque
        const movementForm = document.querySelector('.movement-form');
        if (movementForm) {
            this.setupMovementPreview();
        }

        // Validação de estoque
        const quantityInputs = document.querySelectorAll('input[name="quantity"]');
        quantityInputs.forEach(input => {
            input.addEventListener('input', this.validateStock.bind(this));
        });

        // Auto-refresh para alertas
        const alertsPage = document.querySelector('.alerts-container');
        if (alertsPage) {
            GSE.autoRefresh(30000); // 30 segundos
        }
    },

    // Inicializar funcionalidades
    initializeFeatures: function() {
        // Animar linhas da tabela
        this.animateTableRows();
        
        // Configurar notificações
        this.setupNotifications();
        
        // Inicializar tooltips
        this.initializeTooltips();
    },

    // Busca em tempo real
    handleSearch: function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const productRows = document.querySelectorAll('.product-row');
        
        productRows.forEach(row => {
            const productName = row.querySelector('td:first-child strong').textContent.toLowerCase();
            const productDescription = row.querySelector('.text-muted')?.textContent.toLowerCase() || '';
            const category = row.querySelector('.badge')?.textContent.toLowerCase() || '';
            
            const matches = productName.includes(searchTerm) || 
                           productDescription.includes(searchTerm) || 
                           category.includes(searchTerm);
            
            row.style.display = matches ? 'table-row' : 'none';
        });

        // Atualizar contador de resultados
        this.updateSearchResults();
    },

    // Atualizar contador de resultados
    updateSearchResults: function() {
        const visibleRows = document.querySelectorAll('.product-row[style*="table-row"], .product-row:not([style*="none"])');
        const resultsCounter = document.getElementById('results-counter');
        
        if (resultsCounter) {
            resultsCounter.textContent = `${visibleRows.length} produto(s) encontrado(s)`;
        }
    },

    // Filtros
    handleFilter: function(e) {
        const filterType = e.target.name;
        const filterValue = e.target.value;
        const productRows = document.querySelectorAll('.product-row');
        
        productRows.forEach(row => {
            let show = true;
            
            switch (filterType) {
                case 'category':
                    break;
                    
                case 'stock_status':
                    const stockElement = row.querySelector('.stock-amount');
                    if (stockElement) {
                        const stock = parseInt(stockElement.textContent);
                        switch (filterValue) {
                            case 'normal':
                                show = stock > 0 && !stockElement.classList.contains('low');
                                break;
                            case 'low':
                                show = stockElement.classList.contains('low');
                                break;
                            case 'out':
                                show = stock === 0;
                                break;
                        }
                    }
                    break;
            }
            
            if (filterType !== 'category') {
                row.style.display = show ? 'table-row' : 'none';
            }
        });

        this.updateSearchResults();
    },

    // Preview de movimentação de estoque
    setupMovementPreview: function() {
        const movementType = document.getElementById('id_movement_type');
        const quantity = document.getElementById('id_quantity');
        const preview = document.getElementById('operation-preview');
        const previewOperation = document.getElementById('preview-operation');
        const previewNewStock = document.getElementById('preview-new-stock');
        
        if (!movementType || !quantity || !preview) return;
        
        // Obter estoque atual do elemento HTML
        const stockElement = document.querySelector('.current-stock .amount');
        const currentStock = stockElement ? parseInt(stockElement.textContent.trim()) || 0 : 0;
        
        const updatePreview = () => {
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
                
                if (previewOperation) previewOperation.textContent = operation;
                if (previewNewStock) previewNewStock.textContent = newStock;
                preview.style.display = 'block';
            } else {
                preview.style.display = 'none';
            }
        };
        
        movementType.addEventListener('change', updatePreview);
        quantity.addEventListener('input', updatePreview);
    },

    // Validação de estoque
    validateStock: function(e) {
        const quantity = parseInt(e.target.value) || 0;
        const movementType = document.querySelector('#id_movement_type')?.value;
        const stockElement = document.querySelector('.current-stock .amount');
        const currentStock = stockElement ? parseInt(stockElement.textContent.trim()) || 0 : 0;
        
        if (movementType === 'OUT' && quantity > currentStock) {
            e.target.setCustomValidity(`Estoque insuficiente. Estoque atual: ${currentStock}`);
        } else {
            e.target.setCustomValidity('');
        }
    },

    // Animar linhas da tabela
    animateTableRows: function() {
        const rows = document.querySelectorAll('.product-row');
        rows.forEach((row, index) => {
            row.style.opacity = '0';
            row.style.transform = 'translateY(10px)';
            row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            
            setTimeout(() => {
                row.style.opacity = '1';
                row.style.transform = 'translateY(0)';
            }, index * 50);
        });
    },

    // Configurar notificações
    setupNotifications: function() {
        // Notificação de alertas de estoque
        const urgentElement = document.querySelector('.summary-card.urgent h3');
        const warningElement = document.querySelector('.summary-card.warning h3');
        
        if (urgentElement && warningElement) {
            const urgentCount = parseInt(urgentElement.textContent) || 0;
            const warningCount = parseInt(warningElement.textContent) || 0;
            
            if (urgentCount > 0 || warningCount > 0) {
                this.showStockAlert(urgentCount, warningCount);
            }
        }
    },

    // Mostrar alerta de estoque
    showStockAlert: function(urgentCount, warningCount) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const message = `Você tem ${urgentCount} produtos sem estoque e ${warningCount} com estoque baixo.`;
            new Notification('Alertas de Estoque', {
                body: message,
                icon: '/static/img/alert-icon.png'
            });
        }
    },

    // Inicializar tooltips
    initializeTooltips: function() {
        const tooltipElements = document.querySelectorAll('[data-tooltip]');
        tooltipElements.forEach(element => {
            element.addEventListener('mouseenter', (e) => {
                this.showTooltip(e.target, e.target.dataset.tooltip);
            });
            
            element.addEventListener('mouseleave', () => {
                this.hideTooltip();
            });
        });
    },

    // Mostrar tooltip
    showTooltip: function(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'product-tooltip';
        tooltip.textContent = text;
        tooltip.style.cssText = `
            position: absolute;
            background: #333;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            z-index: 1000;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.3s;
            max-width: 200px;
            word-wrap: break-word;
        `;
        
        document.body.appendChild(tooltip);
        
        const rect = element.getBoundingClientRect();
        tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
        tooltip.style.top = rect.top - tooltip.offsetHeight - 8 + 'px';
        
        setTimeout(() => tooltip.style.opacity = '1', 10);
        
        element._tooltip = tooltip;
    },

    // Esconder tooltip
    hideTooltip: function() {
        const tooltip = document.querySelector('.product-tooltip');
        if (tooltip) {
            tooltip.remove();
        }
    },

    // Carregar dados do produto via AJAX
    loadProductData: function(productId) {
        return GSE.fetchData(`/api/produto/${productId}/`)
            .then(data => {
                this.updateProductDisplay(data);
                return data;
            });
    },

    // Atualizar exibição do produto
    updateProductDisplay: function(data) {
        // Atualizar informações do produto
        const nameElement = document.querySelector('.product-name');
        if (nameElement) nameElement.textContent = data.name;
        
        const descriptionElement = document.querySelector('.product-description');
        if (descriptionElement) descriptionElement.textContent = data.description;
        
        const priceElement = document.querySelector('.product-price');
        if (priceElement) priceElement.textContent = GSE.formatCurrency(data.price);
        
        const stockElement = document.querySelector('.product-stock');
        if (stockElement) {
            stockElement.textContent = data.stock;
            stockElement.className = `product-stock ${data.stock_status.toLowerCase()}`;
        }
    },

    // Exportar dados da tabela
    exportData: function(format = 'csv') {
        const products = Array.from(document.querySelectorAll('.product-row')).map(row => {
            const cells = row.querySelectorAll('td');
            return {
                name: cells[0]?.querySelector('strong')?.textContent || '',
                description: cells[0]?.querySelector('.text-muted')?.textContent || '',
                category: cells[1]?.querySelector('.badge')?.textContent || cells[1]?.textContent || '',
                price: cells[2]?.textContent || '',
                stock: cells[3]?.textContent || '',
                minStock: cells[4]?.textContent || '',
                status: cells[5]?.textContent || ''
            };
        });

        if (format === 'csv') {
            this.exportToCSV(products);
        } else if (format === 'json') {
            this.exportToJSON(products);
        }
    },

    // Exportar para CSV
    exportToCSV: function(data) {
        const headers = ['Nome', 'Descrição', 'Categoria', 'Preço', 'Estoque', 'Estoque Mínimo', 'Status'];
        const csvContent = [
            headers.join(','),
            ...data.map(row => [
                `"${row.name}"`,
                `"${row.description}"`,
                `"${row.category}"`,
                `"${row.price}"`,
                `"${row.stock}"`,
                `"${row.minStock}"`,
                `"${row.status}"`
            ].join(','))
        ].join('\n');

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'produtos.csv';
        link.click();
    },

    // Exportar para JSON
    exportToJSON: function(data) {
        const jsonContent = JSON.stringify(data, null, 2);
        const blob = new Blob([jsonContent], { type: 'application/json' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = 'produtos.json';
        link.click();
    }
};

// Inicializar módulo quando o DOM estiver pronto
GSE.onReady(function() {
    ProductsModule.init();
});

// Exportar para uso global
window.ProductsModule = ProductsModule; 