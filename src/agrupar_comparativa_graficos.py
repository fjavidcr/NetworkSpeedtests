#!/usr/bin/env python3
import os
import csv
from pathlib import Path
from collections import defaultdict
import matplotlib.pyplot as plt

REPORTS_DIR = Path("reports")
# Cambia la carpeta de salida de comparativas
COMPARATIVAS_DIR = Path("comparativas")
COMPARATIVAS_DIR.mkdir(exist_ok=True)

csv_files = sorted(REPORTS_DIR.glob("*_*/resumen.csv"))

all_results = defaultdict(dict)
report_names = []

for csv_file in csv_files:
    report_name = csv_file.parent.name
    report_names.append(report_name)
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            test = row["Prueba"]
            tx = row["Envío (TX) Gbps"]
            rx = row["Recepción (RX) Gbps"]
            all_results[test][report_name] = (tx, rx)

tests = sorted(all_results.keys())

# Crear gráfico comparativo para cada test
output_dir = COMPARATIVAS_DIR
output_dir.mkdir(exist_ok=True)

for test in tests:
    txs = []
    rxs = []
    for name in report_names:
        tx, rx = all_results[test].get(name, ("0", "0"))
        try:
            txs.append(float(tx) if tx != "N/A" else 0)
            rxs.append(float(rx) if rx != "N/A" else 0)
        except Exception:
            txs.append(0)
            rxs.append(0)
    x = range(len(report_names))
    plt.figure(figsize=(10,5))
    plt.bar(x, txs, width=0.4, label="TX (Gbps)", color="#3692eb")
    plt.bar([i+0.4 for i in x], rxs, width=0.4, label="RX (Gbps)", color="#ff6384")
    plt.xticks([i+0.2 for i in x], report_names, rotation=45, ha="right")
    plt.title(f"Comparativa: {test}")
    plt.ylabel("Gbps")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / f"{test.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_')}.png")
    plt.close()

print(f"Gráficos generados en: {output_dir}")
