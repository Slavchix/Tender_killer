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
const browserPath = resolveBrowserPath()
const profile = resolveProfile()
const profileDir = profile.dir
const headless = !['0', 'false', 'no', 'off'].includes(String(process.env.TENDER_KILLER_BROWSER_HEADLESS || '1').toLowerCase())

if (!browserPath) {
  console.error('Browser executable was not found. Set TENDER_KILLER_BROWSER_PATH.')
  process.exit(3)
}

fs.mkdirSync(profileDir, { recursive: true })

let browserProcess
let client
try {
  const port = await findFreePort()
  browserProcess = spawn(browserPath, browserArgs(port, profileDir, headless), {
    stdio: ['ignore', 'ignore', 'pipe'],
    windowsHide: true,
  })
  const stderrChunks = []
  browserProcess.stderr.on('data', (chunk) => stderrChunks.push(chunk.toString()))

  const version = await waitForJson(`http://127.0.0.1:${port}/json/version`, timeoutMs)
  const target = await createTarget(port, version)
  client = await createCdpClient(target.webSocketDebuggerUrl || version.webSocketDebuggerUrl)
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
  if (profile.cleanup) {
    removeProfileDir(profileDir)
  }
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
          matched: ${JSON.stringify(markerExpression())}
        };
      })()`,
      returnByValue: true,
    })
    const value = result?.result?.value || {}
    lastHtml = String(value.html || '')
    if (lastHtml && isGoodEnoughHtml(lastHtml, value.readyState)) {
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
  return ''
}

function isGoodEnoughHtml(html, readyState) {
  if (provider === 'officemag') {
    if (html.includes('js-productListItem') || html.includes('ProductSpecial') || html.includes('ProductHead__name')) {
      return true
    }
    if (html.includes('Ваш браузер не смог пройти') || html.includes('challenge_cookie_expires')) {
      return readyState === 'complete'
    }
    return false
  }
  return html.length > 500 && readyState === 'complete'
}

async function createTarget(port, version) {
  const createUrl = `http://127.0.0.1:${port}/json/new?${encodeURIComponent('about:blank')}`
  try {
    const response = await fetch(createUrl, { method: 'PUT' })
    if (response.ok) {
      return await response.json()
    }
  } catch {
    // Fall back to an existing page target.
  }
  const targets = await waitForJson(`http://127.0.0.1:${port}/json/list`, 3000)
  const page = targets.find((target) => target.type === 'page' && target.webSocketDebuggerUrl)
  if (!page && version.webSocketDebuggerUrl) {
    return version
  }
  if (!page) {
    throw new Error('browser target was not available')
  }
  return page
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

function resolveProfile() {
  if (process.env.TENDER_KILLER_BROWSER_PROFILE_DIR) {
    return { dir: process.env.TENDER_KILLER_BROWSER_PROFILE_DIR, cleanup: false }
  }
  const parentDir = path.join(process.cwd(), 'data', 'browser-profile', 'supplier-fetch-runs')
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
