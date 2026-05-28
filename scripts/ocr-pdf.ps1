param(
    [Parameter(Mandatory = $true, Position = 0)]
    [string] $Path,

    [string] $Language = "rus+eng",
    [int] $Dpi = 300,
    [string] $OcrMyPdf = $env:OCRMYPDF_EXE,
    [string] $Tesseract = $env:TESSERACT_EXE,
    [string] $PdfToPpm = $env:PDFTOPPM_EXE
)

$ErrorActionPreference = "Stop"
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[Console]::OutputEncoding = $utf8NoBom
$OutputEncoding = $utf8NoBom

function Resolve-Executable {
    param(
        [string] $ExplicitPath,
        [string] $CommandName
    )

    if ($ExplicitPath) {
        $candidate = Resolve-Path -LiteralPath $ExplicitPath -ErrorAction SilentlyContinue
        if ($candidate) {
            return $candidate.Path
        }
        return $ExplicitPath
    }

    $command = Get-Command $CommandName -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }
    return $null
}

function Fail-Ocr {
    param([string] $Message)

    [Console]::Error.WriteLine($Message)
    exit 2
}

$pdfPath = Resolve-Path -LiteralPath $Path -ErrorAction Stop
$ocrMyPdfPath = Resolve-Executable -ExplicitPath $OcrMyPdf -CommandName "ocrmypdf"
$tesseractPath = Resolve-Executable -ExplicitPath $Tesseract -CommandName "tesseract"
$pdfToPpmPath = Resolve-Executable -ExplicitPath $PdfToPpm -CommandName "pdftoppm"

$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("tender-killer-ocr-" + [System.Guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $tempRoot | Out-Null

try {
    if ($ocrMyPdfPath) {
        $sidecarPath = Join-Path $tempRoot "ocr.txt"
        $outputPdfPath = Join-Path $tempRoot "ocr.pdf"
        & $ocrMyPdfPath --force-ocr --skip-text --language $Language --sidecar $sidecarPath $pdfPath.Path $outputPdfPath 1>$null
        if ($LASTEXITCODE -ne 0) {
            Fail-Ocr "ocrmypdf exited with code $LASTEXITCODE"
        }
        if (Test-Path -LiteralPath $sidecarPath) {
            Get-Content -LiteralPath $sidecarPath -Raw -Encoding UTF8
        }
        exit 0
    }

    if ($tesseractPath -and $pdfToPpmPath) {
        $pagePrefix = Join-Path $tempRoot "page"
        & $pdfToPpmPath -png -r $Dpi $pdfPath.Path $pagePrefix 1>$null
        if ($LASTEXITCODE -ne 0) {
            Fail-Ocr "pdftoppm exited with code $LASTEXITCODE"
        }

        $pages = Get-ChildItem -LiteralPath $tempRoot -Filter "page-*.png" | Sort-Object Name
        foreach ($page in $pages) {
            & $tesseractPath $page.FullName stdout -l $Language --psm 6
            if ($LASTEXITCODE -ne 0) {
                Fail-Ocr "tesseract exited with code $LASTEXITCODE for $($page.Name)"
            }
        }
        exit 0
    }

    Fail-Ocr "OCR backend not found. Install OCRmyPDF, or install Tesseract plus Poppler pdftoppm, or set OCRMYPDF_EXE/TESSERACT_EXE/PDFTOPPM_EXE."
}
finally {
    if (Test-Path -LiteralPath $tempRoot) {
        Remove-Item -LiteralPath $tempRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# For Tender Killer, configure:
# $env:TENDER_KILLER_PDF_OCR_COMMAND = "powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ocr-pdf.ps1 {path}"
