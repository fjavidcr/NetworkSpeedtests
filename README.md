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
./NetworkSpeedtest.sh [nombre_test] --interface <IFACE> [opciones]
```
Si no se pasa [nombre_test], se usará 'test_red' por defecto.

## Parámetros principales

- `--server-ip IP`, `-s IP`: Especifica la IP del servidor iperf3 al que se conectarán las pruebas. Por defecto es `192.168.100.1`.
- `--interface IFACE`, `-i IFACE`: Especifica la interfaz de red local a usar (ejemplo: eth0). **Obligatorio.**
- `--open-html`, `-O`: Abre automáticamente el informe HTML generado al finalizar (solo macOS).
- `--ping-retries N`: Número de reintentos de ping antes de abortar (por defecto: 3).
- `--ping-wait SEG`: Segundos de espera entre reintentos de ping (por defecto: 2).
- `--help`, `-h`: Muestra la ayuda y opciones disponibles.

### Ejemplo de uso

```bash
./NetworkSpeedtest.sh mi_test --server-ip 10.0.0.2 --interface en0 --open-html
```

Esto ejecutará las pruebas con nombre "mi_test" contra el servidor 10.0.0.2 usando la interfaz en0 y abrirá el informe HTML al finalizar.

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

## Entorno virtual para Python
Se recomienda usar un entorno virtual para instalar las dependencias necesarias para los scripts de análisis y generación de gráficos.

### Crear y activar el entorno virtual
```sh
python3 -m venv venv
source venv/bin/activate
```

### Instalar dependencias
```sh
pip install -r requirements.txt
```

Esto instalará automáticamente `matplotlib` y cualquier otra dependencia necesaria para los scripts de análisis y comparativa.

## Licencia
MIT
