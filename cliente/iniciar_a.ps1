<#
=====================================================================
 MÁQUINA A (Windows - cliente): prepara tudo e inicia o sniffer.

   - pede permissão de administrador (o sniffer precisa)
   - confere o Python, o Npcap e as bibliotecas (instala o que faltar)
   - espera o cabo ser detectado na placa "Ethernet"
   - configura o IP fixo 192.168.10.1/24 e deixa a rede como Privada
   - testa a conexão com a máquina B (ping, HTTP e DNS)
   - abre uma janela para gerar o tráfego da demonstração
   - inicia o sniffer (Ctrl+C para parar e ver o total de pacotes)

 Uso: clique duas vezes em cliente\iniciar_a.bat
      Se a placa tiver outro nome: cliente\iniciar_a.bat "Ethernet 2"
=====================================================================
#>
param([string]$Interface = "Ethernet")

$IP_CLIENTE  = "192.168.10.1"
$IP_SERVIDOR = "192.168.10.2"
$PREFIXO     = 24
$DOMINIO     = "servidor.redes"

function Passo($texto) { Write-Host ""; Write-Host "==> $texto" -ForegroundColor Cyan }
function Aviso($texto) { Write-Host "AVISO: $texto" -ForegroundColor Yellow }
function Falha($texto) { Write-Host "ERRO: $texto" -ForegroundColor Red; exit 1 }

# --- 1. Administrador -------------------------------------------------
$identidade = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal  = New-Object Security.Principal.WindowsPrincipal($identidade)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Pedindo permissão de administrador (clique em Sim)..."
    Start-Process powershell.exe -Verb RunAs -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-NoExit",
        "-File", "`"$PSCommandPath`"", "-Interface", "`"$Interface`"")
    exit
}

# Pasta raiz do projeto (este script fica em cliente\)
$raiz = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Set-Location $raiz

# --- 2. Python, Npcap e bibliotecas --------------------------------------
Passo "Verificando o Python"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Falha "Python não encontrado. Instale pelo python.org marcando 'Add python.exe to PATH' e abra este script de novo."
}
$versao = & python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Falha "Python não encontrado. Instale pelo python.org marcando 'Add python.exe to PATH' e abra este script de novo."
}
Write-Host $versao

Passo "Verificando o Npcap"
if (-not (Get-Service -Name npcap -ErrorAction SilentlyContinue)) {
    Falha "Npcap não encontrado. Instale o Wireshark (wireshark.org) aceitando instalar o Npcap."
}
Write-Host "OK"

Passo "Verificando as bibliotecas (scapy, rich)"
& python -c "import scapy, rich" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Instalando (precisa de internet)..."
    & python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Falha "não consegui instalar as bibliotecas. Conecte na internet e rode de novo." }
}
Write-Host "OK"

# --- 3. Placa e cabo ---------------------------------------------------
Passo "Verificando a placa '$Interface' e o cabo"
if (-not (Get-NetAdapter -Name $Interface -ErrorAction SilentlyContinue)) {
    Get-NetAdapter | Format-Table Name, InterfaceDescription, Status -AutoSize
    Falha "placa '$Interface' não encontrada. Rode de novo com o nome certo, ex.: cliente\iniciar_a.bat `"Ethernet 2`""
}
for ($i = 0; $i -lt 30; $i++) {
    if ((Get-NetAdapter -Name $Interface).Status -eq "Up") { break }
    if ($i -eq 0) { Write-Host "Sem sinal no cabo. Encaixe o cabo firme nas duas máquinas (esperando até 30 s)..." }
    Start-Sleep -Seconds 1
}
if ((Get-NetAdapter -Name $Interface).Status -ne "Up") {
    Falha "o cabo não foi detectado na placa '$Interface' (status: Disconnected)."
}
Write-Host "Cabo OK ($((Get-NetAdapter -Name $Interface).LinkSpeed))"

# --- 4. IP fixo --------------------------------------------------------
Passo "Configurando o IP $IP_CLIENTE/$PREFIXO"
$atuais = Get-NetIPAddress -InterfaceAlias $Interface -AddressFamily IPv4 -ErrorAction SilentlyContinue
if ($atuais.IPAddress -contains $IP_CLIENTE) {
    Write-Host "Já estava configurado"
} else {
    # Desliga o DHCP, apaga o IP automático (169.254.x.x) e coloca o IP fixo
    Set-NetIPInterface -InterfaceAlias $Interface -Dhcp Disabled
    if ($atuais) { $atuais | Remove-NetIPAddress -Confirm:$false -ErrorAction SilentlyContinue }
    New-NetIPAddress -InterfaceAlias $Interface -IPAddress $IP_CLIENTE -PrefixLength $PREFIXO | Out-Null
    Write-Host "Configurado"
}

# Rede como Privada (o perfil pode demorar alguns segundos para aparecer)
$privada = $false
for ($i = 0; $i -lt 10 -and -not $privada; $i++) {
    try {
        Set-NetConnectionProfile -InterfaceAlias $Interface -NetworkCategory Private -ErrorAction Stop
        $privada = $true
    } catch { Start-Sleep -Seconds 1 }
}
if (-not $privada) { Aviso "não consegui marcar a rede como Privada; se algo for bloqueado, confira o firewall." }

# --- 5. Testa a máquina B -----------------------------------------------
Passo "Testando a conexão com a máquina B ($IP_SERVIDOR)"
if (Test-Connection -ComputerName $IP_SERVIDOR -Count 2 -Quiet) {
    Write-Host "Ping: OK"
} else {
    Aviso "a máquina B não respondeu ao ping. Confira se o iniciar_b.sh está rodando nela."
}
try {
    Invoke-WebRequest -Uri "http://$IP_SERVIDOR/" -UseBasicParsing -TimeoutSec 3 | Out-Null
    Write-Host "HTTP: OK"
} catch { Aviso "o servidor HTTP da máquina B não respondeu." }
try {
    Resolve-DnsName $DOMINIO -Server $IP_SERVIDOR -DnsOnly -Type A -ErrorAction Stop | Out-Null
    Write-Host "DNS:  OK"
} catch { Aviso "o servidor DNS da máquina B não respondeu." }

# --- 6. Janela para gerar o tráfego ---------------------------------------
Passo "Abrindo a janela de testes (gerar_trafego.bat)"
Start-Process cmd.exe -ArgumentList "/k cd /d `"$raiz`" && cliente\gerar_trafego.bat"

# --- 7. Sniffer ----------------------------------------------------------
Passo "Iniciando o sniffer na placa '$Interface' (Ctrl+C para parar)"
& python sniffer\main.py --iface $Interface
