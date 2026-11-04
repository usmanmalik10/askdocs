"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import Link from "next/link";
import { api, ApiError } from "@/lib/api";
import type { Answer, Citation, DocumentRecord, Workspace as WorkspaceData } from "@/lib/api";
import { AnswerText, SourceDialog } from "./source-dialog";
import { Welcome, WorkspaceShell } from "./workspace-shell";

function errorMessage(error: unknown) { return error instanceof Error ? error.message : "Something went wrong. Please retry."; }

export function Workspace() {
  const [workspace, setWorkspace] = useState<WorkspaceData | null>(null);
  const [selected, setSelected] = useState<DocumentRecord | null>(null);
  const [answers, setAnswers] = useState<Answer[]>([]);
  const [loading, setLoading] = useState(true);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState("");
  const [expired, setExpired] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [question, setQuestion] = useState("");
  const [source, setSource] = useState<Citation | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const activeOperation = useRef(false);
  const historyRequest = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  function report(error: unknown) {
    setError(errorMessage(error));
    if (error instanceof ApiError && error.status === 410) setExpired(true);
  }

  useEffect(() => {
    const controller = new AbortController();
    async function load() {
      try {
        const data = await api<WorkspaceData>("workspace", { signal: controller.signal });
        if (controller.signal.aborted) return;
        setWorkspace(data);
        const requested = new URLSearchParams(window.location.search).get("document");
        const doc = data.documents.find(d => d.id === requested) || data.documents[0];
        if (doc) {
          const history = await api<{ answers: Answer[] }>(`documents/${doc.id}/answers`, { signal: controller.signal });
          if (!controller.signal.aborted) { setSelected(doc); setAnswers(history.answers); }
        }
      } catch (error) {
        if (!controller.signal.aborted) {
          setError(errorMessage(error));
          if (error instanceof ApiError && error.status === 410) setExpired(true);
        }
      } finally { if (!controller.signal.aborted) setLoading(false); }
    }
    void load();
    return () => { controller.abort(); historyRequest.current?.abort(); };
  }, []);

  async function openDocument(doc: DocumentRecord) {
    if (activeOperation.current) return;
    historyRequest.current?.abort();
    const controller = new AbortController();
    historyRequest.current = controller;
    setSelected(doc); setAnswers([]); setError(""); setQuestion(""); setHistoryLoading(true);
    window.history.replaceState(null, "", `?document=${doc.id}`);
    try {
      const data = await api<{ answers: Answer[] }>(`documents/${doc.id}/answers`, { signal: controller.signal });
      if (!controller.signal.aborted) setAnswers(data.answers);
    } catch (error) { if (!controller.signal.aborted) report(error); }
    finally { if (!controller.signal.aborted) setHistoryLoading(false); }
  }

  function chooseFile(candidate?: File) {
    if (!candidate) return;
    setError("");
    if (!/\.(pdf|txt|md)$/i.test(candidate.name)) { setError("Choose a PDF, TXT, or Markdown (.md) document."); return; }
    if (!candidate.size || candidate.size > 3 * 1024 * 1024) { setError("Choose a non-empty file no larger than 3 MB."); return; }
    setFile(candidate);
  }

  async function upload(event: FormEvent) {
    event.preventDefault();
    if (!file || !consent || activeOperation.current) return;
    activeOperation.current = true; setBusy("upload"); setError("");
    try {
      const body = new FormData(); body.set("file", file); body.set("consent", "true");
      const doc = await api<DocumentRecord>("documents", { method: "POST", body });
      setWorkspace(current => current ? { ...current, documents: [...current.documents, doc] } : current);
      setSelected(doc); setAnswers([]); setFile(null); setQuestion("");
      window.history.replaceState(null, "", `?document=${doc.id}`);
    } catch (error) { report(error); }
    finally { activeOperation.current = false; setBusy(null); }
  }

  async function ask(event: FormEvent) {
    event.preventDefault();
    if (!selected || question.trim().length < 3 || activeOperation.current) return;
    activeOperation.current = true; setBusy("ask"); setError("");
    try {
      const answer = await api<Answer>(`documents/${selected.id}/ask`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: question.trim() }) });
      setAnswers(current => [...current, answer]); setQuestion("");
      requestAnimationFrame(() => bottom.current?.scrollIntoView({ behavior: "instant", block: "nearest" }));
    } catch (error) { report(error); }
    finally { activeOperation.current = false; setBusy(null); }
  }

  async function removeDocument() {
    if (!selected || activeOperation.current || !window.confirm(`Delete “${selected.name}” and all its saved answers? This cannot be undone.`)) return;
    activeOperation.current = true; setBusy("delete"); setError("");
    try {
      await api(`documents/${selected.id}`, { method: "DELETE" });
      setWorkspace(current => current ? { ...current, documents: current.documents.filter(doc => doc.id !== selected.id) } : current);
      historyRequest.current?.abort(); setSelected(null); setAnswers([]); setSource(null); setHistoryLoading(false);
      window.history.replaceState(null, "", "/");
    } catch (error) { report(error); }
    finally { activeOperation.current = false; setBusy(null); }
  }

  async function eraseWorkspace() {
    if (activeOperation.current || !window.confirm("Erase every document and answer in this guest workspace? This cannot be undone.")) return;
    activeOperation.current = true; setBusy("erase"); setError("");
    try { await api("workspace", { method: "DELETE" }); window.location.assign("/"); }
    catch (error) { report(error); activeOperation.current = false; setBusy(null); }
  }

  const library = <>
    {loading ? <p className="empty-library" role="status">Opening your workspace…</p> : workspace?.documents.length ? <ul className="document-list">{workspace.documents.map(doc => <li key={doc.id}><button type="button" aria-current={selected?.id === doc.id ? "true" : undefined} disabled={Boolean(busy)} onClick={() => void openDocument(doc)}><span className="document-icon" aria-hidden="true">▤</span><span><strong>{doc.name}</strong><small>{doc.chunk_count} passages · {Math.max(1, Math.round(doc.byte_size / 1024))} KB</small></span></button></li>)}</ul> : <p className="empty-library">No documents yet.<br/>Your first answer starts with a file.</p>}
    {selected ? <button className="button secondary new-upload" type="button" disabled={Boolean(busy)} onClick={() => { historyRequest.current?.abort(); setSelected(null); setAnswers([]); setError(""); setHistoryLoading(false); window.history.replaceState(null, "", "/"); }}>+ Upload another</button> : null}
    {workspace ? <button className="erase-workspace" type="button" disabled={Boolean(busy)} onClick={() => void eraseWorkspace()}>{busy === "erase" ? "Erasing…" : "Erase this workspace"}</button> : null}
  </>;

  return <WorkspaceShell library={library}>
    {error ? <div className="error" role="alert"><strong>We couldn’t complete that step.</strong><br/>{error}{!workspace && !expired ? <p><button className="button secondary" onClick={() => window.location.reload()}>Retry connection</button></p> : null}</div> : null}
    {selected ? <>
      <div className="document-title"><div><span className="eyebrow">ASK YOUR DOCUMENT</span><h1>{selected.name}</h1><p className="notice">{selected.chunk_count} searchable passages · answers stay with this document</p></div><button className="button danger" type="button" disabled={Boolean(busy)} onClick={() => void removeDocument()}>{busy === "delete" ? "Deleting…" : "Delete document"}</button></div>
      <div className="conversation" aria-label="Document conversation" aria-busy={busy === "ask" || historyLoading}>
        {historyLoading ? <p role="status" className="notice">Loading saved answers…</p> : null}
        {!answers.length && !historyLoading ? <section className="chat-welcome"><span className="eyebrow">READY WHEN YOU ARE</span><h2>What would you like to understand?</h2><p>Ask a specific question about <strong>{selected.name}</strong>. Each answer includes the passages it used.</p><div className="suggestions">{["What are the main points in this document?", "What important dates or deadlines are mentioned?", "What actions does this document recommend?"].map(prompt => <button type="button" key={prompt} onClick={() => setQuestion(prompt)}>{prompt} <span aria-hidden="true">↗</span></button>)}</div></section> : null}
        {answers.map(answer => <article className="answer-pair" key={answer.id}><div className="question-bubble"><span className="eyebrow">YOU ASKED</span><p>{answer.question}</p></div><div className="answer-content"><div className="answer-label"><span className="mini-brand" aria-hidden="true">A</span><strong>AskDocs</strong><span>{answer.grounded ? "Sources checked" : "Not enough evidence"}</span></div><AnswerText text={answer.answer} citations={answer.citations} onSource={setSource}/>{answer.citations.length ? <div className="inline-sources">{answer.citations.map(citation => <button className="source-chip" key={citation.id} type="button" onClick={() => setSource(citation)}>[{citation.id}] {citation.name} <span>Page {citation.page} ↗</span></button>)}</div> : null}</div></article>)}
        {busy === "ask" ? <div className="working" role="status"><span className="pulse"/>Finding passages and checking an answer…</div> : null}
        <div ref={bottom}/>
      </div>
      <form className="question-form" onSubmit={event => void ask(event)}><label htmlFor="question">Ask a question</label><div className="composer"><textarea id="question" value={question} onChange={event => setQuestion(event.target.value)} maxLength={1200} minLength={3} rows={2} required disabled={Boolean(busy) || expired || historyLoading} placeholder="What would you like to know about this document?"/><button className="button" type="submit" disabled={Boolean(busy) || expired || historyLoading || question.trim().length < 3}>{busy === "ask" ? "Checking…" : "Ask your docs ↗"}</button></div><p className="notice">Answers can be wrong. Check the cited passages. Ask complete questions; each question is retrieved independently.</p></form>
    </> : <>
      <Welcome/>
      <form className="upload-card" onSubmit={event => void upload(event)} onDragOver={event => event.preventDefault()} onDrop={event => { event.preventDefault(); if (!busy) chooseFile(event.dataTransfer.files[0]); }}>
        <div className="upload-icon" aria-hidden="true">↑</div><h2>{file ? file.name : "Drop a document here"}</h2><p>{file ? `${Math.max(1, Math.round(file.size / 1024))} KB · ready to upload` : "PDF, TXT, or Markdown · up to 3 MB · 50 PDF pages"}</p>
        <input ref={fileInput} className="sr-only" tabIndex={-1} type="file" accept=".pdf,.txt,.md" aria-label="Choose a document" onChange={event => { chooseFile(event.target.files?.[0]); event.target.value = ""; }}/>
        <div className="upload-actions"><button type="button" className={file ? "button secondary" : "button"} disabled={Boolean(busy) || loading || expired} onClick={() => fileInput.current?.click()}>{file ? "Choose a different file" : "Choose a document"}</button>{file ? <button className="button" type="submit" disabled={!consent || Boolean(busy) || !workspace?.ai_ready || expired}>{busy === "upload" ? "Reading your document…" : "Upload and start ↗"}</button> : null}</div>
        <label className="consent"><input type="checkbox" checked={consent} onChange={event => setConsent(event.target.checked)} disabled={Boolean(busy)}/><span>I understand Google Gemini processes my text and questions. Free-tier content may be used to improve Google products. I’m using non-sensitive material. <Link href="/privacy">Data details</Link></span></label>
        {!loading && workspace && !workspace.ai_ready ? <p className="error" role="status">The site operator still needs to connect the AI provider. Uploads will be available after that connection.</p> : null}
        {busy === "upload" ? <p role="status" className="notice">Extracting text and building searchable passages. This can take up to a minute.</p> : null}
      </form>
      <p className="workspace-footnote">No account. No retained original file. A temporary workspace that expires in 24 hours.</p>
    </>}
    <SourceDialog source={source} onClose={() => setSource(null)}/>
  </WorkspaceShell>;
}
