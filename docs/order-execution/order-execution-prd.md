---
type: prd
feature: order-execution
status: draft
updated: 2026-08-28
links:
  - docs/order-execution/order-execution-urd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/ai-desk/ai-desk-urd.md
  - docs/playbook-grading/playbook-grading-urd.md
---

# order-execution — Product Requirements Document

## 1. Product Overview

`order-execution` là **đường đi nóng** của sản phẩm: nơi một ý định giao dịch rời tay cầm, qua gateway,
tới tài khoản demo cTrader. Mọi feature khác — bàn làm việc AI, chấm luật, nhật ký, chấm điểm, tua lại —
đứng **bên lề** nó và không feature nào được phép chạm vào nó.

Giá trị của feature này không nằm ở tốc độ vào lệnh. Nó nằm ở ba điều: **không bao giờ vào một lệnh
mình không chủ động quyết định**, **luôn biết chắc mình đang ở đâu**, và **luôn thoát ra được** kể cả khi
tay cầm hoặc kết nối đã hỏng.

**Gap neo:** Hiện tại người chơi giao dịch demo bằng chuột trên cTrader — một cú nhấp là một lệnh, không
có ma sát nào chặn cú nhấp bốc đồng, lãi lỗ bằng tiền luôn đập vào mắt, và việc **từ chối** một setup
không để lại dấu vết nào. Sau feature này: mỗi lệnh cần một lần xác nhận hai tay có chủ ý, trạng thái vị
thế đọc bằng đơn vị rủi ro (R) chứ không bằng tiền, và mỗi lần tự kiềm chế được đếm và hiển thị nổi bật
như một thành tích.

## 2. Goals

### 2.1 Goals

* **Không lệnh nào vào sàn mà người chơi không chủ động quyết định** — mỗi vị thế khớp đúng một lần xác
  nhận hai tay (trace UN-001, USC-001).
* **Không bao giờ có trạng thái mơ hồ về một lệnh** — người chơi luôn biết lệnh đã khớp, bị từ chối, hay
  chưa rõ; và "chưa rõ" là một trạng thái được nói ra, không phải một khoảng lặng (trace UN-002, USC-004).
* **Luôn thoát được vị thế trong vòng 10 giây**, kể cả khi tay cầm hết pin, dongle bị rút, tab mất focus
  hoặc mạng rớt (trace UN-003, USC-003).
* **Hạn mức do chính người chơi đặt lúc còn tỉnh được hệ thống thi hành thay** khi đầu không còn tỉnh
  (trace UN-004, UN-010, USC-005).
* **Sự tự kiềm chế được đếm và nhìn thấy** — số lần chủ động huỷ là con số lớn nhất trên màn hình sau giá
  (trace UN-006, USC-002).
* **Quy trình đứng trước tiền** — lãi lỗ hiển thị bằng đơn vị rủi ro làm mặc định (trace UN-005).

### 2.2 Non-goals

* **KHÔNG** giao dịch tiền thật. Chỉ tài khoản demo, ở mọi phiên bản.
* **KHÔNG** lệnh chờ (pending order) — chỉ lệnh thị trường.
* **KHÔNG** đóng một phần vị thế — đóng là đóng hết một vị thế.
* **KHÔNG** đo trạng thái tâm lý hay ma sát thích ứng → `tilt-meter`.
* **KHÔNG** nghi thức chuẩn bị trước phiên và tự chấm đầu/cuối buổi → `daily-journal`. Feature này chỉ
  nhận phần **hạn mức + khoá phiên**.
* **KHÔNG** cộng dồn số lần tự huỷ qua nhiều phiên → `process-score`. Feature này giữ bộ đếm **theo phiên**.
* **KHÔNG** chấm điểm lệnh theo luật playbook → `playbook-grading`. Feature này sở hữu màn xác nhận nhưng
  không sở hữu nội dung điểm hiện trên đó.
* **KHÔNG** tư vấn, tín hiệu, phân tích → `ai-desk`. **KHÔNG** ghi âm lý do vào lệnh → `voice-journal`.
* **KHÔNG** tua lại lệnh qua tape → `trade-replay`. **KHÔNG** báo cáo, xuất dữ liệu, sao lưu →
  `reports-export`.

## 3. Personas

| Persona | Mô tả (1 dòng) | Nhu cầu chính | Nguồn |
|---------|----------------|---------------|-------|
| Người chơi | Một buổi tối, một mình, tay cầm 8BitDo trong tay, tài khoản demo, không tiền thật | Ra được những quyết định mình tự hào vào sáng hôm sau — kể cả và nhất là quyết định *không* vào lệnh | URD Mục 2, UN-001, UN-006 |

> **Không có persona thứ hai.** AI desk và sàn cTrader/Spotware là **actor hệ thống**, không phải người
> dùng — xem `docs/_shared/project-profile.md`. Text canonical về persona sống ở URD Mục 2.

## 4. Capabilities

| ID | Capability | Priority | Rationale (vì sao tier này) | Traces to | Bóc ~N story | Done when (product outcome) | Sẵn sàng |
|----|------------|----------|-----------------------------|-----------|--------------|-----------------------------|----------|
| CAP-order-execution-01 | Phiên giao dịch có hạn mức do người chơi tự đặt | P0 | Không có phiên thì không có gì để giới hạn; hạn mức là chốt an toàn duy nhất người chơi tự dựng khi còn tỉnh | UN-004, UN-010 | ~8 | Người chơi mở được phiên và khai xong hạn mức thi hành cho buổi tối này | ✅ |
| CAP-order-execution-02 | Chuỗi vũ trang → bắn với chốt an toàn hai tay | P0 | Lõi giá trị feature — không có thì không tồn tại ma sát chống cú bấm bốc đồng | UN-001, UN-008 | ~10 | Một vị thế demo chỉ xuất hiện sau đúng một lần xác nhận hai tay của người chơi | ✅ |
| CAP-order-execution-03 | Trạng thái lệnh dứt khoát, kể cả khi chưa rõ kết quả | P0 | "Không biết mình có vị thế hay không" là trạng thái nguy hiểm nhất; im lặng ở đây là hỏng | UN-002 | ~7 | Người chơi luôn đọc được lệnh vừa rồi đã khớp, bị từ chối, hay chưa rõ | ✅ |
| CAP-order-execution-04 | Đường thoát không phụ thuộc tay cầm | P0 | Nghĩa vụ an toàn cao nhất; phải hoạt động cả khi mọi thứ khác đã hỏng | UN-003 | ~5 | Người chơi đóng được toàn bộ vị thế khi tay cầm hoặc kết nối đã hỏng | ✅ |
| CAP-order-execution-05 | Khoá và mở khoá phiên có chủ ý | P0 | Sau thoát khẩn cấp phải có trạng thái dừng; không có thì người chơi vào lại ngay lúc tệ nhất | UN-011 | ~5 | Người chơi hiểu mình đang bị khoá, ra khỏi khoá được, và hạn mức đã tiêu không đặt lại | ⚠️ chờ OQ-2 (độ nặng thao tác mở khoá) |
| CAP-order-execution-06 | Quản lý nhiều vị thế: chọn, đóng, báo kết thúc ngoài ý muốn | P0 | Hạn mức "số vị thế tối đa" ngụ ý > 1; tác động nhầm vị thế là lỗi không sửa được | UN-012, UN-013 | ~8 | Người chơi biết chắc mình đang tác động vào vị thế nào, và biết ngay khi một vị thế kết thúc mà mình không bấm | ✅ |
| CAP-order-execution-07 | Bộ đếm tự huỷ theo phiên | P0 | Đây là phản hồi tích cực duy nhất cho hành vi đúng nhất trong giao dịch; bỏ đi thì mất lý do tồn tại của sản phẩm | UN-006 | ~4 | Mỗi lần người chơi chủ động huỷ, bộ đếm tăng ngay và hiện nổi bật trên màn chính | ✅ |
| CAP-order-execution-08 | Trạng thái theo đơn vị R; tiền sau một thao tác có chủ ý | P0 | Chữ ký của sản phẩm — bỏ đi thì công cụ trở lại thành một giao diện broker khác | UN-005 | ~4 | Người chơi đọc được lãi lỗ bằng R mà không thấy con số tiền nào cho tới khi tự bật | ✅ |
| CAP-order-execution-09 | Menu an toàn không phát ra được lệnh | P0 | Hạ tầng dùng chung: playbook, deck, nhật ký, replay, báo cáo, cài đặt đều mount lên đây | UN-009 | ~5 | Người chơi mở menu giữa phiên mà không có khả năng vô tình mở một lệnh | ✅ |
| CAP-order-execution-10 | Chặn mở lệnh khi dữ liệu giá không còn đáng tin | P0 | Bắn theo một mức giá đã chết nguy hiểm hơn mất kết nối, vì nó trông vẫn bình thường | UN-002 | ~4 | Người chơi không bao giờ mở được một lệnh dựa trên giá đã cũ mà không biết | ✅ |
| CAP-order-execution-14 | **Vòng đệm giá và đóng băng bối cảnh quanh mỗi lệnh** | P0 | **Không backfill được**: không chạy từ phiên đầu thì mọi lệnh trước đó vĩnh viễn không có tape để tua. Và vòng đệm phải sống trên luồng giá của đường đặt lệnh — journal path bị cấm đi trên đó | `trade-replay` UN-014 | ~6 | Bối cảnh quanh mỗi lệnh có mặt tự động; **một buổi không lệnh nào thì không lưu gì cả** | ✅ *(nhận từ `trade-replay` 2026-08-29)* |
| CAP-order-execution-11 | Sửa mức bảo vệ qua bản xem trước + xác nhận hai tay | P1 | Vị thế đã có SL/TP lúc mở nên v1 sống được không có nó; nhưng thao tác chỉnh tay tự gửi đi là rủi ro thật | UN-007 | ~6 | Người chơi dời được SL/TP mà thao tác chỉnh không bao giờ tự tới sàn | ✅ |
| CAP-order-execution-12 | Chọn cặp / khối lượng / khung thời gian bằng tay cầm | P1 | Tiện lợi thuần — dựa trên A-06 chưa xác nhận; v1 chấp nhận đặt trước ngoài phiên | UN-008 | ~6 | Người chơi đổi cặp và khối lượng không phải rời tay sang chuột | ⚠️ dựa A-06 chưa xác nhận |
| CAP-order-execution-13 | Trần lỗ theo **ngày** đứng trên trần lỗ theo phiên | P2 | Chỉ cần khi người chơi thật sự chạy nhiều phiên một ngày; chưa biết điều đó có xảy ra không | UN-004 | ~3 | Mở phiên mới không còn là cách lách hạn mức lỗ đã chạm | 🔒 blocked by OQ-1 |

> **Cảnh báo altitude — P0 = 11 capability** *(thêm CAP-14 khi nhận quyền sở hữu tape 2026-08-29)*, **vượt ngưỡng 7.** Em **không** đề xuất tách feature. Lý do:
> mười capability này là các **bất biến an toàn của cùng một đường đi**, và mỗi cái chỉ đúng khi chín cái
> kia cùng đúng — bộ đếm tự huỷ vô nghĩa nếu không có chuỗi vũ trang; trạng thái khoá vô nghĩa nếu đường
> thoát không mở; chặn giá chết vô nghĩa nếu vẫn bắn được từ menu. Tách đôi đường đặt lệnh sẽ tạo ra hai
> nửa mà mỗi nửa không tự an toàn. Đánh đổi được chấp nhận có ý thức: **v1 của feature này lớn hơn v1
> thông thường**, và các feature khác chờ nó xong.

## 5. Upstream Traceability

| Capability | Traces to | Product outcome | Success metric |
|------------|-----------|-----------------|----------------|
| CAP-02, CAP-09, CAP-10 | UN-001, UN-008, UN-009, UN-002 | Không lệnh nào phát sinh ngoài ý muốn của người chơi | M1 Lệnh ngoài ý muốn |
| CAP-07 | UN-006 | Sự tự kiềm chế được ghi nhận như một thành tích | M2 Tỷ lệ tự kiềm chế |
| CAP-04, CAP-05 | UN-003, UN-011 | Người chơi luôn thoát được, kể cả khi thiết bị hỏng | M3 Thoát thành công khi sự cố |
| CAP-03, CAP-06 | UN-002, UN-012, UN-013 | Không bao giờ hoang mang về trạng thái lệnh của mình | M4 Lần kiểm tra chéo ngoài kế hoạch |
| CAP-01, CAP-13 | UN-004, UN-010 | Hạn mức tự đặt thực sự được thi hành | M5 Lệnh vượt hạn mức |
| CAP-08 | UN-005 | Quyết định bị luật dẫn dắt thay vì bị tiền dẫn dắt | — (không đo trực tiếp; xem ghi chú Mục 7) |
| CAP-11 | UN-007 | Sửa bảo vệ mà không sợ thao tác chỉnh tự gửi đi | — (kiểm bằng checkpoint J6, không phải metric xu hướng) |
| CAP-12 | UN-008 | Trọn bộ thao tác một phiên làm được trên tay cầm | — (phụ thuộc A-06) |

## 6. Key Capability Interactions

* **Vào một lệnh:** CAP-01 (phiên mở, hạn mức đã khai) là tiền đề của CAP-02; CAP-02 gọi CAP-10 (giá còn
  tươi?) và luật hạn mức của CAP-01 trước khi cho ARM; bắn xong chuyển sang CAP-03 (chờ kết quả). Nội dung
  điểm luật trên màn xác nhận do `playbook-grading` cấp — màn xác nhận **không mở ra khi chưa có điểm**.
* **Từ chối một setup:** CAP-02 (đang ARM) → người chơi chủ động huỷ → CAP-07 tăng bộ đếm. Huỷ **bị động**
  (mất pad, mất focus, mở CAP-09) **không** đi qua CAP-07.
* **Thoát khẩn cấp:** CAP-04 chạy độc lập với CAP-02 và không bao giờ bị CAP-01, CAP-05, CAP-09 hay
  `tilt-meter` chặn; xong thì chuyển sang CAP-05 (khoá phiên).
* **Sửa bảo vệ:** CAP-09 (mở menu → huỷ ARM, khoá mở lệnh) → CAP-06 (chọn vị thế) → CAP-11 (dàn bản xem
  trước) → quay lại màn chính → CAP-02 mượn lại chuỗi xác nhận hai tay để gửi đi.
* **Mất kết nối:** CAP-10 và CAP-03 cùng khoá việc mở lệnh mới; CAP-04 vẫn mở. Khi nối lại, CAP-03 đối
  chiếu trạng thái thật với sàn rồi CAP-06 cập nhật danh sách vị thế.
* **Ranh giới với feature khác:** `tilt-meter` **thêm ma sát** lên CAP-02 nhưng không bao giờ chạm CAP-04;
  `ai-desk` chỉ đọc, không có đường nào phát ra lệnh; `daily-journal` áp cỡ lệnh vào bản xem trước của
  CAP-02 nhưng vẫn cần xác nhận hai tay.

## 7. Success Metrics

| Metric | Baseline | Target | Measurement Method | Timeframe |
|--------|----------|--------|--------------------|-----------|
| M1 Lệnh ngoài ý muốn | Chưa có — xác lập từ 10 phiên đầu | 0 lệnh / tháng | Đối chiếu số lệnh trên cTrader demo với **số lần xác nhận hai tay do sản phẩm ghi lại**; mỗi lệnh phải khớp đúng một lần xác nhận | Hằng tháng |
| M2 Tỷ lệ tự kiềm chế | Chưa có — xác lập tỷ lệ trung bình từ 10 phiên đầu | Cao hơn baseline sau 3 tháng, **đồng thời** tổng số lần vũ trang mỗi phiên không tăng bất thường | Số lần huỷ chủ động ÷ số lần vũ trang, đọc cuối mỗi phiên. Dùng tỷ lệ thay số tuyệt đối để không thưởng cho việc vũ trang bừa rồi huỷ lấy điểm | Hằng quý |
| M3 Thoát thành công khi sự cố | Chưa có — chưa có sản phẩm để đo | 100% lần thử, trong vòng 10 giây kể từ lúc quyết định thoát | Diễn tập có chủ ý mỗi tháng: rút dongle / ẩn tab / ngắt mạng khi đang có vị thế, rồi bấm thoát và bấm giờ | Hằng tháng |
| M4 Lần kiểm tra chéo ngoài kế hoạch | Chưa có — chưa có sản phẩm để đo | 0 lần phải mở cTrader ở nơi khác **vì hoang mang không biết lệnh có tồn tại không** | Người chơi ghi nhận mỗi lần đi kiểm tra chéo ngoài kế hoạch, cuối mỗi phiên. Diễn tập M3 và checkpoint của URD Mục 5 không tính | Hằng tháng |
| M5 Lệnh vượt hạn mức | Chưa có — chưa có sản phẩm để đo | 0 lệnh mở ngoài khung giờ đã khai hoặc sau khi chạm mức lỗ tối đa của phiên | Đối chiếu dấu thời gian từng lệnh trên cTrader demo với khung giờ và hạn mức đã khai cho phiên đó | Hằng tháng |

> **CAP-08 (hiển thị theo R) cố ý không có metric xu hướng.** Nó là một ràng buộc nhị phân — hoặc màn hình
> có con số tiền trước một thao tác bật, hoặc không. Kiểm bằng cách rà màn hình mỗi lần đổi giao diện, cùng
> cách `process-score` kiểm ràng buộc tương đương của deck.
>
> **M1 và M4 dùng chung một lần kiểm toán vị thế với `ai-desk` USC-002** — một lần đối chiếu, ba câu hỏi
> khác nhau — để ba thước đo không ra kết quả lệch nhau.

## 8. Dependencies

| Dependency | Owner | Status | Needed-by | Impact if Late |
|------------|-------|--------|-----------|----------------|
| Tài khoản demo cTrader hoạt động, phiên đăng nhập còn hạn | Người chơi (qua Spotware) | On Track | Trước phiên đầu tiên | Chặn toàn bộ feature — không có sàn thì không có gì để đặt lệnh |
| Tay cầm 8BitDo Ultimate 2 + dongle 2.4G (dây USB dự phòng) | Người chơi | On Track | Trước phiên đầu tiên | Chặn CAP-02, CAP-12; CAP-04 vẫn phải chạy được không cần nó |
| Màn tua lại đọc tape do feature này sinh ra | `trade-replay` | On Track | Sau CAP-14 | **Không blocks** — tape vẫn tích luỹ dù `trade-replay` chưa ship; đó chính là lý do chuyển quyền sở hữu |
| Nội dung điểm luật trên màn xác nhận | `playbook-grading` | At Risk | Cùng lúc CAP-02 | Màn xác nhận **không mở ra khi chưa có điểm** — thiếu nguồn này thì phải chốt hành vi thay thế trước khi CAP-02 dùng được |
| **Điện thoại chạy cTrader mobile** để kiểm chứng độc lập | Người chơi | **On Track** (chốt 2026-08-29) | Trước lần đo M1 đầu tiên | Không có thì M1, M3, M4 lùi về profile trình duyệt thứ hai và số đo bị đánh dấu **"đo yếu"** |
| Quyết định trần lỗ theo ngày (OQ-1) | Người chơi | Blocked | Trước khi CAP-13 vào Now | CAP-13 không bắt đầu được; trong lúc chờ, mở phiên mới vẫn là đường lách hạn mức lỗ |

> Ràng buộc **kỹ thuật** (WSS client↔gateway, cTrader Open API là adapter sàn duy nhất, Docker/Ubuntu VPS,
> ngân sách độ trễ nhà→VPS 15–80 ms) đã **chuyển sang SRS Mục 4 (NFR) và Mục 11** theo đúng ranh giới tầng
> — chúng không phải business dependency và không thuộc PRD.

## 9. Assumptions & Validation

| Assumption | Impact if Wrong | Validation | Status |
|------------|-----------------|------------|--------|
| Danh sách cặp (XAUUSD, EURUSD, GBPUSD, USDJPY) người chơi sửa được trong Settings | CAP-12 hẹp lại, mất một nhu cầu tuỳ biến | Hỏi người chơi khi viết SRS chi tiết màn Settings | Open (URD A-01) |
| "Luôn thoát được" nghĩa là đóng được vị thế **không cần tay cầm** | CAP-04 không thoả UN-003 — nghĩa vụ an toàn cao nhất của feature | Xác nhận khi thiết kế màn hình chính | Open (URD A-02) |
| Một phiên = một buổi tối, một phiên mỗi ngày; hạn mức lỗ gắn với **phiên**, không cộng dồn theo ngày lịch | Chạy nhiều phiên một ngày thì mở phiên mới là cách lách hạn mức lỗ | Chốt số phiên tối đa mỗi ngày cùng OQ-1 | Open (URD A-04 → OQ-1) |
| Thao tác chuột trên nhiều cửa sổ làm đứt nhịp quan sát, nên "không rời tay khỏi tay cầm" là nhu cầu thật | Phần tiện lợi thuần của CAP-12 mất cơ sở và nên hạ xuống P2 | Hỏi người chơi trước khi chốt phạm vi bản đồ nút | Open (URD A-06) |
| Người chơi mở được cTrader demo trên **điện thoại** để kiểm chứng | M1, M3, M4 và mọi checkpoint URD Mục 5 mất khả năng kiểm chứng | Đã chốt: điện thoại chạy cTrader mobile | **Confirmed** 2026-08-29 |
| Người chơi chấp nhận đánh đổi độ trễ đường truyền để lấy khả năng chạy liên tục | Cả kiến trúc máy chủ từ xa bị đặt lại vấn đề | Đã quan sát: `README.md` nêu rõ đây là đánh đổi có chủ ý | Confirmed |
| Người chơi chơi một mình, không có ai xem cùng hoặc review realtime | Personas thiếu một tier | Xác nhận với người chơi | Open (URD A-03) |

## 10. Product Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Chuỗi xác nhận hai tay bị cảm nhận là phiền sau vài tuần, người chơi tìm cách đi tắt | Medium | High | Giữ ma sát ở đúng một chỗ (mở lệnh) và tuyệt đối không đặt thêm ma sát lên đóng/thoát; đọc M2 cùng tổng số lần vũ trang để phát hiện sớm | Người chơi |
| Trạng thái "chưa rõ" xuất hiện thường xuyên vì độ trễ nhà→VPS, khiến việc bỏ qua thành thói quen | Medium | High | Mỗi lần bỏ qua đều phải đọc cảnh báo nêu rõ rủi ro hai vị thế; đếm số lần bỏ qua mỗi phiên và đọc cùng M4 | Người chơi |
| Không có trần lỗ theo ngày (OQ-1 chưa chốt) → mở phiên mới là đường lách hạn mức lỗ | High | High | Trong lúc chờ OQ-5, hiển thị rõ đây là phiên thứ mấy trong ngày và tổng lỗ các phiên đã chạy, để việc lách trở nên nhìn thấy được | Người chơi |
| Điện thoại không sẵn lúc cần đo → lùi về profile trình duyệt thứ hai, số đo yếu đi | Low | Medium | Đã chốt điện thoại (2026-08-29). Khi phải lùi thì **đánh dấu số đo là "đo yếu"**, không báo cáo như số thật | Người chơi |
| Mở khoá phiên chỉ tốn một cú bấm (OQ-2) → trạng thái khoá mất sức răn đe | Medium | Medium | Chốt OQ-2 trước khi CAP-05 vào Now; mặc định tạm là thao tác có chủ ý hơn một cú tap | Người chơi |
| `playbook-grading` trượt lịch → màn xác nhận thiếu nguồn điểm | Medium | Medium | Chốt hành vi thay thế trước khi CAP-02 dùng được: màn xác nhận mở bình thường và đọc là "chưa có playbook" thay vì chặn | Người chơi |

## 11. Release & Launch Readiness

### 11.1 Release Horizon

| Horizon | Capabilities | Target | Status |
|---------|--------------|--------|--------|
| Now | CAP-order-execution-01 → 10 (P0) | Chưa chốt lịch | planned |
| Next | CAP-order-execution-11, 12 (P1) | Chưa chốt lịch | planned |
| Later | CAP-order-execution-13 (P2) | Chưa chốt lịch | blocked by OQ-1 |

> **Chưa có ngày phát hành nào được chốt.** Dự án đang ở giai đoạn tài liệu, chưa viết code ứng dụng
> (`docs/_shared/project-profile.md`). Ba dòng trên giữ đúng **thứ tự**, không giả định lịch.

### 11.2 Launch Readiness

Feature này không có team vận hành, không có khách hàng và không có ngày go-live — nên các workstream
dưới đây là **diễn tập tự kiểm của người chơi**, không phải checklist bàn giao.

| Workstream | Must-pass criteria | Status | Guardrail metric (threshold → decision) |
|------------|--------------------|--------|-----------------------------------------|
| An toàn — đường thoát | Diễn tập rút dongle / ẩn tab / ngắt mạng khi đang có vị thế, thoát thành công cả ba lần | ⬜ | Bất kỳ lần thoát nào thất bại hoặc quá 10 giây → dừng dùng sản phẩm để giao dịch cho tới khi sửa xong |
| An toàn — không lệnh ngoài ý muốn | Đối chiếu số lệnh cTrader với số lần xác nhận hai tay, khớp tuyệt đối qua 10 phiên đầu | ⬜ | Một lệnh lệch → sự cố nghiêm trọng, điều tra ngay trước khi chạy phiên tiếp |
| Hạn mức | Thử mở lệnh ngoài khung giờ và sau khi chạm lỗ tối đa, cả hai bị từ chối; đóng vị thế vẫn được phép | ⬜ | Một lệnh lọt qua hạn mức → tắt việc mở lệnh cho tới khi sửa xong |
| Bộ đếm tự huỷ | Huỷ chủ động tăng bộ đếm; rút dongle khi đang ARM **không** tăng | ⬜ | Bộ đếm tăng sai → tạm bỏ con số khỏi màn hình, vì một bộ đếm sai còn tệ hơn không có |
| Kiểm chứng độc lập | **Điện thoại mở được cTrader demo cùng tài khoản** (chốt 2026-08-29) | ⬜ | Điện thoại không dùng được → lùi profile thứ hai và **đánh dấu "đo yếu"**, không báo cáo như số thật |

## 12. Open Questions

* [ ] OQ-1 *(kế thừa URD OQ-5)*: Một ngày chạy được tối đa mấy phiên, và có trần lỗ theo **ngày** đứng
  trên trần lỗ theo **phiên** không? Không có trần ngày thì mở phiên mới là cách lách hạn mức lỗ.
  **Chặn CAP-13.**
* [ ] OQ-2 *(kế thừa URD OQ-6)*: Mở khoá phiên sau khi thoát khẩn cấp cần thao tác nặng tới đâu — một cú
  tap, hay một bước có chủ ý hơn? Một tap thì trạng thái khoá gần như không có sức răn đe.
  **Chặn CAP-05 vào Now.**
* [x] OQ-3 *(kế thừa URD OQ-7)*: Người chơi kiểm chứng độc lập bằng thiết bị nào?
  **Resolved 2026-08-29: điện thoại chạy cTrader mobile** — không đụng ràng buộc giữ Chrome focus, và độc
  lập thật (khác thiết bị, khác đường mạng). **M1, M3, M4 đo được ngay từ phiên đầu.**

* [ ] OQ-4: `playbook-grading` chưa có thì màn xác nhận xử sự thế nào? URD của nó nói màn xác nhận
  **không mở ra khi chưa có điểm** — nhưng ở giai đoạn `order-execution` chạy một mình thì luật đó khoá
  chết chuỗi vũ trang. 🔶 **Tạm quyết:** chưa có nguồn điểm thì màn xác nhận mở bình thường và đọc là
  "chưa có playbook"; luật "không mở khi chưa có điểm" chỉ áp khi `playbook-grading` đã tồn tại.
  *Nếu sai:* CAP-02 phải chờ `playbook-grading` xong mới dùng được, và thứ tự phát hành đảo lại.
* [ ] OQ-5: Danh sách cặp giao dịch cố định hay sửa được trong Settings? Ảnh hưởng phạm vi CAP-12.
  Xem Assumption URD A-01.

---

> **Nguồn:** `docs/order-execution/order-execution-urd.md` (13 nhu cầu, 6 journey, 5 thước đo thành công,
> 7 giả định, 3 câu hỏi mở) cộng bốn tài liệu nền `docs/_shared/`. **Chưa có BRD** cho feature này, nên
> mọi capability trace tới `UN-*`; không có `BO-*` nào để phủ.
>
> **🔶 Quyết định thay user trong bản này:** (1) giữ 10 capability ở P0 thay vì tách feature — lý do ghi
> ở cuối Mục 4; (2) hành vi thay thế của màn xác nhận khi chưa có `playbook-grading` — ghi ở OQ-4;
> (3) đổi Launch Readiness từ khung team sang khung diễn tập tự kiểm — Mục 11.2.
