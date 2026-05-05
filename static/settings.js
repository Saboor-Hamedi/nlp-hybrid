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
            security: { title: 'Security Protocol', desc: 'Configure access controls and API keys' }
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

    window.saveSettings = function() {
        // Show cleaning notification
        if (window.showToast) showToast('Initiating forensic cleaning...', 'info');
        
        // Simulate save
        const btn = document.querySelector('button[onclick="saveSettings()"]');
        if (btn) btn.innerHTML = '<div class="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin mx-auto"></div>';
        
        setTimeout(() => {
            if (btn) btn.innerHTML = 'Update';
            showToast('Settings Updated', 'success');
            toggleSettings();
        }, 800);
    };
})();
