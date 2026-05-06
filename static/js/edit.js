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
    const submitBtn = document.getElementById('editorSubmitBtn');
    
    title.innerText = docId ? `Refining Document #${docId}` : 'Injecting New Correlation';
    if (submitBtn) submitBtn.innerText = docId ? 'Edit' : 'Archive';
    
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
            showToast('Document updated', 'success');
            toggleEditor();

            // Surgical DOM Update
            console.log(`[Neural Forge] Refinement complete for #${docId}. Syncing UI...`);
            
            // 1. Update snippets
            const snippets = document.querySelectorAll(`.forensic-snippet-sync-${docId}`);
            snippets.forEach(el => {
                el.innerText = content;
                el.classList.add('text-blue-500', 'font-bold');
                setTimeout(() => el.classList.remove('text-blue-500', 'font-bold'), 2000);
            });

            // 2. Update card containers (flash effect)
            const cards = document.querySelectorAll(`[id="forensic-card-${docId}"]`);
            cards.forEach(card => {
                card.classList.add('border-blue-500', 'ring-4', 'ring-blue-500/20');
                setTimeout(() => card.classList.remove('border-blue-500', 'ring-4', 'ring-blue-500/20'), 2000);
            });

            // 3. Update main search content
            const mainContent = document.getElementById(`doc-content-${docId}`);
            if (mainContent) {
                mainContent.innerText = content;
                mainContent.classList.add('text-blue-500');
                setTimeout(() => mainContent.classList.remove('text-blue-500'), 2000);
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
    
    const activity = document.getElementById('neuralActivity');
    const hint = document.getElementById('neuralPromptHint');

    if (!rawText.trim() && !prompt.trim()) return showToast('Neural Engine: Instruction or context required.', 'info');

    // Enter Neural Loading State
    if (activity) activity.classList.remove('hidden');
    if (hint) hint.classList.add('hidden');
    promptInput.disabled = true;
    editor.classList.add('ghost-shimmer', 'opacity-50');
    const originalPlaceholder = editor.placeholder;
    editor.placeholder = " [ NEURAL SYNTHESIS IN PROGRESS... ]";

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
        
        // Exit Neural Loading State
        if (activity) activity.classList.add('hidden');
        if (hint) hint.classList.remove('hidden');
        promptInput.disabled = false;
        editor.classList.remove('ghost-shimmer', 'opacity-50');
        editor.placeholder = originalPlaceholder;
        
        // Absolute DOM Override Sequence
        setTimeout(() => {
            try {
                const targets = document.querySelectorAll('#editorContent');
                targets.forEach(el => {
                    // Simple, robust override for blank canvas generation
                    if (!el.value.trim()) {
                        el.value = refined;
                    } else {
                        // Surgical range replacement for existing content
                        el.setSelectionRange(0, el.value.length);
                        el.setRangeText(refined, 0, el.value.length, 'end');
                    }
                    
                    el.dispatchEvent(new Event('input', { bubbles: true }));
                    el.dispatchEvent(new Event('change', { bubbles: true }));

                    el.classList.add('ring-4', 'ring-blue-500/30', 'border-blue-500');
                    setTimeout(() => el.classList.remove('ring-4', 'ring-blue-500/30', 'border-blue-500'), 1000);
                });

                promptInput.value = '';
            } catch (err) {
                console.error('Refinement Injection Error:', err);
                editor.value = refined;
            }
        }, 150);
    } catch (error) {
        // Emergency Reset on Failure
        if (activity) activity.classList.add('hidden');
        if (hint) hint.classList.remove('hidden');
        promptInput.disabled = false;
        editor.classList.remove('ghost-shimmer', 'opacity-50');
        
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
