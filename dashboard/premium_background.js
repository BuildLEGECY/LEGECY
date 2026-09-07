(()=>{
  if(window.__legecyPremiumBackground) return;
  window.__legecyPremiumBackground=true;

  const css=`
    :root{
      --le-bg-ink:#07140f;
      --le-bg-green:#08c76b;
      --le-bg-green-soft:rgba(8,199,107,.16);
      --le-bg-purple:rgba(118,87,223,.13);
    }

    body{position:relative;isolation:isolate;overflow-x:hidden}

    .le-bg-premium{
      position:fixed;inset:0;z-index:-20;pointer-events:none;overflow:hidden;
      background:
        radial-gradient(900px 520px at 78% 8%,rgba(8,199,107,.13),transparent 68%),
        radial-gradient(720px 520px at 12% 45%,rgba(118,87,223,.09),transparent 70%),
        radial-gradient(680px 460px at 52% 105%,rgba(8,199,107,.075),transparent 72%),
        linear-gradient(180deg,#fbfefd 0%,#f5faf7 48%,#f1f8f4 100%);
    }

    .le-bg-premium:before{
      content:"";position:absolute;inset:0;opacity:.34;
      background-image:
        linear-gradient(rgba(9,45,31,.035) 1px,transparent 1px),
        linear-gradient(90deg,rgba(9,45,31,.035) 1px,transparent 1px);
      background-size:52px 52px;
      mask-image:linear-gradient(to bottom,rgba(0,0,0,.9),rgba(0,0,0,.32) 72%,transparent);
    }

    .le-bg-premium:after{
      content:"";position:absolute;inset:-20%;
      background:
        radial-gradient(circle at 20% 30%,rgba(8,199,107,.08) 0 1px,transparent 2px),
        radial-gradient(circle at 72% 24%,rgba(118,87,223,.08) 0 1px,transparent 2px),
        radial-gradient(circle at 56% 78%,rgba(8,199,107,.07) 0 1px,transparent 2px);
      background-size:170px 170px,210px 210px,190px 190px;
      animation:leBgDrift 26s linear infinite;
    }

    .le-bg-aurora{position:absolute;inset:-25%;filter:blur(55px);opacity:.48;transform:translateZ(0)}
    .le-bg-aurora span{position:absolute;display:block;border-radius:50%;mix-blend-mode:multiply}
    .le-bg-aurora .a{width:48vw;height:24vw;left:48%;top:4%;background:rgba(8,199,107,.10);transform:rotate(-17deg);animation:leAuroraA 16s ease-in-out infinite}
    .le-bg-aurora .b{width:40vw;height:22vw;left:-4%;top:30%;background:rgba(118,87,223,.075);transform:rotate(21deg);animation:leAuroraB 20s ease-in-out infinite}
    .le-bg-aurora .c{width:42vw;height:18vw;left:38%;bottom:-5%;background:rgba(8,199,107,.065);transform:rotate(8deg);animation:leAuroraC 18s ease-in-out infinite}

    .le-bg-orb{position:absolute;border-radius:50%;border:1px solid rgba(8,199,107,.12);box-shadow:0 0 70px rgba(8,199,107,.06);animation:leBgFloat 11s ease-in-out infinite}
    .le-bg-orb.o1{width:420px;height:420px;right:-180px;top:110px}
    .le-bg-orb.o2{width:270px;height:270px;left:-130px;top:48%;border-color:rgba(118,87,223,.11);animation-delay:-4s}
    .le-bg-orb.o3{width:620px;height:620px;left:38%;bottom:-500px;border-color:rgba(8,199,107,.075);animation-delay:-7s}

    .le-bg-scan{position:absolute;left:-10%;right:-10%;height:1px;top:18%;background:linear-gradient(90deg,transparent,rgba(8,199,107,.13),transparent);box-shadow:0 0 18px rgba(8,199,107,.09);animation:leScan 12s ease-in-out infinite}

    .le-bg-particles{position:absolute;inset:0}
    .le-bg-particles i{position:absolute;width:3px;height:3px;border-radius:50%;background:#08bf68;opacity:.24;box-shadow:0 0 9px rgba(8,191,104,.55);animation:leParticle 7s ease-in-out infinite}
    .le-bg-particles i:nth-child(2n){background:#7657df;box-shadow:0 0 9px rgba(118,87,223,.5);animation-duration:9s}
    .le-bg-particles i:nth-child(3n){width:2px;height:2px;opacity:.18;animation-duration:11s}

    @keyframes leBgDrift{0%{transform:translate3d(0,0,0)}50%{transform:translate3d(2%,1%,0)}100%{transform:translate3d(0,0,0)}}
    @keyframes leAuroraA{0%,100%{transform:translate3d(0,0,0) rotate(-17deg)}50%{transform:translate3d(-5%,4%,0) rotate(-12deg)}}
    @keyframes leAuroraB{0%,100%{transform:translate3d(0,0,0) rotate(21deg)}50%{transform:translate3d(7%,-4%,0) rotate(27deg)}}
    @keyframes leAuroraC{0%,100%{transform:translate3d(0,0,0) rotate(8deg)}50%{transform:translate3d(-5%,-5%,0) rotate(14deg)}}
    @keyframes leBgFloat{0%,100%{transform:translateY(0) scale(1)}50%{transform:translateY(-18px) scale(1.015)}}
    @keyframes leScan{0%,100%{transform:translateY(0);opacity:0}15%{opacity:1}55%{transform:translateY(62vh);opacity:.7}75%{opacity:0}}
    @keyframes leParticle{0%,100%{transform:translate3d(0,0,0);opacity:.16}50%{transform:translate3d(12px,-18px,0);opacity:.42}}

    @media(prefers-reduced-motion:reduce){.le-bg-premium *{animation:none!important}.le-bg-scan{display:none}}
    @media(max-width:700px){.le-bg-aurora{opacity:.7}.le-bg-orb.o1{width:300px;height:300px}.le-bg-orb.o3{width:420px;height:420px}.le-bg-premium:before{background-size:38px 38px}}
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
    const particles=Array.from({length:26},(_,i)=>{
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
