# packet-sniffer-redes

Sniffer de pacotes em Python (Scapy) que captura em tempo real o tráfego HTTP e DNS entre duas máquinas, exibindo IPs, portas, métodos HTTP e domínios consultados. Trabalho da disciplina de Redes de Computadores. Compatível com Ubuntu e Windows.

## Instalação

### Ubuntu

```bash
sudo apt update
sudo apt install wireshark python3-scapy python3-rich
sudo usermod -aG wireshark $USER   # depois, sair da sessão e entrar de novo
```

Prefira o `apt`: nas versões recentes do Ubuntu, `pip install` fora de um ambiente virtual dá o erro "externally-managed-environment". Se usar venv, rode o sniffer com `sudo venv/bin/python`, porque `sudo python3` ignora o venv.

### Windows

1. Instale o Python (python.org), marcando **"Add Python to PATH"**.
2. Instale o Wireshark (wireshark.org), aceitando instalar o **Npcap** junto. Sem o Npcap, o Scapy não captura.
3. No terminal: `pip install -r requirements.txt`

## Execução

Primeiro descubra o nome da interface de rede (Wi-Fi):

```bash
python3 sniffer/main.py --listar          # Ubuntu
python sniffer\main.py --listar           # Windows
```

Depois inicie a captura com essa interface:

| Sistema                               | Comando                                         |
| ------------------------------------- | ----------------------------------------------- |
| Ubuntu                                | `sudo python3 sniffer/main.py --iface wlp2s0` |
| Windows (terminal como administrador) | `python sniffer\main.py --iface "Wi-Fi"`      |

Pare com **Ctrl+C**. O sniffer mostra o total de pacotes capturados. Para comparar com o Wireshark, use nele o mesmo filtro de captura: `tcp port 80 or udp port 53`.
