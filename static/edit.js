/**
 * Forensic Document Refinement Module
 * Orchestrates manual and AI-driven document updates.
 */

window.toggleEditor = function() {
    const modal = document.getElementById('editorModal');
    if (!modal) return;
    modal.classList.toggle('hidden');
    modal.classList.toggle('flex');
};

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
    const contentArea = document.getElementById('editorContent');
    const content = contentArea.value;
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
        } else {
            const err = await response.json();
            showToast(err.detail || 'Update failed', 'error');
        }
    } catch (error) {
        showToast('Network error during refinement', 'error');
        console.error(error);
    }
};

window.refineCurrentContent = async function() {
    const editor = document.getElementById('editorContent');
    const promptInput = document.getElementById('editorPrompt');
    if (!editor || !promptInput) return;

    const rawText = editor.value;
    const prompt = promptInput.value;
    
    if (!rawText.trim()) return showToast('Input required for refinement', 'info');

    showToast(prompt ? `Neural Engine: Executing '${prompt}'...` : 'Neural Engine: Refining current workspace...', 'info');

    try {
        const response = await fetch('/api/refine', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ 
                text: rawText,
                prompt: prompt 
            })
        });

        if (!response.ok) throw new Error('Neural refinement failed');
        
        const data = await response.json();
        const refined = data.refined_text;
        
        // Absolute DOM Override Sequence
        setTimeout(() => {
            try {
                const targets = document.querySelectorAll('#editorContent');
                targets.forEach(el => {
                    el.readOnly = false;
                    el.disabled = false;
                    el.focus();
                    
                    window.getSelection().removeAllRanges();
                    el.setSelectionRange(0, el.value.length);
                    
                    // Native RangeText Swap
                    el.setRangeText(refined, 0, el.value.length, 'end');

                    if (el.value !== refined) {
                        document.execCommand('insertText', false, refined);
                    }

                    if (el.value !== refined) {
                        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
                        nativeSetter.call(el, refined);
                        el.innerText = refined;
                    }

                    const len = el.value.length;
                    el.setSelectionRange(len, len);
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));

                    el.classList.add('ring-4', 'ring-blue-500/20', 'border-blue-500');
                    setTimeout(() => el.classList.remove('ring-4', 'ring-blue-500/20', 'border-blue-500'), 800);
                });

                // Clear prompt on success
                promptInput.value = '';
                showToast('Neural Refinement applied to workspace.', 'success');
            } catch (err) {
                console.error('Refinement Injection Error:', err);
                editor.value = refined;
            }
        }, 150);
    } catch (error) {
        showToast(error.message, 'error');
    }
};

// Escape Key Listener for Modals
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const editor = document.getElementById('editorModal');
        const viewer = document.getElementById('viewer-modal');
        
        if (editor && !editor.classList.contains('hidden')) {
            window.toggleEditor();
        }
        if (viewer && !viewer.classList.contains('hidden')) {
            if (window.toggleViewer) window.toggleViewer();
            else {
                viewer.classList.add('hidden');
                viewer.classList.remove('flex');
            }
        }
    }
});
