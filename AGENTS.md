# Local development instructions

- Preserve existing files and unrelated work. Read docs/project.md, docs/status.md and docs/development.md for public technical scope and evidence.
- Use the existing mise Java installation where available: `mise exec java@temurin-25.0.3+9.0.LTS -- java ...`. Do not install system Java or change global defaults without authorization. The local OTP scripts use Java directly; inspect existing Docker/Colima settings before container work.
- Keep data/ and results/ out of Git. Do not redistribute feed snapshots, accept agreements, create credentials, publish services or start ongoing collection without appropriate authorization.
- This is the public code repository. Organization coordination, team charters, participant feedback and internal design planning live in a separate private repository. Do not restore those records here or infer publication authority from their historical presence in Git.
- Separate sampled routing results from exhaustive coverage. Verify ART entrance, route allowlists and returned legs. No invented results.
- Obtain independent review for meaningful routing changes and preserve clear file ownership. Commit only completed, reviewed milestones with explicit file staging; stop on concurrent edits or remote divergence. Never force-push or rewrite history without explicit authorization.
