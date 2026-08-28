---
type: project-profile
status: draft
updated: 2026-08-28
links: []
---

# Project Profile

> Kho thông tin cấp dự án tích lũy dần — skill thiếu thông tin sẽ hỏi rồi ghi vào đây, skill sau
> đọc lại không hỏi nữa (xem `.claude/rules/project-profile.md`). Chỉ tạo section khi có nội dung
> thật; mỗi mục kèm ngày ghi.

## Domain

Evening Forex Gold Gamepad là **web game trên Chrome desktop** dùng để giao dịch forex và vàng
bằng tay cầm 8BitDo Ultimate 2 Wireless trên **tài khoản demo cTrader**. Trên nền game là một
**nhật ký giao dịch** lấy tinh thần Edgewonk và TradeZella nhưng dựng lại cho tay cầm.

Bài toán nó xử lý là **chất lượng quyết định, không phải lợi nhuận**: playbook chấm điểm mỗi lệnh
theo chính luật của nó *trước khi* người chơi bấm nút, voice memo ghi lại lý do vào lệnh (vì không
thể gõ phím lúc đang giao dịch), replay tua lại lệnh qua tape bằng cần analog, tilt-meter đọc trạng
thái tâm lý từ chính tay cầm, và process score chấm buổi tối theo quyết định thay vì theo tiền.

Mục tiêu cuối là **sự tự tin và niềm vui** — cải thiện chất lượng quyết định. *(2026-08-28)*

**Trạng thái dự án:** hoàn tất giai đoạn lập kế hoạch, chưa viết code ứng dụng. Nguồn quyền lực là
`plans/260824-1506-evening-forex-gold-gamepad/plan.md` (14 phase). *(2026-08-28)*

## Người dùng & thuật ngữ

| Nhóm user | Gọi là gì trong doc | Ghi chú | Ngày |
|---|---|---|---|
| Người vận hành tay cầm, ra lệnh, viết nhật ký | **người chơi** | Sản phẩm cá nhân, một người dùng duy nhất. README gọi là "player" — dùng "người chơi" trong doc tiếng Việt, không dùng "trader" hay "khách hàng" | 2026-08-28 |
| AI desk (sentinel, copilot, coach) | **AI desk** | KHÔNG phải người dùng — là actor hệ thống tư vấn bên lề, không bao giờ chạm đường đặt lệnh | 2026-08-28 |
| cTrader / Spotware | **sàn** | Hệ thống ngoài, là matching engine thật | 2026-08-28 |

## Đối thủ / benchmark

| Tên | Mạnh về | Monetization | Nguồn / ngày |
|---|---|---|---|
| Edgewonk | Nhật ký giao dịch, phân tích thói quen, chấm điểm kỷ luật | Trả phí một lần / theo năm | README.md · 2026-08-28 |
| TradeZella | Nhật ký + heatmap + review, UX hiện đại | Thuê bao | README.md · 2026-08-28 |

> Cả hai là **benchmark tính năng nhật ký**, không phải đối thủ thương mại — dự án này không bán ra.

## Thị trường & ngôn ngữ

- Công cụ cá nhân, không phát hành thương mại. *(2026-08-28)*
- Giao diện sản phẩm: tiếng Anh (README, story, mockup đều tiếng Anh). Tài liệu BA: tiếng Việt. *(2026-08-28)*
- Thị trường giao dịch: forex và vàng (XAU), qua cTrader demo. *(2026-08-28)*

## Compliance

- **Chỉ tài khoản demo.** Không có tiền thật trong bất kỳ đường nào của hệ thống. *(2026-08-28)*
- **Không phải lời khuyên đầu tư.** README tuyên bố rõ: "Demo only. Not advice. Entertainment, not
  alpha." Mọi nội dung AI desk sinh ra phải giữ đúng khung này. *(2026-08-28)*
- Voice memo tạo **dữ liệu giọng nói cá nhân** — cần nêu rõ nơi lưu và cách xoá trong tài liệu
  tính năng liên quan (phase 8 voice, phase 13 data portability). *(2026-08-28)*

## Ghi chú khác

| Câu hỏi | Trả lời | Ngày | Skill hỏi |
|---|---|---|---|
| Chia feature cho `docs/{feature}/` thế nào? | Theo **năng lực nghiệp vụ**, không bám 14 phase xây dựng | 2026-08-28 | setup docs |
| Dự án có dùng Jira không? | Không → bỏ `jira-map.md` | 2026-08-28 | setup docs |
