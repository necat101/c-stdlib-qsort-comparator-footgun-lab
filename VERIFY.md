# VERIFY.md — c-stdlib-qsort-comparator-footgun-lab

Fresh-clone verification transcript.

```
$ python3 -m py_compile generate_cases.py run_lab.py
$ python3 generate_cases.py
Wrote 50 cases to cases.json
$ python3 run_lab.py
Compiler: zig_cc | clang version 19.1.7 (https://github.com/ziglang/zig-bootstrap de1b01a8c1dddf75a560123ac1c2ab182b4830da)
Compile: 0 in 0.219s

Total rows: 439
Cases: 50, Methods: 16
Wrote RESULTS.md, results_rows.csv/json
```

**Environment:**
- Python: 3.12.3
- Platform: Linux-6.17.0-1009-aws-x86_64-with-glibc2.39
- Compiler: zig cc 0.14.1 (clang 19.1.7 backend, musl target)
- Compile ok: True
- Binary size: 17040 bytes

**Artifacts present:**
- cases.json (50 cases)
- c_qsort_comparator_footgun_harness.c (generated deterministically by run_lab.py)
- RESULTS.md
- results_rows.csv (439 rows)
- results_rows.json
- hn_thread_evidence.md
- hn_nodes_sanitized.json (129 nodes, ~68 KB)

**HN thread access:** Yes – Hacker News Firebase API CLI, thread 39264396, before README was written.

**No network / no package manager / no root** during benchmark run (except HN pre-read).

**UB not run:** Invalid comparators (nontransitive, random, stateful, NaN-like, inconsistent) marked `not_run`, never passed to qsort.

**glibc OOB vulnerability:** NOT reproduced – HN discussion context only.

All 50 cases observed. Naive comparator failed 12 expected cases (boolean return, subtraction overflow, random/stateful/cyclic/NaN-like/inconsistent comparators, contract violations).
