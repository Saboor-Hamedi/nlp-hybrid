/**
 * Neural Forensic Suite - Settings & Modal Manager
 */
(function() {
    const settingsModal = document.getElementById('settings-modal');
    
    // Global toggle function
    window.toggleSettings = function() {
        if (!settingsModal) return;
        const isHidden = settingsModal.classList.contains('hidden');
        
        if (isHidden) {
            settingsModal.classList.remove('hidden');
            settingsModal.classList.add('flex');
            switchTab('profile'); // Default tab
        } else {
            settingsModal.classList.add('hidden');
            settingsModal.classList.remove('flex');
        }
    };

    // Tab switching logic
    window.switchTab = function(tabId) {
        const metadata = {
            profile: { title: 'Researcher Profile', desc: 'Manage forensic identity and access' },
            appearance: { title: 'Interface & Theme', desc: 'Customize neural visual parameters' },
            forensics: { title: 'Engine Calibration', desc: 'Fine-tune document processing vectors' },
            security: { title: 'Security Protocol', desc: 'Configure access controls and API keys' },
            assistance: { title: 'Assistance Hub', desc: 'Manage AI augmentation and RAG parameters' }
        };

        // Hide all tab contents
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.add('hidden');
        });
        
        // Show target tab content
        const targetTab = document.getElementById(`tab-${tabId}`);
        if (targetTab) targetTab.classList.remove('hidden');
        
        // Update header metadata
        const titleEl = document.getElementById('modal-tab-title');
        const descEl = document.getElementById('modal-tab-desc');
        if (titleEl && metadata[tabId]) titleEl.innerText = metadata[tabId].title;
        if (descEl && metadata[tabId]) descEl.innerText = metadata[tabId].desc;

        // Update tab button styles
        document.querySelectorAll('.tab-btn').forEach(btn => {
            if (btn.getAttribute('data-tab') === tabId) {
                btn.classList.add('active-tab');
            } else {
                btn.classList.remove('active-tab');
            }
        });
    };

    // Close on outside click
    if (settingsModal) {
        settingsModal.addEventListener('click', (e) => {
            if (e.target === settingsModal) toggleSettings();
        });

        // Enter to Save logic
        settingsModal.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.target.tagName === 'INPUT') {
                e.preventDefault();
                saveSettings();
            }
        });
    }

    // Close on Escape key
    window.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && settingsModal && !settingsModal.classList.contains('hidden')) {
            toggleSettings();
        }
    });

    // Initial sync
    const saved = localStorage.getItem('theme') || 'light';
    if (window.setTheme) setTheme(saved);
    
    // Load Forensic Settings
    const forensicSaved = JSON.parse(localStorage.getItem('forensic_config') || '{}');
    Object.keys(forensicSaved).forEach(key => {
        const el = document.getElementById(`toggle-clean-${key}`);
        if (el) el.checked = forensicSaved[key];
    });
    
    // Load Assistance Settings
    const assistanceSaved = JSON.parse(localStorage.getItem('assistance_config') || '{"rag_enabled": false, "result_density": 3}');
    const ragToggle = document.getElementById('toggle-rag-engine');
    const ragDensity = document.getElementById('rag-result-density');
    
    if (ragToggle) ragToggle.checked = assistanceSaved.rag_enabled;
    if (ragDensity) ragDensity.value = assistanceSaved.result_density || 3;
    
    window.isRagEnabled = assistanceSaved.rag_enabled;
    window.ragResultDensity = assistanceSaved.result_density || 3;

    window.updateAssistantConfig = function() {
        const toggle = document.getElementById('toggle-rag-engine');
        const densityInput = document.getElementById('rag-result-density');
        
        const isEnabled = toggle ? toggle.checked : false;
        const density = densityInput ? parseInt(densityInput.value) : 3;
        
        window.isRagEnabled = isEnabled;
        window.ragResultDensity = density;
        
        // Save to persistence
        localStorage.setItem('assistance_config', JSON.stringify({
            rag_enabled: isEnabled,
            result_density: density
        }));
        
        if (window.showToast) {
            showToast(`Assistance Engine: ${isEnabled ? 'ACTIVE' : 'BYPASS'} | Density: ${density}`, isEnabled ? 'success' : 'info');
        }
    };
    
    window.updateRagState = window.updateAssistantConfig; // Alias for backward compatibility

    window.saveSettings = function() {
        // Collect Forensic Toggle States
        const forensicSettings = {
            academic: document.getElementById('toggle-clean-academic')?.checked,
            pdf: document.getElementById('toggle-clean-pdf')?.checked,
            math: document.getElementById('toggle-clean-math')?.checked,
            numerical: document.getElementById('toggle-clean-num')?.checked
        };

        console.log('Pushing Forensic Configuration:', forensicSettings);

        // Show cleaning notification
        if (window.showToast) showToast('Initiating forensic cleaning...', 'info');
        
        // UI Feedback
        const btn = document.querySelector('button[onclick="saveSettings()"]');
        const originalText = btn ? btn.innerHTML : 'Update';
        if (btn) btn.innerHTML = '<div class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto"></div>';
        
        // Execute Forensic Sweep via API
        fetch('/api/maintenance/sweep', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(forensicSettings)
        })
        .then(response => response.json())
        .then(data => {
            if (btn) btn.innerHTML = originalText;
            
            if (data.status === 'success') {
                showToast(`Calibration Complete (${data.latency})`, 'success');
                // Save to local persistence
                localStorage.setItem('forensic_config', JSON.stringify(forensicSettings));
                setTimeout(toggleSettings, 800);
            } else {
                showToast('Sweep Failed: ' + data.message, 'error');
            }
        })
        .catch(err => {
            if (btn) btn.innerHTML = originalText;
            showToast('Network Error: Forensic Engine Unreachable', 'error');
            console.error(err);
        });
    };

    window.executeClusterPurge = async function() {
        if (!confirm("CRITICAL: This will purge ALL non-correlative document fragments. This action is irreversible. Proceed?")) return;

        showToast('Initiating Cluster Purge...', 'info');
        try {
            const response = await fetch('/api/maintenance/purge', { method: 'POST' });
            const data = await response.json();
            
            if (data.status === 'success') {
                showToast(`Purge Complete: ${data.purged_count} records removed.`, 'success');
                setTimeout(() => window.location.reload(), 1500);
            } else {
                showToast('Purge Failed: ' + data.message, 'error');
            }
        } catch (err) {
            showToast('Network Error: Maintenance API Offline', 'error');
            console.error(err);
        }
    };
})();
