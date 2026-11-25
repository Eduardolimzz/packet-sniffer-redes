#!/bin/bash
# Sobe um servidor DNS (dnsmasq) que responde só pelo domínio inventado
# "servidor.redes" -> IP desta máquina. Não usa internet nem /etc/hosts.
# Instalar antes: sudo apt install dnsmasq
# Uso: ./iniciar_dns.sh   (Ctrl+C para parar)

# IP desta máquina (B) no cabo de rede
IP_SERVIDOR="192.168.10.2"
DOMINIO="servidor.redes"

echo "DNS em $IP_SERVIDOR:53 respondendo $DOMINIO -> $IP_SERVIDOR. Ctrl+C para parar."
sudo dnsmasq --no-daemon --no-resolv --no-hosts --bind-interfaces \
    --listen-address="$IP_SERVIDOR" \
    --host-record="$DOMINIO,$IP_SERVIDOR" \
    --log-queries
