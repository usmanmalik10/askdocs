import { Welcome, WorkspaceShell } from "@/components/workspace-shell";

export default function Home() {
  return <WorkspaceShell library={<p className="empty-library">Your uploaded documents will appear here.</p>}><Welcome/><section className="upload-card" aria-label="Document upload"><h2>Start with a document</h2><p>PDF, TXT, or Markdown · up to 3 MB · text-based files</p><p className="muted">Upload is being connected to the document service.</p></section></WorkspaceShell>;
}
