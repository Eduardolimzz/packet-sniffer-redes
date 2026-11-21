from scapy.all import IP, UDP, DNS, DNSRR, sniff


def analisar_dns(pkt, callback_exibir=None):
    """
    Analisa pacotes UDP na porta 53 e extrai o domínio consultado
    e eventuais respostas de endereço IP (registro A).
    """
    if not (pkt.haslayer(IP) and pkt.haslayer(UDP) and pkt.haslayer(DNS)):
        return None

    porta_origem = pkt[UDP].sport
    porta_destino = pkt[UDP].dport

    if porta_origem != 53 and porta_destino != 53:
        return None

    ip_origem = pkt[IP].src
    ip_destino = pkt[IP].dst
    camada_dns = pkt[DNS]

    # Extrai o domínio da seção de pergunta (qd)
    dominio = "desconhecido"
    if camada_dns.qd and camada_dns.qd.qname:
        dominio = camada_dns.qd.qname.decode("utf-8", errors="ignore").rstrip(".")

    # qr == 0 indica Consulta (Query); qr == 1 indica Resposta (Response)
    if camada_dns.qr == 0:
        info = f"Consulta DNS: {dominio}"
    else:
        ips_resolvidos = []
        for i in range(camada_dns.ancount):
            resposta = camada_dns.an[i]
            if isinstance(resposta, DNSRR) and resposta.type == 1:  # Registro A (IPv4)
                ips_resolvidos.append(str(resposta.rdata))

        if ips_resolvidos:
            info = f"Resposta DNS: {dominio} -> {', '.join(ips_resolvidos)}"
        else:
            info = f"Resposta DNS: {dominio}"

    resultado = {
        "protocolo": "DNS",
        "ip_origem": ip_origem,
        "porta_origem": porta_origem,
        "ip_destino": ip_destino,
        "porta_destino": porta_destino,
        "info": info,
    }

    if callback_exibir:
        callback_exibir(**resultado)

    return resultado


if __name__ == "__main__":
    # Teste isolado do módulo: sudo python3 sniffer/dns_parser.py
    def exibir_teste(protocolo, ip_origem, porta_origem, ip_destino, porta_destino, info):
        print(f"[{protocolo}] {ip_origem}:{porta_origem} -> {ip_destino}:{porta_destino} | {info}")

    print("Escutando tráfego DNS (porta 53)... Ctrl+C para sair.")
    sniff(filter="udp port 53", prn=lambda p: analisar_dns(p, exibir_teste), store=False)