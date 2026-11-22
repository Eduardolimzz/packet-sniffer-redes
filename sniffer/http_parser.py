from scapy.all import IP, TCP, Raw, sniff


def analisar_http(pkt, callback_exibir=None):
    """
    Analisa pacotes TCP na porta 80 e extrai método/caminho/Host (GET/POST)
    ou status da resposta HTTP.
    """
    if not (pkt.haslayer(IP) and pkt.haslayer(TCP) and pkt.haslayer(Raw)):
        return None

    porta_origem = pkt[TCP].sport
    porta_destino = pkt[TCP].dport

    if porta_origem != 80 and porta_destino != 80:
        return None

    ip_origem = pkt[IP].src
    ip_destino = pkt[IP].dst

    payload = pkt[Raw].load.decode("utf-8", errors="ignore")
    linhas = payload.split("\r\n")
    if not linhas or not linhas[0]:
        return None

    primeira_linha = linhas[0].strip()
    info = None

    # Requisição HTTP (Cliente -> Servidor)
    if primeira_linha.startswith(("GET ", "POST ")):
        partes = primeira_linha.split(" ")
        metodo = partes[0]
        caminho = partes[1] if len(partes) > 1 else "/"
        info = f"{metodo} {caminho}"

        # Cabeçalho Host (as linhas do cabeçalho vêm depois da primeira linha)
        for linha in linhas[1:]:
            if linha.lower().startswith("host:"):
                info += f" (Host: {linha[5:].strip()})"
                break

    # Resposta HTTP (Servidor -> Cliente)
    elif primeira_linha.startswith("HTTP/"):
        info = f"Resposta: {primeira_linha}"

    if not info:
        return None

    resultado = {
        "protocolo": "HTTP",
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
    # Teste isolado do módulo: sudo python3 sniffer/http_parser.py
    def exibir_teste(protocolo, ip_origem, porta_origem, ip_destino, porta_destino, info):
        print(f"[{protocolo}] {ip_origem}:{porta_origem} -> {ip_destino}:{porta_destino} | {info}")

    print("Escutando tráfego HTTP (porta 80)... Ctrl+C para sair.")
    sniff(filter="tcp port 80", prn=lambda p: analisar_http(p, exibir_teste), store=False)