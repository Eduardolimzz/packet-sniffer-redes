# Roteiro da demonstração

- **Máquina A** (cliente, Windows): `192.168.10.1/24`, interface `"Ethernet"`. Roda o sniffer e o Wireshark.
- **Máquina B** (servidor, Ubuntu): `192.168.10.2/24`, interface tipo `enp2s0` (confira com `ip link`).

Ordem: preparação → item 1 → item 3 → item 2 → item 4 → item 5 → encerramento.

---

## 0. Preparação (antes de chamar o professor)

### Máquina B (Ubuntu)

```bash
# Descobrir o nome da interface do cabo (ex.: enp2s0)
ip link

# Criar o perfil do cabo (só na primeira vez; troque enp2s0 pelo nome certo)
sudo nmcli con add type ethernet ifname enp2s0 con-name cabo-cross ipv4.method manual ipv4.addresses 192.168.10.2/24 ipv6.method disabled connection.autoconnect no

# Ativar e conferir
sudo nmcli con up cabo-cross
ip addr show enp2s0
```

Em dois terminais separados, dentro da pasta do repositório:

```bash
# Terminal 1: servidor HTTP
./servidor/iniciar.sh
```

```bash
# Terminal 2: servidor DNS
./servidor/iniciar_dns.sh
```

### Máquina A (Windows, PowerShell como administrador)

```powershell
New-NetIPAddress -InterfaceAlias "Ethernet" -IPAddress 192.168.10.1 -PrefixLength 24
Set-NetConnectionProfile -InterfaceAlias "Ethernet" -NetworkCategory Private

# Conferir
ipconfig
ping -n 4 192.168.10.2
curl.exe http://192.168.10.2/
nslookup servidor.redes. 192.168.10.2
```

Se tudo respondeu, o ambiente está pronto.

---

## 1. Item 1: captura em tempo real

### Máquina A (PowerShell como administrador, na pasta do repositório)

```powershell
python sniffer\main.py --listar
python sniffer\main.py --iface "Ethernet"
```

Ao mesmo tempo, abrir o **Wireshark** na interface "Ethernet", com o filtro de **captura** (antes de iniciar):

```
tcp port 80 or udp port 53
```

Falar: o sniffer usa o mesmo filtro BPF; `store=False` evita acumular pacotes na memória; o total será comparado no final.

---

## 2. Item 3: DNS (UDP/53)

### Máquina A (outro PowerShell)

```powershell
nslookup servidor.redes. 192.168.10.2
```

O ponto final em `servidor.redes.` evita que o Windows acrescente o sufixo da rede Wi-Fi (ex.: `.iesb.br`).
Para mostrar uma resposta com erro:

```powershell
nslookup naoexiste.redes. 192.168.10.2
```

No sniffer aparecem linhas `[DNS]`. Filtro de exibição no Wireshark:

```
dns && udp.port == 53
```

---

## 3. Item 2: HTTP (TCP/80)

### Máquina A

```powershell
curl.exe http://192.168.10.2/
```

No sniffer aparecem linhas `[HTTP]` (requisição e resposta). Filtros de exibição no Wireshark:

```
http
```

```
tcp.port == 80
```

Mostrar que o `ping -n 4 192.168.10.2` **não** aparece no sniffer (não é porta 80 nem 53).

---

## 4. Item 4: IPs e portas (camadas 3 e 4)

Apontar numa linha do sniffer:

```
[HTTP] 192.168.10.1:50123     -> 192.168.10.2:80       | GET / (Host: 192.168.10.2)
[HTTP] 192.168.10.2:80        -> 192.168.10.1:50123    | Resposta: HTTP/1.0 200 OK
```

- `192.168.10.1` → `192.168.10.2`: IPs de origem e destino (camada 3).
- Porta alta aleatória do cliente → porta 80 (ou 53) do servidor (camada 4); na resposta, invertido.
- Conferir os mesmos valores num pacote do Wireshark (filtro `tcp.port == 80 || udp.port == 53`).

---

## 5. Item 5: método HTTP e domínio DNS

### Máquina A

```powershell
curl.exe http://192.168.10.2/
curl.exe -X POST http://192.168.10.2/ -d "teste=123"
nslookup servidor.redes. 192.168.10.2
```

Mostrar no sniffer:

- `GET / (Host: 192.168.10.2)`
- `POST / (Host: 192.168.10.2)`. O servidor responde `501 Unsupported method`, é esperado: o que importa é o POST ter sido capturado e decodificado.
- `Consulta DNS: servidor.redes [A]` e `Resposta DNS: servidor.redes [A] -> 192.168.10.2`.

---

## 6. Encerramento

1. No sniffer, **Ctrl+C**. Aparece `Total de pacotes capturados: N`.
2. No Wireshark, parar a captura e ver o total na barra de status ("Displayed"/"Packets", sem filtro de exibição).
3. Os dois números devem ser iguais (os dois usaram `tcp port 80 or udp port 53`).

Na máquina B: Ctrl+C nos dois servidores e, se quiser, `sudo nmcli con down cabo-cross`.

---

## Plano B: tudo pelo Wireshark

Se o sniffer falhar, demonstrar cada item no Wireshark (interface "Ethernet", filtro de captura `tcp port 80 or udp port 53`):

| Item | Como mostrar no Wireshark |
|------|---------------------------|
| 1 | Captura rodando ao vivo enquanto os comandos são executados |
| 2 | Filtro `tcp.port == 80` e depois `http` |
| 3 | Filtro `dns && udp.port == 53` |
| 4 | Selecionar um pacote → "Internet Protocol" (Src/Dst) e "TCP"/"UDP" (Src Port/Dst Port) |
| 5 | Filtro `http`: coluna Info mostra `GET /` e `POST /`; filtro `dns`: Info mostra `Standard query A servidor.redes` |

Filtro com tudo: `tcp.port == 80 || udp.port == 53`.

---

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| Ubuntu: `NO-CARRIER` em `ip link`; Windows: "Disconnected"/"Cabo de rede desconectado" | Cabo mal encaixado ou com defeito | Reencaixar ou trocar o cabo; conferir a luz da porta |
| Windows com IP `169.254.x.x` | IP fixo não foi configurado (é o IP automático APIPA) | Rodar `New-NetIPAddress ...` de novo, como administrador |
| `ping` não responde, mas o cabo está ok | Firewall do Windows bloqueando | Rede como `Private` (`Set-NetConnectionProfile`) e permitir Python/ICMP no firewall |
| `ping -c 4` dá erro no Windows | No Windows o número de pacotes é `-n` | `ping -n 4 192.168.10.2` |
| `curl` no PowerShell mostra um objeto estranho/pede parâmetros | `curl` no PowerShell é um apelido de `Invoke-WebRequest` | Usar `curl.exe` |
| `nslookup` procura `servidor.redes.iesb.br` | Windows acrescenta o sufixo DNS da rede Wi-Fi | Usar ponto final: `servidor.redes.` |
| `nslookup` dá "Refused" ou "timed out" | dnsmasq não está rodando ou escutando em outro IP | Conferir o terminal do `iniciar_dns.sh` e o IP da máquina B |
| Ubuntu: "libpcap is not available" | Falta a libpcap (o filtro BPF depende dela) | `sudo apt install tcpdump` (ou wireshark) |
| Windows: sniffer não captura nada | Npcap não instalado ou terminal sem administrador | Instalar o Npcap (vem com o Wireshark) e abrir como administrador |
| `iniciar.sh`: "Address already in use" | Já existe algo na porta 80 | Fechar o outro servidor (`sudo ss -ltnp | grep :80`) |
