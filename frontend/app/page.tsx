import Link from "next/link";

const categories = [
  { title: "Tenancy Issue", text: "Rent, eviction, deposits, and landlord disputes.", domain: "tenancy", mark: "01" },
  { title: "Workplace Problem", text: "Understand workplace rights and next steps.", domain: "labor", mark: "02" },
  { title: "File an FIR", text: "Prepare clear information for a criminal complaint.", domain: "criminal", mark: "03" },
  { title: "Consumer Rights", text: "Get help with faulty goods, services, and unfair treatment.", domain: "consumer", mark: "04" },
];

export default function HomePage() {
  return (
    <main className="landing-shell">
      <header className="landing-nav">
        <Link className="brand" href="/">MicroLawyer <span>AI</span></Link>
        <nav aria-label="Main navigation"><Link href="/chat">Chat</Link><Link href="/learn">Learn</Link><Link href="/check">Quick check</Link><Link href="/documents">Documents</Link><Link href="/legal-aid">Legal aid</Link><Link href="/my-case">My Case</Link></nav>
      </header>

      <section className="landing-hero">
        <div className="hero-seal" aria-label="Informational legal assistant for Pakistan"><span>پاکستان</span><strong>ML</strong><small>INFORMATIONAL<br />LEGAL ASSISTANT</small></div>
        <div className="hero-copy">
          <p className="eyebrow">Legal clarity, within reach</p>
          <h1>Know your rights.<br /><em>Take your next step.</em></h1>
          <p className="landing-lede">MicroLawyer AI explains Pakistani law in plain language, helps you understand your options, and prepares careful first drafts for review.</p>
          <div className="landing-actions"><Link className="primary-button" href="/chat">Start a conversation <span aria-hidden="true">→</span></Link><Link className="text-link" href="/documents">Prepare a document <span aria-hidden="true">↗</span></Link></div>
        </div>
      </section>

      <section className="trust-banner"><span className="trust-icon">!</span><p><strong>Important:</strong> MicroLawyer AI is an informational assistant, not a licensed lawyer. Always verify guidance with a qualified lawyer or the relevant authority.</p></section>

      <section className="category-section" aria-labelledby="category-heading">
        <div className="section-heading"><div><p className="eyebrow">Start somewhere familiar</p><h2 id="category-heading">What brings you here?</h2></div><span className="section-note">Choose a topic to begin</span></div>
        <div className="category-grid">{categories.map((category) => <Link className="category-card" href={`/chat?domain=${category.domain}`} key={category.domain}><span className="category-mark">{category.mark}</span><span><h3>{category.title}</h3><p>{category.text}</p></span><span className="card-arrow" aria-hidden="true">↗</span></Link>)}</div>
      </section>

      <footer className="landing-footer"><span>Built for everyday Pakistan</span><span>Free to use · Review before relying</span></footer>
    </main>
  );
}
