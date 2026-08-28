---
type: operating-environment
status: draft
updated: 2026-08-28
links: ["[[system-overview]]"]
---

# Operating Environment

> Môi trường vận hành thật của sản phẩm — ràng buộc nền tảng mà mọi NFR và requirement phải tôn trọng.
> Nguồn: `README.md`, `plans/.../phase-01`, `phase-05`.

## Phía người chơi

| Hạng mục | Giá trị | Ghi chú |
|---|---|---|
| Nền tảng | **Chrome desktop** | Là web game, không phải app native |
| Tay cầm | **8BitDo Ultimate 2 Wireless** | |
| Kết nối tay cầm | **Dongle 2.4G** | Là đường chính |
| Dự phòng | USB có dây | |
| Bluetooth | **Không dùng** | Ultimate 2 cần macOS 26+ → loại trên máy hiện tại |
| Điều kiện phát lệnh | Cửa sổ Chrome phải **đang focus** | Order hot path đi qua app đang focus |

## Phía máy chủ

| Hạng mục | Giá trị |
|---|---|
| Hệ điều hành | **Ubuntu VPS** |
| Đóng gói | **Docker** |
| Giao thức client ↔ gateway | **WSS** (WebSocket secure) |
| Adapter sàn duy nhất | **cTrader Open API** |
| Matching engine | **Spotware** (không phải VPS) |
| Loại tài khoản | **Demo** — không có tiền thật |

## Ràng buộc phải nhớ khi viết requirement

1. **Chặng nhà → VPS (15–80 ms) là phần chiếm phần lớn độ trễ.** Không viết NFR giả định gateway
   ở gần sàn.
2. **Docker/Ubuntu mua "chạy liên tục không cần Windows", không mua tốc độ khớp lệnh.**
3. **AI không bao giờ được chặn một lệnh** — mọi tính năng AI phải chịu được việc bị bỏ qua.
4. **Mở GameOverlay huỷ ARM và khoá mở lệnh mới** — mọi luồng UI phải tính đến trạng thái này.
