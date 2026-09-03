(() => {
  "use strict";
  const data = JSON.parse(document.getElementById("clineflow-data").textContent);
  const $ = (selector, root = document) => root.querySelector(selector);
  const esc = (value = "") => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const compact = new Intl.NumberFormat(undefined, {notation: "compact", maximumFractionDigits: 1});
  const full = new Intl.NumberFormat();
  const time = value => value ? new Date(value).toLocaleString() : "Not recorded";
  const timeline = [
    ...data.events.map(item => ({...item, lane: "event", when: item.at, label: item.type || "event"})),
    ...data.documents.filter(item => item.generated_at).map(item => ({...item, lane: "journal", when: item.generated_at, label: "journal", summary: item.title})),
    ...data.commits.map(item => ({...item, lane: "commit", when: item.committed_at, label: "git"})),
    ...(data.runs || []).map(item => ({...item, lane: "run", when: item.generated_at, label: "visor", summary: `Dashboard run ${item.run_id}`}))
  ].sort((a,b) => new Date(b.when) - new Date(a.when));
  const latest = timeline[0];
  const specification = data.ledgers.clineflow_specification || {};
  const verification = data.ledgers.clineflow_verification || {};
  const goals = data.ledgers.clineflow_goals || {};
  const session = data.ledgers.clineflow_last_session || {};
  const summary = data.insights?.executive_summary || session.latest_change || "Durable context is ready to explore.";
  const latestVerification = data.events.filter(item => item.type === "verification").sort((a,b) => new Date(b.at)-new Date(a.at))[0];
  const unresolved = (specification.open_questions || []).length + (verification.open_verification || []).length;

  document.getElementById("app").innerHTML = `<main class="shell" id="main">
    <header class="topbar"><div class="brand"><span class="brand-mark">CF</span><span>Knowledge Visor / ${esc(data.schema.split("/")[1])}</span></div><div class="toolbar"><span class="pill">${data.git.dirty ? "Working tree · changed" : "Working tree · clean"}</span><button id="time-mode" type="button">Local time</button><span class="pill">${esc(data.git.branch || "detached")}</span></div></header>
    <section class="hero"><article class="hero-main"><div><p class="eyebrow">Executive time brief · ${esc(time(data.run_at))}</p><h1>See how the thinking evolved.</h1><p class="lede">${esc(summary)}</p></div><div class="legend"><span><i class="dot" style="background:var(--mint)"></i>Knowledge events</span><span><i class="dot" style="background:var(--cyan)"></i>Git commits</span><span><i class="dot" style="background:var(--violet)"></i>Evidence</span></div></article>
      <aside class="hero-side"><div class="metric"><span class="label">Latest recorded activity</span><strong>${esc(latest ? new Date(latest.when).toLocaleDateString(undefined,{month:"short",day:"numeric"}) : "—")}</strong></div><div class="metric"><span class="label">Latest verification</span><strong>${esc(latestVerification ? new Date(latestVerification.at).toLocaleDateString(undefined,{month:"short",day:"numeric"}) : "—")}</strong></div><div class="metric"><span class="label">Open questions</span><strong>${full.format(unresolved)}</strong></div><div class="metric"><span class="label">Knowledge footprint</span><strong>${compact.format(data.current_footprint.knowledge_bytes)}B</strong></div><div class="metric"><span class="label">Current net lines</span><strong>${data.current_change.net >= 0 ? "+" : ""}${full.format(data.current_change.net)}</strong></div></aside></section>
    <div class="grid">
      <section class="panel wide"><div class="panel-head"><div><h2>Time spine</h2><p class="panel-copy">Exact knowledge and Git chronology remain separate; dashed annotations are inferred.</p></div></div><div class="time-spine" id="time-spine"></div></section>
      <section class="panel"><div class="panel-head"><div><h2>Change pulse</h2><p class="panel-copy">Committed additions and deletions by moment.</p></div></div><div class="chart" id="change-chart" role="img" aria-label="Git change volume over time"></div></section>
      <section class="panel"><div class="panel-head"><div><h2>Growth ribbon</h2><p class="panel-copy">Tracked project and canonical knowledge bytes.</p></div></div><div class="chart" id="growth-chart" role="img" aria-label="Project and knowledge growth over time"></div></section>
      <section class="panel wide"><div class="panel-head"><div><h2>Decision Atlas</h2><p class="panel-copy">The five ledgers and journals as one inspectable evidence network.</p></div></div><div id="decision-graph" role="img" aria-label="Knowledge relationship graph"></div></section>
      <section class="panel third"><div class="panel-head"><div><h2>Integrity signals</h2><p class="panel-copy">Transparent facts, never a magic score.</p></div></div><div class="signals" id="signals"></div></section>
      <section class="panel third"><div class="panel-head"><div><h2>Drift since baseline</h2><p class="panel-copy">Changed canonical sources.</p></div></div><div class="signals" id="drift"></div></section>
      <section class="panel third"><div class="panel-head"><div><h2>Evidence matrix</h2><p class="panel-copy">Requirements and their available evidence surface.</p></div></div><div class="signals" id="evidence"></div></section>
      <section class="panel wide"><div class="panel-head"><div><h2>About this report</h2><p class="panel-copy">Pinned, locally embedded components and their preserved license identifiers.</p></div></div><div class="asset-grid" id="about"></div></section>
      <section class="panel wide"><div class="panel-head"><div><h2>Knowledge Explorer</h2><p class="panel-copy">Read the durable source without leaving the timeline.</p></div><input class="search" id="search" type="search" placeholder="Search journals and ledgers…" aria-label="Search knowledge"></div><div class="documents"><nav class="document-list" id="document-list" aria-label="Knowledge documents"></nav><article class="document-body" id="document-body"></article></div></section>
    </div><footer class="footer"><span>Generated ${esc(data.run_at)} · ${esc(data.run_id)}</span><span>Private local report · no browser network access</span></footer></main>`;

  let utc = false;
  const renderTimeline = () => {
    $("#time-spine").innerHTML = timeline.slice(0, 80).map(item => {
      const displayed = utc ? new Date(item.when).toISOString() : time(item.when);
      const inferred = item.lane === "event" && item.association?.kind === "inferred" ? `<div class="inferred">┈ likely ${esc(item.association.short_revision)} via ${esc(item.association.matching_refs.join(", "))}</div>` : "";
      return `<div class="time-row"><time title="${esc(item.when)}">${esc(displayed)}</time><span class="lane ${item.lane}">${esc(item.label)}</span><div class="time-summary">${esc(item.summary)}${inferred}</div></div>`;
    }).join("") || `<div class="empty">No timeline data recorded.</div>`;
  };
  $("#time-mode").addEventListener("click", event => { utc = !utc; event.currentTarget.textContent = utc ? "UTC time" : "Local time"; renderTimeline(); });
  renderTimeline();

  const chartBase = {backgroundColor:"transparent", textStyle:{color:"#8db5a9",fontFamily:"IBM Plex Mono"}, grid:{left:50,right:18,top:20,bottom:48}, tooltip:{trigger:"axis",backgroundColor:"#071412",borderColor:"#28534a",textStyle:{color:"#edfff9"}}, xAxis:{type:"category",axisLabel:{color:"#739b90",hideOverlap:true},axisLine:{lineStyle:{color:"#22413b"}}},yAxis:{type:"value",axisLabel:{color:"#739b90"},splitLine:{lineStyle:{color:"rgba(155,255,226,.08)"}}}};
  const commitLabels = data.commits.map(c => new Date(c.committed_at).toLocaleDateString(undefined,{month:"short",day:"numeric"}));
  const charts = [];
  const lazy = (element, initialize) => {
    if (!("IntersectionObserver" in window)) { initialize(); return; }
    const observer = new IntersectionObserver(entries => { if(entries.some(entry=>entry.isIntersecting)){ observer.disconnect(); initialize(); } }, {rootMargin:"180px"});
    observer.observe(element);
  };
  lazy($("#change-chart"), () => { const chart=echarts.init($("#change-chart")); charts.push(chart); chart.setOption({...chartBase,xAxis:{...chartBase.xAxis,data:commitLabels},series:[{name:"Added",type:"bar",stack:"change",data:data.commits.map(c=>c.change.insertions),itemStyle:{color:"#65fbd2",borderRadius:[4,4,0,0]}},{name:"Deleted",type:"bar",stack:"change",data:data.commits.map(c=>-c.change.deletions),itemStyle:{color:"#ff7f9f",borderRadius:[0,0,4,4]}}]}); });
  lazy($("#growth-chart"), () => { const chart=echarts.init($("#growth-chart")); charts.push(chart); chart.setOption({...chartBase,xAxis:{...chartBase.xAxis,data:commitLabels},yAxis:{...chartBase.yAxis,axisLabel:{...chartBase.yAxis.axisLabel,formatter:value=>compact.format(value)}},series:[{name:"Tracked",type:"line",smooth:true,symbolSize:4,data:data.commits.map(c=>c.footprint.tracked_bytes),lineStyle:{color:"#69d9ff",width:2},areaStyle:{color:"rgba(105,217,255,.08)"}},{name:"Knowledge",type:"line",smooth:true,symbolSize:4,data:data.commits.map(c=>c.footprint.knowledge_bytes),lineStyle:{color:"#b29cff",width:2},areaStyle:{color:"rgba(178,156,255,.08)"}}]}); });

  const ledgerNodes = Object.keys(data.ledgers).map((id,index)=>({data:{id:`ledger-${id}`,label:id.replace("clineflow_","").replaceAll("_"," "),kind:"ledger"},position:{x:220+index*220,y:120}}));
  const docNodes = data.documents.map((doc,index)=>({data:{id:doc.id,label:doc.title,kind:"document"},position:{x:120+(index%6)*220,y:310+Math.floor(index/6)*120}}));
  const edges = [];
  Object.entries(data.ledgers).forEach(([ledgerId, ledger]) => {
    const refs = new Set([...(ledger.journal_refs||[]), ...(ledger.evidence_refs||[]), ...(ledger.next_step_refs||[])]);
    data.documents.forEach(doc => { if ([...refs].some(ref => doc.path.endsWith(String(ref).replace(/^\.\.\//,"")))) edges.push({data:{id:`${ledgerId}-${doc.id}`,source:`ledger-${ledgerId}`,target:doc.id}}); });
  });
  lazy($("#decision-graph"), () => { const graph=cytoscape({container:$("#decision-graph"),elements:[...ledgerNodes,...docNodes,...edges],layout:{name:"cose",animate:false,padding:30},style:[{selector:"node",style:{"background-color":"#173a34","border-color":"#65fbd2","border-width":1,"label":"data(label)","color":"#dff9f1","font-family":"Space Grotesk","font-size":10,"text-wrap":"wrap","text-max-width":110,"text-valign":"bottom","text-margin-y":8,"width":24,"height":24}},{selector:'node[kind="ledger"]',style:{"background-color":"#65fbd2","border-color":"#b9ffeb","color":"#65fbd2","width":34,"height":34,"font-weight":600}},{selector:"edge",style:{"width":1,"line-color":"#28534a","target-arrow-color":"#28534a","target-arrow-shape":"triangle","curve-style":"bezier","opacity":.72}}]}); graph.on("tap","node",event=>{ const doc=data.documents.find(item=>item.id===event.target.id()); if(doc) selectDocument(doc.id); }); });

  const knowledgeRefs = data.events.flatMap(event=>event.refs||[]).filter(ref=>/^(?:\.\.\/)?knowledge\/|^journals\//.test(String(ref)));
  const brokenRefs = knowledgeRefs.filter(ref=>!data.documents.some(doc=>doc.path.endsWith(String(ref).replace(/^\.\.\//,"").replace(/^knowledge\//,""))||doc.path.endsWith(String(ref).replace(/^\.\.\//,""))));
  const updated = Object.values(data.ledgers).map(item=>item.updated_at).filter(Boolean);
  const signals = [["Canonical sources",data.documents.length],["Timeline events",data.events.length],["Ledger timestamps",new Set(updated).size===1?"aligned":"differ"],["Unresolved questions",unresolved],["Unresolved references",new Set(brokenRefs).size],["Exact usage records",(data.usage||[]).length]];
  $("#signals").innerHTML=signals.map(([label,value])=>`<div class="signal"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join("");
  const driftRows=[["Baseline",data.baseline_run||"first run"],["Added",data.drift.added.length],["Changed",data.drift.changed.length],["Removed",data.drift.removed.length]];
  $("#drift").innerHTML=driftRows.map(([label,value])=>`<div class="signal"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join("")+`<details><summary>Inspect changed sources</summary><p>${esc([...data.drift.added,...data.drift.changed,...data.drift.removed].slice(0,40).join(" · ")||"No canonical source drift.")}</p></details>`;
  $("#evidence").innerHTML=[["Requirements recorded",specification.updated_at||"—"],["Evidence reviewed",verification.updated_at||"—"],["Latest verification",latestVerification?.at||"—"],["Acceptance criteria",(verification.acceptance_criteria||[]).length],["Evidence references",(verification.evidence_refs||[]).length],["Open verification",(verification.open_verification||[]).length]].map(([label,value])=>`<div class="signal"><span>${esc(label)}</span><strong title="${esc(value)}">${esc(value)}</strong></div>`).join("");
  $("#about").innerHTML=(data.asset_manifest||[]).map(asset=>`<article class="asset"><strong>${esc(asset.name)}</strong><span>${esc(asset.version)} · ${esc(asset.license)}</span><code>${esc(asset.sha256.slice(0,16))}…</code></article>`).join("");

  const renderDocuments = query => {
    const normalized=query.trim().toLowerCase();
    const matches=data.documents.filter(doc=>!normalized||`${doc.title} ${doc.description} ${doc.path} ${(doc.tags||[]).join(" ")} ${doc.raw}`.toLowerCase().includes(normalized));
    $("#document-list").innerHTML=matches.slice(0,150).map(doc=>`<button class="document-button" data-id="${esc(doc.id)}"><strong>${esc(doc.title)}</strong><small>${esc(doc.path)}</small></button>`).join("")||`<div class="empty">No matching knowledge.</div>`;
    $("#document-list").querySelectorAll("button").forEach(button=>button.addEventListener("click",()=>selectDocument(button.dataset.id)));
  };
  function selectDocument(id){ const doc=data.documents.find(item=>item.id===id); if(!doc)return; $("#document-body").innerHTML=`<p class="eyebrow">${esc(doc.path)} · ${esc(doc.status||"source")}</p>${doc.html}`; document.querySelectorAll(".document-button").forEach(button=>button.classList.toggle("active",button.dataset.id===id)); }
  $("#search").addEventListener("input",event=>renderDocuments(event.target.value));
  renderDocuments(""); if(data.documents[0])selectDocument(data.documents[0].id);
  addEventListener("resize",()=>charts.forEach(chart=>chart.resize()));
  if(!matchMedia("(prefers-reduced-motion: reduce)").matches){gsap.from(".hero-main,.hero-side,.panel",{opacity:0,y:18,duration:.7,stagger:.045,ease:"power2.out"});}
})();
