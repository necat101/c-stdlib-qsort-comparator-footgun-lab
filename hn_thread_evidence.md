# HN Thread Evidence — c-stdlib-qsort-comparator-footgun-lab

HN thread accessed via Hacker News Firebase API CLI before writing README.

- **Thread:** https://news.ycombinator.com/item?id=39264396
- **Title:** "Out-of-bounds read and write in the glibc's qsort()"
- **Linked advisory:** https://www.openwall.com/lists/oss-security/2024/01/30/7
- **HN API fetch:** 129 nodes (story + 128 comments)
- **Raw artifact:** `hn_nodes_sanitized.json` (~68 KB)

## Thread Sentiment Summary

The HN discussion around glibc's qsort OOB bug broadened far beyond the advisory itself into C comparator contracts, language safety models, and CVE policy.

Key themes observed in the thread (paraphrased, not quoted):

1. **"Subtraction is not comparison"** – multiple commenters discussed `return a - b` as an obvious but broken integer comparator due to signed overflow. The safe pattern `return (a > b) - (a < b);` was explicitly posted with godbolt link, noting it avoids overflow and is branchless.

2. **qsort comparator contract / total ordering** – ISO C 7.2.5/4 was cited verbatim: comparison function results shall define a total ordering on the array. Several commenters asked whether nontransitive comparators mean UB for all qsort users, or only when nontransitivity is actually triggered.

3. **"Holding it wrong" vs "stdlib should defend itself"** – Extended debate about whether invalid comparators causing memory corruption is a library bug or caller bug. One side: "you handed qsort nonsense input, what did you expect?" Other side: "invalid comparators shouldn't lead to OOB memory access – hard failure is acceptable." Commenters noted blaming users ("holding it wrong") has not succeeded at scale.

4. **CVE / security boundary debate** – Whether glibc should issue a CVE. Arguments about mandatory upgrade costs in regulated industries vs encouraging users to audit their comparator code. CVSS scoring reliability was questioned.

5. **Signed integer overflow** – Extended discussion of signed vs unsigned integer semantics in C, Rust overflow-in-debug/panic vs release-wrapping, and calls for overflow to trap by default.

6. **qsort stability** – Equal elements' relative order is unspecified; qsort is not stable.

7. **bsearch comparator consistency** – bsearch has the same comparison-consistency problem: the array must be sorted and the comparator must be consistent with that order.

8. **NaN / partial orders / random comparators** – NaN-style partial orders break qsort; random comparators / "shuffle by sort" are invalid.

9. **C vs C++ std::sort vs Rust vs Java** – std::sort also requires well-behaved comparators (gcc bugzilla 41448 cited). Rust's Ord is a safe trait – invalid Ord won't cause UB, though results are nonsense. Java comparator contracts discussed.

10. **qsort function-pointer overhead** – "qsort is really slow" and "sometimes barely usable" – function pointer callback overhead came up. Suggestions to wrap std::sort for C.

11. **qsort_r / qsort_s portability** – Context-carrying comparators: qsort_r (GNU vs BSD signature differs), qsort_s (Annex K).

12. **glibc malloc fallback / OOB details** – Surprise that "qsort can malloc". The advisory's OOB was tied to malloc-failure fallback behavior with a nontransitive comparator.

13. **Dynamic linking / patch deployment** – glibc fix applies system-wide via dynamic linking, unlike template-based std::sort which requires recompiling clients.

14. **Comparison operators in C** – C standard explicitly defines `true` as `1` and `false` as `0` (C standard 6.5.8, 7.18 bool macros) – relevant to why `(a > b) - (a < b)` is valid.

15. **Memory safety / language choice** – Extended WUFFS / Rust / Ada / Pascal discussion about whether C/C++ projects should rewrite in safer languages or adopt UB-proof tooling.

The linked advisory is about a specific glibc qsort out-of-bounds read/write triggered under malloc-failure fallback with a nontransitive comparator. The HN thread uses this as a springboard for the broader comparator-contract debate summarized above.

## Lab connection

This toy lab connects the HN debate to a local C harness: comparator return conventions (negative/zero/positive not boolean), total-order/antisymmetry/transitivity checks, signed-overflow comparator hazards, safe relational comparator pattern `(a > b) - (a < b)`, duplicate/equal handling, qsort stability caveats, bsearch sorted-array preconditions, invalid-comparator not_run markers, and qsort_r/qsort_s portability markers – all reflecting actual thread themes, not just the advisory title.

No glibc vulnerability reproduction, no malloc-failure injection, no C++/Rust/Java code – this is a toy C stdlib qsort comparator contract lab.
