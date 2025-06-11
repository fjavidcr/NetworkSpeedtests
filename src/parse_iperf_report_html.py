#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from datetime import datetime

# Etiquetas adaptadas a los nuevos tests del script bash
default_labels = [
    "TCP básico (sencillo)",
    "TCP medio (4 flujos)",
    "TCP medio (8 flujos)",
    "TCP alta (16 flujos)",
    "TCP bidireccional alta",
    "UDP 2.5G"
]

def parse_section(section, label):
    if "medio (4 flujos)" in label or "medio (8 flujos)" in label or "alta (16 flujos)" in label:
        tx = last_value(section, r"\[SUM\].*sender")
        rx = last_value(section, r"\[SUM\].*receiver")
    elif "UDP" in label:
        tx = last_value(section, r"sender")
        rx = last_value(section, r"receiver")
    elif "bidireccional" in label:
        tx = last_value(section, r"\[TX-C\].*sender")
        rx = last_value(section, r"\[RX-C\].*sender")
    else:
        tx = last_value(section, r"sender")
        rx = last_value(section, r"receiver")
    return tx, rx

def last_value(section, pattern):
    matches = [line for line in section if re.search(pattern, line)]
    if matches:
        m = re.search(r"([0-9.]+)\s+(Gbits|Mbits)/sec", matches[-1])
        if m:
            val = float(m.group(1))
            if m.group(2) == "Mbits":
                val = val / 1000.0
            return f"{val:.2f}"
    return "N/A"

def parse_log(logfile):
    with open(logfile, encoding="utf-8") as f:
        lines = f.readlines()
    results = {}
    for label in default_labels:
        start_pat = re.compile(rf"▶️.*{re.escape(label)}")
        end_pat = re.compile(r"iperf Done")
        section = []
        in_section = False
        for line in lines:
            if not in_section and start_pat.search(line):
                in_section = True
            elif in_section and end_pat.search(line):
                break
            if in_section:
                section.append(line)
        if section:
            tx, rx = parse_section(section, label)
            results[label] = (tx, rx)
        else:
            results[label] = ("N/A", "N/A")
    avg_rtt = "N/A"
    for line in lines:
        m = re.search(r"Latencia promedio: ([0-9.]+) ms", line)
        if m:
            avg_rtt = m.group(1)
            break
    # Mejor extracción de UDP Loss: busca porcentaje en línea con 'receiver'
    udp_loss = "N/A"
    for line in lines:
        if 'receiver' in line:
            m = re.search(r"\(([-0-9.]+)%\)", line)
            if m:
                udp_loss = m.group(1) + "%"
                break
    return results, avg_rtt, udp_loss

def write_html(results, avg_rtt, udp_loss, htmlfile, server_ip, test_date, interface, interface_ip):
    labels = list(results.keys())
    txs = [float(tx) if tx != "N/A" else 0 for tx, _ in results.values()]
    rxs = [float(rx) if rx != "N/A" else 0 for _, rx in results.values()]
    with open(htmlfile, "w") as f:
        f.write(f'''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Informe de Red</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{ font-family: sans-serif; padding: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin-bottom: 30px; background: white; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: center; }}
        th {{ background-color: #eee; }}
        canvas {{ max-width: 800px; margin: 0 auto; }}
    </style>
</head>
<body>
    <h1>Informe de Velocidad de Red</h1>
    <p><strong>Servidor:</strong> {server_ip}</p>
    <p><strong>Fecha:</strong> {test_date}</p>
    <p><strong>Interfaz usada:</strong> {interface} ({interface_ip})</p>
    <p><strong>Latencia promedio:</strong> {avg_rtt} ms</p>
    <p><strong>Pérdida de paquetes UDP:</strong> {udp_loss}</p>
    <h2>Resultados de velocidad por test</h2>
    <table>
        <tr><th>Prueba</th><th>Velocidad de Envío (TX) Gbps</th><th>Velocidad de Recepción (RX) Gbps</th></tr>
''')
        for label, (tx, rx) in results.items():
            f.write(f"        <tr><td>{label}</td><td>{tx}</td><td>{rx}</td></tr>\n")
        f.write('''    </table>
    <h2>Gráfico de velocidades</h2>
    <canvas id="speedChart" width="800" height="400"></canvas>
    <script>
        const ctx = document.getElementById("speedChart").getContext("2d");
        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [''' + ", ".join([f'"{l}"' for l in labels]) + '''],
                datasets: [
                    {
                        label: 'Envío (TX) Gbps',
                        backgroundColor: 'rgba(54, 162, 235, 0.7)',
                        data: [''' + ", ".join(map(str, txs)) + ''']
                    },
                    {
                        label: 'Recepción (RX) Gbps',
                        backgroundColor: 'rgba(255, 99, 132, 0.7)',
                        data: [''' + ", ".join(map(str, rxs)) + ''']
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        title: { display: true, text: 'Gbps' }
                    }
                }
            }
        });
    </script>
</body>
</html>
''')

def main():
    if len(sys.argv) < 2:
        print("Uso: parse_iperf_report_html.py <speedtest.log> [output_dir] [server_ip] [interface] [interface_ip]")
        sys.exit(1)
    logfile = sys.argv[1]
    outdir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(logfile).parent
    server_ip = sys.argv[3] if len(sys.argv) > 3 else "-"
    interface = sys.argv[4] if len(sys.argv) > 4 else "-"
    interface_ip = sys.argv[5] if len(sys.argv) > 5 else "-"
    test_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results, avg_rtt, udp_loss = parse_log(logfile)
    write_html(results, avg_rtt, udp_loss, outdir / "informe.html", server_ip, test_date, interface, interface_ip)
    print(f"Informe HTML generado en: {outdir}/informe.html")

if __name__ == "__main__":
    main()
