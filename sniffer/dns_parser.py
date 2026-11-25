from scapy.all import IP, UDP, DNS, DNSRR, sniff

# Nomes dos tipos de consulta mais comuns (campo qtype)
TIPOS_CONSULTA = {1: "A", 2: "NS", 5: "CNAME", 12: "PTR", 15: "MX", 16: "TXT", 28: "AAAA", 33: "SRV", 65: "HTTPS"}

# Códigos de erro da resposta (campo rcode). 0 = sem erro.
ERROS_DNS = {1: "FormErr", 2: "ServFail", 3: "NXDOMAIN", 4: "NotImp", 5: "Refused"}


def primeiro_item(campo):
    """
    Devolve o primeiro registro de DNS.qd ou DNS.an.
    No Scapy novo esses campos são listas; no Scapy 2.5 são pacotes encadeados
    (o próprio campo já é o primeiro registro).
    """
    if campo is None:
        return None
    if isinstance(campo, list):
        return campo[0] if campo else None
    return campo


def item_numero(campo, i):
    """
    Devolve o registro de número i de DNS.an.
    Lista (Scapy novo): campo[i]. Pacote encadeado (Scapy 2.5): campo[i]
    devolve a i-ésima camada da corrente. Devolve None se não existir.
    """
    try:
        return campo[i]
    except (IndexError, TypeError):
        return None


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
    tipo = ""
    pergunta = primeiro_item(camada_dns.qd)
    if pergunta is not None and pergunta.qname:
        dominio = pergunta.qname.decode("utf-8", errors="ignore").rstrip(".")
        # Tipo da consulta entre colchetes, ex.: " [A]" (só se for um tipo conhecido)
        if pergunta.qtype in TIPOS_CONSULTA:
            tipo = f" [{TIPOS_CONSULTA[pergunta.qtype]}]"

    # qr == 0 indica Consulta (Query); qr == 1 indica Resposta (Response)
    if camada_dns.qr == 0:
        info = f"Consulta DNS: {dominio}{tipo}"
    elif camada_dns.rcode != 0:
        # Resposta com erro: mostra o motivo (ex.: Refused, NXDOMAIN)
        motivo = ERROS_DNS.get(camada_dns.rcode, f"erro {camada_dns.rcode}")
        info = f"Resposta DNS: {dominio}{tipo} ({motivo})"
    else:
        ips_resolvidos = []
        for i in range(camada_dns.ancount):
            resposta = item_numero(camada_dns.an, i)
            if isinstance(resposta, DNSRR) and resposta.type == 1:  # Registro A (IPv4)
                ips_resolvidos.append(str(resposta.rdata))

        if ips_resolvidos:
            info = f"Resposta DNS: {dominio}{tipo} -> {', '.join(ips_resolvidos)}"
        else:
            info = f"Resposta DNS: {dominio}{tipo}"

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