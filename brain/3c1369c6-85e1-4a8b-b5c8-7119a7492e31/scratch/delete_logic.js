    async function deleteDocument(id) {
        if (!confirm('Are you sure you want to permanently purge this document?')) return;
        try {
            const response = await fetch(`/api/docs/${id}`, { method: 'DELETE' });
            const data = await response.json();
            if (data.status === 'success') {
                showToast('Document purged from archive.', 'success');
                // Robust Inspector Reset
                document.getElementById('inspector-content').innerHTML = `
                    <div class="flex flex-col items-center justify-center h-64 opacity-20 text-center">
                        <p class="text-[9px] font-bold uppercase tracking-widest">Select segment for<br>deep analytics</p>
                    </div>
                `;
            } else {
                showToast('Purge failed: ' + data.message, 'error');
            }
        } catch (error) {
            showToast('Network error during purge.', 'error');
        }
    }
