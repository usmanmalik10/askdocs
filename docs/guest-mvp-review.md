# Guest MVP engineering review

What this change does: AskDocs lets a visitor upload a document and ask questions without an account. A private Python service retrieves document passages, calls Gemini, and checks that returned citation quotes exist in those passages. The browser exposes sources, saved answers, deletion, and a temporary workspace.

The review assumed a small public free-tier demonstration: up to five retained documents per guest, 20 upload attempts and 100 question attempts across the site per UTC day. It traced the browser, public API boundary, private service, SQL, model requests, migrations, deployment files, and tests. This is a review of the guest release, not an audit certifying the earlier enterprise roadmap.

## Findings before corrections

### Must fix

1. **The Windows server cannot open an async PostgreSQL connection** — [runtime entry point](../apps/backend/runtime.py#L5).
   - **What this is:** Python’s default Windows event loop manages asynchronous work. The PostgreSQL driver needs a different socket-compatible loop.
   - **Problem:** A real Neon connection check failed with the driver’s explicit ProactorEventLoop error, even though Linux CI passed.
   - **Fix:** Use a Windows-compatible runner for the local server and migration command, and the current test-loop factory hook. A new runtime test checks the selected loop.
   - **If skipped:** Windows users see storage-unavailable errors despite valid credentials. **Resolution:** corrected; the real Neon connection and migration then succeeded.

2. **New anonymous workspaces have no creation budget** — [workspace opening](../apps/backend/routes.py#L26), [shared budgets](../apps/backend/quotas.py#L5).
   - **What this is:** Each new browser identity creates a guest record before any upload or question.
   - **Problem:** Repeated requests with fresh cookies can grow guest rows even when all AI budgets are exhausted.
   - **Fix:** Apply atomic guest, address, and site limits before creating a workspace. Existing guests continue working after the new-workspace limit is reached.
   - **If skipped:** The free database can be consumed by empty sessions. **Resolution:** corrected; a real-database test covers rejected creation and continued access for existing guests.

3. **A non-object model response escapes answer validation** — [model payload validation](../apps/backend/answering.py#L26).
   - **What this is:** The model must return a JSON object containing the answer and evidence.
   - **Problem:** A JSON null or array raises an unhandled error before citation validation rather than the intended controlled provider error.
   - **Fix:** Reject non-object payloads before reading fields. Add null and array cases to the validation test.
   - **If skipped:** A malformed upstream response becomes an internal error. **Resolution:** corrected; these responses now return a controlled failure and never an invented answer.

4. **Vercel chooses a pnpm version rejected by the project** — [package-manager pin](../package.json), [deployment operations](engineering-handbook.md#deployment-and-operations).
   - **What this is:** The repository requires pnpm 9.15.0 for installation.
   - **Problem:** The first real deployment used Vercel’s bundled 9.15.9 and failed the strict engine check before building either service.
   - **Fix:** Enable Vercel’s Corepack support so it uses the existing package-manager pin.
   - **If skipped:** Local checks stay green while deployment always fails. **Resolution:** corrected; the next build logged pnpm 9.15.0, built Next.js and Python 3.13, and reached Ready.

5. **Local deployment source includes discarded caches and Git settings** — [deployment exclusions](../.vercelignore).
   - **What this is:** CLI deployment selects files from the local working directory, including files outside Git’s tracked source.
   - **Problem:** Source inspection included old application cache directories and the local Git configuration. These are irrelevant to the guest service and should not be uploaded.
   - **Fix:** Explicitly exclude credentials, local Git configuration, discarded application directories, dependency caches, build artifacts, and test output.
   - **If skipped:** Deployments carry stale implementation metadata and unnecessary local configuration. **Resolution:** corrected; the rebuilt deployment used the reduced current-source selection.

6. **One temporary model failure ends a question immediately** — [provider requests](../apps/backend/provider.py), [request deadlines](../apps/backend/routes.py).
   - **What this is:** Embeddings and generation depend on an external AI service.
   - **Problem:** The first public acceptance run produced a cited answer, then a subsequent request returned a temporary provider failure without a retry.
   - **Fix:** Retry one transport or server failure, keep quota and credential failures immediate, and cancel the full AI operation after 65 seconds. Tests cover retry recovery, quota handling, cancellation, and an empty answer history after timeout.
   - **If skipped:** A brief provider interruption unnecessarily fails the user’s question. **Resolution:** corrected in the review commit; persistent provider failure still returns an honest error rather than an invented answer.

## Verification and practical limits

The initial CI baseline passed 39 Python/PostgreSQL tests, four guest-boundary unit tests, and six desktop/mobile browser scenarios. Review corrections expand the Python suite; the release record identifies the subsequent CI result. Automated upload and source-dialog accessibility scans passed for the checked WCAG rules.

A real protected preview subsequently passed browser upload, real model generation, citation inspection, history reload, irrelevant-question abstention, cross-guest read/question/delete denial, deletion, unauthorized cleanup rejection, and an authorized cleanup call. No confidential document or actual employer data was used.

Temporary upstream failures were observed in initial model and public production checks. The application now retries once within a total deadline, reports persistent failures, and retains the user’s input for retry. Free-tier availability and provider quotas remain external constraints.

Quote matching proves that a cited passage exists; it does not independently prove that every generated claim follows from it. Broad adversarial evaluation, OCR, large-file load testing, commercial guarantees, and enterprise features are outside this release.

Verdict: fix findings 1–6 before release. All six corrections are included in the review commit; the final release remains gated on its CI result and public production verification.

Not checked: production public access at the time of this review. The final result is recorded separately in [release verification](release-verification.md).
