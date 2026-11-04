# Guest MVP release verification

Status: in progress. This record distinguishes implemented code, automated tests, and actual deployment evidence.

## Source and review

- Base: `8b10aa7f3eb7971cb0d3e44098543f54190b94da`.
- Branch: `feat/guest-rag-mvp`.
- One PR: [#4](https://github.com/usmanmalik10/askdocs/pull/4), currently draft.
- Exactly twenty meaningful feature commits are required; eighteen are pushed so far. The final two cover review corrections, operating documentation, and live verification.

## Verified automated baseline

[CI at commit 6a2c071](https://github.com/usmanmalik10/askdocs/actions/runs/41850426278) passed 39 Python/PostgreSQL tests, four guest-boundary unit tests, six desktop/mobile browser tests, lint, TypeScript, and the production build. Browser upload and source-dialog accessibility scans found no violations in the tested WCAG rule set.

Later review changes add the Windows-compatible runner, bounded workspace creation, malformed model-payload handling, and model-outage recovery tests. They need a new CI run on their committed revision before release.

## Cloud setup evidence

- Personal Vercel CLI identity verified as `usmanmalik10`; workspace `usman-malik`.
- AskDocs Vercel project created and linked; Node 22 selected.
- Neon resource `askdocs-db` provisioned on explicit `free_v3`, with built-in authentication disabled.
- Real Neon connection and pgvector availability verified from the Windows-compatible runner; migration `001_guest_workspace.sql` applied successfully.
- Internal and maintenance secrets stored for all three environments without displaying values.
- Gemini key stored for all three environments. Real 768-dimension embeddings, a cited 20-day leave answer, and an irrelevant-question abstention passed with `gemini-3.5-flash-lite`.
- Initial deployment failed because Vercel used pnpm 9.15.9 against the strict 9.15.0 requirement. Corepack was enabled; the rebuilt preview used 9.15.0 and built both services successfully.
- [Protected full-flow preview](https://askdocs-9dx9etznp-usman-malik.vercel.app), deployment `dpl_4mdCWWmzcUd9CdkzbBKPTYUKawcd`, passed actual browser upload, real answer and citation, saved history, abstention, cross-guest read/question/delete denial, document deletion, unauthorized cleanup rejection, and authorized cleanup.

## Gates before claiming completion

- [x] All required runtime keys present and scoped to the intended environments.
- [x] Explicit migrations applied successfully to the intended Neon database.
- [x] Real embeddings and grounded generation succeed with the selected free-tier models.
- [ ] Updated CI passes on the final feature revision.
- [x] Deployed browser upload → question → checked citation succeeds in protected preview; public production remains to be checked.
- [x] An irrelevant question abstains; an independent guest cannot read or delete another guest’s data.
- [x] Deleting test documents removes their passages and saved answers (database cascade verified in CI; history denial verified in the preview).
- [x] Cleanup authorization and an authorized cleanup invocation are verified.
- [ ] Exactly twenty feature commits and one final, accurate PR description.
- [ ] Production URL, final revision, and observed results recorded here.

## Manual acceptance check

Upload the public `leave-policy.txt` fixture, then ask how much annual leave full-time employees receive. Expect 20 working days and a citation whose passage contains that statement. Ask how leave is requested; inspect the two-week notice and manager-approval passage. Ask a question the document does not answer, such as the organization’s revenue; expect an abstention rather than a guessed number.

Open a separate private browser window. Its document list must be empty. Direct requests for the first browser’s document history, questions, or deletion must fail. Return to the first browser, delete the fixture, and verify that it disappears and its history is unavailable.

## Product completion boundary

Even when these gates pass, the result is the latest requested guest MVP. The older enterprise roadmap is not complete. Team administration, accounts, sharing, billing, OCR, and large background ingestion remain separate backlog work. Jira statuses have not been changed during this implementation.
