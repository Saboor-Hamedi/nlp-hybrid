/**
 * Forensic Analytics Module
 * Handles the calculation and visualization of scoring coherency and thematic integrity.
 */

window.ForensicAnalytics = (function() {
    let currentIntelligence = null;

    return {
        setIntelligence: function(intel) {
            currentIntelligence = intel;
        },
        renderGlobalIntelligence: function() {
            const container = document.getElementById('inspector-content');
            if (!container || !currentIntelligence) return;

            const latency = currentIntelligence.latency || {};
            const totalLatency = (latency.total || 0).toFixed(2);
            
            container.innerHTML = `
                <div class="space-y-6 animate-in fade-in duration-500">
                    <div class="pb-4 border-b theme-border">
                        <p class="text-[8px] font-bold text-blue-600 uppercase tracking-[0.2em] mb-1">Search Intelligence</p>
                        <h3 class="text-[11px] font-bold theme-text uppercase tracking-widest">Global Session Metrics</h3>
                    </div>

                    <div class="space-y-4">
                        <p class="text-[8px] font-bold theme-text-sec uppercase tracking-widest opacity-40">Engine Latency</p>
                        <div class="p-4 rounded-lg bg-gray-50/50 dark:bg-gray-800/30 border theme-border">
                             <div class="flex items-end justify-between mb-2">
                                <span class="text-[18px] font-mono font-bold theme-text">${totalLatency}ms</span>
                                <span class="text-[7px] font-bold text-green-500 uppercase tracking-widest">Optimized</span>
                             </div>
                             <div class="w-full h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                                <div class="h-full bg-blue-600" style="width: ${Math.min(100, (totalLatency/1000)*100)}%"></div>
                             </div>
                        </div>

                        <div class="grid grid-cols-2 gap-3">
                            <div class="p-3 rounded-lg border theme-border bg-blue-500/5">
                                <p class="text-[7px] font-bold text-blue-500 uppercase tracking-widest mb-1">Alpha Bias</p>
                                <p class="text-[9px] font-bold theme-text">${currentIntelligence.alpha || '0.5'}</p>
                            </div>
                            <div class="p-3 rounded-lg border theme-border bg-purple-500/5">
                                <p class="text-[7px] font-bold text-purple-500 uppercase tracking-widest mb-1">Precision</p>
                                <p class="text-[9px] font-bold theme-text">High Density</p>
                            </div>
                        </div>
                    </div>

                    <div class="pt-6 border-t theme-border">
                        <p class="text-[8px] theme-text-sec opacity-40 leading-relaxed uppercase tracking-widest">
                            Select a document segment in the stream to inspect individual fusion scores.
                        </p>
                    </div>
                </div>
            `;
        },

        renderScoringSidebar: function(docId, docData, cachedData) {
            const container = document.createElement('div');
            container.className = "space-y-6 mt-6 pt-6 border-t theme-border animate-in fade-in duration-700";
            
            const score = docData.score || cachedData.score || 0;
            const semantic = docData.semantic_score || cachedData.semantic_score || 0;
            const bm25 = docData.bm25_score || cachedData.bm25_score || 0;

            container.innerHTML = `
                <div class="space-y-4">
                    <p class="text-[8px] font-bold theme-text-sec uppercase tracking-[0.2em] opacity-40">Forensic Scoring Coherency</p>
                    
                    <div class="relative h-12 bg-blue-600/5 rounded-lg border theme-border flex items-center px-4 overflow-hidden">
                        <div class="absolute left-0 top-0 bottom-0 bg-blue-600/10" style="width: ${Math.min(100, score * 100)}%"></div>
                        <div class="relative flex-1">
                            <p class="text-[7px] font-bold text-blue-600 uppercase tracking-widest mb-0.5">Fusion Integrity</p>
                            <p class="text-[14px] font-mono font-bold theme-text tracking-tighter">${(score * 100).toFixed(2)}%</p>
                        </div>
                    </div>

                    <div class="grid grid-cols-2 gap-3">
                        <div class="p-3 rounded-lg border theme-border bg-gray-50/5">
                            <p class="text-[7px] font-bold theme-text-sec uppercase tracking-widest mb-1 opacity-50">Semantic</p>
                            <p class="text-[10px] font-mono font-bold theme-text">${semantic.toFixed(4)}</p>
                        </div>
                        <div class="p-3 rounded-lg border theme-border bg-gray-50/5">
                            <p class="text-[7px] font-bold theme-text-sec uppercase tracking-widest mb-1 opacity-50">Lexical</p>
                            <p class="text-[10px] font-mono font-bold theme-text">${bm25.toFixed(4)}</p>
                        </div>
                    </div>
                </div>
            `;

            return container;
        }
    };
})();
