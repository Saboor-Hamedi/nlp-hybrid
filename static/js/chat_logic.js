/**
 * Signal Assistance - Kinetic Chat & Forensic Logic
 * Orchestrates real-time AI synthesis and forensic document retrieval.
 */

let isGenerating = false;
let abortController = null;
let currentMode = "local"; // Default: Local RAG
const thematicCache = {};

// Mode Orchestration
window.setMode = function (mode) {
  currentMode = mode;
  const localBtn = document.getElementById("mode-local");
  const globalBtn = document.getElementById("mode-global");
  const pulsar = document.getElementById("exec-btn");

  if (mode === "local") {
    localBtn.classList.add("bg-blue-600", "text-white", "shadow-sm");
    localBtn.classList.remove("theme-text", "opacity-40");
    globalBtn.classList.remove("bg-purple-600", "text-white", "shadow-sm");
    globalBtn.classList.add("theme-text", "opacity-40");
    pulsar.classList.add("bg-blue-600");
    pulsar.classList.remove("bg-purple-600");
  } else {
    globalBtn.classList.add("bg-purple-600", "text-white", "shadow-sm");
    globalBtn.classList.remove("theme-text", "opacity-40");
    localBtn.classList.remove("bg-blue-600", "text-white", "shadow-sm");
    localBtn.classList.add("theme-text", "opacity-40");
    pulsar.classList.add("bg-purple-600");
    pulsar.classList.remove("bg-blue-600");
  }

  document.getElementById("stream-query").placeholder =
    mode === "local" ? "RAG Assistance..." : "Global Assistance...";
};

// Pulsar Execution Trigger
window.handlePulsarClick = function () {
  if (isGenerating) {
    if (abortController) abortController.abort();
    isGenerating = false;
    revertPulsar();
  } else {
    executeStreamSearch();
  }
};

function revertPulsar() {
  const btn = document.getElementById("exec-btn");
  const sendIcon = document.getElementById("exec-icon-send");
  const stopIcon = document.getElementById("exec-icon-stop");
  btn.classList.add(currentMode === "local" ? "bg-blue-600" : "bg-purple-600");
  btn.classList.remove("bg-gray-800");
  sendIcon.classList.remove("hidden");
  stopIcon.classList.add("hidden");
}

async function executeStreamSearch() {
  const queryInput = document.getElementById("stream-query");
  const query = queryInput.value.trim();
  if (!query) return;

  const thread = document.getElementById("forensic-thread");
  const btn = document.getElementById("exec-btn");
  const sendIcon = document.getElementById("exec-icon-send");
  const stopIcon = document.getElementById("exec-icon-stop");

  if (thread.querySelector(".opacity-10")) thread.innerHTML = "";

  // User Message
  const userMsg = document.createElement("div");
  userMsg.className = "flex flex-col items-end w-full message-bubble";
  const colorClass = currentMode === "local" ? "bg-blue-600" : "bg-purple-600";
  userMsg.innerHTML = `
        <div class="${colorClass} text-white p-4 rounded-2xl rounded-tr-none max-w-[80%] text-left">
            <p class="text-[13px] font-medium leading-relaxed">${query}</p>
        </div>
        <span class="text-[8px] font-bold theme-text-sec opacity-30 uppercase tracking-widest mt-1 mr-1">${currentMode === "local" ? "Forensic Researcher" : "Global Analyst"}</span>
    `;
  thread.appendChild(userMsg);
  queryInput.value = "";
  queryInput.style.height = "44px"; // Reset to new expanded height
  thread.scrollTop = thread.scrollHeight;

  isGenerating = true;
  abortController = new AbortController();
  btn.classList.remove("bg-blue-600", "bg-purple-600");
  btn.classList.add("bg-gray-800");
  sendIcon.classList.add("hidden");
  stopIcon.classList.remove("hidden");

  // AI Message Container
  const aiMsgId = "ai-" + Date.now();
  const aiMsg = document.createElement("div");
  aiMsg.className = "flex flex-col items-start w-full message-bubble mb-6";
  const accentColor = currentMode === "local" ? "bg-blue-500" : "bg-purple-500";

  aiMsg.innerHTML = `
        <div id="${aiMsgId}-evidence" class="hidden mb-6 pb-4 border-b border-dashed theme-border">
            <div class="flex items-center justify-between mb-3">
                <p class="text-[7px] font-bold theme-text-sec uppercase tracking-widest opacity-30">Forensic Source Data</p>
                <div class="h-[1px] flex-1 mx-3 bg-gray-100 dark:bg-gray-800 opacity-20"></div>
            </div>
            <div id="${aiMsgId}-grid" class="grid grid-cols-1 gap-1"></div>
        </div>

        <div id="${aiMsgId}-content" class="markdown-body leading-relaxed opacity-90 px-1"></div>

        <div class="flex items-center gap-2 mt-6 mb-2 ml-1">
            <div class="w-1 h-1 ${accentColor} rounded-full shadow-[0_0_5px_${accentColor}]"></div>
            <span class="text-[7px] font-bold theme-text-sec uppercase tracking-[0.2em] opacity-40">Assistance</span>
            <span id="${aiMsgId}-status" class="typing-dot text-[7px] font-bold text-blue-600 uppercase tracking-widest ml-3">Thinking...</span>
        </div>
        
        <div id="${aiMsgId}-actions" class="hidden mt-4 flex justify-end items-center gap-2 border-t theme-border pt-2 transition-colors">
            <button onclick="saveInsight('${aiMsgId}', \`${query.replace(/`/g, "\\`").replace(/\${/g, "\\${")}\`, '${currentMode}')" 
                    id="${aiMsgId}-save-btn"
                    class="px-3 py-1.5 bg-white dark:bg-gray-800 border theme-border rounded-md text-[7px] font-bold uppercase tracking-widest hover:scale-105 active:scale-95 transition-all flex items-center gap-2 group/save">
                <svg class="w-2.5 h-2.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>
                <span>Save Insight</span>
            </button>
        </div>
    `;
  thread.appendChild(aiMsg);
  thread.scrollTop = thread.scrollHeight;

  const contentEl = document.getElementById(`${aiMsgId}-content`);
  const statusEl = document.getElementById(`${aiMsgId}-status`);
  const actionsEl = document.getElementById(`${aiMsgId}-actions`);
  const evidence = document.getElementById(`${aiMsgId}-evidence`);
  const grid = document.getElementById(`${aiMsgId}-grid`);

  let fullText = "";

  try {
    let searchData = { results: [] };
    if (currentMode === "local") {
      const limit = window.ragResultDensity || 3;
      const searchResponse = await fetch(
        `/api/search?query=${encodeURIComponent(query)}&limit=${limit}`,
        { signal: abortController.signal },
      );
      searchData = await searchResponse.json();

      if (searchData.intelligence) {
        ForensicAnalytics.setIntelligence(searchData.intelligence);
        ForensicAnalytics.renderGlobalIntelligence();
      }

      if (searchData.results.length > 0) {
        evidence.classList.remove("hidden");

        if (window.isRagEnabled !== true) {
          const labelEl = aiMsg.querySelector("span.theme-text-sec");
          if (labelEl) labelEl.innerText = "Forensic Retrieval";
        }

        searchData.results.slice(0, limit).forEach((res) => {
          const card = document.createElement("div");
          card.id = `forensic-card-${res.id}`;
          card.className =
            "w-full py-4 border-b theme-border last:border-0 group/card relative transition-all cursor-pointer";
          card.setAttribute("onclick", `inspectDocument('${res.id}')`);

          card.innerHTML = `
                        <div class="flex items-start gap-4 mb-2">
                            <div class="w-1.5 h-1.5 rounded-full bg-blue-600 mt-1.5 opacity-40 group-hover/card:opacity-100 group-hover/card:scale-125 transition-all"></div>
                            <div class="flex-1">
                                <p class="forensic-snippet-sync-${res.id} text-[12px] theme-text leading-relaxed opacity-80 group-hover/card:opacity-100 transition-opacity">
                                    ${res.snippet || res.content}
                                </p>
                            </div>
                        </div>
                        
                        <div class="flex items-center gap-4 mt-3 ml-5">
                            <div class="flex items-center gap-2">
                                <span class="text-[7px] font-bold text-blue-600 bg-blue-600/5 px-1.5 py-0.5 rounded border border-blue-600/10 uppercase tracking-tighter">DOC #${res.id}</span>
                            </div>
                            
                            <div class="h-[1px] flex-1 bg-gray-100 dark:bg-gray-800 opacity-20"></div>

                            <div class="flex items-center gap-3">
                                <button onclick="openReadMore('${res.id}')" 
                                        class="text-[8px] font-bold text-blue-600 uppercase tracking-widest hover:underline flex items-center gap-1.5">
                                    <span>Inspect Full Dossier</span>
                                    <svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M14 5l7 7m0 0l-7 7m7-7H3"></path></svg>
                                </button>
                                
                                <div class="flex items-center gap-1.5 opacity-40 group-hover/card:opacity-100 transition-opacity ml-2">
                                    <button onclick="event.stopPropagation(); openForensicEditor('${res.id}')" class="p-1.5 hover:text-blue-600 transition-all" title="Update Record">
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-5M18.364 5.636l-3.536 3.536m0 0l-1.06-1.06m1.06 1.06l1.06 1.06m-1.06-1.06l3.536-3.536z"></path></svg>
                                    </button>
                                    <button onclick="event.stopPropagation(); purgeForensicRecord('${res.id}')" class="p-1.5 hover:text-red-600 transition-all" title="Delete Record">
                                        <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
          // Cache thematic and scoring data for this document
          thematicCache[res.id] = {
            lda: res.lda_topic_label,
            bert: res.bert_topic_label,
            score: res.score,
            semantic_score: res.semantic_score,
            bm25_score: res.bm25_score,
            lda_coherence: res.lda_coherence,
          };

          grid.appendChild(card);
        });

        // Auto-Inspect the top result for immediate visibility
        if (searchData.results.length > 0) {
          window.inspectDocument(searchData.results[0].id);
        }
      }
    }

    if (window.isRagEnabled === true) {
      const synthResponse = await fetch("/api/synthesis", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          context_docs: searchData.results,
          mode: currentMode,
        }),
        signal: abortController.signal,
      });

      const reader = synthResponse.body.getReader();
      const decoder = new TextDecoder();
      statusEl.innerText = "Synthesizing...";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        fullText += decoder.decode(value);

        contentEl.innerHTML = marked.parse(fullText);
        thread.scrollTop = thread.scrollHeight;
        statusEl.innerText = "Responding...";
      }
      statusEl.classList.add("hidden");
      actionsEl.classList.remove("hidden");
    } else {
      statusEl.classList.add("hidden");
      revertPulsar();
      isGenerating = false;
    }
  } catch (error) {
    if (error.name === "AbortError") {
      contentEl.innerHTML +=
        '<p class="text-[10px] italic opacity-40 mt-4">[Synthesis Terminated]</p>';
    } else {
      showToast(error.message, "error");
    }
  } finally {
    isGenerating = false;
    revertPulsar();
  }
}

// Forensic CRUD Actions
window.openForensicEditor = function (docId) {
  if (window.openEditor) {
    fetch(`/api/docs/${docId}`)
      .then((r) => r.json())
      .then((data) => {
        window.openEditor(docId, data.content);
      });
  } else {
    showToast("Forensic Editor is currently offline", "error");
  }
};

window.purgeForensicRecord = async function (docId) {
  if (
    !confirm("Are you sure you want to permanently PURGE this forensic record?")
  )
    return;
  try {
    const response = await fetch(`/api/docs/${docId}`, { method: "DELETE" });
    const data = await response.json();
    if (data.status === "success") {
      showToast("Forensic Record Purged", "success");
      document.querySelectorAll(`[onclick*="'${docId}'"]`).forEach((el) => {
        const card = el.closest(".group\\/card") || el.closest(".result-item");
        if (card) {
          card.style.opacity = "0.3";
          card.style.pointerEvents = "none";
          card.style.filter = "grayscale(1)";
        }
      });
    }
  } catch (err) {
    showToast("Purge Error", "error");
  }
};

async function saveInsight(aiMsgId, query, mode) {
  const contentEl = document.getElementById(`${aiMsgId}-content`);
  const btn = document.getElementById(`${aiMsgId}-save-btn`);
  const content = contentEl.innerText;

  try {
    btn.innerHTML = `<div class="w-2.5 h-2.5 border border-blue-600 border-t-transparent rounded-full animate-spin"></div><span>Saving...</span>`;
    const response = await fetch("/api/synthesis/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, content, mode }),
    });
    const data = await response.json();
    if (data.status === "success") {
      btn.className =
        "px-3 py-1.5 bg-green-500 text-white rounded-md text-[7px] font-bold uppercase tracking-widest shadow-sm flex items-center gap-2";
      btn.innerHTML = `<svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg><span>Saved to Archive</span>`;
      btn.onclick = null;
      showToast("Insight committed to forensic registry.", "success");
    }
  } catch (error) {
    showToast("Save failed", "error");
    btn.innerHTML = `<span>Error</span>`;
  }
}

window.inspectDocument = async function(id) {
    const inspector = document.getElementById("inspector-content");
    if (!inspector) return;

    // Remove the intrusive loading state to prevent 'jumping'
    // We only show a subtle indicator if needed, but for fast APIs we can just update directly

    try {
        const response = await fetch(`/api/docs/${id}`);
        const data = await response.json();

        const cached = thematicCache[id] || {};

        // Use fade-in only, remove slide-in to keep it stable
        inspector.innerHTML = `
            <div class="space-y-6 animate-in fade-in duration-300">
                <div class="pb-4 border-b theme-border">
                    <p class="text-[8px] font-bold theme-text-sec uppercase tracking-[0.2em] opacity-40 mb-1">Active Dossier</p>
                    <h3 class="text-[11px] font-bold theme-text uppercase tracking-widest">Document #${id}</h3>
                </div>

                <div class="grid grid-cols-2 gap-3">
                    <div class="p-3 rounded-lg border theme-border bg-purple-500/5">
                        <p class="text-[7px] font-bold text-purple-500 uppercase tracking-widest mb-1">LDA Topic</p>
                        <p class="text-[9px] font-bold theme-text">${cached.lda || data.lda_tag || "Unclassified"}</p>
                    </div>
                    <div class="p-3 rounded-lg border theme-border bg-indigo-500/5">
                        <p class="text-[7px] font-bold text-indigo-500 uppercase tracking-widest mb-1">BERT Context</p>
                        <p class="text-[9px] font-bold theme-text">${cached.bert || data.bert_tag || "Unclassified"}</p>
                    </div>
                </div>
            </div>
        `;

        // Inject Forensic Scoring Section
        const scoringSection = ForensicAnalytics.renderScoringSidebar(id, data, cached);
        inspector.appendChild(scoringSection);

        // Add Read More button at the very bottom
        const footerActions = document.createElement("div");
        footerActions.className = "pt-6 mt-6 border-t theme-border";
        footerActions.innerHTML = `
            <button onclick="openReadMore('${id}')" 
                    class="w-full py-2 bg-blue-600 text-white rounded-lg text-[9px] font-bold uppercase tracking-widest hover:bg-blue-700 transition-all shadow-md shadow-blue-600/20">
                Full Dossier
            </button>
        `;
        inspector.appendChild(footerActions);
    } catch (error) {
        showToast("Inspection failed", "error");
        inspector.innerHTML = `<p class="text-[9px] text-red-500">Retrieval Failure: ${error.message}</p>`;
    }
};

window.openReadMore = async function (id) {
  const modal = document.getElementById("readmore-modal");
  const content = document.getElementById("readmore-content");

  if (!modal || !content) return;

  modal.classList.remove("hidden");
  modal.classList.add("flex");

  content.innerHTML = `
        <div class="flex flex-col items-center justify-center h-full opacity-40">
            <div class="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p class="text-[10px] font-bold uppercase tracking-[0.3em] mt-6">Decrypting Dossier #${id}...</p>
        </div>
    `;

  try {
    const response = await fetch(`/api/docs/${id}`);
    const data = await response.json();

    // Update Metadata (Priority: Cache -> API -> Default)
    const cached = thematicCache[id] || {};
    document.getElementById("readmore-index").innerText =
      `#${String(id).padStart(4, "0")}`;
    document.getElementById("readmore-lda").innerText =
      cached.lda || data.lda_tag || "Unclassified";
    document.getElementById("readmore-bert").innerText =
      cached.bert || data.bert_tag || "Unclassified";
    document.getElementById("readmore-lang").innerText =
      data.language || "Unknown";
    document.getElementById("readmore-date").innerText =
      data.created_at || "--";

    // Update Content with Markdown rendering
    content.innerHTML = marked.parse(data.content);
  } catch (err) {
    content.innerHTML = `<p class="text-red-500 font-bold">Failed to retrieve forensic payload: ${err.message}</p>`;
  }
};

window.closeReadMore = function () {
  const modal = document.getElementById("readmore-modal");
  if (modal) {
    modal.classList.add("hidden");
    modal.classList.remove("flex");
  }
};

// Close modal on Escape
window.addEventListener("keydown", (e) => {
  if (e.key === "Escape") closeReadMore();
});
