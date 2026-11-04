import Link from "next/link";

export default function Privacy() {
  return <main id="main" className="privacy-page">
    <Link href="/">← Back to AskDocs</Link>
    <span className="eyebrow">BEFORE YOU UPLOAD</span>
    <h1>A temporary workspace.<br/>A clear view of your data.</h1>
    <p>AskDocs is an open-source document assistant that works without an account. Use public or non-sensitive material in this free demonstration.</p>
    <h2>What is stored</h2><p>We store your document name, extracted text passages, semantic representations of those passages, questions, answers, and source references. The original uploaded file is processed temporarily and is not retained.</p>
    <h2>Who processes your text</h2><p>Document text is sent to the configured embedding provider. Your question and relevant passages are sent to the configured answer provider. Provider details are shown beside the upload consent. If Gemini’s free tier is used, Google may use submitted content to improve its products. Do not upload personal, confidential, employer, or customer information.</p>
    <h2>How the guest workspace works</h2><p>An essential HttpOnly cookie associates this browser with a temporary workspace. No email address or account is collected. Your raw cookie is not stored in the database. Clearing cookies, changing browsers, or using private browsing can make your workspace inaccessible; there is no account recovery.</p>
    <h2>Retention and deletion</h2><p>Your workspace expires 24 hours after it is created. Access ends at expiry, and a daily cleanup removes expired records. You can delete a document or erase the whole workspace sooner. Deleting a document also removes its passages and saved answers. Infrastructure backups and AI-provider retention follow those providers’ policies; deletion here cannot retract a request already sent to a model.</p>
    <h2>Abuse limits and diagnostics</h2><p>We retain keyed hashes of network addresses and daily usage counters for rate limiting, then clear old counters during cleanup. Hosting and model providers may retain operational logs. AskDocs does not deliberately log document text, questions, cookies, or credentials.</p>
    <h2>Check every answer</h2><p>Generated answers can be incomplete or wrong. Citations show the actual extracted passage so you can verify an answer yourself. This release supports text-based PDFs, UTF-8 text, and Markdown; it does not perform OCR.</p>
    <p><a href="https://github.com/usmanmalik10/askdocs" target="_blank" rel="noreferrer">Review the source code and report an issue ↗</a></p>
  </main>;
}
