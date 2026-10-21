# Demo seed — the film's forged skills

These four JSON files are the skills the Forge synthesized on camera
(54 → 55 tools). A fresh deploy starts from the 51 base tools, so the start
command in `render.yaml` copies them into `state/synthesized_skills/` at boot.
That keeps the live cockpit reading **55 abilities · 4 learned here**, exactly
as the film shows.

**Never seed anything else from `state/`:**

- `brain_config.json` holds the household's API key. Keys belong in Render's
  environment variables, never in git.
- `audit.jsonl` / `receipts.jsonl` are hash-chained. Copying one without the
  other breaks verification.
- `memory*.db`, `*.lock`, `warroom_ipc.jsonl` are runtime junk or internal
  chatter, not demo content.

To re-mint a forged skill in a fresh deploy instead, use the Forge panel in
`/echo` or call `POST /api/forge/synthesize` (rate-limited).
