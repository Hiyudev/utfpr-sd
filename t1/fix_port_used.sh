#!/bin/bash
# Script elaborado para eliminar todos os processos que estejam utilizando as portas definidas pela variável "PORTS".
# O objetivo deste script é contornar o problema do Docker, onde os containeres não são desligados/eliminados corretamente
PORTS=(15672 5672)

for PORT in "${PORTS[@]}"; do
    echo "Checking port $PORT..."
    
    # Get PIDs using lsof and kill them
    PIDS=$(sudo lsof -t -i tcp:$PORT)

    if [ -n "$PIDS" ]; then
        echo "Killing processes on port $PORT: $PIDS"
        sudo kill $PIDS
    else
        echo "No process found on port $PORT."
    fi
done