/** Shapes served by `/api/playbooks*`. */

export interface RuleGrade {
  code: string;
  label: string;
  kind: "auto" | "manual";
  required: boolean;
  ok: boolean;
  unknown: boolean;
  actual: string | null;
  expected: string | null;
}

export interface Grade {
  cid: string;
  playbookId: string;
  required_pass: number;
  required_total: number;
  clean: boolean;
  results: RuleGrade[];
}

export interface PlaybookRule {
  ord: number;
  kind: "auto" | "manual";
  code: string;
  params: Record<string, unknown>;
  label: string | null;
  required: boolean;
}

export interface Playbook {
  id: string;
  name: string;
  slug: string;
  method: string;
  symbols: string[];
  detector_tag: string | null;
  narrative: string | null;
  active: boolean;
  retired_at: number | null;
  rules: PlaybookRule[];
}

export interface GradePreview {
  grade: Grade;
  playbookName: string;
  summary: string;
  firstFailure: RuleGrade | null;
}

/** What the overlay prints beneath the size line. */
export function gradeLine(preview: GradePreview | null): string {
  if (preview === null) return "grading unavailable";
  const failure = preview.firstFailure;
  const detail = failure
    ? ` · ✗ ${failure.label}${failure.actual ? ` (${failure.actual})` : ""}`
    : "";
  return `[${preview.playbookName}] ${preview.summary}${detail}`;
}

/** Manual rules the player can still answer after the trade. */
export function pendingManual(grade: Grade | null): RuleGrade[] {
  if (grade === null) return [];
  return grade.results.filter((r) => r.kind === "manual" && r.unknown);
}
