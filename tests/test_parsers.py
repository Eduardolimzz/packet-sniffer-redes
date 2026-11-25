"""
Testes dos parsers HTTP e DNS, sem root e sem rede.

Cada teste monta um pacote falso com o Scapy, converte para bytes e de volta
(Ether(bytes(pkt))) para simular um pacote vindo da rede, e confere o
dicionário devolvido pelo parser.

Rodar: python3 -m pytest
"""

import os
import sys

# Permite importar os módulos da pasta sniffer/ (o main.py importa do mesmo jeito)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "sniffer"))

from scapy import VERSION  # noqa: E402
from scapy.all import DNS, DNSQR, DNSRR, IP, TCP, UDP, Ether, Raw  # noqa: E402

from dns_parser import analisar_dns  # noqa: E402
from http_parser import analisar_http  # noqa: E402

CLIENTE = "192.168.10.1"
SERVIDOR = "192.168.10.2"


def da_rede(pkt):
    """Simula um pacote capturado: vira bytes e é decodificado de novo."""
    return Ether(bytes(pkt))


def pacote_http(payload, sport=50123, dport=80, src=CLIENTE, dst=SERVIDOR):
    return da_rede(Ether() / IP(src=src, dst=dst) / TCP(sport=sport, dport=dport, flags="PA") / Raw(payload))


def varios_registros(*registros):
    """
    Monta o campo DNS.an com vários registros.
    Scapy 2.6 ou mais novo: lista. Scapy 2.5: registros encadeados com "/".
    """
    versao = tuple(int(x) for x in VERSION.split(".")[:2])
    if versao >= (2, 6):
        return list(registros)
    encadeado = registros[0]
    for registro in registros[1:]:
        encadeado = encadeado / registro
    return encadeado


def pacote_dns(dns, sport=50000, dport=53, src=CLIENTE, dst=SERVIDOR):
    return da_rede(Ether() / IP(src=src, dst=dst) / UDP(sport=sport, dport=dport) / dns)


# ---------- HTTP ----------

def test_http_get():
    pkt = pacote_http(b"GET /index.html HTTP/1.1\r\nHost: 192.168.10.2\r\nUser-Agent: curl\r\n\r\n")
    assert analisar_http(pkt) == {
        "protocolo": "HTTP",
        "ip_origem": CLIENTE,
        "porta_origem": 50123,
        "ip_destino": SERVIDOR,
        "porta_destino": 80,
        "info": "GET /index.html (Host: 192.168.10.2)",
    }


def test_http_post():
    pkt = pacote_http(
        b"POST / HTTP/1.1\r\nHost: 192.168.10.2\r\nContent-Length: 9\r\n\r\nteste=123"
    )
    assert analisar_http(pkt)["info"] == "POST / (Host: 192.168.10.2)"


def test_http_outros_metodos():
    for metodo in ["PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"]:
        pkt = pacote_http(f"{metodo} /x HTTP/1.1\r\nHost: b\r\n\r\n".encode())
        assert analisar_http(pkt)["info"] == f"{metodo} /x (Host: b)"


def test_http_resposta_200():
    pkt = pacote_http(
        b"HTTP/1.0 200 OK\r\nServer: SimpleHTTP\r\n\r\n<html>",
        sport=80, dport=50123, src=SERVIDOR, dst=CLIENTE,
    )
    resultado = analisar_http(pkt)
    assert resultado["info"] == "Resposta: HTTP/1.0 200 OK"
    assert resultado["ip_origem"] == SERVIDOR
    assert resultado["porta_origem"] == 80
    assert resultado["porta_destino"] == 50123


def test_http_syn_sem_payload_e_ignorado():
    pkt = da_rede(Ether() / IP(src=CLIENTE, dst=SERVIDOR) / TCP(sport=50123, dport=80, flags="S"))
    assert analisar_http(pkt) is None


def test_http_porta_diferente_e_ignorado():
    pkt = pacote_http(b"GET / HTTP/1.1\r\n\r\n", dport=8080)
    assert analisar_http(pkt) is None


def test_http_chama_callback():
    recebidos = []
    pkt = pacote_http(b"GET / HTTP/1.1\r\nHost: b\r\n\r\n")
    resultado = analisar_http(pkt, lambda **campos: recebidos.append(campos))
    assert recebidos == [resultado]


# ---------- DNS ----------

def test_dns_consulta():
    pkt = pacote_dns(DNS(id=1, rd=1, qd=DNSQR(qname="servidor.redes", qtype="A")))
    assert analisar_dns(pkt) == {
        "protocolo": "DNS",
        "ip_origem": CLIENTE,
        "porta_origem": 50000,
        "ip_destino": SERVIDOR,
        "porta_destino": 53,
        "info": "Consulta DNS: servidor.redes [A]",
    }


def test_dns_consulta_aaaa():
    pkt = pacote_dns(DNS(id=1, rd=1, qd=DNSQR(qname="servidor.redes", qtype="AAAA")))
    assert analisar_dns(pkt)["info"] == "Consulta DNS: servidor.redes [AAAA]"


def test_dns_resposta_um_registro():
    dns = DNS(
        id=1, qr=1, aa=1, rd=1, ra=1,
        qd=DNSQR(qname="servidor.redes", qtype="A"),
        an=DNSRR(rrname="servidor.redes", type="A", rdata=SERVIDOR),
    )
    pkt = pacote_dns(dns, sport=53, dport=50000, src=SERVIDOR, dst=CLIENTE)
    resultado = analisar_dns(pkt)
    assert resultado["info"] == "Resposta DNS: servidor.redes [A] -> 192.168.10.2"
    assert resultado["porta_origem"] == 53


def test_dns_resposta_dois_registros():
    dns = DNS(
        id=1, qr=1, rd=1, ra=1,
        qd=DNSQR(qname="servidor.redes", qtype="A"),
        an=varios_registros(
            DNSRR(rrname="servidor.redes", type="A", rdata="10.0.0.1"),
            DNSRR(rrname="servidor.redes", type="A", rdata="10.0.0.2"),
        ),
    )
    pkt = pacote_dns(dns, sport=53, dport=50000, src=SERVIDOR, dst=CLIENTE)
    assert analisar_dns(pkt)["info"] == "Resposta DNS: servidor.redes [A] -> 10.0.0.1, 10.0.0.2"


def test_dns_resposta_refused():
    dns = DNS(id=1, qr=1, rd=1, rcode=5, qd=DNSQR(qname="x.iesb.br", qtype="A"))
    pkt = pacote_dns(dns, sport=53, dport=50000, src=SERVIDOR, dst=CLIENTE)
    assert analisar_dns(pkt)["info"] == "Resposta DNS: x.iesb.br [A] (Refused)"


def test_dns_resposta_nxdomain():
    dns = DNS(id=1, qr=1, rd=1, rcode=3, qd=DNSQR(qname="naoexiste.redes", qtype="A"))
    pkt = pacote_dns(dns, sport=53, dport=50000, src=SERVIDOR, dst=CLIENTE)
    assert analisar_dns(pkt)["info"] == "Resposta DNS: naoexiste.redes [A] (NXDOMAIN)"


def test_dns_ignora_http():
    pkt = pacote_http(b"GET / HTTP/1.1\r\n\r\n")
    assert analisar_dns(pkt) is None


# ---------- Exibição ----------

def test_exibicao_formato(capsys):
    from exibicao import exibir
    exibir(protocolo="DNS", ip_origem=CLIENTE, porta_origem=50000,
           ip_destino=SERVIDOR, porta_destino=53, info="Consulta DNS: servidor.redes [A]")
    saida = capsys.readouterr().out
    assert "192.168.10.1:50000" in saida
    assert "-> 192.168.10.2:53" in saida
    assert "| Consulta DNS: servidor.redes [A]" in saida
