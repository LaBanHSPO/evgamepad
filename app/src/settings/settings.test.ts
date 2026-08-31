/**
 * Settings, reports and data management: the surfaces that must not offer what they cannot do.
 *
 * The UI is the *first* of two checks — the gateway re-enforces every gate here. These tests prove
 * the page never presents a control the gateway would refuse, and never claims a safety it does
 * not have.
 */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { bytes } from "./types";

const here = dirname(fileURLToPath(import.meta.url));
const reportsDir = resolve(here, "..", "reports");

/** A file with comments stripped — they name the forbidden things in order to forbid them. */
function code(path: string): string {
  return readFileSync(path, "utf8").replace(/\/\*[\s\S]*?\*\/|\/\/.*/g, "").toLowerCase();
}

describe("the settings page", () => {
  const source = code(resolve(here, "Settings.tsx"));

  it("renders the server's schema rather than a list written here", () => {
    // This is what makes the boundary real: there is no control the gateway did not offer.
    expect(source).toContain("view.schema");
    expect(source).not.toMatch(/const settings\s*=\s*\[/);
  });

  it("offers no control for a safety property", () => {
    for (const forbidden of ["live", "demo mode", "bind", "client_secret", "access_token",
                             "auto_trade", "gate_close", "on_hot_path", "add account",
                             "new account"]) {
      expect(source, `settings mentions ${forbidden}`).not.toContain(forbidden);
    }
  });

  it("shows the account as a chip and never as a selector", () => {
    expect(source).toContain("view.account.broker");
    expect(source).not.toContain("<select");
  });

  it("links the two editors that already exist rather than duplicating them", () => {
    expect(source).toContain("view.elsewhere");
    // No playbook rule editor and no principles textarea on this page.
    expect(source).not.toContain("playbook_rule");
    expect(source).not.toContain("principles");
  });

  it("surfaces the gateway's own refusal rather than inventing a message", () => {
    expect(source).toContain("detail");
  });

  it("introduces no light theme and no mobile layout", () => {
    for (const file of ["Settings.tsx", "DataManagement.tsx"]) {
      const body = code(resolve(here, file));
      expect(body).not.toContain("prefers-color-scheme");
      expect(body).not.toContain("light");
      expect(body).not.toContain("@media (max-width");
    }
  });
});

describe("data management", () => {
  const source = code(resolve(here, "DataManagement.tsx"));
  const raw = readFileSync(resolve(here, "DataManagement.tsx"), "utf8");

  it("requires the exact phrase and a real elapsed hold", () => {
    expect(raw).toContain('const PHRASE = "DELETE EVERYTHING"');
    expect(raw).toContain("const HOLD_MS = 2000");
    // Measured from a timestamp, so letting go resets it rather than banking the time.
    expect(raw).toContain("Date.now() - heldSince");
    expect(raw).toContain("phrase === PHRASE && held >= HOLD_MS");
  });

  it("declares its state to the gateway rather than asserting authority over it", () => {
    expect(raw).toContain('locked: true');
    // The comment beside it says the gateway checks again; the test pins the intent.
    expect(readFileSync(resolve(here, "DataManagement.tsx"), "utf8"))
      .toContain("gateway checks these again");
  });

  it("offers a backup before the delete and never takes one after", () => {
    // A hidden recovery copy made after the final confirmation is not a safety net.
    const deleteFn = raw.slice(raw.indexOf("const doDelete"), raw.indexOf("const armed"));
    expect(deleteFn).not.toContain("/api/data/backup");
    // JSX wraps the copy across lines, so the check normalises whitespace first.
    const prose = source.replace(/\s+/g, " ");
    expect(prose).toContain("take a backup first");
    expect(prose).toContain("nothing is copied aside afterwards");
  });

  it("says what a backup excludes, because that is the part people assume wrongly", () => {
    expect(source).toContain("broker tokens");
    expect(source).toContain("replaceable");
  });

  it("exports through the streaming routes and offers no import", () => {
    expect(source).toContain("/api/export/trades.csv");
    expect(source).toContain("/api/export/journal.json");
    for (const inbound of ["/api/import", "upload", "mt5", "metatrader"]) {
      expect(source).not.toContain(inbound);
    }
  });
});

describe("the report builder", () => {
  const source = code(resolve(reportsDir, "ReportBuilder.tsx"));
  const css = readFileSync(resolve(reportsDir, "report-print.css"), "utf8");

  it("uses the browser's own Save as PDF", () => {
    expect(source).toContain("window.print()");
    // No headless browser on the VPS for a job the local one already does.
    for (const heavy of ["puppeteer", "playwright", "chromium", "jspdf", "html2canvas"]) {
      expect(source).not.toContain(heavy);
    }
  });

  it("re-fetches rather than hiding the outcome appendix", () => {
    // Turning it off must mean the gateway never assembled it, not that a section is display:none.
    expect(source).toContain("include_outcome");
    expect(source).toContain("report.outcome ?");
    expect(source).not.toContain("display: none");
  });

  it("puts the cover first and the outcome on its own page", () => {
    expect(css).toContain(".report .cover");
    expect(css).toContain("break-after: page");
    expect(css).toContain(".report .outcome");
    expect(css).toContain("break-before: page");
  });

  it("inverts to ink for print and leaves the screen dark", () => {
    expect(css).toContain("@media print");
    expect(css).toContain("background: #fff !important");
    // The inversion is inside the print block only.
    expect(css.slice(0, css.indexOf("@media print"))).not.toContain("#fff");
  });

  it("prints the heatmap score as a number, not only as a colour", () => {
    expect(source).toContain("math.round(day.score)");
    expect(css).toContain(".report .heatmap-cell");
  });

  it("hides the controls when printing", () => {
    expect(css).toContain(".no-print");
    expect(source).toContain('classname="no-print"');
  });

  it("keeps a section off a page break", () => {
    expect(css).toContain("break-inside: avoid");
  });
});

describe("formatting", () => {
  it("reads a size the way a person would", () => {
    expect(bytes(512)).toBe("512 B");
    expect(bytes(2048)).toBe("2 KB");
    expect(bytes(5 * 1024 * 1024)).toBe("5.0 MB");
  });
});
