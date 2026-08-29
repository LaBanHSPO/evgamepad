---
type: prd
feature: reports-export
status: draft
updated: 2026-08-29
links:
  - docs/reports-export/reports-export-urd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/process-score/srs/process-score-spec.md
  - docs/daily-journal/srs/daily-journal-spec.md
  - docs/voice-journal/srs/voice-journal-spec.md
  - docs/trade-replay/srs/trade-replay-spec.md
---

# reports-export — Product Requirements Document

## 1. Product Overview

`reports-export` là **lối ra của dữ liệu** — và **lối vào duy nhất được phép đổi cấu hình**.

Tám feature kia sinh ra dữ liệu; feature này là nơi duy nhất dữ liệu đó **rời khỏi màn hình**: một báo cáo
đọc được cho cả một tháng, một bản xuất mang đi được, một gói sao lưu để sống sót qua một ổ đĩa hỏng, và một
đường xoá sạch có chủ ý. Kèm theo là **màn cài đặt an toàn** — nơi đổi được biểu tượng, khung giờ, hiệu
chỉnh tay cầm, rung, micro và mặc định báo cáo, mà **không chạm được vào bất kỳ chốt an toàn nào**.

**Điểm mấu chốt: đây là feature duy nhất chạm được toàn bộ dữ liệu sản phẩm cùng một lúc.** Nên nó cũng là
feature duy nhất có thể **làm mất sạch** hoặc **làm rò rỉ hết**. Hai nghĩa vụ của nó **kéo ngược nhau và cả
hai đều phải giữ**: *mang dữ liệu ra thật dễ*, và *không bao giờ mang theo bí mật, không bao giờ xoá nhầm*.

**Gap neo:** Hiện tại không có gì cầm ra khỏi màn hình — một tháng đã qua không để lại bản chụp nào để so
với tháng sau. Toàn bộ nhật ký nằm trên **một** VPS và **giữ vô hạn**, nên **không có bản sao thứ hai của
bất cứ thứ gì**: một ổ đĩa hỏng xoá sạch nhiều tháng bằng chứng về chất lượng quyết định — đúng thứ tài sản
mà cả sản phẩm này tồn tại để tích luỹ. Và đổi một preference vô hại phải SSH vào máy chủ sửa đúng tệp chứa
các chốt an toàn.

> **Feature này không tính bất kỳ con số nào của riêng nó.** Báo cáo **render lại** đúng những con số
> `process-score` và `daily-journal` đã chốt; nó không dựng một định nghĩa thứ hai cho mức tuân thủ, điểm
> quy trình hay bất kỳ số liệu nào. **Lệch nghĩa là báo cáo sai, không phải deck sai.**

## 2. Goals

### 2.1 Goals

* **Không tệp nào rời khỏi sản phẩm mang theo bí mật** — không giá trị biến môi trường, không token, không
  cấu hình gốc, không đường dẫn tuyệt đối (trace UN-007, UN-010, USC-001).
* **Gói sao lưu thật sự khôi phục được**, không chỉ tạo ra được — *một gói chưa từng khôi phục thử thì chưa
  phải một bản sao lưu* (trace UN-008..013, USC-002).
* **Bản xuất tự đủ nghĩa** để một trợ lý AI ngoài chưa biết gì về sản phẩm đọc và trả lời được câu hỏi dài
  hạn (trace UN-005, USC-003).
* **Những thứ không được phép xuất hiện thì không bao giờ xuất hiện**: con số tiền khi không tích phụ lục ·
  chốt an toàn trong màn cài đặt · nội dung nhật ký sau khi xoá sạch (trace UN-003, UN-019, UN-016, USC-004).
* **Khôi phục hỏng thì dữ liệu hiện tại không suy suyển** (trace UN-012).
* **Không thể xoá nhầm bằng một cú bấm** (trace UN-014).

### 2.2 Non-goals

* **KHÔNG** nhập lịch sử giao dịch từ cTrader, MT5 hay bất kỳ công cụ nào — **dứt khoát không tồn tại**.
  Khôi phục chỉ nhận **gói sao lưu do chính sản phẩm này tạo ra**.
* **KHÔNG** tính toán bất kỳ số liệu nào → `process-score` và `daily-journal`. Báo cáo **render lại** con số
  đã chốt.
* **KHÔNG** đổi bất kỳ **chốt an toàn** nào: chế độ demo/thật, thông tin đăng nhập sàn, địa chỉ lắng nghe,
  quyền công cụ của AI, trọng số các trục điểm. Chúng sống **ngoài cơ sở dữ liệu**, sai thì sản phẩm không
  khởi động, và **cố tình không có mặt trong giao diện**.
* **KHÔNG** sửa luật playbook (`playbook-grading`) hay triết lý và nguyên tắc cá nhân (`daily-journal`) —
  cài đặt chỉ **dẫn sang** trình sửa của feature sở hữu, **không dựng bản sao thứ hai**.
* **KHÔNG** xoá riêng dữ liệu giọng nói → `voice-journal` có đường xoá riêng. Đường xoá sạch ở đây xoá **mọi
  thứ**, bao gồm cả giọng nói.
* **KHÔNG** gỡ một ảnh hoặc một ghi chú vừa đính → làm tại chỗ đính, thuộc `daily-journal`.
* **KHÔNG** thư viện loại lỗi và xu hướng lỗi → `execution-learning` *(chưa có URD)*. Báo cáo chỉ **render
  lại** phần lỗi của feature đó.
* **KHÔNG** chia sẻ, đồng bộ đám mây, gửi báo cáo qua email, hay bất kỳ đường nào **sản phẩm tự gửi dữ liệu
  đi**. Tệp được tạo ra và nằm lại trên máy người chơi; **đưa nó cho ai là việc của người chơi**.
* **KHÔNG** nhắc sao lưu định kỳ — mọi cơ chế nhắc theo nhịp đều là thứ **cộng dồn theo thời gian** mà
  `README.md` đã cấm.
* **KHÔNG** giao diện sáng và giao diện di động.

## 3. Personas

| Persona | Mô tả (1 dòng) | Nhu cầu chính | Nguồn |
|---------|----------------|---------------|-------|
| Người chơi | **Ngoài phiên giao dịch** — cuối tháng ngồi tổng kết, hoặc một buổi dọn dẹp. Trước màn hình với chuột và bàn phím | Cầm được dữ liệu của mình ra khỏi sản phẩm, giữ nó an toàn, và đổi được các thiết lập vô hại **mà không phải đụng vào máy chủ** | URD Mục 2, UN-005, UN-008, UN-018 |

> **Trợ lý AI ngoài không phải người dùng của sản phẩm** — nó là **nơi nhận** một tệp mà người chơi chủ động
> đưa cho. **Sản phẩm không gửi đi đâu cả, không kết nối tới nó, không biết nó là ai.**
> **Sàn cTrader/Spotware không liên quan tới feature này** — không dữ liệu nào của feature này đi tới sàn, và
> không dữ liệu nào từ sàn được nhập vào.

## 4. Capabilities

| ID | Capability | Priority | Rationale (vì sao tier này) | Traces to | Bóc ~N story | Done when (product outcome) | Sẵn sàng |
|----|------------|----------|-----------------------------|-----------|--------------|-----------------------------|----------|
| CAP-reports-export-01 | **Không bản xuất hay gói sao lưu nào mang theo bí mật** | P0 | Đây là ranh giới tuyệt đối và là **rủi ro không hoàn tác được**: tệp đã rời khỏi sản phẩm thì không thu về được. Một lần dính là hỏng | UN-007, UN-010 | ~5 | Không token, không giá trị biến môi trường, không cấu hình gốc, không đường dẫn tuyệt đối trên máy chủ — **kiểm được, không phải một lời hứa** | ✅ |
| CAP-reports-export-02 | Gói sao lưu **đầy đủ** kèm bản kê có mã kiểm tra | P0 | Đây là bảo vệ duy nhất chống mất sạch. Thiếu bản ghi âm, ảnh hoặc tape thì replay và nhật ký giọng nói khôi phục về sẽ **rỗng** | UN-008, UN-009 | ~7 | Người chơi kiểm được gói **còn nguyên vẹn trước khi cần tới nó**, không phải khôi phục thật mới biết | ✅ |
| CAP-reports-export-03 | Gói **luôn là một lát cắt nhất quán** | P0 | **Một gói nửa vời trông y hệt một gói đủ**, và cái giá của nhầm lẫn đó chỉ lộ ra đúng lúc cần khôi phục | UN-024 | ~4 | Hoặc chờ việc nền xong rồi mới chụp, hoặc **bị từ chối kèm nêu rõ việc đang chạy** — không bao giờ tạo ra một gói nửa vời | ✅ |
| CAP-reports-export-04 | Khôi phục **có điều kiện**, và kiểm **trước khi** động vào dữ liệu hiện tại | P0 | Khôi phục từ một gói hỏng mà làm mất luôn dữ liệu đang có là **kịch bản tệ nhất của cả sản phẩm** | UN-011, UN-012 | ~8 | Hỏng ở bất kỳ bước nào thì mở lại **vẫn là nhật ký cũ, đầy đủ, như chưa từng bấm** | ✅ |
| CAP-reports-export-05 | Đối chiếu **bằng con số** sau khi khôi phục | P0 | Tin vào một dòng "thành công" là cách để phát hiện thiếu dữ liệu ba tháng sau | UN-013 | ~3 | Số lượng bản ghi và mã kiểm tra tệp đính kèm **khớp bản kê**, và kết quả **hiện ra cho người chơi xem** | ✅ |
| CAP-reports-export-06 | Ba thao tác nặng cần **một lần xác nhận gần đây** | P0 | **Gói sao lưu chứa toàn bộ giọng nói cá nhân** — nó không được nằm sau đúng một cú bấm | UN-025 | ~4 | Tải gói, khôi phục và xoá sạch **không chạy được chỉ vì cửa sổ trình duyệt đang mở sẵn**; mức chặt tăng dần | ✅ |
| CAP-reports-export-07 | Xuất JSON **tự đủ nghĩa** | P0 | **Đây là mục đích đã chốt của việc xuất dữ liệu** — đưa cho một trợ lý AI ngoài đọc. Không tự đủ nghĩa thì mục đích chính coi như hỏng | UN-005 | ~6 | Trợ lý AI ngoài trả lời được câu hỏi dài hạn **mà không phải hỏi lại "cột này nghĩa là gì"** | ✅ |
| CAP-reports-export-08 | Xoá sạch có chủ ý, **không có bản sao ẩn** sau lời xác nhận cuối | P1 | Nghĩa vụ về dữ liệu cá nhân, và **cơ chế phải đúng ở mức Critical** — nhưng **tần suất thì không**: việc này hiếm khi xảy ra | UN-014, UN-015, UN-016 | ~6 | Gõ đúng câu xác nhận **và** giữ nút hai giây; xoá xong chỉ còn cấu hình, phần mềm, và **một vết ghi nhận không có nội dung** | ⚠️ chờ OQ-1 (ranh giới với đường xoá riêng giọng nói) |
| CAP-reports-export-09 | Màn cài đặt **chỉ đổi được thứ an toàn** | P1 | Trị đúng pain "đổi một preference vô hại phải SSH"; nhưng người chơi vẫn sửa được bằng tay trong lúc chờ | UN-018 | ~6 | Đổi được biểu tượng, khung giờ, lịch buổi tối, hiệu chỉnh tay cầm, rung, micro, giọng đọc, mặc định báo cáo — **ngay trong sản phẩm** | ✅ |
| CAP-reports-export-10 | **Chốt an toàn không xuất hiện trong giao diện** | P1 | Đi cùng CAP-09 — mở màn cài đặt mà không có ranh giới này thì tạo ra đúng rủi ro nó sinh ra để tránh | UN-019, UN-020 | ~3 | Chế độ demo/thật, đăng nhập sàn, địa chỉ lắng nghe, quyền AI, trọng số trục **không có mặt** — kể cả ở dạng chỉ đọc gây hiểu nhầm là sửa được | ✅ |
| CAP-reports-export-11 | Báo cáo theo **kỳ tự chọn**, mở đầu bằng quy trình | P1 | Là lý do gap neo nêu ra, nhưng deck đã trả lời phần lớn câu hỏi đó trên màn hình | UN-001, UN-002 | ~6 | Tạo được cho một tuần, một tháng, một khoảng ngày tuỳ chọn, hoặc **một phiên**; mở đầu bằng bìa quy trình | ⚠️ chờ OQ-4 (ai tính số tổng hợp cho kỳ không phải một tháng trọn) |
| CAP-reports-export-12 | **Phụ lục kết quả mặc định TẮT**, không preference nào bật vĩnh viễn | P1 | Cách duy nhất áp "tiền sau một cú bấm có chủ ý" lên một **tệp tĩnh** — chuyển cú bấm đó về **lúc tạo tệp** | UN-003 | ~4 | Không tích thì trong tệp **không có một đồng nào**; và phụ lục **luôn khởi tạo tắt cho mỗi lần tạo** | ✅ |
| CAP-reports-export-13 | Lưu báo cáo thành **một tệp đọc được ngay trên máy** | P1 | Không có nó thì báo cáo chỉ là một màn hình nữa — mất hẳn lý do tồn tại của phần báo cáo | UN-004 | ~4 | Lưu được bằng chính trình duyệt đang mở; **không thành phần nào phải thêm vào máy chủ** | ✅ |
| CAP-reports-export-14 | **Cảnh báo dung lượng** trước khi hết chỗ | P1 | Ràng buộc "nhật ký giữ vô hạn" gặp một giới hạn vật lý **trong im lặng**, và cái hỏng đầu tiên sẽ là một phiên đang chạy | UN-017 | ~3 | Người chơi biết trước khi hết chỗ, **đủ sớm để còn kịp sao lưu và dọn** | ⚠️ chờ OQ-3 (ngưỡng và nơi hiện cảnh báo) |
| CAP-reports-export-15 | Vết ghi nhận **không có nội dung** cho mọi thao tác dữ liệu | P1 | Cần để tra cứu; nhưng phải cẩn thận **không biến thành lời nhắc theo nhịp** — thứ `README.md` đã cấm | URD Mục 3 | ~2 | Chỉ hành động, thời điểm, số lượng — và **không bao giờ** thành "đã bao lâu kể từ lần sao lưu gần nhất" | ✅ |
| CAP-reports-export-16 | Báo cáo và cài đặt **mở bằng tay cầm** từ menu an toàn | P1 | Nhất quán với hợp đồng điều hướng chung; nhưng đây là bề mặt ngoài phiên nên không cấp bách | UN-023 | ~2 | Mở được bằng tay cầm; việc chọn kỳ, tích phụ lục và xử lý tệp thì dùng chuột và bàn phím | ✅ |
| CAP-reports-export-17 | **Dẫn sang** trình sửa của feature sở hữu, không dựng bản sao | P1 | Hai trình sửa cùng một thứ là cách chắc chắn để chúng lệch nhau | UN-022 | ~2 | Cài đặt dẫn sang trình sửa playbook và trình sửa nguyên tắc cá nhân — **chỉ có một chỗ sửa mỗi thứ** | ✅ |
| CAP-reports-export-18 | Xuất **CSV phẳng** | P2 | Người chơi đã chốt **JSON là ưu tiên số một**; CSV là thứ yếu, dùng khi muốn tự cắt lát bằng bảng tính | UN-006 | ~3 | Mở được bằng bảng tính: **chữ tiếng Việt không vỡ**, memo nhiều dòng và dấu phẩy trong chữ không làm lệch cột | ✅ |

> **Bảy P0 — đúng ngưỡng.** Và nguyên tắc chọn chúng khác mọi feature trước: ở đây tiêu chí là
> **"cái gì hỏng thì không hoàn tác được"**. Tệp đã rời khỏi sản phẩm không thu về được (CAP-01); một gói
> nửa vời chỉ lộ ra đúng lúc cần khôi phục (CAP-03); khôi phục hỏng mà mất luôn dữ liệu đang có là kịch bản
> tệ nhất của cả sản phẩm (CAP-04). Bảy cái này là **hai nghĩa vụ kéo ngược nhau của Mục 1** ở dạng nhỏ
> nhất: *mang được ra* (CAP-02, CAP-07) và *không mất, không rò* (CAP-01, CAP-03, CAP-04, CAP-05, CAP-06).
>
> **Xoá sạch ở P1 là một quyết định có ý thức, không phải hạ thấp mức độ quan trọng.** URD nêu rõ: *việc này
> hiếm khi xảy ra, nhưng khi xảy ra thì không hoàn tác được, nên **cơ chế phải đúng ở mức Critical còn tần
> suất thì không***. Hoãn được — nhưng **không được ship một phiên bản nửa an toàn**.

## 5. Upstream Traceability

| Capability | Traces to | Product outcome | Success metric |
|------------|-----------|-----------------|----------------|
| CAP-01 | UN-007, UN-010 | Không tệp nào rời khỏi sản phẩm mang theo bí mật | M1 Rò rỉ bí mật |
| CAP-02, CAP-03, CAP-04, CAP-05 | UN-008..013, UN-024 | Gói sao lưu **thật sự khôi phục được**, không chỉ tạo ra được | M2 Diễn tập vòng tròn |
| CAP-07 | UN-005 | Một góc nhìn ngoài trả lời được câu hỏi dài hạn | M3 Ba câu hỏi chuẩn |
| CAP-12, CAP-10, CAP-08 | UN-003, UN-019, UN-016 | Những thứ không được phép xuất hiện thì không bao giờ xuất hiện | M4 Ba vế tuyệt đối |
| CAP-06 | UN-025 | Toàn bộ giọng nói cá nhân không nằm sau đúng một cú bấm | M1, M2 (điều kiện) |
| CAP-09, CAP-17 | UN-018, UN-022 | Đổi được thiết lập vô hại mà không đụng máy chủ; chỉ một chỗ sửa mỗi thứ | — |
| CAP-11, CAP-13, CAP-18 | UN-001, UN-002, UN-004, UN-006 | Cầm được một lát cắt của tháng ra khỏi màn hình | — |
| CAP-14, CAP-15 | UN-017 | Ràng buộc "giữ vô hạn" không gặp giới hạn vật lý trong im lặng | — |

## 6. Key Capability Interactions

* **Tạo báo cáo:** CAP-16 (mở bằng tay cầm) → CAP-11 chọn kỳ → CAP-12 phụ lục **đang tắt sẵn** → tạo →
  CAP-13 lưu thành tệp. Con số trong tệp là con số `process-score` và `daily-journal` **đã chốt**; feature
  này **không tính lại**.
* **Xuất dữ liệu:** CAP-07 (JSON) hoặc CAP-18 (CSV) → CAP-01 lọc bí mật **trước khi** tệp được tạo. Ràng
  buộc sản phẩm giữ được nằm ở **lúc tạo tệp**; sau khi tệp ở trên máy người chơi thì nó đi đâu là việc của
  người chơi.
* **Sao lưu:** CAP-06 (xác nhận gần đây) → CAP-03 kiểm việc nền xong chưa → CAP-02 dựng gói + bản kê →
  CAP-01 loại bí mật và thứ thay thế được.
* **Khôi phục:** CAP-06 → CAP-04 kiểm bản kê, mã kiểm tra, tương thích, đường dẫn **trước khi động vào dữ
  liệu hiện tại** → dựng bản mới riêng → đổi chỗ → CAP-05 đối chiếu bằng con số và **hiện kết quả ra**.
* **Xoá sạch:** CAP-06 → CAP-08 mời sao lưu (tạo ra chính bản sao mà OQ-1 lo) → gõ câu xác nhận + giữ hai
  giây → xoá → CAP-15 để lại một vết ghi nhận **không có nội dung**.
* **Ranh giới ra ngoài:** CAP-09 dựng màn cài đặt mà `tilt-meter` (bật/tắt) và `voice-journal` (bật/tắt,
  xoá riêng giọng nói) đặt mục của mình lên; CAP-17 dẫn sang trình sửa của `playbook-grading` và
  `daily-journal`; CAP-14 là nguồn cảnh báo dung lượng mà `daily-journal` phụ thuộc để giữ lời hứa "giữ vô
  hạn".

## 7. Success Metrics

| Metric | Baseline | Target | Measurement Method | Timeframe |
|--------|----------|--------|--------------------|-----------|
| M1 Rò rỉ bí mật | **Có sẵn: 0** — hiện chưa có tệp nào rời khỏi sản phẩm | **0 lần**, mọi bản xuất và mọi gói, **không có ngoại lệ**. Thước đo tuyệt đối, không phải xu hướng | Với mỗi bản xuất và mỗi gói tạo ra trong kỳ: **tìm chuỗi** token, biến môi trường, tên miền máy chủ và đường dẫn tuyệt đối. **Một lần dính là hỏng** | Hằng quý, **và bắt buộc trước lần đầu đưa tệp cho bất kỳ bên thứ ba nào** |
| M2 Diễn tập vòng tròn | Chưa có — xác lập bằng lần diễn tập đầu tiên | Mỗi quý diễn tập một vòng **sao lưu rồi khôi phục** trên dữ liệu bỏ đi được: số lượng và mã kiểm tra **khớp 100%** với bản kê | Chạy vòng tròn đầy đủ, đọc kết quả đối chiếu, ghi lại quý nào đạt. **Không diễn tập được coi như không đạt** — *một gói chưa từng khôi phục thử thì chưa phải một bản sao lưu* | Hằng quý |
| M3 Ba câu hỏi chuẩn | Chưa có — xác lập bằng lần xuất đầu tiên | Đưa bản xuất cho một trợ lý AI ngoài chưa biết gì về sản phẩm và hỏi **ba câu**: tháng nào tuân thủ tốt nhất · loại lỗi nào lặp lại nhiều nhất · điểm quy trình có xu hướng gì. **Cả ba trả lời được chỉ từ tệp** | Chạy đúng ba câu đó. **Phép thử này không tất định** (đổi mô hình là đổi kết quả) nên đi kèm **một vế tất định**: đọc chính tệp và kiểm nó có phần tự mô tả — tên trường, đơn vị, thang điểm, múi giờ | Hằng quý |
| M4 Ba vế tuyệt đối | **Có sẵn: 0 ở cả ba vế** | **0 tệp** có con số tiền khi người chơi không tích phụ lục · **0 khoá** thuộc nhóm chốt an toàn xuất hiện trong màn cài đặt · **0 nội dung nhật ký** còn sót sau xoá sạch | Rà tệp báo cáo mỗi lần đổi phần báo cáo; rà màn cài đặt mỗi lần đổi giao diện; rà nơi lưu sau mỗi lần xoá sạch | Hằng quý, **và bắt buộc sau mỗi lần đổi ba bề mặt đó** |

> **M1 và M3 kéo ngược nhau, và đó là chủ ý.** M3 muốn bản xuất mang theo **càng nhiều ngữ cảnh càng tốt**;
> M1 canh chừng đúng cái giá phải trả nếu "nhiều ngữ cảnh hơn" lặng lẽ trở thành "mang theo cả những thứ
> không được mang". **Phải đọc cùng nhau** — mỗi lần bản xuất giàu thêm là **một lần M1 phải được chạy lại**.
>
> **M4 phủ ba nhu cầu Critical mà trước đó không thước đo nào chạm tới.**
>
> **Giới hạn đã biết.** M2 đo được rằng gói *khôi phục được*, nhưng **không đo được rằng gói được tạo đủ
> thường xuyên**. Vế đó phụ thuộc hoàn toàn vào thói quen thủ công của người chơi, và **thứ duy nhất nhắc là
> cảnh báo dung lượng** — vì mọi lời nhắc theo nhịp đều bị cấm.

## 8. Dependencies

> **Feature này không tính con số nào của riêng nó**, nên mọi phụ thuộc nội dung dưới đây là **nguồn số**,
> không phải nguồn logic.

| Dependency | Owner | Status | Needed-by | Impact if Late |
|------------|-------|--------|-----------|----------------|
| Điểm quy trình, mức tuân thủ và mọi số liệu tổng hợp đã chốt | `process-score` | At Risk | Cùng lúc CAP-11 | Báo cáo không có gì để render — và **không được tự tính thay** |
| Bản đồ nhiệt và số liệu cấp ngày | `daily-journal` | At Risk | Cùng lúc CAP-11 | Như trên |
| Quy tắc **"một ngày là một buổi tối"** để cắt kỳ báo cáo | `daily-journal` (FR-003) | At Risk | Cùng lúc CAP-11 | Cùng một khoảng ngày ra **hai kết quả khác nhau** giữa báo cáo và bản đồ nhiệt |
| Cách tính số tổng hợp cho **kỳ không phải một tháng trọn** | `process-score` | **Blocked** | Trước khi CAP-11 vào Next | Báo cáo tuần và khoảng tuỳ chọn không có số tổng hợp — xem OQ-4 |
| Phần lỗi sai để render | `execution-learning` — **chưa có URD** | **Blocked** | Cùng lúc CAP-11 | Mục lỗi trong báo cáo trống; báo cáo **phải nói rõ** thay vì để một mục rỗng |
| Dữ liệu tám feature để đóng gói: bản ghi âm · ảnh biểu đồ · tape đã đóng băng | `voice-journal` · `daily-journal` · `trade-replay` | At Risk | Cùng lúc CAP-02 | **Gói thiếu một phần thì replay và nhật ký giọng nói khôi phục về sẽ rỗng** |
| Ranh giới với **đường xoá riêng giọng nói** | `voice-journal` (FR-044) | **Blocked** | Trước khi CAP-08 vào Next | Hai đường xoá đá nhau: hoặc xoá thiếu, hoặc người chơi tưởng đã xoá hết mà chưa — xem OQ-1 |
| Menu an toàn làm chỗ mở báo cáo và cài đặt | `order-execution` (FR-052) | On Track | Cùng lúc CAP-16 | Chỉ mở được bằng chuột |
| Trình sửa playbook · trình sửa nguyên tắc cá nhân để **dẫn sang** | `playbook-grading` · `daily-journal` | At Risk | Cùng lúc CAP-17 | Đường dẫn chết; **không được dựng bản sao thứ hai** |
| Mục bật/tắt của `tilt-meter` và `voice-journal` đặt lên màn cài đặt | `tilt-meter` (FR-043) · `voice-journal` (FR-052) | At Risk | Cùng lúc CAP-09 | Hai feature đó không có chỗ để tắt |

## 9. Assumptions & Validation

| Assumption | Impact if Wrong | Validation | Status |
|------------|-----------------|------------|--------|
| Xuất dữ liệu **chủ yếu để đưa cho một trợ lý AI ngoài đọc**, nên JSON đủ ngữ cảnh là ưu tiên số một và CSV là thứ yếu | Nếu thực tế dùng bảng tính là chính, **ưu tiên đảo ngược**: CSV cần được thiết kế kỹ hơn JSON | Kiểm lại sau ba lần dùng thật: bản nào **thực sự được mở**. **Ba tháng đầu không xuất lần nào thì chính giá trị của feature cần xem lại**, không chỉ thứ tự ưu tiên định dạng | **Confirmed** 2026-08-28 (URD A-01) |
| Bản xuất JSON **tự đủ nghĩa** để một trợ lý AI chưa biết gì đọc hiểu | Xuất xong **vẫn phải giải thích thủ công từng trường** — mục đích chính của việc xuất coi như hỏng | Thử ba câu hỏi chuẩn ngay lần xuất đầu tiên, kèm **vế tất định**: đọc chính tệp xem có phần tự mô tả không | Open (URD A-02) |
| Người chơi sao lưu **thủ công**, không theo lịch, và điều đó đủ an toàn | Không sao lưu suốt nhiều tháng rồi mất sạch — **đúng rủi ro feature này sinh ra để chặn, nhưng bị chặn bởi chính quyết định không nhắc** | **Bẫy tự kiểm:** quý đầu không diễn tập được M2 lần nào thì coi giả định này là **sai** và đặt lại quyết định không-nhắc-định-kỳ, thay vì để nó lặng lẽ trôi qua | Open (URD A-03 🔶) |
| Ngưỡng cảnh báo dung lượng đặt được ở mức **đủ sớm** để còn kịp sao lưu và dọn | Cảnh báo tới quá muộn thì vô dụng; quá sớm thì thành tiếng ồn và bị bỏ qua | Đo dung lượng sinh ra mỗi tối trong 10 phiên đầu rồi đặt ngưỡng. **Ứng viên nháp:** cảnh báo khi chỗ trống còn đủ cho khoảng **20 phiên nữa** | Open (URD A-04 → OQ-3) |
| Báo cáo lấy **đúng con số** `process-score` và `daily-journal` đã chốt, không tính lại | Hai nơi lệch nhau thì người chơi **mất niềm tin vào cả báo cáo lẫn deck** | Đối chiếu con số báo cáo với deck | Open (URD A-05) |
| Đường xoá sạch ở đây và đường **xoá riêng giọng nói** là hai đường **độc lập, không đá nhau** | Hai đường chồng nhau thì hoặc **xoá thiếu**, hoặc người chơi **tưởng đã xoá hết mà chưa** | Chốt cùng `voice-journal` | Open (URD A-06 → OQ-1) |
| Feature này ship **sau** chín feature nguồn — tám đã có URD, cộng `execution-learning` **chưa có URD** | Ship sớm thì báo cáo và gói bao gồm những phần chưa tồn tại — **dễ đọc nhầm một gói thiếu thành một gói đủ** | **Bản kê luôn phản ánh đúng thứ thật sự có trong gói**, dù ship theo thứ tự nào. Phần lỗi của báo cáo có thể trống ở ngày ra mắt và **báo cáo phải nói rõ điều đó** | Open (URD A-07) |
| Ba thước đo **kiểm được bằng chính công cụ sẵn có** (tìm chuỗi trong tệp, đối chiếu bản kê, ba câu hỏi cho trợ lý ngoài), không cần thêm cơ chế đo nào | Phải dựng thêm cơ chế đo → ba thước đo trở thành **phạm vi phát sinh** chứ không phải cách kiểm chứng | Xác nhận khi thiết kế | Open (URD A-08 🔶) |

## 10. Product Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| **Một tệp rời khỏi sản phẩm mang theo bí mật** | Low | **Rất cao — không hoàn tác được** | M1 chạy **bắt buộc trước lần đầu đưa tệp cho bất kỳ bên thứ ba nào**, và chạy lại **mỗi lần bản xuất giàu thêm**. Đây là lý do M1 và M3 phải đọc cùng nhau | Người chơi |
| **Không sao lưu suốt nhiều tháng rồi mất sạch** | High | **Rất cao** | Đây là hệ quả trực tiếp của quyết định **không nhắc định kỳ** (đã chốt). Cảnh báo dung lượng là **lời nhắc duy nhất còn lại**. Bẫy tự kiểm: quý đầu không diễn tập được M2 lần nào thì đặt lại chính quyết định đó | Người chơi |
| **Một gói nửa vời trông y hệt một gói đủ** | Medium | **Rất cao** | CAP-03: hoặc chờ việc nền xong, hoặc **từ chối kèm nêu rõ việc đang chạy**. Bản kê luôn phản ánh đúng thứ thật sự có trong gói | Người chơi |
| **Khôi phục hỏng làm mất luôn dữ liệu đang có** | Low | **Rất cao** | CAP-04: kiểm bản kê, mã kiểm tra, tương thích và đường dẫn **trước khi** động vào dữ liệu hiện tại; dựng bản mới riêng rồi mới đổi chỗ | Người chơi |
| **Gói sao lưu cũ làm sống lại dữ liệu đã cố ý xoá** | Medium | High | Gói đã tạo nằm **ngoài vòng kiểm soát của sản phẩm**. Người chơi phải được nói rõ ở **đúng hai chỗ**: lúc xoá riêng giọng nói và lúc xoá sạch — mà lời mời sao lưu ở bước xoá sạch **tạo ra chính bản sao đó**. Xem OQ-1 | Người chơi |
| Hai đường xoá đá nhau → xoá thiếu, hoặc tưởng đã xoá hết mà chưa | Medium | High | Chốt OQ-1 cùng `voice-journal` **trước khi** CAP-08 dùng được; hai lời xác nhận phải **khác nhau đủ để không bấm nhầm** | Người chơi |
| ~~Mâu thuẫn *hạn giữ nhật ký* ↔ *giữ vô hạn*~~ | — | — | **Đã loại bỏ 2026-08-29**: mục *hạn giữ nhật ký* bị bỏ khỏi màn cài đặt, nên **không tồn tại cơ chế tự xoá nào** để vô tình bật | — |
| Preference bị đặt lại theo máy cũ sau khi khôi phục lên máy chủ mới | Medium | Medium | Chưa chốt preference thuộc nhóm bị thay hay nhóm được giữ. Chừng nào chưa chốt, việc khôi phục phải **nói rõ nó sẽ chạm vào những gì trước khi chạy** — xem OQ-5 | Người chơi |
| Bản xuất JSON quá lớn sau nhiều tháng, trình duyệt treo | Medium | Medium | Vẫn tải về được mà trình duyệt không treo; người chơi **giới hạn được kỳ xuất** như khi tạo báo cáo | Người chơi |

## 11. Release & Launch Readiness

### 11.1 Release Horizon

| Horizon | Capabilities | Target | Status |
|---------|--------------|--------|--------|
| Now | CAP-reports-export-01 → 07 (P0) | Chưa chốt lịch | planned — sau chín feature nguồn |
| Next | CAP-reports-export-09, 10, 12, 13, 15, 16, 17 (P1) | Chưa chốt lịch | planned |
| Next (khoá) | CAP-reports-export-08, 11, 14 (P1) | Chưa chốt lịch | CAP-08 chờ OQ-1 · CAP-11 chờ OQ-4 · CAP-14 chờ OQ-3 |
| Later | CAP-reports-export-18 (P2) | Chưa chốt lịch | planned |

> **Feature này ship sau chín feature nguồn** — tám đã có URD, cộng `execution-learning` **chưa có URD**.
> Ship sớm thì báo cáo và gói bao gồm những phần chưa tồn tại, **dễ đọc nhầm một gói thiếu thành một gói đủ**.
> Đổi lại: **bản kê luôn phản ánh đúng thứ thật sự có trong gói**, dù ship theo thứ tự nào.

### 11.2 Launch Readiness

| Workstream | Must-pass criteria | Status | Guardrail metric (threshold → decision) |
|------------|--------------------|--------|-----------------------------------------|
| Không rò rỉ | **Tìm chuỗi** trong mọi bản xuất và mọi gói: không token, không biến môi trường, không tên miền máy chủ, không đường dẫn tuyệt đối | ⬜ | **Một lần dính → dừng toàn bộ việc xuất và sao lưu** cho tới khi sửa; tệp đã ra ngoài thì không thu về được |
| Vòng tròn sao lưu–khôi phục | Chạy đầy đủ trên dữ liệu bỏ đi được: sao lưu → đổi vài thứ → khôi phục → **đối chiếu số lượng và mã kiểm tra khớp bản kê** | ⬜ | Không chạy được vòng này → **coi như chưa có bản sao lưu nào**, dù đã tạo bao nhiêu gói |
| Khôi phục an toàn | Bốn cách hỏng phải **bị từ chối trước khi dữ liệu hiện tại thay đổi**: sai mã kiểm tra · đường dẫn lạ · phiên bản không tương thích · còn vị thế mở. Thêm: tệp **không phải gói của sản phẩm này** phải bị từ chối; và **chỗ trống không đủ** phải bị từ chối sớm kèm con số cần bao nhiêu | ⬜ | Một cách lọt qua → **tắt khôi phục** cho tới khi sửa; đây là kịch bản tệ nhất của cả sản phẩm |
| Gói nhất quán | Tạo gói giữa lúc còn việc chép lời hoặc đóng băng tape đang chạy | ⬜ | Tạo ra một gói nửa vời → sửa ngay; một gói nửa vời **trông y hệt một gói đủ** |
| Tiền không tự vào tệp | Tạo báo cáo một tháng mà **không tích gì thêm**; rà toàn bộ tệp kể cả chú thích và chân trang. Rồi đặt "mặc định báo cáo" và tạo lại — phụ lục **vẫn phải tắt** | ⬜ | Một con số tiền lọt vào → sửa; và nếu preference bật được phụ lục thì **cú bấm có chủ ý đã thành cú bấm một lần** |
| Cài đặt không chạm chốt an toàn | Rà toàn màn cài đặt; rồi gửi thẳng một thay đổi chứa khoá thuộc nhóm cấm ở tầng dưới | ⬜ | Khoá cấm được nhận, hoặc **âm thầm bỏ qua rồi báo thành công** → sửa ngay; người chơi sẽ tưởng thứ mình gửi đã được nhận |
| Xoá là xoá thật | Xoá sạch rồi rà lại **toàn bộ nơi lưu**: không một dòng nhật ký, một bản ghi âm, một ảnh hay ghi chú nào. Và **tìm khắp máy chủ không được có bản sao ẩn nào** | ⬜ | Còn sót → sửa; "xoá là mất hẳn" là lời hứa không được phép sai |
| Xoá không thể nhầm | Bấm xoá khi còn phiên/vị thế → từ chối; gõ sai câu → từ chối; gõ đúng nhưng không giữ đủ hai giây → từ chối | ⬜ | Một cách lọt qua → tắt xoá sạch cho tới khi sửa |
| Bản xuất tự đủ nghĩa | Đưa cho một trợ lý AI ngoài chưa biết gì và hỏi **ba câu chuẩn**; kèm vế tất định là đọc chính tệp tìm phần tự mô tả | ⬜ | Không trả lời được và tệp không tự mô tả → **mục đích chính của việc xuất coi như hỏng**; thiết kế lại trước khi dùng |
| CSV không vỡ | Mở bằng bảng tính: chữ tiếng Việt đúng, memo nhiều dòng và dấu phẩy trong chữ không lệch cột | ⬜ | Vỡ cột → bản xuất phẳng thành vô dụng đúng lúc muốn dùng |

## 12. Open Questions

* [ ] **OQ-1** *(kế thừa URD OQ-5, chung với `voice-journal` OQ-3)*: Đường **xoá sạch** ở đây và đường **xoá
  riêng giọng nói** của `voice-journal` phân định thế nào để không đá nhau? Xoá sạch có **gọi lại** đường
  kia, hay tự xoá phần giọng nói? Hai lời xác nhận có **khác nhau đủ để không bấm nhầm**?
  Và vế thứ ba: `voice-journal` hứa "xoá là mất hẳn", nhưng **một gói sao lưu cũ khôi phục về sẽ mang giọng
  nói đó quay lại** — người chơi được nói điều này **ở đâu và lúc nào**? Lời mời sao lưu ở bước xoá sạch
  **tạo ra chính bản sao đó**. **Chặn CAP-08.**
* [x] **OQ-2** *(kế thừa URD OQ-2, chung với `daily-journal` OQ-5)*: Mục *hạn giữ nhật ký* mâu thuẫn với
  ràng buộc nhật ký giữ vô hạn.
  **Resolved 2026-08-29: bỏ hẳn mục *hạn giữ nhật ký*.** Lý do: nó mâu thuẫn với **hai** quyết định đã chốt (`daily-journal` giữ vô hạn · `voice-journal` bản ghi âm không tự hết hạn); phép tính dung lượng không ủng hộ nó (~20 phiên/tháng, chữ và ảnh không đáng kể, giọng nói "ở mức không đáng kể"); và thứ duy nhất phình thật là **tape** — nay thuộc `order-execution`, nên hạn giữ tape là cấu hình của tape chứ không phải của nhật ký. Thay thế: **cảnh báo dung lượng + xoá thủ công**, vốn đã là thiết kế.

* [ ] **OQ-3** *(kế thừa URD OQ-3)*: Ngưỡng cảnh báo dung lượng là bao nhiêu, và cảnh báo **hiện ở đâu**?
  Chỉ khi mở phần dữ liệu thì **có thể quá muộn**; hiện lên màn hình chính giữa phiên thì **vi phạm nguyên
  tắc màn hình chính chỉ có thứ cần cho việc giao dịch**. **Chặn CAP-14.**
* [ ] **OQ-4** *(kế thừa URD OQ-8)*: **Ai tính số tổng hợp cho một kỳ không phải một tháng trọn?** CAP-11
  hứa báo cáo cho một tuần và một khoảng ngày tuỳ chọn, nhưng `process-score` mới định nghĩa số tổng hợp ở
  mức **tháng** và mức **phiên**, còn `daily-journal` đã đẩy toàn bộ số liệu nhiều phiên sang đó.
  Mở rộng `process-score` cho kỳ tuỳ chọn, hay báo cáo kỳ tuỳ chọn **chỉ liệt kê con số cấp phiên**?
  **Feature này không được tự gộp** — đó là ràng buộc lõi. **Chặn CAP-11.**
* [ ] **OQ-5** *(kế thừa URD OQ-9)*: Khôi phục có **đè các thiết lập hiện tại** không, và xoá sạch có xoá
  luôn chúng không? Nguồn đặt preference nằm **cùng chỗ với dữ liệu nhật ký**, nên cả hai thao tác đều chạm
  tới chúng. Kịch bản thật: dựng máy chủ mới, khôi phục gói cũ, rồi **máy mới bị đặt lại theo hiệu chỉnh tay
  cầm của máy cũ**. 🔶 **Tạm quyết:** chừng nào chưa chốt, việc khôi phục phải **nói rõ nó sẽ chạm vào những
  gì trước khi chạy**. *Cả hai câu đều không hoàn tác được.*
* [ ] **OQ-6** *(kế thừa URD OQ-4)*: Bản xuất có kèm **bản chép giọng nói** không, và có kèm chính **tệp âm
  thanh** không? Mục đích đã chốt là đưa cho một trợ lý AI ngoài đọc — **bản chép làm bản xuất giàu nghĩa
  hơn hẳn**, nhưng nó cũng là **phần riêng tư nhất trong toàn bộ nhật ký**. Dù chốt thế nào, người chơi phải
  **biết trước khi xuất là trong tệp có gì**.
* [ ] **OQ-7** *(kế thừa URD OQ-1)*: Gói sao lưu có được **đặt mật khẩu hoặc mã hoá** không? Nó chứa **dữ
  liệu giọng nói cá nhân** và nằm trên máy người chơi, có thể chép sang ổ ngoài. Không mã hoá thì đơn giản
  hơn nhiều nhưng **bản ghi âm nằm trần trong một tệp ai cầm cũng mở được**.
* [ ] **OQ-8** *(kế thừa URD OQ-6)*: Khôi phục một gói cũ lên một phiên bản sản phẩm **mới hơn** — nâng được
  tới mức nào? Gói cũ bao nhiêu phiên bản thì còn nâng được, và **quá mức đó thì sản phẩm nói gì với người
  chơi**? Từ chối im lặng nghĩa là một gói để lâu sẽ **hết dùng được mà không ai biết trước**.
* [ ] **OQ-9** *(kế thừa URD OQ-7)*: Báo cáo cho một kỳ mà **trọng số các trục điểm đã đổi giữa kỳ** — tính
  lại toàn bộ theo trọng số hiện tại (nhất quán với cách deck làm), hay giữ nguyên con số lúc đó và ghi chú?
  🔶 **Tạm quyết:** **tính lại toàn bộ theo trọng số hiện tại**, nhất quán với `process-score` FR-040, và
  báo cáo **ghi rõ đang dùng bộ trọng số nào**. *Nếu sai:* một tệp trộn hai thước đo mà người đọc không biết.

---

> **Nguồn:** `reports-export-urd.md` (25 nhu cầu, 7 journey, 38 tình huống ngoại lệ, 4 thước đo, 8 giả
> định) · bốn tài liệu nền `docs/_shared/` · ranh giới nhận từ **cả tám feature kia** cộng
> `execution-learning` (chưa có URD). **Chưa có BRD**.
>
> **🔶 Ba quyết định thay user:** OQ-2 (không bật mặc định cơ chế tự xoá), OQ-5 (khôi phục phải nói rõ nó
> chạm gì), OQ-9 (tính lại theo trọng số hiện tại). **OQ-1, OQ-4, OQ-6 và OQ-7 em cố ý không quyết** —
> chúng chạm nghĩa vụ về dữ liệu cá nhân và ranh giới sở hữu giữa các feature.
