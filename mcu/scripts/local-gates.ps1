# 本地一键复跑 CI 全部门（与 scripts/local-gates.sh 同语义、同标签）。
#
# 语义：FAIL 让退出码非零；工具缺失记 SKIP（附安装提示）但**不算失败**——
#       CI 才是真门禁，本脚本只为提交前自查省时。
#
# 本文件必须存成 UTF-8 with BOM：PowerShell 5.1 对没有 BOM 的 UTF-8 会按 ANSI 读，
# 中文标签与提示会全变成乱码（脚本仍能跑，但输出没法看）。
#
# 用法：powershell -File scripts/local-gates.ps1 [-Only <label>]
$ErrorActionPreference = 'Continue'

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $root

$only = ''
if ($args.Count -ge 2 -and $args[0] -eq '-Only') { $only = $args[1] }

$script:PassCount = 0
$script:FailCount = 0
$script:SkipCount = 0
$log = Join-Path $env:TEMP ("local-gates-" + [guid]::NewGuid().ToString('N') + ".log")

function Report([string]$label, [string]$status, [string]$note) {
  $pad = 'FAIL'.Length
  $shown = $status.PadRight($pad)
  if ($note) { Write-Host "[$shown] $label  —— $note" } else { Write-Host "[$shown] $label" }
  if ($status -eq 'PASS') { $script:PassCount++ }
  elseif ($status -eq 'FAIL') { $script:FailCount++ }
  else { $script:SkipCount++ }
}

function Skip-Gate([string]$label, [string]$reason) {
  if ($only -and $only -ne $label) { return }
  Report $label 'SKIP' $reason
}

# 跑一道门：失败时打印输出前 40 行（够定位，又不至于刷屏）
function Invoke-Gate([string]$label, [scriptblock]$body) {
  if ($only -and $only -ne $label) { return }
  $start = Get-Date
  & $body *> $log
  $code = $LASTEXITCODE
  $secs = [int]((Get-Date) - $start).TotalSeconds
  if ($code -eq 0) {
    Report $label 'PASS' "${secs}s"
  } else {
    Report $label 'FAIL' "${secs}s"
    Get-Content $log -TotalCount 40 | ForEach-Object { "    $_" } | Write-Host
  }
}

function Invoke-Npm([string]$scriptName) {
  Invoke-Gate $scriptName { & npm run --silent $scriptName }
}

function Test-Command([string]$name) {
  $null -ne (Get-Command $name -ErrorAction SilentlyContinue)
}

Write-Host '== 本地门禁（与 CI 对齐；FAIL 才算失败，SKIP 是工具不在本机）=='

# ---- 运行时探测 -------------------------------------------------------------
if (-not (Test-Command 'node')) {
  Report 'node' 'FAIL' '装 Node.js 24 再来'
  Write-Host "共 $script:PassCount pass / $script:FailCount fail / $script:SkipCount skip"
  exit 1
}
Report 'node' 'PASS' (& node -v)

$py = ''
foreach ($c in @('python', 'py')) {
  if (Test-Command $c) { $py = $c; break }
}

# ---- 站点与文档门（npm 脚本，与 quality.yml 的 npm run quality 同集合）-----
foreach ($s in @(
    'test', 'projects:check', 'docs:build', 'anim:lint', 'readme:check', 'reading:check',
    'links:check', 'docs:check', 'nav:check', 'seo:check', 'perf:budget', 'a11y:check',
    'pages:check', 'search:check')) {
  Invoke-Npm $s
}

Invoke-Npm 'anim:audit'

& npx --no-install playwright --version *> $null
if ($LASTEXITCODE -eq 0) {
  Invoke-Npm 'test:browser'
} else {
  Skip-Gate 'test:browser' '缺 Playwright：npm i && npx playwright install chromium'
}

# ---- 固件：ARM 工具链不在本机时只做 SKIP（CI 的 arm-host job 才是真门禁）----
if (Test-Command 'arm-none-eabi-gcc') {
  Invoke-Npm 'firmware:check'
} else {
  Skip-Gate 'firmware:check' '缺 arm-none-eabi-gcc'
}

# ---- 整书：构建 → 契约门 → 打包 ----
Invoke-Npm 'book:check'
if ($py) {
  Invoke-Gate 'book:unittest' { & $py -m unittest discover mcu-book/tests }
  Invoke-Gate 'book:pack' { & $py mcu-book/publish_downloads.py --out-dir .temp/book-downloads }
  Invoke-Gate 'book:pack-verify' { & $py mcu-book/publish_downloads.py --verify .temp/book-downloads }
  # PDF 契约门要有 PDF 才跑得动；本地重建一次约 8 分钟，故只在产物已存在时跑，缺就 SKIP
  if (Test-Path 'mcu-book/dist/mcu-deep-book.pdf') {
    Invoke-Gate 'book:pdfcheck' { & $py mcu-book/check_pdf.py }
  } else {
    Skip-Gate 'book:pdfcheck' '先跑 npm run book:pdf 生成 PDF（约 8 分钟），再跑这一项'
  }
} else {
  Skip-Gate 'book:unittest' '缺 Python 3'
  Skip-Gate 'book:pack' '缺 Python 3'
  Skip-Gate 'book:pack-verify' '缺 Python 3'
  Skip-Gate 'book:pdfcheck' '缺 Python 3'
}

# ---- Python 静态检查：只抓真错误，不做格式/风格 ----
$ruffOk = $false
if ($py) {
  & $py -m ruff --version *> $null
  $ruffOk = ($LASTEXITCODE -eq 0)
}
if ($ruffOk) {
  Invoke-Gate 'ruff' { & $py -m ruff check . }
} else {
  Skip-Gate 'ruff' '缺 ruff：python -m pip install ruff==0.15.21'
}

Write-Host "共 $script:PassCount pass / $script:FailCount fail / $script:SkipCount skip"
if ($script:FailCount -gt 0) { exit 1 } else { exit 0 }