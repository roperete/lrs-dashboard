// Drive the built app in headless Chrome through a list of steps and report any page error.
//
//   node scripts/ui_scenario.mjs <devtools-port> <url> <steps.json> [out-dir]
//
// Steps (JSON array), each one of:
//   {"click": "Table"}                 a button or link whose trimmed text is exactly this
//   {"clickSel": "css selector"}       the first element matching
//   {"type": "text"}                   type into the focused element
//   {"focus": "css selector"}
//   {"hover": "css selector"}       move the mouse onto the first match (scrolled into view)
//   {"key": "ArrowDown"}               press a key
//   {"wait": 1500}
//   {"eval": "js expression", "as": "name"}   record a value
//   {"expect": "js expression", "why": "text"} fail the scenario if falsy
//   {"shot": "name"}                   screenshot to out-dir/name.png
//   {"viewport": [390, 844, true]}     width, height, mobile
// Start Chrome with --remote-debugging-port and software WebGL (see check notes in the repo).
import fs from 'node:fs';
import path from 'node:path';

const [port, url, stepsFile, outDir = '/tmp'] = process.argv.slice(2);
const steps = JSON.parse(fs.readFileSync(stepsFile, 'utf8'));
const sleep = ms => new Promise(r => setTimeout(r, ms));
const target = await (await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent('about:blank')}`, { method: 'PUT' })).json();
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let id = 0; const pending = new Map(); const errors = []; const values = {}; const failures = []; const environment = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
  if (m.method === 'Runtime.exceptionThrown') errors.push((m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text).split('\n')[0].slice(0, 300));
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') {
    const msg = m.params.args.map(a => a.value ?? a.description ?? '').join(' ').split('\n')[0].slice(0, 300);
    // headless Chrome's software GL cannot compile some globe shaders: the test machine, not the app
    if (/THREE\.WebGLProgram: Shader Error/.test(msg)) environment.push(msg); else errors.push('console.error: ' + msg);
  }
});
const send = (method, params = {}) => new Promise(r => { const i = ++id; pending.set(i, r); ws.send(JSON.stringify({ id: i, method, params })); });
const evaluate = async expr => {
  const r = await send('Runtime.evaluate', { expression: expr, awaitPromise: true, returnByValue: true });
  return r.result?.exceptionDetails ? { __error: r.result.exceptionDetails.exception?.description?.split('\n')[0] } : r.result?.result?.value;
};

await send('Page.enable'); await send('Runtime.enable');
await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
await send('Page.navigate', { url });
await sleep(Number(process.env.WAIT || 9000));

for (const [i, st] of steps.entries()) {
  const where = `step ${i + 1} ${JSON.stringify(st).slice(0, 80)}`;
  if (st.viewport) {
    const [w, h, mobile] = st.viewport;
    await send('Emulation.setDeviceMetricsOverride', { width: w, height: h, deviceScaleFactor: 1, mobile: !!mobile });
    await sleep(800);
  } else if (st.click !== undefined) {
    const ok = await evaluate(`(() => { const t = ${JSON.stringify(st.click)}; const el = [...document.querySelectorAll('button, a, [role=button]')].find(b => b.textContent.trim() === t || b.getAttribute('aria-label') === t); if (!el) return false; el.click(); return true; })()`);
    if (!ok) failures.push(`${where}: nothing to click`);
    await sleep(st.after ?? 900);
  } else if (st.clickSel) {
    const ok = await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(st.clickSel)}); if (!el) return false; el.click(); return true; })()`);
    if (!ok) failures.push(`${where}: no element`);
    await sleep(st.after ?? 900);
  } else if (st.hover) {
    const pos = await evaluate(`(() => { const el = document.querySelector(${JSON.stringify(st.hover)}); if (!el) return null; el.scrollIntoView({ block: 'center', inline: 'center' }); const b = el.getBoundingClientRect(); return { x: b.left + b.width / 2, y: b.top + b.height / 2 }; })()`);
    if (!pos) failures.push(`${where}: nothing to hover`);
    else { await send('Input.dispatchMouseEvent', { type: 'mouseMoved', x: pos.x, y: pos.y }); await sleep(st.after ?? 600); }
  } else if (st.focus) {
    await evaluate(`document.querySelector(${JSON.stringify(st.focus)})?.focus()`);
  } else if (st.type !== undefined) {
    for (const ch of st.type) { await send('Input.insertText', { text: ch }); await sleep(120); }
    await sleep(600);
  } else if (st.key) {
    const code = st.key.length === 1 ? `Key${st.key.toUpperCase()}` : st.key;
    await send('Input.dispatchKeyEvent', { type: 'keyDown', key: st.key, code, windowsVirtualKeyCode: { ArrowDown: 40, ArrowUp: 38, Enter: 13, Escape: 27, Tab: 9 }[st.key] ?? 0 });
    await send('Input.dispatchKeyEvent', { type: 'keyUp', key: st.key, code });
    await sleep(st.after ?? 500);
  } else if (st.wait) {
    await sleep(st.wait);
  } else if (st.eval) {
    values[st.as || `v${i}`] = await evaluate(st.eval);
  } else if (st.expect) {
    const v = await evaluate(st.expect);
    if (!v || v.__error) failures.push(`${where}: ${st.why || 'expectation failed'}${v?.__error ? ' (' + v.__error + ')' : ''}`);
  } else if (st.shot) {
    const s = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(path.join(outDir, `${st.shot}.png`), Buffer.from(s.result.data, 'base64'));
  }
  // the page must never go blank: the app renders its bar on every screen
  const alive = await evaluate(`!!document.querySelector('header') || !!document.querySelector('[role=alert]')`);
  if (!alive) { failures.push(`${where}: the page went blank`); break; }
}
const alerts = await evaluate(`[...document.querySelectorAll('[role=alert]')].map(a => a.innerText.slice(0, 200))`);
console.log(JSON.stringify({ values, failures, errors, alerts, environment: environment.length ? `${environment.length} software-GL shader messages` : undefined }, null, 1));
ws.close();
// close the tab: left open, each run's globe keeps a WebGL context until Chrome can make no more
await fetch(`http://127.0.0.1:${port}/json/close/${target.id}`).catch(() => {});
process.exit(failures.length || errors.length ? 1 : 0);
