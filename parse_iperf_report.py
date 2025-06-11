#!/usr/bin/env python3
import re
import sys
import csv
from pathlib import Path

# Configuración: puedes cambiar estos nombres si lo deseas
default_labels = [
    "TCP básico",
    "TCP prolongado",
    "TCP múltiples flujos",
    "TCP bidireccional",
    "UDP 2.5G"
]

def parse_section(section, label):
    # Busca la última línea relevante para cada tipo de test
    if label == "TCP múltiples flujos":
        tx = last_value(section, r"\[SUM\].*sender")
        rx = last_value(section, r"\[SUM\].*receiver")
    elif label == "UDP 2.5G":
        tx = last_value(section, r"sender")
        rx = last_value(section, r"receiver")
    elif label == "TCP bidireccional":
        tx = last_value(section, r"\[TX-C\].*sender")
        rx = last_value(section, r"\[RX-C\].*sender")
    else:
        tx = last_value(section, r"sender")
        rx = last_value(section, r"receiver")
    return tx, rx

def last_value(section, pattern):
    # Busca la última línea que coincide y extrae el valor de Gbits/sec
    matches = [line for line in section if re.search(pattern, line)]
    if matches:
        # Busca el valor antes de 'Gbits/sec' o 'Mbits/sec'
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
        # Busca la sección correspondiente
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
    # Latencia
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

def write_csv(results, csvfile):
    with open(csvfile, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Prueba", "Envío (TX) Gbps", "Recepción (RX) Gbps"])
        for label, (tx, rx) in results.items():
            writer.writerow([label, tx, rx])

def write_txt(results, avg_rtt, udp_loss, txtfile):
    with open(txtfile, "w") as f:
        f.write("========== RESUMEN ==========" + "\n")
        f.write(f"{'Prueba':<25}{'TX (Gbps)':>12}{'RX (Gbps)':>12}\n")
        for label, (tx, rx) in results.items():
            f.write(f"{label:<25}{tx:>12}{rx:>12}\n")
        f.write(f"\n📶 Latencia promedio: {avg_rtt} ms\n")
        f.write(f"📉 Pérdida de paquetes UDP: {udp_loss}\n")

def main():
    if len(sys.argv) < 2:
        print("Uso: parse_iperf_report.py <speedtest.log> [output_dir]")
        sys.exit(1)
    logfile = sys.argv[1]
    outdir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(logfile).parent
    results, avg_rtt, udp_loss = parse_log(logfile)
    write_csv(results, outdir / "resumen.csv")
    write_txt(results, avg_rtt, udp_loss, outdir / "resumen.txt")
    print(f"Resumen generado en: {outdir}")

if __name__ == "__main__":
    main()
