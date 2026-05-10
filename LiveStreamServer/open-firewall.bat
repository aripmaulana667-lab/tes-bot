@echo off
chcp 65001 >nul

:: ---------------------------------------------------------------
:: Buka Port 8765 di Windows Firewall (LiveStream API).
:: Cukup dobel-klik file ini. Akan minta hak Administrator (UAC).
:: ---------------------------------------------------------------

:: Cek apakah sudah Administrator. `net session` butuh hak admin.
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo Meminta hak Administrator...
    powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -Verb RunAs"
    exit /b
)

cd /d "%~dp0"

echo ============================================================
echo  LiveStream Server - Buka Port Firewall
echo ============================================================
echo.

:: Hapus aturan lama (kalau ada) supaya idempotent.
netsh advfirewall firewall delete rule name="LiveStream API" >nul 2>&1

:: Tambah aturan inbound TCP 8765, allow.
netsh advfirewall firewall add rule name="LiveStream API" dir=in protocol=TCP localport=8765 action=allow profile=any
if %errorLevel% neq 0 (
    echo.
    echo [ERROR] Gagal menambah aturan firewall.
    echo Pastikan jalankan sebagai Administrator.
    pause
    exit /b 1
)

echo.
echo [OK] Port TCP 8765 sekarang dibuka di Windows Firewall.
echo.
echo Sekarang controller di laptop bisa konek ke server.
echo Pakai IP VPS (yang biasa kamu pakai untuk RDP) di field Host/IP controller.
echo.
pause
