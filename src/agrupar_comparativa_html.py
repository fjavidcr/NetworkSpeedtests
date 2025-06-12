#!/usr/bin/env python3
import os
import csv
from pathlib import Path
from collections import defaultdict
from datetime import datetime
import json
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path("reports")
COMPARATIVAS_DIR = Path("comparativas")
COMPARATIVAS_DIR.mkdir(exist_ok=True)

csv_files = sorted(BASE_DIR.glob("*_*/resumen.csv"))
all_results = defaultdict(dict)
report_names = []

# Para detalles por ejecución (latencia, pérdida, fecha, etc)
report_details = {}
for csv_file in csv_files:
    report_name = csv_file.parent.name
    report_names.append(report_name)
    # Buscar detalles adicionales
    resumen_txt = csv_file.parent / "resumen.txt"
    latencia = perdida = fecha = "N/A"
    if resumen_txt.exists():
        with open(resumen_txt, encoding="utf-8") as f:
            for line in f:
                if "Latencia promedio" in line:
                    latencia = line.split(":")[-1].strip()
                if "Pérdida de paquetes UDP" in line:
                    perdida = line.split(":")[-1].strip()
    # Buscar fecha en el nombre de la carpeta
    try:
        fecha = report_name.split("_")[1] + " " + report_name.split("_")[2].replace("_", ":")
    except Exception:
        fecha = report_name
    report_details[report_name] = {"latencia": latencia, "perdida": perdida, "fecha": fecha}
    with open(csv_file, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            test = row["Prueba"]
            tx = row["Envío (TX) Gbps"]
            rx = row["Recepción (RX) Gbps"]
            all_results[test][report_name] = (tx, rx)

tests = sorted(all_results.keys())

def color_class(val):
    try:
        v = float(val)
        if v >= 1.8:
            return 'cell-green'
        elif v >= 1.5:
            return 'cell-yellow'
        else:
            return 'cell-red'
    except Exception:
        return 'cell-na'

def details_json(test, name, tx, rx):
    import html
    details = report_details.get(name, {})
    d = {"test": test, "exec": name, "tx": tx, "rx": rx, **details}
    return json.dumps(d)

def compute_stats(txs):
    arr = [v for v in txs if isinstance(v, float) or isinstance(v, int)]
    if not arr:
        return ("N/A", "N/A", "N/A")
    return (f"{min(arr):.2f}", f"{max(arr):.2f}", f"{sum(arr)/len(arr):.2f}")

# Prepara stats para cada test
stats = {}
for test in tests:
    txs = []
    rxs = []
    for name in report_names:
        tx, rx = all_results[test].get(name, ("N/A", "N/A"))
        try:
            txs.append(float(tx)) if tx != "N/A" else txs.append(None)
            rxs.append(float(rx)) if rx != "N/A" else rxs.append(None)
        except Exception:
            txs.append(None)
            rxs.append(None)
    min_tx, max_tx, avg_tx = compute_stats(txs)
    min_rx, max_rx, avg_rx = compute_stats(rxs)
    stats[test] = {"min_tx": min_tx, "max_tx": max_tx, "avg_tx": avg_tx, "min_rx": min_rx, "max_rx": max_rx, "avg_rx": avg_rx}

# Calcular medias globales TX y RX
total_tx = 0
total_rx = 0
count_tx = 0
count_rx = 0
for test in tests:
    for name in report_names:
        tx, rx = all_results[test].get(name, ("N/A", "N/A"))
        if tx != "N/A":
            total_tx += float(tx)
            count_tx += 1
        if rx != "N/A":
            total_rx += float(rx)
            count_rx += 1
global_avg_tx = round(total_tx / count_tx, 2) if count_tx else None
global_avg_rx = round(total_rx / count_rx, 2) if count_rx else None

# Calcular variabilidad máxima (max-min) para TX y RX
max_tx = None
min_tx = None
max_rx = None
min_rx = None
for test in stats.values():
    try:
        tx_max = float(test['max_tx'])
        tx_min = float(test['min_tx'])
        rx_max = float(test['max_rx'])
        rx_min = float(test['min_rx'])
    except Exception:
        continue
    if max_tx is None or tx_max > max_tx:
        max_tx = tx_max
    if min_tx is None or tx_min < min_tx:
        min_tx = tx_min
    if max_rx is None or rx_max > max_rx:
        max_rx = rx_max
    if min_rx is None or rx_min < min_rx:
        min_rx = rx_min
max_var_tx = round(max_tx - min_tx, 2) if max_tx is not None and min_tx is not None else None
max_var_rx = round(max_rx - min_rx, 2) if max_rx is not None and min_rx is not None else None

# Renderizar con Jinja2
env = Environment(
    loader=FileSystemLoader(str(Path(__file__).parent / "templates")),
    autoescape=select_autoescape(['html', 'xml'])
)
template = env.get_template("comparativa_reports.html.j2")

html_rendered = template.render(
    fecha_generado=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    report_names=report_names,
    tests=tests,
    all_results=all_results,
    report_details=report_details,
    color_class=color_class,
    details_json=details_json,
    stats=stats,
    global_avg_tx=global_avg_tx,
    global_avg_rx=global_avg_rx,
    max_var_tx=max_var_tx,
    max_var_rx=max_var_rx
)

with open(COMPARATIVAS_DIR / "comparativa_reports.html", "w", encoding="utf-8") as f:
    f.write(html_rendered)

print(f"Comparativa HTML generada en: {COMPARATIVAS_DIR / 'comparativa_reports.html'}")
