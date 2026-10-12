(async function(){
"use strict";
let D;try{D=await (await fetch("data.json",{cache:"no-cache"})).json()}catch(e){document.getElementById("app").innerHTML='<div class="wrap"><div class="empty" style="margin-top:40px"><b>No se pudieron cargar los precios.</b><br>Recarga la página en unos segundos.</div></div>';return}
const GAMES=D.games;
/* ---------- config ---------- */
const STORES={
  steam:{n:"Steam",c:"#1b2838",t:"#66c0f4",m:"S"},
  eneba:{n:"Eneba",c:"#7b3ff2",t:"#fff",m:"E"},
  instant:{n:"Instant Gaming",c:"#ff5400",t:"#fff",m:"IG"},
  kinguin:{n:"Kinguin",c:"#f2a900",t:"#1d1405",m:"K"},
  loaded:{n:"Loaded",c:"#00c2a0",t:"#03201a",m:"L"},
  gamivo:{n:"Gamivo",c:"#2f6bff",t:"#fff",m:"G"},
  fanatical:{n:"Fanatical",c:"#ff7a00",t:"#fff",m:"F"}
};
const REGIONS=["Global","Europa","Resto del mundo"];
const REGION_OK={"Global":true,"Europa":true,"Resto del mundo":false};
const GENRE_ORDER=["Acción","Aventura","RPG","Mundo abierto","Shooter","Soulslike","Terror","Fútbol","Deportes","Carreras","Estrategia","Simulación","Indie","Cooperativo","Multijugador","Casual","Gratis"];
const GENRE_IMG={"Acción":2807960,"Aventura":1174180,"RPG":1086940,"Mundo abierto":1091500,"Shooter":553850,"Soulslike":1245620,"Terror":3764200,"Fútbol":3405690,"Deportes":2878980,"Carreras":1551360,"Estrategia":3551340,"Simulación":413150,"Indie":367520,"Cooperativo":1426210,"Multijugador":2767030,"Casual":1868140,"Gratis":1665460};
/* Real site: dates come from the affiliate feeds as-is. Demo feeds only: shift dates so the demo stays "live". */
const UPDATED=new Date(D.updated);
const DATA_DAY=new Date(UPDATED.getFullYear(),UPDATED.getMonth(),UPDATED.getDate());
const now=new Date(); const today=new Date(now.getFullYear(),now.getMonth(),now.getDate());
const SHIFT=D.demo?Math.max(0,Math.round((today-DATA_DAY)/864e5)):0;
const DAY=864e5;
function shiftISO(iso){if(!iso)return null;const d=new Date(iso+"T23:59:59");return new Date(d.getTime()+SHIFT*DAY)}
GAMES.forEach(g=>{g.o.forEach(o=>{o.end=shiftISO(o.exp);o.sinceD=o.since?new Date(new Date(o.since+"T00:00:00").getTime()+SHIFT*DAY):null});g.relD=g.rel?new Date(g.rel+"T00:00:00"):null;g.sh=Math.min(g.sh,4)});
const BYID=Object.fromEntries(GAMES.map(g=>[g.id,g]));

/* ---------- helpers ---------- */
const $=(s,r=document)=>r.querySelector(s);
const esc=s=>String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const eur=n=>n.toLocaleString("es-ES",{minimumFractionDigits:2,maximumFractionDigits:2})+" €";
const norm=s=>s.normalize("NFD").replace(/[̀-ͯ]/g,"").replace(/[™®©:’'\-]/g," ").replace(/\s+/g," ").toLowerCase().trim();
const img=(id,k)=>`img/${id}_${k}.webp`;
const fmtD=d=>d.toLocaleDateString("es-ES",{day:"numeric",month:"short"});
const fmtDL=d=>d.toLocaleDateString("es-ES",{day:"numeric",month:"long",year:"numeric"});
const STEAM=id=>`https://store.steampowered.com/app/${id}/`;
function store(k,lg){const s=STORES[k];return `<span class="st${lg?" st-lg":""}"><i style="background:${s.c};color:${s.t}">${s.m}</i>${s.n}</span>`}
function daysLeft(d){return Math.ceil((d-now)/DAY)}
function leftTxt(d){const n=daysLeft(d);return n<=0?"Termina hoy":n===1?"Termina mañana":`Termina en ${n} días`}
const ICON={
  search:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
  heart:'<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 4.5 6.8 4.5c2.1 0 3.6 1.2 5.2 3 1.6-1.8 3.1-3 5.2-3 3.8 0 5.9 3.9 4.4 7.3C19.5 16.4 12 21 12 21z"/></svg>',
  heartO:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 21s-7.5-4.6-9.6-9.2C.9 8.4 3 4.5 6.8 4.5c2.1 0 3.6 1.2 5.2 3 1.6-1.8 3.1-3 5.2-3 3.8 0 5.9 3.9 4.4 7.3C19.5 16.4 12 21 12 21z"/></svg>',
  bell:'<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M6 8a6 6 0 1 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.9 1.9 0 0 0 3.4 0"/></svg>',
  clock:'<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
  ext:'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/></svg>',
  l:'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="m15 18-6-6 6-6"/></svg>',
  r:'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="m9 18 6-6-6-6"/></svg>',
  x:'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M6 6l12 12M18 6 6 18"/></svg>',
  check:'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round"><path d="m5 12 5 5L20 7"/></svg>',
  play:'<svg width="22" height="22" viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>',
  warn:'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round"><path d="M12 9v4M12 17h.01M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/></svg>'
};

/* ---------- price engine ---------- */
/* An offer is alive when it has no end date (regular price) or its end date has not passed. Expired offers never reach the page. */
const alive=o=>!o.end||o.end>=now;
function liveOffers(g){return g.o.filter(alive)}
function isDeal(o){return (o.end&&alive(o))||(o.official&&o.p<o.was)}
/* Card price: cheapest live offer, Standard edition, region that activates in Spain. */
function best(g){
  if(g.free) return {free:true};
  const c=liveOffers(g).filter(o=>o.ed==="Standard"&&REGION_OK[o.rg]).sort((a,b)=>a.p-b.p);
  if(!c.length) return null;
  const b=c[0]; const deals=c.filter(isDeal);
  const off=Math.round((1-b.p/b.was)*100);
  return {o:b,p:b.p,was:b.was,off:off>0?off:0,deal:deals.length>0,count:new Set(c.map(o=>o.s)).size};
}
GAMES.forEach(g=>{g.b=best(g)});
const CONTACT_EMAIL="ofertagg.oficial@gmail.com";
const LIVE_STORES=Object.keys(STORES).filter(k=>GAMES.some(g=>g.o.some(o=>o.s===k)));
const SOON_STORES=Object.keys(STORES).filter(k=>!LIVE_STORES.includes(k));
const soonRow=()=>SOON_STORES.length?`<span class="soon-l">Próximamente</span>${SOON_STORES.map(k=>`<span class="st-soon">${store(k)}</span>`).join("")}`:"";
/* "Nueva oferta": a deal that appeared in the last few days. On popular games it goes straight to the top of the home page. */
const NUEVA=(D.nueva_dias||7)*DAY;
/* Only a real, live discount counts: it must have an end date, be cheaper than the normal price by at least 5%, and be recent. */
const isNew=o=>o.end&&alive(o)&&o.p<=o.was*0.95&&o.sinceD&&(now-o.sinceD)<NUEVA&&o.sinceD.getFullYear()>2001;
GAMES.forEach(g=>{const n=liveOffers(g).filter(o=>isNew(o)&&o.ed==="Standard"&&REGION_OK[o.rg]).sort((a,b)=>a.p-b.p);g.nw=n[0]||null;g.hot=!!(g.pop&&g.nw)});
const POP_HI=250000, POP_MID=60000;
const tierOf=g=>g.rec>=POP_HI?3:(g.rec>=POP_MID||g.pop)?2:1;

/* ---------- state ---------- */
const LS={get(k,d){try{const v=localStorage.getItem("ofertagg_"+k);return v?JSON.parse(v):d}catch(e){return d}},set(k,v){try{localStorage.setItem("ofertagg_"+k,JSON.stringify(v))}catch(e){}}};
const S={user:LS.get("user",null),wish:new Set(LS.get("wish",[])),prefs:LS.get("prefs",{weekly:true,drops:true,launch:false}),alerts:LS.get("alerts",{})};
function saveWish(){LS.set("wish",[...S.wish]);updWish()}
function updWish(){const c=$("#wishCount");c.textContent=S.wish.size;c.hidden=!S.wish.size}
function toast(t){const el=document.createElement("div");el.className="toast";el.setAttribute("role","status");el.textContent=t;document.body.append(el);setTimeout(()=>el.remove(),2600)}

/* ---------- components ---------- */
function priceBlock(g,compact){
  const b=g.b;
  if(!b) return `<span class="base-tag">Sin stock</span>`;
  if(b.free) return `<div class="price"><span class="now">Gratis</span></div>`;
  return `<div class="price">${b.off&&b.deal?`<span class="off">-${b.off}%</span>`:""}<span class="now num">${eur(b.p)}</span>${b.off&&b.deal&&!compact?`<span class="was num">${eur(b.was)}</span>`:""}</div>`;
}
function flags(g){
  const f=[];
  if(g.nw) f.push(`<span class="pill pill-hot">Nueva oferta</span>`);
  if(g.soon) f.push(`<span class="pill pill-soon">Reserva · ${fmtD(g.relD)}</span>`);
  else if(g.relD&&(now-g.relD)/DAY<75) f.push(`<span class="pill pill-new">Nuevo</span>`);
  if(g.free) f.push(`<span class="pill pill-free">Gratis</span>`);
  return f.length?`<div class="flag">${f.join("")}</div>`:"";
}
function card(g){
  const b=g.b; const on=S.wish.has(g.id);
  let lbl="";
  if(b&&!b.free) lbl=b.deal?`<div class="lbl">Mejor precio</div>${store(b.o.s)}`:`<div class="lbl">Precio base</div>${store(b.o.s)}`;
  if(b&&b.free) lbl=`<div class="lbl">Disponible en</div>${store("steam")}`;
  return `<a class="card" href="#juego-${g.id}" aria-label="${esc(g.n)}">
    <div class="card-img"><img loading="lazy" src="${img(g.id,"h")}" alt="">${flags(g)}
      <button class="heart${on?" on":""}" data-wish="${g.id}" aria-label="${on?"Quitar de":"Añadir a"} la lista de deseos">${on?ICON.heart:ICON.heartO}</button></div>
    <div class="card-b"><div class="card-t">${esc(g.n)}</div>
      <div class="card-p"><div>${lbl}</div>${priceBlock(g,true)}</div></div></a>`;
}
function tierMark(t){return `<b>${[1,2,3].map(i=>`<i class="${i<=t?"":"off"}"></i>`).join("")}</b>`}
function shelf({title,sub,items,more,tier,row,big}){
  if(!items.length) return "";
  return `<section class="shelf"><div class="shelf-h"><div>${tier?`<div class="tier">${tierMark(tier)}${["","Menos conocidos","Popularidad media","Los más populares"][tier]}</div>`:""}<h2>${title}</h2>${sub?`<p>${sub}</p>`:""}</div>${more?`<a class="more" href="${more}">Ver todos →</a>`:""}</div>
  <div class="${row?"row":"grid"+(big?" big":"")}">${items.map(card).join("")}</div></section>`;
}
function genreCount(gn){return GAMES.filter(g=>g.g.includes(gn)).length}
function gtile(gn){return `<a class="gtile" href="#juegos-${slug(gn)}"><img loading="lazy" src="${img(GENRE_IMG[gn],"h")}" alt=""><span>${gn}</span><small>${genreCount(gn)}</small></a>`}
const slug=s=>norm(s).replace(/ /g,"-");
const GENRE_BY_SLUG=Object.fromEntries(GENRE_ORDER.map(g=>[slug(g),g]));

/* ---------- weekly update info ---------- */
function lastMonday(d0){const d=new Date(d0);const k=(d.getDay()+6)%7;d.setDate(d.getDate()-k);return d}
const UPD=D.demo?today:DATA_DAY; const NEXT=new Date(lastMonday(UPD).getTime()+7*DAY);

/* ---------- views ---------- */
const app=$("#app");
function viewHome(){
  const pop=[...GAMES].filter(g=>!g.soon);
  const hotG=GAMES.filter(g=>g.hot).sort((a,b)=>b.rec-a.rec);
  const feat=[...hotG,...GAMES.filter(g=>g.hero&&!g.hot)].slice(0,8);
  const deals=GAMES.filter(g=>!g.soon&&g.b&&!g.b.free).map(g=>{
      const ds=liveOffers(g).filter(o=>o.end&&o.ed==="Standard"&&REGION_OK[o.rg]).sort((a,b)=>a.p-b.p);
      return ds.length?{g,o:ds[0],off:Math.round((1-ds[0].p/ds[0].was)*100)}:null}).filter(Boolean)
    .sort((a,b)=>b.off-a.off).slice(0,8);
  const newRel=GAMES.filter(g=>!g.soon&&g.relD&&(now-g.relD)/DAY<420).sort((a,b)=>b.relD-a.relD);
  const soon=GAMES.filter(g=>g.soon).sort((a,b)=>a.relD-b.relD);
  const t3=pop.filter(g=>tierOf(g)===3&&!g.free), t2=pop.filter(g=>tierOf(g)===2&&!g.free), t1=pop.filter(g=>tierOf(g)===1&&!g.free);
  const under10=pop.filter(g=>g.b&&!g.b.free&&g.b.p<10).sort((a,b)=>b.rec-a.rec);
  const foot=GAMES.filter(g=>g.g.includes("Fútbol")||g.g.includes("Deportes")).sort((a,b)=>b.rec-a.rec);
  const free=GAMES.filter(g=>g.free);
  app.innerHTML=`<div class="wrap">
  <section class="hero" aria-label="Destacados">${feat.map((g,i)=>`<div class="hero-slide${i?"":" on"}" data-i="${i}">
      <img src="${img(g.id,g.hero?"hero":"s0")}" alt="" ${i?'loading="lazy"':""}>
      <div class="hero-copy"><span class="eyebrow">${g.hot?`<span style="color:var(--gold)">Nueva oferta · ${leftTxt(g.nw.end).toLowerCase()}</span>`:g.soon?"Próximamente":g.relD&&(now-g.relD)/DAY<300?"Lanzamiento reciente":"Destacado de la semana"} · ${esc(g.g.slice(0,2).join(" · "))}</span>
        <h1>${esc(g.n)}</h1><p>${esc(g.sd)}</p>
        <div class="hero-price">${g.b&&!g.b.free?`<span class="big num">${eur(g.b.p)}</span>${g.b.off?`<span class="off">-${g.b.off}%</span>`:""}<span style="color:var(--muted);font-size:13px">en</span>${store(g.b.o.s,1)}`:""}</div>
        <div style="display:flex;gap:10px;flex-wrap:wrap"><a class="btn btn-gold" href="#juego-${g.id}">${g.b&&g.b.count>1?`Comparar ${g.b.count} tiendas`:"Ver el juego"}</a><button class="btn btn-line" data-wish="${g.id}">${S.wish.has(g.id)?"En tu lista":"Añadir a mi lista"}</button></div></div></div>`).join("")}
    <div class="hero-dots">${feat.map((g,i)=>`<button class="${i?"":"on"}" data-dot="${i}" aria-label="${esc(g.n)}"><img src="${img(g.id,"h")}" alt=""></button>`).join("")}</div>
  </section>
  <div class="strip"><span class="eyebrow">Comparamos precios en</span>${LIVE_STORES.map(k=>store(k,1)).join("")}${soonRow()}
    <span style="margin-left:auto;font-size:12.5px;color:var(--muted)">Ofertas comprobadas el ${fmtDL(UPD)} · Revisión completa cada lunes (próxima: ${fmtD(NEXT)})</span></div>

  ${hotG.length?`<section class="shelf"><div class="shelf-h"><div><div class="tier"><span class="live"></span>Recién rebajados</div><h2>Nuevas ofertas en juegos populares</h2><p>Bajadas de precio que acaban de aparecer. Las publicamos en cuanto las detectamos.</p></div><a class="more" href="#ofertas">Todas las ofertas →</a></div>
    <div class="hotgrid">${hotG.map(g=>{const o=g.nw,off=Math.round((1-o.p/o.was)*100);return `<a class="hotc" href="#juego-${g.id}"><img loading="lazy" src="${img(g.id,"h")}" alt=""><div class="hotc-b"><span class="pill pill-hot">Nueva · -${off}%</span><b>${esc(g.n)}</b>
      <div class="hotc-p"><span class="now num">${eur(o.p)}</span><span class="was num">${eur(o.was)}</span>${store(o.s)}</div><span class="clock">${ICON.clock}${leftTxt(o.end)}</span></div></a>`}).join("")}</div></section>`:""}
  ${shelf({title:"Los más populares",sub:hotG.length?"Lo que más se juega ahora mismo, con el precio más bajo entre nuestras tiendas.":"Ahora mismo no hay ofertas nuevas en estos juegos. Te mostramos el precio más bajo que tiene cada uno entre nuestras tiendas.",items:t3.slice(0,10),more:"#juegos",tier:3})}

  ${deals.length?`<section class="shelf"><div class="shelf-h"><div><h2>Ofertas que terminan pronto</h2><p>Descuentos con fecha de fin. Cuando una oferta caduca, desaparece sola de la web.</p></div><a class="more" href="#ofertas">Ver todas →</a></div>
    <div class="deals">${deals.map(({g,o,off})=>`<a class="deal" href="#juego-${g.id}"><img loading="lazy" src="${img(g.id,"h")}" alt=""><div style="min-width:0"><div class="deal-n">${esc(g.n)}</div>
      <div class="deal-m">${store(o.s)}<span>${o.rg}</span><span class="clock">${ICON.clock}${leftTxt(o.end)}</span></div></div>
      <div class="price"><span class="off">-${off}%</span><span class="now num">${eur(o.p)}</span><span class="was num">${eur(o.was)}</span></div></a>`).join("")}</div></section>`:""}

  ${shelf({title:"Nuevos lanzamientos",sub:"Los juegos que han salido en los últimos meses.",items:newRel.slice(0,10),more:"#novedades",row:1})}
  ${shelf({title:"Próximamente · reservas",sub:"Reserva al mejor precio antes del lanzamiento.",items:soon,more:"#proximamente"})}

  <section class="shelf"><div class="shelf-h"><div><h2>Explora por género</h2></div><a class="more" href="#juegos">Todo el catálogo →</a></div>
    <div class="genres">${GENRE_ORDER.map(gtile).join("")}</div></section>

  ${shelf({title:"Fútbol y deportes",items:foot,more:"#juegos-futbol",row:1})}
  ${shelf({title:"Muy recomendados",sub:"Juegos con muchísimas reseñas positivas que quizá aún no tienes.",items:t2,more:"#juegos",tier:2})}
  ${shelf({title:"Por menos de 10 €",items:under10,more:"#juegos",row:1})}
  ${shelf({title:"Joyas por descubrir",sub:"Menos conocidos, igual de buenos.",items:t1,tier:1})}
  ${shelf({title:"Gratis para jugar",items:free})}

  <section class="shelf"><div class="shelf-h"><div><h2>Cómo funciona</h2></div></div>
    <div class="how"><div><span class="n">1</span><h3>Busca tu juego</h3><p>Escribe el nombre arriba o explora por género, novedades y ofertas.</p></div>
    <div><span class="n">2</span><h3>Compara tiendas</h3><p>Ves el precio de cada tienda separado por edición y región, para que sepas exactamente qué compras.</p></div>
    <div><span class="n">3</span><h3>Compra en la tienda</h3><p>Eliges la oferta y te llevamos a la tienda. El pago y la clave los gestiona la tienda.</p></div></div>
    <p class="disclose">OfertaGG no vende juegos. Algunos enlaces son de afiliado: si compras a través de ellos, la tienda puede pagarnos una comisión sin coste extra para ti.</p></section>

  <section class="shelf"><div class="alerts"><div><h2>Que las ofertas te encuentren a ti</h2><p>${D.demo?"Entra con tu cuenta de Google y te avisamos":"Muy pronto podrás entrar con tu cuenta de Google y te avisaremos"} por correo cada semana con las nuevas ofertas, o cuando un juego de tu lista baje de precio.</p>
    <div style="margin-top:18px">${S.user?`<button class="btn btn-gold" data-act="account">Gestionar mis avisos</button>`:`<button class="btn btn-gold" data-act="login"><span class="g-ico">G</span>Entrar con Google</button>`}</div></div>
    <ul><li>${ICON.check}Resumen semanal de ofertas nuevas</li><li>${ICON.check}Aviso cuando un juego de tu lista baja de precio</li><li>${ICON.check}Avisos de lanzamientos y reservas</li><li>${ICON.check}Puedes darte de baja cuando quieras</li></ul></div></section>

  <section class="shelf faq"><div class="shelf-h"><h2>Preguntas frecuentes</h2></div>
    <details><summary>¿Vendéis juegos?</summary><p>No. Somos un comparador: buscamos el precio en varias tiendas y te enviamos a la que elijas. La compra, el pago y la entrega de la clave se hacen en esa tienda.</p></details>
    <details><summary>¿Qué significa Global, Europa o Resto del mundo?</summary><p>Es la región en la que se puede activar la clave. Las claves Global y Europa se activan en España. Las de "Resto del mundo" no se activan en Europa, por eso las mostramos aparte y con aviso.</p></details>
    <details><summary>¿Cada cuánto se actualizan los precios?</summary><p>Cada día comprobamos las ofertas de los juegos más populares, para publicar las rebajas nuevas en cuanto salen. Cada lunes revisamos el catálogo entero: añadimos ofertas nuevas, cambiamos los precios que hayan variado y quitamos las que ya no existen. Las ofertas con fecha de fin desaparecen solas en cuanto caducan.</p></details>
    <details><summary>¿Por qué un juego sale sin descuento?</summary><p>Los juegos nunca se quitan de la web. Si ahora no hay ninguna oferta, ves el precio normal de cada tienda para que elijas la que más te convenga.</p></details>
    <details><summary>¿Qué es la edición Standard o Deluxe?</summary><p>Muchos juegos tienen varias ediciones con contenido extra. Cada edición tiene su propia lista de precios para que no compares cosas distintas.</p></details>
    <details><summary>¿Qué pasa si no hay ninguna oferta?</summary><p>Te mostramos el precio normal más bajo entre las tiendas, marcado como "Precio base".</p></details></section>
  </div>`;
  startHero(feat.length);
}
let heroT=null;
function startHero(n){
  clearInterval(heroT); let i=0;
  const go=k=>{i=(k+n)%n;document.querySelectorAll(".hero-slide").forEach(s=>s.classList.toggle("on",+s.dataset.i===i));document.querySelectorAll("[data-dot]").forEach(s=>s.classList.toggle("on",+s.dataset.dot===i))};
  app.querySelectorAll("[data-dot]").forEach(b=>b.onclick=()=>{go(+b.dataset.dot);clearInterval(heroT)});
  if(!matchMedia("(prefers-reduced-motion: reduce)").matches) heroT=setInterval(()=>go(i+1),6500);
}

/* catalog */
const F={q:"",genres:new Set(),stores:new Set(),max:80,region:"es",deals:false,feats:new Set(),sort:"pop",mode:"all"};
function viewCatalog(mode,genreSlug,q){
  F.mode=mode; F.genres=new Set(); F.q=q||"";
  if(genreSlug&&GENRE_BY_SLUG[genreSlug]) F.genres.add(GENRE_BY_SLUG[genreSlug]);
  F.deals=mode==="ofertas"; F.sort=mode==="novedades"?"new":mode==="proximamente"?"soon":mode==="ofertas"?"off":"pop";
  const title={all:F.genres.size?[...F.genres][0]:"Todos los juegos",ofertas:"Ofertas de la semana",novedades:"Nuevos lanzamientos",proximamente:"Próximamente",gratis:"Juegos gratis",search:`Resultados para "${F.q}"`}[mode];
  const feats=["Un jugador","Multijugador en línea","Cooperativo en línea","JcJ en línea"];
  app.innerHTML=`<div class="wrap"><nav class="crumbs"><a href="#">Inicio</a><span>/</span><span>${esc(title)}</span></nav>
  <div class="cat"><aside class="filters" aria-label="Filtros">
    <details class="fgrp" open><summary>Género</summary><div class="fopts">${GENRE_ORDER.map(gn=>`<label class="chk"><input type="checkbox" id="fg-${slug(gn)}" data-f="genres" value="${gn}" ${F.genres.has(gn)?"checked":""}>${gn}<small>${genreCount(gn)}</small></label>`).join("")}</div></details>
    <details class="fgrp" open><summary>Precio máximo</summary><div class="fopts"><input class="range" type="range" id="fmax" min="5" max="80" step="5" value="${F.max}"><div class="lbl-row"><span>5 €</span><b class="num" id="fmaxv">${F.max>=80?"Sin límite":"Hasta "+F.max+" €"}</b></div></div></details>
    <details class="fgrp" open><summary>Tienda</summary><div class="fopts">${Object.keys(STORES).map(k=>`<label class="chk"><input type="checkbox" id="fs-${k}" data-f="stores" value="${k}">${store(k)}</label>`).join("")}</div></details>
    <details class="fgrp"><summary>Región de activación</summary><div class="fopts">
      <label class="chk"><input type="radio" name="freg" id="fr-es" value="es" checked>Se activa en España</label>
      <label class="chk"><input type="radio" name="freg" id="fr-all" value="all">Todas las regiones</label></div></details>
    <details class="fgrp"><summary>Características</summary><div class="fopts">${feats.map(f=>`<label class="chk"><input type="checkbox" id="ff-${slug(f)}" data-f="feats" value="${f}">${f}</label>`).join("")}</div></details>
    <label class="chk" style="margin-top:8px"><input type="checkbox" id="fdeals" ${F.deals?"checked":""}>Solo juegos con oferta activa</label>
  </aside>
  <div style="min-width:0"><div class="cat-head"><h1>${esc(title)}</h1><span id="ccount" class="num" style="color:var(--muted);font-size:13px"></span>
    <select class="sel" id="fsort" aria-label="Ordenar"><option value="pop">Más populares</option><option value="off">Mayor descuento</option><option value="asc">Precio: menor a mayor</option><option value="desc">Precio: mayor a menor</option><option value="new">Más recientes</option><option value="soon">Próximos lanzamientos</option><option value="mc">Mejor valorados</option></select></div>
    <div class="chips" id="activeChips" style="margin-bottom:14px"></div>
    <div class="grid" id="cgrid"></div></div></div></div>`;
  $("#fsort").value=F.sort;
  app.querySelectorAll("[data-f]").forEach(i=>i.onchange=()=>{F[i.dataset.f][i.checked?"add":"delete"](i.value);renderCat()});
  $("#fmax").oninput=e=>{F.max=+e.target.value;$("#fmaxv").textContent=F.max>=80?"Sin límite":"Hasta "+F.max+" €";renderCat()};
  app.querySelectorAll("[name=freg]").forEach(r=>r.onchange=()=>{F.region=r.value;renderCat()});
  $("#fdeals").onchange=e=>{F.deals=e.target.checked;renderCat()};
  $("#fsort").onchange=e=>{F.sort=e.target.value;renderCat()};
  renderCat();
}
function catPrice(g){
  if(g.free) return {p:0,off:0,deal:false};
  let c=liveOffers(g).filter(o=>o.ed==="Standard"&&(F.region==="all"||REGION_OK[o.rg]));
  if(F.stores.size) c=c.filter(o=>F.stores.has(o.s));
  if(!c.length) return null;
  c.sort((a,b)=>a.p-b.p);
  return {p:c[0].p,off:Math.round((1-c[0].p/c[0].was)*100),deal:c.some(isDeal)};
}
function renderCat(){
  const qn=norm(F.q);
  let list=GAMES.filter(g=>{
    if(F.mode==="novedades"&&(g.soon||!g.relD||(now-g.relD)/DAY>420)) return false;
    if(F.mode==="proximamente"&&!g.soon) return false;
    if(F.mode==="gratis"&&!g.free) return false;
    if(qn&&!norm(g.n+" "+g.dev.join(" ")+" "+g.pub.join(" ")+" "+g.g.join(" ")).includes(qn)) return false;
    for(const gn of F.genres) if(!g.g.includes(gn)) return false;
    for(const f of F.feats) if(!g.feats.includes(f)) return false;
    const cp=catPrice(g); if(!cp) return false; g._cp=cp;
    if(F.max<80&&cp.p>F.max) return false;
    if(F.deals&&!cp.deal) return false;
    return true;});
  const s={pop:(a,b)=>b.rec-a.rec,off:(a,b)=>b._cp.off-a._cp.off,asc:(a,b)=>a._cp.p-b._cp.p,desc:(a,b)=>b._cp.p-a._cp.p,new:(a,b)=>(b.relD||0)-(a.relD||0),soon:(a,b)=>(a.soon===b.soon?(a.relD-b.relD):a.soon?-1:1),mc:(a,b)=>(b.mc||0)-(a.mc||0)}[F.sort];
  list.sort(s);
  $("#ccount").textContent=list.length+" juegos";
  const chips=[...F.genres].map(gn=>`<button class="chip on" data-rm="genres|${gn}">${gn} ✕</button>`).concat([...F.stores].map(k=>`<button class="chip on" data-rm="stores|${k}">${STORES[k].n} ✕</button>`));
  $("#activeChips").innerHTML=chips.join("");
  $("#activeChips").querySelectorAll("[data-rm]").forEach(b=>b.onclick=()=>{const[k,v]=b.dataset.rm.split("|");F[k].delete(v);const i=app.querySelector(`[data-f="${k}"][value="${CSS.escape(v)}"]`);if(i)i.checked=false;renderCat()});
  $("#cgrid").innerHTML=list.length?list.map(card).join(""):`<div class="empty" style="grid-column:1/-1"><b>No hay juegos con estos filtros.</b><br>Prueba a quitar algún filtro o a subir el precio máximo.</div>`;
}

/* game page */
let G=null, sel={ed:"Standard",rg:"Global",pick:null,shot:0};
function viewGame(id){
  const g=BYID[id]; if(!g){viewHome();return}
  G=g; sel={ed:"Standard",rg:"Global",pick:null,shot:0};
  const shots=[...Array(g.sh).keys()];
  const sameCo=GAMES.filter(x=>x.id!==g.id&&(x.pub.some(p=>g.pub.includes(p))||x.dev.some(d=>g.dev.includes(d))));
  const similar=GAMES.filter(x=>x.id!==g.id&&!sameCo.includes(x)).map(x=>({x,s:x.g.filter(t=>g.g.includes(t)).length+x.rec/1e7})).sort((a,b)=>b.s-a.s).slice(0,5).map(o=>o.x);
  const mcCls=g.mc>=85?"":"mid";
  app.innerHTML=`<div class="gp"><div class="gp-bg"><img src="${img(g.id,"h")}" alt=""></div><div class="wrap">
    <nav class="crumbs"><a href="#">Inicio</a><span>/</span><a href="#juegos-${slug(g.g[0]||"accion")}">${esc(g.g[0]||"Juegos")}</a><span>/</span><span>${esc(g.n)}</span></nav>
    <div class="gp-top"><div style="min-width:0">
      <div class="tier">${tierMark(tierOf(g))}${g.soon?"Próximo lanzamiento":["","Joya por descubrir","Muy recomendado","Muy popular"][tierOf(g)]}</div>
      <h1 class="gp-title">${esc(g.n)}</h1>
      <div class="gp-sub"><span>${esc(g.dev.join(", "))}</span>${g.relD?`<span>· ${g.soon?"Sale el":"Lanzado el"} <b>${fmtDL(g.relD)}</b></span>`:""}${g.mc?`<span>· <span class="score ${mcCls}">${g.mc}</span> Metacritic</span>`:""}${g.rec?`<span>· <b class="num">${g.rec.toLocaleString("es-ES")}</b> reseñas en Steam</span>`:""}</div>
      <div class="tags" style="margin:14px 0 16px">${g.g.map(t=>`<a class="tag" href="#juegos-${slug(t)}">${esc(t)}</a>`).join("")}</div>
      <div class="gal-main" id="galMain"><img id="galImg" src="${img(g.id,"s0")}" alt="Captura de ${esc(g.n)}">
        <button class="gal-nav l" data-gal="-1" aria-label="Anterior">${ICON.l}</button><button class="gal-nav r" data-gal="1" aria-label="Siguiente">${ICON.r}</button><span class="gal-count" id="galCount">1 / ${g.sh}</span></div>
      <div class="thumbs">${shots.map(i=>`<button data-shot="${i}" class="${i?"":"on"}" aria-label="Captura ${i+1}"><img loading="lazy" src="${img(g.id,"s"+i)}" alt=""></button>`).join("")}
        ${g.vid?`<a class="vid" href="${STEAM(g.id)}" target="_blank" rel="noopener">${ICON.play}<span>Ver ${g.vid} vídeo${g.vid>1?"s":""}</span></a>`:""}</div>
      <p style="color:#d6d0e2;margin:18px 0 0;max-width:70ch">${esc(g.sd)}</p>
    </div>
    <aside class="buy" id="buy" aria-label="Comparar precios"></aside></div>

    <section class="gp-sec"><div class="tabs" role="tablist">
      <button class="on" data-tab="about">Acerca del juego</button><button data-tab="req">Requisitos</button><button data-tab="lang">Idiomas</button></div>
      <div id="tabBody"></div></section>
    ${sameCo.length?`<section class="shelf"><div class="shelf-h"><div><h2>Más de ${esc(g.pub[0]||g.dev[0])}</h2><p>Otros juegos de la misma compañía.</p></div></div><div class="row">${sameCo.sort((a,b)=>b.rec-a.rec).map(card).join("")}</div></section>`:""}
    ${shelf({title:"Juegos parecidos",items:similar,row:1})}
  </div></div>`;
  renderBuy(); renderTab("about");
  app.querySelectorAll("[data-tab]").forEach(b=>b.onclick=()=>{app.querySelectorAll("[data-tab]").forEach(x=>x.classList.toggle("on",x===b));renderTab(b.dataset.tab)});
  app.querySelectorAll("[data-shot]").forEach(b=>b.onclick=()=>setShot(+b.dataset.shot));
  app.querySelectorAll("[data-gal]").forEach(b=>b.onclick=e=>{e.stopPropagation();setShot(sel.shot+ +b.dataset.gal)});
  $("#galMain").onclick=()=>openLB(sel.shot);
}
function setShot(i){const n=G.sh;sel.shot=(i+n)%n;$("#galImg").src=img(G.id,"s"+sel.shot);$("#galCount").textContent=`${sel.shot+1} / ${n}`;app.querySelectorAll("[data-shot]").forEach(b=>b.classList.toggle("on",+b.dataset.shot===sel.shot))}
function renderTab(t){
  const g=G,b=$("#tabBody");
  if(t==="about") b.innerHTML=`<div class="about"><div class="prose">${esc(g.ab)}</div>
    <dl class="facts"><dt>Desarrollador</dt><dd>${g.dev.map(d=>`<a href="#buscar-${encodeURIComponent(d)}">${esc(d)}</a>`).join(", ")}</dd>
    <dt>Editor</dt><dd>${g.pub.map(d=>`<a href="#buscar-${encodeURIComponent(d)}">${esc(d)}</a>`).join(", ")}</dd>
    <dt>Lanzamiento</dt><dd>${g.relD?fmtDL(g.relD):"Por anunciar"}</dd>
    <dt>Plataforma</dt><dd>PC · Clave de Steam</dd>
    ${g.age?`<dt>Edad</dt><dd>+${g.age}</dd>`:""}
    ${g.mc?`<dt>Metacritic</dt><dd><span class="score ${g.mc>=85?"":"mid"}">${g.mc}</span></dd>`:""}
    ${g.rec?`<dt>Reseñas Steam</dt><dd class="num">${g.rec.toLocaleString("es-ES")}</dd>`:""}
    ${g.ach?`<dt>Logros</dt><dd class="num">${g.ach}</dd>`:""}
    ${g.dlc?`<dt>DLC y extras</dt><dd class="num">${g.dlc}</dd>`:""}
    ${g.feats.length?`<dt>Modos</dt><dd>${g.feats.slice(0,5).map(esc).join(" · ")}</dd>`:""}</dl></div>`;
  if(t==="req") b.innerHTML=`<div class="reqs"><div><span class="eyebrow">Mínimos</span><pre>${esc(g.req.replace(/^Mínimo:\s*/i,"")||"Sin datos")}</pre></div><div><span class="eyebrow">Recomendados</span><pre>${esc(g.reqr.replace(/^Recomendado:\s*/i,"")||"Sin datos")}</pre></div></div>`;
  if(t==="lang") b.innerHTML=`<div class="tags">${g.langs.map(l=>`<span class="tag" style="font-size:13.5px;padding:6px 12px">${esc(l)}</span>`).join("")}</div>`;
}
function renderBuy(){
  const g=G, el=$("#buy");
  if(g.free){el.innerHTML=`<span class="eyebrow">Precio</span><div class="buy-best"><span class="now">Gratis</span>${store("steam",1)}</div>
    <p class="buy-foot" style="margin:0">Este juego es gratuito. Se descarga directamente desde Steam.</p>
    <a class="btn btn-gold go" href="${STEAM(g.id)}" target="_blank" rel="noopener">Ir a Steam ${ICON.ext}</a>${wishBtns(g)}`;bindBuy();return}
  const live=liveOffers(g);
  const eds=[...new Set(g.o.map(o=>o.ed))];
  const forEd=live.filter(o=>o.ed===sel.ed);
  const regs=REGIONS.filter(r=>forEd.some(o=>o.rg===r));
  if(!regs.includes(sel.rg)) sel.rg=regs[0];
  const list=forEd.filter(o=>o.rg===sel.rg).sort((a,b)=>a.p-b.p);
  const b=g.b;
  const minOf=f=>{const c=live.filter(f).map(o=>o.p);return c.length?Math.min(...c):null};
  el.innerHTML=`${g.nw?`<div class="reg-note hotnote">${ICON.clock}<span><b>Nueva oferta</b> en ${STORES[g.nw.s].n}: ${eur(g.nw.p)} · ${leftTxt(g.nw.end).toLowerCase()}</span></div>`:""}<div><span class="eyebrow">${b&&b.deal?"Mejor oferta ahora":"Precio base · sin ofertas activas"}</span>
    <div class="buy-best" style="margin-top:6px">${b?`<span class="now num">${eur(b.p)}</span>${b.off&&b.deal?`<span class="off">-${b.off}%</span>`:""}${store(b.o.s,1)}`:"Sin precio"}</div>
    ${b?`<div style="font-size:12px;color:var(--dim);margin-top:6px">Edición Standard · ${b.o.rg} · ${b.count>1?`comparando ${b.count} tiendas`:"precio oficial"}</div>`:""}</div>
    ${eds.length>1?`<div><div class="lbl-row" style="margin-bottom:6px"><span>Edición</span></div><div class="seg">${eds.map(e=>{const m=minOf(o=>o.ed===e&&REGION_OK[o.rg]);return `<button data-ed="${e}" class="${e===sel.ed?"on":""}">${e}<small>${m!=null?"desde "+eur(m):"—"}</small></button>`}).join("")}</div></div>`:""}
    <div><div class="lbl-row" style="margin-bottom:6px"><span>Región de la clave</span></div><div class="seg">${regs.map(r=>{const m=minOf(o=>o.ed===sel.ed&&o.rg===r);return `<button data-rg="${r}" class="${r===sel.rg?"on":""}">${r==="Resto del mundo"?"Otras":r}<small>${eur(m)}</small></button>`}).join("")}</div></div>
    ${REGION_OK[sel.rg]?`<div class="reg-note ok">${ICON.check}<span>Las claves ${sel.rg} se activan en España.</span></div>`:`<div class="reg-note bad">${ICON.warn}<span>Las claves de "Resto del mundo" <b>no se activan en España</b> ni en Europa. Cómpralas solo si vives fuera de Europa.</span></div>`}
    <div class="offers" role="radiogroup" aria-label="Elige tienda">${list.map((o,i)=>{const k=g.o.indexOf(o);const off=Math.round((1-o.p/o.was)*100);
      return `<label class="offer${sel.pick===k?" on":""}"><input type="radio" name="pick" value="${k}" ${sel.pick===k?"checked":""}><span class="radio"></span>
      <span class="offer-m">${store(o.s)}<span class="offer-sub"><span>${o.official?"Tienda oficial":"Clave Steam"} · ${o.rg}</span>${o.end?`<span class="clock">${ICON.clock}${leftTxt(o.end)} · ${fmtD(o.end)}</span>`:o.official&&off>0?`<span class="clock">Oferta de Steam</span>`:`<span>Precio normal</span>`}</span></span>
      <span class="price">${i===0?`<span class="best-badge">Más barato</span>`:isNew(o)?`<span class="best-badge" style="color:var(--gold)">Nueva</span>`:""}<span class="now num">${eur(o.p)}</span>${off>0?`<span class="was num">${eur(o.was)}</span>`:""}</span></label>`}).join("")||`<div class="empty">No hay ofertas para esta edición y región.</div>`}</div>
    ${SOON_STORES.length?`<div class="soon-box"><span>Muy pronto también compararemos:</span><div>${SOON_STORES.map(k=>`<span class="st-soon">${store(k)}</span>`).join("")}</div></div>`:""}
    ${(()=>{const o=sel.pick!=null?g.o[sel.pick]:null;return o?`<a class="btn btn-gold go" href="${o.url||STEAM(g.id)}" target="_blank" rel="noopener sponsored">Ir a comprar en ${STORES[o.s].n} · ${eur(o.p)} ${ICON.ext}</a>`:`<button class="btn btn-gold go" disabled>Elige una tienda para continuar</button>`})()}
    <p class="buy-foot" style="margin:0">Te llevamos a la tienda que elijas; la compra se hace allí. ${D.demo?'<b style="color:var(--gold)">Demo:</b> por ahora todos los enlaces abren la página del juego en Steam.':""}</p>
    ${wishBtns(g)}`;
  bindBuy();
}
function wishBtns(g){const on=S.wish.has(g.id);const al=S.alerts[g.id];return `<div class="buy-actions"><button class="btn btn-line${on?" on":""}" data-wish="${g.id}">${on?ICON.heart+"En tu lista":ICON.heartO+"Lista de deseos"}</button><button class="btn btn-line${al?" on":""}" data-act="alert">${ICON.bell}${al?"Aviso: "+al+" €":"Avisar si baja"}</button></div>`}
function bindBuy(){
  const el=$("#buy");
  el.querySelectorAll("[data-ed]").forEach(b=>b.onclick=()=>{sel.ed=b.dataset.ed;sel.pick=null;renderBuy()});
  el.querySelectorAll("[data-rg]").forEach(b=>b.onclick=()=>{sel.rg=b.dataset.rg;sel.pick=null;renderBuy()});
  el.querySelectorAll("[name=pick]").forEach(r=>r.onchange=()=>{sel.pick=+r.value;renderBuy();const go=$("#buy .go");go&&go.focus({preventScroll:true})});
}

/* lightbox */
function openLB(i){
  const n=G.sh;let k=i;const lb=document.createElement("div");lb.className="lb";lb.setAttribute("role","dialog");lb.setAttribute("aria-label","Capturas");
  const draw=()=>{lb.innerHTML=`<img src="${img(G.id,"s"+k)}" alt=""><button class="icon-btn x" aria-label="Cerrar">${ICON.x}</button><button class="gal-nav l" aria-label="Anterior">${ICON.l}</button><button class="gal-nav r" aria-label="Siguiente">${ICON.r}</button><div class="lb-c">${k+1} de ${n} · ${esc(G.n)}</div>`;
    lb.querySelector(".x").onclick=close;lb.querySelector(".l").onclick=e=>{e.stopPropagation();k=(k-1+n)%n;draw()};lb.querySelector(".r").onclick=e=>{e.stopPropagation();k=(k+1)%n;draw()}};
  const key=e=>{if(e.key==="Escape")close();if(e.key==="ArrowLeft"){k=(k-1+n)%n;draw()}if(e.key==="ArrowRight"){k=(k+1)%n;draw()}};
  function close(){lb.remove();document.removeEventListener("keydown",key)}
  lb.onclick=e=>{if(e.target===lb)close()};document.addEventListener("keydown",key);draw();document.body.append(lb);
}

/* modals: login / account / alert */
function modal(html,onBind){
  const bg=document.createElement("div");bg.className="modal-bg";bg.innerHTML=`<div class="modal" role="dialog" aria-modal="true">${html}<button class="icon-btn x" aria-label="Cerrar">${ICON.x}</button></div>`;
  const close=()=>{bg.remove();document.removeEventListener("keydown",k)};const k=e=>{if(e.key==="Escape")close()};
  bg.onclick=e=>{if(e.target===bg)close()};bg.querySelector(".x").onclick=close;document.addEventListener("keydown",k);document.body.append(bg);onBind&&onBind(bg,close);
}
function login(after){
  if(!D.demo){soonLogin();return}
  modal(`<div class="logo"><img class="logo-img" src="img/logo_dark.png" alt=""><span class="logo-word">Oferta<em>GG</em></span></div>
    <h2>Entra para recibir avisos</h2><p>Guarda tu lista de deseos y recibe por correo las nuevas ofertas cada semana.</p>
    <button class="gbtn" id="gLogin"><span class="g-ico">G</span>Continuar con Google</button>
    <p style="font-size:12px;color:var(--dim)">Demo: el botón simula el inicio de sesión. En la web real se conecta con Google y solo usamos tu nombre y tu correo.</p>`,
  (m,close)=>{m.querySelector("#gLogin").onclick=()=>{S.user={name:"Jugador",email:"tucorreo@gmail.com"};LS.set("user",S.user);close();renderUser();toast("Sesión iniciada con Google");after&&after();if(location.hash===""||location.hash==="#")viewHome()}});
}
function soonLogin(){
  modal(`<div class="logo"><img class="logo-img" src="img/logo_dark.png" alt=""><span class="logo-word">Oferta<em>GG</em></span></div>
    <h2>Avisos por correo: muy pronto</h2><p>Estamos preparando el acceso con tu cuenta de Google para enviarte las nuevas ofertas y avisarte cuando bajen de precio los juegos de tu lista.</p>
    <p>Mientras tanto, tu lista de deseos se guarda en este navegador. Pulsa el corazón de cualquier juego para guardarlo.</p>
    <a class="btn btn-line" href="#deseos" data-close>Ver mi lista de deseos (${S.wish.size})</a>`,(m,close)=>{m.querySelector("[data-close]").onclick=close});
}
function account(){
  modal(`<div style="display:flex;gap:12px;align-items:center"><span class="avatar">${S.user.name[0]}</span><div><b>${esc(S.user.name)}</b><div style="color:var(--muted);font-size:13px">${esc(S.user.email)}</div></div></div>
    <h2 style="font-size:18px">Avisos por correo</h2>
    ${[["weekly","Resumen semanal de ofertas","Cada lunes, con las ofertas nuevas"],["drops","Bajadas de precio","De los juegos de tu lista de deseos"],["launch","Lanzamientos y reservas","Cuando salga un juego de tus géneros"]].map(([k,t,s])=>`<label class="toggle"><span>${t}<small>${s}</small></span><span class="sw"><input type="checkbox" id="p-${k}" data-p="${k}" ${S.prefs[k]?"checked":""}><i></i></span></label>`).join("")}
    <a class="btn btn-line" href="#deseos" data-close>Ver mi lista de deseos (${S.wish.size})</a>
    <button class="btn btn-line" id="logout">Cerrar sesión</button>`,
  (m,close)=>{m.querySelectorAll("[data-p]").forEach(i=>i.onchange=()=>{S.prefs[i.dataset.p]=i.checked;LS.set("prefs",S.prefs);toast(i.checked?"Aviso activado":"Aviso desactivado")});
    m.querySelector("[data-close]").onclick=close;
    m.querySelector("#logout").onclick=()=>{S.user=null;LS.set("user",null);close();renderUser();toast("Has cerrado sesión")}});
}
function alertModal(){
  if(!S.user){login(alertModal);return}
  const g=G,cur=g.b?g.b.p:0,sug=Math.max(1,Math.floor(cur*0.8));
  modal(`<h2>Avísame si baja de precio</h2><p>${esc(g.n)} · ahora desde <b class="num">${eur(cur)}</b></p>
    <label class="field"><input id="alertP" type="number" min="1" step="0.5" value="${S.alerts[g.id]||sug}" aria-label="Precio objetivo"><span>€</span></label>
    <p style="font-size:12.5px">Te escribiremos a ${esc(S.user.email)} cuando alguna tienda lo tenga por debajo de ese precio.</p>
    <div style="display:flex;gap:8px"><button class="btn btn-gold" id="alertOk" style="flex:1">Crear aviso</button>${S.alerts[g.id]?`<button class="btn btn-line" id="alertDel">Quitar aviso</button>`:""}</div>`,
  (m,close)=>{m.querySelector("#alertOk").onclick=()=>{const v=parseFloat(m.querySelector("#alertP").value);if(!(v>0)){toast("Escribe un precio válido");return}S.alerts[g.id]=v;LS.set("alerts",S.alerts);if(!S.wish.has(g.id)){S.wish.add(g.id);saveWish()}close();renderBuy();toast("Aviso creado: te escribiremos si baja de "+eur(v))};
    const d=m.querySelector("#alertDel");if(d)d.onclick=()=>{delete S.alerts[g.id];LS.set("alerts",S.alerts);close();renderBuy();toast("Aviso eliminado")}});
}
function renderUser(){
  $("#userSlot").innerHTML=S.user?`<button class="avatar" data-act="account" aria-label="Mi cuenta">${S.user.name[0]}</button>`:`<button class="btn btn-gold" data-act="login"><span class="g-ico">G</span><span class="hdr-login-t">Entrar</span></button>`;
}
const LEGAL={
 "aviso-afiliados":["Aviso de afiliación",`<p>OfertaGG es un comparador de precios de videojuegos. <b>No vendemos juegos</b> ni gestionamos pagos ni claves: cuando pulsas "Ir a comprar", te llevamos a la tienda que has elegido y la compra se hace allí, bajo sus condiciones.</p>
<p>Algunos de los enlaces de esta web son <b>enlaces de afiliado</b>. Si compras a través de ellos, la tienda puede pagarnos una pequeña comisión. <b>Para ti el precio es exactamente el mismo.</b> Estas comisiones nos ayudan a mantener la web gratuita.</p>
<p>Las comisiones no influyen en el orden de los precios: siempre mostramos primero la oferta más barata, sea de la tienda que sea.</p>
<p>Los precios se actualizan de forma automática varias veces por semana y pueden cambiar en la tienda en cualquier momento. El precio válido es siempre el que aparece en la tienda al hacer la compra.</p>`],
 "privacidad":["Política de privacidad",`<p><b>Responsable:</b> OfertaGG. Contacto: <span class="sel">${CONTACT_EMAIL}</span>.</p>
<p><b>Qué datos tratamos.</b> Ahora mismo OfertaGG no tiene registro de usuarios ni formularios, así que no recogemos tu nombre ni tu correo. Tu lista de deseos y tus preferencias se guardan solo en tu navegador (almacenamiento local) y no nos llegan.</p>
<p><b>Datos técnicos.</b> Nuestro proveedor de alojamiento, Netlify, registra de forma automática datos técnicos de las visitas (como la dirección IP y el navegador) para servir la web y protegerla. Las fuentes tipográficas se cargan desde Google Fonts, que también recibe la dirección IP de quien visita la web.</p>
<p><b>Enlaces a tiendas.</b> Cuando pulsas un enlace a una tienda, sales de OfertaGG. A partir de ahí se aplica la política de privacidad de esa tienda.</p>
<p><b>Tus derechos.</b> Puedes pedirnos acceso, rectificación o supresión de tus datos escribiendo a <span class="sel">${CONTACT_EMAIL}</span>. También puedes reclamar ante la Agencia Española de Protección de Datos (aepd.es).</p>
<p>Cuando activemos el acceso con Google y los avisos por correo, actualizaremos esta política antes de empezar a usarlos.</p>`],
 "cookies":["Política de cookies",`<p>OfertaGG <b>no usa cookies de publicidad ni de seguimiento</b>.</p>
<p>Solo usamos el almacenamiento local de tu navegador para recordar tu lista de deseos y tus preferencias. Es información que se queda en tu dispositivo y puedes borrarla cuando quieras desde los ajustes de tu navegador.</p>
<p>Las tiendas a las que enlazamos pueden usar sus propias cookies cuando entras en su web, incluidas las que identifican que llegas desde un enlace de afiliado. Consulta la política de cookies de cada tienda.</p>`],
 "contacto":["Contacto",`<p>¿Has visto un precio mal, quieres proponer un juego o eres una tienda y quieres colaborar con nosotros?</p>
<p>Escríbenos a: <span class="sel big">${CONTACT_EMAIL}</span></p>
<p>Respondemos normalmente en uno o dos días.</p>`]
};
function viewLegal(k){
  const [t,body]=LEGAL[k];
  app.innerHTML=`<div class="wrap"><nav class="crumbs"><a href="#">Inicio</a><span>/</span><span>${t}</span></nav>
    <article class="legal-page"><h1>${t}</h1>${body}<p class="legal-upd">Última actualización: ${fmtDL(today)}</p></article></div>`;
}
function viewWish(){
  const list=[...S.wish].map(id=>BYID[id]).filter(Boolean);
  app.innerHTML=`<div class="wrap"><nav class="crumbs"><a href="#">Inicio</a><span>/</span><span>Lista de deseos</span></nav>
    <div class="cat-head" style="margin-top:16px"><h1>Mi lista de deseos</h1>${!S.user?`<button class="btn btn-line" data-act="login">${ICON.bell}Entrar para recibir avisos</button>`:""}</div>
    ${list.length?`<div class="grid">${list.map(card).join("")}</div>`:`<div class="empty"><b>Tu lista está vacía.</b><br>Pulsa el corazón de cualquier juego para guardarlo y te avisaremos cuando baje de precio.</div>`}</div>`;
}

/* ---------- search with suggestions ---------- */
const sIn=$("#q"), sBox=$("#sugg"); let sIdx=-1, sItems=[];
function hl(name,q){if(!q)return esc(name);const n=norm(name);const i=n.indexOf(q);if(i<0)return esc(name);return esc(name.slice(0,i))+"<mark>"+esc(name.slice(i,i+q.length))+"</mark>"+esc(name.slice(i+q.length))}
function score(g,q){const n=norm(g.n);if(n.startsWith(q))return 3;if(n.split(" ").some(w=>w.startsWith(q)))return 2;if(n.includes(q))return 1;if(norm(g.dev.concat(g.pub).join(" ")).includes(q))return .5;return 0}
function suggest(){
  const raw=sIn.value.trim(), q=norm(raw);
  if(!q){
    const trend=[...GAMES].filter(g=>!g.soon).sort((a,b)=>b.rec-a.rec).slice(0,5);
    sItems=trend;
    sBox.innerHTML=`<div class="sugg-h"><span class="eyebrow">Tendencias</span></div>${trend.map((g,i)=>sRow(g,"",i)).join("")}
      <div class="sugg-h"><span class="eyebrow">Géneros</span></div><div class="sugg-chips">${GENRE_ORDER.slice(0,9).map(gn=>`<a class="chip" href="#juegos-${slug(gn)}">${gn}</a>`).join("")}</div>`;
  } else {
    const gens=GENRE_ORDER.filter(gn=>norm(gn).startsWith(q));
    sItems=GAMES.map(g=>({g,s:score(g,q)})).filter(x=>x.s>0).sort((a,b)=>b.s-a.s||b.g.rec-a.g.rec).slice(0,6).map(x=>x.g);
    sBox.innerHTML=(gens.length?`<div class="sugg-chips" style="padding-top:12px">${gens.map(gn=>`<a class="chip" href="#juegos-${slug(gn)}">Género: ${gn}</a>`).join("")}</div>`:"")+
      (sItems.length?`<div class="sugg-h"><span class="eyebrow">Juegos</span><span class="eyebrow">Mejor precio</span></div>${sItems.map((g,i)=>sRow(g,q,i)).join("")}`:`<div class="sugg-empty">No encontramos "${esc(raw)}". Revisa cómo está escrito o prueba con otra palabra.</div>`)+
      `<button class="sugg-all" data-all>Ver todos los resultados de "${esc(raw)}" →</button>`;
  }
  sIdx=-1; sBox.hidden=false;
  sBox.querySelectorAll("[data-sg]").forEach(r=>r.onmousedown=e=>{e.preventDefault();go("#juego-"+r.dataset.sg)});
  sBox.querySelectorAll("a.chip").forEach(a=>a.onmousedown=e=>{e.preventDefault();go(a.getAttribute("href"))});
  const all=sBox.querySelector("[data-all]");if(all)all.onmousedown=e=>{e.preventDefault();go("#buscar-"+encodeURIComponent(raw))};
}
function sRow(g,q,i){const b=g.b;return `<div class="sugg-item" role="option" data-sg="${g.id}" data-i="${i}"><img src="${img(g.id,"h")}" alt=""><div style="min-width:0"><div class="sugg-name">${hl(g.n,q)}</div><div class="sugg-meta">${g.soon?"Reserva · ":""}${esc(g.g.slice(0,3).join(" · "))}</div></div>
  <div class="sugg-price num">${b?b.free?"Gratis":eur(b.p):""}${b&&!b.free?`<div>${store(b.o.s)}</div>`:""}</div></div>`}
function go(h){sBox.hidden=true;sIn.blur();if(location.hash===h)route();else location.hash=h}
sIn.addEventListener("focus",suggest);sIn.addEventListener("input",suggest);
sIn.addEventListener("blur",()=>setTimeout(()=>sBox.hidden=true,120));
sIn.addEventListener("keydown",e=>{
  const rows=[...sBox.querySelectorAll(".sugg-item")];
  if(e.key==="ArrowDown"||e.key==="ArrowUp"){e.preventDefault();sIdx=(sIdx+(e.key==="ArrowDown"?1:-1)+rows.length)%rows.length;rows.forEach((r,i)=>r.classList.toggle("on",i===sIdx));rows[sIdx]&&rows[sIdx].scrollIntoView({block:"nearest"})}
  if(e.key==="Enter"){e.preventDefault();if(sIdx>=0&&rows[sIdx])go("#juego-"+rows[sIdx].dataset.sg);else if(sIn.value.trim())go("#buscar-"+encodeURIComponent(sIn.value.trim()))}
  if(e.key==="Escape"){sBox.hidden=true;sIn.blur()}});
document.addEventListener("keydown",e=>{if(e.key==="/"&&!/input|textarea|select/i.test(document.activeElement.tagName)){e.preventDefault();sIn.focus()}});

/* mega menu */
const mega=$("#mega");
$("#megaBtn").onclick=e=>{e.stopPropagation();mega.hidden=!mega.hidden;$("#megaBtn").setAttribute("aria-expanded",!mega.hidden)};
$("#megaGrid").innerHTML=GENRE_ORDER.map(gtile).join("");
document.addEventListener("click",e=>{if(!mega.hidden&&!mega.contains(e.target))mega.hidden=true});

/* global delegation */
document.addEventListener("click",e=>{
  const w=e.target.closest("[data-wish]");
  if(w){e.preventDefault();e.stopPropagation();const id=+w.dataset.wish;
    if(S.wish.has(id)){S.wish.delete(id);toast("Quitado de tu lista")}else{S.wish.add(id);toast(S.user?"Añadido a tu lista · te avisaremos si baja":"Añadido a tu lista de deseos")}
    saveWish();
    document.querySelectorAll(`.heart[data-wish="${id}"]`).forEach(h=>{const on=S.wish.has(id);h.classList.toggle("on",on);h.innerHTML=on?ICON.heart:ICON.heartO});
    if(G&&G.id===id&&$("#buy"))renderBuy();
    if(w.classList.contains("btn")&&!w.closest("#buy"))w.textContent=S.wish.has(id)?"En tu lista":"Añadir a mi lista";
    if(location.hash==="#deseos")viewWish();
    return}
  const a=e.target.closest("[data-act]");
  if(a){const k=a.dataset.act;if(k==="login")login();if(k==="account")account();if(k==="alert")alertModal()}
});

/* ---------- router ---------- */
function route(){
  const h=decodeURIComponent(location.hash.slice(1));
  clearInterval(heroT); mega.hidden=true;
  document.querySelectorAll(".nav [data-nav]").forEach(a=>a.classList.toggle("on",h.startsWith(a.dataset.nav)&&a.dataset.nav!==""||(!h&&a.dataset.nav==="")));
  if(h.startsWith("juego-")) viewGame(+h.slice(6));
  else if(h.startsWith("juegos-")) viewCatalog("all",h.slice(7));
  else if(h==="juegos") viewCatalog("all");
  else if(h==="ofertas"||h==="novedades"||h==="proximamente"||h==="gratis") viewCatalog(h);
  else if(h.startsWith("buscar-")) {sIn.value=h.slice(7);viewCatalog("search",null,h.slice(7))}
  else if(h==="deseos") viewWish();
  else if(LEGAL[h]) viewLegal(h);
  else viewHome();
  window.scrollTo(0,0);
}
window.addEventListener("hashchange",route);
$("#updTxt").textContent=`Precios del ${fmtD(UPD)}`;
if(!D.demo)$("#demoBar").hidden=true;
renderUser(); updWish(); route();
})();
