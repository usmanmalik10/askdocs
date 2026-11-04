# Guest MVP release verification

Status: the requested guest MVP is published and passed real production acceptance on 4 November 2026. This record distinguishes implementation, automated tests, and actual deployment evidence. The earlier enterprise roadmap is outside this release.

## Source and review

- Base: `8b10aa7f3eb7971cb0d3e44098543f54190b94da`.
- Branch: `feat/guest-rag-mvp`.
- One PR: [#4](https://github.com/usmanmalik10/askdocs/pull/4). Its current integration and check status are visible on GitHub.
- Twenty meaningful feature commits. The nineteenth contains review corrections and the handbook; the twentieth records production acceptance and the bundled font notice.
- Verified application revision: `df47b86ea20f89cf82bb768d99b982b1244a6729`. The twentieth commit changes release documentation and includes the original Inter font license; it does not change application logic.

## Verified automated baseline

[CI at commit 6a2c071](https://github.com/usmanmalik10/askdocs/actions/runs/41850426278) passed 39 Python/PostgreSQL tests, four guest-boundary unit tests, six desktop/mobile browser tests, lint, TypeScript, and the production build. Browser upload and source-dialog accessibility scans found no violations in the tested WCAG rule set.

[CI for the reviewed application revision](https://github.com/usmanmalik10/askdocs/actions/runs/41858249436) passed **49 Python/PostgreSQL tests, four guest-boundary unit tests, and six desktop/mobile browser scenarios**: 59 automated test cases in total. Lint, TypeScript, frozen dependency installation, and the production build passed. This includes Windows startup, bounded workspace creation, malformed model output, transient provider retry, quota non-retry, total-operation cancellation, and rollback after timeout.

The final documentation revision and its merge must also have passing [PR checks](https://github.com/usmanmalik10/askdocs/pull/4/checks). Those live checks are the authoritative result for the current head; this document cannot embed its own future commit hash.

## Cloud setup evidence

- Personal Vercel CLI identity verified as `usmanmalik10`; workspace `usman-malik`.
- AskDocs Vercel project created and linked; Node 22 selected.
- Neon resource `askdocs-db` provisioned on explicit `free_v3`, with built-in authentication disabled.
- Real Neon connection and pgvector availability verified from the Windows-compatible runner; migration `001_guest_workspace.sql` applied successfully.
- Internal and maintenance secrets stored for all three environments without displaying values.
- Gemini key stored for all three environments. Real 768-dimension embeddings, a cited 20-day leave answer, and an irrelevant-question abstention passed with `gemini-3.5-flash-lite`.
- Initial deployment failed because Vercel used pnpm 9.15.9 against the strict 9.15.0 requirement. Corepack was enabled; the rebuilt preview used 9.15.0 and built both services successfully.
- [Protected full-flow preview](https://askdocs-9dx9etznp-usman-malik.vercel.app), deployment `dpl_4mdCWWmzcUd9CdkzbBKPTYUKawcd`, passed actual browser upload, real answer and citation, saved history, abstention, cross-guest read/question/delete denial, document deletion, unauthorized cleanup rejection, and authorized cleanup.
- GitHub app access was granted for the personal AskDocs repository, and the Vercel project is connected to `usmanmalik10/askdocs` with production branch `main`.

## Public production evidence

- Public URL: **[askdocs-self.vercel.app](https://askdocs-self.vercel.app)**.
- Accepted production deployment: [`dpl_6yRRVh8jbdz5xWv9YVBus77mhfEA`](https://vercel.com/usman-malik/askdocs/6yRRVh8jbdz5xWv9YVBus77mhfEA), built from clean application revision `df47b86ea20f89cf82bb768d99b982b1244a6729`.
- Unauthenticated HTTP access returned 200 and the AskDocs page title. The real browser used no Vercel protection token.
- The browser uploaded the fictional leave-policy fixture, asked how many working days of annual leave full-time employees receive, and got **20 working days** with a verified quote. The source dialog displayed the actual extracted passage.
- A revenue question, unsupported by the document, returned an abstention. Both answers persisted through a page reload.
- An independent browser had an empty library. Attempts to read, ask about, or delete the first browser’s document all returned not found.
- Deleting the test document removed it from the library and made its history unavailable. The successful acceptance run erased its own guest workspaces afterward.
- Anonymous cleanup returned unauthorized. An authenticated maintenance call succeeded, reporting zero expired workspaces and zero old counters at verification time.
- Subsequent automatic deployments may replace this accepted deployment after the final documentation commit and merge. The public alias remains the entry point, and CI/production state must be rechecked after integration.

## Gates before claiming completion

- [x] All required runtime keys present and scoped to the intended environments.
- [x] Explicit migrations applied successfully to the intended Neon database.
- [x] Real embeddings and grounded generation succeed with the selected free-tier models.
- [x] Reviewed application CI passes; current documentation/merge checks are linked above and required before integration.
- [x] Deployed browser upload → question → checked citation succeeds without Vercel authentication in public production.
- [x] An irrelevant question abstains; an independent guest cannot read or delete another guest’s data.
- [x] Deleting test documents removes their passages and saved answers (database cascade verified in CI; history denial verified in the preview).
- [x] Cleanup authorization and an authorized cleanup invocation are verified.
- [x] Delivery uses twenty feature commits and one PR; the PR description and current count are available on GitHub.
- [x] Production URL, accepted application revision, and observed results are recorded here.

## Manual acceptance check

Upload the public `leave-policy.txt` fixture, then ask how much annual leave full-time employees receive. Expect 20 working days and a citation whose passage contains that statement. Ask how leave is requested; inspect the two-week notice and manager-approval passage. Ask a question the document does not answer, such as the organization’s revenue; expect an abstention rather than a guessed number.

Open a separate private browser window. Its document list must be empty. Direct requests for the first browser’s document history, questions, or deletion must fail. Return to the first browser, delete the fixture, and verify that it disappears and its history is unavailable.

## Product completion boundary

The delivered result is the latest requested guest MVP. The older enterprise roadmap is not complete. Team administration, accounts, sharing, billing, OCR, and large background ingestion remain separate backlog work. Jira statuses have not been changed during this implementation.

Free-tier model quotas and temporary provider failures remain external limits. Requests retry one temporary provider failure within a 65-second operation deadline; persistent failures remain visible and do not produce invented answers. Source matching verifies quote provenance, not every generated interpretation. Use non-sensitive documents and inspect the cited passages.
