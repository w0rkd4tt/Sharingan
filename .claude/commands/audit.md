# /audit — Whitebox Source Code Audit

## Usage
`/audit <REPO_PATH>`

## Steps
1. **Mount repository**: Verify path exists, detect languages.
2. **Load Memory Store**: Check for previous sessions on this repo.
3. **Execute whitebox pipeline** (follow coordinator.md):
   - Step 1: Receive target
   - Step 2: Spawn `recon-src`
   - Step 3: Spawn `normalize` ×language (parallel)
   - Step 4: Spawn `graph` (persistent thread)
   - Steps 5-7: Hunt loop (chain scan → fan-out hunters → harvest)
   - Step 8: Spawn `reporter-src`
   - Step 9: Outcome evaluation
