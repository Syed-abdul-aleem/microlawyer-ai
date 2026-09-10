"use client";

import Link from "next/link";
import { FormEvent, useEffect, useRef, useState } from "react";
import { askChat, transcribeVoice } from "../../lib/api";
import type { ChatLanguage, ChatResponse, Jurisdiction } from "../../lib/types";

const provinces: { value: Jurisdiction; label: string }[] = [
  { value: "punjab", label: "Punjab" }, { value: "sindh", label: "Sindh" },
  { value: "kp", label: "Khyber Pakhtunkhwa" }, { value: "balochistan", label: "Balochistan" },
  { value: "federal", label: "Islamabad / Federal" },
];
const domains = [
  { value: "tenancy", label: "Tenancy" },
  { value: "labor", label: "Workplace" },
  { value: "criminal", label: "FIR / Criminal" },
  { value: "consumer", label: "Consumer rights" },
] as const;
type ChatDomain = (typeof domains)[number]["value"];
type ChatMessage = { role: "user" | "assistant"; content: string; response?: ChatResponse };
const suggestions = ["What documents do I need?", "Draft a notice for this", "Explain in simpler terms"];

export default function ChatPage() {
  const [province, setProvince] = useState<Jurisdiction | "">("");
  const [language, setLanguage] = useState<ChatLanguage>("roman-urdu");
  const [domain, setDomain] = useState<ChatDomain>("tenancy");
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [recording, setRecording] = useState(false);
  const mediaRecorder = useRef<MediaRecorder | null>(null);
  const audioChunks = useRef<Blob[]>([]);

  useEffect(() => {
    const requestedDomain = new URLSearchParams(window.location.search).get("domain") as ChatDomain | null;
    if (requestedDomain && domains.some((item) => item.value === requestedDomain)) setDomain(requestedDomain);
  }, []);

  async function sendMessage(text: string) {
    if (!province || !text.trim() || busy) return;
    const question = text.trim();
    setMessages((current) => [...current, { role: "user", content: question }]);
    setMessage(""); setBusy(true); setError("");
    try {
      const response = await askChat({ message: question, province, language, domain });
      setMessages((current) => [...current, { role: "assistant", content: response.answer, response }]);
    }
    catch (requestError) { setError(requestError instanceof Error ? requestError.message : "Something went wrong."); }
    finally { setBusy(false); }
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    void sendMessage(message);
  }

  async function startRecording() {
    setError("");
    if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
      setError("Voice recording is not supported in this browser. Please type your question instead.");
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      audioChunks.current = [];
      recorder.ondataavailable = (event) => { if (event.data.size > 0) audioChunks.current.push(event.data); };
      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audio = new File([new Blob(audioChunks.current, { type: recorder.mimeType || "audio/webm" })], "recording.webm", { type: recorder.mimeType || "audio/webm" });
        setBusy(true);
        try {
          const transcription = await transcribeVoice(audio);
          setMessage((current) => current ? `${current} ${transcription.text}` : transcription.text);
        } catch (requestError) {
          setError(requestError instanceof Error ? requestError.message : "Voice transcription failed.");
        } finally { setBusy(false); }
      };
      mediaRecorder.current = recorder;
      recorder.start();
      setRecording(true);
    } catch (requestError) {
      setError(requestError instanceof DOMException && requestError.name === "NotAllowedError" ? "Microphone permission was denied. Please allow microphone access or type your question instead." : "Could not start the microphone. Please check your browser permissions.");
    }
  }

  function stopRecording() {
    if (mediaRecorder.current?.state === "recording") {
      mediaRecorder.current.stop();
      setRecording(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar"><Link className="brand" href="/">MicroLawyer <span>AI</span></Link><nav className="topnav" aria-label="Main navigation"><Link className="active" href="/chat">Chat</Link><Link href="/learn">Learn</Link><Link href="/check">Quick check</Link><Link href="/documents">Documents</Link><Link href="/legal-aid">Legal aid</Link><Link href="/my-case">My Case</Link></nav></header>
      <section className="workspace">
        <div className="page-intro"><p className="eyebrow">Informational legal assistant</p><h1>Ask with context.</h1><p className="lede">Choose your jurisdiction first so answers use the law that applies to you.</p></div>
        <form className="chat-panel" onSubmit={submit}>
          <div className="field-grid">
            <label>Topic<select value={domain} onChange={(event) => setDomain(event.target.value as ChatDomain)}>{domains.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
            <label>Province or jurisdiction<select value={province} onChange={(event) => setProvince(event.target.value as Jurisdiction)} required><option value="">Select before asking</option>{provinces.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
            <label>Answer language<select value={language} onChange={(event) => setLanguage(event.target.value as ChatLanguage)}><option value="roman-urdu">Roman Urdu</option><option value="urdu">Urdu script</option><option value="en">English</option></select></label>
          </div>
          <label className="message-label">Your question<textarea value={message} onChange={(event) => setMessage(event.target.value)} placeholder="Mera landlord notice ke baghair nikalna chahta hai..." rows={5} required /></label>
          <div className="composer-actions"><button className={recording ? "recording-button" : "mic-button"} type="button" onClick={recording ? stopRecording : startRecording} disabled={busy}>{recording ? <><span className="recording-dot" /><span className="waveform"><i /><i /><i /><i /><i /></span> Stop</> : <><span className="mic-glyph" aria-hidden="true">●</span> Use microphone</>}</button><button className="primary-button" type="submit" disabled={busy || recording || !province || !message.trim()}>{busy ? "Thinking..." : "Ask assistant"}</button></div>
          <p className="helper-text">{recording ? "Recording... tap Stop recording when you are finished." : "Your recording is transcribed for review before you send it."}</p>
        </form>
        {error && <p className="error-message" role="alert">{error}</p>}
        {messages.length > 0 && <section className="conversation" aria-live="polite">{messages.map((chatMessage, index) => <div className={`message-row ${chatMessage.role}`} key={`${chatMessage.role}-${index}`}><div className="message-bubble"><span className="message-label">{chatMessage.role === "user" ? "You" : "MicroLawyer AI"}</span><p>{chatMessage.content}</p>{chatMessage.response && <><div className="source-list"><p className="source-heading">Sources used</p>{chatMessage.response.sources.length ? <div className="source-badges">{chatMessage.response.sources.map((source) => <span className="source-badge" key={`${source.source_act}-${source.section_ref}`}>✓ Verified from {source.source_act}</span>)}</div> : <p className="helper-text">No relevant source was retrieved.</p>}</div><div className="suggestions">{suggestions.map((suggestion) => <button className="suggestion-chip" type="button" key={suggestion} onClick={() => void sendMessage(suggestion)} disabled={busy}>{suggestion}</button>)}</div></>}</div></div>)}{busy && <div className="message-row assistant"><div className="message-bubble thinking-bubble"><span className="message-label">MicroLawyer AI</span><span className="thinking-dots" aria-label="Assistant is thinking"><i /><i /><i /></span></div></div>}</section>}
        <p className="disclaimer">Informational only. This is not legal advice or a substitute for a licensed lawyer.</p>
      </section>
    </main>
  );
}
