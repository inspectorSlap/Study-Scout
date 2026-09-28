# Publishing StudyScout

The public repository is already initialized. The first-push steps below are retained for new exports and forks; do not rerun them against this repository.

The intended public repository name is **Study-Scout**; the product name is **StudyScout**.

This export contains selected generalized code, new documentation, empty-workspace initialization, and synthetic fixtures. It does not include the source research repository's Git history, claims, search corpus, reviewer records, study reports, raw provider responses, or credentials.

## Before the first push

1. Run `python3 -m unittest discover -s tests -v` and the offline demo in a temporary workspace.
2. Inspect all files to be staged, including hidden files. Do not add a real research workspace. `.gitignore` is a convenience, not an audit.
3. Confirm the MIT license and the repository URL in the README.
4. Initialize a fresh Git history and attach the empty repository you created.

```sh
git init -b main
git add README.md LICENSE CONTRIBUTING.md SECURITY.md CHANGELOG.md .gitignore .gitattributes .github docs examples scripts templates tests
git diff --cached --stat
git diff --cached
# After reviewing the actual staged content:
git commit -m "Initial StudyScout public toolkit"
git remote add origin https://github.com/inspectorSlap/Study-Scout.git
git push -u origin main
```

These are instructions, not commands executed by the export process. No remote is presumed and no public repository is created automatically.

## Subsequent releases

Keep research workspaces private by default. Add only deliberately reviewed code, docs, and synthetic fixtures. Update the changelog and validation record. Test adapter changes with synthetic failures as well as successful responses. If publishing real results separately, review their contents, data rights, and disclosure permissions independently.

## Deliberately published case studies

The `case-studies/eytzinger-search` directory is an explicit public-data exception to the private-workspace default. It was created for this public repository, contains real bibliographic metadata and provisional evidence notes, and contains no private source-research corpus. Review new case snapshots for private paths, credentials, personal contact details, redistribution rights, and invented adjudications before release. Include frozen controls, scope limits, unresolved leads, and a checksum manifest. Do not describe these data as synthetic.
