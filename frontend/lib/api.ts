import type { CaseRecord, CaseType, ChatLanguage, ChatResponse, Jurisdiction, LearnResponse, QuickCheckResponse } from "./types";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const FRIENDLY_ERROR = "Something went wrong. Please try again in a moment.";

async function requestError(response: Response, operation: string): Promise<Error> {
  const raw = await response.text();
  let details: unknown = raw;
  try { details = raw ? JSON.parse(raw) : raw; } catch { /* Keep non-JSON responses available in the console. */ }
  console.error(`[MicroLawyer AI] ${operation} failed`, { status: response.status, details });
  return new Error(FRIENDLY_ERROR);
}

function networkError(error: unknown, operation: string): Error {
  console.error(`[MicroLawyer AI] ${operation} request failed`, error);
  return new Error(FRIENDLY_ERROR);
}

export async function getApiHealth(): Promise<{ status: string }> {
  try {
    const response = await fetch(`${apiUrl}/health`);
    if (!response.ok) throw await requestError(response, "Health check");
    return response.json();
  } catch (error) { throw networkError(error, "Health check"); }
}

export async function askChat(input: { message: string; province: Jurisdiction; language: ChatLanguage; domain?: "tenancy" | "labor" | "consumer" | "criminal" }): Promise<ChatResponse> {
  try {
    const response = await fetch(`${apiUrl}/api/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
    if (!response.ok) throw await requestError(response, "Chat");
    return response.json();
  } catch (error) { throw networkError(error, "Chat"); }
}

export async function transcribeVoice(file: File): Promise<{ text: string }> {
  const formData = new FormData();
  formData.append("file", file);
  try {
    const response = await fetch(`${apiUrl}/api/voice/transcribe`, { method: "POST", body: formData });
    if (!response.ok) throw await requestError(response, "Voice transcription");
    return response.json();
  } catch (error) { throw networkError(error, "Voice transcription"); }
}

export async function generateDocument(input: {
  document_type: "legal_notice" | "fir_draft" | "rental_dispute_letter";
  language: "en" | "ur" | "roman-urdu";
  jurisdiction: Jurisdiction;
  facts: Record<string, string>;
}): Promise<Blob> {
  try {
    const response = await fetch(`${apiUrl}/api/documents/generate`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
    if (!response.ok) throw await requestError(response, "PDF generation");
    return response.blob();
  } catch (error) { throw networkError(error, "PDF generation"); }
}

export async function draftDocument(input: {
  document_type: "legal_notice" | "fir_draft" | "rental_dispute_letter";
  language: "en" | "ur" | "roman-urdu";
  jurisdiction: Jurisdiction;
  details: Record<string, string>;
}): Promise<{ facts: string; requested_action: string; provider: string }> {
  try {
    const response = await fetch(`${apiUrl}/api/documents/draft`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
    if (!response.ok) throw await requestError(response, "AI document draft");
    return response.json();
  } catch (error) { throw networkError(error, "AI document draft"); }
}

export async function getLearningCards(domain: "tenancy" | "labor" | "consumer" | "criminal", jurisdiction: Jurisdiction): Promise<LearnResponse> {
  try {
    const response = await fetch(`${apiUrl}/api/learn/${domain}?jurisdiction=${jurisdiction}`);
    if (!response.ok) throw await requestError(response, "Learning cards");
    return response.json();
  } catch (error) { throw networkError(error, "Learning cards"); }
}

export async function getDocumentChecklist(input: {
  document_type: "legal_notice" | "fir_draft" | "rental_dispute_letter";
  jurisdiction: Jurisdiction;
}): Promise<{ items: string[]; provider: string; sources: string[] }> {
  try {
    const response = await fetch(`${apiUrl}/api/documents/checklist`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
    if (!response.ok) throw await requestError(response, "Document checklist");
    return response.json();
  } catch (error) { throw networkError(error, "Document checklist"); }
}

export async function quickCheck(input: { scenario: string; province: Jurisdiction; language: ChatLanguage; domain: "tenancy" | "labor" | "consumer" | "criminal" }): Promise<QuickCheckResponse> {
  try {
    const response = await fetch(`${apiUrl}/api/quick-check`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) });
    if (!response.ok) throw await requestError(response, "Quick check");
    return response.json();
  } catch (error) { throw networkError(error, "Quick check"); }
}

export async function listCases(anonymousId: string): Promise<CaseRecord[]> {
  try { const response = await fetch(`${apiUrl}/api/cases?anonymous_id=${encodeURIComponent(anonymousId)}`); if (!response.ok) throw await requestError(response, "Case list"); return response.json(); }
  catch (error) { throw networkError(error, "Case list"); }
}

export async function createCase(input: { anonymous_id: string; case_type: CaseType; case_date: string; notes: string }): Promise<CaseRecord> {
  try { const response = await fetch(`${apiUrl}/api/cases`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(input) }); if (!response.ok) throw await requestError(response, "Case creation"); return response.json(); }
  catch (error) { throw networkError(error, "Case creation"); }
}

export async function updateMilestone(caseId: string, milestoneId: string, completed: boolean): Promise<void> {
  try { const response = await fetch(`${apiUrl}/api/cases/${caseId}/milestones/${milestoneId}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ completed }) }); if (!response.ok) throw await requestError(response, "Milestone update"); }
  catch (error) { throw networkError(error, "Milestone update"); }
}

export async function addMilestone(caseId: string, title: string): Promise<void> {
  try { const response = await fetch(`${apiUrl}/api/cases/${caseId}/milestones`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ title }) }); if (!response.ok) throw await requestError(response, "Milestone creation"); }
  catch (error) { throw networkError(error, "Milestone creation"); }
}
