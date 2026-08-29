---
type: prd
feature: trade-replay
status: draft
updated: 2026-08-29
links:
  - docs/trade-replay/trade-replay-urd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/srs/order-execution-spec.md
  - docs/playbook-grading/srs/playbook-grading-spec.md
  - docs/voice-journal/srs/voice-journal-spec.md
  - docs/daily-journal/srs/daily-journal-spec.md
---

# trade-replay — Product Requirements Document

## 1. Product Overview

`trade-replay` **biến một vị thế đã đóng thành một bài học**: tua lại chính lệnh của mình qua bối cảnh thị
trường lúc đó, bằng đúng cây cần analog đã dùng để vào lệnh.

Feature này nằm hoàn toàn trên đường học hỏi, chậm nhất trong ba đường của hệ thống, và **không bao giờ đặt
được một lệnh**. Điều làm nó thành **huấn luyện** chứ không phải xem biểu đồ chính là **dải sự kiện**: lần vũ
trang đã huỷ, lần bắn, lần dời mức bảo vệ, câu nói lúc đó, và mức tâm lý đang ở đâu.

**Gap neo:** Hiện tại lệnh đóng xong chỉ còn lại con số lãi lỗ trong lịch sử tài khoản — bối cảnh biến mất
cùng lúc với vị thế. Những lần vũ trang rồi tự huỷ, thứ chiếm phần lớn một buổi tối tốt, không để lại dấu
vết nào ngoài một con số đếm. Và công cụ hiện có tua lại lệnh **bằng chuột trên một màn hình khác** — thành
một việc hành chính phải nhớ mới làm. Sau feature này: tua lại ngay trên phần cứng đã giao dịch, và **lần
đứng ngoài nằm trong bản ghi như một sự kiện, không phải như một khoảng trống trong đó**.

## 2. Goals

### 2.1 Goals

* **Thấy lại quyết định của mình đúng thứ tự nó đã xảy ra — cả những quyết định không dẫn tới lệnh nào**
  (trace UN-003, UN-011).
* **Không lệnh nào phát ra được từ màn xem lại**, nhưng **đường thoát không bao giờ bị khoá** (trace UN-002).
* **Xem lại trở thành thói quen thật**, không phải tính năng dùng một lần rồi quên (trace USC-001).
* **Xem lại diễn ra khi bối cảnh còn nóng**, không phải khi đã quên hết (trace USC-002).
* **Điều rút ra được nói thành lời tại đúng chỗ vừa nhận ra nó** (trace UN-008, USC-003).
* **Lệnh cũ không còn bối cảnh vẫn mở ra được** — không bao giờ trắng màn, không bao giờ báo lỗi (trace
  UN-006).

### 2.2 Non-goals

* **KHÔNG** ghi âm và chuyển lời nói thành văn bản → `voice-journal`. Feature này chỉ nhận việc **phát lại**
  memo đúng thời điểm, và **nhu cầu** ghi thêm một memo lúc xem lại.
* **KHÔNG** nội dung chấm luật playbook → `playbook-grading`. Chỉ nhận việc **đặt kết quả đó cạnh dòng thời
  gian**.
* **KHÔNG** tính điểm quy trình → `process-score`. Chỉ nhận **ranh giới**: mở màn replay là đủ để trục Review
  tính, nên feature này **không được đặt thêm điều kiện nào** lên việc đó.
* **KHÔNG** bảng lịch sử lệnh, bản đồ nhiệt, chi tiết một ngày → `daily-journal`. Đó là các **đường vào** dẫn
  tới replay, không phải replay.
* **KHÔNG** so sánh thực tế với kế hoạch và xu hướng lỗi → `execution-learning` *(chưa có URD)*.
  **KHÔNG** so sánh nhiều lệnh với nhau, thống kê theo playbook → `process-score`. **Replay xem một lệnh tại
  một thời điểm.** **KHÔNG** nguyên tắc cá nhân → `daily-journal`.
* **KHÔNG** đo trạng thái tâm lý → `tilt-meter`. Chỉ **hiện lại** mức đã ghi như một sự kiện trên dải thời
  gian.
* **KHÔNG** tư vấn, tín hiệu, phân tích → `ai-desk`. Tín hiệu đã sinh ra lúc đó hiện lại như sự kiện;
  **không có diễn giải mới nào được tạo ra lúc xem lại**.
* **KHÔNG** sao lưu, xuất dữ liệu, xoá toàn bộ → `reports-export`.
* **KHÔNG lưu bối cảnh cho một lần đứng ngoài không dẫn tới lệnh nào** *(chốt 2026-08-28)*. Lần tự huỷ chỉ
  hiện lại khi nó rơi vào cửa sổ quanh một lệnh có thật.
* **KHÔNG** tua lại **cả buổi tối như một dòng liên tục** — replay đi theo từng lệnh, không theo phiên.
* **KHÔNG** mô phỏng "nếu lúc đó tôi làm khác thì sao". Bối cảnh đã lưu là **dữ liệu quá khứ**, không phải mô
  phỏng.

## 3. Personas

| Persona | Mô tả (1 dòng) | Nhu cầu chính | Nguồn |
|---------|----------------|---------------|-------|
| Người chơi | Trước Chrome desktop, **tay cầm trong tay** — ngay sau khi một lệnh vừa đóng, giữa phiên, hoặc sau khi đã đóng phiên | Nhìn lại một lệnh đủ rõ để rút ra được điều gì đó, **mà không phải rời tay cầm và không phải đọc bảng số** | URD Mục 2, UN-001, UN-011 |

> **Không có persona thứ hai.** **AI desk không tham gia vào việc xem lại** — replay **dựng lại sự kiện đã
> ghi, không diễn giải chúng**. Sàn cTrader/Spotware chỉ là nguồn của dữ liệu giá đã lưu.

## 4. Capabilities

| ID | Capability | Priority | Rationale (vì sao tier này) | Traces to | Bóc ~N story | Done when (product outcome) | Sẵn sàng |
|----|------------|----------|-----------------------------|-----------|--------------|-----------------------------|----------|
| CAP-trade-replay-01 | Ranh giới: không lệnh nào phát ra từ màn xem lại, nhưng **đường thoát không bị khoá** | P0 | Rủi ro lớn nhất là một lệnh thật bay ra từ màn ôn tập. Nhưng khoá cả đường thoát còn nguy hiểm hơn nhiều — người chơi đang ôm vị thế bị kẹt | UN-002 | ~4 | Bị khoá: **mở lệnh mới và sửa mức bảo vệ**. Không bị khoá: **đóng một vị thế đã chọn, và thoát khẩn cấp** | ✅ |
| ~~CAP-trade-replay-02~~ | ~~Tự đóng băng bối cảnh quanh mỗi lệnh~~ | — | **Chuyển sang `order-execution` CAP-14 (2026-08-29).** Feature này **chỉ đọc** tape | — | — | — | ➡️ đã chuyển |
| CAP-trade-replay-03 | Tua tới lui bằng cần analog, đổi độ rộng khung nhìn, phát/dừng/đổi tốc độ | P0 | Lõi thao tác. Và "trên phần cứng đã giao dịch" chính là điều tách feature này khỏi công cụ benchmark | UN-001 | ~8 | Đầu phát **bám theo tay không có độ trễ nhận ra được**, và **không vị trí nào trong cửa sổ phải chờ tải** | ✅ |
| CAP-trade-replay-04 | Dải sự kiện đúng thứ tự, **mỗi sự kiện đọc được là gì** | P0 | **Đây là thứ làm nó thành huấn luyện chứ không phải xem biểu đồ.** Bỏ nó đi thì còn lại một cái chart viewer | UN-011, UN-003 | ~7 | Người chơi tua tới một sự kiện và **đọc được nó là gì** — không chỉ thấy có một dấu ở đó | ✅ |
| CAP-trade-replay-05 | Điểm vào, điểm ra, và hai mốc giá đi xa nhất **đúng chiều lệnh** | P0 | Đo lẫn chiều là một lỗi **âm thầm** — hình vẫn đẹp, số vẫn có, chỉ là sai | UN-004, UN-013 | ~5 | Cả hai mốc hiện đúng thời điểm chạm, đo đúng chiều; **điểm vào lấy từ bản ghi lệnh, không suy ra từ biểu đồ** | ✅ |
| CAP-trade-replay-06 | Lệnh không còn bối cảnh vẫn mở ra được, **không bao giờ trắng màn** | P0 | Lệnh cũ hơn ngày bắt đầu lưu là chuyện chắc chắn xảy ra; gặp màn hỏng ở đây là mất lòng tin vào cả feature | UN-006 | ~4 | Bản rút gọn dựng từ bản ghi lệnh, và **nói rõ bối cảnh không còn** — đọc **khác hẳn** trạng thái "đang thu nốt" | ✅ |
| CAP-trade-replay-07 | Mở replay **bất cứ lúc nào**, kể cả đang có vị thế mở | P0 | Xem lại khi bối cảnh còn nóng là chính điều USC-002 đặt cược; bắt chờ hết phiên là giết thói quen | UN-010 | ~3 | Vào thẳng, **không phải xác nhận thêm bước nào**; một dòng thông báo nói rõ đang khoá gì và **cái gì vẫn dùng được** | ✅ |
| CAP-trade-replay-08 | Nghe lại memo **đúng khoảnh khắc đã nói** | P1 | URD xếp nhu cầu này **Critical**, nhưng nó phụ thuộc hoàn toàn `voice-journal`; và giá trị lõi của replay (thấy chuỗi quyết định) đứng vững không có nó | UN-005 | ~5 | Nghe được lời mình rồi nhìn giá lúc đó — cách đối chiếu **suy nghĩ với thực tế** | ⚠️ phụ thuộc `voice-journal` |
| CAP-trade-replay-09 | Kết quả chấm luật của lệnh này **trên cùng màn hình** | P1 | Bỏ đi thì người chơi phải mở nơi khác rồi ghép lại bằng trí nhớ; nhưng replay vẫn dùng được | UN-007 | ~3 | Luật nào đạt, luật nào không, nằm cùng màn với dòng thời gian | ⚠️ phụ thuộc `playbook-grading` |
| CAP-trade-replay-10 | Chuyển lệnh trước/sau **trong cùng phiên** | P1 | Tiện lợi thật khi đi hết một buổi, nhưng quay ra danh sách vẫn làm được | UN-009 | ~3 | Sang được lệnh liền trước/sau **của cùng phiên** — theo định nghĩa phiên, không phải ngày lịch | ✅ |
| CAP-trade-replay-11 | Ghi một memo mới **ngay trong lúc xem lại** | P1 | Là cơ chế duy nhất biến "xem lại" thành "rút ra được điều gì đó"; nhưng phụ thuộc `voice-journal` | UN-008 | ~4 | Memo mới gắn vào **lệnh đang xem**, phân biệt rõ với memo ghi lúc vào lệnh — một cái là **lý do**, một cái là **bài học** | ⚠️ phụ thuộc `voice-journal` |
| CAP-trade-replay-12 | Ghi nhận mỗi lần mở xem lại: **lệnh nào, lúc nào** | P1 | **Không ai khác ghi bản ghi này** — `process-score` chỉ lưu ở mức phiên. Thiếu nó thì cả ba thước đo của feature không đo được | UN-012 | ~2 | Ba thước đo đọc được từ bản ghi do chính feature này tạo ra | ✅ |
| CAP-trade-replay-13 | Mở thẳng màn xem lại **từ thông báo lệnh vừa đóng** | P2 | **Đây là đường vào nóng nhất, đúng đường USC-002 đặt cược** — nhưng nội dung thông báo do feature khác sở hữu | URD Mục 3 | ~2 | Người chơi mở lệnh vừa đóng **không phải đi vòng qua danh sách** | 🔒 blocked by OQ-4 |

> **Sáu P0** *(sau khi CAP-02 chuyển sang `order-execution` 2026-08-29)*. Câu hỏi phạm vi lớn nhất của
> feature đã được giải: việc đóng băng bối cảnh thuộc `order-execution`, nên đây là **màn đọc dữ liệu có
> sẵn** (~35 story), **không phải** màn đọc cộng một hạ tầng ghi chạy nền (~42 story). Hệ quả quan trọng
> hơn con số: **tape tích luỹ từ phiên đầu tiên**, nên replay ra mắt với lịch sử đầy đủ để xem ngay thay vì
> một màn rỗng.

## 5. Upstream Traceability

| Capability | Traces to | Product outcome | Success metric |
|------------|-----------|-----------------|----------------|
| CAP-01 | UN-002 | Không lệnh nào bay ra từ màn ôn tập, và không ai bị kẹt trong đó | — (ranh giới nhị phân, kiểm bằng checkpoint J2 + J8) |
| CAP-02, CAP-03 | UN-014, UN-001 | Tua lại được chính lệnh của mình qua bối cảnh lúc đó | M1 Tỷ lệ lệnh được xem lại |
| CAP-04 | UN-011, UN-003 | **Lần đứng ngoài nằm trong bản ghi như một sự kiện, không phải khoảng trống** | M1 |
| CAP-05 | UN-004, UN-013 | Biết giá đã đi xa tới đâu về hai phía, đo đúng chiều | — (kiểm bằng checkpoint J1, hai chiều lệnh) |
| CAP-06 | UN-006 | Lệnh cũ vẫn mở ra được, không bao giờ gặp màn hỏng | — |
| CAP-07 | UN-010 | Xem lại khi bối cảnh còn nóng | M2 Khoảng cách tới lần xem đầu |
| CAP-08, CAP-11 | UN-005, UN-008 | Đối chiếu suy nghĩ với thực tế, và nói ra điều rút ra | M3 Lệnh có memo lúc xem lại |
| CAP-09, CAP-10 | UN-007, UN-009 | Hiểu vì sao vào lệnh mà không nhảy file; đi hết một phiên không phải quay ra | — |
| CAP-12 | UN-012 | Ba thước đo có nguồn số | M1, M2, M3 (nguồn) |
| CAP-13 | URD Mục 3 | Đường vào nóng nhất, không phải đi vòng | M2 |

## 6. Key Capability Interactions

* **Sau khi một lệnh đóng:** `order-execution` báo lệnh kết thúc → CAP-13 dẫn thẳng sang → CAP-02 có thể
  **chưa thu xong phần sau lúc đóng**, nên CAP-06 phải phân biệt rõ **"đang thu nốt"** với **"bối cảnh không
  còn"** — hai thông điệp khác hẳn nhau.
* **Trong màn xem lại:** CAP-03 (tua) chạy trên bối cảnh của CAP-02; CAP-04 (dải sự kiện) và CAP-05 (mốc
  giá) vẽ đè lên; CAP-09 đặt điểm luật cạnh; CAP-08 phát memo theo đầu phát.
* **Ghi memo lúc xem lại:** CAP-11 dùng **chính cơ chế ghi âm** của `voice-journal`, chỉ khác đích — **lệnh
  đang xem**, ghi đè luật "gắn vào vị thế đang mở". Đây là ngoại lệ có chủ ý, đã cascade sang
  `voice-journal` FR-021.
* **Thoát khẩn cấp giữa lúc xem lại:** CAP-01 cho phép đi thẳng → đóng vị thế **và thoát luôn khỏi màn xem
  lại** về màn chính, để người chơi tự mắt xác nhận mọi thứ đã phẳng.
* **Ranh giới ra ngoài:** `daily-journal` là **đường vào** (lịch sử, chi tiết một lệnh); `process-score` đọc
  bản ghi của CAP-12 ở **mức phiên** (có ít nhất một lần mở) trong khi CAP-12 ghi ở **mức từng lệnh** — hai
  mức khác nhau nhưng **không mâu thuẫn**; `tilt-meter` cấp sự kiện đổi mức cho CAP-04.

## 7. Success Metrics

| Metric | Baseline | Target | Measurement Method | Timeframe |
|--------|----------|--------|--------------------|-----------|
| M1 Tỷ lệ lệnh được xem lại | Chưa có — xác lập từ 10 phiên đầu, **và ghi nhận rằng giai đoạn này là lúc mới lạ nên tỷ lệ tự nhiên cao** | **Không giảm dần theo tháng**, và sau 3 tháng vẫn ở mức người chơi thấy đáng giữ. **Chưa có sàn tối thiểu tuyệt đối** — xem OQ-2 | Đếm số lệnh đã được mở xem lại trên tổng số lệnh đã đóng, đọc cuối tháng **theo đường xu hướng nhiều tháng**, không so đúng một mốc | Hằng quý |
| M2 Khoảng cách tới lần xem đầu | Chưa có — xác lập khoảng cách trung vị từ 10 phiên đầu | Khoảng cách từ lúc lệnh đóng tới lần xem lại đầu tiên **giảm** so với baseline sau 3 tháng | Đọc trung vị khoảng cách đó cuối tháng. **Đi kèm thời lượng xem trung vị** để việc mở rồi thoát ngay không tự động thành "tiến bộ" | Hằng quý |
| M3 Lệnh có memo lúc xem lại | Chưa có — xác lập từ 10 phiên đầu, **chấp nhận rất có thể bằng 0** | Số lệnh có ít nhất một memo thuộc loại "ghi lúc xem lại" **tăng** so với baseline sau 3 tháng | Đếm số lệnh có memo loại đó, đọc cuối mỗi tháng | Hằng quý |

> **Cả ba thước đo có một sàn cứng không tránh được:** một lệnh chỉ tua lại được **sau khi phần sau lúc đóng
> thu xong** (khoảng 5 phút). M2 không bao giờ xuống dưới mốc đó — đó là **giới hạn của thiết kế, không phải
> của thói quen người chơi**.
>
> **Cả ba đọc từ bản ghi do chính feature này tạo ra** (CAP-12) nhưng **được tổng hợp thành xu hướng ở
> `daily-journal` và `process-score`** — feature này không tự đọc dữ liệu của mình thành xu hướng.
>
> **Giới hạn đã biết.** Ba thước đo đo **việc xem lại có diễn ra hay không**, không đo **việc xem lại có làm
> người chơi giao dịch tốt hơn hay không**. Điều thứ hai chỉ đọc được qua điểm quy trình, và ngay cả ở đó
> cũng khó tách phần đóng góp của riêng replay. Đây là **giới hạn chấp nhận được** của một công cụ cá nhân.
>
> **CAP-01 và CAP-05 cố ý không có metric** — chúng là ranh giới và tính đúng đắn, kiểm bằng checkpoint chứ
> không bằng xu hướng.

## 8. Dependencies

| Dependency | Owner | Status | Needed-by | Impact if Late |
|------------|-------|--------|-----------|----------------|
| **Tape + trạng thái thu** (thay cho CAP-02 cũ) | `order-execution` (CAP-14) | On Track | Cùng lúc CAP-03 | **Tape tích luỹ từ phiên đầu nên không blocks lịch ra mắt** — đó chính là lý do chuyển quyền sở hữu |
| Bản ghi lệnh (giá vào, giá ra, khối lượng, `cid`) | `order-execution` | On Track | Cùng lúc CAP-05, CAP-06 | Không có "sự thật" để vẽ mốc; CAP-06 không dựng được bản rút gọn |
| Định nghĩa **phiên** (kể cả khi vắt qua nửa đêm) | `order-execution` (FR-007) | On Track | Cùng lúc CAP-10 | Chuyển lệnh trước/sau cắt theo ngày lịch — sai ranh giới |
| Đường thoát để **không** khoá | `order-execution` (FR-029) | On Track | Cùng lúc CAP-01 | Không có gì để kiểm chứng nửa quan trọng nhất của ranh giới |
| Nội dung thông báo lệnh vừa đóng | `order-execution` (FR-039) | **Blocked** | Cùng lúc CAP-13 | Mất **đường vào nóng nhất** — xem OQ-4 |
| Cơ chế ghi âm và bản ghi âm **tua được** | `voice-journal` (FR-057) | At Risk | Cùng lúc CAP-08, CAP-11 | Hai capability lùi lại; phần còn lại của replay vẫn chạy |
| Ngoại lệ đích gắn memo ở màn xem lại | `voice-journal` (FR-021) | On Track | Cùng lúc CAP-11 | **Đã cascade** — bài học về lệnh này sẽ nằm trong bản ghi của lệnh khác nếu thiếu |
| Kết quả chấm luật theo `cid` | `playbook-grading` (FR-044) | At Risk | Cùng lúc CAP-09 | CAP-09 lùi lại; các phần khác vẫn chạy |
| Sự kiện đổi mức tâm lý kèm mốc thời gian | `tilt-meter` (FR-048) | At Risk | Cùng lúc CAP-04 | Dải sự kiện thiếu một loại; các loại khác vẫn hiện |
| Đường vào từ lịch sử và chi tiết một lệnh | `daily-journal` (FR-044) | At Risk | Cùng lúc CAP-03 | Chỉ còn đường vào từ thông báo — mà đường đó lại đang blocked |
| Bề mặt đọc ba thước đo thành xu hướng | `process-score` + `daily-journal` | At Risk | Trước lần đọc M1/M2/M3 đầu tiên | Bản ghi vẫn sinh ra, chỉ chưa ai đọc thành xu hướng |

## 9. Assumptions & Validation

| Assumption | Impact if Wrong | Validation | Status |
|------------|-----------------|------------|--------|
| ~~Việc tự đóng băng bối cảnh thuộc feature này~~ | — | — | **Resolved 2026-08-29: thuộc `order-execution`.** Feature này là **màn đọc dữ liệu có sẵn** |
| Khoá khi ở màn xem lại áp cho **mở lệnh mới và sửa bảo vệ**, **không** áp cho đóng vị thế và thoát khẩn cấp | Người chơi đang cầm vị thế **bị kẹt trong màn ôn tập**, hoặc bị dồn vào chỗ chỉ còn cách đóng sạch mọi thứ — **rủi ro lớn hơn nhiều so với việc bắn nhầm** | Nêu lại như một bất biến, có test riêng | **Confirmed** 2026-08-28 (URD A-02) |
| Cách nhắc khi vào replay lúc đang có vị thế mở là **một dòng thông báo**, vào thẳng | Cách vào màn xem lại đổi | — | **Confirmed** 2026-08-28 (URD A-03) |
| Người chơi **không cần** xem lại cả buổi như một dòng liên tục | Cách lưu bối cảnh **đổi hoàn toàn** — hiện chỉ lưu quanh từng lệnh | Hỏi khi thiết kế | Open (URD A-04 → OQ-3) |
| Memo ghi lúc xem lại dùng **chính cơ chế ghi âm** đang có, chỉ khác đích: **lệnh đang xem** | Một bài học về lệnh này nằm trong bản ghi của lệnh khác, và **không ai phát hiện ra** | **Đã cascade** sang `voice-journal` FR-021 | Resolved (URD A-05, OQ-9) |
| Người chơi chấp nhận lần đứng ngoài **ngoài cửa sổ của mọi lệnh** không tua lại được | Sau vài tháng thấy tiếc những tối đứng ngoài trọn vẹn → phải quay lại lưu bối cảnh cho cả lần huỷ | Xem lại sau khoảng 20 phiên nếu người chơi hay hỏi tới | **Confirmed** 2026-08-28 (URD A-06) |
| Việc **mở màn replay là đủ** để trục Review ghi nhận sẽ không bị lợi dụng | Thành thói quen mở rồi thoát để lấy điểm → trục Review mất ý nghĩa và điểm quy trình bị thổi lên | Theo dõi qua M2 (thời lượng xem trung vị). **Cơ chế hiện tại chỉ đo chứ không ngăn** | Partially confirmed (URD A-07 — cách tính đã chốt, việc bị lợi dụng thì chưa kiểm được) |
| **Feature này tạo ra bản ghi "lệnh nào đã được xem lại, lúc nào"**; `process-score` và `daily-journal` chỉ đọc | `process-score` chỉ lưu ở mức phiên, không đủ cho M1 (đếm theo lệnh) và M2 (cần mốc thời gian). **Không ai nhận việc ghi thì cả ba thước đo không đo được** | Xác nhận cùng `process-score` | Open (URD A-08 🔶) |
| Cửa sổ **5 phút trước lúc mở và 5 phút sau lúc đóng** là đủ cho việc ôn tập | Ngắn quá thì không thấy bối cảnh dẫn tới setup; dài quá thì tốn chỗ mà không ai xem tới | Hỏi người chơi khi thiết kế | Open (URD A-09) |

## 10. Product Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| ~~Quyền sở hữu việc đóng băng bối cảnh chưa chốt~~ | — | — | **Đã giải 2026-08-29**: thuộc `order-execution`. Quy mô feature xác định: ~35 story, màn đọc thuần | — |
| **Một lệnh thật bay ra từ màn ôn tập** | Low | **Rất cao** | CAP-01 khoá **mở lệnh mới và sửa bảo vệ** trong suốt thời gian ở màn này; kiểm bằng checkpoint J2 mỗi lần đổi màn | Người chơi |
| **Người chơi bị kẹt trong màn xem lại khi cần thoát gấp** | Low | **Rất cao** | Đóng vị thế và thoát khẩn cấp **không bao giờ bị khoá**; thoát khẩn cấp còn **thoát luôn khỏi màn xem lại** để người chơi tự mắt xác nhận | Người chơi |
| Xem lại thành tính năng dùng một lần rồi quên | High | High | M1 đo **đường xu hướng nhiều tháng**, không so một mốc — vì giai đoạn đầu vốn cao do mới lạ. CAP-13 (đường vào nóng nhất) là đòn bẩy chính, mà nó đang blocked | Người chơi |
| Mở rồi thoát ngay để lấy điểm trục Review | Medium | Medium | Ranh giới đã chốt là **mở là tính**, nên feature này không được đặt thêm điều kiện. Đổi lại M2 đọc kèm **thời lượng xem trung vị** — nếu tụt về gần 0 thì đặt lại câu hỏi cùng `process-score` | Người chơi |
| Đo MFE/MAE lẫn chiều lệnh mua và lệnh bán | Medium | High | Đây là **lỗi âm thầm** — hình vẫn đẹp, số vẫn có, chỉ là sai. Checkpoint J1 phải kiểm **cả một lệnh mua và một lệnh bán**, không phải chỉ một chiều | Người chơi |
| Nhầm "đang thu nốt" với "bối cảnh không còn" | Medium | Medium | Hai thông điệp phải **khác nhau rõ**; đối chiếu trực tiếp hai màn khi kiểm | Người chơi |
| Cửa sổ 5 phút không đủ để thấy bối cảnh dẫn tới setup | Medium | Medium | Hỏi người chơi khi thiết kế; con số là lựa chọn kỹ thuật từ nguồn, chưa được chốt | Người chơi |

## 11. Release & Launch Readiness

### 11.1 Release Horizon

| Horizon | Capabilities | Target | Status |
|---------|--------------|--------|--------|
| Now | CAP-trade-replay-01, 03, 04, 05, 06, 07 (P0) | Chưa chốt lịch | planned |
| Now (khoá) | CAP-trade-replay-02 (P0) | Chưa chốt lịch | **blocked by OQ-1 — và nó chặn cả CAP-03** |
| Next | CAP-trade-replay-08 → 12 (P1) | Chưa chốt lịch | CAP-08, CAP-11 phụ thuộc `voice-journal`; CAP-09 phụ thuộc `playbook-grading` |
| Later | CAP-trade-replay-13 (P2) | Chưa chốt lịch | blocked by OQ-4 |

> **CAP-02 blocked kéo theo CAP-03 không chạy được** — không có bối cảnh thì không có gì để tua. Đây là lý do
> OQ-1 phải chốt trước mọi thứ khác của feature này.

### 11.2 Launch Readiness

| Workstream | Must-pass criteria | Status | Guardrail metric (threshold → decision) |
|------------|--------------------|--------|-----------------------------------------|
| Không lệnh nào bay ra | Suốt thời gian màn xem lại mở, bấm mọi tổ hợp vẫn dùng để vào lệnh — cTrader demo **không có vị thế mới nào và không có thay đổi bảo vệ nào** | ⬜ | Một lệnh phát sinh → **dừng feature ngay**; đây là rủi ro lớn nhất |
| Đường thoát không bị khoá | Với một vị thế đang mở: **trước tiên** thử mở một lệnh mới (phải bị chặn), **sau đó** mới thoát khẩn cấp (phải đóng được và tự thoát về màn chính) | ⬜ | **Thứ tự này bắt buộc** — làm ngược thì việc khoá phiên sau thoát khẩn cấp che mất điều đang cần kiểm |
| Khoá nhả đúng | Thoát khỏi màn xem lại rồi bắn một lệnh thật — phải vào bình thường | ⬜ | Khoá không nhả → người chơi mất khả năng giao dịch sau mỗi lần ôn tập |
| Mốc đúng chiều | Kiểm bằng **một lệnh mua và một lệnh bán**, không phải chỉ một chiều | ⬜ | Đo lẫn chiều → tắt hiển thị hai mốc cho tới khi sửa; một con số sai còn tệ hơn không có |
| Điểm vào là sự thật | Điểm vào và điểm ra khớp **bản ghi lệnh**, không suy ra từ nến | ⬜ | Lệch → sửa; nến là bối cảnh, mốc mới là sự thật |
| Không trắng màn | Mở một lệnh chắc chắn không có bối cảnh — hiện nội dung thật, **không màn trắng, không báo lỗi**; và chuyển sang lệnh liền kề vẫn chạy | ⬜ | Trắng màn → sửa trước khi dùng |
| Hai thông điệp khác nhau | Đối chiếu trực tiếp thông điệp "đang thu nốt" với "bối cảnh không còn" | ⬜ | Hai câu giống nhau → viết lại; đọc nhầm làm người chơi tưởng mất dữ liệu |
| Lần đứng ngoài có mặt | Vũ trang rồi huỷ, đợi khoảng nửa phút, vào một lệnh thật và đóng — lần huỷ phải xuất hiện **trước** lần bắn, **cách đúng khoảng thời gian thật** | ⬜ | Không hiện → mất đúng thứ làm feature này thành huấn luyện |

## 12. Open Questions

* [x] **OQ-1** *(kế thừa URD A-01)*: Việc **tự đóng băng bối cảnh** thuộc feature này hay `order-execution`?
  **Resolved 2026-08-29: `order-execution` sở hữu** (CAP-order-execution-14). Feature này trở lại đúng bản
  chất **màn đọc**; CAP-03 hết bị chặn; và **tape tích luỹ từ phiên đầu** thay vì chỉ tồn tại từ ngày feature
  này ship.

* [ ] **OQ-2** *(kế thừa URD OQ-5)*: Tỷ lệ lệnh được xem lại (M1) có **sàn tối thiểu tuyệt đối** không, hay
  chỉ cần không giảm dần? Không có sàn thì M1 vẫn đạt kể cả khi tỷ lệ tuyệt đối rất thấp — và khi đó **không
  đọc được feature có đáng công sức bỏ ra hay không**.
* [x] **OQ-3** *(kế thừa URD OQ-4)*: Có cần xem lại **cả buổi tối như một dòng liên tục** không?
  **Chuyển sang `order-execution` OQ-9 (2026-08-29)** — nó quyết định cách lưu tape, mà việc lưu nay thuộc
  bên đó.

* [ ] **OQ-4** *(kế thừa URD OQ-8)*: Việc mở thẳng màn xem lại **từ thông báo lệnh vừa đóng** — nội dung
  thông báo thuộc `order-execution`, đường dẫn sang thuộc feature này. **Chặn CAP-13.**
  🔶 **Tạm quyết:** `order-execution` **nhận** phần dẫn đường (đã ghi vào `order-execution` OQ-7 và để chỗ
  trong FR-039 của nó). *Nếu sai:* mất **đường vào nóng nhất, đúng đường M2 đặt cược**.
* [ ] **OQ-5** *(kế thừa URD OQ-6)*: Bối cảnh đã lưu **giữ bao lâu** trước khi lệnh rơi về bản rút gọn?
  Nguồn đề xuất khoảng 2 năm, dài hơn hạn giữ bản ghi âm (khoảng 1 năm) — nghĩa là sẽ có **giai đoạn tua
  được hình mà không còn tiếng**. Cả hai con số là lựa chọn kỹ thuật chưa được chốt.
  *Lưu ý:* `voice-journal` đã chốt bản ghi âm **giữ vô thời hạn** — nên tiền đề "1 năm" của câu hỏi này có
  thể đã lỗi thời. Cần đối chiếu.
* [ ] **OQ-6** *(kế thừa URD OQ-7, chung với `daily-journal` OQ-9)*: Lần tự huỷ **nằm ngoài cửa sổ của mọi
  lệnh** hiện ra ở đâu để người chơi "vẫn được ghi nhận là đã xảy ra"? Bề mặt đó thuộc `daily-journal` hay
  feature này?
* [ ] **OQ-7** *(kế thừa URD A-08)*: `process-score` xác nhận rằng **feature này** tạo ra bản ghi "lệnh nào
  đã được xem lại, lúc nào" chứ?
  🔶 **Tạm quyết:** **có** (CAP-12). `process-score` chỉ lưu ở mức phiên, không đủ cho M1 và M2.
  *Nếu sai / nếu không ai nhận:* **cả ba thước đo của feature không đo được.**
* [ ] **OQ-8** *(kế thừa URD OQ-10)*: Nhãn memo trên dải thời gian hiện **bản máy chép** hay **bản người chơi
  đã sửa**? `voice-journal` cho sửa bản chép và bản sửa ghi đè bản máy chép.
  🔶 **Tạm quyết:** hiện **bản đang có hiệu lực** (đã sửa nếu có, không thì bản máy chép) — nhất quán với
  `voice-journal` BR-007.
* [ ] **OQ-9** *(kế thừa URD A-09)*: Cửa sổ **5 phút trước / 5 phút sau** có đủ không? Ngắn quá thì không
  thấy bối cảnh dẫn tới setup; dài quá thì tốn chỗ mà không ai xem tới.

---

> **Nguồn:** `trade-replay-urd.md` (14 nhu cầu, 8 journey, 23 tình huống ngoại lệ, 3 thước đo, 9 giả định) ·
> bốn tài liệu nền `docs/_shared/` · ranh giới nhận từ `order-execution`, `voice-journal`,
> `playbook-grading`, `tilt-meter`, `daily-journal`, `process-score`, `ai-desk`, `reports-export`.
> **Chưa có BRD**.
>
> **🔶 Ba quyết định thay user:** OQ-4 (order-execution nhận phần dẫn đường), OQ-7 (feature này ghi bản ghi
> xem lại), OQ-8 (nhãn memo dùng bản đang có hiệu lực). **OQ-1 em cố ý không quyết** — nó là quyết định
> **phạm vi**, quyết định feature này to gấp đôi hay không, và URD đã đánh dấu "không để trôi".
