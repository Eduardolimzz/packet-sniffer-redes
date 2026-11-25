@echo off
REM Sobe o servidor HTTP na porta 80, servindo os arquivos desta pasta (index.html).
REM Rode como administrador se o Windows bloquear a porta 80 e libere no firewall se pedir.
REM Observacao: o servidor DNS (dnsmasq, iniciar_dns.sh) so existe no Linux;
REM no Windows ha apenas o servidor HTTP.

cd /d "%~dp0"
echo Servidor HTTP na porta 80 (pasta: %CD%). Ctrl+C para parar.
python -m http.server 80
