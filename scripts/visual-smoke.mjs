import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import fs from 'node:fs/promises'
import http from 'node:http'
import net from 'node:net'
import os from 'node:os'
import path from 'node:path'

const DEFAULT_URL = 'http://127.0.0.1:5175/'
const DEFAULT_OUT_DIR = 'artifacts/visual-smoke'
const VIEWPORTS = [
  { name: 'desktop', width: 1440, height: 900, deviceScaleFactor: 1 },
  { name: 'mobile', width: 390, height: 844, deviceScaleFactor: 2 },
]
const WORKSPACE_SELECTORS = {
  analysis: '.fullscreen-workspace.analysis',
  economics: '.fullscreen-workspace.economics',
}

const args = parseArgs(process.argv.slice(2))
const baseUrl = args.url || DEFAULT_URL
const outDir = args.out || DEFAULT_OUT_DIR
const browserPath = args.browser || process.env.CHROME_PATH || findBrowserPath()

if (!browserPath) {
  console.error('No Chrome/Edge executable found. Pass --browser or set CHROME_PATH.')
  process.exit(1)
}
if (typeof WebSocket === 'undefined') {
  console.error('Node.js with built-in WebSocket support is required for scripts/visual-smoke.mjs.')
  process.exit(1)
}

const result = await runVisualSmoke({ baseUrl, browserPath, outDir })
if (args.json) {
  console.log(JSON.stringify(result, null, 2))
} else {
  printHumanResult(result)
}
process.exit(result.ok ? 0 : 1)

async function runVisualSmoke({ baseUrl, browserPath, outDir }) {
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
    await cdp.send('Page.enable')
    await cdp.send('Runtime.enable')

    const checks = []
    for (const viewport of VIEWPORTS) {
      await cdp.send('Emulation.setDeviceMetricsOverride', {
        width: viewport.width,
        height: viewport.height,
        deviceScaleFactor: viewport.deviceScaleFactor,
        mobile: viewport.width < 700,
      })
      await navigate(cdp, baseUrl)
      checks.push(await visualCheck(cdp, viewport, outDir, 'dashboard', [
        '.dashboard-view',
        '.dashboard-queue-board',
        '.dashboard-right-rail',
      ]))
      checks.push(await openTenderListCheck(cdp, viewport, outDir))
      checks.push(await openWorkspaceCheck(cdp, viewport, outDir, 'analysis'))
      checks.push(await openWorkspaceCheck(cdp, viewport, outDir, 'economics'))
    }
    await cdp.close()
    return {
      ok: checks.every((check) => check.ok || check.skipped),
      browser: version.Browser,
      base_url: baseUrl,
      out_dir: outDir,
      checks,
    }
  } finally {
    browser.kill()
    await fs.rm(userDataDir, { recursive: true, force: true })
  }
}

async function openTenderListCheck(cdp, viewport, outDir) {
  await clickByText(cdp, 'Закупки')
  await wait(300)
  return visualCheck(cdp, viewport, outDir, 'tender-list', [
    '.tender-list',
    '.tender-list .rows',
  ])
}

async function openWorkspaceCheck(cdp, viewport, outDir, mode) {
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
  return visualCheck(cdp, viewport, outDir, `${mode}-workspace`, [
    WORKSPACE_SELECTORS[mode],
    '.fullscreen-workspace-header',
    '.fullscreen-workspace-body',
  ])
}

async function visualCheck(cdp, viewport, outDir, name, selectors) {
  const selectorResult = await evaluate(cdp, `(() => {
    const selectors = ${JSON.stringify(selectors)};
    return selectors.map((selector) => {
      const element = document.querySelector(selector);
      if (!element) return { selector, ok: false, error: 'missing selector' };
      const rect = element.getBoundingClientRect();
      const style = getComputedStyle(element);
      return {
        selector,
        ok: rect.width > 24 && rect.height > 24 && style.visibility !== 'hidden' && style.display !== 'none',
        rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
        error: '',
      };
    });
  })()`)
  const failed = selectorResult.find((item) => !item.ok)
  const screenshotPath = path.join(outDir, `${viewport.name}-${name}.png`)
  await captureScreenshot(cdp, screenshotPath)
  return {
    name: `${viewport.name}:${name}`,
    ok: !failed,
    skipped: false,
    screenshot: screenshotPath,
    selectors: selectorResult,
    error: failed ? `${failed.selector}: ${failed.error || 'not visible'}` : '',
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

function parseArgs(argv) {
  const parsed = {}
  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index]
    if (arg === '--json') parsed.json = true
    else if (arg === '--url') parsed.url = argv[++index]
    else if (arg === '--out') parsed.out = argv[++index]
    else if (arg === '--browser') parsed.browser = argv[++index]
  }
  return parsed
}

function printHumanResult(result) {
  console.log(`Tender Killer visual smoke: ${result.ok ? 'ok' : 'failed'}`)
  console.log(`- Browser: ${result.browser}`)
  console.log(`- URL: ${result.base_url}`)
  console.log(`- Screenshots: ${result.out_dir}`)
  for (const check of result.checks) {
    const state = check.skipped ? 'SKIP' : check.ok ? 'OK' : 'FAIL'
    const suffix = check.error ? ` - ${check.error}` : ''
    console.log(`- ${state} ${check.name}${suffix}`)
  }
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
