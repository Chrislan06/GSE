
// Utilitários
const GSE = {
    // Formatação de números
    formatCurrency: function(value) {
        return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
        }).format(value);
    },

    // Formatação de datas
    formatDate: function(date) {
        return new Intl.DateTimeFormat('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    },

    // Validação de formulários
    validateForm: function(formElement) {
        const inputs = formElement.querySelectorAll('input[required], select[required], textarea[required]');
        let isValid = true;

        inputs.forEach(input => {
            if (!input.value.trim()) {
                this.showFieldError(input, 'Este campo é obrigatório');
                isValid = false;
            } else {
                this.clearFieldError(input);
            }
        });

        return isValid;
    },

    // Exibir erro de campo
    showFieldError: function(field, message) {
        this.clearFieldError(field);
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
        field.classList.add('error');
    },

    // Limpar erro de campo
    clearFieldError: function(field) {
        const existingError = field.parentNode.querySelector('.error-message');
        if (existingError) {
            existingError.remove();
        }
        field.classList.remove('error');
    },

    // Notificações
    showNotification: function(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.textContent = message;
        
        // Adicionar ao topo da página
        document.body.insertBefore(notification, document.body.firstChild);
        
        // Remover após 5 segundos
        setTimeout(() => {
            notification.remove();
        }, 5000);
    },

    // Confirmação de ações
    confirmAction: function(message, callback) {
        if (confirm(message)) {
            callback();
        }
    },

    // Debounce para otimização de performance
    debounce: function(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Throttle para otimização de performance
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Carregamento de dados via AJAX
    fetchData: function(url, options = {}) {
        const defaultOptions = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };

        const finalOptions = { ...defaultOptions, ...options };

        return fetch(url, finalOptions)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .catch(error => {
                console.error('Erro na requisição:', error);
                this.showNotification('Erro ao carregar dados', 'danger');
                throw error;
            });
    },

    // Atualização de elementos da interface
    updateElement: function(selector, content) {
        const element = document.querySelector(selector);
        if (element) {
            element.innerHTML = content;
        }
    },

    // Toggle de visibilidade
    toggleElement: function(selector) {
        const element = document.querySelector(selector);
        if (element) {
            element.style.display = element.style.display === 'none' ? 'block' : 'none';
        }
    },

    // Scroll suave
    smoothScroll: function(target, duration = 300) {
        const targetElement = typeof target === 'string' ? document.querySelector(target) : target;
        if (!targetElement) return;

        const targetPosition = targetElement.offsetTop;
        const startPosition = window.pageYOffset;
        const distance = targetPosition - startPosition;
        let startTime = null;

        function animation(currentTime) {
            if (startTime === null) startTime = currentTime;
            const timeElapsed = currentTime - startTime;
            const run = ease(timeElapsed, startPosition, distance, duration);
            window.scrollTo(0, run);
            if (timeElapsed < duration) requestAnimationFrame(animation);
        }

        function ease(t, b, c, d) {
            t /= d / 2;
            if (t < 1) return c / 2 * t * t + b;
            t--;
            return -c / 2 * (t * (t - 2) - 1) + b;
        }

        requestAnimationFrame(animation);
    },

    // Local Storage utilities
    storage: {
        set: function(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
            } catch (e) {
                console.error('Erro ao salvar no localStorage:', e);
            }
        },

        get: function(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (e) {
                console.error('Erro ao ler do localStorage:', e);
                return defaultValue;
            }
        },

        remove: function(key) {
            try {
                localStorage.removeItem(key);
            } catch (e) {
                console.error('Erro ao remover do localStorage:', e);
            }
        }
    },

    // Event listeners utilitários
    onReady: function(callback) {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', callback);
        } else {
            callback();
        }
    },

    // Auto-refresh
    autoRefresh: function(interval = 30000) {
        setInterval(() => {
            location.reload();
        }, interval);
    }
};

// Inicialização quando o DOM estiver pronto
GSE.onReady(function() {
    // Configurar listeners globais
    setupGlobalListeners();
    
    // Inicializar funcionalidades comuns
    initializeCommonFeatures();
});

// Configurar listeners globais
function setupGlobalListeners() {
    // Listener para formulários
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.classList.contains('needs-validation')) {
            if (!GSE.validateForm(form)) {
                e.preventDefault();
                e.stopPropagation();
            }
        }
    });

    // Listener para confirmações de exclusão
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('confirm-delete')) {
            e.preventDefault();
            const message = e.target.dataset.confirmMessage || 'Tem certeza que deseja excluir este item?';
            const href = e.target.href;
            
            GSE.confirmAction(message, () => {
                window.location.href = href;
            });
        }
    });

    // Listener para tooltips
    document.addEventListener('mouseenter', function(e) {
        if (e.target.dataset.tooltip) {
            showTooltip(e.target, e.target.dataset.tooltip);
        }
    });

    document.addEventListener('mouseleave', function(e) {
        if (e.target.dataset.tooltip) {
            hideTooltip();
        }
    });
}

// Inicializar funcionalidades comuns
function initializeCommonFeatures() {
    // Auto-hide para alertas
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Animações de entrada
    const animatedElements = document.querySelectorAll('.fade-in');
    animatedElements.forEach((element, index) => {
        setTimeout(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        }, index * 100);
    });
}

// Função para mostrar tooltip
function showTooltip(element, text) {
    const tooltip = document.createElement('div');
    tooltip.className = 'tooltip';
    tooltip.textContent = text;
    tooltip.style.cssText = `
        position: absolute;
        background: #333;
        color: white;
        padding: 5px 10px;
        border-radius: 4px;
        font-size: 12px;
        z-index: 1000;
        pointer-events: none;
        opacity: 0;
        transition: opacity 0.3s;
    `;
    
    document.body.appendChild(tooltip);
    
    const rect = element.getBoundingClientRect();
    tooltip.style.left = rect.left + (rect.width / 2) - (tooltip.offsetWidth / 2) + 'px';
    tooltip.style.top = rect.top - tooltip.offsetHeight - 5 + 'px';
    
    setTimeout(() => tooltip.style.opacity = '1', 10);
    
    element._tooltip = tooltip;
}

// Função para esconder tooltip
function hideTooltip() {
    const tooltip = document.querySelector('.tooltip');
    if (tooltip) {
        tooltip.remove();
    }
}

// Exportar para uso global
window.GSE = GSE; 