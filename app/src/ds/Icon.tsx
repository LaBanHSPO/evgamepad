import type { CSSProperties, HTMLAttributes } from "react";

/**
 * Port of components/core/Icon.jsx.
 *
 * The design-system original fetched each glyph from the lucide-static CDN at
 * runtime. The markup it produced is reproduced exactly, but the glyph bodies
 * are inlined from lucide-static 0.417.0 — the same version the bundle pinned —
 * so the icons render offline and on first paint.
 */

const SIZES: Record<string, number> = { xs: 12, sm: 14, md: 16, lg: 20, xl: 24 };

const GLYPHS: Record<string, string> = {
  shield:
    '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z" />',
  "gamepad-2":
    '<line x1="6" x2="10" y1="11" y2="11" /><line x1="8" x2="8" y1="9" y2="13" /><line x1="15" x2="15.01" y1="12" y2="12" /><line x1="18" x2="18.01" y1="10" y2="10" /><path d="M17.32 5H6.68a4 4 0 0 0-3.978 3.59c-.006.052-.01.101-.017.152C2.604 9.416 2 14.456 2 16a3 3 0 0 0 3 3c1 0 1.5-.5 2-1l1.414-1.414A2 2 0 0 1 9.828 16h4.344a2 2 0 0 1 1.414.586L17 18c.5.5 1 1 2 1a3 3 0 0 0 3-3c0-1.545-.604-6.584-.685-7.258-.007-.05-.011-.1-.017-.151A4 4 0 0 0 17.32 5z" />',
  terminal: '<polyline points="4 17 10 11 4 5" /><line x1="12" x2="20" y1="19" y2="19" />',
  target:
    '<circle cx="12" cy="12" r="10" /><circle cx="12" cy="12" r="6" /><circle cx="12" cy="12" r="2" />',
  "chart-candlestick":
    '<path d="M9 5v4" /><rect width="4" height="6" x="7" y="9" rx="1" /><path d="M9 15v2" /><path d="M17 3v2" /><rect width="4" height="8" x="15" y="5" rx="1" /><path d="M17 13v3" /><path d="M3 3v16a2 2 0 0 0 2 2h16" />',
  timer:
    '<line x1="10" x2="14" y1="2" y2="2" /><line x1="12" x2="15" y1="14" y2="11" /><circle cx="12" cy="14" r="8" />',
  database:
    '<ellipse cx="12" cy="5" rx="9" ry="3" /><path d="M3 5V19A9 3 0 0 0 21 19V5" /><path d="M3 12A9 3 0 0 0 21 12" />',
  bot: '<path d="M12 8V4H8" /><rect width="16" height="12" x="4" y="8" rx="2" /><path d="M2 14h2" /><path d="M20 14h2" /><path d="M15 13v2" /><path d="M9 13v2" />',
  check: '<path d="M20 6 9 17l-5-5" />',
  pencil:
    '<path d="M21.174 6.812a1 1 0 0 0-3.986-3.987L3.842 16.174a2 2 0 0 0-.5.83l-1.321 4.352a.5.5 0 0 0 .623.622l4.353-1.32a2 2 0 0 0 .83-.497z" /><path d="m15 5 4 4" />',
  play: '<polygon points="6 3 20 12 6 21 6 3" />',
  user: '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />',
  x: '<path d="M18 6 6 18" /><path d="m6 6 12 12" />',
  "chevron-up": '<path d="m18 15-6-6-6 6" />',
  "chevron-down": '<path d="m6 9 6 6 6-6" />',
  "chevron-left": '<path d="m15 18-6-6 6-6" />',
  "chevron-right": '<path d="m9 18 6-6-6-6" />',
  circle: '<circle cx="12" cy="12" r="10" />',
};

export type IconName = keyof typeof GLYPHS | (string & {});

export interface IconProps extends Omit<HTMLAttributes<HTMLSpanElement>, "color"> {
  name?: IconName;
  size?: "xs" | "sm" | "md" | "lg" | "xl" | number;
  color?: string;
  style?: CSSProperties;
}

export function Icon({ name = "circle", size = "md", color, style, className, ...rest }: IconProps) {
  const px = typeof size === "number" ? size : SIZES[size] || 16;
  const body = GLYPHS[name] ?? "";
  return (
    <span
      role="img"
      aria-label={name}
      data-icon={name}
      className={className}
      style={{
        display: "inline-flex",
        width: px,
        height: px,
        flex: "0 0 auto",
        color: color || "currentColor",
        ...style,
      }}
      {...rest}
    >
      <svg
        width={px}
        height={px}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        dangerouslySetInnerHTML={{ __html: body }}
      />
    </span>
  );
}
