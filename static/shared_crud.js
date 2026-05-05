/**
 * Shared Forensic CRUD Utilities
 */
window.currentDocId = null;

window.toggleEditor = function() {
    const modal = document.getElementById('editorModal');
    if (!modal) return;
    const isHidden = modal.classList.contains('hidden');
    if (isHidden) {
        modal.classList.remove('hidden');
        modal.classList.add('flex');
    } else {
        modal.classList.add('hidden');
        modal.classList.remove('flex');
    }
};

window.showToast = function(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `fixed bottom-6 right-6 px-6 py-3 rounded-xl shadow-2xl z-[9999] transform translate-y-20 opacity-0 transition-all duration-300 font-bold text-[11px] uppercase tracking-widest border ${
        type === 'success' ? 'bg-green-500 text-white border-green-600' : 'bg-red-500 text-white border-red-600'
    }`;
    toast.innerHTML = message;
    document.body.appendChild(toast);
    requestAnimationFrame(() => {
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '1';
    });
    setTimeout(() => {
        toast.style.transform = 'translateY(20px)';
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
};

window.deleteDocument = async function(docId) {
    if (!confirm(`Are you sure you want to permanently purge Document #${docId}?`)) return;
    const card = document.querySelector(`[data-doc-id="${docId}"]`);
    if (card) card.style.opacity = '0.5';

    try {
        const response = await fetch(`/api/docs/${docId}`, { method: 'DELETE' });
        if (response.ok) {
            if (card) {
                card.style.transition = 'all 0.5s ease-out';
                card.style.transform = 'translateX(50px)';
                card.style.opacity = '0';
                setTimeout(() => card.remove(), 500);
            }
            showToast(`Document #${docId} purged.`, 'success');
        } else {
            throw new Error('Purge failed');
        }
    } catch (error) {
        if (card) card.style.opacity = '1';
        showToast(error.message, 'error');
    }
};

// Dispatcher for Commit button
window.saveDocument = function() {
    if (window.currentDocId) {
        if (window.performUpdate) window.performUpdate(window.currentDocId);
    } else {
        if (window.performInsert) window.performInsert();
    }
};
