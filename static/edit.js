/**
 * Forensic Document Refinement Module
 */
window.openEditor = function(docId = null, existingContent = '') {
    window.currentDocId = docId;
    const modal = document.getElementById('editorModal');
    if (!modal) return;
    
    const title = document.getElementById('editorTitle');
    const contentArea = document.getElementById('editorContent');
    
    title.innerText = docId ? `Refining Document #${docId}` : 'Injecting New Correlation';
    contentArea.value = existingContent;
    
    toggleEditor();
};

window.performUpdate = async function(docId) {
    const content = document.getElementById('editorContent').value;
    if (!content.trim()) return showToast('Content is required', 'error');

    try {
        const response = await fetch(`/api/docs/${docId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: content })
        });

        if (response.ok) {
            showToast('Correlation updated successfully', 'success');
            toggleEditor();

            // Surgical DOM Update
            const contentEl = document.getElementById(`doc-content-${docId}`);
            if (contentEl) {
                contentEl.innerText = content;
                contentEl.classList.add('text-blue-500');
                setTimeout(() => contentEl.classList.remove('text-blue-500'), 2000);
            }
            const card = document.querySelector(`[data-doc-id="${docId}"]`);
            const titleEl = card ? card.querySelector('h3, h2') : null;
            if (titleEl) {
                titleEl.innerText = content.substring(0, 120) + '...';
            }
        } else {
            const err = await response.json();
            showToast(err.detail || 'Update failed', 'error');
        }
    } catch (error) {
        showToast('Network error during refinement', 'error');
        console.error(error);
    }
};
