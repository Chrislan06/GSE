/**
 * Low Stock Alert JavaScript
 * Gerencia a funcionalidade de alertas de estoque baixo
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-refresh a cada 30 segundos
    setInterval(function() {
        location.reload();
    }, 30000);

    // Notificação de alertas
    showStockNotifications();
});

/**
 * Mostra notificações de alertas de estoque
 */
function showStockNotifications() {
    // Obter contadores dos elementos HTML
    const urgentElement = document.querySelector('.summary-card.urgent h3');
    const warningElement = document.querySelector('.summary-card.warning h3');
    
    if (urgentElement && warningElement) {
        const urgentCount = parseInt(urgentElement.textContent) || 0;
        const warningCount = parseInt(warningElement.textContent) || 0;
        
        if (urgentCount > 0 || warningCount > 0) {
            // Mostrar notificação se o navegador suportar
            if ('Notification' in window && Notification.permission === 'granted') {
                const message = `Você tem ${urgentCount} produtos sem estoque e ${warningCount} com estoque baixo.`;
                new Notification('Alertas de Estoque', {
                    body: message,
                    icon: '/static/img/alert-icon.png'
                });
            }
        }
    }
} 