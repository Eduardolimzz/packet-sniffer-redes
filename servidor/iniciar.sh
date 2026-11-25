#!/bin/bash
# Sobe o servidor HTTP na porta 80, servindo os arquivos desta pasta (index.html).
# Porta 80 é "privilegiada" no Linux, por isso o sudo.
# Uso: ./iniciar.sh   (Ctrl+C para parar)

cd "$(dirname "$0")"
echo "Servidor HTTP na porta 80 (pasta: $(pwd)). Ctrl+C para parar."
sudo python3 -m http.server 80
