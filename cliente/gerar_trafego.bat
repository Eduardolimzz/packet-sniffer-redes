@echo off
REM ==================================================================
REM  Gera o trafego da demonstracao, um passo de cada vez.
REM  Deixe o sniffer (e o Wireshark) capturando antes de comecar.
REM ==================================================================
title Gerador de trafego - Maquina A
set "SERVIDOR=192.168.10.2"

echo Deixe o sniffer capturando na outra janela.
echo Cada passo espera voce apertar uma tecla.
pause
echo.
echo ===== [1/6] DNS: consulta de servidor.redes (itens 3 e 5)
nslookup servidor.redes. %SERVIDOR%
pause
echo.
echo ===== [2/6] DNS: dominio que nao existe (NXDOMAIN)
nslookup naoexiste.redes. %SERVIDOR%
pause
echo.
echo ===== [3/6] HTTP: GET / (itens 2, 4 e 5)
curl.exe -s -o NUL -w "Resposta: HTTP %%{http_code}\n" http://%SERVIDOR%/
pause
echo.
echo ===== [4/6] HTTP: GET de pagina que nao existe (404)
curl.exe -s -o NUL -w "Resposta: HTTP %%{http_code}\n" http://%SERVIDOR%/naoexiste
pause
echo.
echo ===== [5/6] HTTP: POST (item 5)
curl.exe -s -o NUL -w "Resposta: HTTP %%{http_code}\n" -X POST -d "teste=123" http://%SERVIDOR%/
pause
echo.
echo ===== [6/6] HTTP: PUT
curl.exe -s -o NUL -w "Resposta: HTTP %%{http_code}\n" -X PUT -d "x=1" http://%SERVIDOR%/
echo.
echo Fim. Volte na janela do sniffer e aperte Ctrl+C para ver o total de pacotes.
pause
