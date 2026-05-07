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
  if(!btn) return;
  btn.classList.add(currentMode === "local" ? "bg-blue-600" : "bg-purple-600");
  btn.classList.remove("bg-gray-800");
  if(sendIcon) sendIcon.classList.remove("hidden");
  if(stopIcon) stopIcon.classList.add("hidden");
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
  userMsg.className = "flex flex-col items-end w-full message-bubble mb-6";
  const colorClass = currentMode === "local" ? "bg-blue-600" : "bg-purple-600";
  userMsg.innerHTML = `
        <div class="${colorClass} text-white p-4 rounded-2xl rounded-tr-none max-w-[80%] text-left shadow-sm">
            <p class="text-[13px] font-medium leading-relaxed">${query}</p>
        </div>
        <span class="text-[8px] font-bold theme-text-sec opacity-30 uppercase tracking-widest mt-1 mr-1">${currentMode === "local" ? "Forensic Researcher" : "Global Analyst"}</span>
    `;
  thread.appendChild(userMsg);
  queryInput.value = "";
  queryInput.style.height = "44px"; 
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
  aiMsg.className = "flex flex-col w-full message-bubble mb-10";
  
  aiMsg.innerHTML = `
        <div id="${aiMsgId}-evidence" class="hidden w-full mb-8 pb-4 border-b border-dashed theme-border">
            <div class="flex items-center justify-between mb-4">
                <p class="text-[7px] font-bold theme-text-sec uppercase tracking-widest opacity-30">Forensic Source Data</p>
                <div class="h-[1px] flex-1 mx-3 bg-gray-100 dark:bg-gray-800 opacity-20"></div>
            </div>
            <div id="${aiMsgId}-grid" class="grid grid-cols-1 gap-1 w-full"></div>
        </div>

        <div id="${aiMsgId}-content" class="markdown-body leading-relaxed opacity-90 px-1"></div>

        <div class="flex items-center gap-2 mt-6 mb-2 ml-1">
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
    const socialQueries = ["hello", "hi", "hey", "who are you", "help", "thanks", "thank you", "good morning", "good afternoon"];
    const isSocial = socialQueries.includes(query.toLowerCase().replace(/[?!. ]+$/, "").trim());

    // 1. DATA RETRIEVAL (ALWAYS ATTEMPTED UNLESS SOCIAL)
    if (!isSocial) {
      try {
        const limit = window.ragResultDensity || parseInt(document.getElementById("rag-result-density")?.value || "3");
        console.log(`%c[Forensic Engine] Initiating retrieval with density: ${limit}`, "color: #2563eb; font-weight: bold;");
        const searchResponse = await fetch(`/api/search?query=${encodeURIComponent(query)}&limit=${limit}`, { signal: abortController.signal });
        searchData = await searchResponse.json();

        if (searchData.intelligence) {
            ForensicAnalytics.setIntelligence(searchData.intelligence);
            ForensicAnalytics.renderGlobalIntelligence();
        }
      } catch (err) {
        console.warn("Search Retrieval failed or aborted", err);
      }
    }

    // 2. RENDER FORENSIC CARDS
    if (searchData.results && searchData.results.length > 0) {
        evidence.classList.remove("hidden");
        grid.innerHTML = "";
        searchData.results.forEach((res) => {
          const card = document.createElement("div");
          card.id = `forensic-card-${res.id}`;
          card.className = "w-full py-4 border-b theme-border last:border-0 group/card relative transition-all cursor-pointer";
          card.setAttribute("onclick", `inspectDocument('${res.id}')`);
          card.setAttribute("data-forensic-id", res.id);

          card.innerHTML = `
                <div class="mb-4">
                    <div class="flex items-center justify-between mb-1">
                        <h4 class="text-[10px] font-bold theme-text uppercase tracking-widest">${res.smart_title || 'Forensic Dossier'}</h4>
                        <span class="text-[7px] font-mono theme-text opacity-30">SCORE: ${res.score.toFixed(3)}</span>
                    </div>
                    <p class="text-[7px] font-bold text-blue-500 uppercase tracking-[0.2em] opacity-60">${res.smart_subtitle || 'Neural Analysis'}</p>
                </div>
                <div class="flex items-start gap-4 mb-2">
                    <div class="flex-1">
                        <div id="forensic-content-${res.id}" class="forensic-content-body markdown-body text-[11px] theme-text leading-relaxed opacity-80 group-hover/card:opacity-100 transition-opacity">
                            ${marked.parse(res.snippet || res.content)}
                        </div>
                    </div>
                </div>
                <div class="flex items-center gap-4 mt-4 ml-5">
                    <span class="text-[7px] font-bold text-blue-600 bg-blue-600/5 px-1.5 py-0.5 rounded border border-blue-600/10 uppercase tracking-tighter">DOC #${res.id}</span>
                    <div class="h-[1px] flex-1 bg-gray-100 dark:bg-gray-800 opacity-20"></div>
                    <div class="flex items-center gap-1 opacity-30 group-hover/card:opacity-100 transition-opacity ml-2">
                        <button onclick="event.stopPropagation(); openForensicEditor('${res.id}')" class="p-1.5 hover:text-blue-600 transition-all"><svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-5M18.364 5.636l-3.536 3.536m0 0l-1.06-1.06m1.06 1.06l1.06 1.06m-1.06-1.06l3.536-3.536z"></path></svg></button>
                        <button onclick="event.stopPropagation(); purgeForensicRecord('${res.id}')" class="p-1.5 hover:text-red-600 transition-all"><svg class="w-2.5 h-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg></button>
                    </div>
                </div>
          `;
          thematicCache[res.id] = { lda: res.lda_topic_label, bert: res.bert_topic_label, score: res.score };
          grid.appendChild(card);
        });
        window.inspectDocument(searchData.results[0].id);
    }

    // 3. NEURAL SYNTHESIS (IF ENABLED)
    if (window.isRagEnabled === true) {
      try {
        const synthResponse = await fetch("/api/synthesis", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ query, context_docs: searchData.results, mode: currentMode }),
          signal: abortController.signal
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
        }
      } catch (err) {
        console.error("Synthesis error", err);
      }
      statusEl.classList.add("hidden");
      actionsEl.classList.remove("hidden");
    } else {
      contentEl.innerHTML = `<p class="text-[11px] opacity-40 italic">Synthesis offline. Retrieval complete.</p>`;
      statusEl.classList.add("hidden");
    }
  } catch (error) {
    console.error("Critical Failure", error);
  } finally {
    isGenerating = false;
    revertPulsar();
  }
}

// Global CRUD Helpers
window.openForensicEditor = (id) => fetch(`/api/docs/${id}`).then(r => r.json()).then(d => window.openEditor(id, d.content));
window.purgeForensicRecord = async (id) => {
    if(!confirm("Purge record?")) return;
    const r = await fetch(`/api/docs/${id}`, { method: 'DELETE' });
    if(r.ok) showToast("Purged", "success");
};

window.inspectDocument = async (id) => {
    const el = document.getElementById("inspector-content");
    if(!el) return;
    const r = await fetch(`/api/docs/${id}`);
    const d = await r.json();
    const c = thematicCache[id] || {};
    el.innerHTML = `<div class="space-y-6">
        <h3 class="text-[11px] font-bold theme-text uppercase">Document #${id}</h3>
        <div class="grid grid-cols-2 gap-3 text-[9px] theme-text">
            <div class="p-3 theme-bg-sec border theme-border rounded"><b>LDA:</b> ${c.lda || d.lda_tag}</div>
            <div class="p-3 theme-bg-sec border theme-border rounded"><b>BERT:</b> ${c.bert || d.bert_tag}</div>
        </div>
        <button onclick="openReadMore('${id}')" class="w-full py-2 bg-blue-600 text-white rounded text-[9px] font-bold uppercase">Full Dossier</button>
    </div>`;
};

window.openReadMore = async (id) => {
    const m = document.getElementById("readmore-modal");
    const c = document.getElementById("readmore-content");
    m.classList.replace("hidden", "flex");
    const r = await fetch(`/api/docs/${id}`);
    const d = await r.json();
    c.innerHTML = marked.parse(d.content);
};

window.closeReadMore = () => document.getElementById("readmore-modal").classList.replace("flex", "hidden");
window.addEventListener("keydown", (e) => e.key === "Escape" && closeReadMore());
