(() => {
  "use strict";

  const presentation = JSON.parse(document.getElementById("clineflow-presentation").textContent);
  const $ = (selector, root = document) => root.querySelector(selector);
  const esc = (value = "") => String(value).replace(/[&<>"']/g, char => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[char]));
  const titleCase = value => String(value || "").replaceAll("_", " ").replace(/\b\w/g, letter => letter.toUpperCase());
  const date = value => value && Number.isFinite(new Date(value).getTime()) ? new Date(value) : null;
  const fullTime = value => date(value) ? `${date(value).toLocaleString(undefined, {timeZone:"UTC"})} UTC` : "Not recorded";
  const shortDate = value => date(value) ? new Intl.DateTimeFormat(undefined, {month:"short", day:"numeric", year:"numeric", timeZone:"UTC"}).format(date(value)) : "Undated";
  const dayNumber = value => date(value) ? new Intl.DateTimeFormat(undefined, {day:"2-digit", timeZone:"UTC"}).format(date(value)) : "—";
  const month = value => date(value) ? new Intl.DateTimeFormat(undefined, {month:"short", timeZone:"UTC"}).format(date(value)).toUpperCase() : "DATE";
  const iso = value => value ? String(value).replace("T", " ").replace(/\.\d+Z$/, "Z") : "Not captured";

  const docs = presentation.documents || [];
  const byId = new Map(docs.map(doc => [doc.id, doc]));
  const sourceButton = ids => (ids || []).find(id => byId.has(id));
  const narratives = presentation.narratives || {};
  const sparks = presentation.sparks || [];
  const sparkHarness = presentation.observations_harness || {};
  const workstreams = presentation.workspace?.workstreams || [];
  const commentary = presentation.workspace?.commentary || [];
  const reportHistory = presentation.workspace?.report_history || {};
  const decisionLenses = presentation.workspace?.decision_lenses || [];
  const onboarding = presentation.onboarding || {};
  const activity = presentation.activity || {};
  const evidence = presentation.evidence_register || {};
  const report = presentation.report || {};
  const reportOptions = report.selector || [];
  const blog = presentation.blog || {};
  const blogPublication = blog.publication || {};
  const latestBlogArticle = blog.latest_published || blog.current || {};
  const blogHasNothingNew = blogPublication.status === "nothing_new";
  const identity = presentation.identity || {};
  const project = identity.project || {};
  const coverage = identity.coverage || {};
  const revision = identity.revision || {};
  const condition = identity.condition || {};
  const journalCount = workstreams.reduce((count, stream) => count + (stream.journals || []).length, 0);

  const modal = document.createElement("dialog");
  modal.className = "reader-modal";
  modal.setAttribute("aria-labelledby", "reader-title");
  document.body.append(modal);
  let readerTrail = [];
  let readerFocus = null;
  let activeReader = null;

  const sourceIdsForEvent = event => (event.refs || []).map(ref => docs.find(doc => doc.path === ref)?.id).filter(Boolean);
  const sourceLabelForEvent = event => {
    const source = sourceIdsForEvent(event).map(id => byId.get(id)).find(Boolean);
    return source?.title || "Recorded source";
  };
  const sourceIdsForSpark = spark => [...(spark.origins || []), ...(spark.supporting || []), ...(spark.challenging || [])].map(ref => ref.source_id);
  const cleanEventText = value => String(value || "").replace(/^\d{4}-\d{2}-\d{2}\s*:\s*/, "").trim();
  const activityPreview = event => {
    const title = cleanEventText(event.title).replace(/…$/, "");
    const summary = cleanEventText(event.summary);
    return !summary || (title && summary.startsWith(title)) ? `Recorded in ${sourceLabelForEvent(event)}` : summary;
  };
  const recordPreview = (value, limit = 220) => {
    const text = String(value || "No detail recorded.").replace(/\s+/g, " ").trim();
    return text.length <= limit ? text : `${text.slice(0, limit).replace(/\s+\S*$/, "")}…`;
  };
  const ledgerRecordBody = record => {
    const highlights = record.highlights || [];
    const keyPoints = highlights.length ? `<ul class="record-highlights">${highlights.map(item => `<li>${esc(item)}</li>`).join("")}</ul>` : `<p>${esc(record.summary || "No compact key points are available for this record.")}</p>`;
    const timing = record.recorded_at ? `<p class="record-date-detail"><span>${esc(record.date_label || "Recorded")}</span> ${esc(fullTime(record.recorded_at))}</p>` : "";
    return `<section class="ledger-record-detail"><div><p class="kicker">${esc(record.kind || "RECORDED STATEMENT")}</p><strong>${esc(record.status || "Recorded")}</strong>${timing}</div><div><p class="kicker">KEY POINTS</p>${keyPoints}</div></section><details class="record-full"><summary>Read full recorded statement</summary><p>${esc(record.detail || "No detail recorded.")}</p></details><details><summary>Inspect source fragment</summary><pre>${esc(JSON.stringify(record.raw || record, null, 2))}</pre></details>`;
  };

  const renderReader = reader => {
    activeReader = reader;
    const sources = (reader.ids || []).map(id => byId.get(id)).filter(Boolean);
    modal.innerHTML = `<header class="reader-head"><div>${readerTrail.length ? `<button type="button" class="reader-back" aria-label="Back to previous reader">← Back</button>` : ""}<p class="kicker">${esc(reader.kicker || "PROJECT RECORD")}</p></div><form method="dialog"><button class="modal-close" aria-label="Close reader">×</button></form></header><h2 id="reader-title" tabindex="-1">${esc(reader.title)}</h2><div class="modal-copy">${reader.body}</div>${sources.length ? `<footer><p class="kicker">SOURCE RECORDS</p>${sources.map(doc => `<button type="button" class="source-link" data-source="${esc(doc.id)}"><strong>${esc(doc.title)}</strong><span>${esc(doc.path)}</span></button>`).join("")}</footer>` : ""}`;
    $(".reader-back", modal)?.addEventListener("click", () => renderReader(readerTrail.pop()));
    modal.querySelectorAll("[data-source]").forEach(button => button.addEventListener("click", () => {
      const doc = byId.get(button.dataset.source);
      if (!doc) return;
      readerTrail.push(activeReader);
      openDocument(doc, reader.locators?.[doc.id]);
    }));
    modal.querySelectorAll("[data-ledger-record]").forEach(button => button.addEventListener("click", () => {
      const record = JSON.parse(button.dataset.ledgerRecord);
      readerTrail.push(activeReader);
      renderReader({title: record.title || "Ledger record", kicker: "LEDGER RECORD", body: ledgerRecordBody(record), ids: reader.ids || []});
    }));
    modal.querySelectorAll("[data-item]").forEach(button => button.addEventListener("click", () => {
      readerTrail.push(activeReader);
      renderReader(itemReader(JSON.parse(button.dataset.item)));
    }));
    modal.querySelectorAll(".rich-text a").forEach(link => {
      const href = link.getAttribute("href") || "";
      if (/^https?:/i.test(href)) { link.target = "_blank"; link.rel = "noopener noreferrer"; return; }
      if (/^mailto:/i.test(href)) return;
      link.addEventListener("click", event => {
        event.preventDefault();
        const path = new URL(href, `https://snapshot.invalid/${reader.path || ""}`).pathname.slice(1);
        const source = docs.find(doc => doc.path === decodeURIComponent(path));
        readerTrail.push(activeReader);
        if (source) openDocument(source);
        else renderReader({title:"Reference outside this snapshot", kicker:"SOURCE AVAILABILITY", body:`<p>This reference was not included in the frozen report. Open it in the original project.</p><pre>${esc(href)}</pre>`, ids:[]});
      });
    });
    if (!modal.open) modal.showModal();
    modal.scrollTop = 0;
    $("#reader-title", modal).focus({preventScroll:true});
  };
  const openModal = (title, body, ids = [], kicker, locators = {}) => {
    readerFocus = document.activeElement;
    readerTrail = [];
    renderReader({title, body, ids, kicker, locators});
  };
  const openDocument = (doc, sectionLabel = "") => {
    const guided = doc.guided || {};
    const sections = (guided.sections || []).map((section, index) => {
      const content = section.type === "list" ? `<ul>${(section.items || []).map(item => `<li><strong>${esc(item.title || item.label || "Recorded item")}</strong><p>${esc(item.detail || item.summary || "")}</p></li>`).join("")}</ul>` : section.type === "fields" ? `<dl>${(section.items || []).map(item => `<div><dt>${esc(item.label)}</dt><dd>${esc(item.detail || item.value)}</dd></div>`).join("")}</dl>` : section.type === "markdown" ? `<div class="rich-text">${section.html || ""}</div>` : `<p>${esc(section.detail || section.value || "")}</p>`;
      const expanded = sectionLabel ? section.label.toLowerCase() === sectionLabel.replace(/^#+\s*/, "").toLowerCase() : index === 0;
      return `<details class="reader-section"${expanded ? " open" : ""}><summary>${esc(section.label)}</summary><section>${content}</section></details>`;
    }).join("");
    const records = guided.ledger_records || [];
    const ledgerMeta = (guided.ledger_meta || []).length ? `<dl class="ledger-meta">${guided.ledger_meta.map(item => `<div><dt>${esc(item.label)}</dt><dd>${esc(item.value)}</dd></div>`).join("")}</dl>` : "";
    const visibleRecords = records.slice(0, 6);
    const hiddenRecords = records.slice(6);
    const recordButton = record => `<button type="button" class="ledger-record" data-ledger-record='${esc(JSON.stringify(record))}'><span class="state-chip ${String(record.status || "recorded").toLowerCase()}">${esc(record.status || "Recorded")}</span><strong>${esc(record.title || "Ledger record")}</strong><p>${esc(recordPreview(record.summary))}</p><em>Read record →</em></button>`;
    const ledgerCatalogue = records.length ? `<section class="ledger-catalogue"><header><div><p class="kicker">RECORDED KNOWLEDGE</p><h3>${records.length} record${records.length === 1 ? "" : "s"}</h3></div><p>Open a named record for its full decision context.</p></header><div class="ledger-records">${visibleRecords.map(recordButton).join("")}</div>${hiddenRecords.length ? `<details class="ledger-more"><summary>Show ${hiddenRecords.length} more records</summary><div class="ledger-records">${hiddenRecords.map(recordButton).join("")}</div></details>` : ""}</section>` : "";
    renderReader({title: doc.title, path:doc.path, kicker: doc.kind === "journal" ? "JOURNAL" : "REFERENCE", body: `<p class="modal-summary">${esc(guided.summary || doc.description || "Canonical record")}</p>${ledgerMeta}${sections}${ledgerCatalogue}<details><summary>Source file · ${esc(doc.path)}</summary><pre>${esc(doc.yaml?.normalized || doc.raw || "No normalized source available.")}</pre></details>`, ids: []});
  };
  modal.addEventListener("close", () => {
    readerTrail = [];
    activeReader = null;
    readerFocus?.focus?.();
  });
  modal.addEventListener("click", event => {
    if (event.target !== modal) return;
    const box = modal.getBoundingClientRect();
    if (event.clientX < box.left || event.clientX > box.right || event.clientY < box.top || event.clientY > box.bottom) modal.close();
  });

  const setTab = (tab, navigate = false) => {
    const target = ["workspace", "sparks", "activity", "evidence", "onboarding", "blog"].includes(tab) ? tab : "workspace";
    document.querySelectorAll("[data-tab]").forEach(button => {
      const selected = button.dataset.tab === target;
      button.classList.toggle("active", selected);
      button.setAttribute("aria-selected", String(selected));
      button.tabIndex = selected ? 0 : -1;
      button.id = `tab-${button.dataset.tab}`;
      button.setAttribute("aria-controls", `${button.dataset.tab}-panel`);
    });
    document.querySelectorAll(".tab-panel").forEach(panel => {
      panel.hidden = panel.id !== `${target}-panel`;
      panel.setAttribute("aria-labelledby", `tab-${panel.id.replace("-panel", "")}`);
    });
    if (navigate && location.hash !== `#${target}`) history.pushState(null, "", `#${target}`);
  };
  const briefCard = (key, tone) => {
    const item = narratives[key] || {};
    return `<article class="narrative-card ${tone}"><p class="kicker">${esc(item.title || titleCase(key))}</p><p>${esc(item.text || "No source-bound narrative is available.")}</p>${sourceButton(item.source_ids) ? `<button data-record="${esc(sourceButton(item.source_ids))}" type="button">Read source</button>` : ""}</article>`;
  };
  const quietValue = (value, fallback) => value || fallback;
  // Inline Material-style SVGs retain the offline, single-file report boundary.
  // They are intentionally limited to wayfinding and high-value actions.
  const iconPaths = {
    article: "M5 3h10a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2m2 4v2h6V7H7m0 4v2h8v-2H7m0 4v2h8v-2H7Z",
    dashboard: "M3 3h8v8H3V3m10 0h8v5h-8V3M3 13h8v8H3v-8m10-3h8v11h-8V10Z",
    auto_awesome: "m19 9-1.25-2.75L15 5l2.75-1.25L19 1l1.25 2.75L23 5l-2.75 1.25L19 9M9 11l-2.25-4.75L2 4l4.75-2.25L9-3l2.25 4.75L16 4l-4.75 2.25L9 11m10 11-2.5-5.5L11 14l5.5-2.5L19 6l2.5 5.5L27 14l-5.5 2.5L19 22M4 22l-1.5-3.5L-1 17l3.5-1.5L4 12l1.5 3.5L9 17l-3.5 1.5L4 22Z",
    timeline: "M7 5h2v4h6V7l4 4-4 4v-2H7V5m10 14H7v-4h2v2h8v-4h2v4a2 2 0 0 1-2 2Z",
    fact_check: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6m0 2.5L17.5 8H14V4.5M7 12l2 2 4-4 1.4 1.4L9 16l-3.4-3.4L7 12m0 6l2 2 4-4 1.4 1.4L9 22l-3.4-3.4L7 18Z",
    school: "m12 3 10 5-10 5L2 8l10-5m-6 9.2 6 3 6-3V17c0 1.7-2.7 3-6 3s-6-1.3-6-3v-4.8Z",
    feed: "M4 4h16v2H4V4m0 7h16v2H4v-2m0 7h11v2H4v-2Z",
    search: "M9.5 3a6.5 6.5 0 1 1 0 13 6.5 6.5 0 0 1 0-13m0 2a4.5 4.5 0 1 0 0 9 4.5 4.5 0 0 0 0-9m7.7 10.8L22 20.6 20.6 22l-4.8-4.7 1.4-1.5Z",
    picture_as_pdf: "M19 2H8c-1.1 0-2 .9-2 2v16c0 1.1.9 2 2 2h8l5-5V4c0-1.1-.9-2-2-2m-1 15h-3v3H9v-3H7v-2h2v-2h6v2h3v2m1-9h-5V4l5 4Z",
    dark_mode: "M12 3c.13 0 .26 0 .39.01A7 7 0 0 0 19 13.4 7 7 0 0 1 12 21a9 9 0 0 1 0-18Z",
    arrow_outward: "M5 5h9.59L3 16.59 4.41 18 16 6.41V16h2V3H5v2Z",
  };
  const icon = (name, label = "") => `<svg class="mui-icon" viewBox="0 0 24 24"${label ? ' role="img" aria-label="' + esc(label) + '"' : ' aria-hidden="true"'} focusable="false"><path d="${iconPaths[name] || iconPaths.article}"/></svg>`;
  const recordLink = ids => sourceButton(ids) ? `<button type="button" data-record="${esc(sourceButton(ids))}">Open record</button>` : "";
  const onboardingStep = item => `<article class="onboarding-step"><div><span>${esc(item.step || "—")}</span><h4>${esc(item.title || "Read a record")}</h4></div>${item.points?.length ? `<ul class="onboarding-points">${item.points.map(point => `<li>${esc(point)}</li>`).join("")}</ul>` : `<p class="onboarding-answer">${esc(item.answer || "Open the source to read this part of the project.")}</p>`}<footer>${recordLink(item.source_ids)}</footer><details><summary>Go deeper with your project assistant</summary><p>${esc(item.question || "")}</p><button type="button" class="copy-prompt" data-copy="${esc(item.prompt || item.question || "")}">Copy question</button></details></article>`;
  const journalButtons = workstreams.flatMap(stream => (stream.journals || []).map(journal => `<button type="button" class="source-queue-item" data-record="${esc(journal.id)}"><span>${esc(titleCase(stream.topic))}</span><strong>${esc(journal.title)}</strong><em>${esc(journal.status || "recorded")}</em></button>`));
  const lensCard = item => `<article class="lens-card"><p class="kicker">${esc(item.label || titleCase(item.category || "signal"))}</p><strong>${esc(item.value || "Not recorded")}</strong><p>${esc(item.text || "No source-bound interpretation is available.")}</p>${recordLink(item.source_ids)}</article>`;
  const decisionLensesMarkup = decisionLenses.length ? `<section class="decision-lenses" aria-labelledby="decision-lenses-title"><header><div><p class="kicker">DECISION LENSES</p><h3 id="decision-lenses-title">One record, three useful perspectives</h3></div><p>Team, recorded calendar coverage, and a non-financial return proxy. No headcount, money, or realized ROI is inferred.</p></header><div class="lens-tabs" role="tablist" aria-label="Decision lens">${decisionLenses.map((lens, index) => `<button type="button" role="tab" data-lens="${esc(lens.id)}" aria-controls="lens-${esc(lens.id)}" aria-selected="${index === 0}">${esc(lens.label || "Decision lens")}</button>`).join("")}</div><div class="lens-panels">${decisionLenses.map((lens, index) => `<section id="lens-${esc(lens.id)}" class="lens-panel" role="tabpanel" data-lens-panel="${esc(lens.id)}"${index ? " hidden" : ""}><header><h4>${esc(lens.label || "Decision lens")}</h4><p>${esc(lens.description || "Read source-bound signals for this decision context.")}</p></header><div class="lens-grid">${(lens.insights || []).map(lensCard).join("")}</div></section>`).join("")}</div></section>` : "";
  const followUps = presentation.now?.follow_ups || [];
  const attention = presentation.unresolved || [];
  const itemButton = item => `<button type="button" class="reading-row" data-item='${esc(JSON.stringify(item))}'><span class="state-chip">${esc(item.status || item.kind || "Record")}</span><span class="reading-copy"><strong>${esc(item.title)}</strong><p>${esc(recordPreview(item.detail || item.summary, 180))}</p></span>${item.recorded_at ? `<time class="record-date" datetime="${esc(item.recorded_at)}">${esc(item.date_label || "Recorded")} · ${esc(shortDate(item.recorded_at))}</time>` : ""}<span class="row-arrow" aria-hidden="true">${icon("arrow_outward")}</span></button>`;
  const ledgerStrip = `<div class="ledger-strip">${(presentation.workspace?.ledgers || []).map(ledger => `<button type="button" class="ledger-card" data-record="${esc(ledger.id)}"><span>${esc(ledger.title)}</span><small>${esc((byId.get(ledger.id)?.guided?.ledger_records || []).length)} entries</small><b>Browse →</b></button>`).join("")}</div>`;

  const app = $("#app");
  app.innerHTML = `<main class="report-shell" id="main">
    <header class="masthead"><a class="wordmark" href="#workspace">CLINEFLOW <span>Knowledge Visor</span></a><div class="report-meta"><label class="report-switcher"><span>FROZEN REPORT</span><select id="report-selector" aria-label="Choose a frozen report">${reportOptions.map(item => `<option value="${esc(item.href || "index.html")}"${item.current ? " selected" : ""}>${esc(item.current ? `Current · ${iso(item.generated_at)}` : iso(item.generated_at))} · ${esc(item.run_id || "Report")}</option>`).join("") || `<option selected>Current · ${esc(iso(presentation.generated_at))}</option>`}</select></label><button id="open-search" type="button">${icon("search")}<span>Find records</span></button><button id="theme-toggle" type="button">${icon("dark_mode")}<span>Dark reader</span></button></div></header>
    <section class="project-header"><div><p class="kicker">SOURCE-BOUND PROJECT RECORD</p><h1>${esc(project.title || "Project record")}</h1><p>${esc(project.description || "A read-only record of project context, development, learning, and evidence.")}</p></div><dl class="project-stats"><div><dt>Coverage</dt><dd>${esc(shortDate(coverage.from))} — ${esc(shortDate(coverage.to))}</dd></div><div><dt>Snapshot</dt><dd>${esc(revision.short || "Not captured")}</dd></div><div><dt>Condition</dt><dd>${esc(condition.label || "Not captured")}</dd></div></dl></section>
    <section class="quick-find" id="quick-find" hidden><label for="record-search">Find a journal, source, or event</label><div><input id="record-search" type="search" autocomplete="off" placeholder="Search this report"><button id="close-search" type="button">Close</button></div><div id="search-results" class="search-results" aria-live="polite"></div></section>
    <nav class="tabbar" aria-label="Knowledge report views" role="tablist"><button data-tab="workspace" class="active" type="button" role="tab" aria-selected="true">${icon("dashboard")}<span>Workspace</span></button><button data-tab="sparks" type="button" role="tab" aria-selected="false">${icon("auto_awesome")}<span>Sparks</span></button><button data-tab="activity" type="button" role="tab" aria-selected="false">${icon("timeline")}<span>Activity</span></button><button data-tab="evidence" type="button" role="tab" aria-selected="false">${icon("fact_check")}<span>Evidence</span></button><button data-tab="onboarding" type="button" role="tab" aria-selected="false">${icon("school")}<span>Learning</span></button><button data-tab="blog" type="button" role="tab" aria-selected="false">${icon("feed")}<span>Blog</span></button></nav>
    <section id="workspace-panel" class="tab-panel" role="tabpanel">
      <header class="section-intro"><div><p class="kicker">PROJECT BRIEF</p><h2>Pick up where the project left off.</h2></div><p>A snapshot of the latest change, recorded follow-ups, and the journals behind them.</p></header>
      <section class="brief-layout">
        <article class="project-brief"><div class="brief-label"><span class="status-dot"></span><p class="kicker">LATEST RECORDED CHANGE</p><time>${esc(shortDate(coverage.to))}</time></div><h3>${esc(presentation.now?.latest_change || presentation.now?.summary || "No recent change recorded.")}</h3>${presentation.now?.intent ? `<p class="brief-intent"><strong>Objective</strong> ${esc(presentation.now.intent)}</p>` : ""}<footer>${recordLink(presentation.now?.source_ids)}<a href="#activity">Explore activity →</a></footer></article>
        <aside class="next-step"><p class="kicker">WHERE TO GO NEXT</p><h3>${esc(presentation.now?.next_move || "Review the recorded follow-ups.")}</h3><p>${followUps.length} follow-up records · ${attention.length} open or conflicting entries</p><button type="button" id="open-follow-ups">Review follow-ups <span aria-hidden="true">→</span></button><a href="#onboarding">New to the project? Start here →</a></aside>
      </section>
      <div class="brief-metrics"><span><strong>${journalCount}</strong> journals</span><span><strong>${(activity.events || []).length}</strong> recorded events</span><span><strong>${(evidence.verification || []).length}</strong> verification entries</span><a href="#evidence">Browse the evidence →</a></div>
      <details class="secondary-section report-history"><summary><span>Report chronology</span><small>${esc(reportHistory.mode === "comparison" ? "Compared with the preceding dashboard" : "First dashboard baseline")}</small></summary><p class="method-note">${esc(reportHistory.summary || "No report-history comparison is available.")}</p><section class="commentary-grid" aria-label="Report chronology commentary">${(reportHistory.cards || []).map(item => `<article class="commentary-card"><p class="kicker">${esc(item.label)}</p><strong>${esc(item.value)}</strong><p>${esc(item.text)}</p>${recordLink(item.source_ids)}</article>`).join("")}</section></details>
      <section class="content-section"><header class="section-label"><div><p class="kicker">PROJECT MEMORY</p><h3>Journals & workstreams</h3></div><label class="journal-filter"><span class="sr-only">Filter journals</span><input id="journal-search" type="search" placeholder="Find a journal…"></label></header><div class="journal-library">${workstreams.flatMap(stream => stream.journals.map(journal => `<button type="button" class="journal-row" data-journal data-record="${esc(journal.id)}"><span class="journal-icon" aria-hidden="true">${icon("article")}</span><span class="journal-copy"><small>${esc(titleCase(stream.topic))}</small><strong>${esc(journal.title)}</strong><p>${esc(journal.description || "Open journal to explore its decisions and evidence.")}</p></span><span class="journal-meta"><time>${esc(shortDate(journal.generated_at))}</time><span class="state-chip">${esc(journal.status || "recorded")}</span></span><span class="row-arrow" aria-hidden="true">${icon("arrow_outward")}</span></button>`)).join("") || '<p class="empty">No journals in this snapshot.</p>'}</div><p id="journal-empty" class="empty" hidden>No journals match. Try another term.</p></section>
      <details class="secondary-section"><summary><span>Project signals & role perspectives</span><small>Recorded activity, team, time and return</small></summary><section class="commentary-grid" aria-label="Project commentary">${commentary.map(item => `<article class="commentary-card"><p class="kicker">${esc(item.label)}</p><strong>${esc(item.value)}</strong><p>${esc(item.text)}</p>${recordLink(item.source_ids)}</article>`).join("")}</section>${decisionLensesMarkup}</details>
      <details class="secondary-section"><summary><span>Reference ledgers</span><small>Goals, specifications, verification & history</small></summary>${ledgerStrip}</details>
    </section>
    <section id="onboarding-panel" class="tab-panel" role="tabpanel" hidden>
      <header class="section-intro"><div><p class="kicker">PROJECT ONBOARDING</p><h2>${esc(onboarding.title || "Learn this project from its record")}</h2></div><p>${esc(onboarding.text || "Read a source, then ask a focused question.")}</p></header>
      <section class="orientation-grid" aria-label="Project orientation"><section class="onboarding-card"><header><div><p class="kicker">SOURCE ROUTE</p><h3>Start with the record, not a guess</h3></div><p>Each step opens its source and offers a question you can take into a project assistant.</p></header><div class="onboarding-steps">${(onboarding.steps || []).map(onboardingStep).join("") || "<p class=\"empty\">No orientation route is available for this report.</p>"}</div></section></section>
    </section>
    <section id="sparks-panel" class="tab-panel" role="tabpanel" hidden>
      <header class="section-intro"><div><p class="kicker">SPARKS</p><h2>Decisions worth carrying forward.</h2></div><p>Lessons and decisions drawn from project journals. Read the context before reusing them.</p></header>
      <div class="spark-toolbar"><span><strong>${sparks.length}</strong> project notes</span><label><span class="sr-only">Find a Spark</span><input id="spark-search" type="search" placeholder="Search learnings…"></label></div>
      <div class="spark-grid">${sparks.map((spark, index) => `<article class="spark-card" data-spark-card><div class="spark-topline"><span class="spark-number">${String(index + 1).padStart(2, "0")}</span><span class="state-chip ${esc(spark.state)}">${esc(spark.basis === "recorded_decision" ? "Recorded decision" : spark.basis === "source_excerpt" ? "Source excerpt" : titleCase(spark.state))}</span></div><h3>${esc(spark.title)}</h3><p>${esc(spark.learning)}</p><footer><span>${esc(spark.source_title || spark.scope)}</span><button type="button" data-spark-index="${index}">Read context →</button></footer></article>`).join("") || '<p class="empty">No source material is available to derive a project learning yet.</p>'}</div>
      <p id="spark-empty" class="empty" hidden>No learnings match this search.</p>
      <details class="secondary-section"><summary><span>How this learning changed</span><small>Comparison with the preceding report</small></summary><section class="spark-reconciliation"><strong>This run</strong><dl><div><dt>New</dt><dd>${esc(sparkHarness.reconciliation?.new || 0)}</dd></div><div><dt>Unchanged</dt><dd>${esc(sparkHarness.reconciliation?.unchanged || 0)}</dd></div><div><dt>Revised</dt><dd>${esc(sparkHarness.reconciliation?.revised || 0)}</dd></div><div><dt>Retired</dt><dd>${esc(sparkHarness.reconciliation?.retired || 0)}</dd></div></dl></section><p class="method-note">An unchanged note has the same recorded basis; repeating a run adds no evidence. Extracted decisions remain specific to their source.</p>${(sparkHarness.reconciliation?.retired_items || []).map(item => `<p>${esc(item.title)} — ${esc(item.reason)}</p>`).join("")}</details>
    </section>
    <section id="activity-panel" class="tab-panel" role="tabpanel" hidden>
      <header class="section-intro"><div><p class="kicker">DEVELOPMENT RECORD</p><h2>See how the project evolved.</h2></div><p>Latest entries first, grouped by day. Narrow the story to a journal or search for a decision.</p></header>
      <div class="filters activity-filters"><label>Type<select id="activity-type"><option value="">All types</option>${(activity.types || []).map(value => `<option value="${esc(value)}">${esc(titleCase(value))}</option>`).join("")}</select></label><label>Journal<select id="activity-journal"><option value="">All journals</option>${docs.filter(doc => doc.kind === "journal").map(doc => `<option value="${esc(doc.path)}">${esc(doc.title)}</option>`).join("")}</select></label><label class="filter-search">Find<input id="activity-search" type="search" placeholder="Search activity"></label><button id="activity-reset" type="button">Reset</button><output id="activity-count" aria-live="polite"></output></div>
      <div class="activity-list" id="activity-list"></div>
    </section>
    <section id="evidence-panel" class="tab-panel" role="tabpanel" hidden>
      <header class="section-intro"><div><p class="kicker">EVIDENCE</p><h2>Check what the project actually records.</h2></div><p>Browse verification, decisions, and open questions. Every entry opens its recorded detail and source.</p></header>
      <div class="filters evidence-filters"><label>Category<select id="evidence-type"><option value="">All records</option><option value="verification">Verification</option><option value="decisions">Decisions & questions</option><option value="relationships">Relationships</option></select></label><label class="filter-search">Find<input id="evidence-search" type="search" placeholder="Search evidence"></label><output id="evidence-count" aria-live="polite"></output></div>
      <div id="evidence-list" class="reading-list"></div><button id="evidence-more" class="load-more" type="button" hidden>Show more records</button>
      <details class="secondary-section"><summary><span>Project story</span><small>Origins, overall direction & recent developments</small></summary><div class="narrative-grid">${briefCard("origin", "origin")}${briefCard("overall", "overall")}${briefCard("recent", "recent")}${briefCard("digest", "digest")}</div></details>
      <details class="secondary-section"><summary><span>Browse source ledgers</span><small>The underlying project records</small></summary>${ledgerStrip}</details>
      <section class="evidence-method"><p class="kicker">REPORT METHOD</p><p>Every entry above remains source-bound and can be opened with its recorded detail and original source. The dashboard intentionally does not turn these records into a generated report artifact.</p><button id="provenance" type="button">About this report</button></section>
    </section>
    <section id="blog-panel" class="tab-panel" role="tabpanel" hidden>
      <header class="section-intro"><div><p class="kicker">ENGINEERING BLOG</p><h2>An engineering notebook, written from the work.</h2></div><p>Each changed frozen source bundle becomes one first-person post with its own permanent local URL.</p></header>
      <section class="blog-feature"><div><p class="kicker">${blogHasNothingNew ? "NO NEW NOTE" : "PUBLISHED THIS REPORT"}</p><h3>${esc(blogHasNothingNew ? "Nothing new to publish." : blog.current?.title || "No engineering note is available yet.")}</h3><p>${esc(blogHasNothingNew ? "This report matches the frozen source behind the last engineering note. It did not create or rewrite an article." : blog.current?.dek || "Generate a report to publish an engineering note from its structured source record.")}</p>${latestBlogArticle?.title ? `<dl><div><dt>${blogHasNothingNew ? "Last technical topic" : "Technical topic"}</dt><dd>${esc(latestBlogArticle.technical_topic || "Not recorded")}</dd></div><div><dt>Last published</dt><dd>${esc(shortDate(latestBlogArticle.generated_at))}</dd></div></dl>` : ""}<div class="artifact-actions">${latestBlogArticle?.url ? `<a href="${esc(latestBlogArticle.url)}" target="_blank" rel="noopener">${blogHasNothingNew ? "Read last post ↗" : "Read post ↗"}</a>` : ""}${latestBlogArticle?.json_url ? `<a href="${esc(latestBlogArticle.json_url)}" target="_blank" rel="noopener">Article JSON ↗</a>` : ""}${blog.archive_url ? `<a href="${esc(blog.archive_url)}" target="_blank" rel="noopener">Notebook ↗</a>` : ""}${blog.index_json ? `<a href="${esc(blog.index_json)}" target="_blank" rel="noopener">Archive JSON ↗</a>` : ""}</div></div><aside><p class="kicker">PUBLISHING SURFACE</p><strong>${(blog.articles || []).length} durable engineering note${(blog.articles || []).length === 1 ? "" : "s"}</strong><p>${blog.public_archive_url ? `Public archive configured at ${esc(blog.public_archive_url)}.` : "Local archive is ready. Set CLINEFLOW_DASHBOARD_PUBLIC_BASE_URL when deploying to emit crawlable robots.txt and sitemap.xml with your real domain."}</p></aside></section>
      <section class="blog-archive" aria-label="Release article archive">${(blog.articles || []).map(item => `<div><a href="${esc(item.url)}" target="_blank" rel="noopener"><time>${esc(shortDate(item.generated_at))}</time><span><strong>${esc(item.title)}</strong><small>${esc(item.technical_topic || "Technical record")}</small></span><span aria-hidden="true">↗</span></a><a class="blog-json-link" href="${esc(item.json_url || "")}" target="_blank" rel="noopener">JSON</a></div>`).join("") || '<p class="empty">No published release notes are available yet.</p>'}</section>
    </section>
    <footer class="report-footer">Frozen locally · ${esc(report.run_id || "")} · no browser network access</footer>
  </main>`;

  const attachRecordButtons = root => root.querySelectorAll("[data-record]").forEach(button => button.addEventListener("click", () => {
    const doc = byId.get(button.dataset.record);
    if (!doc) return;
    readerFocus = document.activeElement;
    readerTrail = [];
    openDocument(doc);
  }));
  attachRecordButtons(app);
  const reportSelector = $("#report-selector", app);
  reportSelector?.addEventListener("change", () => {
    if (reportSelector.value) window.location.assign(reportSelector.value);
  });
  const selectLens = id => {
    app.querySelectorAll("[data-lens]").forEach(button => {
      const selected = button.dataset.lens === id;
      button.classList.toggle("active", selected);
      button.setAttribute("aria-selected", String(selected));
    });
    app.querySelectorAll("[data-lens-panel]").forEach(panel => panel.hidden = panel.dataset.lensPanel !== id);
  };
  app.querySelectorAll("[data-lens]").forEach(button => button.addEventListener("click", () => selectLens(button.dataset.lens)));
  const copyPrompt = async button => {
    const value = button.dataset.copy || "";
    if (!value) return;
    const restore = () => window.setTimeout(() => { button.textContent = "Copy question"; }, 1500);
    let copied = false;
    try {
      await navigator.clipboard.writeText(value);
      copied = true;
    } catch (_) {
      const input = document.createElement("textarea");
      input.value = value;
      input.setAttribute("readonly", "");
      input.style.position = "fixed";
      input.style.opacity = "0";
      document.body.append(input);
      input.select();
      try { copied = document.execCommand("copy"); } catch (_) { copied = false; }
      input.remove();
    }
    button.textContent = copied ? "Copied" : "Copy unavailable";
    if (!copied) openModal("Copy this question", `<p>Select and copy the question below.</p><textarea class="manual-copy" readonly aria-label="Question to copy">${esc(value)}</textarea>`, [], "PROJECT ASSISTANT");
    restore();
  };
  app.querySelectorAll(".copy-prompt").forEach(button => button.addEventListener("click", () => copyPrompt(button)));
  app.querySelectorAll("[data-tab]").forEach(button => button.addEventListener("click", () => setTab(button.dataset.tab, true)));
  const wireTabKeys = (selector, select, key) => {
    const buttons = [...app.querySelectorAll(selector)];
    buttons.forEach((button, index) => button.addEventListener("keydown", event => {
      if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
      event.preventDefault();
      const next = event.key === "Home" ? 0 : event.key === "End" ? buttons.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + buttons.length) % buttons.length;
      select(buttons[next].dataset[key]); buttons[next].focus();
    }));
  };
  wireTabKeys("[data-tab]", id => setTab(id, true), "tab");
  wireTabKeys("[data-lens]", selectLens, "lens");
  const applyTheme = dark => {
    document.documentElement.classList.toggle("dark", dark);
    $("#theme-toggle").textContent = dark ? "Light reader" : "Dark reader";
    $("#theme-toggle").setAttribute("aria-pressed", String(dark));
  };
  try { applyTheme(localStorage.getItem("clineflow-reader-theme") === "dark"); } catch (_) { applyTheme(false); }
  $("#theme-toggle").addEventListener("click", event => {
    const dark = !document.documentElement.classList.contains("dark");
    applyTheme(dark);
    try { localStorage.setItem("clineflow-reader-theme", dark ? "dark" : "light"); } catch (_) { /* A blocked preference never blocks reading. */ }
  });

  $("#journal-search").addEventListener("input", event => {
    const query = event.target.value.trim().toLowerCase();
    const rows = [...app.querySelectorAll("[data-journal]")];
    rows.forEach(row => row.hidden = !`${row.textContent} ${byId.get(row.dataset.record)?.raw || ""}`.toLowerCase().includes(query));
    $("#journal-empty").hidden = rows.some(row => !row.hidden);
  });
  $("#spark-search").addEventListener("input", event => {
    const query = event.target.value.trim().toLowerCase();
    const cards = [...app.querySelectorAll("[data-spark-card]")];
    cards.forEach(card => card.hidden = !card.textContent.toLowerCase().includes(query));
    $("#spark-empty").hidden = cards.some(card => !card.hidden);
  });

  const expandedActivityDays = new Set();
  const renderActivity = () => {
    const type = $("#activity-type").value;
    const query = $("#activity-search").value.trim().toLowerCase();
    const journal = $("#activity-journal").value;
    const selected = (activity.events || []).filter(event => (!type || event.type === type) && (!journal || (event.refs || []).includes(journal)) && (!query || `${event.title} ${event.summary} ${sourceLabelForEvent(event)}`.toLowerCase().includes(query))).sort((a, b) => String(b.at || "").localeCompare(String(a.at || "")));
    $("#activity-count").textContent = `${selected.length} record${selected.length === 1 ? "" : "s"}`;
    const groups = new Map();
    selected.forEach(event => {
      const label = shortDate(event.at);
      groups.set(label, [...(groups.get(label) || []), event]);
    });
    $("#activity-list").innerHTML = [...groups.entries()].map(([label, events], index) => {
      const expanded = expandedActivityDays.has(label);
      const visible = expanded ? events : events.slice(0, 4);
      const rows = visible.map(event => `<button type="button" class="activity-row" data-event='${esc(JSON.stringify(event))}'><time aria-label="${esc(fullTime(event.at))}"><b>${esc(dayNumber(event.at))}</b><span>${esc(month(event.at))}</span></time><span class="event-kind">${esc(titleCase(event.type || "event"))}</span><span class="activity-copy"><strong>${esc(cleanEventText(event.title) || "Recorded event")}</strong><p>${esc(activityPreview(event))}</p></span><span class="activity-source">${esc(sourceLabelForEvent(event))}</span><span class="activity-open" aria-hidden="true">↗</span></button>`).join("");
      const disclosure = events.length > 4 ? `<button type="button" class="day-more" data-day="${index}">${expanded ? "Show fewer records" : `Show ${events.length - 4} more records`}</button>` : "";
      return `<section class="activity-day"><h3>${esc(label)} <span>${events.length} record${events.length === 1 ? "" : "s"}</span></h3><div>${rows}${disclosure}</div></section>`;
    }).join("") || "<section class=\"empty compact-empty\"><strong>No activity matches these filters.</strong><p>Clear a filter or search for another recorded term.</p></section>";
    $("#activity-list").querySelectorAll("[data-event]").forEach(button => button.addEventListener("click", () => {
      const event = JSON.parse(button.dataset.event);
      openModal(event.title || "Recorded event", `<p class="modal-summary">${esc(event.summary || "No summary recorded.")}</p><dl><div><dt>When</dt><dd>${esc(fullTime(event.at))}</dd></div><div><dt>Type</dt><dd>${esc(titleCase(event.type || "event"))}</dd></div><div><dt>Recorded by</dt><dd>${esc(event.actor || "Not recorded")}</dd></div></dl><details><summary>Inspect normalized event</summary><pre>${esc(JSON.stringify(event.raw || event, null, 2))}</pre></details>`, sourceIdsForEvent(event), "ACTIVITY RECORD");
    }));
    $("#activity-list").querySelectorAll("[data-day]").forEach(button => button.addEventListener("click", () => {
      const label = [...groups.keys()][Number(button.dataset.day)];
      expandedActivityDays.has(label) ? expandedActivityDays.delete(label) : expandedActivityDays.add(label);
      renderActivity();
    }));
  };
  ["#activity-type", "#activity-search", "#activity-journal"].forEach(selector => $(selector).addEventListener("input", renderActivity));
  $("#activity-reset").addEventListener("click", () => { ["#activity-type", "#activity-search", "#activity-journal"].forEach(selector => $(selector).value = ""); expandedActivityDays.clear(); renderActivity(); });
  renderActivity();

  const itemReader = item => ({title:item.title || "Recorded item", body:item.highlights?.length ? ledgerRecordBody(item) : `<p class="modal-summary">${esc(item.kind || "Project record")} · ${esc(item.status || "Recorded")}${item.recorded_at ? ` · ${esc(item.date_label || "Recorded")} ${esc(fullTime(item.recorded_at))}` : ""}</p><div class="record-body">${esc(item.detail || item.text || item.summary || "No detail recorded.")}</div><details><summary>Inspect prepared record</summary><pre>${esc(JSON.stringify(item.raw || item, null, 2))}</pre></details>`, ids:item.source_ids, kicker:"EVIDENCE RECORD"});
  const attachItemButtons = root => root.querySelectorAll("[data-item]").forEach(button => button.addEventListener("click", () => {
    const item = JSON.parse(button.dataset.item);
    const reader = itemReader(item);
    openModal(reader.title, reader.body, reader.ids, reader.kicker);
  }));
  attachItemButtons(app);
  const openSpark = spark => openModal(spark.title || "Project learning", `<div class="rich-text spark-excerpt">${spark.excerpt_html || esc(spark.learning)}</div><dl><div><dt>Basis</dt><dd>${esc(spark.basis ? titleCase(spark.basis) : spark.state)}</dd></div><div><dt>Source passage</dt><dd>${esc((spark.origins || []).map(ref => ref.locator).join(", "))}</dd></div></dl><p class="method-note">${esc(spark.limits || "Read the source to assess this learning.")}</p>`, [...new Set(sourceIdsForSpark(spark))], "PROJECT LEARNING", Object.fromEntries((spark.origins || []).map(ref => [ref.source_id, ref.locator])));
  app.querySelectorAll("[data-spark-index]").forEach(button => button.addEventListener("click", () => {
    openSpark(sparks[Number(button.dataset.sparkIndex)]);
  }));
  $("#open-follow-ups").addEventListener("click", () => openModal("Recorded follow-ups", `<p class="modal-summary">${esc(presentation.now?.next_move)} These entries retain their recorded context; they are not a ranked task list.</p><div class="reading-list">${followUps.map(itemButton).join("") || '<p>No follow-up records in this snapshot.</p>'}</div>`, presentation.now?.source_ids, "PROJECT DIRECTION"));
  const evidenceItems = [...(evidence.verification || []).map(item => ({...item, category:"verification"})), ...(evidence.decisions || []).map(item => ({...item, category:"decisions"})), ...[...(evidence.relationships || []), ...(evidence.unknowns || [])].map(item => ({...item, category:"relationships"}))];
  let evidenceLimit = 12;
  const renderEvidence = () => {
    const query = $("#evidence-search").value.trim().toLowerCase();
    const category = $("#evidence-type").value;
    const selected = evidenceItems.filter(item => (!category || item.category === category) && `${item.title} ${item.detail || item.text || item.summary}`.toLowerCase().includes(query));
    $("#evidence-count").textContent = `${selected.length} records`;
    $("#evidence-list").innerHTML = selected.slice(0, evidenceLimit).map(itemButton).join("") || '<p class="empty">No matching records. Clear the search or choose another category.</p>';
    $("#evidence-more").hidden = selected.length <= evidenceLimit;
    $("#evidence-more").textContent = `Show ${Math.min(12, selected.length - evidenceLimit)} more records`;
    attachItemButtons($("#evidence-list"));
  };
  ["#evidence-search", "#evidence-type"].forEach(selector => $(selector).addEventListener("input", () => { evidenceLimit = 12; renderEvidence(); }));
  $("#evidence-more").addEventListener("click", () => { evidenceLimit += 12; renderEvidence(); });
  renderEvidence();
  $("#provenance").addEventListener("click", () => openModal("Report provenance", `<dl><div><dt>Facts hash</dt><dd>${esc(evidence.provenance?.facts_source_hash || "Not recorded")}</dd></div><div><dt>Observations hash</dt><dd>${esc(evidence.provenance?.observations_source_hash || "Not recorded")}</dd></div><div><dt>Source coverage</dt><dd>${esc(evidence.provenance?.source_count || 0)} sources; ${esc(evidence.provenance?.covered_journal_count || 0)}/${esc(evidence.provenance?.journal_count || 0)} journals covered</dd></div><div><dt>Uncovered journals</dt><dd>${esc((evidence.provenance?.uncovered_journal_ids || []).length || "None")}</dd></div></dl><p class="modal-summary">Validation binds report observations to the recorded sources. It preserves unknown relationships for human judgment.</p>`, [], "REPORT METHOD"));

  const search = $("#record-search");
  const quickFind = $("#quick-find");
  const renderSearch = () => {
    const query = search.value.trim().toLowerCase();
    const result = $("#search-results");
    if (!query) { result.innerHTML = ""; return; }
    const documentResults = docs.filter(doc => `${doc.title} ${doc.description} ${doc.path} ${doc.raw || ""}`.toLowerCase().includes(query)).slice(0, 8).map(doc => `<button type="button" data-record="${esc(doc.id)}"><span>Source</span><strong>${esc(doc.title)}</strong><em>${esc(doc.path)}</em></button>`);
    const sparkResults = sparks.map((spark, index) => ({spark, index})).filter(({spark}) => `${spark.title} ${spark.learning} ${spark.excerpt || ""}`.toLowerCase().includes(query)).slice(0, 4).map(({spark, index}) => `<button type="button" data-search-spark="${index}"><span>Spark</span><strong>${esc(spark.title)}</strong><em>${esc(spark.source_title || spark.scope)}</em></button>`);
    const eventResults = (activity.events || []).filter(event => `${event.title} ${event.summary}`.toLowerCase().includes(query)).slice(0, 4).map(event => `<button type="button" data-search-event='${esc(JSON.stringify(event))}'><span>Activity</span><strong>${esc(event.title || "Recorded event")}</strong><em>${esc(shortDate(event.at))}</em></button>`);
    result.innerHTML = [...sparkResults, ...documentResults, ...eventResults].join("") || "<p>No matching source, learning or event.</p>";
    result.querySelectorAll("[data-search-spark]").forEach(button => button.addEventListener("click", () => openSpark(sparks[Number(button.dataset.searchSpark)])));
    attachRecordButtons(result);
    result.querySelectorAll("[data-search-event]").forEach(button => button.addEventListener("click", () => {
      const event = JSON.parse(button.dataset.searchEvent);
      openModal(event.title || "Recorded event", `<p class="modal-summary">${esc(event.summary || "No summary recorded.")}</p>`, sourceIdsForEvent(event), "ACTIVITY RECORD");
    }));
  };
  $("#open-search").addEventListener("click", () => { quickFind.hidden = false; search.focus(); });
  $("#close-search").addEventListener("click", () => { quickFind.hidden = true; search.value = ""; renderSearch(); });
  search.addEventListener("input", renderSearch);
  document.addEventListener("keydown", event => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k" && !modal.open) { event.preventDefault(); quickFind.hidden = false; search.focus(); }
    if (event.key === "Escape" && !modal.open && !quickFind.hidden) { quickFind.hidden = true; $("#open-search").focus(); }
  });
  window.addEventListener("hashchange", () => { if (location.hash !== "#main") setTab(location.hash.slice(1)); });
  setTab(location.hash.slice(1));
})();
