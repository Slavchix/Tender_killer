import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import fs from 'node:fs/promises'
import http from 'node:http'
import net from 'node:net'
import os from 'node:os'
import path from 'node:path'

const DEFAULT_URL = 'http://127.0.0.1:5175/'
const DEFAULT_OUT_DIR = 'artifacts/visual-smoke'
const VALID_SCOPES = new Set(['full', 'tz'])
const SURFACE_SCOPES = {
  tz: ['dashboard', 'tender-list', 'analysis-workspace'],
  full: ['dashboard', 'tender-list', 'analysis-workspace', 'economics-workspace'],
}
const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900, deviceScaleFactor: 1 },
  { name: 'mobile', width: 390, height: 844, deviceScaleFactor: 2 },
]
const WORKSPACE_SELECTORS = {
  analysis: '.fullscreen-workspace.analysis',
  economics: '.fullscreen-workspace.economics',
}
const SURFACE_CHECKS = {
  dashboard: [
    { id: 'dashboard-root', selector: '.dashboard-view' },
    { id: 'dashboard-queue-board', selector: '.dashboard-queue-board' },
    { id: 'dashboard-queue-columns', selector: '.dashboard-queue-column', minCount: 1 },
    { id: 'dashboard-queue-items', selector: '.dashboard-queue-items', minCount: 1 },
    { id: 'dashboard-right-rail', selector: '.dashboard-right-rail' },
  ],
  'tender-list': [
    { id: 'tender-list-root', selector: '.tender-list' },
    { id: 'tender-list-rows', selector: '.tender-list .rows', minWidth: 24, minHeight: 0 },
    { id: 'tender-list-row-insights', selector: '.tender-row .row-insights', optional: true },
  ],
  'analysis-workspace': [
    { id: 'analysis-workspace-root', selector: '.fullscreen-workspace.analysis' },
    { id: 'analysis-workspace-core', selector: '.fullscreen-workspace.analysis .fullscreen-workspace-body' },
    { id: 'analysis-header', selector: '.fullscreen-workspace-header' },
    { id: 'analysis-decision-brief', selector: '.analysis-decision-brief', optional: true },
    { id: 'analysis-passport', selector: '.analysis-passport', optional: true },
  ],
  'economics-workspace': [
    { id: 'economics-workspace-root', selector: '.fullscreen-workspace.economics' },
    { id: 'economics-workspace-core', selector: '.fullscreen-workspace.economics .fullscreen-workspace-body' },
    { id: 'economics-header', selector: '.fullscreen-workspace-header' },
  ],
}

const args = parseArgs(process.argv.slice(2))
const baseUrl = args.url || DEFAULT_URL
const outDir = args.out || DEFAULT_OUT_DIR
const browserPath = args.browser || process.env.CHROME_PATH || findBrowserPath()
const scope = normalizeScope(args.scope)

if (!browserPath) {
  console.error('No Chrome/Edge executable found. Pass --browser or set CHROME_PATH.')
  process.exit(1)
}
if (typeof WebSocket === 'undefined') {
  console.error('Node.js with built-in WebSocket support is required for scripts/visual-smoke.mjs.')
  process.exit(1)
}

const result = await runVisualSmoke({ baseUrl, browserPath, outDir, scope })
if (args.json) {
  console.log(JSON.stringify(result, null, 2))
} else {
  printHumanResult(result)
}
process.exit(result.ok ? 0 : 1)

async function runVisualSmoke({ baseUrl, browserPath, outDir, scope }) {
  await fs.mkdir(outDir, { recursive: true })
  const userDataDir = await fs.mkdtemp(path.join(os.tmpdir(), 'tender-killer-visual-'))
  const port = await freePort()
  const browser = spawn(browserPath, [
    '--headless=new',
    '--disable-gpu',
    '--no-first-run',
    '--no-default-browser-check',
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${userDataDir}`,
    'about:blank',
  ], { stdio: 'ignore' })

  try {
    const version = await waitForJson(`http://127.0.0.1:${port}/json/version`, 8000)
    const page = await newPage(port, baseUrl)
    const cdp = await connectCdp(page.webSocketDebuggerUrl)
    const browserEvents = createBrowserEventLog()
    await cdp.send('Page.enable')
    await cdp.send('Log.enable')
    await cdp.send('Runtime.enable')
    installBrowserEventListeners(cdp, browserEvents)

    const checks = []
    const surfaces = SURFACE_SCOPES[scope]
    for (const viewport of VIEWPORTS) {
      await cdp.send('Emulation.setDeviceMetricsOverride', {
        width: viewport.width,
        height: viewport.height,
        deviceScaleFactor: viewport.deviceScaleFactor,
        mobile: viewport.width < 700,
      })
      resetBrowserEvents(browserEvents)
      await navigate(cdp, baseUrl)
      if (surfaces.includes('dashboard')) {
        checks.push(await visualCheck(cdp, viewport, outDir, 'dashboard', SURFACE_CHECKS.dashboard, browserEvents))
      }
      if (surfaces.includes('tender-list')) {
        checks.push(await openTenderListCheck(cdp, viewport, outDir, browserEvents))
      }
      if (surfaces.includes('analysis-workspace')) {
        checks.push(await openWorkspaceCheck(cdp, viewport, outDir, browserEvents, 'analysis'))
      }
      if (surfaces.includes('economics-workspace')) {
        checks.push(await openWorkspaceCheck(cdp, viewport, outDir, browserEvents, 'economics'))
      }
    }
    await cdp.close()
    return {
      ok: checks.every((check) => check.ok || check.skipped),
      browser: version.Browser,
      base_url: baseUrl,
      out_dir: outDir,
      scope,
      checks,
      browser_events: browserEvents.all,
    }
  } finally {
    await stopBrowser(browser)
    await removeUserDataDir(userDataDir)
  }
}

async function openTenderListCheck(cdp, viewport, outDir, browserEvents) {
  resetBrowserEvents(browserEvents)
  await clickByText(cdp, 'Закупки')
  await wait(300)
  return visualCheck(cdp, viewport, outDir, 'tender-list', SURFACE_CHECKS['tender-list'], browserEvents)
}

async function openWorkspaceCheck(cdp, viewport, outDir, browserEvents, mode) {
  resetBrowserEvents(browserEvents)
  await clickByText(cdp, 'Закупки')
  await wait(300)
  const hasTender = await evaluate(cdp, `Boolean(document.querySelector('.tender-row'))`)
  if (!hasTender) {
    return {
      name: `${viewport.name}:${mode}-workspace`,
      ok: true,
      skipped: true,
      error: 'No tender rows available in the current dev database.',
    }
  }
  await evaluate(cdp, `document.querySelector('.tender-row')?.click()`)
  await waitForSelector(cdp, '.tender-detail-card', 8000)
  await evaluate(cdp, `document.querySelector('.summary-card.${mode}')?.click()`)
  await wait(500)
  return visualCheck(cdp, viewport, outDir, `${mode}-workspace`, SURFACE_CHECKS[`${mode}-workspace`] || [
    { id: `${mode}-workspace-root`, selector: WORKSPACE_SELECTORS[mode] },
    { id: `${mode}-workspace-header`, selector: '.fullscreen-workspace-header' },
    { id: `${mode}-workspace-body`, selector: '.fullscreen-workspace-body' },
  ], browserEvents)
}

async function visualCheck(cdp, viewport, outDir, name, checks, browserEvents) {
  const selectorResult = await evaluate(cdp, `(() => {
    const checks = ${JSON.stringify(checks)};
    return checks.map((check) => {
      const elements = Array.from(document.querySelectorAll(check.selector));
      if (!elements.length) {
        return {
          id: check.id,
          selector: check.selector,
          optional: Boolean(check.optional),
          ok: Boolean(check.optional),
          count: 0,
          error: check.optional ? 'optional selector absent' : 'missing selector',
        };
      }
      const visible = elements
        .map((element) => {
          const rect = element.getBoundingClientRect();
          const style = getComputedStyle(element);
          const minWidth = Number(check.minWidth ?? 24);
          const minHeight = Number(check.minHeight ?? 24);
          return {
            rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
            visible: rect.width >= minWidth && rect.height >= minHeight && style.visibility !== 'hidden' && style.display !== 'none',
          };
        })
        .filter((item) => item.visible);
      const minCount = Number(check.minCount || 1);
      const first = visible[0] || { rect: { x: 0, y: 0, width: 0, height: 0 } };
      return {
        id: check.id,
        selector: check.selector,
        optional: Boolean(check.optional),
        ok: visible.length >= minCount,
        count: elements.length,
        visible_count: visible.length,
        rect: first.rect,
        error: visible.length >= minCount ? '' : 'not visible enough',
      };
    });
  })()`)
  const failed = selectorResult.find((item) => !item.ok)
  const browserCheck = assertNoNewBrowserErrors(browserEvents)
  const screenshotPath = path.join(outDir, `${viewport.name}-${name}.png`)
  await captureScreenshot(cdp, screenshotPath)
  return {
    name: `${viewport.name}:${name}`,
    ok: !failed && browserCheck.ok,
    skipped: false,
    screenshot: screenshotPath,
    selectors: selectorResult,
    browser_errors: browserCheck.errors,
    error: failed ? `${failed.selector}: ${failed.error || 'not visible'}` : browserCheck.error,
  }
}

async function captureScreenshot(cdp, filePath) {
  const result = await cdp.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false })
  await fs.writeFile(filePath, Buffer.from(result.data, 'base64'))
}

async function navigate(cdp, url) {
  const load = waitForEvent(cdp, 'Page.loadEventFired', 10000)
  await cdp.send('Page.navigate', { url })
  await load
  await waitForSelector(cdp, '#root', 8000)
  await wait(500)
}

async function clickByText(cdp, text) {
  await evaluate(cdp, `(() => {
    const text = ${JSON.stringify(text)};
    const buttons = Array.from(document.querySelectorAll('button'));
    const button = buttons.find((item) => (item.textContent || '').includes(text));
    if (button) button.click();
    return Boolean(button);
  })()`)
}

async function waitForSelector(cdp, selector, timeoutMs) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    if (await evaluate(cdp, `Boolean(document.querySelector(${JSON.stringify(selector)}))`)) return
    await wait(100)
  }
  throw new Error(`Timed out waiting for ${selector}`)
}

async function evaluate(cdp, expression) {
  const result = await cdp.send('Runtime.evaluate', {
    expression,
    awaitPromise: true,
    returnByValue: true,
  })
  if (result.exceptionDetails) {
    throw new Error(result.exceptionDetails.text || 'Runtime.evaluate failed')
  }
  return result.result.value
}

async function connectCdp(webSocketUrl) {
  const socket = new WebSocket(webSocketUrl)
  const callbacks = new Map()
  const listeners = new Map()
  let nextId = 1
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true })
    socket.addEventListener('error', reject, { once: true })
  })
  socket.addEventListener('message', (event) => {
    const message = JSON.parse(event.data)
    if (message.id && callbacks.has(message.id)) {
      const { resolve, reject } = callbacks.get(message.id)
      callbacks.delete(message.id)
      if (message.error) reject(new Error(message.error.message))
      else resolve(message.result || {})
      return
    }
    if (message.method && listeners.has(message.method)) {
      for (const listener of listeners.get(message.method)) listener(message.params || {})
    }
  })
  return {
    send(method, params = {}) {
      const id = nextId++
      socket.send(JSON.stringify({ id, method, params }))
      return new Promise((resolve, reject) => callbacks.set(id, { resolve, reject }))
    },
    on(method, listener) {
      listeners.set(method, [...(listeners.get(method) || []), listener])
    },
    close() {
      socket.close()
    },
  }
}

function waitForEvent(cdp, method, timeoutMs) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Timed out waiting for ${method}`)), timeoutMs)
    cdp.on(method, (params) => {
      clearTimeout(timer)
      resolve(params)
    })
  })
}

async function newPage(port, url) {
  const response = await fetch(`http://127.0.0.1:${port}/json/new?${encodeURIComponent(url)}`, { method: 'PUT' })
  if (!response.ok) throw new Error(`Could not create Chrome target: HTTP ${response.status}`)
  return response.json()
}

async function waitForJson(url, timeoutMs) {
  const deadline = Date.now() + timeoutMs
  while (Date.now() < deadline) {
    try {
      return await getJson(url)
    } catch {
      await wait(100)
    }
  }
  throw new Error(`Timed out waiting for ${url}`)
}

function getJson(url) {
  return new Promise((resolve, reject) => {
    http.get(url, (response) => {
      let body = ''
      response.setEncoding('utf8')
      response.on('data', (chunk) => { body += chunk })
      response.on('end', () => {
        try {
          resolve(JSON.parse(body))
        } catch (error) {
          reject(error)
        }
      })
    }).on('error', reject)
  })
}

function freePort() {
  return new Promise((resolve, reject) => {
    const server = net.createServer()
    server.listen(0, '127.0.0.1', () => {
      const address = server.address()
      server.close(() => resolve(address.port))
    })
    server.on('error', reject)
  })
}

function findBrowserPath() {
  const candidates = process.platform === 'win32'
    ? [
        `${process.env.PROGRAMFILES || 'C:\\Program Files'}\\Google\\Chrome\\Application\\chrome.exe`,
        `${process.env['PROGRAMFILES(X86)'] || 'C:\\Program Files (x86)'}\\Google\\Chrome\\Application\\chrome.exe`,
        `${process.env.LOCALAPPDATA || ''}\\Google\\Chrome\\Application\\chrome.exe`,
        `${process.env.PROGRAMFILES || 'C:\\Program Files'}\\Microsoft\\Edge\\Application\\msedge.exe`,
        `${process.env['PROGRAMFILES(X86)'] || 'C:\\Program Files (x86)'}\\Microsoft\\Edge\\Application\\msedge.exe`,
      ]
    : ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium']
  return candidates.find((candidate) => Boolean(candidate) && existsSync(candidate))
}

function stopBrowser(browser) {
  if (browser.exitCode !== null || browser.signalCode !== null) return Promise.resolve()
  return new Promise((resolve) => {
    let settled = false
    const done = () => {
      if (settled) return
      settled = true
      resolve()
    }
    browser.once('exit', done)
    browser.once('close', done)
    browser.kill()
    const timer = setTimeout(done, 3000)
    if (typeof timer.unref === 'function') timer.unref()
  })
}

async function removeUserDataDir(userDataDir) {
  const retryableCodes = new Set(['EBUSY', 'EPERM', 'ENOTEMPTY'])
  for (let attempt = 0; attempt < 8; attempt += 1) {
    try {
      await fs.rm(userDataDir, { recursive: true, force: true })
      return
    } catch (error) {
      if (!retryableCodes.has(error.code) || attempt === 7) throw error
      await wait(150 * (attempt + 1))
    }
  }
}

function parseArgs(argv) {
  const parsed = { scope: 'full' }
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    if (arg === '--json') parsed.json = true
    else if (arg === '--url') parsed.url = argv[++index]
    else if (arg === '--out') parsed.out = argv[++index]
    else if (arg === '--browser') parsed.browser = argv[++index]
    else if (arg === '--scope') parsed.scope = argv[++index]
  }
  return { ...parsed, scope: parsed.scope || 'full' }
}

function normalizeScope(value) {
  const scope = value || 'full'
  if (!VALID_SCOPES.has(scope)) {
    console.error(`Unknown visual smoke scope "${scope}". Use one of: ${Array.from(VALID_SCOPES).join(', ')}.`)
    process.exit(1)
  }
  return scope
}

function printHumanResult(result) {
  console.log(`Tender Killer visual smoke: ${result.ok ? 'ok' : 'failed'}`)
  console.log(`- Browser: ${result.browser}`)
  console.log(`- URL: ${result.base_url}`)
  console.log(`- Scope: ${result.scope}`)
  console.log(`- Screenshots: ${result.out_dir}`)
  for (const check of result.checks) {
    const state = check.skipped ? 'SKIP' : check.ok ? 'OK' : 'FAIL'
    const suffix = check.error ? ` - ${check.error}` : ''
    console.log(`- ${state} ${check.name}${suffix}`)
  }
}

function createBrowserEventLog() {
  return { all: [], since_reset: [] }
}

function installBrowserEventListeners(cdp, browserEvents) {
  cdp.on('Runtime.exceptionThrown', (params) => {
    recordBrowserEvent(browserEvents, {
      type: 'runtime_exception',
      level: 'error',
      text: params.exceptionDetails?.text || params.exceptionDetails?.exception?.description || 'Runtime exception',
    })
  })
  cdp.on('Runtime.consoleAPICalled', (params) => {
    if (!['error', 'assert'].includes(params.type)) return
    recordBrowserEvent(browserEvents, {
      type: 'console',
      level: params.type,
      text: (params.args || []).map((arg) => arg.value || arg.description || '').filter(Boolean).join(' '),
    })
  })
  cdp.on('Log.entryAdded', (params) => {
    const entry = params.entry || {}
    if (isIgnoredBrowserLogEntry(entry)) return
    if (!['error', 'warning'].includes(entry.level)) return
    recordBrowserEvent(browserEvents, {
      type: 'log',
      level: entry.level,
      text: entry.text || entry.url || 'Browser log entry',
      url: entry.url,
    })
  })
}

function isIgnoredBrowserLogEntry(entry) {
  const url = String(entry.url || '')
  const text = String(entry.text || '')
  return url.includes('favicon.ico') || text.includes('favicon.ico')
}

function recordBrowserEvent(browserEvents, event) {
  const item = {
    ...event,
    text: String(event.text || '').slice(0, 500),
  }
  browserEvents.all.push(item)
  browserEvents.since_reset.push(item)
}

function resetBrowserEvents(browserEvents) {
  browserEvents.since_reset = []
}

function assertNoNewBrowserErrors(browserEvents) {
  const errors = browserEvents.since_reset.filter((event) => event.level === 'error' || event.level === 'assert')
  return {
    ok: errors.length === 0,
    errors,
    error: errors.length ? errors.map((event) => `${event.type}: ${event.text}`).join('; ').slice(0, 500) : '',
  }
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
