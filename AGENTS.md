# Local development instructions

- Work in /Users/mvexel/dev/take-uta-to-work. Preserve existing files and unrelated work.
- Martijn uses mise for Java and authorizes its use in this project. Check `mise ls java` and use the installed Java 25 explicitly: `mise exec java@temurin-25.0.3+9.0.LTS -- java ...`. Do not infer that Java is absent from /usr/bin/java failing, install system Java, or change global Java defaults.
- Docker host is Colima. Martijn started his default profile; active context is `colima`. Preserve that selection. The extra `docker` profile used earlier was stopped. Inspect current profiles/contexts before container work; do not assume Docker Desktop or change global settings. The running OTP graphs use mise Java directly.
- Read docs/status.md and docs/development.md for current evidence. Keep data/ and results/ out of Git. Public local ingestion is permitted; no feed redistribution, agreements, credentials, deployment or ongoing collection.
- Separate sampled routing results from exhaustive coverage. Verify ART entrance, route allowlists and returned legs. No invented results.
- Use an independent reviewer for routing code; direct collaborator messages are supported. Keep file ownership clear and update durable status.
