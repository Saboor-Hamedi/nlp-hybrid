/**
 * Neural Forensic Suite - Standalone Notification System
 * High-fidelity telemetry alerts with industrial aesthetics.
 */
window.showToast = function(message, type = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    // Prevent multiple instances - clear previous telemetry
    container.innerHTML = '';

    const toast = document.createElement('div');
    // Premium industrial styling
    toast.className = `pointer-events-auto px-5 py-3.5 rounded-[5px] shadow-2xl border theme-border theme-bg theme-text text-[9px] font-bold uppercase tracking-[0.2em] flex items-center gap-4 modal-enter min-w-[240px]`;
    
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-600',
        warning: 'bg-amber-500'
    };
    
    const dotColor = colors[type] || colors.info;
    
    toast.innerHTML = `
        <div class="relative flex items-center justify-center">
            <div class="w-2 h-2 rounded-full ${dotColor}"></div>
        </div>
        <div class="flex-1">${message}</div>
        <div class="w-[1px] h-4 theme-border border-l opacity-20"></div>
        <button onclick="this.parentElement.remove()" class="opacity-40 hover:opacity-100 transition-opacity">
            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12"></path></svg>
        </button>
    `;
    
    container.appendChild(toast);

    // Auto-remove with smooth transition
    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(20px)';
            toast.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            setTimeout(() => toast.remove(), 400);
        }
    }, 4500);
};
