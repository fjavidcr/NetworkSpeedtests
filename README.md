# NetworkSpeedtests

Scripts para automatizar y analizar pruebas de velocidad de red usando `iperf3` y generar informes en TXT, CSV y HTML.

## Requisitos
- bash (recomendado bash 4+)
- Python 3
- iperf3
- awk, sed, grep, coreutils
- macOS o Linux

## Archivos principales
- `NetworkSpeedtest.sh`: Script principal para ejecutar pruebas de red y generar reportes.
- `parse_iperf_report.py`: Analiza el log generado y produce resumen en TXT y CSV.
- `parse_iperf_report_html.py`: Genera un informe HTML con gráficos a partir del log.

## Uso rápido
```sh
chmod +x NetworkSpeedtest.sh
./NetworkSpeedtest.sh --interface <IFACE> [opciones]
```

### Opciones principales
- `--interface`, `-i <IFACE>`: Interfaz de red a usar (obligatorio, ej: eth0, en0)
- `--open-html`, `-O`: Abre automáticamente el informe HTML al finalizar (solo macOS)
- `--ping-retries <N>`: Número de reintentos de ping (por defecto: 3)
- `--ping-wait <SEG>`: Segundos de espera entre reintentos de ping (por defecto: 2)
- `--help`, `-h`: Muestra la ayuda

### Ejemplo
```sh
./NetworkSpeedtest.sh --interface en0 --open-html
```

Los resultados se guardan en una carpeta `reports/` con subcarpetas por fecha y hora.

## Informes generados
- `speedtest.log`: Log completo de la prueba
- `resumen.txt`: Resumen legible
- `resumen.csv`: Resumen en formato CSV
- `informe.html`: Informe visual con gráficos

## Ejecución manual de los analizadores
Si tienes un log generado, puedes crear los informes manualmente:
```sh
python3 parse_iperf_report.py <ruta/speedtest.log> [output_dir]
python3 parse_iperf_report_html.py <ruta/speedtest.log> [output_dir] [server_ip] [interface] [interface_ip]
```

## Ejecución en el servidor (iperf3)
Antes de lanzar las pruebas, asegúrate de que el servidor iperf3 esté escuchando. En el equipo destino ejecuta:

```sh
iperf3 -s
```

Esto dejará el servidor iperf3 escuchando para las pruebas TCP y UDP en el puerto 5201 por defecto.

## Notas
- El script detecta automáticamente la IP de la interfaz.
- Si usas macOS, el informe HTML se abre automáticamente con `--open-html`.
- El servidor iperf3 debe estar corriendo en la IP configurada en el script (`SERVER_IP`).

## Arquitectura: Cliente y Servidor
Este sistema de pruebas requiere dos equipos:

- **Servidor:** Ejecuta `iperf3` en modo escucha. Es el equipo destino al que se conectan las pruebas. Debe estar en la red y accesible desde el cliente.
- **Cliente:** Ejecuta el script `NetworkSpeedtest.sh`, realiza las pruebas de velocidad y genera los informes. El cliente se conecta al servidor usando la IP configurada en el script.

Asegúrate de que ambos equipos tengan conectividad de red entre sí y que el puerto de iperf3 (por defecto 5201) esté abierto.

## Licencia
MIT
