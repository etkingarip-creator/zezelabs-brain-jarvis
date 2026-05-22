# ZEZE-LABS JARVIS DESKTOP AUTO-SETUP
# Bu script backend ve desktop'ı otomatik başlatır

param(
    [string]$Mode = "full",  # full | backend_only | desktop_only
    [switch]$SkipInstall
)

$ErrorActionPreference = "Continue"
$RepoRoot = "C:\Users\Zezelabs2\.gemini\antigravity\scratch\zezelabs-brain"

Write-Host "🏛️ ZEZE-LABS JARVIS AUTO-SETUP başlıyor..." -ForegroundColor Cyan

# --- ADIM 1: Git Pull ---
Write-Host "`n📥 En son kodlar çekiliyor..." -ForegroundColor Yellow
Set-Location $RepoRoot
git checkout main
git pull origin main
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️ Git pull başarısız, mevcut kodla devam ediliyor" -ForegroundColor Yellow
}

# --- ADIM 2: Dependencies ---
if ($SkipInstall -eq $false) {
    Write-Host "`n📦 Bağımlılıklar yükleniyor..." -ForegroundColor Yellow
    pip install -q -r requirements.txt
}

# --- ADIM 3: Environment Setup ---
Write-Host "`n⚙️ Ortam değişkenleri ayarlanıyor..." -ForegroundColor Yellow

$env:AI_PROVIDER = "deepseek"
$env:DEEPSEEK_MODEL = "deepseek-chat"
$env:ZOM_MOCK_DEEPSEEK = "true"
$env:ZOM_ENABLE_RABBITMQ = "false"
$env:ZOM_ENABLE_HERMES_SYNC = "false"
$env:ZOM_ENABLE_VOICE_LISTENER = "false"
$env:ZOM_ENABLE_AUTO_GITHUB_PUSH = "false"
$env:ZOM_ENABLE_LEGACY_OPENCLAW_CLEANUP = "false"

# --- ADIM 4: Port Kontrolü ---
Write-Host "`n🔍 Port kontrolü..." -ForegroundColor Yellow
$backendRunning = $false
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue

if ($portInUse) {
    # Port 8000 kullanımda, çalışan backend aktif mi kontrol edelim
    try {
        $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/runtime/status" -TimeoutSec 3 -ErrorAction Stop
        if ($health.status -eq "active") {
            Write-Host "   ✅ Backend zaten aktif ve çalışıyor: $($health.ai_mode)" -ForegroundColor Green
            $backendRunning = $true
        }
    } catch {
        # Yanıt vermedi veya aktif değil, sonlandırmayı deneyelim
        Write-Host "   ⚠️ Port 8000 kullanımda fakat yanıt vermiyor. Sonlandırılıyor..." -ForegroundColor Yellow
    }

    if ($backendRunning -eq $false) {
        $processes = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess | Select-Object -Unique
        foreach ($procId in $processes) {
            if ($procId) {
                Write-Host "   Stopping process $procId..." -ForegroundColor Gray
                Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep -Seconds 2
    }
}

# --- ADIM 5: Backend Başlatma ---
if ($Mode -eq "full" -or $Mode -eq "backend_only") {
    if ($backendRunning) {
        Write-Host "`n🚀 Backend zaten aktif olduğu için yeniden başlatma atlandı." -ForegroundColor Green
    } else {
        Write-Host "`n🚀 Backend server başlatılıyor..." -ForegroundColor Green
        
        $backendJob = Start-Job -ScriptBlock {
            param($root)
            Set-Location $root
            python -m uvicorn backend.jarvis:app --host 127.0.0.1 --port 8000
        } -ArgumentList $RepoRoot
        
        Write-Host "   Backend PID: $($backendJob.Id)" -ForegroundColor Cyan
        Start-Sleep -Seconds 3
        
        # Backend kontrolü
        try {
            $health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/runtime/status" -TimeoutSec 5 -ErrorAction Stop
            if ($health.status -eq "active") {
                Write-Host "   ✅ Backend aktif: $($health.ai_mode)" -ForegroundColor Green
            } else {
                Write-Host "   ❌ Backend başlamadı (Durum: $($health.status))" -ForegroundColor Red
            }
        } catch {
            Write-Host "   ❌ Backend başlamadı, logları kontrol et" -ForegroundColor Red
        }
    }
}


# --- ADIM 6: Desktop Başlatma ---
if ($Mode -eq "full" -or $Mode -eq "desktop_only") {
    Write-Host "`n🖥️ Desktop uygulaması başlatılıyor..." -ForegroundColor Green
    
    Start-Job -ScriptBlock {
        param($root)
        Set-Location $root
        python desktop/jarvis_desktop.py
    } -ArgumentList $RepoRoot | Out-Null
    
    Write-Host "   ✅ Desktop başlatıldı" -ForegroundColor Green
}

# --- BİTİŞ ---
Write-Host "`n🏛️ ZEZE-LABS JARVIS HAZIR!" -ForegroundColor Cyan
Write-Host "`n📋 Kontrol:" -ForegroundColor White
Write-Host "   • http://127.0.0.1:8000 -> API" -ForegroundColor Gray
Write-Host "   • http://127.0.0.1:8000/docs -> Dokümanlar" -ForegroundColor Gray
Write-Host "   • Masaüstü penceresi açık olmalı" -ForegroundColor Gray

# --- Kapanış ---
if ($Mode -eq "full") {
    Write-Host "`n💡 Kapatmak için: Ctrl+C veya pencereyi kapat" -ForegroundColor Yellow
    Write-Host "   Backend durdurmak için: Get-Job | Stop-Job -ErrorAction SilentlyContinue" -ForegroundColor Yellow
    
    # Beklet
    while ($true) {
        Start-Sleep -Seconds 10
    }
}
