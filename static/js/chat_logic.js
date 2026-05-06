/**
 * Neural Forensic Suite - Stream Orchestrator
 * Handles RAG synthesis, document inspection, and kinetic UI manifesting.
 */

let currentMode = "local";
let abortController = null;
let isGenerating = false;
let thematicCache = {}; // ID -> Thematic Data

function setMode(mode) {
  if (isGenerating) return;
  currentMode = mode;
  const localBtn = document.getElementById("mode-local");
  const globalBtn = document.getElementById("mode-global");
  const queryInput = document.getElementById("stream-query");
  const btn = document.getElementById("exec-btn");

  if (mode === "local") {
    localBtn.className =
      "px-2 py-1 rounded-md text-[7px] font-bold uppercase tracking-widest transition-all bg-blue-600 text-white shadow-sm";
    globalBtn.className =
      "px-2 py-1 rounded-md text-[7px] font-bold uppercase tracking-widest transition-all theme-text opacity-40 hover:opacity-100";
    queryInput.placeholder = "Assistance...";
    btn.className =
      "w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center hover:bg-blue-700 active:scale-90 transition-all shadow-lg";
  } else {
    globalBtn.className =
      "px-2 py-1 rounded-md text-[7px] font-bold uppercase tracking-widest transition-all bg-purple-600 text-white shadow-sm";
    localBtn.className =
      "px-2 py-1 rounded-md text-[7px] font-bold uppercase tracking-widest transition-all theme-text opacity-40 hover:opacity-100";
    queryInput.placeholder = "Assistance...";
    btn.className =
      "w-8 h-8 bg-purple-600 text-white rounded-full flex items-center justify-center hover:bg-purple-700 active:scale-90 transition-all shadow-lg";
  }
}

function handlePulsarClick() {
  if (isGenerating) stopGeneration();
  else executeStreamSearch();
}

function stopGeneration() {
  if (abortController) {
    abortController.abort();
    isGenerating = false;
    revertPulsar();
  }
}

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
  const query = queryInput.value;
  if (!query.trim()) return;

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
        <div class="${colorClass} text-white p-4 rounded-2xl rounded-tr-none max-w-[80%] shadow-sm text-left">
            <p class="text-[13px] font-medium leading-relaxed">${query}</p>
        </div>
        <span class="text-[8px] font-bold theme-text-sec opacity-30 uppercase tracking-widest mt-1 mr-1">${currentMode === "local" ? "Forensic Researcher" : "Global Analyst"}</span>
    `;
  thread.appendChild(userMsg);
  queryInput.value = "";
  queryInput.style.height = "24px"; // Reset to ultra-slim integrated height
  thread.scrollTop = thread.scrollHeight;

  isGenerating = true;
  abortController = new AbortController();
  btn.classList.remove("bg-blue-600", "bg-purple-600");
  btn.classList.add("bg-gray-800");
  sendIcon.classList.add("hidden");
  stopIcon.classList.remove("hidden");

  // AI Message
  const aiMsgId = "ai-" + Date.now();
  const aiMsg = document.createElement("div");
  aiMsg.className = "flex flex-col items-start w-full message-bubble mb-6";
  const accentColor = currentMode === "local" ? "bg-blue-500" : "bg-purple-500";
  const label = "Assistance";

  aiMsg.innerHTML = `
        <div class="flex items-center gap-2 mb-1.5 ml-1">
            <div class="w-1 h-1 ${accentColor} rounded-full shadow-[0_0_5px_${accentColor}]"></div>
            <span class="text-[7px] font-bold theme-text-sec uppercase tracking-[0.2em] opacity-40">${label}</span>
            <span id="${aiMsgId}-status" class="typing-dot text-[7px] font-bold text-blue-600 uppercase tracking-widest ml-3">Thinking...</span>
        </div>
        <!-- Bubble starts hidden and grows as content arrives -->
        <div id="${aiMsgId}-bubble" class="hidden theme-bg p-4 md:p-5 rounded-xl rounded-tl-none border theme-border shadow-sm max-w-[85%] theme-text relative group/bubble overflow-hidden animate-in fade-in zoom-in-95 duration-300">
            <div id="${aiMsgId}-content" class="markdown-body leading-relaxed opacity-90"></div>
            
            <div id="${aiMsgId}-actions" class="hidden mt-4 flex justify-end items-center gap-2 border-t border-transparent pt-2 group-hover/bubble:border-gray-100 dark:group-hover/bubble:border-gray-800 transition-colors">
                <button onclick="saveInsight('${aiMsgId}', \`${query}\`, '${currentMode}')" 
                        id="${aiMsgId}-save-btn"
                        class="px-3 py-1.5 bg-white dark:bg-gray-800 border theme-border rounded-md text-[7px] font-bold uppercase tracking-widest shadow-sm hover:scale-105 active:scale-95 transition-all flex items-center gap-2 group/save">
                    <svg class="w-2.5 h-2.5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>
                    <span>Save Insight</span>
                </button>
            </div>

            <div id="${aiMsgId}-evidence" class="hidden mt-6 pt-4 border-t border-dashed theme-border">
                <div class="flex items-center justify-between mb-3">
                    <p class="text-[7px] font-bold theme-text-sec uppercase tracking-widest opacity-30">Forensic Source Data</p>
                    <div class="h-[1px] flex-1 mx-3 bg-gray-100 dark:bg-gray-800 opacity-20"></div>
                </div>
                <div id="${aiMsgId}-grid" class="grid grid-cols-1 md:grid-cols-2 gap-3"></div>
            </div>
        </div>
    `;
  thread.appendChild(aiMsg);
  thread.scrollTop = thread.scrollHeight;

  const contentEl = document.getElementById(`${aiMsgId}-content`);
  const statusEl = document.getElementById(`${aiMsgId}-status`);
  const actionsEl = document.getElementById(`${aiMsgId}-actions`);
  let fullText = "";

  try {
    let searchData = { results: [] };
    if (currentMode === "local") {
      const searchResponse = await fetch(
        `/api/search?query=${encodeURIComponent(query)}`,
        { signal: abortController.signal },
      );
      searchData = await searchResponse.json();
      if (searchData.results.length > 0) {
        const grid = document.getElementById(`${aiMsgId}-grid`);
        document
          .getElementById(`${aiMsgId}-evidence`)
          .classList.remove("hidden");
        grid.innerHTML = searchData.results
          .slice(0, 4)
          .map((res) => {
            // Cache thematic data for inspector
            thematicCache[res.id] = res;
            return `
                        <div class="p-3.5 rounded-xl bg-gray-50/50 dark:bg-gray-800/50 border theme-border cursor-pointer hover:border-blue-500 transition-all" onclick="inspectDocument(${res.id})">
                            <div class="flex items-center justify-between mb-1.5">
                                <span class="text-[7px] font-bold text-blue-600 uppercase tracking-widest bg-blue-50 dark:bg-blue-900/20 px-1.5 py-0.5 rounded border border-blue-100 dark:border-blue-800">${res.tag}</span>
                                <span class="text-[7px] theme-text-sec opacity-40">#${res.id}</span>
                            </div>
                            <p class="text-[11px] theme-text-sec line-clamp-2 opacity-70 leading-relaxed">${res.content}</p>
                        </div>
                    `;
          })
          .join("");
      }
    }

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

      // Kinetic Manifestation: Unhide with smooth transition
      if (fullText.length > 0) {
        const bubble = document.getElementById(`${aiMsgId}-bubble`);
        if (bubble.classList.contains("hidden")) {
          bubble.classList.remove("hidden");
          bubble.classList.add("animate-in", "fade-in", "slide-in-from-top-2");
        }
      }

      contentEl.innerHTML = marked.parse(fullText);
      thread.scrollTop = thread.scrollHeight;
      statusEl.innerText = "Responding...";
    }
    statusEl.classList.add("hidden");
    actionsEl.classList.remove("hidden");
  } catch (error) {
    if (error.name === "AbortError")
      contentEl.innerHTML +=
        '<p class="text-[10px] italic opacity-40 mt-4">[Synthesis Terminated]</p>';
    else showToast(error.message, "error");
  } finally {
    isGenerating = false;
    revertPulsar();
  }
}

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

async function inspectDocument(id) {
  const inspector = document.getElementById("inspector-content");
  inspector.innerHTML = `<div class="flex flex-col items-center justify-center h-64"><div class="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div><p class="text-[9px] font-bold uppercase tracking-widest mt-4 opacity-40">Inspecting #${id}...</p></div>`;
  try {
    const response = await fetch(`/api/docs/${id}`);
    const data = await response.json();
    const thematic = thematicCache[id] || {};

    inspector.innerHTML = `
            <div class="space-y-8 message-bubble">
                <section class="space-y-4">
                    <h4 class="text-[9px] font-bold theme-text-sec uppercase tracking-widest opacity-40">Thematic Matrices</h4>
                    <div class="space-y-4">
                        <div class="p-4 rounded-xl border theme-border bg-blue-600/5">
                            <div class="flex items-center justify-between mb-2">
                                <p class="text-[8px] font-bold text-blue-600 uppercase tracking-widest">LDA Topic</p>
                                <span class="text-[7px] font-bold theme-text opacity-30 uppercase italic">Dynamic</span>
                            </div>
                            <p class="text-xs theme-text font-bold mb-3">${thematic.lda_topic_label || "Unlabeled"}</p>
                            <div class="flex flex-wrap gap-1.5">
                                ${Object.keys(thematic.lda_keywords || {})
                                  .map(
                                    (kw) => `
                                    <span class="text-[7px] px-1.5 py-0.5 bg-white dark:bg-gray-800 border theme-border theme-text opacity-60 rounded capitalize">${kw}</span>
                                `,
                                  )
                                  .join("")}
                            </div>
                        </div>
                        <div class="p-4 rounded-xl border theme-border bg-purple-600/5">
                            <div class="flex items-center justify-between mb-2">
                                <p class="text-[8px] font-bold text-purple-600 uppercase tracking-widest">BERT Context</p>
                                <span class="text-[7px] font-bold theme-text opacity-30 uppercase italic">Contextual</span>
                            </div>
                            <p class="text-xs theme-text font-bold mb-3">${thematic.bert_topic_label || "Unprocessed"}</p>
                            <div class="flex flex-wrap gap-1.5">
                                ${(thematic.bert_keywords || [])
                                  .map(
                                    (kw) => `
                                    <span class="text-[7px] px-1.5 py-0.5 bg-white dark:bg-gray-800 border theme-border theme-text opacity-60 rounded capitalize">${kw}</span>
                                `,
                                  )
                                  .join("")}
                            </div>
                        </div>
                    </div>
                </section>
                <section class="space-y-3 pt-6 border-t theme-border">
                    <h4 class="text-[9px] font-bold theme-text-sec uppercase tracking-widest opacity-40">Forensic Controls</h4>
                    <div class="flex flex-col gap-2">
                        <a href="/show/${data.id}" target="_blank" class="w-full py-2.5 bg-blue-600 text-white rounded-lg text-[10px] font-bold uppercase hover:bg-blue-700 transition-all text-center shadow-md shadow-blue-600/10">Open Full Dossier</a>
                        <button onclick="openEditor(${data.id}, \`${data.content.replace(/`/g, "\\`").replace(/\${/g, "\\${")}\`)" class="w-full py-2.5 bg-gray-100 dark:bg-gray-800 theme-text rounded-lg text-[10px] font-bold uppercase hover:bg-gray-200 dark:hover:bg-gray-700 transition-all text-center">Refine in Neural Forge</button>
                        <button onclick="deleteDocument(${data.id})" class="w-full py-2.5 text-red-500 text-[10px] font-bold uppercase hover:bg-red-500/10 transition-all mt-2">Purge from Archive</button>
                    </div>
                </section>
            </div>
        `;
  } catch (error) {
    showToast("Inspection failed", "error");
  }
}
async function deleteDocument(id) {
  if (!confirm("Are you sure you want to permanently purge this document?"))
    return;
  try {
    const response = await fetch(`/api/docs/${id}`, { method: "DELETE" });
    const data = await response.json();
    if (data.status === "success") {
      showToast("Document purged from archive.", "success");
      // Reset Inspector instantly
      document.getElementById("inspector-content").innerHTML = `
                <div class="flex flex-col items-center justify-center h-64 opacity-20 text-center">
                    <p class="text-[9px] font-bold uppercase tracking-widest">Select segment for<br>deep analytics</p>
                </div>
            `;
    } else {
      showToast("Purge failed", "error");
    }
  } catch (error) {
    showToast("Network error", "error");
  }
}
