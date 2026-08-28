# Evening Forex Gold Gamepad

Web game giao dịch forex/vàng bằng tay cầm 8BitDo trên cTrader demo, kèm trading journal
(playbook, voice memo, replay, tilt-meter, process-weighted score). Chi tiết sản phẩm: `README.md`.

Repo này có gắn **bộ skill BA (AI4BA BA-Kit)** để viết tài liệu nghiệp vụ cho từng feature.

## Skill BA đã cài

| Lệnh | Làm gì | Ghi ra |
|---|---|---|
| `/urd` | User Requirements — nhu cầu `UN-*`, user journeys ưu tiên | `docs/{feature}/{feature}-urd.md` |
| `/srs` | Software Requirements — `FR-*`/`NFR-*`, BR, Error Matrix, ERD, flows, states | `docs/{feature}/srs/{feature}-spec.md` (+ `-flows/-erd/-states.md`) |
| `/user-flow` | Luồng người dùng + danh sách màn hình (mermaid) | `docs/{feature}/srs/{feature}-userflow.md` |
| `/wireframe-html` | Wireframe HTML B&W click được, 1 file/flow + index điều hướng | `docs/{feature}/html-wireframe/` |
| `/ask` | Hỏi-đáp nghiệp vụ trên tài liệu đã có (chỉ đọc, không ghi) | — |
| `/cr` | Change Request: đánh giá impact 6 chiều rồi áp thay đổi xuyên tài liệu | `docs/cr/CR-{YYYYMMDD}-{NNN}.md` |
| `/userguide` | Cẩm nang người dùng (Diátaxis), có chụp màn hình tự động | `docs/userguide/` |

## Cấu trúc

```
.claude/skills/     11 skill (7 chính + kg, wireframe-ascii, prototype-html, figma)
.claude/rules/      13 rule dùng chung — naming-conventions.md là nguồn path duy nhất
.claude/agents/     9 reviewer agent (senior-ba, qa-, tech-, uxui-, flow-, po-, manual-reviewer,
                    change-tracker, gap-analyst)
.claude/scripts/    mermaid-verify.mjs
.claude/hooks/      auto-changelog · status-transition · post-edit-stale · kg-refresh · session-init
_templates/         15 template output
docs/{feature}/     tài liệu BA sinh ra (sống chung với docs/how-the-app-works.html sẵn có)
docs/_shared/       nền tảng dùng chung: project-profile · definitions · system-overview ·
                    operating-environment · changelog (traceability/screen-patterns sinh sau)
```

## Quy tắc khi chạy skill BA

- **Không tự ghi file trước khi user duyệt.** Mọi skill có approval gate (L1/L2) hoặc HARD STOP —
  chạy ở main conversation, không dùng `context: fork`, không để subagent tự Write file đích.
- **Reviewer agent là bắt buộc**, không phải tuỳ chọn: `/user-flow` → `flow-reviewer` (Phase E.5),
  `/userguide` → `manual-reviewer` (Pha C), `/srs` → `senior-ba` + `qa-reviewer` + `tech-reviewer`.
- **Verify mermaid sau mỗi lần Write** file có sơ đồ:
  `node .claude/scripts/mermaid-verify.mjs --file <path>` — không báo "xong" khi còn block fail.
- **Knowledge Graph chọn file, prose kết luận.** `node .claude/skills/kg/engine/kg-query.mjs ...`
  chỉ dùng để khoanh vùng đọc; kết luận nghiệp vụ phải đọc prose. Xem `.claude/rules/kg-usage.md`.

## Giới hạn đã biết

- **`/srs` chỉ chạy được Tầng 1 (spec).** Tầng 2–4 gọi `/usecase` `/sequence` `/erd` `/state`
  `/userstory` `/ac` — chưa cài. Cần thì import thêm từ BA-Kit.
- **`/userguide` chưa chụp được ảnh** — thiếu Playwright. Cài khi cần:
  `cd .claude/skills/userguide/engine && npm install && npx playwright install chromium`
- `wireframe-ascii`, `prototype-html`, `figma` copy về **chỉ để đường dẫn `@` không gãy**;
  chưa kiểm chứng chạy đủ.

## Công cụ ngoài

`node` v22 ✅ · `mmdc` 11.16 + Chrome for Testing ✅ · `playwright` ❌ (chỉ `/userguide` cần)
