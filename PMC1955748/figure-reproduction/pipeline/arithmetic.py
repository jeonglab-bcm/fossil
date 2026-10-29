"""Numbers in the paper that follow from other numbers in the paper.

Usage: arithmetic.py OUT.json
"""
import json
import sys

# Table 2 as printed: CPU (s), CPU/Align, Rel. to FAST, Align Missing.
table2 = {
    'Dali': (12895, '6.2', '20', 121),
    'SRUCTAL': (3703, '1.8', '5', 0),
    'GASH': (3197, '1.5', '5', 4),
    'RASH': (1424, '.69', '2', 0),
    'FAST': (645, '.31', '1', 3),
}
pairs = 2071                              # Table 2 footnote and Fig. 2 caption
out = {'table2': {}}
for prog, (cpu, per, rel, miss) in table2.items():
    out['table2'][prog] = {
        'cpu_s': cpu, 'printed_cpu_per_align': per, 'cpu_s_over_2071': round(cpu / pairs, 3),
        'printed_rel_to_fast': rel, 'cpu_over_fast': round(cpu / table2['FAST'][0], 2),
    }

n_test = 2930
out['test_set_pairs'] = {
    'abstract': 4298905,
    'n_choose_2_of_2930': n_test * (n_test - 1) // 2,     # "all 2930 x 2929/2 unique, non-identical structure pairs"
    'n_times_n_of_2930': n_test * n_test,
}
out['lash_cpu'] = {
    'printed_hours': 891, 'printed_s_per_alignment': '.37',
    's_per_alignment_2930x2930': round(891 * 3600 / (n_test * n_test), 4),
    's_per_alignment_2930x2929/2': round(891 * 3600 / (n_test * (n_test - 1) / 2), 4),
}
out['reduced_training_set'] = {'full': 2911, 'removed': 2514, 'printed_reduced': 1397,
                               'full_minus_removed': 2911 - 2514}
out['geometric_test_set'] = {'methods_section': 2070, 'table2_and_fig2': 2071}
json.dump(out, open(sys.argv[1], 'w'), indent=1)
print(json.dumps(out, indent=1))
