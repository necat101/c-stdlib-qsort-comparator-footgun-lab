# c-stdlib-qsort-comparator-footgun-lab

Toy local correctness and safety lab about **C `qsort` and `bsearch` comparator contracts** – driven by [HN thread 39264396: "Out-of-bounds read and write in the glibc's qsort()"](https://news.ycombinator.com/item?id=39264396).

The linked advisory is about a glibc `qsort()` out-of-bounds read/write triggered under malloc-failure fallback with a nontransitive comparator. The HN discussion broadens into ISO C/POSIX comparator requirements, total ordering, signed overflow, `qsort` interface design, memory safety, CVE boundaries, Rust/Java/C++ behavior, `qsort` performance, function pointer callbacks, library robustness, and whether the real problem is C, glibc, comparator APIs, or invalid caller code.

## What Hacker News users were actually debating

> **Hacker News thread access:** the HN Firebase API CLI (`python3 ./hackernews get-item --id 39264396`) was used to read the linked HN thread before writing this sentiment summary. See [`hn_thread_evidence.md`](hn_thread_evidence.md) and `hn_nodes_sanitized.json` (~68 KB, 129 nodes) for auditable evidence.

HN commenters were not just discussing a glibc bug – the thread is a broad comparator-contract debate. Paraphrased themes (not direct quotes):

- **"Subtraction is not comparison"** – `return a - b` is an obvious but broken integer comparator. Signed overflow breaks transitivity. The safe pattern `return (a > b) - (a < b);` was explicitly posted with a godbolt link – it avoids overflow and is branchless.

- **Total ordering / comparator contract** – ISO C 7.2.5/4 was cited verbatim: comparison function results "shall define a total ordering on the array". Commenters debated whether nontransitive comparators mean UB for all qsort users, or only when nontransitivity is actually triggered.

- **"Holding it wrong" vs "stdlib should defend itself"** – Core tension in the thread. One side: you handed qsort nonsense input, what did you expect? Other side: invalid comparators shouldn't lead to OOB memory access – hard failure is acceptable. Multiple commenters argued blaming users ("holding it wrong") has not succeeded at scale for memory safety.

- **CVE / security boundary** – Should glibc issue a CVE? Mandatory upgrade costs in regulated industries vs encouraging users to audit comparator code. CVSS scoring reliability was questioned with concrete examples.

- **Signed integer overflow** – Extended language-comparison subthread: Rust overflow-in-debug/panic vs release-wrapping, C# checked overflow, MIPS trapping integer overflow, calls for overflow to trap by default.

- **qsort is NOT stable** – Equal elements' relative order is unspecified. This came up repeatedly.

- **bsearch comparator consistency** – bsearch has the same comparison-consistency problem in a different form: array must be sorted, comparator must be consistent with that order.

- **NaN / partial orders / random comparators** – NaN-style partial orders break qsort. Random comparators / "shuffle by sort" are invalid.

- **C vs C++ std::sort vs Rust vs Java** – std::sort also requires well-behaved comparators (gcc bugzilla 41448 cited). Rust's Ord is a *safe* trait – invalid Ord won't cause UB, just nonsense results. Java comparator contracts discussed. WUFFS / Ada / Pascal came up for range-checked types.

- **qsort function-pointer overhead** – "qsort is really slow" / "sometimes barely usable". Suggestions to wrap std::sort for C.

- **qsort_r / qsort_s portability** – Context-carrying comparators: qsort_r (GNU vs BSD signature differs!), qsort_s (Annex K). Global-state comparator context / thread safety came up.

- **glibc malloc fallback / OOB details** – Surprise that "qsort can malloc". The advisory's OOB was tied to malloc-failure fallback with a nontransitive comparator.

- **Dynamic linking / patch deployment** – glibc fix applies system-wide via dynamic linking, unlike template-based std::sort which requires recompiling clients.

- **Comparison operators in C** – C standard explicitly defines `true` as `1`, `false` as `0` (C standard 6.5.8, 7.18 bool macros) – relevant to why `(a > b) - (a < b)` is valid C.

The README reflects the actual HN discussion themes, not just the advisory title.

## What this lab does

A tiny reproducible C stdlib harness testing qsort/bsearch comparator contracts:

- **qsort comparator must define a consistent total order** – negative / zero / positive return values, not arbitrary booleans
- **Returning `a - b` for integers can overflow** – breaks transitivity, signed overflow is UB
- **Safe comparator:** `(a > b) - (a < b)` – no signed overflow for simple integers
- **Equal elements may be reordered** – qsort is NOT stable, equal-element order is unspecified
- **bsearch assumes sorted array + consistent comparator**
- **Random / NaN-like / stateful / inconsistent comparators = invalid** – marked `not_run`, never passed to qsort
- **qsort_r / qsort_s / global-state context** – portability markers, not required locally
- **glibc malloc-fallback OOB** – HN/advisory context, NOT reproduced locally

**50 deterministic synthetic cases:**

qsort_valid_small_ints, qsort_valid_reverse_ints, qsort_valid_duplicates, qsort_valid_already_sorted, qsort_valid_single_element, qsort_valid_zero_elements, qsort_valid_records_by_key, qsort_equal_elements_order_unspecified, qsort_not_stable, qsort_comparator_negative_zero_positive, qsort_boolean_comparator_not_enough, safe_int_comparator_relational, safe_int_comparator_branchless, subtraction_comparator_overflow_triplet, subtraction_comparator_nontransitive, subtraction_comparator_not_passed_to_qsort, random_comparator_not_run, stateful_flipping_comparator_not_run, cyclic_modulo_comparator_not_run, nan_like_partial_order_not_run, inconsistent_equal_comparator_not_run, comparator_total_order_checker_pass/fail, comparator_antisymmetry_checker_pass/fail, comparator_transitivity_checker_pass/fail, bsearch_found_sorted_array, bsearch_missing_sorted_array, bsearch_requires_sorted_input, bsearch_unsorted_input_not_run, bsearch_comparator_consistency, qsort_size_parameter, qsort_nmemb_size_t, qsort_void_pointer_cast, qsort_element_size_mismatch_not_run, qsort_null_base_zero_count_scope, qsort_null_base_positive_count_not_run, qsort_r_posix_gnu_bsd_portability, qsort_s_annex_k_context, global_state_comparator_context, function_pointer_overhead_context, std_sort_context_not_tested, rust_java_safety_context_not_tested, glibc_malloc_fallback_not_reproduced, glibc_oob_vulnerability_not_reproduced, cve_boundary_context, dynamic_linking_patch_context, production_sort_not_tested, safety_caveat.

## Methods tested

- `preserve_original_case_baseline` – preserve synthetic input/expected output
- `compiler_discovery_checker` – zig cc / cc / clang / gcc discovery
- `c_harness_compile_checker` – compile with `-std=c11 -Wall -Wextra`
- `safe_qsort_observer` – qsort with valid total-order comparators only
- `safe_bsearch_observer` – bsearch on sorted arrays with consistent comparator
- `comparator_contract_checker` – total-order / antisymmetry / transitivity checks
- `overflow_risk_marker` – INT_MIN/0/INT_MAX triplet, subtraction overflow risk
- `relational_comparator_marker` – safe `(a < b) ? -1 : (a > b) ? 1 : 0` and branchless `(a > b) - (a < b)` shapes
- `invalid_comparator_not_run_marker` – nontransitive/random/stateful/NaN-like cases never passed to qsort
- `stability_scope_marker` – qsort is not stable
- `extension_scope_marker` – qsort_r/qsort_s portability, not ISO C
- `implementation_scope_marker` – glibc OOB, CVE, C++/Rust/Java – HN context, not tested
- `wrapper_policy_marker` – project-local `compare_result` struct with total_order_ok/antisymmetry_ok/transitivity_ok/qsort_called/bsearch_called/invalid_reason/portability_scope
- `copy_size_timing_marker` – file sizes, timing, subprocess count
- `naive_qsort_comparator_marker` – assumes `a - b` is safe, boolean return is enough, qsort is stable, partial orders are OK, bsearch needs no sorted input, qsort_r is portable ISO C – **fails 12/50 cases (expected)**
- `external_sort_truth_not_tested_marker` – glibc internals, C++/Rust/Java, fuzzing, sanitizers – intentionally not tested

## Results

**Compiler:** zig cc 0.14.1 (clang 19.1.7 backend, musl target)

| Method | success | fail | skip | not_tested |
|---|---|---|---|---|
| safe_qsort_observer | 19 | 0 | 14 | 12 |
| safe_bsearch_observer | 4 | 0 | 1 | 0 |
| comparator_contract_checker | 23 | 0 | 15 | 12 |
| naive_qsort_comparator_marker | 23 | **12** | 3 | 12 |

Naive comparator fails on: boolean return, subtraction overflow triplet, subtraction nontransitive, random comparator, stateful flipping, cyclic modulo, NaN-like partial order, inconsistent equal, and all three contract checker failures (total_order / antisymmetry / transitivity).

See [RESULTS.md](RESULTS.md) for full tables, skip matrix, and per-case artifacts (`results_rows.csv`, `results_rows.json`).

## Scope / Safety

This is a **toy local lab, not a production sorting library.** Specifically NOT:

- a replacement qsort / production sorting library
- a glibc vulnerability reproducer / CVE exploit
- a malloc-failure harness / OOB reproducer
- a C++ std::sort / Rust / Java benchmark
- a stable-sort implementation / shuffle algorithm
- a sanitizer / fuzzer / static analyzer
- a proof of production sorting safety

Uses only **deterministic synthetic arrays** generated by the repo itself. Fake labels: `fake_array`, `demo_values`, `synthetic_order`, `toy_sort_case`, `example_records`, `sample_keys`, `fake_user_ids`, `demo_scores`, `synthetic_triplet`, `toy_bsearch_case`, `fictional_items`, `fake_priority_list`, `sample_duplicate_group`, `demo_cmp_case`, `synthetic_nan_like_case`, `toy_context_case`.

No real files, credentials, user records, database keys, downloaded corpora, production workloads, external validators, or network access during the benchmark.

Invalid comparators (nontransitive, random, stateful, NaN-like, inconsistent) are **marked `not_run` and never passed to `qsort`**. No intentional UB. No signed overflow execution in C – overflow risk modeled with safe checks.

## Running the lab

```bash
python3 -m py_compile generate_cases.py run_lab.py
python3 generate_cases.py   # writes cases.json (50 cases)
python3 run_lab.py          # finds compiler, builds harness, runs cases, writes RESULTS.md
```

`run_lab.py` searches for a compiler in order: `zig cc`, `cc`, `clang`, `gcc`. No root / package manager / network required. If no compiler is available, the run honestly records that and does not claim C harness validation.

## What this lab does NOT test

- glibc qsort OOB vulnerability reproduction
- malloc-failure injection / prlimit / resource limits
- C++ std::sort / Rust sort / Java comparator behavior
- Sanitizers (ASan/UBSan), Valgrind, fuzzers, static analyzers
- Production sorting correctness / huge arrays / real workloads
- qsort_r / qsort_s portability beyond marking them as extension_not_required
- External sort libraries / benchmark suites

The glibc OOB bug, malloc-failure fallback, CVE assignment, C++/Rust/Java safety models, qsort performance, and function-pointer overhead are **HN discussion context, not locally reproduced**.

## References

- HN thread: https://news.ycombinator.com/item?id=39264396
- Advisory: https://www.openwall.com/lists/oss-security/2024/01/30/7
- "Subtraction is not comparison": https://flak.tedunangst.com/post/subtraction-is-not-comparison
- C qsort: https://en.cppreference.com/w/c/algorithm/qsort
- C bsearch: https://en.cppreference.com/w/c/algorithm/bsearch
- POSIX qsort: https://man7.org/linux/man-pages/man3/qsort.3.html
- Zig compiler: https://ziglang.org/documentation/master/

## License

MIT
