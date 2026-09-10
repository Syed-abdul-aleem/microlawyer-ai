export type Jurisdiction = "federal" | "punjab" | "sindh" | "kp" | "balochistan";

export type ChatLanguage = "en" | "urdu" | "roman-urdu";

export type ChatSource = {
	source_act: string;
	section_ref: string | null;
	similarity: number;
};

export type ChatResponse = {
	answer: string;
	jurisdiction: Jurisdiction;
	provider: string;
	sources: ChatSource[];
};

export type LearnCard = { title: string; body: string; source_act: string };
export type LearnResponse = { domain: "tenancy" | "labor" | "consumer" | "criminal"; jurisdiction: Jurisdiction; cards: LearnCard[]; provider: string };
export type QuickCheckResponse = { verdict: "Yes" | "No" | "It depends"; reason: string; jurisdiction: Jurisdiction; provider: string; sources: ChatSource[] };
export type CaseType = "tenancy" | "labor" | "consumer" | "criminal" | "other";
export type CaseMilestone = { id: string; case_id: string; title: string; completed: boolean; position: number; completed_at: string | null };
export type CaseRecord = { id: string; anonymous_id: string; case_type: CaseType; case_date: string; notes: string; created_at: string; updated_at: string; milestones: CaseMilestone[] };
