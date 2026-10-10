# Case study: does a different array layout make binary search faster?

**A real, bounded literature search about Eytzinger layout, software prefetching, and concurrent readers.** Run on 27 September 2026 (UTC). This is a research-workflow demonstration, not a new search algorithm or a rerun of performance benchmarks.

Eytzinger layout stores a binary search tree breadth-first in an array. The question here is deliberately narrower than “is it fast?”: does the literature test a specific implementation, comparator, working-set size, and concurrency setting?

**Read the results within these bounds:** 49 candidate records include 13 awaiting full text. Of eight recorded retrieval executions, five hit a page limit, two were manually stopped, and one was rate-limited. Three human reviews remain pending; no expansion rounds were completed, and stopping is **NOT SATISFIED**. The findings below are provisional judgments about inspected sources, not a completeness claim.

## What the run found

| Frozen claim | Agent proposal | Why |
|---|---|---|
| C1: Eytzinger with branch-free traversal and prefetch can beat optimized sorted binary search above last-level cache | **PRECEDED, 5/5 — human review pending** | Khuong and Morin's Figure 22 includes the specified comparison. |
| C2: the same implementation retains that advantage with concurrent readers | **Unresolved** | The earlier paper's threaded figure uses a Btree comparator. A later, close comparison reports near parity under a different batched implementation. |

Read the [evidence report](REPORT.md), then inspect the generated [matrix](snapshot/data/synthesis/matrix.md) and [pending review packets](snapshot/data/reviews/BATCH-001.md) ([additional partial-precedence review](snapshot/data/reviews/BATCH-002.md)). Scores measure experimental correspondence, not confidence or effect size. A close experiment can fail to support the proposed result: EV-000003 deliberately records 4/5 with `UNCERTAIN`.

The useful result is the distinction between a topic match and an experiment match. “The paper discusses threads” is insufficient when its plotted comparator differs from the claim.

## Replay in under a minute

From the repository root, with Python 3.10+:

```sh
python3 scripts/replay_case.py --case case-studies/eytzinger-search --workspace workspace/eytzinger-replay
```

Use a new destination; the command refuses to overwrite an existing workspace. It checks the bundled SHA-256 manifest, copies the snapshot, validates its records and frozen controls, and regenerates the matrix and stopping status byte-for-byte. No API keys, third-party Python packages, or network requests are needed.

**Replay is not a new literature search.** It does not reproduce search-engine rankings, confirm that a source is unchanged, rerun the cited benchmarks, or perform human adjudication. Checksums detect changed bundled bytes; they are not independent attestation of the research process.

## What is included

- [Frozen study specification](study.json), [prospective protocol](PROTOCOL.md), and original freeze hashes.
- Six actual API attempts: five returned pages, one HTTP 429. Raw metadata responses and normalized result rows are preserved, with two public email occurrences removed from one response; [redaction hashes](REDACTIONS.json) identify that change.
- 50 API result routes yielding 48 distinct bibliographic records, plus one original benchmark report imported from web search: **49 candidate records**, not 49 independent studies.
- [Screening decisions](snapshot/data/corpus/screening.csv): 33 exclusions at title/metadata level, 13 leads awaiting full text, and three included records representing two research families. The preprint and journal entries belong to the same family.
- Three initial web queries in one merged response (39 visible leads), and one registered follow-up (24 visible leads). Web leads are separate from the API corpus count. Only the selected follow-up report was imported.
- Three evidence proposals, three pending mandatory reviews under the current review rule, and **stopping NOT SATISFIED**.

## Limits worth reading before sharing

This was one agent-assisted worked example with prior general knowledge of the topic, not two independent agents or a blinded discovery evaluation. The schema's `STAGE_1_COLD` label means no injected candidate list was used; it does not prove model ignorance or process isolation. No human has adjudicated the proposals.

The operator did not know the Eytzinger result in advance. The central paper entered as OpenAlex position 2 for a frozen seed query; the [discovery route](snapshot/data/corpus/discoveries.csv) records this. The agent's general topic knowledge is disclosed because it may shape search terms, not because the paper was supplied or the result was known.

The one-page API budget left five capped executions; one OpenAlex request was rate-limited. Crossref returned mostly unrelated metadata. These are retained, not cleaned into an artificially successful search. Thirteen corpus leads remain unresolved, most web leads were not inspected in full, and no complete expansion rounds were claimed. The search stopped early within its maximum budget after finding contrasting examples. This is not saturation, a systematic review, or evidence that C2 is novel or false everywhere.

Publications were inspected through public sources. The package contains bibliographic metadata and original notes, not PDFs, article copies, author code, private research, or fabricated reviews. Publication and provider terms remain their own; the toolkit's MIT license does not relicense them.

## Repeat the live process

Initialize a new workspace from `study.json` using the [implementation guide](../../docs/IMPLEMENTATION.md), copy the three seed rows and source register from the snapshot, and freeze before retrieval. Execute each seed once against Crossref and OpenAlex with `--page-size 10 --max-pages 1`; the exact successful and failed API commands are in [live-run-commands.json](live-run-commands.json). Use new execution identifiers in a fresh workspace.

The [query registry](snapshot/data/searches/queries.csv) records the follow-up text and [parent links](snapshot/data/searches/query-parents.csv). The [retrieval ledger](snapshot/data/searches/retrieval-ledger.csv) preserves limits and failures. Web discovery and primary inspection were agent-operated, outside the Python adapters; their records were entered afterward with date-only timestamps rather than invented exact times. Search results will change. Do not overwrite this historical snapshot with a new run.
