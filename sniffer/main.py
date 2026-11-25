"""
Ponto de entrada do sniffer.

Ubuntu:   sudo python3 sniffer/main.py --iface enp2s0
Windows:  (terminal como administrador) python sniffer\\main.py --iface "Ethernet"
Listar:   python3 sniffer/main.py --listar
"""

import argparse

from captura import FILTRO_BPF, Captura, listar_interfaces
from dns_parser import analisar_dns
from http_parser import analisar_http

try:
    # Função padronizada da Pessoa 4 (item 4).
    from exibicao import exibir
except ImportError:
    # Enquanto o exibicao.py não existir, usa uma saída simples no mesmo formato.
    def exibir(protocolo, ip_origem, porta_origem, ip_destino, porta_destino, info):
        print(f"[{protocolo}] {ip_origem}:{porta_origem} -> {ip_destino}:{porta_destino} | {info}")


def ler_argumentos():
    parser = argparse.ArgumentParser(
        description="Sniffer de tráfego HTTP (TCP/80) e DNS (UDP/53).",
    )
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument("--iface", help="interface de captura (veja os nomes com --listar)")
    grupo.add_argument("--listar", action="store_true", help="mostra as interfaces disponíveis")
    return parser.parse_args()


def main():
    args = ler_argumentos()

    if args.listar:
        print(f"{'NOME':<20} {'IP':<16} DESCRIÇÃO")
        for iface in listar_interfaces():
            print(f"{iface['nome']:<20} {iface['ip']:<16} {iface['descricao']}")
        return

    analisadores = [
        lambda pkt: analisar_http(pkt, exibir),
        lambda pkt: analisar_dns(pkt, exibir),
    ]
    captura = Captura(args.iface, analisadores)

    print(f"Capturando na interface {args.iface} (filtro: {FILTRO_BPF}). Ctrl+C para parar.\n")
    captura.iniciar()

    print("\n--- Captura encerrada ---")
    print(f"Total de pacotes capturados: {captura.total_pacotes}")


if __name__ == "__main__":
    main()
