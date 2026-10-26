#!/usr/bin/env python3
"""
NONCE Free Mint - SAT Solver
Versi: nonce-logic-connected-1536
- 1536 variabel
- 6912 klausa
- 24 fragment

Cara pakai:
1. Jalanin: python3 sat_solver.py
2. Paste semua JSON fragment waktu diminta
3. Script output assignment string 1536 karakter
"""

import json
import sys

def parse_fragments(raw_input):
    """Parse fragment JSON dari input, support berbagai format."""
    clauses = []
    
    # Coba parse sebagai array JSON
    try:
        data = json.loads(raw_input)
        if isinstance(data, list):
            for item in data:
                if isinstance(item, list):
                    # Langsung array of clauses
                    clauses.extend(item)
                elif isinstance(item, dict):
                    # Object dengan field clauses/data/fragments
                    for key in ['clauses', 'data', 'fragments', 'content']:
                        if key in item:
                            val = item[key]
                            if isinstance(val, list):
                                clauses.extend(val)
                            break
        elif isinstance(data, dict):
            for key in ['clauses', 'data', 'fragments', 'content']:
                if key in data:
                    val = data[key]
                    if isinstance(val, list):
                        clauses.extend(val)
                    break
        if clauses:
            return clauses
    except:
        pass
    
    # Coba parse multiple JSON objects (satu per baris atau dipisah)
    import re
    json_objects = re.findall(r'\{[^{}]*\}|\[[^\[\]]*\]', raw_input, re.DOTALL)
    for obj_str in json_objects:
        try:
            obj = json.loads(obj_str)
            if isinstance(obj, list) and len(obj) > 0:
                if isinstance(obj[0], list) and len(obj[0]) == 3:
                    clauses.extend(obj)
                elif isinstance(obj[0], int):
                    # Flat list of ints, group per 3
                    for i in range(0, len(obj)-2, 3):
                        clauses.append([obj[i], obj[i+1], obj[i+2]])
            elif isinstance(obj, dict):
                for key in ['clauses', 'data', 'fragments', 'content']:
                    if key in obj:
                        val = obj[key]
                        if isinstance(val, list):
                            if len(val) > 0 and isinstance(val[0], list):
                                clauses.extend(val)
                            elif len(val) > 0 and isinstance(val[0], int):
                                for i in range(0, len(val)-2, 3):
                                    clauses.append([val[i], val[i+1], val[i+2]])
                        break
        except:
            continue
    
    return clauses


def solve_sat(num_vars, clauses):
    """
    Solve SAT pake pysat (python-sat).
    Fallback ke DPLL sederhana kalau pysat ga ada.
    """
    try:
        from pysat.solvers import Glucose3
        solver = Glucose3()
        for clause in clauses:
            solver.add_clause(clause)
        
        if solver.solve():
            model = solver.get_model()
            solver.delete()
            return model
        else:
            solver.delete()
            return None
    except ImportError:
        print("[!] pysat tidak tersedia, pakai DPLL fallback...")
        print("[!] Install dulu: pip install python-sat --break-system-packages")
        return dpll_solve(num_vars, clauses)


def dpll_solve(num_vars, clauses):
    """DPLL solver sederhana sebagai fallback."""
    assignment = {}
    
    def unit_propagate(clauses, assignment):
        changed = True
        while changed:
            changed = False
            for clause in clauses:
                unassigned = []
                satisfied = False
                for lit in clause:
                    var = abs(lit)
                    if var in assignment:
                        val = assignment[var]
                        if (lit > 0 and val) or (lit < 0 and not val):
                            satisfied = True
                            break
                    else:
                        unassigned.append(lit)
                if satisfied:
                    continue
                if len(unassigned) == 0:
                    return False, assignment
                if len(unassigned) == 1:
                    lit = unassigned[0]
                    var = abs(lit)
                    assignment[var] = (lit > 0)
                    changed = True
        return True, assignment
    
    def is_satisfied(clauses, assignment):
        for clause in clauses:
            sat = False
            for lit in clause:
                var = abs(lit)
                if var in assignment:
                    val = assignment[var]
                    if (lit > 0 and val) or (lit < 0 and not val):
                        sat = True
                        break
            if not sat:
                return False
        return True
    
    def dpll(clauses, assignment, depth=0):
        ok, assignment = unit_propagate(clauses, assignment.copy())
        if not ok:
            return None
        
        if is_satisfied(clauses, assignment):
            return assignment
        
        # Pilih variabel yang belum di-assign
        var = None
        for clause in clauses:
            for lit in clause:
                v = abs(lit)
                if v not in assignment:
                    var = v
                    break
            if var:
                break
        
        if var is None:
            return assignment if is_satisfied(clauses, assignment) else None
        
        # Coba True dulu
        new_assign = assignment.copy()
        new_assign[var] = True
        result = dpll(clauses, new_assign, depth+1)
        if result is not None:
            return result
        
        # Coba False
        new_assign = assignment.copy()
        new_assign[var] = False
        return dpll(clauses, new_assign, depth+1)
    
    print(f"[*] Running DPLL pada {num_vars} variabel, {len(clauses)} klausa...")
    print("[!] DPLL bisa lambat untuk instance besar. Sangat disarankan install pysat:")
    print("    pip install python-sat --break-system-packages")
    
    result = dpll(clauses, {})
    if result is None:
        return None
    
    # Convert ke model format (list of signed ints)
    model = []
    for i in range(1, num_vars + 1):
        val = result.get(i, True)  # default True kalau ga ke-assign
        model.append(i if val else -i)
    return model


def model_to_assignment(model, num_vars):
    """Convert model ke string binary 1536 karakter."""
    assignment_map = {}
    for lit in model:
        var = abs(lit)
        assignment_map[var] = '1' if lit > 0 else '0'
    
    result = ''
    for i in range(1, num_vars + 1):
        result += assignment_map.get(i, '1')  # default '1' kalau missing
    
    return result


def verify_assignment(assignment_str, clauses, num_vars):
    """Verifikasi semua clause terpenuhi."""
    assignment = {}
    for i, c in enumerate(assignment_str):
        assignment[i+1] = (c == '1')
    
    failed = 0
    for clause in clauses:
        sat = False
        for lit in clause:
            var = abs(lit)
            val = assignment.get(var, True)
            if (lit > 0 and val) or (lit < 0 and not val):
                sat = True
                break
        if not sat:
            failed += 1
    
    return failed == 0, failed


def main():
    NUM_VARS = 1536
    EXPECTED_CLAUSES = 6912
    FRAGMENT_COUNT = 24
    
    print("=" * 50)
    print("NONCE SAT Solver - nonce-logic-connected-1536")
    print("=" * 50)
    print(f"Target: {NUM_VARS} variabel, {EXPECTED_CLAUSES} klausa, {FRAGMENT_COUNT} fragment")
    print()
    
    # Cek apakah ada file input argument
    if len(sys.argv) > 1:
        filename = sys.argv[1]
        print(f"[*] Baca dari file: {filename}")
        try:
            with open(filename, 'r') as f:
                raw_input = f.read()
        except:
            print(f"[!] Gagal baca file {filename}")
            sys.exit(1)
    else:
        print("Paste semua JSON fragment dari Hark di bawah ini.")
        print("Setelah selesai paste, ketik END lalu Enter:")
        print()
        
        lines = []
        while True:
            try:
                line = input()
                if line.strip() == 'END':
                    break
                lines.append(line)
            except EOFError:
                break
        
        raw_input = '\n'.join(lines)
    
    print()
    print("[*] Parsing fragment...")
    clauses = parse_fragments(raw_input)
    
    if not clauses:
        print("[!] Gagal parse clauses. Pastikan format JSON benar.")
        print("    Format yang diterima:")
        print('    [[1, -2, 3], [-1, 4, -5], ...]')
        print('    atau {"clauses": [[1,-2,3], ...]}')
        sys.exit(1)
    
    print(f"[+] Berhasil parse {len(clauses)} klausa")
    
    if len(clauses) != EXPECTED_CLAUSES:
        print(f"[!] Warning: ekspektasi {EXPECTED_CLAUSES} klausa, dapat {len(clauses)}")
        print("[!] Pastikan semua 24 fragment sudah di-collect")
        if len(clauses) < EXPECTED_CLAUSES * 0.9:
            print("[!] Terlalu sedikit, kemungkinan ada fragment yang missing. Lanjut tetap dicoba...")
    
    print()
    print("[*] Solving SAT...")
    
    model = solve_sat(NUM_VARS, clauses)
    
    if model is None:
        print("[!] UNSAT - tidak ada solusi. Cek apakah semua fragment benar.")
        sys.exit(1)
    
    assignment = model_to_assignment(model, NUM_VARS)
    
    print("[*] Verifikasi assignment...")
    ok, failed = verify_assignment(assignment, clauses, NUM_VARS)
    
    if ok:
        print(f"[+] Verifikasi OK - semua {len(clauses)} klausa terpenuhi")
    else:
        print(f"[!] Verifikasi GAGAL - {failed} klausa tidak terpenuhi")
        sys.exit(1)
    
    print()
    print("=" * 50)
    print("ASSIGNMENT STRING (copy paste ke Hark):")
    print("=" * 50)
    print(assignment)
    print("=" * 50)
    print(f"[+] Panjang: {len(assignment)} karakter (harus 1536)")
    print()
    print("Perintah ke Hark:")
    print(f'Submit artifact with this exact assignment: "{assignment}"')


if __name__ == '__main__':
    main()
