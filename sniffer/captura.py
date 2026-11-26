"""
Item 1: captura em tempo real.

Abre a captura na interface escolhida, entrega cada pacote aos parsers
(HTTP e DNS) e conta os pacotes para comparar com o Wireshark  no final.
"""

from scapy.all import conf, sniff

# Mesmo filtro que deve ser usado como "filtro de captura" no Wireshark,
# para que os totais dos dois possam ser comparados.
FILTRO_BPF = "tcp port 80 or udp port 53"


def listar_interfaces():
    """Devolve as interfaces de rede disponíveis (funciona no Ubuntu e no Windows)."""
    interfaces = []
    for iface in conf.ifaces.values():
        interfaces.append({
            "nome": iface.name,
            "descricao": iface.description,
            "ip": iface.ip or "-",
        })
    return sorted(interfaces, key=lambda i: i["nome"])


class Captura:
    """Captura ao vivo com contagem de pacotes."""

    def __init__(self, iface, analisadores, filtro=FILTRO_BPF):
        """
        iface        -- nome da interface (ex.: "enp2s0" no Ubuntu, "Ethernet" no Windows)
        analisadores -- lista de funções que recebem o pacote e devolvem um
                        dicionário (pacote reconhecido) ou None (ignorado)
        filtro       -- filtro BPF aplicado pelo sistema antes de chegar ao Python
        """
        self.iface = iface
        self.analisadores = analisadores
        self.filtro = filtro
        self.total_pacotes = 0

    def _processar(self, pkt):
        self.total_pacotes += 1
        for analisar in self.analisadores:
            if analisar(pkt):
                break

    def iniciar(self):
        """
        Captura até o usuário apertar Ctrl+C. O próprio sniff() do Scapy
        trata o Ctrl+C e retorna normalmente, então o total sempre é exibido.
        store=False: os pacotes não ficam guardados na memória, o que evita
        que o programa fique lento (e perca pacotes) em capturas longas.
        """
        sniff(iface=self.iface, filter=self.filtro, prn=self._processar, store=False)
