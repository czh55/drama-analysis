#!/usr/bin/env node
// 用法: node render-recap.mjs <内容JSON> <输出HTML路径>
// 内容 JSON 结构见 README 或 docs/WORKFLOW.md Step 6
import { readFileSync, writeFileSync } from 'node:fs';

const [, , contentPath, outPath] = process.argv;
if (!contentPath || !outPath) {
  console.error('用法: node render-recap.mjs <内容JSON> <输出HTML>');
  process.exit(1);
}

const C = JSON.parse(readFileSync(contentPath, 'utf8'));

const esc = (s) =>
  String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

const sceneNav = C.scenes
  .map(
    (s) => `        <a class="map-link" href="#${s.id}">
          <span class="map-id">${s.num}</span>
          <span><b>${esc(s.title)}</b><small>${esc(s.time)}</small></span>
        </a>`
  )
  .join('\n');

const lessonNav = `        <a class="map-link lesson-map-link" href="#lessons">
          <span class="map-id lesson-id">启</span>
          <span><b>人生启示 · 六条处世智慧</b><small>LIFE LESSONS</small></span>
        </a>`;

const lessonCards = C.lessons
  .map(
    (l) => `        <article class="lesson-card">
          <span class="lesson-tag">${esc(l.tag)}</span>
          <h3>${esc(l.title)}</h3>
          <p class="lesson-situation"><b>情境：</b>${esc(l.situation)}</p>
          <div class="lesson-advice">
            <b>遇到这种情况，可以这样做</b>
            <ol>
              ${l.advice.map((a) => `<li>${esc(a)}</li>`).join('\n              ')}
            </ol>
          </div>
        </article>`
  )
  .join('\n\n');

const sceneCards = C.scenes
  .map(
    (s) => `    <section class="card scene-card" id="${s.id}">
      <div class="scene-topline">
        <div><span class="scene-id">${s.num}</span><span class="time">${esc(s.time)}</span></div>
      </div>
      <img class="scene-frame" src="images/${C.slug}/${s.id}.jpg" alt="${esc(s.title)}" loading="lazy">
      <h2>${esc(s.title)}</h2>
      <div class="scene-body">
        ${s.body.map((p) => `<p>${esc(p)}</p>`).join('\n')}
      </div>
      <div class="quotes">
        <p class="quotes-title">关键台词</p>
        <ul>
          ${s.quotes.map((q) => `<li>${esc(q)}</li>`).join('\n')}
        </ul>
      </div>
    </section>`
  )
  .join('\n\n');

const castCards = C.cast
  .map(
    (c) => `        <article>
          <div class="cast-name"><h3>${esc(c.name)}</h3><span>${esc(c.role)}</span></div>
          <p>${esc(c.desc)}</p>
        </article>`
  )
  .join('\n\n');

const highlightCards = C.highlights
  .map(
    (h) => `        <article>
          <h3>${esc(h.title)}</h3>
          <p>${esc(h.desc)}</p>
        </article>`
  )
  .join('\n\n');

const foreshadowCards = C.foreshadows
  .map(
    (f) => `        <article>
          <h3>${esc(f.title)}</h3>
          <p>${esc(f.desc)}</p>
        </article>`
  )
  .join('\n\n');

const css = `:root {
  --teal-950:#073f42; --teal-800:#0d686c; --teal-700:#0f7c80; --teal-600:#14919b;
  --mint-100:#dff4ec; --mint-50:#f0faf6; --ink:#183536; --muted:#607879;
  --line:#d7e8e2; --paper:#fff; --amber:#a85d08; --shadow:0 12px 32px rgba(7,63,66,.08);
}
* { box-sizing:border-box; }
html { scroll-behavior:smooth; scroll-padding-top:24px; }
body { margin:0; color:var(--ink); background:#edf7f2; font-family:Inter,"PingFang SC","Noto Sans SC","Microsoft YaHei",system-ui,sans-serif; line-height:1.75; }
a { color:inherit; }
.hero { color:#fff; background:radial-gradient(circle at 85% 10%,rgba(129,230,196,.24),transparent 30%),linear-gradient(125deg,#073f42,#0d7377 56%,#14919b); }
.hero-inner { width:min(1440px,100%); margin:auto; padding:48px clamp(20px,5vw,72px) 42px; }
.hero-flex { display:flex; gap:clamp(18px,3vw,40px); align-items:flex-start; }
.hero-cover { width:min(360px,52vw); height:auto; max-height:320px; object-fit:cover; object-position:center; border-radius:16px; border:1px solid rgba(255,255,255,.28); box-shadow:0 18px 44px rgba(0,0,0,.32); flex-shrink:0; }
.hero-text { min-width:0; flex:1; }
.eyebrow { margin:0 0 12px; font-size:.78rem; font-weight:800; letter-spacing:.14em; text-transform:uppercase; opacity:.8; }
h1 { max-width:1020px; margin:0; font-size:clamp(2rem,4.2vw,4rem); line-height:1.13; letter-spacing:-.04em; }
.hero-ep { margin:8px 0 0; font-size:clamp(1.15rem,2.2vw,1.6rem); font-weight:650; opacity:.95; }
.hero-en { margin:10px 0 24px; font-size:clamp(.95rem,1.6vw,1.1rem); opacity:.8; }
.hero-meta { display:flex; flex-wrap:wrap; gap:9px; align-items:center; }
.chip { border:1px solid rgba(255,255,255,.28); border-radius:99px; padding:5px 11px; font-size:.82rem; background:rgba(255,255,255,.08); }
.page { width:min(1440px,100%); margin:auto; padding:28px clamp(16px,3vw,44px) 64px; display:grid; grid-template-columns:minmax(230px,280px) minmax(0,1fr); gap:30px; align-items:start; }
.sidebar { position:sticky; top:20px; min-width:0; }
.sidebar-box { background:rgba(255,255,255,.8); border:1px solid var(--line); border-radius:16px; padding:17px; box-shadow:var(--shadow); backdrop-filter:blur(12px); }
.sidebar h2 { margin:0 0 13px; font-size:.9rem; letter-spacing:.08em; color:var(--teal-800); }
.map-link { display:grid; grid-template-columns:34px minmax(0,1fr); gap:9px; padding:10px 6px; text-decoration:none; border-top:1px solid var(--line); }
.map-link:hover b { color:var(--teal-700); }
.map-id { width:30px; height:30px; display:grid; place-items:center; border-radius:9px; color:#fff; background:var(--teal-700); font-size:.72rem; font-weight:800; }
.map-link b { display:block; font-size:.78rem; line-height:1.4; }
.map-link small { display:block; color:var(--muted); font-size:.67rem; line-height:1.4; margin-top:2px; overflow-wrap:anywhere; }
.content { min-width:0; }
.card { background:var(--paper); border:1px solid var(--line); border-radius:20px; padding:clamp(20px,3vw,34px); margin-bottom:24px; box-shadow:var(--shadow); overflow:hidden; }
.scene-frame { display:block; width:100%; max-height:480px; object-fit:cover; object-position:center; border-radius:14px; margin:16px 0 4px; border:1px solid var(--line); box-shadow:0 10px 28px rgba(7,63,66,.1); }
.scene-topline { display:flex; justify-content:space-between; gap:16px; align-items:center; }
.scene-id { display:inline-grid; place-items:center; min-width:42px; height:30px; padding:0 10px; color:#fff; background:var(--teal-700); border-radius:8px; font-size:.78rem; font-weight:850; }
.time { margin-left:10px; color:var(--muted); font-size:.82rem; font-variant-numeric:tabular-nums; }
.scene-card h2 { margin:18px 0 2px; font-size:clamp(1.35rem,2.4vw,2rem); line-height:1.25; color:var(--teal-950); }
.scene-body p { margin:0 0 12px; color:#33504f; }
.scene-body p:last-child { margin-bottom:0; }
.quotes { margin-top:16px; padding:14px 16px; background:var(--mint-50); border-left:3px solid var(--teal-600); border-radius:0 12px 12px 0; }
.quotes-title { margin:0 0 8px; font-size:.72rem; font-weight:800; letter-spacing:.12em; color:var(--teal-700); }
.quotes ul { margin:0; padding-left:18px; }
.quotes li { margin:4px 0; color:#3d6d6b; font-size:.92rem; }
.section-heading { display:flex; align-items:baseline; gap:10px; margin:0 0 15px; color:var(--teal-950); font-size:1.35rem; }
.section-heading small { color:var(--teal-600); font-size:.78rem; letter-spacing:.05em; }
.overview-lead { margin:0 0 10px; padding:12px 15px; color:#496566; background:var(--mint-50); border-left:3px solid var(--teal-600); border-radius:0 10px 10px 0; font-size:.95rem; font-weight:650; }
.overview p { margin:0; color:#33504f; }
.study-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:14px; }
.study-grid article { padding:17px; background:#fff; border:1px solid var(--line); border-radius:14px; box-shadow:0 6px 18px rgba(7,63,66,.05); min-width:0; }
.study-grid h3 { margin:0 0 7px; font-size:1rem; color:var(--teal-800); }
.study-grid p { margin:0; font-size:.88rem; color:#496566; }
.cast-name { display:flex; align-items:baseline; gap:8px; flex-wrap:wrap; }
.cast-name h3 { margin:0; }
.cast-name span { font-size:.72rem; color:var(--muted); }
.study-section { margin:38px 0 0; }
.lessons-intro { margin:0 0 18px; padding:13px 16px; color:#496566; background:#fdf6ea; border-left:3px solid var(--amber); border-radius:0 10px 10px 0; font-size:.92rem; line-height:1.7; }
.lesson-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:16px; }
.lesson-card { background:#fff; border:1px solid var(--line); border-top:3px solid var(--amber); border-radius:16px; padding:20px; box-shadow:0 6px 18px rgba(7,63,66,.05); min-width:0; }
.lesson-tag { display:inline-block; margin-bottom:9px; padding:3px 10px; border-radius:99px; background:#fdf3e3; color:var(--amber); font-size:.7rem; font-weight:750; letter-spacing:.04em; }
.lesson-card h3 { margin:0 0 11px; font-size:1.05rem; line-height:1.45; color:var(--teal-950); }
.lesson-situation { margin:0 0 12px; padding:10px 13px; background:#f5f7f6; border-radius:10px; color:#607879; font-size:.85rem; line-height:1.6; }
.lesson-situation b { color:var(--ink); }
.lesson-advice b { display:block; margin-bottom:8px; color:var(--amber); font-size:.78rem; letter-spacing:.06em; }
.lesson-advice ol { margin:0; padding-left:20px; }
.lesson-advice li { margin:6px 0; color:#33504f; font-size:.88rem; line-height:1.62; }
.map-link.lesson-map-link { border-top:2px solid var(--amber); }
.lesson-id { background:var(--amber); }
footer { margin-top:38px; padding-top:16px; color:var(--muted); font-size:.78rem; text-align:center; border-top:1px solid var(--line); }
@media (max-width:900px) {
  .page { grid-template-columns:1fr; }
  .sidebar { position:static; }
  .sidebar-box { overflow-x:auto; padding:12px; }
  .sidebar h2 { padding-left:5px; }
  .map-nav { display:flex; width:max-content; gap:8px; }
  .map-link { width:230px; border:1px solid var(--line); border-radius:10px; padding:8px; }
}
@media (max-width:620px) {
  .hero-inner { padding-top:32px; }
  .hero-flex { flex-direction:column; align-items:center; }
  .hero-cover { width:100%; max-width:420px; }
  .hero-text { text-align:center; }
  .page { padding-inline:10px; gap:18px; }
  .scene-card { border-radius:14px; padding:17px 13px; }
  .study-grid { grid-template-columns:1fr; }
  .lesson-grid { grid-template-columns:1fr; }
}
@media (prefers-reduced-motion:reduce) { html { scroll-behavior:auto; } }`;

const html = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <meta name="description" content="电视剧《${C.drama}》第 ${C.episode} 集剧情图文总结" />
  <title>${C.drama}｜第 ${C.episode} 集 · 剧情总结</title>
  <style>
${css}
</style>
</head>
<body>
  <header class="hero">
    <div class="hero-inner">
      <div class="hero-flex">
        <img class="hero-cover" src="images/${C.slug}/hero.jpg" alt="《${C.drama}》第 ${C.episode} 集 封面" loading="lazy">
        <div class="hero-text">
          <p class="eyebrow">Drama Recap · 剧情图文总结</p>
          <h1>${C.drama}</h1>
          <p class="hero-ep">第 ${C.episode} 集 · ${esc(C.title)}</p>
          <p class="hero-en">${esc(C.subtitle)}</p>
          <div class="hero-meta">
            ${C.meta.map((m) => `<span class="chip">${esc(m)}</span>`).join('\n            ')}
          </div>
        </div>
      </div>
    </div>
  </header>
  <main class="page">
    <aside class="sidebar" aria-label="剧情地图">
      <div class="sidebar-box">
        <h2>剧情地图 · SCENE MAP</h2>
        <nav class="map-nav">
${sceneNav}

${lessonNav}
        </nav>
      </div>
    </aside>
    <div class="content">
      <section class="card" id="overview">
        <h2 class="section-heading">剧情梗概 <small>OVERVIEW</small></h2>
        <p class="overview-lead">${esc(C.overviewLead)}</p>
        <p>${esc(C.overview)}</p>
      </section>

      <section class="study-section" id="lessons">
        <h2 class="section-heading">人生启示 <small>LIFE LESSONS</small></h2>
        <p class="lessons-intro">剧里的鸡毛蒜皮，往往是人生的缩影。这些情节不只是故事——当你在现实中遇到同样的处境时，它们能提醒你：先做什么、别做什么、怎么说才有效。</p>
        <div class="lesson-grid">
${lessonCards}

        </div>
      </section>

      <section class="study-section" id="scenes">
        <h2 class="section-heading">关键情节 <small>KEY SCENES</small></h2>
${sceneCards}
      </section>

      <section class="study-section" id="cast">
        <h2 class="section-heading">登场人物 <small>CAST</small></h2>
        <div class="study-grid">
${castCards}
        </div>
      </section>

      <section class="study-section" id="highlights">
        <h2 class="section-heading">关键看点 <small>HIGHLIGHTS</small></h2>
        <div class="study-grid">
${highlightCards}
        </div>
      </section>

      <section class="study-section" id="foreshadows">
        <h2 class="section-heading">伏笔悬念 <small>FORESHADOWING</small></h2>
        <div class="study-grid">
${foreshadowCards}
        </div>
      </section>

      <footer>本页剧情描述基于第 ${C.episode} 集语音转录整理 · ASR 专有名词已按语境校正 · 台词为引用转述，细节以正片为准</footer>
    </div>
  </main>
</body>
</html>`;

writeFileSync(outPath, html, 'utf8');
console.log(`已生成: ${outPath} (${C.scenes.length} 场景, ${C.lessons.length} 启示)`);
