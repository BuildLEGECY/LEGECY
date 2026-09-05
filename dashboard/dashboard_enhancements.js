(() => {
  const ORIGINAL = "https://raw.githubusercontent.com/BuildLEGECY/LEGECY/87b087ae07de90020c427595b85046157c0dcd43/dashboard/dashboard_enhancements.js";
  const MASCOT = "https://github.com/BuildLEGECY.png";

  function applyBranding() {
    if (document.getElementById("legecyMascotBranding")) return;
    const style = document.createElement("style");
    style.id = "legecyMascotBranding";
    style.textContent = `
      .mark:before{content:""!important;display:block!important;width:100%!important;height:100%!important;background:url("${MASCOT}") center/cover no-repeat!important}
      .mark:after{display:none!important}
      .mark{background:#fff!important;overflow:hidden!important;border:1px solid #dce9e3!important}
    `;
    document.head.appendChild(style);

    const mark = document.querySelector("header .mark");
    if (mark) {
      mark.setAttribute("aria-label", "LEGECY mascot");
      mark.setAttribute("title", "LEGECY");
    }

    const hero = document.querySelector(".le-mascot");
    if (hero) {
      hero.innerHTML = "";
      hero.style.background = `url("${MASCOT}") center/cover no-repeat`;
      hero.style.display = "block";
    }
  }

  function loadOriginal() {
    const script = document.createElement("script");
    script.src = ORIGINAL;
    script.onload = () => {
      applyBranding();
      const observer = new MutationObserver(() => applyBranding());
      observer.observe(document.body, { childList: true, subtree: true });
      setTimeout(() => observer.disconnect(), 10000);
    };
    script.onerror = () => {
      console.error("LEGECY enhancement bundle failed to load.");
      applyBranding();
    };
    document.head.appendChild(script);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", loadOriginal, { once: true });
  } else {
    loadOriginal();
  }
})();
