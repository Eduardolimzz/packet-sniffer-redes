@echo off
REM ==================================================================
REM  MAQUINA A (Windows): prepara tudo e inicia o sniffer com um clique.
REM  Uso: clique duas vezes neste arquivo
REM       ou, se a placa tiver outro nome: cliente\iniciar_a.bat "Ethernet 2"
REM ==================================================================
set "IFACE=%~1"
if "%IFACE%"=="" set "IFACE=Ethernet"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0iniciar_a.ps1" -Interface "%IFACE%"
echo.
echo (Se uma janela de administrador foi aberta, o sniffer esta rodando nela.)
pause
