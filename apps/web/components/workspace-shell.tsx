import Link from "next/link";

export function WorkspaceShell({ children, library }: { children: React.ReactNode; library: React.ReactNode }) {
  return <div className="app-shell">
    <aside className="sidebar" aria-label="Document workspace">
      <Link className="brand" href="/" aria-label="AskDocs home"><span className="brand-mark" aria-hidden="true">A<span>↗</span></span>AskDocs</Link>
      <p className="brand-caption">Your documents. Clear answers.</p>
      <div className="workspace-label"><span className="status-dot" /> Guest workspace <span className="small-tag">24h</span></div>
      <div className="library-heading"><h2>Your documents</h2><span className="eyebrow">LIBRARY</span></div>
      {library}
      <div className="sidebar-note"><strong>A little more clarity.</strong><p>Find the answer, then check the passage it came from.</p><Link href="/privacy">How your data is handled ↗</Link></div>
      <a className="repository-link" href="https://github.com/usmanmalik10/askdocs" target="_blank" rel="noreferrer">Open source on GitHub ↗</a>
    </aside>
    <div className="workspace-body">
      <header className="topbar"><span>Workspace <span aria-hidden="true">/</span> <strong>Ask your docs</strong></span><span className="guest-badge"><span className="status-dot" /> No account needed</span></header>
      <main id="main" className="main-content">{children}</main>
    </div>
  </div>;
}

export function Welcome() {
  return <div className="welcome">
    <div className="welcome-symbol" aria-hidden="true"><svg viewBox="0 0 48 48" fill="none"><path d="M13 7h15l8 8v26H13V7Z" stroke="currentColor" strokeWidth="2.5" strokeLinejoin="round"/><path d="M27 7v10h9M19 25h11M19 31h8" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round"/></svg></div>
    <span className="eyebrow">LESS SEARCHING. MORE UNDERSTANDING.</span>
    <h1>Your next answer<br/>is in your documents.</h1>
    <p className="welcome-description">Turn the pages you have into the answers you need.<br className="desktop-break"/> Ask a question and follow every answer back to its source.</p>
    <ol className="steps"><li><span>01</span><strong>Bring a document</strong><p>A PDF, text file, or Markdown note.</p></li><li><span>02</span><strong>Ask in your own words</strong><p>Get help understanding what it says.</p></li><li><span>03</span><strong>Check the source</strong><p>Read the passages behind the answer.</p></li></ol>
  </div>;
}
