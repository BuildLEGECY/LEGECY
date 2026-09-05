(() => {
  const API = window.LEGECY_API_URL || "";
  const esc = (value) => String(value ?? "").replace(/[&<>\"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
  const short = (value) => {
    const s = String(value || "");
    return s.length > 18 ? `${s.slice(0, 8)}…${s.slice(-8)}` : s;
  };
  const request = async (url, options = {}) => {
    const response = await fetch(`${API}${url}`, { headers: { "Content-Type": "application/json" }, ...options });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail?.message || data.detail || "Request failed.");
    return data;
  };

  function injectStyles() {
    if (document.getElementById("legecyEnhancementStyles")) return;
    const style = document.createElement("style");
    style.id = "legecyEnhancementStyles";
    style.textContent = `
      .le-enhance-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
      .le-panel-actions{display:flex;gap:8px;align-items:center}
      .le-input{width:100%;border:1px solid #202a35;border-radius:10px;background:#0a0f15;color:#fff;padding:10px 11px;outline:0;font:12px inherit}
      .le-input:focus{border-color:#78f5a2}
      .le-btn{border:1px solid #26313d;border-radius:9px;background:#111821;color:#c9d1da;padding:9px 12px;font:700 11px inherit;cursor:pointer}
      .le-btn:hover{border-color:#78f5a2;color:#78f5a2}.le-btn.primary{background:#78f5a2;color:#07100a;border-color:#78f5a2}
      .le-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 0;border-bottom:1px solid #18212a}
      .le-row:last-child{border-bottom:0}.le-wallet{font:11px ui-monospace,SFMono-Regular,Menlo,monospace;color:#c5ced8}.le-meta{font-size:10px;color:#657280;margin-top:4px}
      .le-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}.le-mini{background:#0a0f15;border:1px solid #17202a;border-radius:10px;padding:10px}.le-mini b{display:block;font-size:14px}.le-mini span{font-size:9px;color:#667381;text-transform:uppercase;letter-spacing:.7px}
      .le-rank{font-size:12px;font-weight:850;color:#78f5a2;width:25px}.le-empty{color:#596675;font-size:11px;padding:8px 0}.le-error{color:#ff6f7d;font-size:11px;padding:8px 0}
      .le-form{display:flex;gap:8px;margin-bottom:10px}.le-form .le-input{flex:1}.le-current{font-size:10px;color:#697684;margin-bottom:9px}
      @media(max-width:800px){.le-enhance-grid{grid-template-columns:1fr}.le-grid{grid-template-columns:1fr 1fr}.le-form{flex-direction:column}}
    `;
    document.head.appendChild(style);
  }

  function panelMarkup() {
    const section = document.createElement("section");
    section.className = "le-enhance-grid";
    section.id = "legecyEnhancements";
    section.innerHTML = `
      <div class="card">
        <div class="section-title"><h3>Watchlist</h3><span>Tracked wallets</span></div>
        <div class="le-form"><input id="leWatchLabel" class="le-input" placeholder="Label for current wallet"><button id="leWatchAdd" class="le-btn primary">Add wallet</button></div>
        <div id="leWatchCurrent" class="le-current">Analyze a wallet to add it to your watchlist.</div>
        <div id="leWatchList" class="le-empty">Loading watchlist…</div>
      </div>
      <div class="card">
        <div class="section-title"><h3>Smart Money Ranking</h3><span>Confidence-adjusted</span></div>
        <div class="le-form"><input id="leRankWallet" class="le-input" placeholder="Seed wallet address"><button id="leRankRun" class="le-btn primary">Rank wallets</button></div>
        <div id="leRankStatus" class="le-current">Use the analyzed wallet as a seed, or enter another wallet.</div>
        <div id="leRankList" class="le-empty">No ranking loaded.</div>
      </div>`;
    return section;
  }

  let currentWallet = "";

  async function loadWatchlist() {
    const target = document.getElementById("leWatchList");
    try {
      const items = await request("/watchlist");
      if (!items.length) { target.innerHTML = '<div class="le-empty">No wallets are being watched.</div>'; return; }
      target.innerHTML = items.map((item) => `
        <div class="le-row"><div><div class="le-wallet">${esc(short(item.wallet))}</div><div class="le-meta">${esc(item.label || "Unlabeled")}</div></div><button class="le-btn" data-remove-wallet="${esc(item.wallet)}">Remove</button></div>`).join("");
      target.querySelectorAll("[data-remove-wallet]").forEach((button) => button.addEventListener("click", async () => {
        button.disabled = true;
        try { await request(`/watchlist/${encodeURIComponent(button.dataset.removeWallet)}`, { method: "DELETE" }); await loadWatchlist(); }
        catch (error) { alert(error.message); button.disabled = false; }
      }));
    } catch (error) { target.innerHTML = `<div class="le-error">${esc(error.message)}</div>`; }
  }

  async function addCurrentWallet() {
    if (!currentWallet) { alert("Analyze a wallet first."); return; }
    const button = document.getElementById("leWatchAdd");
    button.disabled = true;
    try {
      await request("/watchlist", { method: "POST", body: JSON.stringify({ wallet: currentWallet, label: document.getElementById("leWatchLabel").value.trim() }) });
      document.getElementById("leWatchLabel").value = "";
      await loadWatchlist();
    } catch (error) { alert(error.message); }
    finally { button.disabled = false; }
  }

  async function runRanking() {
    const wallet = document.getElementById("leRankWallet").value.trim();
    const status = document.getElementById("leRankStatus");
    const target = document.getElementById("leRankList");
    if (!wallet) { status.textContent = "Enter a seed wallet address."; return; }
    status.textContent = "Finding and ranking wallets…";
    target.innerHTML = "";
    const button = document.getElementById("leRankRun"); button.disabled = true;
    try {
      const data = await request(`/rank/${encodeURIComponent(wallet)}`);
      const rows = Array.isArray(data.ranked_wallets) ? data.ranked_wallets : [];
      status.textContent = `${rows.length} wallet${rows.length === 1 ? "" : "s"} passed the confidence filter.`;
      if (!rows.length) { target.innerHTML = '<div class="le-empty">No wallets met the current confidence threshold.</div>'; return; }
      target.innerHTML = rows.slice(0, 10).map((row) => `
        <div class="le-row"><div class="le-rank">#${esc(row.rank)}</div><div style="flex:1"><div class="le-wallet">${esc(short(row.wallet))}</div><div class="le-grid">
          <div class="le-mini"><b>${esc(row.ranking_score)}</b><span>Ranking</span></div>
          <div class="le-mini"><b>${esc(row.smart_money_score)}</b><span>Smart Money</span></div>
          <div class="le-mini"><b>${esc(row.reputation_score)}</b><span>Reputation</span></div>
          <div class="le-mini"><b>${esc(row.confidence)}</b><span>Confidence</span></div>
        </div></div></div>`).join("");
    } catch (error) { status.textContent = "Ranking failed."; target.innerHTML = `<div class="le-error">${esc(error.message)}</div>`; }
    finally { button.disabled = false; }
  }

  function hookWalletAnalysis() {
    const original = window.renderProfile;
    if (typeof original !== "function" || window.__legecyProfileHooked) return;
    window.__legecyProfileHooked = true;
    window.renderProfile = function (data) {
      original.apply(this, arguments);
      currentWallet = data?.wallet || "";
      const current = document.getElementById("leWatchCurrent");
      const rank = document.getElementById("leRankWallet");
      if (current) current.textContent = currentWallet ? `Current wallet: ${short(currentWallet)}` : "Analyze a wallet to add it to your watchlist.";
      if (rank && currentWallet) rank.value = currentWallet;
      document.getElementById("legecyEnhancements")?.scrollIntoView({ behavior: "smooth", block: "start" });
    };
  }

  function init() {
    if (document.getElementById("legecyEnhancements")) return;
    injectStyles();
    const dashboard = document.getElementById("dashboard");
    if (!dashboard) return;
    const panel = panelMarkup();
    dashboard.appendChild(panel);
    document.getElementById("leWatchAdd").addEventListener("click", addCurrentWallet);
    document.getElementById("leRankRun").addEventListener("click", runRanking);
    document.getElementById("leRankWallet").addEventListener("keydown", (event) => { if (event.key === "Enter") runRanking(); });
    hookWalletAnalysis();
    loadWatchlist();
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
