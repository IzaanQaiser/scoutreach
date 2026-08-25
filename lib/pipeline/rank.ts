// Stage [6] — spec §9.1.
//
// Scoring formula as originally specified:
//
//   score = title_weight
//         + 15 if department matches your strongest project's domain
//         + 10 if tenure > 12 months        (new hires don't own headcount)
//         +  8 if public footprint exists   (GitHub, blog, talks — gives you a hook)
//         - 20 if title is recruiter AND headcount < 120
//
// ADAPTED (confirmed with user 2026-08-25): Apollo's free People Search
// (stage [5]) doesn't return seniority/department/linkedin/tenure —
// verified against Apollo's API schema, see ../providers/contact-provider.ts.
// Those fields only exist after enrich() (stage [7]), which must run
// AFTER ranking/selection, not before. So this implementation:
// - computes title_weight from the title STRING (still fully available)
// - approximates the department bonus from title text too, when the
//   caller supplies domain keywords (e.g. ["engineering"]) — optional,
//   since the real source (Phase 4's project data) doesn't exist yet
// - drops the tenure term entirely (unknown pre-enrichment, no proxy)
// - drops the public-footprint term entirely (no data source in scope)
// - keeps the recruiter penalty (title text is enough to detect it)
//
// title_weight:
//   CTO / technical co-founder        100
//   VP Eng / Head of Engineering       90
//   Director of Engineering            80
//   Engineering Manager                70
//   Staff / Principal Engineer         65
//   Senior Engineer                    55
//   Technical recruiter / Head Talent  40
//   Junior / mid IC (fallback)         20
//
// Selection: top N for the headcount band (spec §3 — 2 for 11-50, 3 for
// 51-120, 3-4 for 121-200), must include >=1 budget-owner, at most 1
// recruiter, no two contacts with identical titles. Degrades gracefully
// (never throws) if the candidate pool can't satisfy every constraint —
// e.g. no budget-owner exists in the pool at all.

import type { contacts } from "../db/schema";

type ContactCandidate = typeof contacts.$inferSelect;

interface TitleTier {
  pattern: RegExp;
  weight: number;
  isBudgetOwner: boolean;
}

const TITLE_TIERS: TitleTier[] = [
  { pattern: /\b(chief technology officer|cto|technical co-?founder)\b/i, weight: 100, isBudgetOwner: true },
  { pattern: /\b(vp|vice president)\s*(of\s+)?engineering\b|\bhead of engineering\b/i, weight: 90, isBudgetOwner: true },
  { pattern: /\bdirector\s+(of\s+)?engineering\b/i, weight: 80, isBudgetOwner: true },
  { pattern: /\bengineering manager\b/i, weight: 70, isBudgetOwner: true },
  { pattern: /\b(staff|principal)\s+engineer\b/i, weight: 65, isBudgetOwner: false },
  { pattern: /\bsenior\s+engineer\b/i, weight: 55, isBudgetOwner: false },
  { pattern: /\b(technical recruiter|head of talent)\b/i, weight: 40, isBudgetOwner: false },
];
const FALLBACK_WEIGHT = 20;
const RECRUITER_PATTERN = /recruit|talent acquisition/i;
const DEPARTMENT_BONUS = 15;
const RECRUITER_PENALTY = -20;
const RECRUITER_PENALTY_HEADCOUNT_THRESHOLD = 120;

function classify(title: string): { weight: number; isBudgetOwner: boolean } {
  const tier = TITLE_TIERS.find((t) => t.pattern.test(title));
  return tier ? { weight: tier.weight, isBudgetOwner: tier.isBudgetOwner } : { weight: FALLBACK_WEIGHT, isBudgetOwner: false };
}

export function isRecruiterTitle(title: string): boolean {
  return RECRUITER_PATTERN.test(title);
}

export interface ScoreOptions {
  // Optional proxy for the spec's "department matches strongest project's
  // domain" — matched against the title string. Real source (Phase 4
  // project data) doesn't exist yet, so this defaults to no bonus.
  departmentKeywords?: string[];
}

export function scoreContact(
  candidate: ContactCandidate,
  headcount: number,
  { departmentKeywords = [] }: ScoreOptions = {},
): number {
  const title = candidate.title ?? "";
  const { weight } = classify(title);

  let score = weight;

  if (departmentKeywords.some((kw) => title.toLowerCase().includes(kw.toLowerCase()))) {
    score += DEPARTMENT_BONUS;
  }

  if (isRecruiterTitle(title) && headcount < RECRUITER_PENALTY_HEADCOUNT_THRESHOLD) {
    score += RECRUITER_PENALTY;
  }

  return score;
}

// spec §3: contacts per company by headcount band.
export function targetContactCount(headcount: number): number {
  if (headcount <= 50) return 2;
  if (headcount <= 120) return 3;
  return 4;
}

export function rankContacts(
  candidates: ContactCandidate[],
  headcount: number,
  options: ScoreOptions = {},
): ContactCandidate[] {
  const targetN = targetContactCount(headcount);

  const scored = candidates
    .map((c) => ({ candidate: c, score: scoreContact(c, headcount, options) }))
    .sort((a, b) => b.score - a.score);

  const selected: ContactCandidate[] = [];
  const seenTitles = new Set<string>();
  let recruiterCount = 0;

  for (const { candidate } of scored) {
    if (selected.length >= targetN) break;

    const title = (candidate.title ?? "").trim().toLowerCase();
    if (title && seenTitles.has(title)) continue;

    if (isRecruiterTitle(candidate.title ?? "")) {
      if (recruiterCount >= 1) continue;
      recruiterCount += 1;
    }

    selected.push(candidate);
    if (title) seenTitles.add(title);
  }

  // Ensure >=1 budget-owner if the pool has one and it didn't already
  // make the cut — swap out the lowest-scored non-budget-owner pick.
  // If the pool has no budget-owner at all, this is a no-op (degrades
  // gracefully rather than throwing).
  const hasBudgetOwner = selected.some((c) => classify(c.title ?? "").isBudgetOwner);
  if (!hasBudgetOwner) {
    const bestBudgetOwner = scored.find(({ candidate }) => classify(candidate.title ?? "").isBudgetOwner);
    if (bestBudgetOwner && selected.length > 0) {
      selected[selected.length - 1] = bestBudgetOwner.candidate;
    } else if (bestBudgetOwner) {
      selected.push(bestBudgetOwner.candidate);
    }
  }

  return selected;
}
