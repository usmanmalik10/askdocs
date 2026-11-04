"use client";

import { useEffect, useRef } from "react";
import type { Citation } from "@/lib/api";

export function SourceDialog({ source, onClose }: { source: Citation | null; onClose: () => void }) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const element = dialog.current;
    if (source && element && !element.open) element.showModal();
    if (!source && element?.open) element.close();
  }, [source]);
  return <dialog ref={dialog} className="source-dialog" aria-labelledby="source-title" onClose={onClose} onClick={event => { if (event.target === event.currentTarget) dialog.current?.close(); }}>
    {source ? <div className="source-inner"><header><div><span className="eyebrow">SOURCE [{source.id}] · PAGE {source.page}</span><h2 id="source-title">{source.name}</h2></div><button type="button" className="close-button" aria-label="Close source details" onClick={() => dialog.current?.close()}>×</button></header><p className="notice">The quote below was checked against this extracted passage.</p><blockquote>{source.quote}</blockquote><h3>Full passage</h3><p className="source-passage">{source.passage}</p><p className="notice">Original files are not retained. Page numbers refer to the uploaded PDF; text files use page 1.</p></div> : null}
  </dialog>;
}

export function AnswerText({ text, citations, onSource }: { text: string; citations: Citation[]; onSource: (source: Citation) => void }) {
  return <p className="answer-text">{text.split(/(\[\d+\])/g).map((part, index) => {
    const id = /^\[(\d+)\]$/.exec(part)?.[1];
    const source = id ? citations.find(item => item.id === Number(id)) : undefined;
    return source ? <button type="button" className="citation-inline" key={index} onClick={() => onSource(source)} aria-label={`Open source ${source.id}, ${source.name}, page ${source.page}`}>{part}</button> : part;
  })}</p>;
}
