document.addEventListener('DOMContentLoaded', function() {
    const searchModal = document.getElementById('search-modal');
    const searchInput = document.getElementById('command-search');
    const triggerSearch = document.getElementById('trigger-search');
    const paletteResults = document.getElementById('search-results');

    if (!searchModal || !triggerSearch) return;

    let selectedIndex = -1;

    function toggleSearch() {
        searchModal.classList.toggle('active');
        if (searchModal.classList.contains('active')) {
            selectedIndex = -1;
            setTimeout(() => {
                if (searchInput) searchInput.focus();
            }, 100);
        }
    }

    function updateSelection() {
        const results = paletteResults.querySelectorAll('a');
        results.forEach((el, idx) => {
            if (idx === selectedIndex) {
                el.classList.add('selected');
                el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                el.classList.remove('selected');
            }
        });
    }

    triggerSearch.addEventListener('click', toggleSearch);

    window.addEventListener('keydown', (e) => {
        const results = paletteResults.querySelectorAll('a');
        
        if ((e.ctrlKey || e.metaKey) && (e.code === 'KeyK' || e.key === 'k')) {
            e.preventDefault();
            e.stopPropagation();
            toggleSearch();
        }
        else if (e.key === 'Escape' && searchModal.classList.contains('active')) {
            toggleSearch();
        }
        else if (searchModal.classList.contains('active')) {
            if (e.key === 'ArrowDown') {
                e.preventDefault();
                selectedIndex = (selectedIndex + 1) % results.length;
                updateSelection();
            } 
            else if (e.key === 'ArrowUp') {
                e.preventDefault();
                selectedIndex = (selectedIndex - 1 + results.length) % results.length;
                updateSelection();
            } 
            else if (e.key === 'Enter' && selectedIndex >= 0) {
                e.preventDefault();
                results[selectedIndex].click();
            }
        }
    });

    searchModal.addEventListener('click', (e) => {
        if (e.target === searchModal) toggleSearch();
    });

    let searchTimeout;
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        clearTimeout(searchTimeout);
        selectedIndex = -1; // Reset selection on new search
        
        if (query.length < 2) {
            paletteResults.innerHTML = `
                <div class="p-8 text-center">
                    <p class="text-[10px] font-bold text-gray-300 uppercase tracking-widest">Type to search forensic records</p>
                </div>`;
            return;
        }

        searchTimeout = setTimeout(async () => {
            paletteResults.innerHTML = `
                <div class="p-8 text-center">
                    <div class="w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
                    <p class="text-[9px] font-bold text-gray-400 uppercase tracking-widest">Neural correlate sync...</p>
                </div>`;
            
            try {
                const response = await fetch(`/api/quick-search?query=${encodeURIComponent(query)}`);
                const results = await response.json();
                
                if (results.length === 0) {
                    paletteResults.innerHTML = `
                        <div class="p-8 text-center">
                            <p class="text-[9px] font-bold text-gray-400 uppercase tracking-widest">No signals detected for "${query}"</p>
                        </div>`;
                    return;
                }

                paletteResults.innerHTML = results.map(res => `
                    <a href="/show/${res.id}" class="palette-item flex items-center justify-between p-3 rounded-xl transition-all group border border-transparent">
                        <div class="flex items-center gap-3">
                            <div class="w-8 h-8 theme-bg-sec border theme-border rounded-lg flex items-center justify-center theme-text-sec group-hover:text-blue-600 transition-all">
                                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>
                            </div>
                            <div class="max-w-[340px]">
                                <p class="text-xs font-bold theme-text line-clamp-1">${res.content}</p>
                                <p class="text-[9px] theme-text-sec opacity-40 uppercase tracking-tight">Record ID: #${res.id}</p>
                            </div>
                        </div>
                        <div class="text-right">
                            <span class="text-[9px] font-bold text-blue-600 theme-bg-sec px-1.5 py-0.5 rounded border theme-border">SC ${res.score}</span>
                        </div>
                    </a>
                `).join('');

            } catch (err) {
                paletteResults.innerHTML = `<div class="p-8 text-center text-red-500 text-[9px] font-bold uppercase">Sync Failure: Network Latency</div>`;
            }
        }, 300);
    });
});
