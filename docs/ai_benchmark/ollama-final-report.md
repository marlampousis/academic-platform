# Ollama final benchmark report — scoring audit v1

Project: Intelligent Academic Credentials Platform. Analysis date: 25 October 2026.

Batch: `c42e7725-2ed4-49d3-8ce9-2c05ccfcf61e`. Source archive: `ollama-final-c42e7725.zip`.

## Outcome and scope

The Ollama adapter and 66-request generation batch are complete. The local scoring audit confirmed and corrected three measurement limitations without regenerating any answer or editing the original archive. The corrections pass 48 isolated assertions. One project-side replay remains to confirm integration with the repository's shared helpers. Accurate extraction and abstention on these examples coexist with substantial alignment/reasoning errors and slow Greek responses. This is a measured local baseline, not a validated autonomous hiring or eligibility system.

Do not rerun the models to obtain better scores. Keep the original batch and the separate audit together. No overall accuracy, global hallucination rate, or provider ranking is claimed.

## Provenance and fixed settings

- User-reported current commit: `11e37293d2c5d1794724e64201fd6343ad0cb156`; working tree clean when checked after execution. These were not embedded at run time, so this is reported provenance rather than independently verified execution-time identity.
- User-reported Ollama version: `0.40.6`; model `qwen3:1.7b`, model ID prefix `8f68893c685c`, displayed size 1.4 GB. Full digest unavailable. Installed `qwen3:4b` was not tested in this batch.
- Previously reported machine: 7.8 GB RAM, Intel Core i5-10210U, Intel UHD Graphics. Runtime memory, CPU/GPU allocation, thermal state, and background load were not measured.
- Every record requests context 8192, timeout 600 seconds, maximum output 2048 tokens, temperature 0, and thinking disabled. JSON mode was used for JSON tasks and text mode for others.
- Archive SHA-256: `87b475f2c09ff1c85a1cb4a280a9362e044696d673250cc3b756f9a7b1b5e2e8`.
- There are 12 task types and 22 candidate/task cases, repeated 3 times. Earlier outputs informed prompt/reference revisions; this is a development-informed suite, not a held-out generalization study. Compare providers on the same final version and apply scoring corrections uniformly.

## Execution and timing

All 66 records parse; run IDs and (test, case, repetition) tuples are unique. Every case has repetitions 1–3. Settings, batch, provider, and model are consistent. Raw responses and rendered prompts are retained.

| Measure | Result |
|---|---:|
| Requests saved | 66/66 |
| Provider errors | 0/66 |
| Reported normal stop | 66/66 |
| Confirmed output truncations | 0/66 |
| Valid JSON on JSON tasks | 36/36 |
| Stored structural schema compliance on JSON tasks | 33/36 |
| Mean client latency | 91.59 seconds |
| Median client latency | 50.99 seconds |
| 95th percentile latency, nearest rank | 359.43 seconds |
| Minimum / maximum latency | 1.22 / 539.59 seconds |
| Sum of client request durations | 6044.68 seconds, about 100.7 minutes |

Console start/end were approximately 00:20:34–02:01:10 as printed. Differences between wall-clock log intervals and client monotonic durations prevent a precise decomposition of timing. Zero output truncation does not establish absence of input truncation or context shifting across the whole batch; server logs are not included. Test 11 reports 4441 input tokens, matching the earlier full prompt count.

These latency measurements combine request processing, loading and generation. The archive lacks separate prompt-evaluation/generation durations, and no controlled randomized order or warmup was documented. Greek QA averages 446.39 seconds and Greek JSON 378.53 seconds. This limits interactive usefulness on this machine; it is not a universal measurement of Ollama performance.

## Per-test findings

| Test | Runs | Mean latency (s) | Findings |
|---|---:|---:|---|
| test_01_extraction | 9 | 60.62 | All recorded extraction accuracy checks pass in 9/9 runs. |
| test_02_summary | 9 | 26.91 | Original coverage 66.7%; audited lexical coverage 92.6%. Word limits pass 9/9. This is mention recognition, not factuality. |
| test_03_alignment | 9 | 71.80 | Mean stored recall 53.2%; unsupported alignment flagged 4/9. Manual review finds invented requirements and unsupported AI links. |
| test_04_explainable_alignment | 9 | 149.96 | Stored schema passes 6/9. All 9 answers contain an area in both sections. Candidate C fails schema 3/3. No model-output repair applied. |
| test_05_grounded_qa | 3 | 46.41 | Course F1 1.0; course-detail accuracy corrected from 0.2 to 1.0 for all 3 runs. |
| test_06_missing_thesis | 3 | 9.02 | Required thesis-title abstention exact in 3/3. |
| test_07_missing_hindex | 3 | 10.90 | Required h-index abstention exact in 3/3. |
| test_08_evidence_retrieval | 3 | 50.82 | Known publications and years correct in 3/3; mean position-area accuracy 66.7%. Incorrect topic attribution remains. |
| test_09_potential_gaps | 9 | 31.11 | Stored gap F1 0.0 in 9/9. Outputs repeatedly provide one broad application gap; exact matching and empty-reference conventions limit semantic interpretation. |
| test_10_greek_qa | 3 | 446.39 | Language/length/item-count checks pass 3/3. Stored area coverage 0.75 partly reflects Greek inflection matching. Grammar and attribution concerns remain. |
| test_11_greek_json | 3 | 378.53 | All recorded accuracy and structure checks pass 3/3, with identical raw answers. Full input count 4441. |
| test_12_adversarial_grounding | 3 | 51.65 | Classification accuracy corrected from 0 to 1.0 for 3/3. Evidence-recognition score also 1.0; semantic evidence review remains required. Contradiction distinction untested. |

## Confirmed scoring corrections

### Test 2: summary evidence recognition

The evaluator previously recognized only complete publication/project titles. The prompt asks for a short summary mentioning research experience, so documented publication venues and project acronyms are also legitimate lexical references. The updated expected data derives venues and acronyms from all three supplied candidate records; it is not populated from generated answer text. The evaluator now recognizes those additions.

Acronym matching preserves internal punctuation and word boundaries. In particular, the project acronym SMART-GRID must not match the course title Smart Grid Technologies. Negative tests cover this collision and invented venues. Generic references such as 'leading journals' still do not count as known publication references; a paraphrase omitting a known title/acronym may still be missed.

Across the nine summaries, the mean stored coverage changes from 0.6667 to 0.9259 (50/54 category checks). Five runs recognize all six categories; four recognize five of six. Original word counts and word-limit checks are preserved. Lexical coverage cannot establish truth, negation handling, complete coverage of every research area, or academic tone. Unsupported prestige wording and factual embellishment remain review concerns.

Changed project files: `evaluators/test_02.py` and `expected/test_02_expected.json`.

### Test 5: multiline JSON records

The previous detail scorer required every detail to be on the same line as its course title. In each saved answer, the course was a JSON object with details on separate lines, so only title checks passed. This produced 0.2 despite correct content.

The corrected evaluator associates fields within parsed JSON course records. All 15 requested values match the embedded source per run, giving detail accuracy 1.0 in all three runs (45/45 field checks). It also handles reordered records, counts unexpected/duplicate records against precision, rejects missing or malformed details, and does not pool information across unrelated records. Conflicting duplicate records are reported. Non-JSON responses retain the original conservative same-line baseline; multiline prose is still a documented limitation.

The expected Test 5 data is unchanged. Changed file: `evaluators/test_05.py`.

### Test 12: claim punctuation and applicability

All four expected claim strings end in full stops; the model's claim fields omit those stops. The original normalizer preserved punctuation, so all claims failed exact lookup and the stored classification/evidence metrics became zero. Normalization now ignores punctuation and typography while preserving the words, numbers, and negation. It does not use fuzzy semantic matching.

All four supplied claim labels are recognized and correctly classified in every run: PhD and Computer Vision publications supported; teaching duration over ten years and h-index 25 not supported. Classification accuracy changes from 0 to 1.0 in 3/3 runs. Duplicate or additional claims are penalized through the denominator, and supported-versus-unsupported distinction requires both categories to be classified correctly.

No reference claim is contradicted. Therefore `unsupported_contradicted_distinction` is null (untested), rather than claiming a successful distinction from this sample. A synthetic contradictory reference exercised that branch in the isolated checks. Do not add a new contradictory claim to the frozen batch retrospectively.

The evidence score remains a recognition heuristic: supported items match known evidence phrases; unsupported/contradicted items require nonempty evidence but are not semantically verified. `evidence_review_required` is true. An evidence score of 1.0 is not proof that every explanation is grounded. Runs 2/3 omit the h-index issue in the overall assessment despite classifying it in the claim list.

Expected Test 12 data is unchanged. Changed file: `evaluators/test_12.py`.

## Unchanged model failures and other measurement limitations

All nine Test 4 answers place at least one area in both sections. Six are structurally valid, with logical-consistency false. Candidate C has empty evidence arrays and fails schema in all three repetitions. The model infers Deep Learning from energy-system titles without supplied support. Candidate A omits Machine Learning alignment despite explicit evidence. High aligned-label F1 alone conceals these errors.

Candidate B's later Test 4 responses cite real journal names rather than the reference's accepted article/project titles for research experience, producing a false evidence check. This remaining lexical limitation is documented rather than expanding the rubric again. Subject taxonomies such as AI versus related methods need consistent operational definitions; not every broad association is a demonstrated specific qualification.

Test 3 adds industry/international requirements not supplied by the position and overstates candidate C's AI/ML alignment. Test 8 incorrectly assigns Computer Vision/Deep Learning to a clinical decision-support paper whose supplied description only supports ML. Test 9 repeatedly produces one broad application-related gap and misses expected specific subfields. Its stored zero F1 also depends on exact requirement matching and empty-reference conventions, so it is not a full semantic score.

For Greek QA, repetition 1 substitutes 'υπολογιστική έρευνα' for Computer Vision. Repetitions 2/3 mention Computer Vision but inflected Greek causes the exact matcher to miss another area. They also attribute supervised-learning/neural-network-evaluation detail to the project that is supplied under teaching descriptions rather than that project. The language heuristic, recognized-title indicator and item count do not validate all facts or grammar.

All stored qualitative and safety ratings remain null, meaning unassessed. Targeted observations in this report do not replace a scored human rubric, independent annotation, or inter-rater agreement. Eight of 22 cases have identical raw responses across all repetitions; 14 have identical original metric records. Temperature 0 does not guarantee identical outputs, and repeated identical mistakes are not reliable correctness. Three repetitions of a small fixed dataset support descriptive comparisons only.

## Validation, artifacts, and closure

Validation covered 48 isolated assertions: punctuation tolerance versus altered claim meaning/numbers, missing/extra/duplicate claims, a synthetic contradiction case, JSON field association, missing/swapped values, unexpected/duplicate courses, a text-format fallback, known/unknown venues, and acronym boundaries. Python files compile and JSON references parse. All 15 affected saved runs were replayed locally. Standard precision/recall/F1 arithmetic was supplied in the isolated environment because the project's shared automatic.py was not attached. Word-count metrics were preserved, not recalculated. Run the provided script in the project to verify integration with its real shared helpers.

Artifacts:
- `ollama-final-metrics.json` preserves the 66 original per-run metrics and adds a separate `scoring_audit_v1` ledger.
- `ollama-scoring-audit-v1.json` contains 15 original/rescored metric pairs, changed fields, run IDs, source archive hash, and scorer/reference hashes.
- `rescore_ollama_audit.py` provides project-side replay without a model request. It refuses to overwrite an existing audit output. The archive and generated answers remain untouched.

Next: install the four corrected files and the replay script, replay against the same archive, then run the mock integration check. Commit the scoring changes and documentation on main. A change of scoring after generation must be disclosed as an audit correction and applied uniformly to all future provider results. Once project-side checks pass and the documented limitations are accepted, close this Ollama implementation/baseline sprint and proceed to the next provider. Further Ollama tuning, extra models and LangChain integration are separate work.
