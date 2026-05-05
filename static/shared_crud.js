/**
 * Shared CRUD Orchestration
 * Unified lifecycle management for forensic document actions.
 */

window.currentDocId = null;

// Global dispatcher for forensic actions
window.openViewer = async function(id) {
    try {
        const response = await fetch(`/api/docs/${id}`);
        if (!response.ok) throw new Error('Forensic retrieval failed');
        const data = await response.json();

        // Populate Viewer Modal
        document.getElementById('viewerTitle').innerText = `Document Inspection: #${id}`;
        document.getElementById('viewerBody').innerText = data.content;
        
        // Handle Thematic Labels
        const ldaLabel = document.getElementById('viewerLdaLabel');
        const bertLabel = document.getElementById('viewerBertLabel');
        
        ldaLabel.innerText = data.lda_topic_label || 'N/A';
        bertLabel.innerText = data.bert_topic_label || 'N/A';

        // Handle Keywords
        const ldaList = document.getElementById('viewerLdaKeywords');
        const bertList = document.getElementById('viewerBertKeywords');
        
        ldaList.innerHTML = (data.lda_keywords || []).map(kw => 
            `<span class="px-2 py-0.5 rounded theme-bg-sec theme-text-sec text-[10px] border theme-border">${kw}</span>`
        ).join('');
        
        bertList.innerHTML = (data.bert_keywords || []).map(kw => 
            `<span class="px-2 py-0.5 rounded theme-bg-sec theme-text-sec text-[10px] border theme-border">${kw}</span>`
        ).join('');

        toggleViewer();

        // Trigger Neural Insight (RAG) for the current document
        const insightContent = document.getElementById('viewerInsightContent');
        const insightStatus = document.getElementById('viewerInsightStatus');
        
        insightContent.innerText = "Analyzing forensic signatures...";
        insightStatus.innerText = "Processing...";

        try {
            const synthResponse = await fetch('/api/synthesis', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ 
                    query: "Analyze the significance and primary themes of this forensic record.", 
                    context_docs: [data] 
                })
            });
            const synthData = await synthResponse.json();
            insightContent.innerText = synthData.synthesis;
            insightStatus.innerText = "Analysis Complete";
        } catch (error) {
            insightContent.innerText = "Neural synthesis temporarily unavailable.";
            insightStatus.innerText = "Analysis Suspended";
        }
    } catch (error) {
        showToast(error.message, 'error');
    }
};

// Surgical Neural Refinement
window.refineWithAI = async function(id) {
    const contentElement = document.getElementById(`doc-content-${id}`);
    if (!contentElement) return;

    const rawText = contentElement.innerText;
    showToast('Neural Engine: Initiating deep-clean...', 'info');

    try {
        const response = await fetch('/api/refine', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ text: rawText })
        });
        
        if (!response.ok) throw new Error('Neural refinement failed');
        
        const data = await response.json();
        const refinedText = data.refined_text;
        
        // Open Editor with refined content
        openEditor(id, refinedText);
        showToast('Neural Refinement Complete: Ready for commit.', 'success');
    } catch (error) {
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

window.deleteDocument = async function(id) {
    if (!confirm('Are you sure you want to purge this record from the archive?')) return;
    
    try {
        const response = await fetch(`/api/docs/${id}`, { method: 'DELETE' });
        if (!response.ok) throw new Error('Forensic purge failed');
        
        showToast('Record purged successfully', 'success');
        // Reload or remove from DOM
        window.location.reload();
    } catch (error) {
        showToast(error.message, 'error');
    }
};

function toggleViewer() {
    const modal = document.getElementById('viewer-modal');
    modal.classList.toggle('hidden');
    modal.classList.toggle('flex');
}

window.showToast = function(message, type = 'info') {
    if (window.triggerNotification) {
        window.triggerNotification(message, type);
    } else {
        alert(message);
    }
};
