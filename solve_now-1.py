#!/usr/bin/env python3
import json
from pysat.solvers import Glucose3

import glob, sys

# Auto-detect file JSON, atau terima argument
if len(sys.argv) > 1:
    fname = sys.argv[1]
else:
    files = glob.glob('*.json')
    if not files:
        print("Ga ada file JSON ditemukan!")
        sys.exit(1)
    fname = files[0]
    print(f"Baca file: {fname}")

with open(fname, 'r') as f:
    data = json.load(f)

all_clauses = []
for k in sorted(data.keys(), key=int):
    for clause in data[k]['fragment']['clauses']:
        all_clauses.append(clause)

print(f"Total clauses: {len(all_clauses)}")

solver = Glucose3()
for clause in all_clauses:
    solver.add_clause(clause)

if solver.solve():
    model = solver.get_model()
    solver.delete()
    assignment = ''
    model_map = {abs(l): l > 0 for l in model}
    for i in range(1, 385):
        assignment += '1' if model_map.get(i, True) else '0'
    print(f"\nLength: {len(assignment)} (harus 384)")
    print("\n=== ASSIGNMENT (copy ke Hark) ===")
    print(assignment)
else:
    print("UNSAT!")
