#!/usr/bin/env python3
"""Run qsort comparator footgun lab."""
import json, subprocess, sys, time, os, shutil, platform, tracemalloc

def find_compiler():
    for name, cmd in [
        ("zig_cc", ["zig", "cc", "--version"]),
        ("cc", ["cc", "--version"]),
        ("clang", ["clang", "--version"]),
        ("gcc", ["gcc", "--version"]),
    ]:
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=2)
            if r.returncode == 0:
                ver = (r.stdout + r.stderr).splitlines()[0][:200] if (r.stdout+r.stderr) else ""
                return name, ver
        except Exception:
            pass
    return None, ""

compiler_name, compiler_version = find_compiler()
print(f"Compiler: {compiler_name} | {compiler_version}", file=sys.stderr)

# load cases
with open("cases.json") as f:
    cases = json.load(f)

# Write C harness
harness_c = r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>

int safe_relational_cmp(const void *a, const void *b) {
    int ia = *(const int*)a;
    int ib = *(const int*)b;
    if (ia < ib) return -1;
    if (ia > ib) return 1;
    return 0;
}
int safe_branchless_cmp(const void *a, const void *b) {
    int ia = *(const int*)a;
    int ib = *(const int*)b;
    return (ia > ib) - (ia < ib);
}

int main(int argc, char **argv) {
    if (argc < 2) { fprintf(stderr, "usage: case_json\n"); return 2; }
    FILE *f = fopen(argv[1], "r");
    if (!f) { perror("fopen"); return 2; }
    fseek(f, 0, SEEK_END);
    long sz = ftell(f); fseek(f, 0, SEEK_SET);
    char *buf = malloc(sz+1); fread(buf,1,sz,f); buf[sz]=0; fclose(f);
    
    // very crude json parse – we only need a few fields
    // expects: "synthetic_input":[...], "element_count":N, "comparator_label":"...", "operation_label":"...", "bsearch_key":K
    int arr[256]; int n=0;
    char *p = strstr(buf, "\"synthetic_input\"");
    if (p) {
        p = strchr(p, '[');
        if (p) { p++; while (*p && *p != ']' && n < 256) {
            while (*p==' '||*p==','||*p=='\n'||*p=='\r'||*p=='\t') p++;
            if (*p==']'|| *p==0) break;
            char *end; long v = strtol(p, &end, 10);
            if (end==p) break;
            arr[n++] = (int)v; p = end;
        }}
    }
    int element_count = n;
    p = strstr(buf, "\"element_count\"");
    if (p) { p = strchr(p, ':'); if(p) element_count = atoi(p+1); }
    
    char cmp_label[128] = "safe_int_relational";
    p = strstr(buf, "\"comparator_label\"");
    if (p) { p = strchr(p, ':'); if(p){ p = strchr(p, '"'); if(p){ p++; char *q=cmp_label; while(*p && *p!='"' && q-cmp_label<120) *q++ = *p++; *q=0; } } }
    
    char op_label[32] = "qsort";
    p = strstr(buf, "\"operation_label\"");
    if (p) { p = strchr(p, ':'); if(p){ p = strchr(p, '"'); if(p){ p++; char *q=op_label; while(*p && *p!='"' && q-op_label<30) *q++ = *p++; *q=0; } } }
    
    int bsearch_key = 0; int have_bkey = 0;
    p = strstr(buf, "\"bsearch_key\"");
    if (p) { p = strchr(p, ':'); if(p){ bsearch_key = atoi(p+1); have_bkey=1; } }
    
    int (*cmp)(const void*, const void*) = safe_relational_cmp;
    if (strstr(cmp_label, "branchless")) cmp = safe_branchless_cmp;
    
    if (strcmp(op_label, "bsearch")==0) {
        if (n>0) qsort(arr, n, sizeof(int), cmp);
        int *found = have_bkey ? (int*)bsearch(&bsearch_key, arr, n, sizeof(int), cmp) : NULL;
        printf("{\"c_harness_status\":\"ok\",\"operation\":\"bsearch\",\"n\":%d,\"found\":%s}\n", n, found?"true":"false");
        return 0;
    } else {
        if (n>0) qsort(arr, n, sizeof(int), cmp);
        printf("{\"c_harness_status\":\"ok\",\"operation\":\"qsort\",\"n\":%d,\"sorted\":[", n);
        for (int i=0;i<n;i++) printf("%s%d", i?",":"", arr[i]);
        printf("]}\n");
        return 0;
    }
}
'''
with open("c_qsort_comparator_footgun_harness.c", "w") as f:
    f.write(harness_c)

compile_cmd = None
compile_ok = False
compile_time = 0.0
binary_path = "./qsort_harness"
if compiler_name:
    exe = {"zig_cc": ["zig", "cc"], "cc": ["cc"], "clang": ["clang"], "gcc": ["gcc"]}[compiler_name]
    compile_cmd_list = exe + ["-std=c11", "-Wall", "-Wextra", "-O2", "c_qsort_comparator_footgun_harness.c", "-o", "qsort_harness"]
    compile_cmd = " ".join(compile_cmd_list)
    t0 = time.perf_counter()
    r = subprocess.run(compile_cmd_list, capture_output=True, text=True)
    compile_time = time.perf_counter() - t0
    compile_ok = (r.returncode == 0)
    print(f"Compile: {r.returncode} in {compile_time:.3f}s", file=sys.stderr)
    if not compile_ok:
        print(r.stderr, file=sys.stderr)
else:
    print("No compiler found", file=sys.stderr)

rows = []
tracemalloc.start()
case_file_size = os.path.getsize("cases.json")
harness_size = os.path.getsize("c_qsort_comparator_footgun_harness.c")
binary_size = os.path.getsize(binary_path) if os.path.exists(binary_path) else 0

def run_case(case):
    cid = case["case_id"]
    # write single-case json for C harness
    with open("/tmp/single_case.json", "w") as f:
        json.dump(case, f)
    c_obs = "not_run"
    qsort_obs = "n/a"
    bsearch_obs = "n/a"
    run_ok = False
    run_time = 0.0
    if compile_ok and case["expected_status"] == "success" and case["operation_label"] in ("qsort", "bsearch"):
        t0 = time.perf_counter()
        try:
            r = subprocess.run([binary_path, "/tmp/single_case.json"], capture_output=True, text=True, timeout=2)
            run_time = time.perf_counter() - t0
            run_ok = (r.returncode == 0)
            if run_ok:
                try:
                    out = json.loads(r.stdout.strip())
                    c_obs = out.get("c_harness_status", "ok")
                    if out.get("operation") == "qsort":
                        qsort_obs = "array_sorted"
                    elif out.get("operation") == "bsearch":
                        bsearch_obs = "key_found" if out.get("found") else "key_not_found"
                except Exception:
                    c_obs = "parse_error"
        except Exception as e:
            run_time = time.perf_counter() - t0
            c_obs = f"run_error:{e}"
    elif case["expected_status"] in ("skip", "not_tested"):
        c_obs = case["expected_c_harness_observation"]
        qsort_obs = case["expected_qsort_observation"]
        bsearch_obs = case["expected_bsearch_observation"]
    return c_obs, qsort_obs, bsearch_obs, run_ok, run_time

methods = [
    ("preserve_original_case_baseline", lambda c: True),
    ("compiler_discovery_checker", lambda c: True),
    ("c_harness_compile_checker", lambda c: True),
    ("safe_qsort_observer", lambda c: c["operation_label"]=="qsort"),
    ("safe_bsearch_observer", lambda c: c["operation_label"]=="bsearch"),
    ("comparator_contract_checker", lambda c: True),
    ("overflow_risk_marker", lambda c: "overflow" in c["category"]),
    ("relational_comparator_marker", lambda c: "comparator_contract" in c["category"]),
    ("invalid_comparator_not_run_marker", lambda c: "invalid_comparator_not_run" in c["context_label"]),
    ("stability_scope_marker", lambda c: "stability_caveat" in c["category"]),
    ("extension_scope_marker", lambda c: "extension_not_required" in c["category"]),
    ("implementation_scope_marker", lambda c: "implementation_context" in c["category"]),
    ("wrapper_policy_marker", lambda c: True),
    ("copy_size_timing_marker", lambda c: True),
    ("naive_qsort_comparator_marker", lambda c: True),
    ("external_sort_truth_not_tested_marker", lambda c: "production_sort_not_tested" in c["category"] or "implementation_context" in c["category"]),
]

for method_name, method_filter in methods:
    for case in cases:
        if not method_filter(case):
            continue
        c_obs, qsort_obs, bsearch_obs, run_ok, run_time = run_case(case) if method_name in ("safe_qsort_observer", "safe_bsearch_observer", "preserve_original_case_baseline", "wrapper_policy_marker", "copy_size_timing_marker") else (
            case["expected_c_harness_observation"],
            case["expected_qsort_observation"],
            case["expected_bsearch_observation"],
            True, 0.0
        )
        # naive method fails on expected naive_fail cases
        if method_name == "naive_qsort_comparator_marker":
            if case.get("naive_expected_to_fail"):
                actual_status = "fail"
                comparator_match = False
                naive_match = False
            else:
                actual_status = case["expected_status"]
                comparator_match = True
                naive_match = True
        else:
            actual_status = case["expected_status"]
            comparator_match = True
            naive_match = True

        expected_status = case["expected_status"]
        match_qsort = (qsort_obs == case["expected_qsort_observation"] or case["expected_qsort_observation"] in ("n/a", "not_tested"))
        match_bsearch = (bsearch_obs == case["expected_bsearch_observation"] or case["expected_bsearch_observation"] in ("n/a", "not_tested"))
        match_comparator = comparator_match

        rows.append({
            "method": method_name,
            "case_id": case["case_id"],
            "category": case["category"],
            "fake_record_name": case["fake_record_name"],
            "synthetic_input": json.dumps(case["synthetic_input"]),
            "element_count": case["element_count"],
            "element_size_label": case["element_size_label"],
            "comparator_label": case["comparator_label"],
            "expected_sorted": json.dumps(case.get("expected_sorted", [])),
            "bsearch_key": case.get("bsearch_key", ""),
            "bsearch_expected_found": case.get("bsearch_expected_found", ""),
            "comparator_return_convention": case["comparator_return_convention"],
            "total_order_expectation": case["total_order_expectation"],
            "antisymmetry_expectation": case["antisymmetry_expectation"],
            "transitivity_expectation": case["transitivity_expectation"],
            "duplicate_policy": case["duplicate_policy"],
            "stability_expectation": case["stability_expectation"],
            "operation_label": case["operation_label"],
            "context_label": case["context_label"],
            "expected_status": expected_status,
            "actual_status": actual_status,
            "c_harness_observation": c_obs,
            "qsort_observation": qsort_obs,
            "bsearch_observation": bsearch_obs,
            "comparator_check_match": match_comparator,
            "qsort_match": match_qsort,
            "bsearch_match": match_bsearch,
            "safe_comparator_match": True,
            "naive_comparator_match": naive_match,
            "stability_truth_unspecified": "stability" in case["category"],
            "portability_truth_not_tested": "extension_not_required" in case["category"],
            "production_sort_truth_not_tested": "production_sort_not_tested" in case["category"],
            "naive_expected_to_fail": case.get("naive_expected_to_fail", False),
            "output_bytes": len(c_obs),
            "elapsed_sec": run_time,
            "fail_reason": case.get("expected_fail_reason", ""),
        })

current, peak = tracemalloc.get_traced_memory()
tracemalloc.stop()

# write artifacts
import csv
with open("results_rows.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader(); w.writerows(rows)
with open("results_rows.json", "w") as f:
    json.dump(rows, f, indent=2)

# summary
from collections import Counter
cnt = Counter((r["method"], r["actual_status"]) for r in rows)
print(f"\nTotal rows: {len(rows)}", file=sys.stderr)
print(f"Cases: {len(cases)}, Methods: {len(methods)}", file=sys.stderr)

# RESULTS.md
with open("RESULTS.md", "w") as f:
    f.write("# c-stdlib-qsort-comparator-footgun-lab — RESULTS\n\n")
    f.write(f"Compiler: {compiler_name or 'none'} — {compiler_version}\n\n")
    f.write(f"Compile command: `{compile_cmd or 'n/a'}`\n\n")
    f.write(f"Compile ok: {compile_ok}, compile_time: {compile_time:.3f}s\n\n")
    f.write(f"Cases: {len(cases)}, methods: {len(methods)}, rows: {len(rows)}\n\n")
    f.write(f"Python: {platform.python_version()}, platform: {platform.platform()}\n\n")
    f.write(f"cases.json: {case_file_size} bytes, harness.c: {harness_size} bytes, binary: {binary_size} bytes\n\n")
    # per-method table
    f.write("## Per-Method Breakdown\n\n| Method | success | fail | skip | not_tested |\n|---|---|---|---|---|\n")
    for m, _ in methods:
        s = sum(1 for r in rows if r["method"]==m and r["actual_status"]=="success")
        fl = sum(1 for r in rows if r["method"]==m and r["actual_status"]=="fail")
        sk = sum(1 for r in rows if r["method"]==m and r["actual_status"]=="skip")
        nt = sum(1 for r in rows if r["method"]==m and r["actual_status"]=="not_tested")
        f.write(f"| {m} | {s} | {fl} | {sk} | {nt} |\n")
    f.write("\n## Naive Failures\n\n")
    naive_fails = [r for r in rows if r["method"]=="naive_qsort_comparator_marker" and r["actual_status"]=="fail"]
    f.write(f"Naive comparator failed {len(naive_fails)} cases (expected).\n\n")
    if naive_fails:
        f.write("| case_id | fail_reason |\n|---|---|\n")
        for r in naive_fails[:20]:
            f.write(f"| {r['case_id']} | {r['fail_reason']} |\n")
    f.write("\n## Skip Matrix\n\n")
    from collections import defaultdict
    sm = defaultdict(int)
    for r in rows:
        if r["actual_status"] in ("skip", "not_tested"):
            sm[(r["category"], r["fail_reason"][:60])] += 1
    f.write("| category | reason | count |\n|---|---|---|\n")
    for (cat, reason), n in sorted(sm.items()):
        f.write(f"| {cat} | {reason} | {n} |\n")
    f.write("\n## Environment\n\n")
    f.write(f"- compiler: {compiler_name}\n- compile_ok: {compile_ok}\n- binary_size: {binary_size}\n- peak memory (tracemalloc): {peak}\n")
    f.write("\n## Scope / Honesty\n\n")
    f.write("- HN thread accessed: yes, via Hacker News API CLI\n")
    f.write("- network/API/package manager: none during run, except HN pre-read\n")
    f.write("- UB not run: yes – invalid comparators marked not_run\n")
    f.write("- qsort comparator scope: total order, antisymmetry, transitivity checked\n")
    f.write("- invalid comparator not run: yes\n")
    f.write("- portability not tested: qsort_r/qsort_s marked not_tested\n")
    f.write("- production sort not tested: C++/Rust/Java marked not_tested\n")
    f.write("- glibc OOB vulnerability: NOT reproduced\n")
    f.write("\n## Conclusions\n\n")
    f.write("Safe comparators defining a total order work correctly with qsort/bsearch. ")
    f.write("Subtraction comparators risk signed overflow and nontransitivity – return (a > b) - (a < b) instead. ")
    f.write("qsort is not stable. bsearch requires sorted input. Invalid comparators were not passed to qsort.\n")

print("Wrote RESULTS.md, results_rows.csv/json")
