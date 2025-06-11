#!/bin/bash

# Forzar ejecución con bash si no se está usando bash
if [ -z "$BASH_VERSION" ]; then
    exec /bin/bash "$0" "$@"
fi

clear

SERVER_IP="192.168.100.1"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RAND_ID=$(LC_CTYPE=C tr -dc 'a-z0-9' < /dev/urandom | head -c 6)
REPORTS_DIR="reports"
OUTPUT_DIR="$REPORTS_DIR/test_red_${TIMESTAMP}_${RAND_ID}"

OPEN_HTML=false
INTERFACE=""
INTERFACE_IP=""

# Valores por defecto para ping
PING_RETRIES=3
PING_WAIT=2

# Crear carpeta reports si no existe
mkdir -p "$REPORTS_DIR"

# Procesar argumentos
while [[ $# -gt 0 ]]; do
    case "$1" in
        --open-html|-O)
            OPEN_HTML=true
            shift
            ;;
        --interface|-i)
            INTERFACE="$2"
            if [[ -z "$INTERFACE" ]]; then
                echo "❗ Debes especificar una interfaz después de --interface o -i"
                exit 1
            fi
            if command -v ip &>/dev/null; then
                INTERFACE_IP=$(ip -o -4 addr show "$INTERFACE" 2>/dev/null | awk '{print $4}' | cut -d/ -f1)
            else
                INTERFACE_IP=$(ifconfig "$INTERFACE" 2>/dev/null | awk '/inet / {print $2}')
            fi
            if [[ -z "$INTERFACE_IP" ]]; then
                echo "❗ No se pudo obtener la IP para la interfaz '$INTERFACE'"
                exit 1
            fi
            shift 2
            ;;
        --ping-retries)
            PING_RETRIES="$2"
            shift 2
            ;;
        --ping-wait)
            PING_WAIT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Uso: $0 [opciones]"
            echo ""
            echo "Opciones disponibles:"
            echo "  --open-html, -O      Abre automáticamente el informe HTML"
            echo "  --interface, -i IFACE Usa la interfaz de red especificada (ej: eth0)"
            echo "  --ping-retries N      Número de reintentos de ping (por defecto: 3)"
            echo "  --ping-wait SEG      Segundos de espera entre reintentos de ping (por defecto: 2)"
            echo "  --help, -h           Muestra esta ayuda"
            exit 0
            ;;
        *)
            echo "❗ Argumento no reconocido: $1"
            echo "Usa --help para ver las opciones disponibles."
            exit 1
            ;;
    esac

done

# Validar conectividad con ping con reintentos
success=false
for ((i=1; i<=PING_RETRIES; i++)); do
    if ping -c 1 -W 1 -S "$INTERFACE_IP" "$SERVER_IP" &>/dev/null; then
        success=true
        break
    else
        echo "❗ Intento $i: No se puede alcanzar el servidor $SERVER_IP desde $INTERFACE ($INTERFACE_IP)"
        if [[ $i -lt $PING_RETRIES ]]; then
            sleep $PING_WAIT
        fi
    fi

done
if ! $success; then
    echo "❗ No se pudo establecer conectividad tras $PING_RETRIES intentos. Abortando."
    exit 1
fi

echo "✅ Conectividad con $SERVER_IP desde $INTERFACE ($INTERFACE_IP) verificada."

# Solo crear carpeta y archivos si el ping fue exitoso
mkdir -p "$OUTPUT_DIR"

LOG_FILE="${OUTPUT_DIR}/speedtest.log"
SUMMARY_FILE="${OUTPUT_DIR}/resumen.txt"
CSV_FILE="${OUTPUT_DIR}/resumen.csv"
HTML_FILE="${OUTPUT_DIR}/informe.html"

SCRIPT_VERSION="5.0"

echo -e "\n"
echo "==============================="
echo "  NetworkSpeedtest.sh v$SCRIPT_VERSION"
echo "  Script de pruebas de red"
echo "==============================="

run_test() {
    local label="$1"
    local command="$2"

    # Mostrar nombre del test en consola en una línea separada
    echo -e "\n" | tee -a "$LOG_FILE"
    echo -e "\n ▶️ \t $label" | tee -a "$LOG_FILE"
    echo "------------------------------------" | tee -a "$LOG_FILE"
    echo "$2" | tee -a "$LOG_FILE"
    { command time -p bash -c "$2"; } 2>&1 | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
}

# Iniciar contador de tiempo total
SECONDS=0

# Función de barra de progreso
show_progress() {
    local current=$1
    local total=$2
    local width=30
    local percent=$(( 100 * current / total ))
    local filled=$(( width * current / total ))
    local empty=$(( width - filled ))
    local bar=""
    for ((i=0; i<filled; i++)); do bar+="█"; done
    for ((i=0; i<empty; i++)); do bar+=" "; done
    printf "\rProgreso: [%s] %d%% (%d/%d)" "$bar" "$percent" "$current" "$total"
    if [[ $current -eq $total ]]; then
        echo ""
    fi
}

# Definir número de pasos totales (ping + 5 tests iperf3)
TOTAL_STEPS=6
STEP=1

# Mostrar barra al inicio (0%)
echo -e "\n " | tee -a "$LOG_FILE"
show_progress 0 $TOTAL_STEPS

# Ping
echo -e "\n " | tee -a "$LOG_FILE"
echo -e "\n ▶️ \t Ping al servidor ($SERVER_IP)" | tee -a "$LOG_FILE"
ping_output=$(ping -c 10 -S "$INTERFACE_IP" "$SERVER_IP")
echo "$ping_output" | tee -a "$LOG_FILE"
# Extraer latencia promedio compatible con Linux y macOS
encontrado=false
avg_rtt=$(echo "$ping_output" | awk -F'/' '/rtt/ { print $5 }')
if [[ -z "$avg_rtt" ]]; then
    avg_rtt=$(echo "$ping_output" | awk -F'/' '/round-trip/ { print $5 }')
fi
if [[ -z "$avg_rtt" ]]; then
    avg_rtt="N/A"
fi
echo "📶 Latencia promedio: ${avg_rtt} ms" | tee -a "$LOG_FILE"
echo "" | tee -a "$LOG_FILE"
show_progress $STEP $TOTAL_STEPS
STEP=$((STEP+1))

# iperf3 tests
run_test "TCP básico" "iperf3 -c $SERVER_IP -B $INTERFACE_IP"
show_progress $STEP $TOTAL_STEPS
STEP=$((STEP+1))
run_test "TCP prolongado" "iperf3 -c $SERVER_IP -t 30 -B $INTERFACE_IP"
show_progress $STEP $TOTAL_STEPS
STEP=$((STEP+1))
run_test "TCP múltiples flujos" "iperf3 -c $SERVER_IP -P 4 -B $INTERFACE_IP"
show_progress $STEP $TOTAL_STEPS
STEP=$((STEP+1))
run_test "TCP bidireccional" "iperf3 -c $SERVER_IP --bidir -B $INTERFACE_IP"
show_progress $STEP $TOTAL_STEPS
STEP=$((STEP+1))
run_test "UDP 2.5G" "iperf3 -c $SERVER_IP -u -b 2.5G -t 10 --get-server-output -B $INTERFACE_IP"
show_progress $STEP $TOTAL_STEPS
STEP=$((STEP+1))

# CSV
#echo "Prueba,Envío (TX) Gbps,Recepción (RX) Gbps" > "$CSV_FILE"

# --- ELIMINADO: extract_and_save y llamadas ---
#extract_and_save() {
#    ...
#}
#extract_and_save "TCP básico" "▶️ TCP básico"
#extract_and_save "TCP prolongado" "▶️ TCP prolongado"
#extract_and_save "TCP múltiples flujos" "▶️ TCP múltiples flujos"
#extract_and_save "TCP bidireccional" "▶️ TCP bidireccional"
#extract_and_save "UDP 2.5G" "▶️ UDP 2.5G"

# --- ELIMINADO: UDP Loss y generación manual de resumenes ---
#udp_loss_line=$(awk '/▶️ UDP 2.5G/,/receiver/ { if (/receiver/ && /datagrams/) print }' "$LOG_FILE" | head -n1)
#if [[ -n "$udp_loss_line" ]]; then
#    # Extraer perdidos y totales del receiver
#    lost=$(echo "$udp_loss_line" | sed -n 's/.* \([0-9]+\)\/[0-9]+ (\([0-9.]*\)%).*/\1/p')
#    total=$(echo "$udp_loss_line" | sed -n 's/.*\/[0-9]+ (\([0-9.]*\)%).*/\1/p')
#    percent=$(echo "$udp_loss_line" | sed -n 's/.*(\([0-9.]*\)%).*/\1/p')
#    # Si no se pudo extraer, usar método alternativo
#    if [[ -z "$percent" ]]; then
#        # Buscar la forma X/Y (Z%)
#        percent=$(echo "$udp_loss_line" | sed -n 's/.*(\([0-9.]*\)%).*/\1/p')
#    fi
#    if [[ -n "$percent" ]]; then
#        udp_loss="$percent%"
#    else
#        udp_loss="N/A"
#    fi
#else
#    udp_loss="N/A"
#fi

# Generar informes con Python (CSV, TXT, HTML con gráficos)
python3 "$PWD/parse_iperf_report.py" "$LOG_FILE" "$OUTPUT_DIR"
python3 "$PWD/parse_iperf_report_html.py" "$LOG_FILE" "$OUTPUT_DIR" "$SERVER_IP" "$INTERFACE" "$INTERFACE_IP"

# Mostrar rutas de los informes generados
echo "✅ Resumen TXT: $OUTPUT_DIR/resumen.txt"
echo "✅ Resumen CSV: $OUTPUT_DIR/resumen.csv"
echo "✅ Informe HTML: $OUTPUT_DIR/informe.html"

# Abrir automáticamente el informe en macOS
if [[ "$OSTYPE" == "darwin"* && "$OPEN_HTML" == true ]]; then
    open "$OUTPUT_DIR/informe.html"
fi

# Mostrar tiempo total al final
total_time=${SECONDS:-0}
mins=$((total_time/60))
secs=$((total_time%60))
printf $'⏱️  Tiempo total: %dm %ds (%d segundos)\n' "$mins" "$secs" "$total_time"
