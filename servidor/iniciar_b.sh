#!/bin/bash
# =====================================================================
# MÁQUINA B (Ubuntu - servidor): prepara tudo com um comando só.
#
#   - instala o dnsmasq-base, se faltar (precisa de internet só na 1ª vez)
#   - encontra a placa cabeada e cria/atualiza a conexão "cabo-cross"
#   - espera o cabo ser detectado e ativa o IP 192.168.10.2/24
#   - libera as portas 80/TCP e 53/UDP no firewall (se o ufw estiver ativo)
#   - sobe o servidor HTTP (porta 80) e o servidor DNS (porta 53)
#
# Uso:  ./servidor/iniciar_b.sh            (descobre a placa sozinho)
#       ./servidor/iniciar_b.sh enp3s0     (informa a placa manualmente)
# Ctrl+C encerra os dois servidores.
# =====================================================================

IP_SERVIDOR="192.168.10.2"
PREFIXO="24"
DOMINIO="servidor.redes"
CONEXAO="cabo-cross"
PASTA="$(cd "$(dirname "$0")" && pwd)"   # pasta servidor/ (onde está o index.html)

passo() { echo; echo "==> $1"; }
falha() { echo "ERRO: $1"; exit 1; }

# Pede a senha do sudo uma vez só, no começo
sudo -v || falha "é preciso a senha de administrador (sudo)."

# --- 1. Dependências -------------------------------------------------
passo "Verificando dependências"
command -v python3 >/dev/null || falha "python3 não encontrado."
if ! command -v dnsmasq >/dev/null; then
    echo "Instalando o dnsmasq-base (precisa de internet)..."
    sudo apt install -y dnsmasq-base || falha "não consegui instalar o dnsmasq-base. Ligue na internet e rode de novo."
fi
command -v nmcli >/dev/null || falha "nmcli (NetworkManager) não encontrado."
echo "OK"

# --- 2. Placa de rede cabeada ----------------------------------------
passo "Procurando a placa de rede cabeada"
IFACE="$1"
if [ -z "$IFACE" ]; then
    # Primeira placa do tipo "ethernet" que o NetworkManager conhece
    IFACE="$(nmcli -t -f DEVICE,TYPE device status | awk -F: '$2=="ethernet" {print $1; exit}')"
fi
[ -n "$IFACE" ] || falha "nenhuma placa cabeada encontrada. Rode: ./servidor/iniciar_b.sh NOME_DA_PLACA"
[ -d "/sys/class/net/$IFACE" ] || falha "a placa '$IFACE' não existe. Veja os nomes com: nmcli device status"
echo "Placa: $IFACE"

# --- 3. Conexão "cabo-cross" (IP fixo, sem gateway) --------------------
passo "Configurando a conexão $CONEXAO ($IP_SERVIDOR/$PREFIXO)"
CONFIG="ipv4.method manual ipv4.addresses $IP_SERVIDOR/$PREFIXO ipv6.method disabled connection.autoconnect no"
if nmcli -t -f NAME con show | grep -qx "$CONEXAO"; then
    # Já existe: só garante que está com a placa e o IP certos
    sudo nmcli con mod "$CONEXAO" connection.interface-name "$IFACE" $CONFIG || falha "não consegui atualizar a conexão."
else
    sudo nmcli con add type ethernet ifname "$IFACE" con-name "$CONEXAO" $CONFIG >/dev/null || falha "não consegui criar a conexão."
fi
echo "OK"

# --- 4. Espera o cabo e ativa ----------------------------------------
passo "Verificando o cabo"
sudo ip link set "$IFACE" up
for i in $(seq 1 30); do
    [ "$(cat "/sys/class/net/$IFACE/carrier" 2>/dev/null)" = "1" ] && break
    [ "$i" -eq 1 ] && echo "Sem sinal no cabo. Encaixe o cabo firme nas duas máquinas (esperando até 30 s)..."
    sleep 1
done
[ "$(cat "/sys/class/net/$IFACE/carrier" 2>/dev/null)" = "1" ] || falha "o cabo não foi detectado em $IFACE (NO-CARRIER)."
sudo nmcli con up "$CONEXAO" >/dev/null || falha "não consegui ativar a conexão $CONEXAO."
ip -4 addr show "$IFACE" | grep -q "$IP_SERVIDOR" || falha "a placa não ficou com o IP $IP_SERVIDOR."
echo "Cabo OK, IP $IP_SERVIDOR ativo em $IFACE"

# --- 5. Firewall -------------------------------------------------------
passo "Verificando o firewall"
if command -v ufw >/dev/null && sudo ufw status | grep -qiE "^(status|estado): *(active|ativo)"; then
    sudo ufw allow 80/tcp >/dev/null
    sudo ufw allow 53/udp >/dev/null
    echo "ufw ativo: portas 80/tcp e 53/udp liberadas"
else
    echo "ufw desativado, nada a fazer"
fi

# --- 6. Limpa servidores que tenham ficado abertos de outra vez ---------
# (o "[h]" e o "[d]" evitam que o pkill encontre a si mesmo)
sudo pkill -f "[h]ttp.server 80" 2>/dev/null
sudo pkill -f "[d]nsmasq.*host-record=$DOMINIO" 2>/dev/null
if systemctl is-active --quiet dnsmasq 2>/dev/null; then
    echo "Parando o serviço dnsmasq do sistema (ele ocupa a porta 53)..."
    sudo systemctl stop dnsmasq
fi
sleep 1

# --- 7. Sobe os servidores ---------------------------------------------
passo "Iniciando os servidores"
sudo python3 -m http.server 80 --directory "$PASTA" &
PID_HTTP=$!

# --local=/redes/: o dnsmasq é o "dono" do domínio .redes
#   -> nome inexistente responde NXDOMAIN; consulta IPv6 (AAAA) volta vazia
sudo dnsmasq --no-daemon --no-resolv --no-hosts --bind-interfaces \
    --listen-address="$IP_SERVIDOR" \
    --local=/redes/ \
    --host-record="$DOMINIO,$IP_SERVIDOR" \
    --log-queries &
PID_DNS=$!

encerrar() {
    echo; echo "Encerrando os servidores..."
    sudo kill "$PID_HTTP" "$PID_DNS" 2>/dev/null
    sudo pkill -f "[h]ttp.server 80" 2>/dev/null
    sudo pkill -f "[d]nsmasq.*host-record=$DOMINIO" 2>/dev/null
    echo "Pronto. Para voltar à internet: religue o cabo no roteador e rode"
    echo "  sudo nmcli con up NOME_DA_CONEXAO_DE_INTERNET   (veja o nome com: nmcli con show)"
    exit 0
}
trap encerrar INT TERM

sleep 2
echo
echo "================================================================"
echo " MÁQUINA B PRONTA"
echo "   Placa:  $IFACE    IP: $IP_SERVIDOR"
echo "   HTTP:   http://$IP_SERVIDOR/   (porta 80/TCP)"
echo "   DNS:    $DOMINIO -> $IP_SERVIDOR   (porta 53/UDP)"
echo "   Os acessos da máquina A aparecem abaixo. Ctrl+C para encerrar."
echo "================================================================"
wait
