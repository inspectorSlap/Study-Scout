# Contributing

StudyScout values reproducible research records and explicit uncertainty.

For bugs, include the Python version, command, expected behavior, and a minimal synthetic reproduction. Do not attach private research workspaces, API keys, unpublished claims, or full-text papers to public issues.

For changes, explain the research failure being prevented and add an offline test. Run:

```sh
python3 -m unittest discover -s tests -v
```

Keep examples synthetic. Preserve original proposals when recording review decisions. Do not make failed retrieval look exhaustive, unreviewed judgments look adjudicated, or absence of a result look like proof of novelty. Schema changes must update writers, readers, validators, examples, and documentation together.

New dependencies or orchestration layers should solve a demonstrated problem; the initial toolkit is standard-library only. Contributions are made under the repository's MIT license.
