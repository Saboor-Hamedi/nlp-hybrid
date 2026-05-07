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
            showToast('Registry Updated', 'success');
            toggleEditor();

            // 🚀 NUCLEAR SYNC ENGINE
            console.group(`[Neural Sync] Record #${docId}`);
            
            const possibleSelectors = [
                `[data-forensic-id="${docId}"]`,
                `#forensic-card-${docId}`,
                `#card-${docId}`
            ];
            
            let foundCount = 0;
            possibleSelectors.forEach(sel => {
                const targets = document.querySelectorAll(sel);
                targets.forEach(target => {
                    foundCount++;
                    const body = target.querySelector('.forensic-content-body') || 
                                 target.querySelector('.markdown-body') || 
                                 target;
                                 
                    if (typeof marked !== 'undefined') {
                        body.innerHTML = marked.parse(content);
                    } else {
                        body.innerText = content;
                    }
                    target.classList.add('ring-4', 'ring-blue-600', 'bg-blue-600/10', 'animate-pulse');
                    setTimeout(() => target.classList.remove('ring-4', 'ring-blue-600', 'bg-blue-600/10', 'animate-pulse'), 4000);
                });
            });

            console.groupEnd();
            
            // Auto-refresh the inspector if it matches the current doc
            const inspectorTitle = document.getElementById('inspector-content')?.innerText;
            if (inspectorTitle && inspectorTitle.includes(`#${docId}`)) {
                if (window.inspectDocument) window.inspectDocument(docId);
            }
            
        } else {
            const err = await response.json();
            showToast(err.detail || 'Update failed', 'error');
        }
    } catch (error) {
        showToast('Network error during sync', 'error');
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

    if (!rawText.trim() && !prompt.trim()) return showToast('Instruction required.', 'info');

    if (activity) activity.classList.remove('hidden');
    if (hint) hint.classList.add('hidden');
    promptInput.disabled = true;
    editor.classList.add('ghost-shimmer', 'opacity-50');

    try {
        const response = await fetch('/api/refine', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ text: rawText, prompt: prompt })
        });

        if (!response.ok) throw new Error('Neural refinement failed');
        const data = await response.json();
        editor.value = data.refined_text;
        promptInput.value = '';
    } catch (error) {
        showToast(error.message, 'error');
    } finally {
        if (activity) activity.classList.add('hidden');
        if (hint) hint.classList.remove('hidden');
        promptInput.disabled = false;
        editor.classList.remove('ghost-shimmer', 'opacity-50');
    }
};
