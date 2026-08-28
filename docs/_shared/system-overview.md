---
type: system-overview
status: draft
updated: 2026-08-28
links: ["[[project-profile]]", "[[operating-environment]]", "[[definitions]]"]
---

# System Overview

> Kiến trúc và ranh giới hệ thống. Nguồn: `README.md` mục Architecture + `docs/how-the-app-works.svg`
> + `plans/260824-1506-evening-forex-gold-gamepad/plan.md`. Đây là tài liệu **nghiệp vụ về ranh giới**,
> không phải thiết kế kỹ thuật chi tiết.

## Ranh giới quan trọng nhất

> **Gateway là thành phần DUY NHẤT được phép duyệt một lệnh demo.**

Tay cầm và ứng dụng Chrome chỉ **chuẩn bị ý định** (intent). Execution sidecar (Python) dịch một lệnh
đã được duyệt thành thông điệp cTrader Open API. **Spotware — không phải VPS — mới là matching engine
thật.** Mọi tài liệu tính năng phải giữ đúng ranh giới này: không tính năng nào được mô tả như thể
client tự đặt được lệnh.

## Ba đường đi

### 1. Order hot path — đường đặt lệnh

```
tay cầm → app Chrome đang focus → gateway (kiểm tra rủi ro) → execution sidecar → cTrader demo
```

Chi tiết: pad → intent `{clutch, armedAt, relativeSl?, relativeTp?}` → WSS → cid reserve → risk check
→ `MARKET ProtoOANewOrderReq` → execution event → ack → rung tay cầm.

Sửa bảo vệ (SL/TP) của vị thế đang mở dùng `ProtoOAAmendPositionSLTPReq`, và **phải qua một lần
xác nhận `LT+RT` nữa**.

### 2. Broker return path — đường phản hồi từ sàn

Dữ liệu thị trường, khớp lệnh, vị thế và acknowledgement đi ngược về qua đúng chuỗi dịch vụ tin cậy
đó để cập nhật HUD và rung tay cầm.

### 3. Learning path — đường học hỏi

AI coaching, chuyển giọng nói thành văn bản, ghi nhật ký, replay và chấm điểm chạy **song song** với
đường đặt lệnh. Chúng có thể làm giàu hoặc ghi lại một phiên, nhưng **không bao giờ đặt được lệnh**.

- **Cold path:** sentinel 1–5 s · copilot 1–30 s · TradingView webhook → chỉ sinh ra `signal.item`.
- **Journal path** (chậm hơn nữa, không bao giờ đi trên order socket): readiness/analysis + plan
  snapshot → trade facts/events → voice/transcript + tape freeze → Process Score đã chốt →
  review/heatmap/history hằng ngày → report/export/backup.

## Ngân sách độ trễ

| Chặng | Mục tiêu |
|---|---|
| Pad poll → intent | < 16 ms |
| Nhà → VPS WS | 15–80 ms (chiếm phần lớn) |
| Gateway risk check | < 5 ms |
| VPS → Spotware demo ack | vài chục ms là điển hình |
| AI advice | 1–5 s, **không bao giờ chặn một lệnh** |

## Ghi chú thiết kế

Docker trên Ubuntu **không** mua được nanosecond kiểu Equinix-to-broker; nó mua **khả năng chạy
liên tục mà không cần Windows**. Đừng viết requirement dựa trên giả định VPS làm giảm độ trễ khớp lệnh.
