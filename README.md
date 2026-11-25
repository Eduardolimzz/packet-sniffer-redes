# packet-sniffer-redes

Sniffer de pacotes em Python (Scapy) que captura em tempo real o tráfego HTTP e DNS entre duas máquinas, exibindo IPs, portas, métodos HTTP e domínios consultados. Trabalho da disciplina de Redes de Computadores. Compatível com Ubuntu e Windows.

## Instalação

### Ubuntu

```bash
sudo apt update
sudo apt install wireshark tcpdump python3-scapy python3-rich
sudo usermod -aG wireshark $USER   # depois, sair da sessão e entrar de novo
```

No Linux, o filtro BPF usado pelo sniffer (`tcp port 80 or udp port 53`) depende da **libpcap**, que é instalada junto com o Wireshark/tcpdump. Sem ela, o Scapy falha com o erro "libpcap is not available".

Prefira o `apt`: nas versões recentes do Ubuntu, `pip install` fora de um ambiente virtual dá o erro "externally-managed-environment". Se usar venv, rode o sniffer com `sudo venv/bin/python`, porque `sudo python3` ignora o venv.

### Windows

1. Instale o Python (python.org), marcando **"Add Python to PATH"**.
2. Instale o Wireshark (wireshark.org), aceitando instalar o **Npcap** junto. Sem o Npcap, o Scapy não captura.
3. No terminal: `pip install -r requirements.txt`

## Execução

Primeiro descubra o nome da interface de rede do cabo (Ethernet):

```bash
python3 sniffer/main.py --listar          # Ubuntu
python sniffer\main.py --listar           # Windows
```

Depois inicie a captura com essa interface:

| Sistema                               | Comando                                         |
| ------------------------------------- | ----------------------------------------------- |
| Ubuntu                                | `sudo python3 sniffer/main.py --iface enp2s0` |
| Windows (terminal como administrador) | `python sniffer\main.py --iface "Ethernet"`   |

Pare com **Ctrl+C**. O sniffer mostra o total de pacotes capturados. Para comparar com o Wireshark, use nele o mesmo filtro de captura: `tcp port 80 or udp port 53`.

## Ambiente com cabo de rede

As duas máquinas são ligadas por um cabo de rede direto, com IPs fixos e sem gateway:

| Máquina | Sistema | IP | Interface | Papel |
| ------- | ------- | -- | --------- | ----- |
| A | Windows | `192.168.10.1/24` | `"Ethernet"` | cliente; roda o sniffer e o Wireshark |
| B | Ubuntu | `192.168.10.2/24` | `enp2s0` (varia) | servidor HTTP (porta 80) e DNS (porta 53) |

- Scripts para subir os servidores na máquina B: pasta [`servidor/`](servidor/) (`iniciar.sh` para HTTP, `iniciar_dns.sh` para DNS com dnsmasq).
- Passo a passo da apresentação, com todos os comandos: [`docs/roteiro-demo.md`](docs/roteiro-demo.md).
- Os 5 itens avaliados e como validar cada um: [`docs/itens-escopo.md`](docs/itens-escopo.md).

## Testes

Os testes montam pacotes falsos com o Scapy e não precisam de root nem de rede:

```bash
pip install -r requirements-dev.txt
python3 -m pytest
```
