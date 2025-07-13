/**
 * Reports Dashboard JavaScript
 * Gerencia a funcionalidade do dashboard de relatórios
 */

document.addEventListener('DOMContentLoaded', function() {
    // Auto-refresh do dashboard a cada 60 segundos
    setInterval(function() {
        location.reload();
    }, 60000);

    // Animações de entrada
    animateCards();
});

/**
 * Anima os cards do dashboard com efeito de entrada
 */
function animateCards() {
    const cards = document.querySelectorAll('.stat-card, .report-card, .action-card');
    
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
} 