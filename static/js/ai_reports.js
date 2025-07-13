/**
 * JavaScript para o Gerador de Relatórios com IA
 */

document.addEventListener('DOMContentLoaded', function() {
    // Elementos do DOM
    const formatCards = document.querySelectorAll('.format-card');
    const selectedFormatInput = document.getElementById('selectedFormat');
    const previewBtn = document.getElementById('previewBtn');
    const generateBtn = document.getElementById('generateBtn');
    const loading = document.getElementById('loading');
    const previewContainer = document.getElementById('previewContainer');
    const previewContent = document.getElementById('previewContent');
    const aiReportForm = document.getElementById('aiReportForm');

    // Seleção de formato
    formatCards.forEach(card => {
        card.addEventListener('click', function() {
            // Remover seleção anterior
            formatCards.forEach(c => c.classList.remove('selected'));
            
            // Selecionar o card clicado
            this.classList.add('selected');
            
            // Atualizar input hidden
            const format = this.dataset.format;
            selectedFormatInput.value = format;
            
            // Feedback visual
            showNotification(`Formato selecionado: ${format.toUpperCase()}`, 'info');
        });
    });

    // Selecionar XLSX por padrão
    if (formatCards.length > 0) {
        // Encontrar o card XLSX e selecioná-lo
        const xlsxCard = Array.from(formatCards).find(card => card.dataset.format === 'xlsx');
        if (xlsxCard) {
            xlsxCard.click();
        } else {
            // Fallback para o primeiro card se XLSX não for encontrado
            formatCards[0].click();
        }
    }

    // Prévia dos insights
    previewBtn.addEventListener('click', function() {
        generatePreview();
    });

    // Geração do relatório
    aiReportForm.addEventListener('submit', function(e) {
        e.preventDefault();
        generateReport();
    });

    /**
     * Gera prévia dos insights
     */
    function generatePreview() {
        showLoading(true);
        
        const formData = new FormData(aiReportForm);
        formData.append('action', 'preview');
        
        fetch('/relatorios/ia/preview/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            showLoading(false);
            
            if (data.error) {
                showNotification(data.error, 'error');
                return;
            }
            
            // Exibir prévia
            displayPreview(data);
            
        })
        .catch(error => {
            showLoading(false);
            console.error('Erro ao gerar prévia:', error);
            showNotification('Erro ao gerar prévia dos insights', 'error');
        });
    }

    /**
     * Gera relatório completo
     */
    function generateReport() {
        showLoading(true);
        
        const formData = new FormData(aiReportForm);
        
        fetch('/relatorios/ia/gerar/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        })
        .then(response => {
            showLoading(false);
            
            if (!response.ok) {
                throw new Error('Erro na geração do relatório');
            }
            
            // Verificar se é um arquivo para download
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/')) {
                // É um arquivo para download
                return response.blob();
            } else {
                // É uma resposta JSON com erro
                return response.json();
            }
        })
        .then(data => {
            if (data instanceof Blob) {
                // Download do arquivo
                downloadFile(data);
                showNotification('Relatório gerado com sucesso!', 'success');
            } else {
                // Erro
                showNotification(data.error || 'Erro ao gerar relatório', 'error');
            }
        })
        .catch(error => {
            showLoading(false);
            console.error('Erro ao gerar relatório:', error);
            showNotification('Erro ao gerar relatório', 'error');
        });
    }

    /**
     * Exibe a prévia dos insights
     */
    function displayPreview(data) {
        const format = selectedFormatInput.value;
        const summary = data.summary;
        
        let previewText = `# Prévia dos Insights - ${format.toUpperCase()}\n\n`;
        
        // Adicionar resumo
        previewText += `## Resumo Executivo\n`;
        previewText += `- Total de Produtos: ${summary.total_products}\n`;
        previewText += `- Total de Categorias: ${summary.total_categories}\n`;
        previewText += `- Produtos com Estoque Baixo: ${summary.low_stock_products}\n`;
        previewText += `- Produtos Sem Estoque: ${summary.out_of_stock_products}\n`;
        previewText += `- Total de Movimentações: ${summary.total_movements}\n\n`;
        
        // Adicionar insights da IA
        previewText += `## Análise e Insights\n\n`;
        previewText += data.insights;
        
        // Status da IA
        if (data.ai_enabled) {
            previewText += `\n\n---\n*Insights gerados por IA*`;
        } else {
            previewText += `\n\n---\n*Análise básica (IA não configurada)*`;
        }
        
        // Exibir no container
        previewContent.textContent = previewText;
        previewContainer.style.display = 'block';
        
        // Scroll para a prévia
        previewContainer.scrollIntoView({ behavior: 'smooth' });
    }

    /**
     * Faz download do arquivo gerado
     */
    function downloadFile(blob) {
        const format = selectedFormatInput.value;
        const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
        const filename = `relatorio_estoque_${timestamp}.${format}`;
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }

    /**
     * Mostra/esconde loading
     */
    function showLoading(show) {
        if (show) {
            loading.style.display = 'block';
            previewBtn.disabled = true;
            generateBtn.disabled = true;
        } else {
            loading.style.display = 'none';
            previewBtn.disabled = false;
            generateBtn.disabled = false;
        }
    }

    /**
     * Esconde a prévia
     */
    window.hidePreview = function() {
        previewContainer.style.display = 'none';
    };

    /**
     * Obtém o token CSRF
     */
    function getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }

    /**
     * Mostra notificação
     */
    function showNotification(message, type = 'info') {
        // Criar elemento de notificação
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Estilos da notificação
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'error' ? '#f8d7da' : type === 'success' ? '#d4edda' : '#d1ecf1'};
            color: ${type === 'error' ? '#721c24' : type === 'success' ? '#155724' : '#0c5460'};
            border: 1px solid ${type === 'error' ? '#f5c6cb' : type === 'success' ? '#c3e6cb' : '#bee5eb'};
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            max-width: 400px;
            animation: slideIn 0.3s ease;
        `;
        
        // Adicionar ao DOM
        document.body.appendChild(notification);
        
        // Remover automaticamente após 5 segundos
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    // Adicionar estilos CSS para animação
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from {
                transform: translateX(100%);
                opacity: 0;
            }
            to {
                transform: translateX(0);
                opacity: 1;
            }
        }
        
        .notification-content {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .notification-close {
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
            margin-left: 10px;
            opacity: 0.7;
        }
        
        .notification-close:hover {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);

    // Validação de datas
    const startDateInput = document.getElementById('start_date');
    const endDateInput = document.getElementById('end_date');

    startDateInput.addEventListener('change', validateDates);
    endDateInput.addEventListener('change', validateDates);

    function validateDates() {
        const startDate = startDateInput.value;
        const endDate = endDateInput.value;
        
        if (startDate && endDate && startDate > endDate) {
            showNotification('A data inicial não pode ser posterior à data final', 'error');
            endDateInput.value = '';
        }
    }

    // Configurar data padrão (últimos 30 dias)
    if (!startDateInput.value) {
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        startDateInput.value = thirtyDaysAgo.toISOString().split('T')[0];
    }

    if (!endDateInput.value) {
        const today = new Date();
        endDateInput.value = today.toISOString().split('T')[0];
    }
}); 