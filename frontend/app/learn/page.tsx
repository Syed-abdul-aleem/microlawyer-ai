"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { getLearningCards } from "../../lib/api";
import type { Jurisdiction, LearnResponse } from "../../lib/types";

const topics = [
  { value: "tenancy", label: "Tenancy", note: "Renting a home" },
  { value: "labor", label: "Workplace", note: "Work and wages" },
  { value: "consumer", label: "Consumer", note: "Buying and services" },
  { value: "criminal", label: "Criminal / FIR", note: "Safety and complaints" },
] as const;
const provinces: { value: Jurisdiction; label: string }[] = [
  { value: "punjab", label: "Punjab" }, { value: "sindh", label: "Sindh" },
  { value: "kp", label: "Khyber Pakhtunkhwa" }, { value: "balochistan", label: "Balochistan" },
];
type LearnDomain = (typeof topics)[number]["value"];

export default function LearnPage() {
  const [domain, setDomain] = useState<LearnDomain>("tenancy");
  const [jurisdiction, setJurisdiction] = useState<Jurisdiction>("punjab");
  const [result, setResult] = useState<LearnResponse | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let active = true;
    setBusy(true); setError("");
    getLearningCards(domain, domain === "criminal" ? "federal" : jurisdiction)
      .then((response) => { if (active) setResult(response); })
      .catch((requestError) => { if (active) setError(requestError instanceof Error ? requestError.message : "Learning cards could not be loaded."); })
      .finally(() => { if (active) setBusy(false); });
    return () => { active = false; };
  }, [domain, jurisdiction]);

  return (
    <main className="app-shell">
      <header className="topbar"><Link className="brand" href="/">MicroLawyer <span>AI</span></Link><nav className="topnav" aria-label="Main navigation"><Link href="/chat">Chat</Link><Link className="active" href="/learn">Learn</Link><Link href="/check">Quick check</Link><Link href="/documents">Documents</Link><Link href="/legal-aid">Legal aid</Link><Link href="/my-case">My Case</Link></nav></header>
      <section className="workspace learn-workspace">
        <div className="page-intro"><p className="eyebrow">Rights, in plain language</p><h1>Learn before you act.</h1><p className="lede">A few grounded facts can make the next step feel clearer. Swipe through the topic that matters to you.</p></div>
        <div className="learn-topics" role="tablist" aria-label="Learning topics">{topics.map((topic) => <button className={domain === topic.value ? "topic-tab active" : "topic-tab"} key={topic.value} type="button" onClick={() => setDomain(topic.value)} role="tab" aria-selected={domain === topic.value}><strong>{topic.label}</strong><span>{topic.note}</span></button>)}</div>
        {domain !== "criminal" && <label className="learn-province">Your province<select value={jurisdiction} onChange={(event) => setJurisdiction(event.target.value as Jurisdiction)}>{provinces.map((province) => <option key={province.value} value={province.value}>{province.label}</option>)}</select></label>}
        {busy && <div className="learn-status"><span className="thinking-dots" aria-label="Loading learning cards"><i /><i /><i /></span><p>Finding verified facts...</p></div>}
        {error && <p className="error-message" role="alert">{error}</p>}
        {!busy && result && <><div className="learn-meta"><span>{result.jurisdiction === "federal" ? "Federal sources" : `${result.jurisdiction} sources`}</span><span>Generated from verified legal documents</span></div><div className="learn-cards">{result.cards.map((card, index) => <article className="learn-card" key={`${card.source_act}-${index}`}><span className="card-number">0{index + 1}</span><h2>{card.title}</h2><p>{card.body}</p><span className="learn-source">Source: {card.source_act}</span></article>)}</div></>}
        <p className="disclaimer">These are educational summaries, not legal advice. Laws can change; verify important decisions with a qualified lawyer or relevant authority.</p>
      </section>
    </main>
  );
}