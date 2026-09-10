import Link from "next/link";

type AidEntry = {
  name: string;
  phone: string;
  help: string;
  status: "placeholder" | "confirmed";
  note: string;
};

const regions: { name: string; note: string; entries: AidEntry[] }[] = [
  {
    name: "Punjab",
    note: "Lahore, Rawalpindi, Faisalabad, Multan, and other districts",
    entries: [
      { name: "Provincial legal aid referral service", phone: "To be added", help: "Free or low-cost advice, referrals, and help finding a qualified lawyer.", status: "placeholder", note: "Contact information pending verification" },
      { name: "District bar legal aid desk", phone: "To be added", help: "Initial guidance and referrals through the relevant district bar association.", status: "placeholder", note: "Confirm availability and hours with the local district bar" },
    ],
  },
  {
    name: "Sindh",
    note: "Karachi, Hyderabad, Sukkur, and other districts",
    entries: [
      { name: "Provincial legal aid referral service", phone: "To be added", help: "Free or low-cost advice, referrals, and help finding a qualified lawyer.", status: "placeholder", note: "Contact information pending verification" },
      { name: "District bar legal aid desk", phone: "To be added", help: "Initial guidance and referrals through the relevant district bar association.", status: "placeholder", note: "Confirm availability and hours with the local district bar" },
    ],
  },
  {
    name: "Khyber Pakhtunkhwa",
    note: "Peshawar, Abbottabad, Mardan, and other districts",
    entries: [
      { name: "Provincial legal aid referral service", phone: "To be added", help: "Free or low-cost advice, referrals, and help finding a qualified lawyer.", status: "placeholder", note: "Contact information pending verification" },
      { name: "District bar legal aid desk", phone: "To be added", help: "Initial guidance and referrals through the relevant district bar association.", status: "placeholder", note: "Confirm availability and hours with the local district bar" },
    ],
  },
  {
    name: "Balochistan",
    note: "Quetta and other districts",
    entries: [
      { name: "Provincial legal aid referral service", phone: "To be added", help: "Free or low-cost advice, referrals, and help finding a qualified lawyer.", status: "placeholder", note: "Contact information pending verification" },
      { name: "District bar legal aid desk", phone: "To be added", help: "Initial guidance and referrals through the relevant district bar association.", status: "placeholder", note: "Confirm availability and hours with the local district bar" },
    ],
  },
  {
    name: "Islamabad / Federal",
    note: "Islamabad Capital Territory and federal matters",
    entries: [
      { name: "Police emergency helpline", phone: "15", help: "Immediate police assistance in an emergency. This is not a legal-aid or lawyer referral service.", status: "confirmed", note: "Generally recognized emergency police number in Pakistan; verify locally if safe to do so" },
      { name: "Federal legal aid referral service", phone: "To be added", help: "Free or low-cost advice, referrals, and help finding a qualified lawyer.", status: "placeholder", note: "Contact information pending verification" },
      { name: "Islamabad district bar legal aid desk", phone: "To be added", help: "Initial guidance and referrals through the relevant bar association.", status: "placeholder", note: "Confirm availability and hours before visiting" },
    ],
  },
];

export default function LegalAidPage() {
  return (
    <main className="app-shell">
      <header className="topbar"><Link className="brand" href="/">MicroLawyer <span>AI</span></Link><nav className="topnav" aria-label="Main navigation"><Link href="/chat">Chat</Link><Link href="/learn">Learn</Link><Link href="/check">Quick check</Link><Link href="/documents">Documents</Link><Link className="active" href="/legal-aid">Legal aid</Link><Link href="/my-case">My Case</Link></nav></header>
      <section className="workspace aid-workspace">
        <div className="page-intro"><p className="eyebrow">Finding support</p><h1>Legal aid directory.</h1><p className="lede">A starting point for finding help by province. We are building this list carefully, so every placeholder below is clearly marked for verification.</p></div>
        <div className="aid-notice"><span className="trust-icon">i</span><p><strong>Please verify before relying.</strong> Many entries are placeholders until an organization, phone number, eligibility rules, and opening hours can be checked from an official source.</p></div>
        <div className="aid-regions">{regions.map((region, regionIndex) => <section className="aid-region" key={region.name}><div className="aid-region-heading"><span className="category-mark">0{regionIndex + 1}</span><div><h2>{region.name}</h2><p>{region.note}</p></div></div><div className="aid-entry-grid">{region.entries.map((entry) => <article className="aid-entry" key={entry.name}><div className="aid-entry-top"><span className={entry.status === "confirmed" ? "status-badge confirmed" : "status-badge"}>{entry.status === "confirmed" ? "Generally recognized" : "Placeholder"}</span><span className="aid-phone">{entry.phone}</span></div><h3>{entry.name}</h3><p>{entry.help}</p><small>{entry.note}</small></article>)}</div></section>)}</div>
        <p className="disclaimer">MicroLawyer AI is not a legal-aid provider. This directory is informational, and contact details should be verified before sharing personal information or travelling.</p>
      </section>
    </main>
  );
}
