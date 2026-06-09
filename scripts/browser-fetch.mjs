import { spawn } from 'node:child_process'
import fs from 'node:fs'
import net from 'node:net'
import os from 'node:os'
import path from 'node:path'

const targetUrl = process.argv[2]
if (!targetUrl) {
  console.error('Usage: browser-fetch.mjs <url>')
  process.exit(2)
}

const timeoutMs = positiveEnvFloat('TENDER_KILLER_BROWSER_TIMEOUT_SECONDS', 30) * 1000
const provider = String(process.env.TENDER_KILLER_BROWSER_PROVIDER || '').toLowerCase()
const cdpBaseUrl = resolveCdpBaseUrl()
const browserPath = cdpBaseUrl ? '' : resolveBrowserPath()
const profile = cdpBaseUrl ? null : resolveProfile()
const profileDir = profile?.dir || ''
const headless = !['0', 'false', 'no', 'off'].includes(String(process.env.TENDER_KILLER_BROWSER_HEADLESS || '1').toLowerCase())

if (!cdpBaseUrl && !browserPath) {
  console.error('Browser executable was not found. Set TENDER_KILLER_BROWSER_PATH.')
  process.exit(3)
}

if (profileDir) {
  fs.mkdirSync(profileDir, { recursive: true })
}

let browserProcess
let client
try {
  const browser = cdpBaseUrl ? await attachToBrowser(cdpBaseUrl) : await launchBrowser(browserPath, profileDir, headless)
  browserProcess = browser.process
  const target = browser.target
  client = await createCdpClient(target.webSocketDebuggerUrl)
  await client.call('Page.enable')
  await client.call('Runtime.enable')
  await client.call('Page.navigate', { url: targetUrl })

  const html = await waitForHtml(client, timeoutMs)
  process.stdout.write(html)
} catch (error) {
  console.error(error && error.message ? error.message : String(error))
  process.exit(1)
} finally {
  if (client) {
    client.close()
  }
  if (browserProcess) {
    await stopBrowserProcess(browserProcess)
  }
  if (profile?.cleanup) {
    removeProfileDir(profileDir)
  }
}

async function launchBrowser(executablePath, profileDir, useHeadless) {
  const port = await findFreePort()
  const process = spawn(executablePath, browserArgs(port, profileDir, useHeadless), {
    stdio: ['ignore', 'ignore', 'pipe'],
    windowsHide: true,
    detached: true,
  })
  const stderrChunks = []
  process.stderr.on('data', (chunk) => stderrChunks.push(chunk.toString()))

  const version = await waitForJson(`http://127.0.0.1:${port}/json/version`, timeoutMs)
  const { target } = await createTarget(`http://127.0.0.1:${port}`, version)
  return { process, target, ownedTarget: null }
}

async function attachToBrowser(baseUrl) {
  const version = await waitForJson(`${baseUrl}/json/version`, timeoutMs)
  const reusableTarget = await findReusableTarget(baseUrl)
  if (reusableTarget) {
    return { process: null, target: reusableTarget }
  }
  const { target, owned } = await createTarget(baseUrl, version)
  if (owned) {
    rememberReusableTarget(baseUrl, target)
  }
  return { process: null, target }
}

function browserArgs(port, userDataDir, useHeadless) {
  const args = [
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${userDataDir}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-extensions',
    '--disable-popup-blocking',
    '--disable-background-networking',
    '--disable-crash-reporter',
    '--disable-breakpad',
    '--disable-features=Translate',
    'about:blank',
  ]
  if (useHeadless) {
    args.unshift('--headless=new', '--disable-gpu')
  }
  return args
}

async function waitForHtml(cdp, timeout) {
  const deadline = Date.now() + timeout
  let lastHtml = ''
  while (Date.now() < deadline) {
    const result = await cdp.call('Runtime.evaluate', {
      expression: `(() => {
        const html = document.documentElement ? document.documentElement.outerHTML : '';
        return {
          html,
          readyState: document.readyState,
          href: location.href,
          matched: Boolean(${markerExpression()})
        };
      })()`,
      returnByValue: true,
    })
    const value = result?.result?.value || {}
    lastHtml = String(value.html || '')
    if (lastHtml && isGoodEnoughHtml(lastHtml, value.readyState, value.matched)) {
      return lastHtml
    }
    await sleep(500)
  }
  if (lastHtml) {
    return lastHtml
  }
  throw new Error('browser fetch timed out before DOM was available')
}

function markerExpression() {
  if (provider === 'officemag') {
    return `document.querySelector('.listItemsWrapper li.listItem, .listItemsWrapper .js-productListItem, .ProductHead__name, .listItemsWrapper .Product__price, .listItemsWrapper .js-productSum, input[name="SECTION"]')`
  }
  if (provider === 'komus') {
    return `document.querySelector('a[href*="/p/"], .product-card, [data-qa*="product" i]') ||
      Array.from(document.querySelectorAll('script[type*="ld+json" i]')).some((script) =>
        /"@type"\\s*:\\s*(?:"Product"|\\[[^\\]]*"Product")/i.test(script.textContent || '')
      )`
  }
  if (provider === 'petrovich') {
    return `document.querySelector('a[href*="/product/"], .product-card, [data-test*="product" i]') ||
      Array.from(document.querySelectorAll('script[type*="ld+json" i]')).some((script) =>
        /"@type"\\s*:\\s*(?:"Product"|\\[[^\\]]*"Product")/i.test(script.textContent || '')
      )`
  }
  if (provider === 'vseinstrumenti') {
    return `document.querySelector('a[href*="/product/"], .product-card, [data-qa*="product" i]') ||
      Array.from(document.querySelectorAll('script[type*="ld+json" i]')).some((script) =>
        /"@type"\\s*:\\s*(?:"Product"|\\[[^\\]]*"Product")/i.test(script.textContent || '')
      )`
  }
  if (provider === 'lemanapro') {
    return `document.querySelector('a[href*="/product/"], .product-card, [data-qa*="product" i]') ||
      /window\\.INITIAL_STATE\\["plp"\\].*"products"/is.test(document.documentElement?.outerHTML || '')`
  }
  return 'false'
}

function isGoodEnoughHtml(html, readyState, matched) {
  if (provider === 'officemag') {
    if (matched || html.includes('js-productListItem') || html.includes('ProductSpecial') || html.includes('ProductHead__name')) {
      return true
    }
    if (html.includes('Ваш браузер не смог пройти') || html.includes('challenge_cookie_expires')) {
      return readyState === 'complete'
    }
    return false
  }
  if (provider === 'komus') {
    if (matched || html.includes('href="/p/') || html.includes('"@type":"Product"') || html.includes('"@type": "Product"')) {
      return true
    }
    return false
  }
  if (provider === 'petrovich') {
    if (matched || html.includes('href="/product/') || html.includes('"@type":"Product"') || html.includes('"@type": "Product"')) {
      return true
    }
    return false
  }
  if (provider === 'vseinstrumenti') {
    if (matched || html.includes('href="/product/') || html.includes('"@type":"Product"') || html.includes('"@type": "Product"')) {
      return true
    }
    return false
  }
  if (provider === 'lemanapro') {
    if (matched || html.includes('href="/product/') || /window\.INITIAL_STATE\["plp"\].*"products"/is.test(html)) {
      return true
    }
    return false
  }
  return html.length > 500 && readyState === 'complete'
}

async function createTarget(baseUrl, version) {
  const createUrl = `${baseUrl}/json/new?${encodeURIComponent('about:blank')}`
  try {
    const response = await fetch(createUrl, { method: 'PUT' })
    if (response.ok) {
      return { target: await response.json(), owned: true }
    }
  } catch {
    // Fall back to an existing page target.
  }
  const targets = await waitForJson(`${baseUrl}/json/list`, 3000)
  const page = targets.find((target) => target.type === 'page' && target.webSocketDebuggerUrl)
  if (!page && version.webSocketDebuggerUrl) {
    return { target: version, owned: false }
  }
  if (!page) {
    throw new Error('browser target was not available')
  }
  return { target: page, owned: false }
}

async function findReusableTarget(baseUrl) {
  const targetId = readReusableTargetId(baseUrl)
  if (!targetId) {
    return null
  }
  try {
    const targets = await waitForJson(`${baseUrl}/json/list`, 3000)
    return targets.find((target) => target.id === targetId && target.type === 'page' && target.webSocketDebuggerUrl) || null
  } catch {
    return null
  }
}

function readReusableTargetId(baseUrl) {
  try {
    const state = JSON.parse(fs.readFileSync(reusableTargetStatePath(baseUrl), 'utf8'))
    return typeof state.targetId === 'string' ? state.targetId : ''
  } catch {
    return ''
  }
}

function rememberReusableTarget(baseUrl, target) {
  if (!target?.id) {
    return
  }
  try {
    fs.writeFileSync(
      reusableTargetStatePath(baseUrl),
      JSON.stringify({ baseUrl, targetId: target.id }),
      'utf8',
    )
  } catch {
    // Reuse is an optimization; the request can still complete with a fresh tab.
  }
}

function reusableTargetStatePath(baseUrl) {
  const dir = path.join(os.tmpdir(), 'tender-killer', 'browser-profile', 'supplier-fetch-targets')
  fs.mkdirSync(dir, { recursive: true })
  const key = baseUrl.replace(/[^a-z0-9]+/gi, '_').replace(/^_+|_+$/g, '') || 'default'
  return path.join(dir, `${key}.json`)
}

async function createCdpClient(webSocketUrl) {
  if (!webSocketUrl) {
    throw new Error('browser websocket endpoint was not available')
  }
  const socket = new WebSocket(webSocketUrl)
  const pending = new Map()
  let nextId = 1
  await new Promise((resolve, reject) => {
    socket.addEventListener('open', resolve, { once: true })
    socket.addEventListener('error', reject, { once: true })
  })
  socket.addEventListener('message', (event) => {
    const payload = JSON.parse(event.data)
    if (!payload.id || !pending.has(payload.id)) {
      return
    }
    const { resolve, reject } = pending.get(payload.id)
    pending.delete(payload.id)
    if (payload.error) {
      reject(new Error(payload.error.message || JSON.stringify(payload.error)))
    } else {
      resolve(payload.result)
    }
  })
  return {
    call(method, params = {}) {
      const id = nextId++
      socket.send(JSON.stringify({ id, method, params }))
      return new Promise((resolve, reject) => {
        pending.set(id, { resolve, reject })
      })
    },
    close() {
      socket.close()
    },
  }
}

async function waitForJson(url, timeout) {
  const deadline = Date.now() + timeout
  let lastError = null
  while (Date.now() < deadline) {
    try {
      const response = await fetch(url)
      if (response.ok) {
        return await response.json()
      }
    } catch (error) {
      lastError = error
    }
    await sleep(200)
  }
  throw new Error(`timed out waiting for ${url}: ${lastError ? lastError.message : 'no response'}`)
}

async function findFreePort() {
  const server = net.createServer()
  await new Promise((resolve, reject) => {
    server.listen(0, '127.0.0.1', resolve)
    server.on('error', reject)
  })
  const port = server.address().port
  await new Promise((resolve) => server.close(resolve))
  return port
}

function resolveBrowserPath() {
  if (process.env.TENDER_KILLER_BROWSER_PATH && fs.existsSync(process.env.TENDER_KILLER_BROWSER_PATH)) {
    return process.env.TENDER_KILLER_BROWSER_PATH
  }
  const candidates = process.platform === 'win32'
    ? [
        'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
        'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
      ]
    : [
        '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/usr/bin/microsoft-edge',
        '/usr/bin/google-chrome',
        '/usr/bin/chromium',
      ]
  return candidates.find((candidate) => fs.existsSync(candidate)) || ''
}

function resolveCdpBaseUrl() {
  const value = String(process.env.TENDER_KILLER_BROWSER_CDP_URL || '').trim()
  if (!value) {
    return ''
  }
  try {
    const url = new URL(value)
    if (!['http:', 'https:'].includes(url.protocol)) {
      return ''
    }
    url.pathname = url.pathname.replace(/\/+$/, '')
    url.search = ''
    url.hash = ''
    return url.toString().replace(/\/+$/, '')
  } catch {
    return ''
  }
}

function resolveProfile() {
  if (process.env.TENDER_KILLER_BROWSER_PROFILE_DIR) {
    return { dir: process.env.TENDER_KILLER_BROWSER_PROFILE_DIR, cleanup: false }
  }
  const parentDir = path.join(os.tmpdir(), 'tender-killer', 'browser-profile', 'supplier-fetch-runs')
  fs.mkdirSync(parentDir, { recursive: true })
  return { dir: fs.mkdtempSync(path.join(parentDir, 'run-')), cleanup: true }
}

async function stopBrowserProcess(process) {
  if (process.exitCode !== null || process.killed) {
    return
  }
  process.kill()
  await Promise.race([
    new Promise((resolve) => process.once('exit', resolve)),
    sleep(1500),
  ])
}

function removeProfileDir(profileDir) {
  for (let attempt = 0; attempt < 5; attempt += 1) {
    try {
      fs.rmSync(profileDir, { recursive: true, force: true, maxRetries: 3, retryDelay: 200 })
      return
    } catch {
      // Edge can keep profile files locked for a short moment after exit.
    }
  }
}

function positiveEnvFloat(name, fallback) {
  const value = Number.parseFloat(process.env[name] || '')
  return Number.isFinite(value) && value > 0 ? value : fallback
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
