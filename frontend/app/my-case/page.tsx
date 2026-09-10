"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { addMilestone, createCase, listCases, updateMilestone } from "../../lib/api";
import type { CaseRecord, CaseType } from "../../lib/types";

const anonymousKey = "microlawyer-anonymous-id";
const caseLabels: Record<CaseType, string> = { tenancy: "Tenancy", labor: "Workplace", consumer: "Consumer", criminal: "Criminal / FIR", other: "Other" };

export default function MyCasePage() {
  const [anonymousId, setAnonymousId] = useState("");
  const [cases, setCases] = useState<CaseRecord[]>([]);
  const [caseType, setCaseType] = useState<CaseType>("tenancy");
  const [caseDate, setCaseDate] = useState("");
  const [notes, setNotes] = useState("");
  const [newMilestones, setNewMilestones] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const existing = localStorage.getItem(anonymousKey) ?? crypto.randomUUID();
    localStorage.setItem(anonymousKey, existing); setAnonymousId(existing);
    listCases(existing).then(setCases).catch((requestError) => setError(requestError instanceof Error ? requestError.message : "Something went wrong."));
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault(); if (!anonymousId || !caseDate) return;
    setBusy(true); setError("");
    try { const created = await createCase({ anonymous_id: anonymousId, case_type: caseType, case_date: caseDate, notes }); setCases((current) => [created, ...current]); setCaseDate(""); setNotes(""); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Something went wrong."); }
    finally { setBusy(false); }
  }

  async function toggle(caseId: string, milestoneId: string, completed: boolean) {
    setError(""); try { await updateMilestone(caseId, milestoneId, completed); setCases((current) => current.map((item) => item.id === caseId ? { ...item, milestones: item.milestones.map((milestone) => milestone.id === milestoneId ? { ...milestone, completed } : milestone) } : item)); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Something went wrong."); }
  }

  async function add(caseId: string) {
    const title = newMilestones[caseId]?.trim(); if (!title) return;
    setError(""); try { await addMilestone(caseId, title); const refreshed = await listCases(anonymousId); setCases(refreshed); setNewMilestones((current) => ({ ...current, [caseId]: "" })); } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Something went wrong."); }
  }

  return (
    <main className="app-shell"><header className="topbar"><Link className="brand" href="/">MicroLawyer <span>AI</span></Link><nav className="topnav" aria-label="Main navigation"><Link href="/chat">Chat</Link><Link href="/learn">Learn</Link><Link href="/check">Quick check</Link><Link href="/documents">Documents</Link><Link href="/legal-aid">Legal aid</Link><Link className="active" href="/my-case">My Case</Link></nav></header>
      <section className="workspace case-workspace"><div className="page-intro"><p className="eyebrow">Your private browser tracker</p><h1>My Case.</h1><p className="lede">Keep a simple record of what happened and the next steps you want to track. No login is required.</p></div>
        <form className="chat-panel case-form" onSubmit={submit}><div className="field-grid"><label>Case type<select value={caseType} onChange={(event) => setCaseType(event.target.value as CaseType)}>{Object.entries(caseLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label><label>Date<input className="case-date-input" type="date" value={caseDate} onChange={(event) => setCaseDate(event.target.value)} required /></label></div><label className="document-field">Notes<textarea value={notes} onChange={(event) => setNotes(event.target.value)} placeholder="Add a short note about this dispute" rows={4} /></label><button className="primary-button generate-button" type="submit" disabled={busy || !caseDate}>{busy ? "Saving..." : "Add case"}</button>{error && <p className="error-message" role="alert">{error}</p>}</form>
        <div className="case-list">{cases.length === 0 && <div className="case-empty"><p className="eyebrow">Nothing tracked yet</p><p>Your cases will appear here after you add the first one.</p></div>}{cases.map((item) => <article className="case-card" key={item.id}><div className="case-card-heading"><div><span className="status-badge">{caseLabels[item.case_type]}</span><h2>{item.case_date}</h2></div><span className="case-progress">{item.milestones.filter((milestone) => milestone.completed).length}/{item.milestones.length} complete</span></div>{item.notes && <p className="case-notes">{item.notes}</p>}<div className="milestone-list">{item.milestones.map((milestone) => <label className={milestone.completed ? "milestone completed" : "milestone"} key={milestone.id}><input type="checkbox" checked={milestone.completed} onChange={(event) => void toggle(item.id, milestone.id, event.target.checked)} /><span>{milestone.title}</span></label>)}</div><div className="add-milestone"><input value={newMilestones[item.id] ?? ""} onChange={(event) => setNewMilestones((current) => ({ ...current, [item.id]: event.target.value }))} placeholder="Add a custom milestone" /><button className="secondary-button" type="button" onClick={() => void add(item.id)}>Add</button></div></article>)}</div>
        <p className="disclaimer">Your anonymous case ID is stored in this browser. Do not use this tracker for emergencies or store highly sensitive information.</p>
      </section></main>
  );
}