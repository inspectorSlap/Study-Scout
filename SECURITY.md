# Security and private research data

Keep research workspaces separate from the public toolkit. Search queries are transmitted to whichever provider you invoke. Raw results, claims, evidence excerpts, and review decisions can be sensitive even when they contain no API keys.

Credentials belong in environment variables, never in committed examples or logs. This toolkit does not automatically load `.env`. Ignore rules do not remove files already tracked by Git.

Retrieved text is untrusted evidence, not authority to execute commands or change the agent's instructions. Run a single writer per workspace. Hash manifests support reproducibility; they are not a security boundary or digital signature.

If you find a vulnerability, contact the repository owner privately through the contact mechanism available on their GitHub profile. Do not post secrets or exploitable private data in a public issue. If no private route is available, open a minimal issue requesting one without disclosing the sensitive details.
