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

  function injectLightTheme() {
    if (document.getElementById("legecyLightTheme")) return;
    const style = document.createElement("style");
    style.id = "legecyLightTheme";
    style.textContent = `
      :root{--bg:#f6f8f7!important;--panel:#ffffff!important;--panel2:#f1f5f3!important;--line:#dce5e0!important;--text:#101714!important;--muted:#64716b!important;--green:#16a35a!important;--green2:#0f8f4d!important;--purple:#7657d9!important;--red:#d84f5e!important;--yellow:#b27a00!important}
      body{background:radial-gradient(circle at 82% -12%,rgba(22,163,90,.10),transparent 30%),radial-gradient(circle at 8% 18%,rgba(118,87,217,.07),transparent 25%),#f6f8f7!important;color:#101714!important}
      body:before{opacity:.32!important;background-image:linear-gradient(rgba(16,23,20,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(16,23,20,.035) 1px,transparent 1px)!important}
      header{border-bottom-color:#dce5e0!important}
      .mark{border-color:rgba(22,163,90,.35)!important;background:rgba(22,163,90,.06)!important;box-shadow:0 8px 24px rgba(22,163,90,.10)!important;color:#16a35a!important}
      .logo{color:#101714!important}.logo span{color:#16a35a!important}.header-right{color:#64716b!important}.dot{background:#16a35a!important;box-shadow:0 0 10px rgba(22,163,90,.35)!important}
      .hero p{color:#64716b!important}.eyebrow{color:#16a35a!important}
      .search{background:rgba(255,255,255,.90)!important;border-color:#d5e0da!important;box-shadow:0 16px 50px rgba(22,42,31,.08)!important}
      .search input{color:#101714!important}.search input::placeholder{color:#8a9690!important}.search button{background:#16a35a!important;color:#fff!important}.search button:hover{background:#0f8f4d!important}
      .walletbar,.card{background:rgba(255,255,255,.92)!important;border-color:#dce5e0!important;box-shadow:0 10px 35px rgba(22,42,31,.07)!important}
      .address{color:#44534b!important}.label{color:#708078!important}.live{color:#16a35a!important}
      .score-ring{background:conic-gradient(#16a35a var(--score,0),#e2e9e5 0)!important}.score-ring:after,.sm-score:after{background:#fff!important;border-color:#e0e8e3!important}
      .score,.rep-copy h2,.section-title h3,.sm-copy h3{color:#101714!important}.score small,.sm-score-value small{color:#718078!important}.rating{color:#16a35a!important}
      .stat .value,.mini-stat strong,.metric .val{color:#101714!important}.stat .sub,.section-title span,.metric .name{color:#718078!important}
      .metric{background:#f7faf8!important;border-color:#e1e9e4!important}.signal{color:#4d5d55!important;background:#f1f6f3!important;border-color:#dce6e0!important}
      .protocol-head span:first-child,td{color:#33423a!important}.protocol-head span:last-child{color:#16a35a!important}.bar{background:#e2e9e5!important}.bar i{background:linear-gradient(90deg,#0f8f4d,#16a35a)!important}
      .sm-score{background:conic-gradient(#7657d9 var(--sm-score,0),#e5e2f3 0)!important}.sm-rating{color:#7657d9!important}.sm-copy p,.sm-confidence{color:#68766f!important}.sm-confidence strong{color:#16a35a!important}.sm-risk .signal{border-color:rgba(216,79,94,.22)!important;color:#a33f4b!important;background:#fff5f6!important}
      th{color:#718078!important}td{border-bottom-color:#e1e8e4!important}.empty{color:#829088!important}
      footer{border-top-color:#dce5e0!important;color:#718078!important}
      .le-nav{display:flex;align-items:center;gap:22px;margin-left:auto;margin-right:24px}.le-nav a{font-size:12px;color:#526159;text-decoration:none;font-weight:650}.le-nav a:hover{color:#16a35a}.le-nav .le-nav-active{color:#16a35a}
      .le-social{display:inline-flex!important;align-items:center;gap:8px}.le-social a{color:#526159;text-decoration:none}.le-social a:hover{color:#16a35a}
      @media(max-width:900px){.le-nav{gap:12px;margin-right:12px}.le-nav a:nth-child(n+4){display:none}}
      @media(max-width:650px){.le-nav{display:none}}
    `;
    document.head.appendChild(style);
  }

  function injectNavigation() {
    if (document.getElementById("legecyMainNav")) return;
    const header = document.querySelector("header");
    if (!header) return;
    const nav = document.createElement("nav");
    nav.id = "legecyMainNav";
    nav.className = "le-nav";
    nav.innerHTML = `
      <a class="le-nav-active" href="/">Intelligence</a>
      <a href="/#dashboard">Analysis</a>
      <a href="/docs/">Docs</a>
      <a href="https://github.com/BuildLEGECY/LEGECY" target="_blank" rel="noopener noreferrer">GitHub</a>
      <a href="https://x.com/BuildLEGECY" target="_blank" rel="noopener noreferrer">𝕏</a>`;
    const right = header.querySelector(".header-right");
    header.insertBefore(nav, right || null);
  }

  function injectFooterLinks() {
    const footer = document.querySelector("footer");
    if (!footer || document.getElementById("legecyFooterSocial")) return;
    const links = document.createElement("span");
    links.id = "legecyFooterSocial";
    links.className = "le-social";
    links.innerHTML = `<a href="/docs/">Docs</a><span>·</span><a href="https://x.com/BuildLEGECY" target="_blank" rel="noopener noreferrer">𝕏 @BuildLEGECY</a><span>·</span><a href="https://github.com/BuildLEGECY/LEGECY" target="_blank" rel="noopener noreferrer">GitHub</a>`;
    footer.appendChild(links);
  }

  function injectStyles() {
    if (document.getElementById("legecyEnhancementStyles")) return;
    const style = document.createElement("style");
    style.id = "legecyEnhancementStyles";
    style.textContent = `
      .le-enhance-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:14px}
      .le-panel-actions{display:flex;gap:8px;align-items:center}
      .le-input{width:100%;border:1px solid #dce5e0;border-radius:10px;background:#f7faf8;color:#101714;padding:10px 11px;outline:0;font:12px inherit}
      .le-input:focus{border-color:#16a35a}
      .le-btn{border:1px solid #d3ded8;border-radius:9px;background:#fff;color:#405048;padding:9px 12px;font:700 11px inherit;cursor:pointer}
      .le-btn:hover{border-color:#16a35a;color:#16a35a}.le-btn.primary{background:#16a35a;color:#fff;border-color:#16a35a}
      .le-row{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 0;border-bottom:1px solid #e1e8e4}
      .le-row:last-child{border-bottom:0}.le-wallet{font:11px ui-monospace,SFMono-Regular,Menlo,monospace;color:#3d4d45}.le-meta{font-size:10px;color:#75837c;margin-top:4px}
      .le-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-top:12px}.le-mini{background:#f7faf8;border:1px solid #e1e9e4;border-radius:10px;padding:10px}.le-mini b{display:block;font-size:14px;color:#101714}.le-mini span{font-size:9px;color:#718078;text-transform:uppercase;letter-spacing:.7px}
      .le-rank{font-size:12px;font-weight:850;color:#16a35a;width:25px}.le-empty{color:#829088;font-size:11px;padding:8px 0}.le-error{color:#d84f5e;font-size:11px;padding:8px 0}
      .le-form{display:flex;gap:8px;margin-bottom:10px}.le-form .le-input{flex:1}.le-current{font-size:10px;color:#718078;margin-bottom:9px}
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
    injectLightTheme();
    injectNavigation();
    injectFooterLinks();
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
