"""
Item 4: exibição padronizada dos pacotes reconhecidos.

Formato de cada linha:
    [PROTOCOLO] IP_ORIGEM:PORTA -> IP_DESTINO:PORTA | info

Usa a biblioteca "rich" para colorir (HTTP em verde, DNS em ciano).
Se a rich não estiver instalada, usa um print simples no mesmo formato.
"""

try:
    from rich.console import Console
    from rich.markup import escape

    console = Console(highlight=False)  # highlight=False: a rich não colore números/IPs sozinha
except ImportError:
    console = None

# Cor de cada protocolo (nomes de cores da rich)
CORES = {
    "HTTP": "bold green",
    "DNS": "bold cyan",
}

# Larguras das colunas, para que as linhas fiquem alinhadas.
# "255.255.255.255:65535" tem 21 caracteres.
LARGURA_PROTOCOLO = 6
LARGURA_ENDERECO = 21


def exibir(protocolo, ip_origem, porta_origem, ip_destino, porta_destino, info):
    """Mostra um pacote na tela. Os parsers chamam esta função com argumentos nomeados."""
    origem = f"{ip_origem}:{porta_origem}"
    destino = f"{ip_destino}:{porta_destino}"

    # Monta as colunas com largura fixa (:< alinha à esquerda)
    coluna_protocolo = f"[{protocolo}]".ljust(LARGURA_PROTOCOLO)
    coluna_origem = origem.ljust(LARGURA_ENDERECO)
    coluna_destino = destino.ljust(LARGURA_ENDERECO)

    if console is None:
        # Sem a rich: texto puro, mesmo formato
        print(f"{coluna_protocolo} {coluna_origem} -> {coluna_destino} | {info}")
        return

    cor = CORES.get(protocolo, "bold white")
    # escape() impede que "[" dentro do texto seja interpretado como marcação da rich
    # soft_wrap=True: a rich não quebra a linha sozinha (o terminal é que quebra, se precisar)
    console.print(
        f"[{cor}]{escape(coluna_protocolo)}[/] "
        f"[yellow]{coluna_origem}[/] -> [magenta]{coluna_destino}[/] | {escape(str(info))}",
        soft_wrap=True,
    )
