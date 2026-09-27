# Troubleshooting

| Symptom | Action |
|---|---|
| Workspace already exists | Choose a new directory. Initialization and the demo deliberately refuse overwriting. |
| Missing study specification | Set `STUDYSCOUT_WORKSPACE` to the initialized workspace in the same shell. |
| Study is not frozen | Add seeds, validate, then run `freeze_study.py`. |
| Frozen artifact changed | Inspect the change. Restore the exact original bytes for accidental edits, or create a new versioned workspace for an intentional revision. |
| Duplicate execution ID | Preserve the old record and choose a fresh ID. A rerun is a new execution. |
| HTTP 429 / RATE_LIMITED | Wait according to provider guidance, check your budget/key, then retry as a new execution. Do not call it source exhaustion. |
| API_FAILURE or ACCESS_BLOCKED | Inspect the execution and raw response. Validate credentials, service status, and API format. Partial results remain partial. |
| PAGE_LIMIT_REACHED | You reached your configured budget. Document the gap; this runner does not automatically resume a cursor. |
| Unknown evidence criteria | Use exactly the names from the frozen `study.json`, including explicit unknown values. |
| Mandatory judgment remains provisional | Obtain a real human decision and apply it with the assigned batch ID. |
| Review batch is empty | It includes only unassigned pending mandatory items. Previously assigned items remain in their original batch. |
| Stopping checker exits 0 but says NOT SATISFIED | Zero means the declared records are consistent. Read the reported stopping condition separately. |
| Validation fails after interruption | Review the affected files against your private backup. CSV writes across files are not transactional. |

Live API calls are optional. You can import manually collected normalized results and retain the same evidence/review workflow. See `log_retrieval.py --help` and `examples/results.csv`.
