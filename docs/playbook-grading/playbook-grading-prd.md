---
type: prd
feature: playbook-grading
status: draft
updated: 2026-08-29
links:
  - docs/playbook-grading/playbook-grading-urd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/order-execution-urd.md
  - docs/order-execution/srs/order-execution-spec.md
---

# playbook-grading — Product Requirements Document

## 1. Product Overview

`playbook-grading` đưa **một câu hỏi vào đúng khoảnh khắc người chơi còn quyền không vào lệnh**: lệnh sắp
bắn này có khớp với chính luật mình đã viết ra không? Nó đứng **sát** đường đặt lệnh nhưng không nằm trên
nó — điểm số là một lớp thông tin, không phải một cái chốt.

Hai mệnh đề làm nên feature này, và mệnh đề thứ hai quan trọng ngang mệnh đề thứ nhất: **đối chiếu luật
đúng lúc còn sửa được**, và **luật của tôi không bao giờ được phép cấm tôi**.

**Gap neo:** Hiện tại luật giao dịch chỉ sống trong đầu người chơi và trôi theo tâm trạng — cùng một setup,
tối nay đủ tiêu chuẩn, tối mai không. Nếu có checklist thì nó nằm trên giấy, và người chơi chỉ nhớ ra luật
**sau** khi đã vào lệnh, lúc không còn sửa được gì. Sau feature này: mỗi lần vũ trang, màn xác nhận nêu tên
playbook đang dùng, số luật đạt trên tổng, và luật nào không đạt — đọc hết trước khi bấm nút cuối cùng.

## 2. Goals

### 2.1 Goals

* **Người chơi biết lệnh có đúng sách không *trước* khi bấm**, không phải sáng hôm sau (trace UN-001).
* **Luật do người chơi viết không bao giờ chặn được lệnh của chính họ** — chỉ hạn mức rủi ro mới chặn
  được, và không có cách nào khai một luật playbook thành luật chặn (trace UN-002).
* **Điểm là kết quả tính toán xác định, không phải ý kiến của một mô hình** — cùng một bối cảnh luôn cho
  cùng một điểm (trace UN-007).
* **Người chơi bắt đầu với một quyển sách thật, không phải màn hình trống** (trace UN-003).
* **Mỗi lệnh mang nhãn playbook và điểm của nó**, làm nguyên liệu cho `process-score` trả lời "kiểu setup
  nào của tôi thực sự hoạt động" (trace UN-014).
* **Sửa luật không làm sai lệch bản ghi cũ** — điểm đã chấm là bản ghi của quyết định lúc đó (trace UN-004).

### 2.2 Non-goals

* **KHÔNG** để một luật playbook có hệ quả như một luật rủi ro. Hạn mức và việc thi hành chúng →
  `order-execution`.
* **KHÔNG** thống kê hiệu quả theo từng playbook (kỳ vọng theo R, MFE/MAE, so sánh nhiều lệnh) →
  `process-score`. Feature này tạo **dữ liệu điểm**; nơi đọc nó thành xu hướng là deck.
* **KHÔNG** điểm quy trình 5 trục và biểu đồ radar → `process-score`.
* **KHÔNG** sở hữu bộ đếm số lần tự huỷ trên màn chính → `order-execution`. Feature này chỉ gắn **điểm**
  vào một lần tự huỷ.
* **KHÔNG** đo trạng thái tâm lý → `tilt-meter`. **KHÔNG** nhận diện setup trên biểu đồ, tư vấn, tín hiệu →
  `ai-desk`. **Không mô hình ngôn ngữ nào chấm một lệnh.**
* **KHÔNG** ghi âm lý do vào lệnh → `voice-journal`. **KHÔNG** tua lại lệnh qua tape → `trade-replay`.
* **KHÔNG** nghi thức chuẩn bị trước phiên → `daily-journal`. **KHÔNG** báo cáo, xuất dữ liệu →
  `reports-export`.
* **KHÔNG** chia sẻ, nhập hoặc xuất playbook giữa nhiều người dùng — sản phẩm chỉ có một người dùng.

## 3. Personas

| Persona | Mô tả (1 dòng) | Nhu cầu chính | Nguồn |
|---------|----------------|---------------|-------|
| Người chơi — vai **người viết luật** | Ngoài phiên, trước màn hình, có chuột và bàn phím | Biến một thói quen đang nằm trong đầu thành một danh sách máy đối chiếu được | URD Mục 2, UN-013, UN-012 |
| Người chơi — vai **người bị luật soi** | Trong phiên, tay đặt trên tay cầm, không rảnh mắt | Giao dịch theo sách của chính mình và biết mình có làm đúng vậy không, trước khi bấm | URD Mục 2, UN-001, UN-006 |

> Đây là **một người ở hai bối cảnh**, không phải hai persona. Cách chia này quyết định phân công thiết bị:
> soạn luật bằng chuột và bàn phím, chọn luật bằng tay cầm. **AI desk không tham gia chấm điểm** — nó là
> actor hệ thống bị loại khỏi phạm vi, xem `docs/_shared/project-profile.md`.

## 4. Capabilities

| ID | Capability | Priority | Rationale (vì sao tier này) | Traces to | Bóc ~N story | Done when (product outcome) | Sẵn sàng |
|----|------------|----------|-----------------------------|-----------|--------------|-----------------------------|----------|
| CAP-playbook-grading-01 | Soạn playbook: tên, phương pháp, cặp áp dụng, mô tả, danh sách luật có thứ tự | P0 | Không có nơi khai luật thì không có gì để chấm — đây là gốc của cả feature | UN-013, UN-012 | ~9 | Người chơi biến được một cách chơi quen thuộc thành một danh sách luật máy đối chiếu được | ⚠️ chờ OQ-4 (khai luật tự do hay chọn từ danh sách) |
| CAP-playbook-grading-02 | Mỗi luật khai rõ **bắt buộc hay không** và **hệ thống tự kiểm hay tự trả lời sau lệnh** | P0 | Hai thuộc tính này quyết định mẫu số của mọi phép chấm; thiếu chúng thì con số `n/m` vô nghĩa | UN-013, UN-009 | ~4 | Mỗi luật có đủ hai thuộc tính, và người chơi hiểu hệ quả của từng lựa chọn | ✅ |
| CAP-playbook-grading-03 | Bộ playbook mẫu theo các setup M5 quen thuộc | P0 | Nguồn nói thẳng "màn hình trống chính là trạng thái thất bại"; không có bộ mẫu thì feature chết ngay ngày đầu | UN-003 | ~4 | Người chơi mở sản phẩm lần đầu đã có một quyển sách thật, dùng được ngay và sửa được | ✅ |
| CAP-playbook-grading-04 | Chọn playbook đang dùng bằng tay cầm trong menu an toàn | P0 | Chọn sai sách thì chấm sai toàn bộ buổi; và việc chọn xảy ra **trong phiên** nên bắt buộc phải làm bằng tay cầm | UN-006 | ~4 | Người chơi đổi được sách giữa phiên không phải rời tay sang chuột, và luôn thấy sách đang dùng trên màn chính | ✅ |
| CAP-playbook-grading-05 | Chấm điểm mỗi lần vũ trang và mỗi lần bắn, xác định và không có mô hình ngôn ngữ | P0 | Lõi giá trị feature. Tính xác định là điều kiện để người chơi tin con số | UN-001, UN-007, UN-008 | ~10 | Cùng một bối cảnh luôn cho cùng một điểm, và điểm lúc bắn là bản ghi chính thức | ✅ |
| CAP-playbook-grading-06 | Hiển thị điểm trên màn xác nhận, trước thao tác cuối | P0 | Nếu điểm tới sau khi bấm thì feature mất toàn bộ lý do tồn tại — nó thành sổ sách thay vì người huấn luyện | UN-001 | ~5 | Người chơi đọc được `n/m` và tên luật không đạt trước khi bấm nút cuối cùng | ✅ |
| CAP-playbook-grading-07 | Ranh giới cứng: luật playbook không bao giờ chặn được lệnh | P0 | Nỗi sợ lớn nhất của người chơi là công cụ quay ra cấm mình; phá ranh giới này là phá lòng tin không lấy lại được | UN-002 | ~3 | Một luật không đạt vẫn cho lệnh đi trọn vẹn, không cản, không cảnh báo chặn, không xác nhận phụ | ✅ |
| CAP-playbook-grading-08 | Nhóm "ngoài kế hoạch" khi chưa chọn playbook | P0 | Bắn khi chưa chọn sách là chuyện sẽ xảy ra; không xử lý thì hoặc crash, hoặc ghi nhầm là đúng sách | UN-005 | ~3 | Lệnh vẫn đi bình thường và được đọc trung thực là ngoài kế hoạch ở mọi nơi nhìn lại | ✅ |
| CAP-playbook-grading-09 | Xem lại một lệnh đã chấm với trạng thái từng luật | P0 | Đây là bề mặt tự kiểm chứng của **mọi** journey khác trong feature; không có nó thì không checkpoint nào chạy được | UN-014 | ~5 | Người chơi mở một lệnh cũ và thấy playbook nào chấm nó, từng luật đạt / không đạt / không kiểm được / chưa trả lời | ✅ |
| CAP-playbook-grading-10 | Sửa luật giữa phiên mà không đụng điểm đã chấm | P0 | Nếu sửa luật làm đổi bản ghi cũ thì lịch sử nói dối, và mọi so sánh về sau vô nghĩa | UN-004 | ~4 | Điểm của lệnh cũ giữ nguyên đúng như lúc chấm; luật mới chỉ áp cho lần vũ trang sau | ✅ |
| CAP-playbook-grading-11 | Checklist tự-đánh-giá sau khi lệnh đóng | P1 | Mở rộng phạm vi luật kiểm được, nhưng v1 sống được chỉ với luật hệ thống tự kiểm | UN-009 | ~5 | Người chơi trả lời được những luật chỉ mình biết, tối đa 3 câu, và bỏ qua không tốn gì | ✅ |
| CAP-playbook-grading-12 | Ngừng dùng một playbook mà giữ nguyên lịch sử | P1 | Chỉ cần khi người chơi đã tích luỹ vài sách; v1 chưa có sách nào để bỏ | UN-011 | ~3 | Playbook ngừng dùng biến khỏi danh sách chọn, các lệnh cũ vẫn tra ra đúng tên và đúng điểm | ✅ |
| CAP-playbook-grading-13 | Điểm của một lần tự huỷ **đạt đủ luật bắt buộc** | P1 | Giá trị cao nhưng phụ thuộc một định nghĩa chưa chốt; làm sớm mà sai định nghĩa thì hiện quá thường xuyên và mất tác dụng | UN-010 | ~4 | Người chơi nhận ra khi mình đang bỏ qua một cơ hội đúng sách vì sợ, chứ không vì luật | ⚠️ chờ OQ-3 (định nghĩa "đạt chuẩn") |
| CAP-playbook-grading-14 | Cảnh báo (không chặn) khi một luật bắt buộc gần như luôn đạt trong lịch sử | P2 | Chống việc pha loãng luật khó bằng luật dễ; chỉ có nghĩa sau khi đã tích luỹ vài tháng lịch sử | UN-013 | ~3 | Người chơi thấy được luật nào của mình đang không phân biệt được gì | 🔒 blocked by OQ-5 |

> **P0 = 10 capability, vượt ngưỡng cảnh báo 7.** Em **không** đề xuất tách feature, nhưng lý do khác đợt
> trước: mười cái này không phải bất biến an toàn mà là **một vòng khép kín nhỏ nhất** — khai luật (01, 02),
> có sách để khai (03), chọn được sách (04), chấm (05), hiện đúng lúc (06), không chặn (07), xử lý trường
> hợp không có sách (08), xem lại được (09), sửa luật an toàn (10). Bỏ bất kỳ mắt nào thì vòng đứt và bảy
> mắt còn lại không tự chứng minh được. CAP-09 đặc biệt: nó là **bề mặt kiểm chứng của cả feature**.

## 5. Upstream Traceability

| Capability | Traces to | Product outcome | Success metric |
|------------|-----------|-----------------|----------------|
| CAP-05, CAP-06 | UN-001, UN-007, UN-008 | Đối chiếu luật xảy ra khi còn sửa được | M2 Tỷ lệ đạt đủ luật bắt buộc |
| CAP-07 | UN-002 | Người chơi không bao giờ bị luật của chính mình cấm | — (ranh giới nhị phân, kiểm bằng checkpoint J2) |
| CAP-01, CAP-02, CAP-03, CAP-04 | UN-013, UN-012, UN-003, UN-006 | Luật trong đầu trở thành thứ đối chiếu được | M1 Tỷ lệ lệnh gắn playbook |
| CAP-08 | UN-005 | Lệnh ngoài sách được ghi trung thực thay vì ghi nhầm là đúng sách | M1 (mẫu số) |
| CAP-09, CAP-10, CAP-12 | UN-014, UN-004, UN-011 | Lịch sử điểm đáng tin qua thời gian | M1, M2 (cả hai đọc từ lịch sử) |
| CAP-11 | UN-009 | Những luật chỉ người chơi biết cũng vào được bản ghi | M2 (mẫu số mở rộng) |
| CAP-13 | UN-010 | Phân biệt được tự huỷ vì kỷ luật với tự huỷ vì sợ | — (xem ghi chú Mục 7) |
| CAP-14 | UN-013 | Chất lượng cuốn sách, không chỉ sự tuân thủ nó | — (chống gian lận cho M2) |

## 6. Key Capability Interactions

* **Vào một lệnh có sách:** CAP-04 (sách đang dùng, thuộc trạng thái phiên) → người chơi vũ trang →
  CAP-05 chấm lần vũ trang → CAP-06 đưa `n/m` lên **màn xác nhận do `order-execution` sở hữu** → bắn →
  CAP-05 chấm lại tại thời điểm bắn, và **điểm lúc bắn là bản ghi chính thức**.
* **Không có sách:** CAP-08 thay chỗ CAP-04; CAP-06 vẫn hiện màn xác nhận, đọc là "chưa có playbook".
* **Sau khi lệnh đóng:** CAP-11 xếp hàng checklist; câu trả lời chảy ngược vào bản ghi của CAP-09 và
  **có** làm đổi kết luận "đạt đủ luật bắt buộc" — vì đó chính là việc nó sinh ra để làm.
* **Tự huỷ:** `order-execution` tăng bộ đếm (luật rộng) **cùng khoảnh khắc** CAP-13 xét điều kiện hiện
  điểm. Hai thông tin phải đọc được như một, không đá nhau.
* **Sửa luật:** CAP-10 đóng băng phần hệ thống tự kiểm ngay tại thời điểm bắn; CAP-01 sửa luật chỉ ảnh
  hưởng lần vũ trang sau.
* **Ranh giới ra ngoài:** `process-score` đọc điểm của CAP-05 làm **trục tuân thủ**; `tilt-meter` đọc số
  luật không đạt trong ba lần bắn gần nhất làm **một tín hiệu**; `trade-replay` đặt kết quả chấm cạnh dòng
  thời gian. Cả ba chỉ **đọc**, không cái nào sửa được điểm.

## 7. Success Metrics

| Metric | Baseline | Target | Measurement Method | Timeframe |
|--------|----------|--------|--------------------|-----------|
| M1 Tỷ lệ lệnh gắn playbook | Chưa có — xác lập tỷ lệ trung bình từ 10 phiên đầu | Cao hơn baseline sau 3 tháng. **Chưa có sàn tối thiểu** — xem OQ-2 | Đếm số lệnh theo nhóm playbook so với nhóm "ngoài kế hoạch", đọc cuối mỗi tháng. **Không tính vào tử số** những lệnh mà chính luật "cặp nằm trong danh sách playbook khai" không đạt — chọn một sách đầu phiên rồi bắn mọi thứ dưới nó không làm con số này đẹp lên | Hằng quý |
| M2 Tỷ lệ đạt đủ luật bắt buộc | Chưa có — xác lập tỷ lệ trung bình từ 10 phiên đầu | Cao hơn baseline sau 3 tháng, **đồng thời** số luật bắt buộc trung bình mỗi playbook không giảm | Đọc tỷ lệ cuối mỗi tháng, **kèm** số luật bắt buộc trung bình của các sách đang dùng **và** số lần sửa tham số luật theo hướng lỏng hơn trong kỳ. Ba số đi cùng nhau để việc bớt luật hoặc nới ngưỡng không tự động thành "tiến bộ" | Hằng quý |

> **Feature này không tự đo được thành công của chính nó.** Cả hai thước đo đọc từ bề mặt thuộc
> `process-score` (URD A-08). `process-score` trượt lịch thì feature chạy mà không biết mình có hiệu quả
> không — xem OQ-6.
>
> **Giới hạn đã biết.** Cả hai đo *sự nhất quán với sách của mình*, không đo *chất lượng của cuốn sách*.
> M2 chặn được việc bớt luật cho dễ đạt, nhưng **không** chặn được việc thêm luật bắt buộc gần như luôn
> đúng để pha loãng một hai luật thật sự khó. CAP-14 sinh ra để bịt lỗ này — và nó đang ở P2.
>
> **CAP-07 và CAP-13 cố ý không có metric xu hướng.** CAP-07 là ranh giới nhị phân (một luật không đạt
> vẫn cho lệnh đi, hoặc không) — kiểm bằng checkpoint hai-bối-cảnh của URD Journey 2. CAP-13 là một sự
> kiện hiếm, đo bằng tần suất thì khuyến khích sai hành vi.

## 8. Dependencies

| Dependency | Owner | Status | Needed-by | Impact if Late |
|------------|-------|--------|-----------|----------------|
| Màn xác nhận và chuỗi vũ trang–bắn | `order-execution` | On Track | Cùng lúc CAP-06 | Chặn CAP-05, CAP-06 — feature này **đóng góp nội dung** vào màn đó, không sở hữu nó |
| Menu an toàn (GameOverlay) làm chỗ đặt màn chọn sách | `order-execution` | On Track | Cùng lúc CAP-04 | Chặn CAP-04; không có nơi nào khác chọn được sách bằng tay cầm |
| Khái niệm "hạn mức rủi ro" để phân biệt với luật playbook | `order-execution` | On Track | Cùng lúc CAP-07 | Không có ranh giới đối chiếu thì CAP-07 không kiểm chứng được |
| Bề mặt đọc điểm thành xu hướng (deck) | `process-score` | At Risk | Trước lần đọc M1/M2 đầu tiên | **Cả hai metric không đo được** — xem OQ-6 |
| Danh sách bối cảnh hệ thống quan sát được (giá, trung bình động, biên độ, chênh lệch giá, đồng hồ phiên, vị thế mở, trạng thái AI desk) | `order-execution` + `ai-desk` | At Risk | Trước khi chốt CAP-01 | Luật người chơi muốn nhưng nằm ngoài danh sách phải hạ xuống tự-đánh-giá — có thể gây thất vọng khi soạn |
| Quyết định định nghĩa "đạt chuẩn" cho một lần tự huỷ | Người chơi | Blocked | Trước khi CAP-13 vào Next | CAP-13 không bắt đầu được |

## 9. Assumptions & Validation

| Assumption | Impact if Wrong | Validation | Status |
|------------|-----------------|------------|--------|
| Người chơi soạn playbook bằng chuột và bàn phím, ngoài lúc giao dịch | CAP-01 sai; phải thiết kế cả đường soạn luật bằng tay cầm, tốn kém hơn nhiều | Hỏi người chơi khi thiết kế trang soạn | Open (URD A-01) |
| Một playbook đang dùng tại một thời điểm | Cách chấm và cách hiện điểm đổi hoàn toàn | Xác nhận trước khi chốt màn chọn playbook | Open (URD A-02) |
| Danh sách bối cảnh kiểm tự động được là **đóng** | Luật ngoài danh sách phải hạ xuống tự-đánh-giá — mất khả năng hiện trước khi bấm | Chốt danh sách cùng `order-execution` và `ai-desk` | Open (URD A-03) |
| Người chơi chịu trả lời checklist **sau khi lệnh đóng** thay vì ngay lúc vào lệnh | Bỏ qua mọi lần thì toàn bộ nhóm luật tự-đánh-giá thành vô dụng | Theo dõi sau 10 phiên đầu; bỏ qua toàn bộ thì thiết kế lại cách hỏi | Partially confirmed (URD A-04 — thời điểm hỏi đã chốt, việc chịu trả lời thì chưa) |
| "Đạt chuẩn" nghĩa là đạt đủ luật **bắt buộc**, không cần đạt luật không bắt buộc | Thông tin ở CAP-13 hiện quá thường xuyên và mất tác dụng | Xác nhận với người chơi | Open (URD A-05 🔶 → OQ-3) |
| Việc chấm luôn xong kịp để màn xác nhận mở ra ngay khi vũ trang | Màn xác nhận mở muộn — người chơi mất phản hồi tức thì của nút bấm, nhịp thao tác đứt | Đo độ trễ mở màn xác nhận khi có sản phẩm | Partially confirmed (URD A-06 — cách xử lý đã chốt, tốc độ thì chưa kiểm được) |
| Người chơi khai luật bằng cách **chọn từ danh sách có sẵn rồi đặt tham số**, không viết luật tự do | Phần lớn luật rơi vào nhóm tự-đánh-giá và mất khả năng hiện trước khi bấm | Xác nhận khi thiết kế trang soạn | Open (URD A-07 → OQ-4) |
| Feature này không tự đo được thành công của chính nó | `process-score` trượt lịch thì feature chạy mà không biết có hiệu quả không | Chấp nhận, hoặc thống nhất một cách đọc thô tạm thời | Open (URD A-08 → OQ-6) |
| Playbook đang dùng bị ngừng dùng giữa phiên thì lần vũ trang sau rơi về "ngoài kế hoạch" | Người chơi bất ngờ mất nhãn playbook giữa buổi | Xác nhận với người chơi | Open (URD A-09 🔶) |

## 10. Product Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| Người chơi nới luật dần để điểm đẹp lên, M2 vẫn tăng mà chất lượng không đổi | High | High | Đọc M2 cùng số luật bắt buộc trung bình và số lần nới tham số; nâng CAP-14 lên P1 nếu thấy dấu hiệu | Người chơi |
| Checklist sau lệnh đóng gây mệt, người chơi bỏ qua mọi lần → nhóm luật tự-đánh-giá thành vô dụng | High | Medium | Trần cứng 3 câu, mỗi câu một thao tác; bỏ qua không bao giờ bị trừ; theo dõi tỷ lệ trả lời trong 10 phiên đầu | Người chơi |
| Việc chấm chậm làm màn xác nhận mở muộn, phá nhịp thao tác trên tay cầm | Medium | High | Giữ phép chấm là hàm thuần trên bối cảnh đã có sẵn, không gọi ra ngoài; đo độ trễ ngay phiên đầu | Người chơi |
| `process-score` trượt lịch → cả M1 và M2 không đo được | Medium | High | Thống nhất một cách đọc thô tạm thời (đếm tay từ bản ghi lệnh) trước khi chạy 10 phiên đầu | Người chơi |
| Bộ playbook mẫu không giống cách chơi thật, người chơi bỏ hết rồi rơi vĩnh viễn vào "ngoài kế hoạch" | Medium | Medium | Danh sách chọn rỗng thì nói rõ và chỉ đường về trang soạn; **không** tự dựng lại bộ mẫu người chơi đã chủ động bỏ | Người chơi |
| Người chơi hiểu nhầm điểm playbook là một cái chặn, rồi ngại vũ trang | Low | High | Ranh giới CAP-07 phải hiện diện trong chính wording màn xác nhận, không chỉ trong tài liệu | Người chơi |

## 11. Release & Launch Readiness

### 11.1 Release Horizon

| Horizon | Capabilities | Target | Status |
|---------|--------------|--------|--------|
| Now | CAP-playbook-grading-01 → 10 (P0) | Chưa chốt lịch | planned — sau `order-execution` |
| Next | CAP-playbook-grading-11 → 13 (P1) | Chưa chốt lịch | CAP-13 blocked by OQ-3 |
| Later | CAP-playbook-grading-14 (P2) | Chưa chốt lịch | blocked by OQ-5 |

> Feature này **không chạy được trước `order-execution`** — nó đóng góp nội dung vào màn xác nhận và màn
> chọn sách nằm trong menu an toàn, hai thứ do feature kia sở hữu.

### 11.2 Launch Readiness

| Workstream | Must-pass criteria | Status | Guardrail metric (threshold → decision) |
|------------|--------------------|--------|-----------------------------------------|
| Ranh giới không-chặn | Checkpoint hai bối cảnh: vi phạm **luật playbook** → vị thế mới xuất hiện trên cTrader demo; vi phạm **hạn mức rủi ro** → lệnh bị chặn | ⬜ | Một lần luật playbook chặn được lệnh → tắt hiển thị điểm cho tới khi sửa xong, vì một cái chốt giả còn tệ hơn không có điểm |
| Điểm đúng lúc | Không lần vũ trang nào mà màn xác nhận hiện ra kèm ô điểm trống | ⬜ | Ô điểm trống xuất hiện → dừng dùng điểm để ra quyết định cho tới khi sửa |
| Tính xác định | Cùng một bối cảnh dựng lại cho ra cùng một điểm, kiểm 10 lần | ⬜ | Một lần lệch → điều tra ngay; điểm không xác định thì mọi so sánh về sau vô nghĩa |
| Lịch sử bất biến | Ghi điểm một lệnh, sửa ngưỡng theo hướng làm nó đáng lẽ phải fail, mở lại — điểm y nguyên | ⬜ | Điểm cũ đổi theo luật mới → dừng tính năng sửa luật cho tới khi sửa xong |
| Bộ mẫu dùng được | Người chơi chạy được một phiên chỉ với bộ playbook mẫu, không phải soạn gì | ⬜ | Không dùng được → bộ mẫu là công thừa, làm lại theo cách chơi thật |

## 12. Open Questions

* [ ] OQ-1 *(kế thừa URD OQ-2)*: Tỷ lệ lệnh có playbook (M1) có **sàn tối thiểu tuyệt đối** không, hay chỉ
  cần cao hơn baseline? Không có sàn thì M1 vẫn đạt kể cả khi tỷ lệ tuyệt đối rất thấp.
* [ ] OQ-2 *(kế thừa URD OQ-6)*: Người chơi tự khai được một **luật kiểu hoàn toàn mới** không, hay chỉ
  chọn từ danh sách luật có sẵn rồi đặt tham số? **Chặn phạm vi CAP-01.** Xem URD A-07.
* [ ] OQ-3 *(kế thừa URD A-05)*: "Đạt chuẩn" ở CAP-13 nghĩa là đạt đủ luật **bắt buộc**, hay đạt **mọi**
  luật? Người chơi đã chốt *nguyên tắc* chỉ-hiện-khi-đạt-chuẩn nhưng chưa chốt *định nghĩa*.
  **Chặn CAP-13 vào Next.**
* [ ] OQ-4: Trang soạn playbook dùng chuột và bàn phím (URD A-01) — xác nhận trước khi chốt phạm vi CAP-01.
  Nếu sai thì phải thiết kế cả đường soạn luật bằng tay cầm.
* [ ] OQ-5 *(kế thừa URD OQ-7)*: Có cần cảnh báo (không chặn) khi một luật bắt buộc **gần như luôn đạt**
  trong lịch sử không? **Chặn CAP-14.** Không có gì nhắc thì thêm luật dễ là cách làm đẹp M2 mà chất lượng
  thật không đổi.
* [ ] OQ-6 *(kế thừa URD A-08)*: `process-score` chưa có thì đọc M1/M2 bằng cách nào? 🔶 **Tạm quyết:** đếm
  tay từ bản ghi lệnh của chính feature này trong ba tháng đầu, và ghi rõ đó là số đọc thô.
  *Nếu sai:* feature chạy ba tháng mà không biết mình có hiệu quả không.
* [ ] OQ-7 *(kế thừa URD A-09)*: Playbook đang dùng bị **ngừng dùng giữa phiên** thì lần vũ trang sau rơi
  về "ngoài kế hoạch", hay giữ nguyên sách đó tới hết phiên? Cả hai phương án đều hợp lý.

---

> **Nguồn:** `playbook-grading-urd.md` (14 nhu cầu, 8 journey, 19 tình huống ngoại lệ, 2 thước đo, 9 giả
> định) · bốn tài liệu nền `docs/_shared/` · ranh giới nhận từ `order-execution`, `process-score`,
> `tilt-meter`, `ai-desk`. **Chưa có BRD** — mọi capability trace tới `UN-*`.
>
> **🔶 Một quyết định thay user:** cách đọc M1/M2 khi `process-score` chưa có (OQ-6). Hai chỗ khác
> (CAP-13 "đạt chuẩn", playbook ngừng dùng giữa phiên) em **không** tự quyết — chúng đổi hành vi người chơi
> nhìn thấy, nên để nguyên ở OQ-3 và OQ-7.
