// Stage [6] — spec §9.1. Scoring formula (implement exactly, not re-derived):
//
//   score = title_weight
//         + 15 if department matches your strongest project's domain
//         + 10 if tenure > 12 months        (new hires don't own headcount)
//         +  8 if public footprint exists   (GitHub, blog, talks — gives you a hook)
//         - 20 if title is recruiter AND headcount < 120
//
//   title_weight:
//     CTO / technical co-founder        100
//     VP Eng / Head of Engineering       90
//     Director of Engineering            80
//     Engineering Manager                70
//     Staff / Principal Engineer         65
//     Senior Engineer                    55
//     Technical recruiter / Head Talent  40
//     Junior / mid IC                    20
//
// Selection: top N for the headcount band (spec §3 — 2 for 11-50, 3 for
// 51-120, 3-4 for 121-200), must include >=1 budget-owner, at most 1
// recruiter, no two contacts with identical titles.

import type { contacts } from "../db/schema";

type ContactCandidate = typeof contacts.$inferSelect;

export function rankContacts(
  _candidates: ContactCandidate[],
  _headcount: number,
): ContactCandidate[] {
  throw new Error("not implemented — see spec §9.1 stage [6] scoring formula above");
}
