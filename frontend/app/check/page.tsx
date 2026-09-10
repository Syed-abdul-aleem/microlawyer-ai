"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { askChat, quickCheck } from "../../lib/api";
import type { ChatLanguage, ChatResponse, Jurisdiction, QuickCheckResponse } from "../../lib/types";

const domains = [
  { value: "tenancy", label: "Tenancy" }, { value: "labor", label: "Workplace" },
  { value: "consumer", label: "Consumer rights" }, { value: "criminal", label: "FIR / Criminal" },
] as const;
const provinces: { value: Jurisdiction; label: string }[] = [
  { value: "punjab", label: "Punjab" }, { value: "sindh", label: "Sindh" },
  { value: "kp", label: "Khyber Pakhtunkhwa" }, { value: "balochistan", label: "Balochistan" },
  { value: "federal", label: "Islamabad / Federal" },
];
type CheckDomain = (typeof domains)[number]["value"];

export default function CheckPage() {
  const [scenario, setScenario] = useState("");
  const [domain, setDomain] = useState<CheckDomain>("tenancy");
  const [province, setProvince] = useState<Jurisdiction>("punjab");
  const [language, setLanguage] = useState<ChatLanguage>("en");
  const [result, setResult] = useState<QuickCheckResponse | null>(null);
  const [explanation, setExplanation] = useState<ChatResponse | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!scenario.trim()) return;
    setBusy(true); setError(""); setExplanation(null);
    try { setResult(await quickCheck({ scenario: scenario.trim(), domain, province, language })); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Something went wrong."); }
    finally { setBusy(false); }
  }

  async function explainMore() {
    if (!result || !scenario.trim()) return;
    setBusy(true); setError("");
    try { setExplanation(await askChat({ message: scenario.trim(), province, language, domain })); }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Something went wrong."); }
    finally { setBusy(false); }
  }

  return (
    <main className="app-shell">
      <header className="topbar"><Link className="brand" href="/">MicroLawyer <span>AI</span></Link><nav className="topnav" aria-label="Main navigation"><Link href="/chat">Chat</Link><Link href="/learn">Learn</Link><Link className="active" href="/check">Quick check</Link><Link href="/documents">Documents</Link><Link href="/legal-aid">Legal aid</Link><Link href="/my-case">My Case</Link></nav></header>
      <section className="workspace check-workspace">
        <div className="page-intro"><p className="eyebrow">A quick first read</p><h1>Is this legal?</h1><p className="lede">Describe one short situation. We will give a source-grounded starting point, not a final legal verdict.</p></div>
        <form className="chat-panel check-form" onSubmit={submit}>
          <label>What happened?<textarea value={scenario} onChange={(event) => setScenario(event.target.value)} placeholder="Can my landlord keep my security deposit?" rows={4} required /></label>
          <div className="field-grid"><label>Topic<select value={domain} onChange={(event) => setDomain(event.target.value as CheckDomain)}>{domains.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label><label>Province or jurisdiction<select value={province} onChange={(event) => setProvince(event.target.value as Jurisdiction)}>{provinces.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label><label>Answer language<select value={language} onChange={(event) => setLanguage(event.target.value as ChatLanguage)}><option value="en">English</option><option value="roman-urdu">Roman Urdu</option><option value="urdu">Urdu script</option></select></label></div>
          <button className="primary-button generate-button" type="submit" disabled={busy || !scenario.trim()}>{busy ? "Checking..." : "Check this scenario"}</button>
          {error && <p className="error-message" role="alert">{error}</p>}
        </form>
        {result && <section className="check-result" aria-live="polite"><span className={`verdict verdict-${result.verdict.toLowerCase().replace(" ", "-")}`}>{result.verdict}</span><p>{result.reason}</p><div className="source-badges">{result.sources.map((source) => <span className="source-badge" key={`${source.source_act}-${source.section_ref}`}>✓ Verified from {source.source_act}</span>)}</div><button className="secondary-button explain-button" type="button" onClick={() => void explainMore()} disabled={busy}>{busy ? "Explaining..." : "Explain more"}</button></section>}
        {explanation && <section className="answer-panel check-explanation"><div className="answer-heading"><p className="eyebrow">Full explanation</p><span>{explanation.jurisdiction} · {explanation.provider}</span></div><p className="answer-text">{explanation.answer}</p></section>}
        <p className="disclaimer">This quick check is informational only. Important decisions should be reviewed with a qualified lawyer or relevant authority.</p>
      </section>
    </main>
  );
}