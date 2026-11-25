# Itens do escopo

Os 5 itens avaliados no trabalho, o que cada um significa e como provar que funciona.

| # | Item | Onde está no código |
|---|------|---------------------|
| 1 | Captura em tempo real | `sniffer/captura.py` |
| 2 | Filtragem HTTP (TCP/80) | `captura.py` (filtro BPF) + `sniffer/http_parser.py` |
| 3 | Filtragem DNS (UDP/53) | `captura.py` (filtro BPF) + `sniffer/dns_parser.py` |
| 4 | Cabeçalhos das camadas 3 e 4 | parsers + `sniffer/exibicao.py` |
| 5 | Decodificação do payload | `http_parser.py` (método) e `dns_parser.py` (domínio) |

## 1. Captura em tempo real na interface correta, sem descarte de quadros

**Descrição:** o sniffer abre a interface do cabo (`--iface`) e mostra cada pacote assim que ele chega. Usa `store=False` para não acumular pacotes na memória, e o filtro BPF é aplicado pelo sistema (libpcap/Npcap), antes do Python, reduzindo a carga.

**Critério de validação:**
- O sniffer é iniciado com a interface do cabo e as linhas aparecem no mesmo instante em que os comandos são executados na outra máquina.
- Ao final (Ctrl+C), o total de pacotes do sniffer é igual ao total do Wireshark capturando na mesma interface com o filtro de captura `tcp port 80 or udp port 53`.

## 2. Filtragem do tráfego HTTP (porta 80/TCP)

**Descrição:** só pacotes TCP com porta de origem ou destino 80 são considerados HTTP.

**Critério de validação:**
- `curl.exe http://192.168.10.2/` gera linhas `[HTTP]`.
- Tráfego em outras portas (ex.: `ping`) não aparece.
- Conferir no Wireshark com `tcp.port == 80` e `http`.

## 3. Filtragem das consultas DNS (porta 53/UDP)

**Descrição:** só pacotes UDP com porta de origem ou destino 53 são considerados DNS.

**Critério de validação:**
- `nslookup servidor.redes. 192.168.10.2` gera linhas `[DNS]` (consulta e resposta).
- Conferir no Wireshark com `dns && udp.port == 53`.

## 4. Exibição dos cabeçalhos das camadas 3 e 4

**Descrição:** para cada pacote é mostrado o IP de origem e destino (camada 3, IP) e a porta de origem e destino (camada 4, TCP/UDP), no formato `IP:porta -> IP:porta`.

**Critério de validação:**
- Requisições saem de `192.168.10.1:<porta alta>` para `192.168.10.2:80` (HTTP) ou `:53` (DNS); as respostas fazem o caminho inverso.
- Os valores batem com os campos "Source", "Destination", "Src Port" e "Dst Port" do Wireshark.

## 5. Decodificação do payload

**Descrição:** o sniffer lê o conteúdo (camada de aplicação) e mostra o método HTTP (GET, POST e outros) com o caminho e o Host, o status das respostas HTTP, e o domínio consultado no DNS (com o tipo e os IPs da resposta, ou o motivo do erro).

**Critério de validação:**
- `curl.exe http://192.168.10.2/` → `GET / (Host: 192.168.10.2)`.
- `curl.exe -X POST http://192.168.10.2/ -d "teste=123"` → `POST / (Host: 192.168.10.2)` (o servidor responde 501, o que é esperado).
- `nslookup servidor.redes. 192.168.10.2` → `Consulta DNS: servidor.redes [A]` e `Resposta DNS: servidor.redes [A] -> 192.168.10.2`.
