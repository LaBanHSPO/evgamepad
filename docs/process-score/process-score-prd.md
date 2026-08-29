---
type: prd
feature: process-score
status: draft
updated: 2026-08-29
links:
  - docs/process-score/process-score-urd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/srs/order-execution-spec.md
  - docs/playbook-grading/srs/playbook-grading-spec.md
  - docs/ai-desk/srs/ai-desk-spec.md
  - docs/tilt-meter/srs/tilt-meter-spec.md
  - docs/voice-journal/srs/voice-journal-spec.md
  - docs/daily-journal/srs/daily-journal-spec.md
  - docs/trade-replay/srs/trade-replay-spec.md
---

# process-score — Product Requirements Document

## 1. Product Overview

`process-score` cho **một con số duy nhất cho buổi tối, dựng trên chất lượng quyết định thay vì trên tiền** —
và bề mặt nhìn lại nơi con số đó sống: **deck**.

Điểm mấu chốt không phải "chấm điểm cho vui" mà là một tính chất rất cụ thể: **với cùng mức chuẩn bị và nhìn
lại, một tối đứng ngoài đúng lúc không bao giờ chấm thấp hơn một tối giao dịch tốt.** Mọi thứ khác — năm
trục, radar, bảng theo playbook, tab kết quả nằm sau một cú bấm có chủ ý — đều tồn tại **để bảo vệ tính chất
đó khỏi bị bào mòn**.

Feature này **không sinh ra dữ liệu nào của riêng nó**. Nó đọc bằng chứng do **bảy** feature khác tạo ra rồi
gộp phần lớn chúng thành câu trả lời cho câu hỏi mà không nơi nào khác trả lời được: **"tôi có đang khá lên
không."**

**Gap neo:** Hiện tại con số duy nhất nói về một buổi tối là lãi lỗ — thứ phần lớn do thị trường quyết. Tối
chơi ẩu mà lãi vẫn đọc là "thắng"; tối kỷ luật mà tape chết vẫn đọc là "thua" — **học sai bài mỗi tối**. Và
một tối đứng ngoài cả buổi thì sổ trống, trông y hệt một buổi bỏ bê, sinh áp lực phải giao dịch để "có gì đó
trong sổ". Sau feature này: tape chết + chuẩn bị đầy đủ chấm **100**, trong khi một tối giao dịch tốt với
một luật hụt chấm **98**.

## 2. Goals

### 2.1 Goals

* **Một con số cho buổi tối dựng trên quyết định, không phải trên tiền** — tỷ lệ thắng, profit factor, lãi
  lỗ và R **không phải là trục** (trace UN-001).
* **Tối đứng ngoài đúng lúc không bao giờ chấm thấp hơn tối giao dịch tốt cùng mức chuẩn bị** (trace UN-002).
* **Điểm không trở thành nỗi lo mới thay chỗ lãi lỗ** — không có điểm sống để canh giữa phiên (trace UN-004,
  USC-001).
* **Không có gì cộng dồn xuyên phiên** — không chuỗi ngày, không cấp độ, không huy hiệu (trace UN-005).
* **Mọi con số truy ngược được về đầu vào của nó**, và đổi trọng số thì lịch sử tính lại (trace UN-009).
* **Điểm là kết quả tính toán xác định, không phải ý kiến của một mô hình** (trace UN-010).

### 2.2 Non-goals

* **KHÔNG** sinh ra dữ liệu của riêng mình. Feature này **đọc** bằng chứng từ bảy feature khác. Ngoại lệ duy
  nhất: bản ghi **số lần mở deck giữa phiên** — vì đó là số liệu đo chính rủi ro lớn nhất của nó.
* **KHÔNG** chấm điểm từng lệnh theo luật playbook → `playbook-grading`. Feature này chỉ **tiêu thụ** kết
  quả đó làm trục tuân thủ; nó không định nghĩa luật, không chấm, không sửa điểm của một lệnh.
* **KHÔNG** sinh ra chỉ số chất lượng cơ hội → `ai-desk`. Chỉ **đọc** con số đó để tính trục chọn lọc.
* **KHÔNG** đo trạng thái tâm lý → `tilt-meter`. Chỉ nhận phần **hiển thị hồi tưởng**, và nhận ràng buộc
  **tilt không bao giờ là đầu vào điểm**.
* **KHÔNG** hạn mức rủi ro và việc thi hành → `order-execution`. Trục kỷ luật rủi ro chấm lại **đúng bộ luật
  mà gateway đã thi hành**, không dựng một định nghĩa thứ hai.
* **KHÔNG** sở hữu bộ đếm tự huỷ → `order-execution`. Feature này chỉ nhận phần **quy ra điểm**, và chỉ quy
  trên **tập con** những lần huỷ xảy ra lúc đang có điều kiện đứng ngoài.
* **KHÔNG** thu điểm tự chấm đầu/cuối buổi và nghi thức chuẩn bị → `daily-journal`. Deck **render** những
  dòng đó, tuyệt đối **không mở một luồng thu thứ hai**.
* **KHÔNG** ghi âm (`voice-journal`) · tua lại tape (`trade-replay`) · bàn làm việc AI và giọng huấn luyện
  (`ai-desk`) · báo cáo, xuất dữ liệu, sao lưu (`reports-export`).
* **KHÔNG** chia sẻ, xếp hạng hoặc so sánh điểm với bất kỳ ai — sản phẩm chỉ có một người dùng.

## 3. Personas

| Persona | Mô tả (1 dòng) | Nhu cầu chính | Nguồn |
|---------|----------------|---------------|-------|
| Người chơi | **Sau khi đóng phiên**, rời tay cầm, ngồi trước màn hình với chuột và bàn phím — hoặc **cuối tháng** khi muốn nhìn lại một quãng dài | Biết mình có đang ra quyết định tốt hơn không, **bằng một thước đo mà thị trường không quyết hộ** | URD Mục 2, UN-001, UN-013 |

> **Không có persona thứ hai.** **AI desk là actor hệ thống**: copilot **đọc được các trục** để huấn luyện,
> nhưng **không tính bất kỳ con số nào hiện trên deck** và không đặt được lệnh. Sàn cTrader/Spotware là
> nguồn sự thật cho tiền.

## 4. Capabilities

| ID | Capability | Priority | Rationale (vì sao tier này) | Traces to | Bóc ~N story | Done when (product outcome) | Sẵn sàng |
|----|------------|----------|-----------------------------|-----------|--------------|-----------------------------|----------|
| CAP-process-score-01 | Một điểm quy trình cho mỗi buổi tối, từ **năm trục chỉ-về-quy-trình** | P0 | Lõi feature. Trọng số cộng lại đúng 1.00; không con số kết quả nào tham gia | UN-001 | ~8 | Người chơi đọc được một con số cho buổi tối mà **thị trường không quyết hộ** | ✅ |
| CAP-process-score-02 | **Tối đứng ngoài đúng lúc không bao giờ chấm thấp hơn** tối giao dịch tốt cùng mức chuẩn bị | P0 | **Đây là tính chất phải giữ, không phải hệ quả tình cờ.** Mọi capability khác tồn tại để bảo vệ nó | UN-002 | ~5 | Tape chết + chuẩn bị đầy đủ chấm **100**; tối giao dịch tốt với một luật hụt và một lần bắn thiếu SL chấm **98** | ✅ |
| CAP-process-score-03 | Trục thiếu bằng chứng **rơi khỏi công thức**, trọng số còn lại chia lại | P0 | Không có nó thì CAP-02 bất khả thi: chấm 0 là phạt việc đứng ngoài, chấm 100 là cho điểm miễn phí | UN-003 | ~6 | Trục không có mẫu số hiện thành **vòng gạch đứt "không áp dụng"**, không phải nan quạt bằng 0 | ✅ |
| CAP-process-score-04 | Điểm **chốt ngay khi đóng phiên**; không có điểm sống để canh | P0 | Đây là cơ chế chống **rủi ro số một**: điểm thay chỗ lãi lỗ làm nỗi lo mới | UN-004 | ~5 | Không tồn tại điểm tạm thời; điểm **không bao giờ xuất hiện trên màn hình chính** lúc đang giao dịch | ✅ |
| CAP-process-score-05 | Deck mở ở **panel quy trình**; tiền sau một cú bấm có chủ ý | P0 | Chữ ký của cả sản phẩm. Một con số tiền lọt vào panel quy trình là đủ phá lời hứa | UN-006 | ~6 | **Không đồng nào** nhìn thấy được trước cú bấm đó — kể cả trong radar, các bảng, và thông báo | ✅ |
| CAP-process-score-06 | Lưu **đầu vào của từng trục**, không chỉ điểm tổng | P0 | **Không backfill được về sau.** Không lưu từ ngày đầu thì đổi trọng số không tính lại được và không con số nào truy ngược được | UN-009 | ~5 | Đổi trọng số thì lịch sử **tính lại từ chính các đầu vào đã lưu**; mọi con số trên deck đối chiếu được | ✅ |
| CAP-process-score-07 | Điểm là **hàm thuần trên bản ghi**; không mô hình ngôn ngữ nào tính một con số hiện trên deck | P0 | Điều kiện để người chơi tin con số. Copilot chỉ được **kể lại** những con số deck đã tính | UN-010 | ~3 | Cùng một dữ liệu **luôn** cho ra cùng một điểm | ✅ |
| CAP-process-score-08 | Ghi lại **mỗi lần mở deck giữa lúc phiên còn chạy** | P0 | **Không backfill được.** Đây là số liệu duy nhất đo rủi ro số một; không ghi từ ngày đầu thì USC-001 không bao giờ đo được | URD Mục 3 | ~2 | Rủi ro lớn nhất của feature **có nguồn số để canh chừng** ngay từ phiên đầu tiên | ✅ |
| CAP-process-score-09 | Biểu đồ radar năm trục | P1 | Biết **yếu ở trục nào**, không chỉ biết một con số — nhưng hình thức thể hiện chưa chốt | UN-007 | ~4 | Đông cứng trong tape giàu cơ hội (**70**) đọc ra khác hẳn giao dịch quá tay trong tape chết (**65**), và **chính tên trục nói ra sự khác nhau** | ⚠️ chờ OQ-5 (radar hay bảng năm dòng) |
| CAP-process-score-10 | **Trần** phần cộng điểm cho việc tự huỷ | P1 | Chống farm điểm; chỉ cần khi người chơi đã có thói quen vũ trang rồi huỷ | UN-008 | ~3 | Huỷ hàng chục lần **cũng không mua thêm được điểm nào**; trục chọn lọc không vượt quá 100 | ⚠️ chờ OQ-3 (danh sách "điều kiện đứng ngoài") |
| CAP-process-score-11 | Mẫu ít thì **nói thẳng là mẫu ít** | P1 | Một con số tự tin dựng trên mẫu quá nhỏ còn tệ hơn không có số; nhưng chỉ có nghĩa sau vài tháng | UN-011 | ~3 | Chỉ số cần mẫu lớn hiện **"chưa đủ phiên"** khi dưới ngưỡng, và **luôn in kèm cỡ mẫu** | ✅ |
| CAP-process-score-12 | Bảng thống kê theo playbook | P1 | Trả lời "cách chơi nào thực sự sinh lợi thế"; cần vài tháng dữ liệu mới có nghĩa | UN-012 | ~5 | So sánh được các playbook: **con số quy trình mặc định, con số kết quả sau cùng cú bấm** | ✅ |
| CAP-process-score-13 | Tháng này so tháng trước, trên số liệu quy trình | P1 | **Đây là câu trả lời chính cho "tôi có đang khá lên không"** — nhưng cần ít nhất hai tháng dữ liệu | UN-013 | ~5 | Người chơi đọc được chênh lệch trên mức tuân thủ, tỷ lệ từ chối, điểm tự chấm — và **phân bố điểm kèm số phiên** | ✅ |
| CAP-process-score-14 | Tilt hiện như **hồi tưởng của buổi tối**, không phải lời phán xét | P1 | Giải thích chứ không trừng phạt; và ranh giới "tilt không vào điểm" đã nằm trong CAP-01 nên không chờ cái này | UN-014 | ~4 | Các dải trạng thái đối chiếu với **mức tuân thủ**, không đối chiếu với lãi lỗ | ✅ |
| CAP-process-score-15 | Không trừ điểm vì một tính năng người chơi **chủ động không dùng** | P1 | Công bằng cơ bản; nhưng chỉ phát sinh khi đã có tính năng để tắt | UN-015 | ~3 | Tiểu mục dựa vào memo **rơi khỏi trục và trục chuẩn hoá lại** khi ghi âm bị tắt. **Nhưng nếu sẵn sàng mà bỏ qua thì vẫn là thiếu sót thật** | ✅ |
| CAP-process-score-16 | Deck **mở bằng tay cầm**, đọc bằng chuột và bàn phím | P1 | Mở được ngay khi rời tay cầm là tiện lợi thật; nhưng đây là màn nhìn lại, không phải thao tác nhanh | UN-016 | ~3 | Người chơi mở deck **không phải rời tay đi tìm chuột**; việc đọc bảng và lọc thì dùng chuột | ✅ |
| CAP-process-score-17 | Copilot huấn luyện được **một trục có tên** | P2 | Giá trị cao nhưng phụ thuộc `ai-desk`; và deck vẫn hữu ích khi tự đọc | UN-017 | ~3 | Copilot trả lời dựa trên **chính các trục deck đã tính**, và vẫn **không có công cụ ghi hay đặt lệnh nào** | ⚠️ phụ thuộc `ai-desk` |

> **Tám P0, và nguyên tắc chọn chúng khác các feature trước.** Ở đây tiêu chí không phải "đủ để launch v1"
> mà là **"cái gì không backfill được về sau"**. CAP-06 (lưu đầu vào từng trục) và CAP-08 (ghi lần mở deck
> giữa phiên) đều rẻ, đều không phải tính năng người chơi nhìn thấy — nhưng **không lưu từ ngày đầu thì mất
> vĩnh viễn**: đổi trọng số không tính lại được, và rủi ro số một của feature không bao giờ đo được. Sáu cái
> còn lại là điểm số cộng tính chất trung tâm cộng hai ranh giới bảo vệ nó.
>
> **Lưu ý về "không cộng dồn xuyên phiên" (UN-005).** Nó **không** xuất hiện ở đây như một capability vì nó
> là một **điều không được xây** — nó sống ở tầng ràng buộc (NFR/BR), nơi nó thực sự được thi hành, chứ
> không phải ở danh sách việc cần làm.

## 5. Upstream Traceability

| Capability | Traces to | Product outcome | Success metric |
|------------|-----------|-----------------|----------------|
| CAP-01, CAP-07 | UN-001, UN-010 | Một thước đo mà thị trường không quyết hộ | M2 Điểm quy trình trung bình |
| CAP-02, CAP-03 | UN-002, UN-003 | Đứng ngoài đúng lúc được ghi nhận là một quyết định | — (tính chất tuyệt đối, kiểm bằng checkpoint J2) |
| CAP-04, CAP-08 | UN-004 | Điểm **không trở thành nỗi lo mới** thay chỗ lãi lỗ | M1 Số lần mở deck giữa phiên |
| CAP-05 | UN-006 | Quy trình đứng trước tiền ở deck | — (ranh giới nhị phân) |
| CAP-06 | UN-009 | Mọi con số truy ngược được; đổi trọng số thì lịch sử tính lại | M2 (vế "cùng một bộ trọng số") |
| CAP-09, CAP-13 | UN-007, UN-013 | Biết yếu ở trục nào, và có khá lên không | M2 |
| CAP-10 | UN-008 | Tự kiềm chế được cộng điểm nhưng **không farm được** | M2 (chống thổi điểm) |
| CAP-11 | UN-011 | Không tin một con số tự tin dựng trên mẫu quá nhỏ | M2 (đọc kèm số phiên) |
| CAP-12 | UN-012 | Biết cách chơi nào thực sự sinh lợi thế | — |
| CAP-14, CAP-15 | UN-014, UN-015 | Tilt giải thích chứ không trừng phạt; không bị trừ điểm vì tính năng chủ động không dùng | — (checkpoint chung với `tilt-meter`) |
| CAP-16, CAP-17 | UN-016, UN-017 | Mở deck không rời tay cầm; được huấn luyện đúng trục yếu | M3 Điểm tự chấm cuối buổi |

## 6. Key Capability Interactions

* **Chốt điểm:** phiên đóng → CAP-04 chốt **lặng lẽ**, không có gì bật ra → CAP-01 gộp năm trục → CAP-03 loại
  trục thiếu bằng chứng và chia lại trọng số → CAP-06 lưu **đầu vào từng trục**, không chỉ điểm tổng.
* **Đọc deck:** người chơi tự mở (CAP-16, bằng tay cầm từ menu an toàn) → CAP-05 mở ở panel quy trình →
  CAP-09 hiện radar → muốn xem tiền thì bấm sang tab kết quả.
* **Mở deck giữa phiên:** **không bị chặn** — nhưng CAP-08 ghi lại mỗi lần, và **buổi hôm nay chưa tồn tại
  trên deck** cho tới khi đóng phiên (CAP-04). Vì deck mở từ menu an toàn, việc mở nó **huỷ ARM và khoá mở
  lệnh mới** (luật `order-execution`), và màn hình nói rõ điều đó ngay lúc mở.
* **Đổi trọng số:** bộ mới phải cộng đúng 1.00, nếu không **hệ thống không chạy** → CAP-06 cho phép tính lại
  toàn bộ lịch sử từ đầu vào đã lưu → CAP-13 vẫn so sánh được các tháng vì mọi tháng dùng **cùng một thước**.
* **Bảy nguồn bằng chứng:** tuân thủ ← `playbook-grading` · chọn lọc ← `ai-desk` + `order-execution` · kỷ
  luật rủi ro ← `order-execution` · chuẩn bị ← `daily-journal` + `playbook-grading` + `voice-journal` ·
  nhìn lại ← `daily-journal` + `voice-journal` + `trade-replay` + `playbook-grading`.
* **Tilt là ngoại lệ có chủ ý:** `tilt-meter` là nguồn thứ tám, nhưng nó **chỉ được đọc để kể lại buổi tối**
  (CAP-14) — **nó không đi vào phép gộp**, và tập "điều kiện đứng ngoài" của CAP-10 **không bao gồm mức tâm
  lý**, để tilt không lọt vào điểm qua cửa sau.

## 7. Success Metrics

| Metric | Baseline | Target | Measurement Method | Timeframe |
|--------|----------|--------|--------------------|-----------|
| M1 Số lần mở deck giữa phiên | Chưa có — xác lập số lần mở giữa phiên **và** số lệnh trung bình mỗi tối từ 10 phiên đầu | **Không tăng theo tháng**, đồng thời số lệnh trung bình mỗi tối không tăng khi chất lượng cơ hội trung bình không đổi. **Chưa có ngưỡng tuyệt đối và cố ý chưa đặt** — để phân bố 10 phiên đầu tự nói | Deck ghi lại mỗi lần mở khi phiên còn chạy (CAP-08); đọc cuối tháng, **đặt cạnh số lệnh trung bình và chất lượng cơ hội trung bình**. Đọc kèm **tỷ lệ phiên có mở deck sau khi đóng phiên** — tỷ lệ này tụt về 0 thì M1 đẹp vì **bỏ bê** chứ không phải vì bình tĩnh | Đọc hằng tháng, kết luận hằng quý |
| M2 Điểm quy trình trung bình | Chưa có — xác lập từ 10 phiên đầu | Cao hơn mốc gốc sau 3 tháng, **đồng thời mọi tháng đem so đều đã được tính lại bằng cùng một bộ trọng số** | Đọc điểm trung bình theo tháng kèm **số phiên** và **phiên bản trọng số đang dùng**. Đổi trọng số giữa kỳ thì **so lại toàn bộ lịch sử bằng bộ mới trước khi kết luận** | Đọc hằng tháng, kết luận hằng quý |
| M3 Điểm tự chấm cuối buổi | Chưa có — xác lập từ 10 phiên đầu | Cao hơn mốc gốc sau 3 tháng, **đọc cạnh điểm quy trình chứ không cạnh lãi lỗ** | Đọc trung bình theo tháng, kèm **tỷ lệ phiên có tự chấm** — tỷ lệ này tụt thì con số trung bình mất ý nghĩa (chỉ còn những tối thấy vui mới buồn bấm) | Đọc hằng tháng, kết luận hằng quý |

> **M1 và M2 kéo ngược nhau, và đó là chủ ý.** M2 muốn điểm đi lên; M1 canh chừng đúng cái giá phải trả nếu
> người chơi bắt đầu **đuổi theo con số đó**. **Phải đọc cùng nhau** — M2 đạt trong khi M1 xấu đi thì feature
> đang **thất bại** chứ không phải thành công.
>
> **M3 là thước đo cấp sản phẩm** ("người chơi tự tin và vui hơn"), feature này **đọc hộ**, không truy về một
> nhu cầu riêng của nó.
>
> **Giới hạn đã biết.** Cả ba đọc từ chính dữ liệu do sản phẩm sinh ra, nên chúng đo *sự nhất quán của quy
> trình*, không đo *chất lượng của quy trình*. M2 chặn được việc **nới trọng số** (vế "cùng một bộ trọng
> số"), nhưng **không** chặn được việc **hạ chuẩn ở tầng dưới** — nới luật playbook làm trục tuân thủ đẹp
> lên. Vế phòng thủ cho việc đó nằm ở `playbook-grading` SC-02, và **hai thước đo cần đọc cùng nhau**.
>
> **Lá chắn của M2 chưa phủ hết.** Trục chọn lọc phụ thuộc **số lệnh kỳ vọng và độ rộng dải** — cấu hình
> riêng của feature này, **không phải trọng số** — nên nới chúng vẫn là một đường làm đẹp điểm mà vế "cùng
> một bộ trọng số" **không chặn được**. Xem OQ-2.

## 8. Dependencies

> Bảng "năm trục dựng trên bằng chứng của feature nào" là **căn cứ đọc toàn bộ mục này**. Feature này
> **không sinh dữ liệu của riêng nó** (trừ bản ghi mở deck giữa phiên), nên mọi phụ thuộc dưới đây đều là
> phụ thuộc **nội dung**, không phải phụ thuộc hạ tầng.

| Dependency | Owner | Status | Needed-by | Impact if Late |
|------------|-------|--------|-----------|----------------|
| Kết quả chấm luật playbook mỗi lần bắn → **trục tuân thủ** | `playbook-grading` | At Risk | Cùng lúc CAP-01 | Trục tuân thủ rơi khỏi công thức (CAP-03 xử lý được) |
| Kết quả kiểm hạn mức tại mỗi lần bắn → **trục kỷ luật rủi ro** | `order-execution` | On Track | Cùng lúc CAP-01 | Như trên |
| Chỉ số chất lượng cơ hội, **ghi lại suốt phiên để lấy trung bình** → **trục chọn lọc** | `ai-desk` (FR-048) | **At Risk** | Cùng lúc CAP-01 | **Trục làm nên toàn bộ tính chất "đứng ngoài chấm tốt" mất đầu vào** — xem OQ-4 |
| Bộ đếm tự huỷ **kèm cờ điều kiện đứng ngoài** | `order-execution` (FR-049) | On Track | Cùng lúc CAP-10 | Không quy được điểm cho việc tự huỷ |
| Kế hoạch đã xác nhận trước lệnh đầu · tự chấm đầu buổi → **trục chuẩn bị** | `daily-journal` (FR-009, FR-013) | **At Risk** | Cùng lúc CAP-01 | **Ngày ra mắt deck chỉ có 3/5 trục** — xem OQ-1 |
| Tự chấm cuối buổi · memo · đã mở replay · checklist đã trả lời → **trục nhìn lại** | `daily-journal` · `voice-journal` · `trade-replay` · `playbook-grading` | **At Risk** | Cùng lúc CAP-01 | Như trên |
| Bản ghi **"lệnh nào đã xem lại, lúc nào"** | `trade-replay` (FR-049) | At Risk | Cùng lúc CAP-01 | Tiểu mục "đã mở replay" của trục nhìn lại rơi ra |
| Dữ liệu hồi tưởng tilt (dải trạng thái, nguyên nhân chính) | `tilt-meter` (FR-047, FR-048) | At Risk | Cùng lúc CAP-14 | CAP-14 lùi lại; **điểm không đổi**, vì tilt vốn không phải đầu vào |
| Menu an toàn làm chỗ mở deck bằng tay cầm | `order-execution` (FR-052) | On Track | Cùng lúc CAP-16 | Deck chỉ mở được bằng chuột |
| Copilot đọc được các trục | `ai-desk` | At Risk | Cùng lúc CAP-17 | CAP-17 đã ở P2 nên không ảnh hưởng lịch |
| **Quyết định danh sách "điều kiện đứng ngoài"** | Người chơi | **Blocked** | Trước khi CAP-10 vào Next | Không biết quy điểm cho lần huỷ nào — xem OQ-3 |

## 9. Assumptions & Validation

| Assumption | Impact if Wrong | Validation | Status |
|------------|-----------------|------------|--------|
| Số lệnh tối đa kỳ vọng và độ rộng dải hợp với nhịp giao dịch thật của người chơi này | Trục chọn lọc hoặc **luôn dính 100**, hoặc **không bao giờ với tới** — trục quan trọng nhất mất tác dụng phân biệt | Cả hai là cấu hình và đầu vào đều được lưu; đọc lại sau tháng đầu rồi hiệu chuẩn | Open (URD A-01 → OQ-2) |
| Chỉ số chất lượng cơ hội quy về được thang 0–1 **có cơ sở**, không cần hằng số tuỳ tiện | Trục chọn lọc hạ xuống ba mức thô; độ phân giải giảm nhưng tính chất "đứng ngoài chấm tốt" vẫn giữ. **Thêm một điều kiện chưa ai nhận:** trục này cần chỉ số **trung bình cả phiên**, mà `ai-desk` mới cam kết *hiện nhãn mức* | Chốt khi `ai-desk` có sản phẩm; ghi rõ trong cấu hình đang dùng cách nào | Open (URD A-02 → OQ-4) |
| Người chơi chấp nhận **một con số duy nhất** làm thước đo buổi tối, và nó **không thay chỗ lãi lỗ làm nỗi lo mới** | **Toàn bộ cơ chế phản tác dụng** — feature sinh ra để chữa lo âu lại tạo ra một nguồn lo âu mới | Theo dõi M1 trong 10 phiên đầu; tăng dần thì **đặt lại thiết kế** | Open (URD A-03 — rủi ro số một) |
| Điểm tự chấm đầu/cuối buổi **do feature khác thu**; deck chỉ hiển thị | Deck cần một luồng nhập liệu — **mở rộng phạm vi đáng kể và vi phạm nguyên tắc "không luồng thu thứ hai"** | Xác nhận ranh giới với `daily-journal` | Open (URD A-04) |
| Bốn trục quy trình có đủ bằng chứng **tại thời điểm bắn**, nên điểm chốt được ngay khi đóng phiên | Nếu một trục thật sự cần lệnh đóng mới chấm được, **điểm sẽ chốt bằng dữ liệu thiếu** | **Soát từng tiểu mục của năm trục**; cái nào cần lệnh đóng thì tách ra như con số kết quả | Partially confirmed (URD A-05 — cách xử lý chốt 2026-08-28, từng tiểu mục thì chưa soát) |
| Khi người chơi bắt đầu dùng deck thật, **bảy nguồn bằng chứng đã có mặt** | Giữ thứ tự kế hoạch hiện tại thì `daily-journal` ra **sau** feature này, nên **ngày ra mắt deck chỉ có 3/5 trục** (chuẩn bị 0.15 + nhìn lại 0.10 = **25% trọng số rơi ra**). Đó là **trạng thái mặc định lúc ra mắt, không phải tình huống hiếm** | Hoặc đổi thứ tự để `daily-journal` ra trước, hoặc chấp nhận và để deck nói rõ điểm dựa trên mấy trục | Open (URD A-06 → OQ-1) |
| Trục tuân thủ đọc **đúng bộ luật mà gateway đã thi hành**, không có định nghĩa thứ hai | Deck báo một lệnh phá luật mà gateway đã cho qua — **người chơi mất niềm tin vào cả hai** | Đối chiếu với `order-execution` và `playbook-grading` | Open (URD A-07) |
| Ngưỡng "bao nhiêu lần mở deck giữa phiên là đáng lo" **tự lộ ra từ mốc gốc 10 phiên đầu** | Đặt sai ngưỡng thì M1 hoặc báo động giả liên tục, hoặc không bao giờ kêu | Đọc phân bố sau 10 phiên đầu **rồi mới** đặt ngưỡng | Confirmed cách lấy số (URD A-08); ngưỡng **cố ý chưa đặt** |
| Tập "điều kiện đứng ngoài" dùng để quy điểm **không bao gồm mức tâm lý** | Tilt đi vào trục chọn lọc **qua cửa sau**: cùng một lần huỷ, tâm lý cao thì được cộng điểm, tâm lý thấp thì không. Lời hứa "tilt không bao giờ là đầu vào" **sẽ sai** | **Cái giá đã chấp nhận:** tự huỷ *vì biết mình đang nóng* — hành vi kỷ luật nhất — **không được cộng điểm chọn lọc**, trừ khi cùng lúc có hoàn cảnh khác | **Chốt** 2026-08-28 (URD A-09) — người chơi chọn giữ lời hứa |
| Câu trả lời checklist muộn **không** làm tính lại điểm đã chốt | Cùng một buổi tối cho **hai con số khác nhau** tuỳ lúc đọc — phá đúng tính chất "chốt ngay khi đóng phiên" | Xác nhận cùng `playbook-grading` | Open (URD A-10 🔶) |

## 10. Product Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| **Điểm trở thành nỗi lo mới thay chỗ lãi lỗ** | High | **Rất cao** | Đây là **rủi ro số một**. CAP-04 (không có điểm sống, không hiện trên HUD) là cơ chế chính; CAP-08 là số liệu canh chừng. **M1 và M2 phải đọc cùng nhau** | Người chơi |
| **Deck ra mắt với 3/5 trục** vì `daily-journal` ra sau | High | High | Hoặc đổi thứ tự phát hành, hoặc chấp nhận và **để deck nói rõ điểm đang dựa trên mấy trục** — để người chơi không đọc nhầm một con số mỏng thành một đánh giá đầy đủ. Xem OQ-1 | Người chơi |
| Nới **số lệnh kỳ vọng / độ rộng dải** để làm đẹp điểm — mà M2 không chặn được | Medium | High | Vế "cùng một bộ trọng số" **chỉ phủ trọng số**, không phủ cấu hình trục chọn lọc. Cần một lá chắn riêng — xem OQ-2 | Người chơi |
| Trục chọn lọc mất đầu vào vì `ai-desk` chỉ hiện nhãn mà **không ghi lại** chỉ số suốt phiên | Medium | High | `ai-desk` FR-048 đã nhận nghĩa vụ ghi lại. Nếu không, lùi về **ba mức thô** và ghi rõ trong cấu hình — công thức không đổi, chỉ độ phân giải giảm | Người chơi |
| Trục tuân thủ dựng một **định nghĩa thứ hai** khác với bộ luật gateway đã thi hành | Medium | High | Một bộ luật, **nhập từ `order-execution`**, không tự cài lại. Deck báo lệnh phá luật mà gateway cho qua thì mất niềm tin vào cả hai | Người chơi |
| Số liệu tiền trên deck lệch với tài khoản trên sàn | Medium | Medium | Deck **luôn lấy con số của sàn làm chuẩn**, không tự dựng lại từ các lần khớp; lệch thì **nói rõ đang lệch và chỉ về sàn** | Người chơi |
| Không lưu đầu vào từng trục từ ngày đầu → không backfill được | Low | **Rất cao** | CAP-06 ở P0 chính vì lý do này. Không lưu thì đổi trọng số **không bao giờ** tính lại được cho quá khứ | Người chơi |

## 11. Release & Launch Readiness

### 11.1 Release Horizon

| Horizon | Capabilities | Target | Status |
|---------|--------------|--------|--------|
| Now | CAP-process-score-01 → 08 (P0) | Chưa chốt lịch | **CAP-01 chỉ có 3/5 trục nếu ra trước `daily-journal`** — xem OQ-1 |
| Next | CAP-process-score-11 → 16 (P1) | Chưa chốt lịch | planned |
| Next (khoá) | CAP-process-score-09, 10 (P1) | Chưa chốt lịch | CAP-09 chờ OQ-5, CAP-10 chờ OQ-3 |
| Later | CAP-process-score-17 (P2) | Chưa chốt lịch | phụ thuộc `ai-desk` |

> **Feature này ship sau bảy feature nguồn — nhưng "sau" không có nghĩa là "đủ".** Với thứ tự kế hoạch hiện
> tại, `daily-journal` ra sau deck, nên **ngày ra mắt deck có 25% trọng số rơi ra**. Đó là trạng thái mặc
> định, không phải tình huống hiếm.

### 11.2 Launch Readiness

| Workstream | Must-pass criteria | Status | Guardrail metric (threshold → decision) |
|------------|--------------------|--------|-----------------------------------------|
| Tính chất trung tâm | Dựng hai buổi **cùng mức chuẩn bị và nhìn lại**: A (tape chết, không lệnh) phải chấm **100**; B (tape bình thường, một luật hụt + một lần bắn thiếu SL) phải chấm **98**. Rồi kiểm rộng: **mọi** cặp buổi cùng mức chuẩn bị, buổi đứng ngoài **không bao giờ chấm thấp hơn** | ⬜ | Một cặp vi phạm → **dừng dùng điểm** cho tới khi sửa; đây là lý do tồn tại của cả feature |
| Không có điểm sống | Trong lúc phiên còn chạy, rà màn hình chính và deck | ⬜ | Điểm xuất hiện ở đâu đó giữa phiên → gỡ ngay; đó chính là rủi ro số một thành hiện thực |
| Tiền sau một cú bấm | Mở deck và **không bấm gì** — rà toàn màn hình, kể cả radar, các bảng, và thông báo | ⬜ | Một con số tiền lọt vào panel quy trình → sửa trước khi dùng |
| Trục rỗng đọc đúng | Buổi không lệnh nào: trục tuân thủ và kỷ luật rủi ro hiện **vòng gạch đứt "không áp dụng"**, **không phải nan quạt bằng 0** | ⬜ | Hiện thành 0 → phạt việc đứng ngoài; sửa trước khi dùng |
| Tilt không vào điểm | **Ép chỉ số tâm lý lên mức quá nóng** trong khi giữ nguyên mọi hành vi đặt lệnh — điểm quy trình **không đổi** | ⬜ | Điểm đổi → tách tilt khỏi mọi đầu vào. **Checkpoint chung với `tilt-meter`** — không feature nào sở hữu nó một mình |
| Trọng số hợp lệ | Đặt bộ trọng số cộng lại **không** bằng 1.00 | ⬜ | Hệ thống phải **không chạy** và nói rõ vì sao. **Âm thầm tự chuẩn hoá là sai** — người chơi sẽ tin vào một thước đo khác với thứ mình nghĩ mình đã đặt |
| Tính lại lịch sử | Ghi điểm một buổi cũ → đổi trọng số → mở lại buổi đó | ⬜ | Điểm không đổi theo công thức mới → CAP-06 chưa lưu đủ đầu vào; sửa **ngay**, vì không backfill được |
| Không cộng dồn | Rà toàn deck tìm chuỗi ngày, cấp độ, huy hiệu, "đã bao nhiêu ngày kể từ" | ⬜ | Tìm thấy bất kỳ thứ nào → gỡ; nó tạo áp lực không được bỏ một tối nào |
| Mẫu nhỏ nói thẳng | Dựng một tháng chỉ có 2 phiên | ⬜ | Chỉ số cần mẫu lớn ra một con số thay vì "chưa đủ phiên" → sửa |

## 12. Open Questions

* [ ] **OQ-1** *(kế thừa URD A-06, chung với `daily-journal` OQ-6)*: `daily-journal` ra **trước hay sau**
  feature này? Với thứ tự hiện tại, deck ra mắt với **3/5 trục** (25% trọng số rơi ra) — **trạng thái mặc
  định, không phải tình huống hiếm**.
  🔶 **Tạm quyết:** chấp nhận ra mắt 3/5 trục, và **deck nói rõ điểm đang dựa trên mấy trục**.
  *Nếu sai:* nên đổi thứ tự để `daily-journal` ra trước — nhưng đó là quyết định lịch, không phải quyết định
  thiết kế.
* [ ] **OQ-2** *(kế thừa URD OQ-7)*: Hiệu chuẩn lại **số lệnh kỳ vọng và độ rộng dải** — làm khi nào và dựa
  trên bao nhiêu phiên? Đổi giữa chừng thì các tháng cũ có được tính lại như khi đổi trọng số không?
  **Đây là lỗ hổng M2 không chặn được**: nới hai con số này là một đường làm đẹp điểm mà vế "cùng một bộ
  trọng số" không phủ tới.
* [ ] **OQ-3** *(kế thừa URD OQ-10)*: Danh sách đóng **"điều kiện đứng ngoài"** dùng để quy điểm gồm đúng
  những hoàn cảnh nào — sắp có tin, chênh lệch giá vượt trần, ngoài khung giờ, không playbook nào đủ luật?
  **Mức tâm lý đã bị loại** (đã chốt). Câu còn lại là bốn hoàn cảnh kia đã đủ chưa. **Chặn CAP-10.**
* [ ] **OQ-4** *(kế thừa URD OQ-11, `ai-desk` đã trả lời)*: `ai-desk` có **ghi lại** chỉ số chất lượng cơ hội
  suốt phiên không? Trục chọn lọc cần **mức trung bình cả phiên**.
  🔶 **Tạm quyết:** `ai-desk` FR-048 **đã nhận nghĩa vụ ghi lại**. Nếu không có, lùi về **ba mức thô** và ghi
  rõ trong cấu hình — công thức không đổi, chỉ độ phân giải giảm.
  *Nếu sai:* trục chọn lọc — **trục làm nên toàn bộ tính chất "đứng ngoài chấm tốt"** — rơi khỏi công thức.
* [ ] **OQ-5** *(kế thừa URD OQ-12)*: Hình thức thể hiện năm trục — **biểu đồ radar** (theo nguồn) hay **một
  bảng năm dòng** có cùng thông tin? Với một người dùng, bảng rẻ hơn nhiều. **Chặn CAP-09**; chốt lúc vẽ
  wireframe.
* [ ] **OQ-6** *(kế thừa URD OQ-9, chung với `daily-journal` OQ-3)*: Feature này có cung cấp điểm ở mức
  **buổi tối** không, hay chỉ mức **phiên**? Nguồn chỉ định nghĩa điểm theo phiên. Một buổi có hai phiên trở
  lên thì bản đồ nhiệt của `daily-journal` phải tô bằng một con số — **quy tắc gộp nhiều phiên thành một ô
  thuộc feature nào?**
* [ ] **OQ-7** *(kế thừa URD A-05)*: Soát **từng tiểu mục của năm trục** — cái nào thật sự chấm được tại
  **thời điểm bắn**, cái nào cần lệnh đóng? Cách xử lý đã chốt (chốt ngay khi đóng phiên), nhưng **từng tiểu
  mục thì chưa soát**. Cái nào cần lệnh đóng phải **tách ra như một con số kết quả**.
* [ ] **OQ-8** *(kế thừa URD A-10, chung với `playbook-grading`)*: Câu trả lời checklist tự-đánh-giá **muộn**
  có làm tính lại điểm đã chốt không?
  🔶 **Tạm quyết:** **không**. Câu trả lời muộn làm giàu bản ghi của **lệnh**, không đụng tới điểm của
  **buổi** — nhất quán với `playbook-grading` FR-043.
  *Nếu sai:* cùng một buổi tối cho hai con số khác nhau tuỳ lúc đọc.
* [ ] **OQ-9** *(chung với `daily-journal` OQ-9 và `trade-replay` OQ-6)*: Những lần **tự huỷ không dẫn tới
  lệnh nào** hiện ở đâu? **Cần chốt một lần cho cả ba tài liệu.**

---

> **Nguồn:** `process-score-urd.md` (17 nhu cầu, 8 journey, 21 tình huống ngoại lệ, 3 thước đo, 10 giả định) ·
> bốn tài liệu nền `docs/_shared/` · bằng chứng đọc từ **bảy** feature: `playbook-grading`, `ai-desk`,
> `order-execution`, `daily-journal`, `voice-journal`, `trade-replay`, `playbook-grading` — cộng
> `tilt-meter` như nguồn thứ tám **chỉ để kể lại, không vào phép gộp**. **Chưa có BRD**.
>
> **🔶 Ba quyết định thay user:** OQ-1 (chấp nhận ra mắt 3/5 trục), OQ-4 (lùi về ba mức thô nếu thiếu),
> OQ-8 (câu trả lời muộn không tính lại điểm buổi). **OQ-3 và OQ-6 em cố ý không quyết** — cái đầu là một
> danh sách nghiệp vụ đóng, cái sau chạm ranh giới với `daily-journal`.
