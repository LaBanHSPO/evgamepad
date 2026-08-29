---
type: definitions
status: draft
updated: 2026-08-28
links: ["[[project-profile]]", "[[system-overview]]"]
---

# Definitions

> Từ điển thuật ngữ nghiệp vụ dùng chung mọi feature. Nguồn: `README.md`, `story.md`,
> `plans/260824-1506-evening-forex-gold-gamepad/`. Thuật ngữ mới phát sinh khi viết SRS thì bổ sung
> vào đây thay vì định nghĩa lại trong từng doc.

## Điều khiển & đặt lệnh

| Thuật ngữ | Nghĩa |
|---|---|
| **Clutch** | Giữ `LT`. Không có gì được bắn ra nếu không giữ clutch. Là chốt an toàn cấp một |
| **ARM** | Trạng thái đã chọn hướng (`A` mua / `B` bán) nhưng **chưa** gửi lệnh |
| **Fire** | Bấm `RT` khi đang ARM → gửi intent đi. `LT+RT` là cặp xác nhận bắt buộc |
| **Arms cancelled** | Số lần người chơi đã ARM rồi **chủ động huỷ**, không bắn. Là con số **lớn nhất trên HUD sau giá** — đo kỷ luật, đếm tăng dần, màu xanh |
| **Flatten (panic)** | `Y` — đóng toàn bộ vị thế ngay |
| **GameOverlay** | Lớp menu an toàn mở bằng `Menu`. Mở overlay **huỷ ARM và khoá mở lệnh mới** |
| **Modify preview** | Sửa SL/TP trong overlay chỉ **dàn sẵn** một bản xem trước, chưa gửi đi. Vẫn cần `LT+RT` mới tới được cTrader |
| **Intent** | Gói ý định `{clutch, armedAt, relativeSl?, relativeTp?}` client gửi lên gateway. **Không phải lệnh** — gateway mới là nơi duyệt |

> Hợp đồng điều hướng chung của Playbook, Journal, System, Reports, Settings: D-pad chọn đích,
> `LB/RB` đổi tab, `A` vào/áp dụng, `B` quay lại, `Menu` thoát.
> **Điều hướng và áp dụng preference không bao giờ phát ra được lệnh open/modify.**

## Nhật ký & chấm điểm

| Thuật ngữ | Nghĩa |
|---|---|
| **Playbook** | Tập luật giao dịch do người chơi tự khai. Chấm điểm mỗi lệnh theo chính luật của nó **trước khi** người chơi bấm nút |
| **Rule registry** | Nơi lưu và phiên bản hoá các luật playbook |
| **Process Score** | Điểm chấm buổi giao dịch theo **chất lượng quyết định**, không theo lãi lỗ. Chốt **ngay khi đóng phiên**, tính trên bằng chứng quy trình tại thời điểm bắn; chỉ các con số kết quả bằng tiền mới chờ lệnh ngã ngũ (chốt 2026-08-28) |
| **Tilt-meter** | Chỉ số trạng thái tâm lý đọc từ **hành vi trên tay cầm** (nhịp bấm, huỷ, tần suất) cộng **dữ liệu sẵn có trong nhật ký** (thua gần nhất, khối lượng so mức thường, luật playbook không đạt). Mọi mốc so sánh là mức thường của chính người chơi |
| **Adaptive friction** | Cơ chế tăng độ khó thao tác khi tilt-meter cao — cản người chơi giao dịch trong trạng thái xấu |
| **Voice memo** | Ghi âm lý do vào lệnh bằng `LB+RB` (push-to-talk), vì không thể gõ phím khi đang giao dịch |
| **Tape freeze** | Đóng băng dữ liệu thị trường quanh thời điểm lệnh để replay tua lại đúng bối cảnh |
| **Replay** | Tua lại lệnh qua tape bằng cần analog |
| **Readiness / analysis** | Bước chuẩn bị trước phiên: tự đánh giá trạng thái và phân tích thị trường, tạo ra plan snapshot |
| **Plan snapshot** | Bản chụp kế hoạch trước phiên, dùng để đối chiếu với thứ thực sự đã làm |

## AI desk

| Thuật ngữ | Nghĩa |
|---|---|
| **AI desk** | Cụm dịch vụ tư vấn bên lề. **Không bao giờ chạm đường đặt lệnh** |
| **Sentinel** | Thành phần quan sát nhanh, chu kỳ 1–5 s |
| **Copilot** | Thành phần tư vấn chậm hơn, chu kỳ 1–30 s |
| **Coach** | Phản hồi huấn luyện, có TTS đọc ra |
| **signal.item** | Đơn vị tín hiệu duy nhất mà cold path (sentinel/copilot/TradingView webhook) được phép sinh ra |

## Hệ thống

| Thuật ngữ | Nghĩa |
|---|---|
| **Gateway** | Thành phần **duy nhất** được duyệt một lệnh demo. Chạy Docker trên Ubuntu VPS |
| **Broker link** | Kết nối cTrader Open API **nằm bên trong gateway** (thư viện `ctrader-open-api`), dịch lệnh đã duyệt sang thông điệp Open API. Không phải một dịch vụ riêng |
| **Hot path** | Đường đặt lệnh, ưu tiên độ trễ |
| **Cold path** | Đường tín hiệu AI, 1–30 s, không bao giờ chặn một lệnh |
| **Journal path** | Đường ghi nhật ký, chậm nhất, **không bao giờ đi trên order socket** |
