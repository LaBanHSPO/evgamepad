/** Shapes served by `/api/settings`, `/api/reports` and `/api/data/*`. */

export interface SettingDefinition {
  key: string;
  describe: string;
  default: unknown;
}

export interface SettingsView {
  settings: Record<string, unknown>;
  schema: SettingDefinition[];
  symbols: string[];
  /** What the account is. Never anything that could authenticate as it. */
  account: { broker: string; platform: string; mode: string; readOnly: boolean; note?: string };
  elsewhere: { what: string; where: string }[];
}

export interface BackupRow {
  name: string;
  bytes: number;
  modified: number;
}

export interface ArchiveSummary {
  createdAt: number;
  files: number;
  counts: Record<string, number>;
  schema: string[];
}

export interface ReportView {
  kind: "period" | "session";
  period: string;
  from?: number | null;
  to?: number | null;
  sessionId?: string;
  generatedAt: number;
  cover: Record<string, unknown>;
  heatmap?: { sessionId: string; score: number | null; trades: number; declined: number }[];
  process?: Record<string, unknown>;
  playbooks?: Record<string, unknown>[];
  mistakes?: { mistakes: { code: string; count: number }[]; focus: string | null };
  groups?: { groups: Record<string, number>; unclassified: number };
  readiness?: { item: string; ok: boolean | null }[];
  analysis?: { thesis: string | null } | null;
  trades?: { cid: string; symbol: string; side: string; rMultiple: number | null }[];
  /** Present only when the appendix was asked for by name. */
  outcome?: Record<string, unknown>;
  disclaimer: string;
}

export function bytes(value: number): string {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(0)} KB`;
  return `${(value / (1024 * 1024)).toFixed(1)} MB`;
}
