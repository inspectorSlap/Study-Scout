# StudyScout

**Find the work that challenges your research claim—and keep the evidence trail.**

StudyScout is a Python toolkit and agent-assisted workflow for adversarial literature review. Define your claims and comparison criteria, record how you searched, inspect the closest experimental evidence, and preserve both provisional judgments and human decisions.

The goal is to identify the strongest precedent for a claim. StudyScout deliberately has no `NOVEL` verdict: its conclusions are bounded by the sources, evidence, and cutoff date of a particular search.

## What it does

- Freezes your claims, criteria, source policy, and seed queries before retrieval.
- Tracks query ancestry, API executions, access failures, and incomplete pagination.
- Retrieves bibliographic metadata through five source adapters.
- Deduplicates candidate records while preserving individual discovery routes.
- Records experiment-level evidence against your own criteria.
- Routes high-equivalence and `PRECEDED` proposals to human review.
- Produces a paper-by-claim matrix and checks declared expansion-round counts.

This is a **v0.1 command-line research toolkit**. It does not autonomously read and adjudicate papers, prove novelty, provide patent clearance, or enforce agent isolation. You can use it manually or with an agent that can operate local files and inspect literature.

## Try it offline

Requires **Python 3.10+**. The toolkit uses the standard library; no API key, model subscription, or dependency installation is needed for the demo.

```sh
git clone https://github.com/inspectorSlap/Study-Scout.git
cd Study-Scout
python3 scripts/demo.py --workspace ./workspace/demo
python3 -m unittest discover -s tests -v
```

The demo creates a new workspace and refuses to overwrite an existing one. All included papers, evidence, and reviewer decisions are explicitly synthetic. **No network requests occur.** Open `workspace/demo/data/synthesis/matrix.md` afterward.

## Start a real study

1. Copy `examples/study.json` and replace every example claim and criterion.
2. Initialize a separate workspace with `scripts/init_study.py`.
3. Add seed queries and freeze the controls.
4. Register queries, retrieve candidates, inspect primary evidence, and submit strong matches for human review.

See the [implementation guide](docs/IMPLEMENTATION.md) for the complete command sequence, [methodology](docs/METHODOLOGY.md) for research rules, and [agent brief](templates/AGENT-BRIEF.md) for a reusable handoff.

## Documentation

| Document | Purpose |
|---|---|
| [Implementation guide](docs/IMPLEMENTATION.md) | Configure and run your first real study |
| [Methodology](docs/METHODOLOGY.md) | Claims, cold search, scoring, review, and stopping |
| [Data model](docs/DATA-MODEL.md) | Files, identifiers, schemas, and configurable criteria |
| [Command reference](docs/COMMANDS.md) | Script purposes and CLI usage |
| [Architecture and extension](docs/ARCHITECTURE.md) | Internal boundaries and adding adapters |
| [Troubleshooting](docs/TROUBLESHOOTING.md) | Freeze failures, credentials, pagination, and review |
| [Release preparation](docs/RELEASING.md) | Publishing the toolkit without research data |
| [Validation record](docs/VALIDATION.md) | What was tested and what remains unverified |

## Source integrations

Adapters are included for OpenAlex, Crossref, Semantic Scholar, arXiv, and DBLP. Live availability, credentials, and rate limits depend on the provider. Read [provider notes](docs/IMPLEMENTATION.md#provider-notes) before making requests. Search text is transmitted to the provider you select.

StudyScout saves raw responses and normalized metadata in the research workspace. Full-text inspection and evidence coding are separate steps. The configured cutoff date must be checked during screening; the adapters do not automatically enforce it.

## Development

Run `python3 -m unittest discover -s tests -v`. Tests are offline. Contributions should include synthetic fixtures and keep failures, incomplete retrieval, and provisional judgments visible. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE). Provider data and retrieved publications retain their own terms and licenses.
