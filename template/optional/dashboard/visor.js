(() => {
  "use strict";
  const data = JSON.parse(document.getElementById("clineflow-data").textContent);
  const observations = JSON.parse(document.getElementById("clineflow-observations").textContent);
  const $ = (selector, root = document) => root.querySelector(selector);
  const esc = (value = "") => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const compact = new Intl.NumberFormat(undefined, {notation: "compact", maximumFractionDigits: 1});
  const full = new Intl.NumberFormat();
  const time = value => value ? new Date(value).toLocaleString() : "Not recorded";
  const eventValue = (event, keys) => keys.map(key=>event?.[key]).find(value=>value!==undefined&&value!==null&&value!=="");
  const eventTime = event => eventValue(event,["at","timestamp","occurred_at","datetime","date","time"]);
  const eventType = event => eventValue(event,["type","kind","category","event_type","action"])||"event";
  const eventSummary = event => eventValue(event,["summary","text","description","message","detail","change","event"]);
  const compactTitle = value => { const text=String(value||"Recorded event").replace(/\s+/g," ").trim(); const first=text.split(/(?<=[.!?])\s+|\s+\(|\s+—\s+|\s+[-:]\s+/)[0]||text; return first.length<=74?first:`${first.slice(0,75).replace(/\s+\S*$/,"").replace(/[.,;:]$/,"")}…`; };
  const eventTitle = event => eventValue(event,["short_title","title","label","name"])||compactTitle(eventSummary(event));
  const eventRefs = event => { const refs=eventValue(event,["refs","references","links","journal_refs","evidence_refs"]); return Array.isArray(refs)?refs:(refs?[refs]:[]); };
  const timeline = [
    ...data.events.map(item => ({...item, lane: "event", when: eventTime(item), label: eventType(item), title:eventTitle(item), summary: eventSummary(item)||"Event recorded without a narrative summary."})),
    ...data.documents.filter(item => item.generated_at).map(item => ({...item, lane: "journal", when: item.generated_at, label: "journal", title:item.title, summary: item.description||item.title})),
    ...data.commits.map(item => ({...item, lane: "commit", when: item.committed_at, label: "git", title:compactTitle(item.summary), summary:item.summary})),
    ...(data.runs || []).map(item => ({...item, lane: "run", when: item.generated_at, label: "visor", title:"Dashboard report generated", summary: `Dashboard run ${item.run_id}`}))
  ].sort((a,b) => new Date(b.when) - new Date(a.when));
  const latestRecorded = timeline.find(item => item.lane === "event" || item.lane === "commit") || timeline[0];
  const specification = data.ledgers.clineflow_specification || {};
  const verification = data.ledgers.clineflow_verification || {};
  const goals = data.ledgers.clineflow_goals || {};
  const session = data.ledgers.clineflow_last_session || {};
  const summary = observations.executive_summary || session.latest_change || "Durable context is ready to explore.";
  const latestVerification = data.events.filter(item => eventType(item) === "verification").sort((a,b) => new Date(eventTime(b))-new Date(eventTime(a)))[0];
  const unresolved = (specification.open_questions || []).length + (verification.open_verification || []).length;
  const currentIntent = (goals.active_goals || [])[0] || session.next_recommended_step || "No active goal recorded.";
  const nextMove = session.next_recommended_step || "Review the latest durable context.";
  const phase = latestRecorded?.label ? String(latestRecorded.label).replaceAll("_", " ") : "not recorded";
  const evidenceCount = (verification.evidence_refs || []).length;

  document.getElementById("app").innerHTML = `<main class="shell" id="main">
    <header class="topbar"><div class="brand"><span class="brand-mark">CF</span><span>Knowledge Visor / ${esc(data.schema.split("/")[1])}</span></div><div class="toolbar"><span class="pill">${data.git.dirty ? "Working tree · changed" : "Working tree · clean"}</span><button id="time-mode" type="button">Local time</button><span class="pill">${esc(data.git.branch || "detached")}</span></div></header>
    <nav class="story-nav" aria-label="Dashboard story"><a href="#executive"><span>01</span>Now</a><a href="#trajectory"><span>02</span>Trajectory</a><a href="#decisions"><span>03</span>Story</a><a href="#proof"><span>04</span>Proof</a><a href="#source"><span>05</span>Source</a></nav>
    <section class="hero" id="executive"><article class="hero-main"><div><p class="eyebrow">01 / Executive brief · ${esc(time(data.run_at))}</p><h1>What changed.<br>Why it matters.<br>What comes next.</h1><p class="lede">${esc(summary)}</p></div><div class="audience-switch" id="audience-switch" role="tablist" aria-label="Narrative audience"><button class="active" data-audience="executive" role="tab" aria-selected="true">Executive</button><button data-audience="manager" role="tab" aria-selected="false">Manager</button><button data-audience="engineer" role="tab" aria-selected="false">Engineer</button></div><div class="audience-story" id="audience-story" aria-live="polite"></div><div class="brief-grid"><div><span class="label">Current intent</span><p>${esc(currentIntent)}</p></div><div><span class="label">Latest proof</span><p>${esc(latestVerification?.summary || "No verification event recorded yet.")}</p></div><div><span class="label">Next move</span><p>${esc(nextMove)}</p></div></div><div class="legend"><span><i class="dot" style="background:var(--mint)"></i>Knowledge events</span><span><i class="dot" style="background:var(--cyan)"></i>Git commits</span><span><i class="dot" style="background:var(--violet)"></i>Evidence</span></div></article>
      <aside class="hero-side"><div class="metric"><span class="label">Latest knowledge activity</span><strong>${esc(latestRecorded?.when ? new Date(latestRecorded.when).toLocaleDateString(undefined,{month:"short",day:"numeric"}) : "—")}</strong></div><div class="metric"><span class="label">Latest verification</span><strong>${esc(eventTime(latestVerification) ? new Date(eventTime(latestVerification)).toLocaleDateString(undefined,{month:"short",day:"numeric"}) : "—")}</strong></div><div class="metric"><span class="label">Open questions</span><strong>${full.format(unresolved)}</strong></div><div class="metric"><span class="label">Knowledge footprint</span><strong>${compact.format(data.current_footprint.knowledge_bytes)}B</strong></div><div class="metric"><span class="label">Current net lines</span><strong>${data.current_change.net >= 0 ? "+" : ""}${full.format(data.current_change.net)}</strong></div></aside></section>
    <div class="grid">
      <header class="chapter" id="trajectory"><span>02</span><div><p class="eyebrow">Manager view</p><h2>Trajectory and change</h2><p>Follow the sequence, scope, and growth behind the current phase: <strong>${esc(phase)}</strong>.</p></div></header>
      <section class="panel wide"><div class="panel-head"><div><h2>Time spine</h2><p class="panel-copy">Exact knowledge and Git chronology remain separate; dashed annotations are inferred.</p></div></div><div class="time-spine" id="time-spine"></div></section>
      <section class="panel"><div class="panel-head"><div><h2>Change pulse</h2><p class="panel-copy">Committed additions and deletions by moment.</p></div></div><div class="chart" id="change-chart" role="img" aria-label="Git change volume over time"></div></section>
      <section class="panel"><div class="panel-head"><div><h2>Growth ribbon</h2><p class="panel-copy">Tracked project and canonical knowledge bytes.</p></div></div><div class="chart" id="growth-chart" role="img" aria-label="Project and knowledge growth over time"></div></section>
      <header class="chapter" id="decisions"><span>03</span><div><p class="eyebrow">Reasoning view</p><h2>The project story</h2><p>Not a graph: a source-bound explanation of how the work evolved, what matters now, and where attention belongs next.</p></div></header>
      <section class="panel wide project-story-panel"><div class="panel-head"><div><h2>Project story</h2><p class="panel-copy">Each claim below is derived from facts and hands off to its canonical record.</p></div><span class="story-badge">Source-bound reasoning</span></div><div id="project-story" class="project-story" aria-live="polite"></div></section>
      <header class="chapter" id="proof"><span>04</span><div><p class="eyebrow">Shared proof</p><h2>Confidence without a magic score</h2><p>${full.format(evidenceCount)} evidence references, explicit open questions, and source drift remain inspectable.</p></div></header>
      <section class="panel third"><div class="panel-head"><div><h2>Integrity signals</h2><p class="panel-copy">Transparent facts, never a magic score.</p></div></div><div class="signals" id="signals"></div></section>
      <section class="panel third"><div class="panel-head"><div><h2>Drift since baseline</h2><p class="panel-copy">Changed canonical sources.</p></div></div><div class="signals" id="drift"></div></section>
      <section class="panel third"><div class="panel-head"><div><h2>Evidence matrix</h2><p class="panel-copy">Requirements and their available evidence surface.</p></div></div><div class="signals" id="evidence"></div></section>
      <header class="chapter" id="source"><span>05</span><div><p class="eyebrow">Source of truth</p><h2>Read the record itself</h2><p>Search the canonical ledgers and engineering journals behind every summary above.</p></div></header>
      <section class="panel wide explorer-panel"><div class="panel-head"><div><h2>Knowledge Explorer</h2><p class="panel-copy">Understand the model first; inspect YAML or Markdown only when you need it.</p></div><div class="explorer-tools"><div class="document-filters" id="document-filters" role="group" aria-label="Document type"><button class="active" data-filter="all" type="button">All</button><button data-filter="ledger" type="button">Ledgers</button><button data-filter="journal" type="button">Journals</button></div><input class="search" id="search" type="search" placeholder="Search decisions, evidence, journals…" aria-label="Search knowledge"></div></div><div class="documents"><nav class="document-list" id="document-list" aria-label="Knowledge documents"></nav><article class="document-body" id="document-body"></article></div></section>
    </div><footer class="footer"><span>Generated ${esc(data.run_at)} · ${esc(data.run_id)}</span><span>Private local report · no browser network access</span></footer></main>`;

  const renderAudience = audience => {
    const story=observations.audiences?.[audience]||{};
    $("#audience-story").innerHTML=`<div><span class="label">The read</span><strong>${esc(story.headline||summary)}</strong></div><div><span class="label">Why it matters</span><p>${esc(story.why_it_matters||"Open the evidence below to inspect why this matters.")}</p></div><div><span class="label">Recommended move</span><p>${esc(story.next_move||nextMove)}</p></div>`;
  };
  $("#audience-switch").querySelectorAll("button").forEach(button=>button.addEventListener("click",()=>{$("#audience-switch").querySelectorAll("button").forEach(item=>{const active=item===button;item.classList.toggle("active",active);item.setAttribute("aria-selected",String(active));});renderAudience(button.dataset.audience);}));
  renderAudience("executive");
  let utc = false;
  const formatTimelineNote = value => String(value||"").split(/\n\s*\n/).map(paragraph=>`<p>${esc(paragraph.trim())}</p>`).join("");
  const renderTimeline = () => {
    $("#time-spine").innerHTML = timeline.slice(0, 80).map(item => {
      const displayed = utc && item.when ? new Date(item.when).toISOString() : time(item.when);
      const inferred = item.lane === "event" && item.association?.kind === "inferred" ? `<div class="inferred">┈ likely ${esc(item.association.short_revision)} via ${esc(item.association.matching_refs.join(", "))}</div>` : "";
      const details=item.summary&&item.summary!==item.title?`<details class="time-details"><summary>Read event note</summary>${formatTimelineNote(item.summary)}</details>`:"";
      return `<div class="time-row"><time title="${esc(item.when)}">${esc(displayed)}</time><span class="lane ${item.lane}">${esc(item.label)}</span><div class="time-summary"><strong>${esc(item.title||item.label)}</strong>${details}${inferred}</div></div>`;
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

  const humanize = value => String(value||"").replace(/^clineflow_/,"").replaceAll("_"," ").replace(/\b\w/g,letter=>letter.toUpperCase());
  const statementText = value => {
    if(value===null||value===undefined) return "Not recorded";
    if(typeof value!=="object") return String(value);
    if(Array.isArray(value)) return value.map(statementText).filter(Boolean).join(" · ")||"Not recorded";
    for(const key of ["text","summary","title","name","criterion","requirement","description","message","label","value"]){
      if(value[key]!==undefined&&value[key]!==null&&typeof value[key]!=="object") return String(value[key]);
    }
    return Object.entries(value).map(([key,item])=>`${humanize(key)}: ${statementText(item)}`).join(" · ")||"Structured record";
  };
  const projectStory = observations.project_story||{};
  const storyCard = (key, tone) => {
    const card=projectStory[key]||{};
    const source=(card.source_ids||[])[0];
    return `<article class="story-card ${esc(tone)}"><p class="eyebrow">${esc(key.replaceAll("_"," "))}</p><h3>${esc(card.title||"Not recorded")}</h3><p>${esc(card.text||"No source-backed observation is available yet.")}</p>${source?`<button type="button" data-story-source="${esc(source)}">Open supporting record <span aria-hidden="true">↗</span></button>`:""}</article>`;
  };
  const renderProjectStory = () => {
    const milestones=(projectStory.milestones||[]).map(item=>`<li><time title="${esc(item.at)}">${esc(time(item.at))}</time><strong>${esc(item.title||"Recorded milestone")}</strong></li>`).join("")||"<li><strong>No chronological milestones are recorded yet.</strong></li>";
    $("#project-story").innerHTML=`<div class="story-arc">${storyCard("evolution","evolution")}<ol class="story-milestones">${milestones}</ol></div><div class="story-actions">${storyCard("important_now","importance")}${storyCard("urgency","urgency")}${storyCard("next_action","next")}</div>`;
    $("#project-story").querySelectorAll("[data-story-source]").forEach(button=>button.addEventListener("click",()=>{selectDocument(button.dataset.storySource);$("#document-body").scrollIntoView({behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth",block:"center"});}));
  };
  renderProjectStory();

  const knowledgeRefs = data.events.flatMap(event=>eventRefs(event)).filter(ref=>/^(?:\.\.\/)?knowledge\/|^journals\//.test(String(ref)));
  const brokenRefs = knowledgeRefs.filter(ref=>!data.documents.some(doc=>doc.path.endsWith(String(ref).replace(/^\.\.\//,"").replace(/^knowledge\//,""))||doc.path.endsWith(String(ref).replace(/^\.\.\//,""))));
  const updated = Object.values(data.ledgers).map(item=>item.updated_at).filter(Boolean);
  const signals = [["Canonical sources",data.documents.length],["Timeline events",data.events.length],["Ledger timestamps",new Set(updated).size===1?"aligned":"differ"],["Unresolved questions",unresolved],["Unresolved references",new Set(brokenRefs).size],["Exact usage records",(data.usage||[]).length]];
  $("#signals").innerHTML=signals.map(([label,value])=>`<div class="signal"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join("");
  const driftRows=[["Baseline",data.baseline_run||"first run"],["Added",data.drift.added.length],["Changed",data.drift.changed.length],["Removed",data.drift.removed.length]];
  $("#drift").innerHTML=driftRows.map(([label,value])=>`<div class="signal"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`).join("")+`<details><summary>Inspect changed sources</summary><p>${esc([...data.drift.added,...data.drift.changed,...data.drift.removed].slice(0,40).join(" · ")||"No canonical source drift.")}</p></details>`;
  $("#evidence").innerHTML=[["Requirements recorded",specification.updated_at||"—"],["Evidence reviewed",verification.updated_at||"—"],["Latest verification",latestVerification?.at||"—"],["Acceptance criteria",(verification.acceptance_criteria||[]).length],["Evidence references",(verification.evidence_refs||[]).length],["Open verification",(verification.open_verification||[]).length]].map(([label,value])=>`<div class="signal"><span>${esc(label)}</span><strong title="${esc(value)}">${esc(value)}</strong></div>`).join("");
  const renderPrimitive = value => value===null||value===undefined ? `<span class="empty-value">Not recorded</span>` : esc(typeof value==="boolean"?(value?"Yes":"No"):statementText(value));
  const renderObject = value => `<dl class="fact-object">${Object.entries(value||{}).map(([key,item])=>`<div><dt>${esc(humanize(key))}</dt><dd>${typeof item==="object"?`<code>${esc(JSON.stringify(item))}</code>`:renderPrimitive(item)}</dd></div>`).join("")}</dl>`;
  const renderItems = (items,key) => {
    if(!items.length)return `<div class="structured-empty">Nothing recorded here.</div>`;
    if(key==="events")return `<div class="event-stack">${items.slice().reverse().map(item=>{const eventAt=eventTime(item), refs=eventRefs(item); return `<article class="structured-event"><div><span class="lane event">${esc(eventType(item))}</span><time title="${esc(eventAt)}">${esc(time(eventAt))}</time></div><p>${esc(eventSummary(item)||statementText(item)||"No narrative recorded.")}</p>${refs.length?`<div class="reference-row">${refs.map(ref=>`<code>${esc(ref)}</code>`).join("")}</div>`:""}</article>`;}).join("")}</div>`;
    return `<ol class="fact-list">${items.map((item,index)=>`<li><span>${String(index+1).padStart(2,"0")}</span><div>${typeof item==="object"?renderObject(item):`<p>${renderPrimitive(item)}</p>`}</div></li>`).join("")}</ol>`;
  };
  const renderStructured = doc => {
    const value=doc.structured;
    if(!value||typeof value!=="object")return `<div class="yaml-diagnostic error"><strong>YAML could not be modeled</strong><p>${esc(doc.yaml?.error||"The document does not contain a mapping or sequence.")}</p></div>`;
    if(Array.isArray(value))return renderItems(value,"items");
    const references=[];
    const sections=Object.entries(value).filter(([key])=>!['version','updated_at'].includes(key)).map(([key,item])=>{
      if(key.endsWith("_refs")){references.push(...(Array.isArray(item)?item:[]));return "";}
      const count=Array.isArray(item)?item.length:null;
      const content=Array.isArray(item)?renderItems(item,key):(item&&typeof item==="object"?renderObject(item):`<p class="fact-scalar">${renderPrimitive(item)}</p>`);
      return `<section class="fact-section"><header><div><p class="eyebrow">${esc(doc.title)}</p><h3>${esc(humanize(key))}</h3></div>${count!==null?`<span class="count">${full.format(count)}</span>`:""}</header>${content}</section>`;
    }).join("");
    return `${sections}${references.length?`<section class="fact-section references"><header><div><p class="eyebrow">Traceability</p><h3>Linked sources</h3></div><span class="count">${references.length}</span></header><div class="reference-row">${references.map(ref=>`<code>${esc(ref)}</code>`).join("")}</div></section>`:""}`;
  };
  const copyText = async (value,button) => {
    try { await navigator.clipboard.writeText(value); }
    catch { const area=document.createElement("textarea");area.value=value;area.style.position="fixed";area.style.opacity="0";document.body.append(area);area.select();document.execCommand("copy");area.remove(); }
    const prior=button.textContent;button.textContent="Copied";setTimeout(()=>button.textContent=prior,1200);
  };
  let selectedDocumentId="", documentFilter="all";
  const renderDocumentPanel = (doc,view="story") => {
    const isYaml=Boolean(doc.yaml), valid=doc.yaml?.valid;
    const updated=doc.structured?.updated_at||doc.generated_at;
    const story=isYaml?renderStructured(doc):doc.html;
    const content=view==="source"?`<pre class="source-code"><code>${esc(doc.raw)}</code></pre>`:view==="json"?`<pre class="source-code"><code>${esc(JSON.stringify(doc.structured,null,2))}</code></pre>`:story;
    $("#document-body").innerHTML=`<header class="document-hero"><div><p class="eyebrow">${esc(humanize(doc.kind||"source"))} · ${esc(doc.path)}</p><h2>${esc(doc.title)}</h2>${doc.description?`<p>${esc(doc.description)}</p>`:""}</div><div class="document-badges">${isYaml?`<span class="status ${valid?"valid":"invalid"}">${valid?"Valid YAML":"YAML issue"}</span>`:""}${updated?`<time title="${esc(updated)}">Updated ${esc(utc?updated:time(updated))}</time>`:""}</div></header>${isYaml&&!valid?`<div class="yaml-diagnostic error"><strong>Parser diagnostic</strong><p>${esc(doc.yaml.error)}</p><code>Line ${esc(doc.yaml.line||"?")}, column ${esc(doc.yaml.column||"?")}</code></div>`:isYaml?`<div class="yaml-diagnostic safe"><strong>${doc.yaml.normalization_changed?"Normalized repair available":"YAML structure verified"}</strong><p>Parsed with the pinned optional runtime. Copy a normalized version to repair formatting; the dashboard never changes canonical source files.</p></div>`:""}<div class="document-tabs" role="tablist"><button data-view="story" class="${view==="story"?"active":""}" type="button">Guided view</button>${isYaml?`<button data-view="json" class="${view==="json"?"active":""}" type="button">JSON</button>`:""}<button data-view="source" class="${view==="source"?"active":""}" type="button">Source</button>${isYaml&&valid?`<button class="copy-action" data-copy="yaml" type="button">Copy normalized YAML</button><button class="copy-action" data-copy="json" type="button">Copy JSON</button>`:""}</div><div class="document-content">${content}</div>`;
    $("#document-body").querySelectorAll("[data-view]").forEach(button=>button.addEventListener("click",()=>renderDocumentPanel(doc,button.dataset.view)));
    $("#document-body").querySelectorAll("[data-copy]").forEach(button=>button.addEventListener("click",()=>copyText(button.dataset.copy==="yaml"?doc.yaml.normalized:JSON.stringify(doc.structured,null,2),button)));
  };
  const renderDocuments = query => {
    const normalized=query.trim().toLowerCase();
    const matches=data.documents.filter(doc=>!doc.path.endsWith("TASK_TEMPLATE.md")&&(documentFilter==="all"||doc.kind===documentFilter)&&(!normalized||`${doc.title} ${doc.description} ${doc.path} ${(doc.tags||[]).join(" ")} ${doc.raw}`.toLowerCase().includes(normalized)));
    $("#document-list").innerHTML=matches.slice(0,150).map(doc=>`<button class="document-button ${doc.id===selectedDocumentId?"active":""}" data-id="${esc(doc.id)}"><span class="document-kind">${esc(humanize(doc.kind||"source"))}</span><strong>${esc(doc.title)}</strong><small>${esc(doc.path)}</small></button>`).join("")||`<div class="empty">No matching knowledge.</div>`;
    $("#document-list").querySelectorAll("button").forEach(button=>button.addEventListener("click",()=>selectDocument(button.dataset.id)));
  };
  function selectDocument(id){ const doc=data.documents.find(item=>item.id===id); if(!doc)return;selectedDocumentId=id;renderDocumentPanel(doc);renderDocuments($("#search").value); }
  $("#search").addEventListener("input",event=>renderDocuments(event.target.value));
  $("#document-filters").querySelectorAll("button").forEach(button=>button.addEventListener("click",()=>{$("#document-filters").querySelectorAll("button").forEach(item=>item.classList.toggle("active",item===button));documentFilter=button.dataset.filter;renderDocuments($("#search").value);}));
  renderDocuments(""); const startingDocument=data.documents.find(doc=>doc.path.endsWith("clineflow_last_session.yml"))||data.documents.find(doc=>doc.kind==="ledger")||data.documents[0];if(startingDocument)selectDocument(startingDocument.id);
  addEventListener("resize",()=>charts.forEach(chart=>chart.resize()));
  if(!matchMedia("(prefers-reduced-motion: reduce)").matches){gsap.from(".hero-main,.hero-side,.panel",{opacity:0,y:18,duration:.7,stagger:.045,ease:"power2.out"});}
})();
