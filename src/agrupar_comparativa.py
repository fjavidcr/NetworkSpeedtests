#!/usr/bin/env python3
import os
import csv
from pathlib import Path
from collections import defaultdict

REPORTS_DIR = Path("reports")

# Encuentra todos los archivos resumen.csv en subcarpetas de reports
csv_files = sorted(REPORTS_DIR.glob("test_red_*/resumen.csv"))

# Diccionario: {nombre_test: {nombre_report: (tx, rx)}}
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

# Ordenar los tests por nombre
tests = sorted(all_results.keys())

# Crear CSV agrupado
output_csv = REPORTS_DIR / "comparativa_reports.csv"
with open(output_csv, "w", newline="") as f:
    writer = csv.writer(f)
    header = ["Prueba"]
    for name in report_names:
        header.append(f"{name} TX (Gbps)")
        header.append(f"{name} RX (Gbps)")
    writer.writerow(header)
    for test in tests:
        row = [test]
        for name in report_names:
            tx, rx = all_results[test].get(name, ("N/A", "N/A"))
            row.extend([tx, rx])
        writer.writerow(row)

print(f"Comparativa generada en: {output_csv}")
