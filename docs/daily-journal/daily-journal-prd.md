---
type: prd
feature: daily-journal
status: draft
updated: 2026-08-29
links:
  - docs/daily-journal/daily-journal-urd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/srs/order-execution-spec.md
  - docs/voice-journal/srs/voice-journal-spec.md
  - docs/process-score/process-score-urd.md
  - docs/trade-replay/trade-replay-urd.md
---

# daily-journal — Product Requirements Document

## 1. Product Overview

`daily-journal` phục vụ **hai đầu của một buổi tối**: bước vào đã có chuẩn bị, và bước ra với một bản ghi
trung thực đủ để sáng hôm sau đọc lại vẫn hiểu mình đã làm gì và vì sao.

Đây là **đường chậm nhất** trong ba đường của hệ thống. Nó không đứng trên đường đặt lệnh, không tính điểm,
không khuyên gì. Giá trị của nó nằm ở chỗ khác: nó là nơi **duy nhất** giữ lại những thứ không tự sinh ra từ
sàn — luận điểm trước phiên, trạng thái người chơi lúc ngồi xuống, và bối cảnh của một quyết định vốn chỉ
tồn tại trong đầu vài phút rồi biến mất.

**Gap neo:** Hiện tại người chơi ngồi xuống là mở biểu đồ và giao dịch ngay, không có nghi thức nào ở giữa —
nên đêm mệt và đêm tỉnh táo được đối xử y hệt nhau. Công cụ nhật ký hiện có thì mở đầu bằng lãi lỗ, kéo buổi
review về kết quả trong ba giây đầu. Và sau khi đóng phiên thì đóng luôn trình duyệt, nên vòng học khép lại
nửa chừng: có dữ liệu nhưng không bao giờ được đọc. Sau feature này: một màn "hôm nay" vừa là điểm vào vừa
là điểm về, mở đầu bằng quy trình, và tiền nằm sau một lần bấm có chủ ý.

> **Mệnh đề trung tâm không phải "xem lại thành tích"** mà là *"chuẩn bị được, ghi lại được, và tìm lại
> được — mà không có gì tôi viết ra sửa được sự thật từ sàn, cũng không có thao tác nào trong nhật ký phát
> ra được một lệnh."*

## 2. Goals

### 2.1 Goals

* **Buổi tối bắt đầu bằng một lần dừng lại có ý thức**, thay vì bắt đầu giữa chừng (trace UN-001, USC-001).
* **Mức sẵn sàng thấp không bao giờ khoá người chơi lại** — người chơi vẫn là người quyết định (trace
  UN-002).
* **Một quyết định cũ dựng lại được, không phải đoán** (trace UN-013, USC-002).
* **Quy trình đứng trước tiền ở mọi lối vào nhật ký** — lãi lỗ bằng tiền chỉ hiện sau một lần bấm có chủ ý
  (trace UN-010, USC-003).
* **Chữ người chơi viết không bao giờ sửa được sự thật từ sàn**, và **không thao tác nhật ký nào phát ra
  được một lệnh** (trace UN-014, UN-015, USC-004).
* **Phân biệt được điều mình tin *trước* khi vào lệnh với điều mình viết *sau* khi đã biết kết quả** (trace
  UN-017).

### 2.2 Non-goals

* **KHÔNG** học từ chất lượng thực thi — đối chiếu kế hoạch với thứ đã thực sự làm, phân nhóm lệnh
  có-kế-hoạch / bốc-đồng, thư viện các loại lỗi và xu hướng lỗi → feature **`execution-learning`**
  *(tách khỏi feature này 2026-08-28; **chưa có URD**)*. Nhật ký **hiển thị** lỗi đã được gắn và **lọc** theo
  nó, nhưng không định nghĩa, không tự suy ra, không chấm.
* **KHÔNG** tính điểm quy trình → `process-score`. Nhật ký chỉ **đọc điểm đã chốt** và dùng nó để tô bản đồ
  nhiệt.
* **KHÔNG** tính bất kỳ con số so sánh nhiều phiên nào — độ ổn định quy trình, hệ số lợi nhuận, tỉ lệ thắng,
  sụt giảm tối đa, R trung bình, tháng này so tháng trước → `process-score`. *(Nguyên tắc **một nơi tính,
  một nơi đọc**: nhật ký duyệt bản ghi từng ngày và từng lệnh; mọi con số tổng hợp qua nhiều phiên thuộc
  deck.)* **Kể cả việc gộp điểm nhiều phiên trong một buổi tối.**
* **KHÔNG** hạn mức rủi ro, khoá và mở khoá phiên → `order-execution`. Nhật ký chỉ nhận việc người chơi
  **xác nhận đã chấp nhận hạn mức tối nay** như một mục trong danh sách sẵn sàng.
* **KHÔNG** ghi âm và chuyển lời nói thành văn bản → `voice-journal`. Nhật ký chỉ **hiển thị** memo đã có và
  **cho mượn khung màn hình** để đặt ba thao tác nghe/sửa/xoá lên.
* **KHÔNG** tua lại lệnh qua tape → `trade-replay`. Nhật ký chỉ giữ **đường dẫn sang đó**.
* **KHÔNG** chấm luật playbook (`playbook-grading`) · đo trạng thái tâm lý (`tilt-meter`) · tư vấn, tín
  hiệu, kế hoạch do AI soạn (`ai-desk`) · báo cáo in được, xuất CSV/JSON, sao lưu, khôi phục, xoá toàn bộ,
  màn cài đặt (`reports-export`).
* **KHÔNG** nhiều tài khoản · nhập lịch sử từ MT5 hay sàn khác · bản dùng trên điện thoại · giao diện sáng ·
  lấy ảnh biểu đồ tự động từ TradingView hay nguồn giá không chính thức.

## 3. Personas

| Persona | Mô tả (1 dòng) | Nhu cầu chính | Nguồn |
|---------|----------------|---------------|-------|
| Người chơi — **trước phiên** | Ngồi trước desktop, tay chưa cầm tay cầm, còn dùng bàn phím bình thường | Bước vào buổi tối đã biết mình định làm gì | URD Mục 2, UN-001, UN-004 |
| Người chơi — **sau phiên** | Vẫn màn hình đó, phiên đã đóng, **đầu còn nóng** | Bước ra với một bản ghi mà sáng mai đọc lại vẫn hiểu | URD Mục 2, UN-009, UN-013 |

> Đây là **một người ở hai thời điểm** — và cách chia này quyết định vì sao màn "hôm nay" vừa là điểm vào vừa
> là điểm về. **AI desk** là actor hệ thống và chỉ được **đọc số liệu tổng hợp**; nó không bao giờ viết, sửa
> hay xoá một dòng nhật ký nào. Sàn cTrader/Spotware là **nguồn sự thật** cho dữ kiện khớp lệnh.

## 4. Capabilities

| ID | Capability | Priority | Rationale (vì sao tier này) | Traces to | Bóc ~N story | Done when (product outcome) | Sẵn sàng |
|----|------------|----------|-----------------------------|-----------|--------------|-----------------------------|----------|
| CAP-daily-journal-01 | Màn "hôm nay": một điểm vào trước phiên và một điểm về sau phiên | P0 | Không có nó thì buổi tối vẫn bắt đầu giữa chừng và kết thúc bằng việc tắt máy — đúng hai vấn đề ở gap neo | UN-001, UN-009 | ~6 | Sau khi đóng phiên, màn hình **tự đáp xuống** "hôm nay" với dữ liệu buổi vừa xong đã có sẵn | ⚠️ chờ OQ-2 (người chơi có review ngay trong buổi không) |
| CAP-daily-journal-02 | Năm mục sẵn sàng — chỉ để tự biết, **không bao giờ chặn** | P0 | Nghi thức mở đầu là lõi của feature; và ranh giới không-chặn quan trọng ngang nó | UN-001, UN-002 | ~4 | Bỏ trống hết vẫn mở khoá phiên và vào lệnh được; **không cảnh báo nào biến thành rào chặn** | ✅ |
| CAP-daily-journal-03 | Kế hoạch của tối nay, chụp lại bất biến tại lệnh đầu tiên | P0 | Không có bản chụp thì sáng mai người chơi tin nhầm là mình đã nghĩ thế từ đầu — nhật ký nói dối | UN-004, UN-017 | ~7 | Bản chụp trước lệnh đầu không đổi; phần viết thêm hiện ra **là** viết thêm, kèm thời điểm | ✅ |
| CAP-daily-journal-04 | Quy trình đứng trước tiền ở **mọi** lối vào | P0 | Chữ ký của cả sản phẩm. Một lối vào rò rỉ con số tiền là đủ phá lời hứa | UN-010 | ~3 | Màn mặc định nói về quy trình; **không con số tiền nào** hiện trước một lần bấm có chủ ý | ✅ |
| CAP-daily-journal-05 | Chi tiết một lệnh: đủ bối cảnh ở một chỗ | P0 | Đây là **bề mặt mà bốn feature khác gắn nội dung lên** (memo, điểm luật, lỗi, link replay); thiếu nó thì bốn feature kia không có khung | UN-013 | ~8 | Người chơi mở một lệnh và trả lời được: lúc đó định làm gì, đã làm gì, và sàn ghi nhận gì — **không rời màn** | ✅ |
| CAP-daily-journal-06 | Chữ người chơi không sửa được dữ kiện từ sàn | P0 | Nếu nhật ký sửa được giá khớp thì mọi con số về sau đều vô nghĩa | UN-014 | ~3 | Nhận xét thêm vào được, nhưng giá khớp, thời điểm và lãi lỗ do sàn tính **không bao giờ đổi theo** | ✅ |
| CAP-daily-journal-07 | Nhật ký không phát ra được lệnh và không làm chậm đường đặt lệnh | P0 | Kế thừa ranh giới nền; mở nhật ký giữa phiên là chuyện sẽ xảy ra | UN-015 | ~4 | Mở nhật ký huỷ ARM và khoá mở lệnh mới, **nói rõ ngay lúc mở**; đóng vị thế và thoát khẩn cấp **vẫn luôn được phép** | ✅ |
| CAP-daily-journal-08 | Bốn đồng hồ phiên thị trường, đúng cả tuần đổi giờ mùa | P1 | Giá trị thật nhưng buổi tối vẫn chuẩn bị được không có nó; đổi lại phần đổi giờ mùa là chỗ dễ sai nhất | UN-003 | ~4 | Bốn đồng hồ đọc đúng giờ địa phương thật, kể cả trong cửa sổ châu Âu đã đổi mà Mỹ thì chưa | ✅ |
| CAP-daily-journal-09 | Máy tính cỡ lệnh; áp giá trị **chỉ dàn bản xem trước** | P1 | Trị đúng pain "rủi ro thật lệch khỏi rủi ro đã định"; nhưng v1 người chơi vẫn nhẩm được | UN-006, UN-007 | ~7 | Thấy cả **số yêu cầu và số sàn nhận sau làm tròn**, rủi ro thật bằng tiền, hạn mức đang áp — và áp xong **vẫn cần `LT+RT`** | ✅ |
| CAP-daily-journal-10 | Bản đồ nhiệt một tháng, **mặc định tô theo quy trình** | P1 | Là câu trả lời cho "tháng qua đêm nào tôi giữ được quy trình"; cần vài tuần dữ liệu mới có nghĩa | UN-011 | ~6 | Người chơi nhìn một tháng trong một hình và **chỉ ra được đêm đáng xem ngay từ bản đồ nhiệt** | ⚠️ chờ OQ-1 (ngày không giao dịch hiện thế nào) |
| CAP-daily-journal-11 | Lọc lịch sử nhiều chiều cùng lúc | P1 | Cần khi đã có vài trăm lệnh; bốn chiều hay dùng nhất là kỳ, cặp, phiên thị trường, kết quả | UN-012 | ~6 | Người chơi ra đúng nhóm lệnh cần nhìn, **không lẫn lệnh ngoài điều kiện đã chọn** | ✅ |
| CAP-daily-journal-12 | Mười lệnh gần nhất hiện sẵn | P1 | Lối vào rẻ nhất khi chưa có câu hỏi cụ thể; nhưng chỉ tiện, không thiết yếu | UN-018 | ~2 | Mười lệnh gần nhất hiện sẵn, mỗi lệnh đủ để nhận ra và mở thẳng vào chi tiết | ✅ |
| CAP-daily-journal-13 | Tự chấm 1–5 đầu phiên và cuối phiên, bằng tay cầm | P1 | **Là bằng chứng cho hai trục của `process-score`** — nhưng chính feature này sống được không có nó | UN-008 | ~3 | Hai lần bấm là xong; **bỏ qua không bị hiểu là điểm kém** | ✅ |
| CAP-daily-journal-14 | Đính ảnh biểu đồ đã tự chụp | P1 | Bổ trợ cho kế hoạch; không có thì kế hoạch vẫn viết được bằng chữ | UN-005 | ~4 | Ảnh nằm cạnh chữ, mở lại vẫn còn, không phải lục thư mục ảnh | ✅ |
| CAP-daily-journal-15 | Triết lý và nguyên tắc cốt lõi của chính người chơi | P2 | Giá trị dài hạn, dùng thưa; và chỉ có nghĩa sau khi đã tích luỹ vài bài học lặp lại | UN-016 | ~3 | Có một chỗ cố định để đọc lại **trước những đêm khó**, sửa được khi suy nghĩ thay đổi | ✅ |
| CAP-daily-journal-16 | Đọc kế hoạch AI đã lưu **cạnh** kế hoạch mình tự viết | P2 | Tiện lợi thuần; và phụ thuộc `ai-desk` đã có kế hoạch phiên | UN-019 | ~2 | Hai bản nằm riêng, **luôn phân biệt được nguồn**; chữ người chơi không bị AI sửa | ✅ |

> **Bảy P0 — đúng ngưỡng.** Bảy cái này là **một vòng khép kín nhỏ nhất của một buổi tối**: có chỗ vào (01),
> có nghi thức không cản (02), có thứ để đối chiếu (03), đọc nó không bị tiền kéo đi (04), có chỗ về đủ bối
> cảnh (05), và hai ranh giới giữ cho nhật ký không nói dối (06) và không nguy hiểm (07).
>
> **CAP-13 ở P1 có hệ quả liên feature phải nói rõ.** Tự chấm 1–5 (CAP-13), mục sẵn sàng (CAP-02) và bản
> chụp kế hoạch (CAP-03) **là ba nguồn bằng chứng cho hai trục "chuẩn bị" và "nhìn lại" của `process-score`**.
> Nếu `daily-journal` ra sau `process-score`, deck sẽ ra mắt với **3/5 trục** — đó chính là `process-score`
> A-06, và nó là **trạng thái mặc định lúc ra mắt, không phải tình huống hiếm**. Xem OQ-6.

## 5. Upstream Traceability

| Capability | Traces to | Product outcome | Success metric |
|------------|-----------|-----------------|----------------|
| CAP-01, CAP-02, CAP-03 | UN-001, UN-002, UN-004 | Buổi tối bắt đầu có chuẩn bị thay vì bắt đầu giữa chừng | M1 Phiên có chuẩn bị |
| CAP-05, CAP-03, CAP-14 | UN-013, UN-017, UN-005 | Một quyết định cũ dựng lại được, không phải đoán | M2 Lệnh dựng lại được |
| CAP-04 | UN-010 | Quy trình đứng trước tiền ở mọi lối vào | M3 Lối vào rò rỉ tiền |
| CAP-06, CAP-07 | UN-014, UN-015 | Nhật ký không nói dối và không nguy hiểm | M4 Nhật ký chạm đường đặt lệnh |
| CAP-10 | UN-011 | Trả lời được "tháng qua đêm nào tôi giữ được quy trình" | M5 Chỉ ra được đêm từ bản đồ nhiệt |
| CAP-08 | UN-003 | Ngồi vào bàn đúng lúc, kỳ vọng thanh khoản đúng | M6 Giờ phiên lệch |
| CAP-09 | UN-006, UN-007 | Rủi ro thật khớp rủi ro đã định, sau khi sàn làm tròn | — (kiểm bằng checkpoint J2) |
| CAP-11, CAP-12 | UN-012, UN-018 | Tìm lại được một nhóm lệnh cũ mà không phải cuộn qua tất cả | — (kiểm bằng checkpoint J5) |
| CAP-13 | UN-008 | Trạng thái tự khai được ghi lại — **và làm bằng chứng cho `process-score`** | — (xem ghi chú Mục 4) |
| CAP-15, CAP-16 | UN-016, UN-019 | Điều đã nhận ra được viết xuống ở chỗ cố định · đọc được kế hoạch AI mà không lẫn chữ | — |

## 6. Key Capability Interactions

* **Mở đầu buổi tối:** CAP-01 (màn "hôm nay") → CAP-08 (bốn đồng hồ đang chạy) → CAP-02 (soát năm mục) →
  CAP-13 (tự chấm đầu phiên) → CAP-03 (viết luận điểm, đính ảnh qua CAP-14, đọc kế hoạch AI qua CAP-16) →
  sang màn chính mở khoá phiên. **CAP-02 không bao giờ chặn bước cuối cùng.**
* **Lệnh đầu tiên chốt bản chụp:** khoảnh khắc `order-execution` khớp lệnh đầu → CAP-03 đóng băng kế hoạch.
  Sau đó viết thêm được, nhưng phần thêm **hiện ra là phần thêm**.
* **Tính cỡ lệnh:** CAP-09 → áp giá trị **chỉ đổi bản xem trước** trên HUD của `order-execution` → vẫn cần
  `LT+RT`. Giữa hai bước đó, **không gì rời khỏi máy**.
* **Đóng phiên và đọc lại:** đóng phiên → CAP-01 tự đáp xuống "hôm nay" → CAP-13 (tự chấm cuối phiên) →
  CAP-04 giữ tiền sau một lần bấm → đọc điểm quy trình **đã chốt** do `process-score` cung cấp.
* **Nhìn lại một lệnh:** CAP-12 hoặc CAP-11 → CAP-05 (chi tiết một lệnh) — đây là nơi `voice-journal` đặt ba
  thao tác nghe/sửa/xoá memo, `playbook-grading` đặt bản ghi điểm, `execution-learning` đặt lỗi đã gắn, và
  `trade-replay` nhận đường dẫn sang.
* **Ranh giới ra ngoài:** `process-score` **tính**, nhật ký **đọc** — kể cả việc gộp điểm nhiều phiên trong
  một buổi tối; chiều ngược lại thì nhật ký **cấp bằng chứng** chuẩn bị và nhìn lại cho deck.

## 7. Success Metrics

| Metric | Baseline | Target | Measurement Method | Timeframe |
|--------|----------|--------|--------------------|-----------|
| M1 Phiên có chuẩn bị | Chưa có — xác lập từ 10 buổi tối đầu | **≥ 80%** số phiên trong tháng có ít nhất một phần chuẩn bị được ghi (mục sẵn sàng hoặc kế hoạch của ngày) | Đếm số phiên có bản ghi chuẩn bị gắn với nó, trên tổng số phiên | Hằng tháng |
| M2 Lệnh dựng lại được | Chưa có — xác lập từ 10 buổi tối đầu | **≥ 90%** số lệnh trong tháng mở ra thấy đủ **kế hoạch lúc vào + dữ kiện từ sàn + ít nhất một dấu vết lý do** (memo, ghi chú, hoặc kết quả chấm luật) | Đếm số lệnh đủ ba phần. **Nguồn dấu vết nào đang bị tắt hoặc chưa tồn tại thì loại khỏi mẫu số và ghi rõ đang đo trên mấy nguồn** — không tính là thiếu sót của người chơi | Hằng tháng |
| M3 Lối vào rò rỉ tiền | Chưa có | **100%** màn mặc định không hiển thị con số tiền nào trước một lần bấm có chủ ý | Rà lại **từng lối vào** nhật ký sau mỗi lần đổi giao diện | Mỗi lần đổi giao diện nhật ký |
| M4 Nhật ký chạm đường đặt lệnh | Chưa có | **0** trường hợp một thao tác nhật ký phát ra lệnh hoặc sửa lệnh; và khi nhật ký đang mở, độ trễ đặt lệnh vẫn nằm trong ngân sách ở `system-overview.md` | Đo độ trễ đặt lệnh trong **hai điều kiện** — nhật ký đóng và nhật ký đang mở — mỗi lần thêm màn nhật ký mới | Hằng tháng và mỗi lần thêm màn mới |
| M5 Chỉ ra được đêm từ bản đồ nhiệt | Chưa có — xác lập từ 10 buổi tối đầu | Chỉ ra được đêm giữ được quy trình **ngay từ bản đồ nhiệt**, không phải mở từng ngày để dò | Người chơi tự trả lời có/không một lần mỗi tháng khi nhìn lại tháng vừa xong | Hằng tháng |
| M6 Giờ phiên lệch | Chưa có | **0** lần đọc sai giờ ở bất kỳ mốc đổi giờ nào của London, New York hoặc Sydney — kể cả trong cửa sổ châu Âu đã đổi mà Mỹ thì chưa | Đối chiếu bốn đồng hồ với giờ thật **ngay sau mỗi mốc đổi giờ** | Sau mỗi mốc đổi giờ — khoảng **6 lần một năm** (châu Âu ×2, Mỹ ×2, Úc ×2) |

> **M2 cố ý loại nguồn chưa tồn tại khỏi mẫu số.** Ba tháng đầu, `voice-journal` và `playbook-grading` có
> thể chưa chạy — nếu tính chúng vào mẫu số thì con số đo **thứ tự phát hành**, không đo thói quen người
> chơi. Cùng nguyên tắc với `process-score` UN-015.
>
> **M6 chỉ đo được 6 lần một năm** và mỗi lần là một cơ hội không lặp lại — bỏ lỡ một mốc đổi giờ là mất một
> phép kiểm chứng cho tới lần sau. Đó là lý do nó có chu kỳ riêng thay vì đọc hằng tháng.
>
> **CAP-09 (máy tính cỡ lệnh) cố ý không có metric.** "Áp giá trị không tự gửi lệnh đi" là ranh giới nhị
> phân, kiểm bằng checkpoint hai bước của URD Journey 2 — giữa bước áp và bước bắn, bên sàn **không thấy bất
> kỳ lệnh hay thay đổi nào**.

## 8. Dependencies

| Dependency | Owner | Status | Needed-by | Impact if Late |
|------------|-------|--------|-----------|----------------|
| Vòng đời phiên, hạn mức, khoá/mở khoá | `order-execution` | On Track | Cùng lúc CAP-01, CAP-02 | Không có khái niệm "phiên" để gắn bản ghi chuẩn bị vào |
| Khoảnh khắc **lệnh đầu tiên khớp** để chốt bản chụp kế hoạch | `order-execution` | On Track | Cùng lúc CAP-03 | Bản chụp không biết chốt lúc nào — CAP-03 mất ý nghĩa |
| Bản xem trước trên HUD để áp cỡ lệnh vào | `order-execution` (FR-013) | On Track | Cùng lúc CAP-09 | Không có chỗ để áp giá trị |
| Hàm quy đổi và **làm tròn theo bước nhảy của sàn** | `order-execution` | On Track | Cùng lúc CAP-09 | Con số cỡ lệnh sai đúng chỗ máy tính này sinh ra để chống |
| Dữ kiện khớp và đóng lệnh từ sàn | Sàn cTrader/Spotware | On Track | Cùng lúc CAP-05, CAP-06 | Không có "sự thật từ sàn" để bảo vệ |
| **Điểm quy trình đã chốt** để tô bản đồ nhiệt | `process-score` | **At Risk** | Cùng lúc CAP-10 | Bản đồ nhiệt không có gì để tô. Nhật ký **không được tự tính thay** |
| Điểm ở mức **buổi tối** khi một buổi có nhiều phiên | `process-score` | **Blocked** | Trước khi CAP-10 vào Next | Ô nhiệt phải tô bằng một con số mà nhật ký không được tự gộp — xem OQ-3 |
| Nội dung memo + ba thao tác nghe/sửa/xoá | `voice-journal` | At Risk | Sau CAP-05 | CAP-05 vẫn mở được, chỉ thiếu một phần nội dung |
| Kết quả chấm luật của một lệnh | `playbook-grading` | At Risk | Sau CAP-05 | Như trên |
| Đường dẫn sang bản tua lại | `trade-replay` | At Risk | Sau CAP-05 | CAP-05 mở được và **nói rõ phần tua lại không có** |
| **Định nghĩa loại lỗi** để hiển thị và lọc theo | `execution-learning` — **chưa có URD** | **Blocked** | Trước khi CAP-11 lọc theo lỗi | Chiều "loại lỗi" của CAP-11 không dựng được; các chiều khác vẫn chạy — xem OQ-4 |
| Kế hoạch phiên AI đã lưu | `ai-desk` (FR-032) | At Risk | Cùng lúc CAP-16 | CAP-16 đã ở P2 nên không ảnh hưởng lịch |
| Cảnh báo dung lượng trước khi hết chỗ | `reports-export` (UN-017) | On Track | Trước khi CAP-14 tích luỹ nhiều ảnh | Ràng buộc "giữ vô hạn" gặp giới hạn vật lý **trong im lặng** |

## 9. Assumptions & Validation

> **Hai quyết định đã chốt 2026-08-28** — không còn là giả định chờ kiểm chứng:
>
> * **D-01:** Triết lý và nguyên tắc cốt lõi **thuộc feature này**. Câu tương ứng trong `trade-replay` đã sửa
>   cho khớp.
> * **D-02:** Nhật ký chỉ **đọc** điểm quy trình và mọi con số tổng hợp đã tính sẵn, **không tự tính con số
>   nào — kể cả việc gộp điểm nhiều phiên trong một buổi tối**. Chiều ngược lại thì có: nhật ký **cung cấp
>   bằng chứng** chuẩn bị và nhìn lại cho điểm quy trình.

| Assumption | Impact if Wrong | Validation | Status |
|------------|-----------------|------------|--------|
| Một ngày **không giao dịch là dữ liệu hợp lệ**, không phải dữ liệu thiếu | Bản đồ nhiệt và mọi số trung bình hiểu sai những đêm đứng ngoài — **phá đúng nguyên tắc lớn nhất của sản phẩm** | Kiểm khi thiết kế bản đồ nhiệt | Open (URD A-03 → OQ-1) |
| Người chơi review **ngay trong buổi tối đó**, không phải vài ngày sau | "Hôm nay" không còn là điểm về, và **toàn bộ mô hình màn hình chính phải xoay trục quanh việc chọn ngày cũ** | **Hỏi TRƯỚC khi khoá luồng màn hình** — đây là quyết định tổ chức thông tin, để trôi sang giai đoạn thiết kế là muộn | Open (URD A-04 → OQ-2) |
| Khoảng **20 phiên mỗi tháng** — lượng dữ liệu một năm vẫn nhỏ | Nhiều hơn nhiều lần thì việc lọc và xem lại cần cách tổ chức khác | Xem lại sau ba tháng dùng thật | Open (URD A-05) |
| Người chơi muốn đọc kế hoạch của ngày **cạnh từng lệnh**, không chỉ ở cấp ngày | Phần liên kết lệnh với luận điểm là công thừa | Hỏi cùng OQ-4 | Open (URD A-06) |
| Bốn đồng hồ đổi giờ theo lịch **của chính từng thành phố**, và chỉ Tokyo không bao giờ đổi | M6 sai; người chơi ngồi vào bàn lệch một tiếng trong cửa sổ 2–3 tuần mỗi năm | Đối chiếu ngay sau mỗi mốc đổi giờ | Confirmed (URD UN-003 — là dữ kiện, không phải giả định) |

## 10. Product Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| **Đêm chủ động đứng ngoài bị bản đồ nhiệt đọc thành "đêm tệ"** | High | **Rất cao** | Đây là thứ phá đúng nguyên tắc lớn nhất của sản phẩm. CAP-10 bị **chặn bởi OQ-1** cho tới khi chốt cách hiển thị; và phải phân biệt được với ngày **thị trường đóng** | Người chơi |
| Người chơi review vài ngày sau chứ không ngay trong buổi | Medium | High | **Hỏi trước khi khoá luồng màn hình** (OQ-2). Để trôi thì toàn bộ CAP-01 phải thiết kế lại quanh việc chọn ngày cũ | Người chơi |
| `process-score` chưa có → bản đồ nhiệt không có gì để tô, và nhật ký bị cám dỗ tự tính | Medium | High | D-02 là ranh giới cứng: **nhật ký không tự tính con số nào**. Chưa có điểm thì ô nhiệt nói rõ chưa có, **không bịa một con số trung bình** | Người chơi |
| `execution-learning` chưa có URD → chiều "loại lỗi" của bộ lọc không dựng được | Medium | Medium | Các chiều khác của CAP-11 vẫn chạy; cột lỗi ghi **"không có dữ liệu"**, không suy đoán ngược — xem OQ-4 | Người chơi |
| Ảnh đính tích tụ làm đầy chỗ lưu | Medium | Medium | Cho biết đang dùng bao nhiêu chỗ **trước khi** hết, không phải lúc đã hỏng. Phụ thuộc cảnh báo dung lượng của `reports-export` | Người chơi |
| Mở nhật ký ở hai tab và sửa cùng một buổi tối, bản sau đè mất bản trước | Low | Medium | **Không âm thầm mất chữ** — bản đang mở biết là đã cũ và nói ra trước khi ghi đè | Người chơi |
| ~~Mâu thuẫn "giữ vô hạn" với mục *hạn giữ nhật ký*~~ | — | — | **Đã loại bỏ 2026-08-29**: `reports-export` bỏ hẳn mục đó, nên **không tồn tại cơ chế tự xoá nào** trong sản phẩm | — |

## 11. Release & Launch Readiness

### 11.1 Release Horizon

| Horizon | Capabilities | Target | Status |
|---------|--------------|--------|--------|
| Now | CAP-daily-journal-01 → 07 (P0) | Chưa chốt lịch | **CAP-01 chờ OQ-2** |
| Next | CAP-daily-journal-08, 09, 11, 12, 13, 14 (P1) | Chưa chốt lịch | planned |
| Next (khoá) | CAP-daily-journal-10 (P1) | Chưa chốt lịch | blocked by OQ-1 và OQ-3 |
| Later | CAP-daily-journal-15, 16 (P2) | Chưa chốt lịch | planned |

> **Thứ tự phát hành có một hệ quả liên feature.** CAP-02, CAP-03 và CAP-13 là ba nguồn bằng chứng cho hai
> trục của `process-score`. Ra sau deck nghĩa là deck ra mắt với **3/5 trục** — xem OQ-6.

### 11.2 Launch Readiness

| Workstream | Must-pass criteria | Status | Guardrail metric (threshold → decision) |
|------------|--------------------|--------|-----------------------------------------|
| Không chặn | Mở khoá phiên **thành công** ngay cả khi cả năm mục sẵn sàng đều bỏ trống | ⬜ | Một lần mức sẵn sàng chặn được việc mở khoá → gỡ ngay, vì nó biến một nghi thức thành một cái chốt |
| Quy trình trước tiền | Từ lúc đóng phiên tới lúc đọc xong buổi tối, **không con số tiền nào xuất hiện** cho tới khi tự bấm sang | ⬜ | Một lối vào rò rỉ tiền → sửa trước khi dùng; đây là chữ ký của cả sản phẩm |
| Không chạm đường đặt lệnh | Đo độ trễ đặt lệnh với nhật ký đóng và nhật ký đang mở | ⬜ | Độ trễ ra ngoài ngân sách `system-overview.md` → tách hẳn nhật ký khỏi tiến trình chính |
| Bản chụp bất biến | Viết kế hoạch → vào lệnh đầu → sửa kế hoạch → mở lại: bản chụp **y nguyên**, phần thêm hiện tách bạch kèm thời điểm | ⬜ | Bản chụp đổi được → tắt tính năng sửa sau lệnh đầu, vì nhật ký nói dối còn tệ hơn nhật ký thiếu |
| Dữ kiện sàn bất khả xâm phạm | Thử sửa giá khớp, thời điểm, lãi lỗ | ⬜ | Sửa được → dừng dùng nhật ký làm nguồn đối chiếu cho tới khi sửa |
| Áp cỡ lệnh không tự gửi | Giữa bước áp và bước bắn, kiểm bên sàn **không thấy lệnh hay thay đổi nào** | ⬜ | Một lệnh phát sinh → **dừng CAP-09 ngay**; đây là sự cố nghiêm trọng nhất feature này có thể gây ra |
| Đêm đứng ngoài đọc đúng | Một ngày **không giao dịch** mở được và đọc ra là không giao dịch, **không phải một đêm điểm thấp** | ⬜ | Đọc nhầm → chặn CAP-10 cho tới khi sửa, vì nó phá nguyên tắc lớn nhất của sản phẩm |
| Giờ đổi mùa | Đối chiếu bốn đồng hồ ngay sau mỗi mốc đổi giờ | ⬜ | Lệch một tiếng → sửa trước mốc kế tiếp; **mỗi mốc là một cơ hội không lặp lại** |

## 12. Open Questions

* [ ] **OQ-1** *(kế thừa URD OQ-1)*: Một ngày **không giao dịch** hiện màu gì trên bản đồ nhiệt để không bao
  giờ bị đọc nhầm thành đêm tệ — cùng thang màu quy trình, một màu trung tính riêng, hay một ký hiệu riêng?
  Và nó phải phân biệt được với ngày **thị trường đóng**. **Chặn CAP-10.**
* [ ] **OQ-2** *(kế thừa URD A-04)*: Người chơi review **ngay trong buổi tối đó** hay vài ngày sau?
  **Chặn CAP-01.** Nếu review muộn thì "hôm nay" không còn là điểm về và toàn bộ mô hình màn hình chính phải
  xoay trục quanh việc chọn ngày cũ. **Đây là quyết định tổ chức thông tin — để trôi sang giai đoạn thiết kế
  là muộn.**
* [ ] **OQ-3** *(kế thừa URD OQ-7, chung với `process-score` OQ-9)*: `process-score` có cung cấp điểm ở mức
  **buổi tối** không, hay chỉ mức **phiên**? Một buổi có hai phiên trở lên thì ô nhiệt phải tô bằng một con
  số — mà D-02 cấm nhật ký tự gộp. **Chặn CAP-10.**
* [ ] **OQ-4** *(kế thừa URD OQ-3, OQ-4)*: Việc **gắn một lệnh với luận điểm của ngày** thuộc feature nào?
  Kế hoạch của ngày do feature này sở hữu, nhưng việc **đối chiếu** kế hoạch với thứ đã làm thuộc
  `execution-learning` — vốn **chưa có URD**. Để muộn thì hai feature dễ dựng trùng cùng một đường liên kết.
  Và: giữ slug `execution-learning` không, URD của nó viết trước hay sau?
* [x] **OQ-5** *(kế thừa URD OQ-11, chung với `reports-export` OQ-2)*: Mâu thuẫn *hạn giữ nhật ký* ↔
  *giữ vô hạn*.
  **Resolved 2026-08-29: bỏ hẳn mục *hạn giữ nhật ký*.** Lý do: nó mâu thuẫn với **hai** quyết định đã chốt (`daily-journal` giữ vô hạn · `voice-journal` bản ghi âm không tự hết hạn); phép tính dung lượng không ủng hộ nó (~20 phiên/tháng, chữ và ảnh không đáng kể, giọng nói "ở mức không đáng kể"); và thứ duy nhất phình thật là **tape** — nay thuộc `order-execution`, nên hạn giữ tape là cấu hình của tape chứ không phải của nhật ký. Thay thế: **cảnh báo dung lượng + xoá thủ công**, vốn đã là thiết kế.

* [ ] **OQ-6** *(mới — hệ quả thứ tự phát hành)*: `daily-journal` ra **trước hay sau** `process-score`?
  CAP-02, CAP-03, CAP-13 là ba nguồn bằng chứng cho hai trục của deck. Ra sau nghĩa là deck ra mắt với
  **3/5 trục** — đó là trạng thái mặc định lúc ra mắt, không phải tình huống hiếm. Xem `process-score` A-06.
* [ ] **OQ-7** *(kế thừa URD OQ-2)*: Giữa phiên có cần **ghi chú nhanh bằng tay cầm** không, ngoài tự chấm
  1–5 và memo giọng nói? Nếu có thì hình thức nào chịu được ràng buộc "ngắn và bằng tay cầm"?
* [ ] **OQ-8** *(kế thừa URD OQ-5, chung với `voice-journal`)*: Kế hoạch của ngày, ghi chú và nguyên tắc có
  **tìm theo chữ** được không? `voice-journal` đã chốt memo thì **không**. Nếu cả nhóm này cũng không, thì
  với dữ liệu giữ vô hạn, thứ đã viết ra chỉ tìm lại được qua **ngày** hoặc qua **lệnh**.
* [ ] **OQ-9** *(kế thừa URD OQ-8, chung với `trade-replay` OQ-7 và `process-score`)*: Những lần **tự huỷ
  không dẫn tới lệnh nào** hiện ở đâu? Ứng viên tự nhiên là chi tiết một buổi tối trong nhật ký, nhưng con
  số cộng dồn đã chốt thuộc `process-score`. **Cần chốt một lần cho cả ba tài liệu.**
* [ ] **OQ-10** *(kế thừa URD OQ-10)*: Gỡ **một** ảnh hoặc một ghi chú vừa đính — gỡ hẳn, hay đánh dấu đã gỡ
  mà vẫn giữ vết?

---

> **Nguồn:** `daily-journal-urd.md` (19 nhu cầu, 7 journey, 20 tình huống ngoại lệ, 6 thước đo, 2 quyết định
> đã chốt + 4 giả định) · bốn tài liệu nền `docs/_shared/` · ranh giới nhận từ `order-execution`,
> `process-score`, `voice-journal`, `playbook-grading`, `trade-replay`, `ai-desk`, `reports-export`,
> `execution-learning`. **Chưa có BRD**.
>
> **🔶 Một quyết định thay user:** không bật mặc định cơ chế tự xoá nào trong lúc chờ OQ-5. **OQ-1 và OQ-2 em
> cố ý không quyết** — cái đầu chạm nguyên tắc lớn nhất của sản phẩm, cái sau là quyết định tổ chức thông
> tin mà chỉ người chơi mới trả lời được.
