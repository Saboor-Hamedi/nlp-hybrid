/**
 * Forensic Document Insertion Module
 */
window.performInsert = async function() {
    const content = document.getElementById('editorContent').value;
    if (!content.trim()) return showToast('Content is required', 'error');

    try {
        const response = await fetch('/api/docs', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });

        if (response.ok) {
            const data = await response.json();
            showToast('Document created', 'success');
            toggleEditor();

            // Fluid Prepend logic
            const container = document.querySelector('.space-y-4') || document.querySelector('.flex.flex-col.gap-4');
            if (container) {
                const newCard = document.createElement('div');
                newCard.className = 'theme-bg p-6 rounded-xl border theme-border border-blue-500/30 hover:border-blue-500 transition-all duration-500 group modal-enter';
                newCard.setAttribute('data-doc-id', data.id);
                newCard.innerHTML = `
                    <div class="flex items-start justify-between gap-6">
                        <div class="flex-1 min-w-0">
                            <div class="flex items-center gap-2.5 mb-3">
                                <span class="text-[9px] font-bold text-blue-600 bg-blue-500/10 px-2 py-0.5 rounded uppercase tracking-wide border border-blue-500/20">New Record</span>
                                <span class="text-[9px] font-medium theme-text-sec opacity-40">#${data.id}</span>
                            </div>
                            <h3 class="theme-text font-semibold text-sm mb-2 line-clamp-1 group-hover:text-blue-600 transition-colors">${content.substring(0, 120)}...</h3>
                            <p id="doc-content-${data.id}" class="text-xs theme-text-sec opacity-70 leading-relaxed line-clamp-2 mb-4 font-light">${content}</p>
                            <div class="flex items-center gap-4 mb-4">
                                <span class="text-[9px] font-bold text-yellow-600 uppercase tracking-widest opacity-60 italic">Analysis Pending...</span>
                            </div>
                        </div>
                    </div>
                `;
                container.prepend(newCard);
            }
        } else {
            const err = await response.json();
            showToast(err.detail || 'Insertion failed', 'error');
        }
    } catch (error) {
        showToast('Network error during injection', 'error');
        console.error(error);
    }
};
