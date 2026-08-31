/** The overlay line, and the rule that skipping the checklist costs nothing. */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { expect, it } from "vitest";
import type { Grade, GradePreview, RuleGrade } from "./types";
import { gradeLine, pendingManual } from "./types";

const here = dirname(fileURLToPath(import.meta.url));

function rule(over: Partial<RuleGrade> = {}): RuleGrade {
  return {
    code: "ema_distance", label: "Not chasing", kind: "auto", required: true,
    ok: true, unknown: false, actual: null, expected: null, ...over,
  };
}

function preview(over: Partial<GradePreview> = {}): GradePreview {
  const grade: Grade = {
    cid: "01ABC", playbookId: "pb-range-break", required_pass: 4, required_total: 5,
    clean: false, results: [rule()],
  };
  return { grade, playbookName: "M5 range break", summary: "4/5 rules OK",
           firstFailure: null, ...over };
}

it("names the playbook and counts the rules before the fire", () => {
  expect(gradeLine(preview())).toBe("[M5 range break] 4/5 rules OK");
});

it("adds the one failure the overlay has room for", () => {
  const line = gradeLine(preview({
    firstFailure: rule({ ok: false, label: "Not chasing", actual: "3.00 ATR" }),
  }));
  expect(line).toBe("[M5 range break] 4/5 rules OK · ✗ Not chasing (3.00 ATR)");
});

it("says grading is unavailable rather than inventing a score", () => {
  expect(gradeLine(null)).toBe("grading unavailable");
});

it("only offers the manual rules that are still unanswered", () => {
  const grade: Grade = {
    cid: "01ABC", playbookId: "pb", required_pass: 1, required_total: 2, clean: false,
    results: [
      rule({ code: "no_chase", kind: "manual", unknown: true, ok: false }),
      rule({ code: "waited_for_retest", kind: "manual", unknown: false, ok: true }),
      rule({ code: "ema_distance", kind: "auto", unknown: true, ok: false }),
    ],
  };
  expect(pendingManual(grade).map((r) => r.code)).toEqual(["no_chase"]);
  expect(pendingManual(null)).toEqual([]);
});

it("skipping the checklist sends no answers at all", () => {
  // A skip must post nothing, so every unanswered rule stays unknown server-side.
  const source = readFileSync(resolve(here, "PostTradeChecklist.tsx"), "utf8");
  expect(source).toMatch(/onDone\(\{\}\)/);
  expect(source).toContain("skipping costs nothing");
});

it("renders the player's narrative as text, never as markup", () => {
  const source = readFileSync(resolve(here, "PlaybookPicker.tsx"), "utf8");
  expect(source).not.toContain("dangerously");
  expect(source).toContain("{playbooks.find((p) => p.id === activeId)?.narrative}");
});

it("treats no playbook as a valid state rather than an error", () => {
  const source = readFileSync(resolve(here, "PlaybookPicker.tsx"), "utf8");
  expect(source).toContain("unplanned");
  expect(source).toMatch(/onSelect\(null\)/);
});
