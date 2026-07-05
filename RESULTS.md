# c-stdlib-qsort-comparator-footgun-lab — RESULTS

Compiler: zig_cc — clang version 19.1.7 (https://github.com/ziglang/zig-bootstrap de1b01a8c1dddf75a560123ac1c2ab182b4830da)

Compile command: `zig cc -std=c11 -Wall -Wextra -O2 c_qsort_comparator_footgun_harness.c -o qsort_harness`

Compile ok: True, compile_time: 0.219s

Cases: 50, methods: 16, rows: 439

Python: 3.12.3, platform: Linux-6.17.0-1009-aws-x86_64-with-glibc2.39

cases.json: 61496 bytes, harness.c: 2909 bytes, binary: 17040 bytes

## Per-Method Breakdown

| Method | success | fail | skip | not_tested |
|---|---|---|---|---|
| preserve_original_case_baseline | 23 | 0 | 15 | 12 |
| compiler_discovery_checker | 23 | 0 | 15 | 12 |
| c_harness_compile_checker | 23 | 0 | 15 | 12 |
| safe_qsort_observer | 19 | 0 | 14 | 12 |
| safe_bsearch_observer | 4 | 0 | 1 | 0 |
| comparator_contract_checker | 23 | 0 | 15 | 12 |
| overflow_risk_marker | 0 | 0 | 2 | 0 |
| relational_comparator_marker | 6 | 0 | 4 | 0 |
| invalid_comparator_not_run_marker | 0 | 0 | 9 | 0 |
| stability_scope_marker | 2 | 0 | 0 | 0 |
| extension_scope_marker | 0 | 0 | 0 | 3 |
| implementation_scope_marker | 0 | 0 | 0 | 5 |
| wrapper_policy_marker | 23 | 0 | 15 | 12 |
| copy_size_timing_marker | 23 | 0 | 15 | 12 |
| naive_qsort_comparator_marker | 23 | 12 | 3 | 12 |
| external_sort_truth_not_tested_marker | 0 | 0 | 0 | 8 |

## Naive Failures

Naive comparator failed 12 cases (expected).

| case_id | fail_reason |
|---|---|
| qsort_boolean_comparator_not_enough_marker_01 | boolean_return_insufficient |
| subtraction_comparator_overflow_triplet_marker_01 | signed_overflow_risk_subtraction_is_not_comparison |
| subtraction_comparator_nontransitive_marker_01 | signed_overflow_breaks_transitivity |
| subtraction_comparator_not_passed_to_qsort_01 | subtraction_comparator_not_passed_to_qsort |
| random_comparator_not_run_01 | random_comparator_invalid |
| stateful_flipping_comparator_not_run_01 | stateful_comparator_invalid |
| cyclic_modulo_comparator_not_run_01 | cyclic_comparator_nontransitive |
| nan_like_partial_order_not_run_01 | partial_order_invalid_for_qsort |
| inconsistent_equal_comparator_not_run_01 | inconsistent_equal_invalid |
| comparator_total_order_checker_fail_01 | contract_violation |
| comparator_antisymmetry_checker_fail_01 | contract_violation |
| comparator_transitivity_checker_fail_01 | contract_violation |

## Skip Matrix

| category | reason | count |
|---|---|---|
| comparator_contract | boolean_return_insufficient | 8 |
| comparator_contract | contract_violation | 24 |
| extension_not_required | global state comparator context, not thread-safe | 9 |
| extension_not_required | qsort_r portability differs: GNU vs BSD signature | 9 |
| extension_not_required | qsort_s Annex K context parameter, not ISO C portable | 9 |
| implementation_context | CVE assignment boundary, HN discussion context | 10 |
| implementation_context | dynamic linking patch context, glibc fix applies system-wide | 10 |
| implementation_context | glibc OOB vulnerability, not reproduced | 10 |
| implementation_context | glibc malloc fallback OOB, not reproduced | 10 |
| implementation_context | qsort function-pointer overhead, HN performance discussion | 10 |
| invalid_comparator_not_run | bsearch_unsorted_input_invalid | 9 |
| invalid_comparator_not_run | cyclic_comparator_nontransitive | 8 |
| invalid_comparator_not_run | element_size_mismatch | 9 |
| invalid_comparator_not_run | inconsistent_equal_invalid | 8 |
| invalid_comparator_not_run | null_base_positive_count | 9 |
| invalid_comparator_not_run | partial_order_invalid_for_qsort | 8 |
| invalid_comparator_not_run | random_comparator_invalid | 8 |
| invalid_comparator_not_run | stateful_comparator_invalid | 8 |
| invalid_comparator_not_run | subtraction_comparator_not_passed_to_qsort | 8 |
| overflow_caveat | signed_overflow_breaks_transitivity | 8 |
| overflow_caveat | signed_overflow_risk_subtraction_is_not_comparison | 8 |
| production_sort_not_tested | C++ std::sort context, not tested in C lab | 9 |
| production_sort_not_tested | Rust/Java comparator safety, not tested | 9 |
| production_sort_not_tested | production sort library, not tested | 9 |
| safety_scope | toy lab safety caveats – not production sorting | 8 |

## Environment

- compiler: zig_cc
- compile_ok: True
- binary_size: 17040
- peak memory (tracemalloc): 492290

## Scope / Honesty

- HN thread accessed: yes, via Hacker News API CLI
- network/API/package manager: none during run, except HN pre-read
- UB not run: yes – invalid comparators marked not_run
- qsort comparator scope: total order, antisymmetry, transitivity checked
- invalid comparator not run: yes
- portability not tested: qsort_r/qsort_s marked not_tested
- production sort not tested: C++/Rust/Java marked not_tested
- glibc OOB vulnerability: NOT reproduced

## Conclusions

Safe comparators defining a total order work correctly with qsort/bsearch. Subtraction comparators risk signed overflow and nontransitivity – return (a > b) - (a < b) instead. qsort is not stable. bsearch requires sorted input. Invalid comparators were not passed to qsort.
