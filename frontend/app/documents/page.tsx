"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { draftDocument, generateDocument, getDocumentChecklist } from "../../lib/api";
import type { Jurisdiction } from "../../lib/types";

type DocumentType = "legal_notice" | "fir_draft" | "rental_dispute_letter";

const provinces: { value: Jurisdiction; label: string }[] = [
  { value: "punjab", label: "Punjab" }, { value: "sindh", label: "Sindh" },
  { value: "kp", label: "Khyber Pakhtunkhwa" }, { value: "balochistan", label: "Balochistan" },
  { value: "federal", label: "Islamabad / Federal" },
];

const documentFields: Record<DocumentType, { key: string; label: string; placeholder: string; multiline?: boolean }[]> = {
  legal_notice: [
    { key: "sender_name", label: "Your name", placeholder: "Your full name" },
    { key: "recipient_name", label: "Recipient name", placeholder: "Person or organization receiving the notice" },
    { key: "subject", label: "Subject", placeholder: "What is this notice about?" },
    { key: "facts", label: "What happened?", placeholder: "Explain the important facts and dates.", multiline: true },
    { key: "requested_action", label: "Requested action", placeholder: "What should the recipient do?", multiline: true },
  ],
  fir_draft: [
    { key: "sender_name", label: "Complainant name", placeholder: "Your full name" },
    { key: "recipient_name", label: "Police station or authority", placeholder: "Relevant police station" },
    { key: "subject", label: "Incident subject", placeholder: "Short description of the incident" },
    { key: "facts", label: "Incident details", placeholder: "Explain what happened, when, where, and who was involved.", multiline: true },
    { key: "requested_action", label: "Requested action", placeholder: "What action are you requesting?", multiline: true },
  ],
  rental_dispute_letter: [
    { key: "sender_name", label: "Tenant name", placeholder: "Your full name" },
    { key: "recipient_name", label: "Landlord name", placeholder: "Landlord or property manager" },
    { key: "subject", label: "Subject", placeholder: "Short description of the rental dispute" },
    { key: "facts", label: "What happened?", placeholder: "Explain the tenancy, dates, and dispute.", multiline: true },
    { key: "requested_action", label: "Requested action", placeholder: "What resolution are you asking for?", multiline: true },
  ],
};

export default function DocumentsPage() {
  const [documentType, setDocumentType] = useState<DocumentType>("legal_notice");
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction | "">("");
  const [language, setLanguage] = useState<"en" | "ur" | "roman-urdu">("en");
  const [facts, setFacts] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [draftProvider, setDraftProvider] = useState("");
  const [drafted, setDrafted] = useState(false);
  const [draftInput, setDraftInput] = useState<Record<string, string>>({});
  const [checklist, setChecklist] = useState<{ items: string[]; provider: string; sources: string[] } | null>(null);
  const [checklistBusy, setChecklistBusy] = useState(false);
  const [checklistError, setChecklistError] = useState("");

  async function loadChecklist(type: DocumentType, selectedJurisdiction: Jurisdiction | "") {
    if (!selectedJurisdiction) { setChecklist(null); return; }
    setChecklistBusy(true); setChecklistError("");
    try { setChecklist(await getDocumentChecklist({ document_type: type, jurisdiction: selectedJurisdiction })); }
    catch (requestError) { setChecklistError(requestError instanceof Error ? requestError.message : "The preparation checklist could not be loaded."); }
    finally { setChecklistBusy(false); }
  }

  function changeType(value: DocumentType) { setDocumentType(value); setFacts({}); setDrafted(false); setDraftProvider(""); setDraftInput({}); void loadChecklist(value, jurisdiction); }
  function updateFact(key: string, value: string) { setFacts((current) => ({ ...current, [key]: value })); }

  async function draft(event?: FormEvent) {
    event?.preventDefault();
    if (!jurisdiction) return;
    setBusy(true); setError("");
    try {
      const details = Object.keys(draftInput).length ? draftInput : facts;
      if (!Object.keys(draftInput).length) setDraftInput({ ...facts });
      const result = await draftDocument({ document_type: documentType, language, jurisdiction, details });
      setFacts((current) => ({ ...current, facts: result.facts, requested_action: result.requested_action }));
      setDraftProvider(result.provider); setDrafted(true);
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "The AI draft could not be created."); }
    finally { setBusy(false); }
  }

  async function generate(event: FormEvent) {
    event.preventDefault();
    if (!jurisdiction || !drafted) return;
    setBusy(true); setError("");
    try {
      const pdf = await generateDocument({ document_type: documentType, language, jurisdiction, facts });
      const url = URL.createObjectURL(pdf);
      const link = document.createElement("a");
      link.href = url; link.download = `${documentType}-draft.pdf`; link.click();
      URL.revokeObjectURL(url);
    } catch (requestError) { setError(requestError instanceof Error ? requestError.message : "The PDF could not be generated."); }
    finally { setBusy(false); }
  }

  const fields = documentFields[documentType].filter((field) => field.key !== "requested_action");
  return (
    <main className="app-shell">
      <header className="topbar"><Link className="brand" href="/">MicroLawyer <span>AI</span></Link><nav className="topnav" aria-label="Main navigation"><Link href="/chat">Chat</Link><Link href="/learn">Learn</Link><Link href="/check">Quick check</Link><Link className="active" href="/documents">Documents</Link><Link href="/legal-aid">Legal aid</Link><Link href="/my-case">My Case</Link></nav></header>
      <section className="workspace">
        <div className="page-intro"><p className="eyebrow">Draft generator</p><h1>Prepare a careful first draft.</h1><p className="lede">Add the facts you know. Review the PDF with a qualified lawyer or relevant authority before using it.</p></div>
        <form className="chat-panel document-form" onSubmit={draft}>
          <div className="field-grid">
            <label>Document type<select value={documentType} onChange={(event) => changeType(event.target.value as DocumentType)}><option value="legal_notice">Legal notice</option><option value="fir_draft">FIR draft</option><option value="rental_dispute_letter">Rental dispute letter</option></select></label>
                <label>Province or jurisdiction<select value={jurisdiction} onChange={(event) => { const value = event.target.value as Jurisdiction; setJurisdiction(value); setDrafted(false); setDraftInput({}); void loadChecklist(documentType, value); }} required><option value="">Select one</option>{provinces.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
          </div>
          <label className="language-field">Document language<select value={language} onChange={(event) => { setLanguage(event.target.value as "en" | "ur" | "roman-urdu"); setDrafted(false); }}><option value="en">English</option><option value="ur">Urdu script</option><option value="roman-urdu">Roman Urdu</option></select></label>
              <section className="checklist-panel" aria-live="polite"><div className="checklist-heading"><div><p className="eyebrow">Prepare first</p><h2>What to gather</h2></div>{checklist?.provider && <span>AI-assisted</span>}</div>{!jurisdiction && <p className="helper-text">Choose your province to see a practical checklist before filling the form.</p>}{checklistBusy && <p className="helper-text">Building your preparation checklist...</p>}{checklistError && <p className="error-message" role="alert">{checklistError}</p>}{checklist && !checklistBusy && <><ul className="checklist-items">{checklist.items.map((item) => <li key={item}><span aria-hidden="true">✓</span>{item}</li>)}</ul>{checklist.sources.length > 0 && <p className="checklist-sources">Grounded where possible in: {checklist.sources.join(", ")}</p>}</>}</section>
          {fields.map((field) => <label className="document-field" key={field.key}>{field.key === "facts" ? "Briefly describe what happened, in your own words" : field.label}{field.multiline ? <textarea value={facts[field.key] ?? ""} onChange={(event) => { updateFact(field.key, event.target.value); setDrafted(false); setDraftInput({}); }} placeholder={field.key === "facts" ? "Write casually in English, Urdu, or Roman Urdu. Include dates and important details you remember." : field.placeholder} rows={4} required /> : <input value={facts[field.key] ?? ""} onChange={(event) => { updateFact(field.key, event.target.value); setDrafted(false); setDraftInput({}); }} placeholder={field.placeholder} required />}</label>)}
          <button className="primary-button generate-button" type="submit" disabled={busy || !jurisdiction}>{busy ? "Drafting with AI..." : "Draft with AI"}</button>
          {error && <p className="error-message" role="alert">{error}</p>}
        </form>
        {drafted && <section className="chat-panel review-panel"><div className="answer-heading"><p className="eyebrow">Review and edit before generating</p><span>Drafted with {draftProvider}</span></div><label className="document-field">Professional facts paragraph<textarea value={facts.facts ?? ""} onChange={(event) => updateFact("facts", event.target.value)} rows={6} required /></label><label className="document-field">Requested action paragraph<textarea value={facts.requested_action ?? ""} onChange={(event) => updateFact("requested_action", event.target.value)} rows={5} required /></label><div className="review-actions"><button className="secondary-button" type="button" onClick={() => draft()} disabled={busy}>Regenerate</button><button className="primary-button" type="button" onClick={generate} disabled={busy}>{busy ? "Generating PDF..." : "Generate PDF"}</button></div></section>}
        <p className="disclaimer">Every PDF is an informational draft, not legal advice or a final legal filing.</p>
      </section>
    </main>
  );
}
