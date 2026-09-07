(()=>{
  if(window.__legecyPremiumBackground) return;
  window.__legecyPremiumBackground=true;

  const css=`
    :root{
      --le-bg:#020806;
      --le-panel:rgba(5,18,16,.72);
      --le-panel-2:rgba(8,27,23,.82);
      --le-border:rgba(65,226,166,.20);
      --le-green:#00e889;
      --le-green-soft:rgba(0,232,137,.18);
      --le-purple:#8b6cff;
      --le-text:#f4fff9;
      --le-muted:#91aaa1;
    }

    body{
      position:relative!important;
      isolation:isolate!important;
      overflow-x:hidden!important;
      background:#020806!important;
      color:var(--le-text)!important;
    }

    /* Deep-space / Solana-style environment behind the existing application. */
    .le-bg-premium{
      position:fixed;inset:0;z-index:-20;pointer-events:none;overflow:hidden;
      background:
        radial-gradient(900px 600px at 76% 32%,rgba(0,232,137,.14),transparent 64%),
        radial-gradient(780px 560px at 91% 40%,rgba(139,108,255,.16),transparent 65%),
        radial-gradient(700px 500px at 20% 75%,rgba(0,190,120,.12),transparent 68%),
        linear-gradient(180deg,#020806 0%,#030d0a 48%,#020608 100%);
    }

    .le-bg-premium:before{
      content:"";position:absolute;inset:0;opacity:.30;
      background-image:
        linear-gradient(rgba(80,255,202,.045) 1px,transparent 1px),
        linear-gradient(90deg,rgba(80,255,202,.045) 1px,transparent 1px);
      background-size:58px 58px;
      mask-image:linear-gradient(to bottom,rgba(0,0,0,.95),rgba(0,0,0,.4) 78%,transparent);
    }

    .le-bg-premium:after{
      content:"";position:absolute;left:-10%;right:-10%;bottom:-5%;height:44%;
      background:
        radial-gradient(ellipse at 15% 100%,rgba(0,232,137,.28),transparent 42%),
        radial-gradient(ellipse at 78% 100%,rgba(139,108,255,.24),transparent 44%),
        linear-gradient(175deg,transparent 0 45%,rgba(0,0,0,.82) 74%);
      clip-path:polygon(0 45%,7% 34%,14% 49%,22% 25%,31% 48%,40% 36%,49% 52%,58% 29%,67% 46%,76% 21%,84% 48%,92% 31%,100% 43%,100% 100%,0 100%);
      filter:blur(2px);
      opacity:.72;
    }

    .le-bg-aurora{position:absolute;inset:-25%;filter:blur(72px);opacity:.60;transform:translateZ(0)}
    .le-bg-aurora span{position:absolute;display:block;border-radius:50%;mix-blend-mode:screen}
    .le-bg-aurora .a{width:48vw;height:25vw;left:46%;top:3%;background:rgba(0,232,137,.12);transform:rotate(-17deg);animation:leAuroraA 17s ease-in-out infinite}
    .le-bg-aurora .b{width:42vw;height:24vw;right:-8%;top:27%;background:rgba(139,108,255,.13);transform:rotate(18deg);animation:leAuroraB 21s ease-in-out infinite}
    .le-bg-aurora .c{width:45vw;height:20vw;left:25%;bottom:-4%;background:rgba(0,190,120,.10);transform:rotate(8deg);animation:leAuroraC 19s ease-in-out infinite}

    .le-bg-orb{position:absolute;border-radius:50%;border:1px solid rgba(0,232,137,.15);box-shadow:0 0 100px rgba(0,232,137,.07);animation:leBgFloat 12s ease-in-out infinite}
    .le-bg-orb.o1{width:560px;height:560px;right:-260px;top:100px}
    .le-bg-orb.o2{width:340px;height:340px;left:-180px;top:42%;border-color:rgba(139,108,255,.16);animation-delay:-4s}
    .le-bg-orb.o3{width:760px;height:760px;left:36%;bottom:-620px;border-color:rgba(0,232,137,.10);animation-delay:-7s}

    .le-bg-scan{position:absolute;left:-10%;right:-10%;height:1px;top:12%;background:linear-gradient(90deg,transparent,rgba(0,232,137,.22),transparent);box-shadow:0 0 28px rgba(0,232,137,.12);animation:leScan 14s ease-in-out infinite}

    .le-bg-particles{position:absolute;inset:0}
    .le-bg-particles i{position:absolute;width:3px;height:3px;border-radius:50%;background:#00e889;opacity:.28;box-shadow:0 0 10px rgba(0,232,137,.70);animation:leParticle 7s ease-in-out infinite}
    .le-bg-particles i:nth-child(2n){background:#8b6cff;box-shadow:0 0 10px rgba(139,108,255,.65);animation-duration:9s}
    .le-bg-particles i:nth-child(3n){width:2px;height:2px;opacity:.20;animation-duration:11s}

    /* Premium dark application surface. No data, API or interaction is changed. */
    header{
      background:rgba(2,10,8,.78)!important;
      border-bottom:1px solid rgba(61,214,165,.16)!important;
      box-shadow:0 12px 40px rgba(0,0,0,.20)!important;
      backdrop-filter:blur(18px)!important;
    }
    header .logo{color:#f4fff9!important}
    header .logo span{color:var(--le-green)!important}
    header .le-social a,.le-nav a{color:#d7e7e0!important}
    header .le-social a:hover,.le-nav a:hover{color:var(--le-green)!important}
    header .mark{background:linear-gradient(145deg,#071a15,#0a2b21)!important;border:1px solid rgba(0,232,137,.34)!important;box-shadow:0 0 30px rgba(0,232,137,.18)!important}
    header .mark:before{background:linear-gradient(145deg,#09241c,#0a1512)!important;color:#fff!important}

    .le-countdown{
      background:rgba(4,19,16,.82)!important;
      border-color:rgba(0,232,137,.28)!important;
      box-shadow:0 0 28px rgba(0,232,137,.07),inset 0 0 20px rgba(0,232,137,.025)!important;
    }
    .le-countdown-status{border-right-color:rgba(76,226,177,.22)!important}
    .le-countdown-copy strong{color:#effff8!important}
    .le-countdown-copy span,.le-countdown-unit span{color:#7d9890!important}
    .le-countdown-unit b{color:var(--le-green)!important;text-shadow:0 0 14px rgba(0,232,137,.18)}
    .le-countdown-sep{color:#527b6b!important}

    .hero{
      background:transparent!important;
      min-height:650px!important;
      padding-top:62px!important;
    }
    .hero:after{
      border-color:rgba(0,232,137,.10)!important;
      box-shadow:0 0 120px rgba(0,232,137,.08)!important;
    }
    .hero:before{border-color:rgba(139,108,255,.16)!important}
    .eyebrow{
      background:rgba(0,232,137,.07)!important;
      border-color:rgba(0,232,137,.32)!important;
      color:#55f2b6!important;
      box-shadow:0 0 24px rgba(0,232,137,.06)!important;
    }
    .hero h1{color:#f6fffb!important;text-shadow:0 10px 45px rgba(0,0,0,.28)!important}
    .hero h1:after{box-shadow:0 0 22px rgba(0,232,137,.75)!important}
    .hero p{color:#9ab1a8!important}

    .search{
      background:rgba(3,15,12,.84)!important;
      border-color:rgba(72,224,177,.25)!important;
      box-shadow:0 24px 65px rgba(0,0,0,.28),inset 0 0 24px rgba(0,232,137,.025)!important;
      backdrop-filter:blur(14px)!important;
    }
    .search input{color:#f2fff9!important;background:transparent!important}
    .search input::placeholder{color:#617c71!important}
    .search button{background:linear-gradient(135deg,#00f18d,#00bd6f)!important;color:#00150d!important;box-shadow:0 0 30px rgba(0,232,137,.20)!important}

    /* Make the existing hero intelligence object feel integrated into the environment. */
    .le-visual,.le-premium-hero{filter:drop-shadow(0 28px 50px rgba(0,0,0,.30))!important}
    .le-float-card,.le-premium-label{
      background:rgba(5,19,16,.78)!important;
      border-color:rgba(76,226,177,.22)!important;
      color:#8fa8a0!important;
      box-shadow:0 20px 50px rgba(0,0,0,.30),inset 0 0 22px rgba(0,232,137,.025)!important;
      backdrop-filter:blur(18px)!important;
    }
    .le-float-card strong,.le-premium-label strong{color:#f1fff9!important}
    .le-float-card b{color:var(--le-green)!important}

    .le-wallet-body,.le-premium-node{
      box-shadow:0 24px 55px rgba(0,0,0,.42),0 0 42px rgba(0,232,137,.12),inset 0 0 30px rgba(77,255,207,.12)!important;
    }

    .le-feature-strip{margin-top:6px!important}
    .le-feature,.le-stat,.le-why-card,.card,.walletbar{
      background:linear-gradient(145deg,rgba(5,19,16,.82),rgba(4,13,12,.74))!important;
      border-color:rgba(72,224,177,.17)!important;
      box-shadow:0 18px 45px rgba(0,0,0,.22),inset 0 1px 0 rgba(255,255,255,.025)!important;
      color:#edf9f4!important;
      backdrop-filter:blur(14px)!important;
    }
    .le-feature:hover,.le-why-card:hover{border-color:rgba(0,232,137,.34)!important;box-shadow:0 22px 55px rgba(0,0,0,.30),0 0 25px rgba(0,232,137,.06)!important}
    .le-feature strong,.le-why-card h3,.le-stat b{color:#f1fff9!important}
    .le-feature span,.le-stat span,.le-why-card p{color:#819b91!important}
    .le-feature .ico{background:rgba(0,232,137,.08)!important;color:#00e889!important;border:1px solid rgba(0,232,137,.18)!important}
    .le-stats{background:rgba(3,13,11,.80)!important;border-color:rgba(72,224,177,.17)!important}
    .le-stat{border-right-color:rgba(72,224,177,.12)!important}
    .le-section-intro h2{color:#f4fff9!important}
    .le-section-intro p{color:#819b91!important}

    .metric,.le-mini{background:rgba(6,20,17,.82)!important;border-color:rgba(72,224,177,.13)!important;color:#e8f6f0!important}
    .signal{background:rgba(0,232,137,.055)!important;border-color:rgba(0,232,137,.16)!important;color:#9eb7ad!important}
    .section-title h3,.rep-copy h2,.score,.stat .value,.metric .val,.mini-stat strong,.sm-copy h3{color:#f1fff9!important}
    .label,.section-title span,.metric .name,.stat .sub{color:#78948a!important}
    .address{color:#b3c8c0!important}
    .bar{background:rgba(125,155,145,.15)!important}
    .bar i{background:linear-gradient(90deg,#00bd6f,#00f18d)!important;box-shadow:0 0 12px rgba(0,232,137,.18)}
    .positive{color:#35e89e!important}.negative{color:#ff7080!important}

    .le-input{background:rgba(2,12,10,.75)!important;border-color:rgba(72,224,177,.17)!important;color:#ecfff7!important}
    .le-input::placeholder{color:#617b71!important}
    .le-btn{background:rgba(8,24,20,.82)!important;border-color:rgba(72,224,177,.16)!important;color:#b9cec6!important}
    .le-btn.primary{background:linear-gradient(135deg,#00df82,#00b96d)!important;color:#00170e!important;border-color:#00df82!important;box-shadow:0 0 22px rgba(0,232,137,.13)!important}
    .le-row{border-bottom-color:rgba(72,224,177,.10)!important}
    .le-wallet{color:#c2d4cd!important}.le-meta,.le-current{color:#718c82!important}
    .le-rank{color:#00e889!important}.le-empty{color:#718c82!important}.le-error{color:#ff7180!important}

    footer{border-top-color:rgba(72,224,177,.12)!important;color:#6f8a80!important;background:rgba(2,8,7,.35)!important}
    footer strong{color:#f0fff8!important}

    @keyframes leBgDrift{0%{transform:translate3d(0,0,0)}50%{transform:translate3d(2%,1%,0)}100%{transform:translate3d(0,0,0)}}
    @keyframes leAuroraA{0%,100%{transform:translate3d(0,0,0) rotate(-17deg)}50%{transform:translate3d(-5%,4%,0) rotate(-12deg)}}
    @keyframes leAuroraB{0%,100%{transform:translate3d(0,0,0) rotate(18deg)}50%{transform:translate3d(5%,-4%,0) rotate(25deg)}}
    @keyframes leAuroraC{0%,100%{transform:translate3d(0,0,0) rotate(8deg)}50%{transform:translate3d(-5%,-5%,0) rotate(14deg)}}
    @keyframes leBgFloat{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-20px) scale(1.015)}}
    @keyframes leScan{0%,100%{transform:translateY(0);opacity:0}15%{opacity:1}55%{transform:translateY(68vh);opacity:.7}75%{opacity:0}}
    @keyframes leParticle{0%,100%{transform:translate3d(0,0,0);opacity:.16}50%{transform:translate3d(12px,-18px,0);opacity:.46}}

    @media(prefers-reduced-motion:reduce){.le-bg-premium *{animation:none!important}.le-bg-scan{display:none}}
    @media(max-width:1050px){.le-bg-aurora{opacity:.72}.le-bg-orb.o1{width:380px;height:380px}.le-bg-orb.o3{width:520px;height:520px}}
    @media(max-width:800px){.hero{min-height:670px!important}.le-bg-aurora{opacity:.62}.le-bg-premium:before{background-size:40px 40px}.le-bg-premium:after{height:36%}.le-countdown{transform:scale(.88);transform-origin:left center}.le-feature-strip,.le-why,.le-enhance-grid,.le-stats{grid-template-columns:1fr 1fr!important}}
    @media(max-width:560px){.le-countdown{display:none!important}.hero{min-height:650px!important}.le-feature-strip,.le-why,.le-enhance-grid,.le-stats{grid-template-columns:1fr!important}.le-bg-premium:after{height:30%}}
  `;

  const style=document.createElement('style');
  style.id='legecyPremiumBackgroundCss';
  style.textContent=css;
  document.head.appendChild(style);

  function mount(){
    if(document.querySelector('.le-bg-premium')) return;
    const bg=document.createElement('div');
    bg.className='le-bg-premium';
    bg.setAttribute('aria-hidden','true');
    const particles=Array.from({length:34},(_,i)=>{
      const left=(i*37+11)%97;
      const top=(i*61+7)%94;
      const delay=-(i%9)*.8;
      return `<i style="left:${left}%;top:${top}%;animation-delay:${delay}s"></i>`;
    }).join('');
    bg.innerHTML=`<div class="le-bg-aurora"><span class="a"></span><span class="b"></span><span class="c"></span></div><div class="le-bg-orb o1"></div><div class="le-bg-orb o2"></div><div class="le-bg-orb o3"></div><div class="le-bg-scan"></div><div class="le-bg-particles">${particles}</div>`;
    document.body.prepend(bg);
  }

  if(document.readyState==='loading') document.addEventListener('DOMContentLoaded',mount,{once:true});
  else mount();
})();
