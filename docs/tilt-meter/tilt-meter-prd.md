---
type: prd
feature: tilt-meter
status: draft
updated: 2026-08-29
links:
  - docs/tilt-meter/tilt-meter-urd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/srs/order-execution-spec.md
  - docs/playbook-grading/srs/playbook-grading-spec.md
  - docs/voice-journal/voice-journal-urd.md
  - docs/process-score/process-score-urd.md
---

# tilt-meter — Product Requirements Document

## 1. Product Overview

`tilt-meter` giúp người chơi **nhận ra mình đang ở trạng thái xấu ngay lúc nó đang diễn ra** — đọc từ chính
hành vi trên tay cầm, không phải từ một bản tự chấm sau phiên — và cản lại **đúng một chỗ duy nhất: lúc mở
lệnh mới**.

Sản phẩm đã có sẵn những thứ chặn người chơi — hạn mức rủi ro, chốt an toàn khi vắng mặt — nhưng tất cả đều
dựa trên **một luật do chính người chơi đặt ra trước phiên**. Feature này là thứ **duy nhất** làm chậm người
chơi lại dựa trên **một nhận định về trạng thái hiện tại của họ**. Vì vậy hai ranh giới sinh ra cùng lúc với
nó và quan trọng ngang nhu cầu chính: **nó không bao giờ được chạm vào đường thoát**, và **nó không bao giờ
được trừ điểm ai**.

**Gap neo:** Hiện tại công cụ giao dịch chỉ có hai mức — im lặng, hoặc cấm. Không có gì nằm giữa "không nhắc
gì" và "khoá tài khoản". Các hệ thống chấm điểm kỷ luật thì trừ điểm khi phát hiện trạng thái xấu, biến công
cụ thành nơi bị mắng. Sau feature này: bốn mức với hệ quả tăng dần, mức thấp nhất im lặng hoàn toàn, mức ấm
**không tốn gì cả**, và một buổi có lúc quá nóng nhưng người chơi dừng lại đúng lúc thì vẫn được chấm **tốt**.

> **Một cơ chế cản người ở sai chỗ thì nguy hiểm; một cơ chế mắng người thì bị tắt sau hai tuần. Cả hai đều
> là thất bại** — và đó là lý do hai capability đầu tiên của feature này là hai ranh giới, không phải hai
> tính năng.

## 2. Goals

### 2.1 Goals

* **Đường thoát không bao giờ bị cơ chế này chạm tới** — đóng vị thế, thoát khẩn cấp, nút thoát trên màn
  hình và tự khoá phiên hoạt động y hệt như khi chỉ số ở mức thấp nhất (trace UN-001).
* **Không bao giờ trừ điểm ai vì mười phút xấu** — trạng thái tâm lý không xuất hiện trong bất kỳ phép tính
  điểm nào (trace UN-002).
* **Cản lại đúng lúc còn kịp**, chứ không nhắc sau khi đã vào lệnh (trace UN-003).
* **Người chơi biết vì sao mình bị đánh giá là đang xấu, bằng một câu chứ không phải một con số** — nhờ vậy
  một cảnh báo sai **nhìn là biết sai ngay** thay vì thành một phán xét không cãi được (trace UN-004).
* **Chỉ bị so với chính mình**, không bị so với một chuẩn nào bên ngoài (trace UN-005).
* **Người chơi vẫn còn bật cơ chế này sau ba tháng** — điều kiện sống còn, không phải một chỉ số phụ
  (trace USC-003).

### 2.2 Non-goals

* **KHÔNG** phân loại cảm xúc, phát hiện từ ngữ tiêu cực, chấm điểm nội dung lời nói, hay bất kỳ mô hình
  ngôn ngữ nào trong phép tính. **Ngoài phạm vi vĩnh viễn** — đây là ranh giới nguỵ khoa học không được vượt.
* **KHÔNG** đo trạng thái giọng nói (nhịp nói, độ lớn). Người chơi đã **bỏ hẳn khỏi phạm vi** 2026-08-28;
  mở lại phải qua một CR.
* **KHÔNG** là một hạn mức. Tilt **thêm ma sát**; nó không từ chối vì vượt trần và không dùng chung cách nói
  với hạn mức → `order-execution`.
* **KHÔNG** chạm chốt an toàn khi người chơi vắng mặt (mất tay cầm, mất focus, mất kết nối) →
  `order-execution`. Hai cơ chế cùng chỉ chạm việc mở lệnh nhưng **xử sự ngược nhau khi mất tín hiệu**.
* **KHÔNG** bảng nhìn lại các mức tilt theo phiên và tương quan với tuân thủ → `process-score`. Feature này
  **tạo dữ liệu**; nơi đọc nó thành xu hướng là deck.
* **KHÔNG** sở hữu bộ đếm tự huỷ → `order-execution`. **KHÔNG** chấm luật playbook → `playbook-grading`;
  feature này chỉ **tiêu thụ** kết quả chấm như một tín hiệu.
* **KHÔNG** ghi âm và chép lời → `voice-journal`; feature này chỉ dùng **sự kiện "đã ghi một memo"**, không
  dùng nội dung và không phân tích âm thanh.
* **KHÔNG** nghi thức chuẩn bị trước phiên → `daily-journal`. **KHÔNG** tua lại tape → `trade-replay`.
  **KHÔNG** báo cáo, xuất dữ liệu → `reports-export`.

## 3. Personas

| Persona | Mô tả (1 dòng) | Nhu cầu chính | Nguồn |
|---------|----------------|---------------|-------|
| Người chơi | Tay đặt trên tay cầm, trong phiên, **thường sau một chuỗi kết quả xấu — đúng lúc khả năng tự đánh giá kém nhất** | Được cản lại đúng lúc mình đang trượt, mà không mất quyền thoát và không bị chấm điểm nhân cách | URD Mục 2, UN-001, UN-002, UN-003 |

> **Không có persona thứ hai.** AI desk **không tham gia tính chỉ số** — không mô hình ngôn ngữ nào nằm trong
> phép tính; nó chỉ **đọc** được mức và nguyên nhân chính ở dạng tổng hợp. Text canonical về persona sống ở
> URD Mục 2.

## 4. Capabilities

| ID | Capability | Priority | Rationale (vì sao tier này) | Traces to | Bóc ~N story | Done when (product outcome) | Sẵn sàng |
|----|------------|----------|-----------------------------|-----------|--------------|-----------------------------|----------|
| CAP-tilt-meter-01 | Ranh giới cứng: không bao giờ chạm đường thoát | P0 | Đây là kịch bản nguy hiểm duy nhất của cả feature. Cản người ở sai chỗ nguy hiểm hơn nhiều so với không cản gì | UN-001 | ~4 | Đóng vị thế, thoát khẩn cấp, nút thoát màn hình, tự khoá phiên hoạt động y hệt như ở mức thấp nhất | ⚠️ chờ OQ-1 (thao tác sửa SL/TP có bị siết không) |
| CAP-tilt-meter-02 | Ranh giới cứng: không bao giờ là đầu vào của điểm | P0 | Một cơ chế mắng người thì bị tắt sau hai tuần — và khi đó cả feature vô dụng, kể cả phần đúng | UN-002 | ~3 | Một buổi có lúc quá nóng nhưng người chơi dừng lại đúng lúc được chấm **tốt** | ✅ |
| CAP-tilt-meter-03 | Đo từ hành vi tay cầm và dữ liệu nhật ký sẵn có | P0 | Lõi của cả feature; và ranh giới "không suy đoán cảm xúc" nằm ngay trong cách đo | UN-006 | ~10 | Mọi thành phần đều là một hành vi đếm được hoặc một dữ kiện có sẵn — không phân loại cảm xúc, không mô hình ngôn ngữ | ✅ |
| CAP-tilt-meter-04 | Mốc so sánh là mức thường của chính người chơi, 30 phiên gần nhất | P0 | Không có mốc riêng thì cơ chế áp chuẩn của đám đông lên người chơi — người vốn bấm nhanh sẽ luôn bị coi là đang tilt | UN-005 | ~5 | Người chơi chỉ bị so với chính mình, không với một chuẩn nào bên ngoài | ✅ |
| CAP-tilt-meter-05 | Bốn mức, cộng một trạng thái trung tính riêng | P0 | Thang bốn mức chính là thứ lấp khoảng trống giữa "im lặng" và "cấm" mà gap neo mô tả | UN-009 | ~5 | Chỉ số luôn ở đúng một mức; trạng thái "chưa đủ dữ liệu" đọc **khác hẳn** mức bình thường và không bao giờ sinh ma sát | ✅ |
| CAP-tilt-meter-06 | Nêu tên hành vi đang đẩy chỉ số lên, bằng một câu | P0 | Đây là thứ biến một cảnh báo sai thành **nhìn là biết sai** thay vì thành một phán xét không cãi được | UN-004 | ~4 | Màn hình luôn nêu tên hành vi bằng lời mô tả chính việc người chơi vừa làm, không bao giờ chỉ một con số trần | ✅ |
| CAP-tilt-meter-07 | Mức ấm không tốn của người chơi thứ gì | P0 | "Một lời nhắc không tốn gì là lời nhắc còn được nghe sau ba tháng" — đây là cơ chế bảo vệ USC-003 | UN-008 | ~2 | Mức ấm chỉ thêm một dòng chữ và đổi màu; thao tác bắn **không đổi một chút nào** | ✅ |
| CAP-tilt-meter-08 | Mức nóng siết thao tác bắn | P0 | Là mức can thiệp đầu tiên có giá; đủ để một cú bấm bốc đồng không tự đi qua | UN-003 | ~5 | Người chơi phải **giữ** nút xác nhận thay vì bấm nhả, và trong lúc giữ còn kịp đổi ý | ✅ |
| CAP-tilt-meter-09 | Mức quá nóng khoá mở lệnh 5 phút, có đường ra bằng memo | P0 | Là can thiệp mạnh nhất; và **đường ra phải luôn dùng được**, nếu không thì nó thành hình phạt | UN-003, UN-007 | ~7 | Người chơi hoặc chờ hết khoảng khoá, hoặc ghi một memo và thấy chỉ số hạ xuống **thật** | ⚠️ chờ OQ-2 (đường ra khi không ghi memo được) |
| CAP-tilt-meter-10 | Khoảng khoá đi theo đồng hồ, và **mở ra khi đồng hồ không tin được** | P0 | Một cái khoá mà người chơi có thể bị kẹt trong đó là tệ hơn không có khoá; đây là mặt trái bắt buộc của CAP-09 | UN-013 | ~4 | Khoá không rút ngắn được bằng cách đóng-mở phiên; nhưng đồng hồ hỏng thì **cho phép giao dịch** | ✅ |
| CAP-tilt-meter-11 | Tắt được hoàn toàn, không để lại dấu vết | P0 | USC-003 (còn bật sau 3 tháng) là điều kiện sống còn — mà điều kiện để nó có nghĩa là việc tắt phải thật sự dễ và thật sự sạch | UN-010 | ~4 | Tắt xong thì không chỉ báo, không dòng cảnh báo, không ma sát, không khoá; không phần nào sót lại "để tham khảo" | ✅ |
| CAP-tilt-meter-12 | Mức tilt tại thời điểm bắn gắn vào mỗi lệnh | P1 | Biến một cảm giác mơ hồ thành dữ kiện đối chiếu được, nhưng chỉ có giá trị khi đã có lịch sử để nhìn lại | UN-012 | ~3 | Người chơi mở một lệnh cũ và biết lúc bấm nút đó mình đang ở trạng thái nào | ✅ |
| CAP-tilt-meter-13 | Ghi lại mỗi lần đổi mức kèm mốc thời gian và hành vi gây ra nó | P1 | `trade-replay` cần nó ở mức **Critical** cho dải sự kiện; nhưng feature đó ra sau | UN-014 | ~3 | `trade-replay` đặt được mỗi lần đổi mức đúng chỗ trên dải thời gian của một lệnh | ✅ |
| CAP-tilt-meter-14 | Giữ hai con số theo phiên cho hai thước đo của chính mình | P1 | Không tự giữ thì cả M1 và M2 **không đo được ở đâu cả** — `process-score` tuyên bố không sinh dữ liệu của riêng nó | URD Mục 3 | ~2 | Hai thước đo đọc được ngay cả khi `process-score` chưa tồn tại | ✅ |
| CAP-tilt-meter-15 | Chế độ diễn tập: đặt thẳng mức để tự kiểm hai ranh giới | P1 | **Ranh giới an toàn quan trọng nhất của feature lại là thứ khó kiểm nhất** — dựng bằng hành vi thật tốn cả một buổi và phụ thuộc thị trường | URD OQ-10 | ~3 | Người chơi kiểm được CAP-01 và CAP-02 trong vài phút thay vì cả một buổi tối | 🔒 blocked by OQ-3 |

> **P0 = 11 capability, vượt ngưỡng 7.** Không đề xuất tách feature, và lý do khác hai đợt trước: ở đây
> **hai capability đầu tiên không phải tính năng mà là ranh giới**, và chín cái còn lại chỉ là *một thang đo
> với bốn hệ quả*. Bỏ một mức thì thang gãy: bỏ mức ấm thì mất lời-nhắc-không-tốn-gì (và người chơi tắt cơ
> chế); bỏ mức nóng thì nhảy thẳng từ im lặng sang khoá — đúng cái nhị phân mà gap neo mô tả là vấn đề. Ba
> cái còn lại (04 mốc riêng, 06 câu nêu lý do, 11 tắt được) là ba thứ giữ cho cơ chế **không bị tắt vì mất
> lòng tin**, nên chúng đứng cùng hạng với chính thang đo.

## 5. Upstream Traceability

| Capability | Traces to | Product outcome | Success metric |
|------------|-----------|-----------------|----------------|
| CAP-01, CAP-10 | UN-001, UN-013 | Người chơi không bao giờ bị kẹt hay bị cản đường ra | — (ranh giới nhị phân, kiểm bằng checkpoint J1) |
| CAP-02 | UN-002 | Một buổi có mười phút xấu không bị phạt | — (ranh giới nhị phân, kiểm bằng checkpoint chung với `process-score` J8) |
| CAP-03, CAP-08, CAP-09 | UN-006, UN-003 | Bị cản lại đúng lúc còn kịp | M1 Vào lại sau thua · M2 Khối lượng vọt |
| CAP-04, CAP-05, CAP-06 | UN-005, UN-009, UN-004 | Cảnh báo sai nhìn là biết sai, nên cơ chế giữ được lòng tin | M3 Còn bật sau 3 tháng |
| CAP-07, CAP-11 | UN-008, UN-010 | Cơ chế không bị tắt vì khó chịu | M3 |
| CAP-12, CAP-13 | UN-012, UN-014 | Đối chiếu được quyết định với trạng thái lúc ra quyết định | — (dữ liệu cho `trade-replay` và `process-score`) |
| CAP-14 | URD Mục 3 | Hai thước đo của chính feature đọc được mà không phụ thuộc lịch feature khác | M1, M2 (nguồn số) |
| CAP-15 | URD OQ-10 | Hai ranh giới quan trọng nhất kiểm được trong vài phút | — (làm cho checkpoint của CAP-01/02 chạy được) |

## 6. Key Capability Interactions

* **Đo và phân mức:** CAP-03 thu hành vi → CAP-04 so với mức thường 30 phiên → CAP-05 rơi vào một trong bốn
  mức (hoặc trung tính) → CAP-06 nêu tên hành vi đóng góp lớn nhất.
* **Hệ quả tăng dần:** mức bình thường im lặng → CAP-07 (ấm: chỉ một dòng chữ) → CAP-08 (nóng: giữ nút để
  bắn) → CAP-09 (quá nóng: khoá 5 phút + mời ghi memo).
* **Đường ra khỏi khoá:** CAP-09 mời ghi memo → sự kiện "đã ghi một memo" từ `voice-journal` → CAP-03 hạ
  chỉ số → **nếu** xuống dưới ngưỡng thì mở lại trước 5 phút. Bấm "đã đọc" chỉ tắt dòng cảnh báo và
  **không** đổi chỉ số.
* **Xung đột với chốt an toàn khi vắng mặt:** cả hai chạm việc mở lệnh nhưng **xử sự ngược nhau khi mất tín
  hiệu** — chốt an toàn *đóng lại* (vì phòng việc không có người), CAP-10 *mở ra* (vì chỉ là một nhận định).
  Khi một cơ chế khác **đã xử lý xong** tình huống, feature này **không nói thêm gì**.
* **Ranh giới ra ngoài:** `process-score` đọc dữ liệu của CAP-12/CAP-13 để **kể lại buổi tối**, tuyệt đối
  không đưa vào phép gộp điểm (CAP-02); `trade-replay` đặt sự kiện đổi mức của CAP-13 lên dải thời gian;
  `playbook-grading` cấp số luật không đạt trong ba lần bắn gần nhất làm **một tín hiệu** cho CAP-03;
  `voice-journal` cấp sự kiện "đã ghi memo" cho CAP-09 — **không bao giờ cấp nội dung memo**.

## 7. Success Metrics

| Metric | Baseline | Target | Measurement Method | Timeframe |
|--------|----------|--------|--------------------|-----------|
| M1 Vào lại sau thua | Chưa có — xác lập số trung bình mỗi phiên từ **4 phiên đầu**, giai đoạn cơ chế chưa hoạt động | Số lần mở lệnh trong vòng 60 giây sau một lần đóng lỗ, trung bình mỗi phiên, **thấp hơn** baseline sau 3 tháng | Đếm số lần thoả điều kiện, chia số phiên, đọc cuối tháng. **Đọc kèm tổng số lệnh mỗi phiên** — giảm vì giao dịch ít hẳn đi thì không tính là tiến bộ | Hằng quý |
| M2 Khối lượng vọt bất thường | Chưa có — xác lập tỷ lệ trung bình từ **4 phiên đầu** | Tỷ lệ lệnh có khối lượng từ gấp đôi mức thường của phiên trở lên, **thấp hơn** baseline sau 3 tháng | Đếm số lệnh thoả điều kiện trên tổng số lệnh, đọc cuối tháng. **Đọc kèm mức thường của phiên theo tháng** — nếu chính mức thường bò lên thì tỷ lệ đẹp mà hành vi không đổi | Hằng quý |
| M3 Còn bật sau 3 tháng | **Không cần baseline** — đây là điều kiện sống còn, không phải xu hướng | Cơ chế ở trạng thái **bật** ở cuối tháng thứ ba, và không có giai đoạn tắt kéo dài quá một phiên | Ghi nhận mọi lần đổi trạng thái bật/tắt kèm ngày (CAP-11); người chơi nêu lý do nếu muốn, không bắt buộc | Hằng tháng |

> **Baseline lấy từ 4 phiên đầu, không phải 10.** Vì cơ chế **không sinh ma sát trong 5 phiên đầu**, lấy
> baseline từ 10 phiên sẽ trộn 6 phiên đã có ma sát vào chính mốc gốc — và khi đó M1/M2 đo chính mình.
>
> **M3 là thước đo canh gác hai cái kia.** Một cơ chế bị tắt thì M1 và M2 vẫn có thể đẹp lên vì lý do khác,
> và con số sẽ nói dối. **Ba thước đo phải đọc cùng nhau.**
>
> **Giới hạn đã biết:** cả ba đo *hành vi giảm đi*, không đo *quyết định tốt lên*. Người chơi vào lại ít hơn
> vì đã bình tĩnh, và người chơi vào lại ít hơn vì đã chán, cho ra **cùng một con số**.
>
> **CAP-01 và CAP-02 cố ý không có metric xu hướng** — chúng là ranh giới nhị phân, kiểm bằng checkpoint.

## 8. Dependencies

| Dependency | Owner | Status | Needed-by | Impact if Late |
|------------|-------|--------|-----------|----------------|
| Chuỗi vũ trang–bắn để gắn ma sát vào | `order-execution` (FR-011..FR-017) | On Track | Cùng lúc CAP-08 | Chặn CAP-08, CAP-09 |
| Đường thoát để **không** chạm vào | `order-execution` (FR-029) | On Track | Cùng lúc CAP-01 | Không có gì để kiểm chứng ranh giới quan trọng nhất |
| Sự kiện **"đã ghi một memo"** (không phải nội dung memo) | `voice-journal` | At Risk | Cùng lúc CAP-09 | **Đường ra sớm khỏi khoá biến mất** → khoá 5 phút thành hình phạt thuần |
| Đường ghi memo bằng **bàn phím**, dùng được trong lúc bị khoá | `voice-journal` (UN-011) | At Risk | Cùng lúc CAP-09 | Không mic hoặc đã tắt giọng nói → kẹt trọn 5 phút không lối thoát — xem OQ-2 |
| Số luật không đạt trong ba lần bắn gần nhất | `playbook-grading` | On Track | Cùng lúc CAP-03 | Thành phần đó không áp; chỉ số vẫn tính trên phần còn lại |
| Bề mặt hiển thị hồi tưởng tilt của một buổi tối | `process-score` | At Risk | Sau CAP-13 | Dữ liệu vẫn được sinh ra nhưng chưa ai đọc thành xu hướng — chấp nhận được |
| Dải sự kiện trên dòng thời gian một lệnh | `trade-replay` | At Risk | Sau CAP-13 | Như trên |
| Quyết định ma sát có áp cho thao tác sửa SL/TP không | Người chơi | **Blocked** | **Trước khi CAP-01 chốt** | Ranh giới an toàn còn một khoảng hở — xem OQ-1 |

## 9. Assumptions & Validation

| Assumption | Impact if Wrong | Validation | Status |
|------------|-----------------|------------|--------|
| **Người chơi này thực sự có các hành vi tiền-tilt** mà gap neo mô tả | Cơ chế đo đúng nhưng đo một thứ không xảy ra — chỉ số nằm im ở mức bình thường suốt và feature vô dụng (không có hại) | Đọc lại sau 10 phiên đầu: chỉ số có bao giờ rời mức bình thường không | Open (URD A-11) |
| 5 phút là đủ để nguội mà không bị cảm nhận thành hình phạt | Quá ngắn thì vô tác dụng; quá dài thì người chơi tắt hẳn — và CAP-11 thành đường thoát thường xuyên | Đo sau 10 phiên đầu: số lần bị khoá, số lần ghi memo để ra sớm, số lần tắt cơ chế | Open (URD A-01) |
| Giữ nút một khoảng ngắn là mức ma sát cảm nhận được mà không gây bực | Quá ngắn thì không cản được cú bấm bốc đồng; quá dài thì phá nhịp thao tác của cả sản phẩm | Thử vài mức khi có sản phẩm — đây là số cần người chơi **cảm nhận**, không quyết được trên giấy | Open (URD A-02) |
| Ba ngưỡng chia bốn mức hợp với chính người chơi này | Hoặc luôn ở mức ấm (mất tác dụng cảnh báo), hoặc hay chạm mức nóng oan | Xem lại sau một tháng dữ liệu | Open (URD A-03 → OQ-4) |
| Bỏ thành phần giọng nói không làm chỉ số kém nhạy đi đáng kể | Các thành phần hành vi không đủ nhạy → cơ chế bỏ sót đúng những lúc cần nhất | Sau 3 tháng nếu bỏ sót rõ rệt thì mở lại **bằng một CR**, không âm thầm thêm vào | Decided (URD A-04 — quyết định đã chốt, giả định chưa kiểm được) |
| **Chỉ số** sống trong phiên nhưng **khoảng khoá** đi theo đồng hồ, sống qua ranh giới phiên | Nếu khoá cũng reset theo phiên thì đóng-mở phiên là đường vượt khoá dễ hơn cả nút tắt | Xác nhận với người chơi | Open (URD A-05 🔶 → OQ-5) |
| Ghi memo trong lúc bị khoá luôn là một hành động có ý thức; hệ thống không xét nội dung | Người chơi ghi memo rỗng để mở khoá sớm, và cơ chế mất răng | Theo dõi 10 phiên đầu; memo rỗng thành thói quen thì xem lại **liều lượng**, không xem lại ranh giới | Decided (URD A-06 🔶) |
| Người chơi nhận ra một cảnh báo sai **là sai** nhờ câu nêu lý do | Câu đó khó hiểu → cảnh báo sai thành phán xét không cãi được, người chơi mất lòng tin và tắt cơ chế | Kiểm khi có sản phẩm: mỗi lần vào mức nóng, người chơi có nói được câu đó đúng hay sai không | Open (URD A-07) |
| Tắt cơ chế chỉ có hiệu lực từ phiên sau, không xoá được khoảng khoá đang chạy | Tắt là mở khoá ngay → CAP-11 trở thành đường lách chính thức của CAP-09 | Xác nhận với người chơi | Open (URD A-08 🔶) |
| Feature này **tự giữ** hai con số của M1/M2 theo phiên | Không tự giữ thì cả hai **không đo được ở đâu cả** | Đã sửa vào phạm vi: CAP-14 | Decided (URD A-09 🔶) |
| Đường ghi memo luôn dùng được trong lúc bị khoá | Cả hai đường đóng → "không có đường vượt" biến thành kẹt trọn 5 phút không lối thoát — đúng cảm giác bị phạt mà feature sinh ra để tránh | Chốt cùng `voice-journal` | Open (URD A-10 🔶 → OQ-2) |
| **Dưới 5 phiên nên im lặng hoàn toàn** thay vì chạy bằng các thành phần hành vi | Người chơi mất bảo vệ đúng tuần đầu — giai đoạn làm quen và dễ tilt nhất | Xác nhận với người chơi | Open (URD A-12 🔶 → OQ-6) |
| Nhả sớm nút xác nhận **không** phải một lần tự huỷ | Mỗi lần trượt tay ở mức nóng lại được khen là kỷ luật, và bộ đếm mất ý nghĩa | Xác nhận cùng `order-execution` và `process-score` | Open (URD A-13 🔶) |

## 10. Product Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| **Một lệnh đóng bị chậm hoặc bị từ chối vì tilt** | Low | **Rất cao** | CAP-01 là ranh giới cứng, không có cấu hình nào bật được việc cản đường thoát. CAP-15 (chế độ diễn tập) tồn tại chính để kiểm được điều này thường xuyên | Người chơi |
| Người chơi tắt cơ chế sau vài tuần vì thấy phiền | High | High | Mức ấm **không tốn gì**; khoảng khoá **không leo thang** theo số lần; CAP-06 làm cảnh báo sai nhìn là biết sai. M3 canh chừng trực tiếp rủi ro này | Người chơi |
| Cảnh báo sai nhiều vì ngưỡng chưa hiệu chuẩn cho người chơi này | High | Medium | Mốc so sánh là mức thường của chính người chơi (CAP-04); ba ngưỡng là cấu hình, xem lại sau một tháng dữ liệu — xem OQ-4 | Người chơi |
| **Cơ chế đo đúng nhưng đo một thứ không xảy ra** với chính người chơi này | Medium | Medium | Đọc lại sau 10 phiên đầu: chỉ số có bao giờ rời mức bình thường không. Nếu không, feature vô dụng chứ **không có hại** — đó là lý do rủi ro này không cao hơn | Người chơi |
| Không có đường ghi memo lúc bị khoá → kẹt trọn 5 phút | Medium | High | Chốt OQ-2 cùng `voice-journal` **trước khi** CAP-09 dùng được; trong lúc chờ, màn khoá nói thẳng "lần này chỉ còn cách chờ hết giờ" thay vì mời một việc không làm được | Người chơi |
| Memo rỗng thành thói quen để mở khoá sớm | Medium | Medium | Chấp nhận có ý thức — hệ thống **không đọc nội dung memo**, đó là ranh giới đã chốt. Việc dừng lại để nói ra một điều gì đó đã là một khoảng nghỉ. Nếu thành thói quen thì xem lại **liều lượng**, không xem lại ranh giới | Người chơi |
| Đóng-mở phiên trở thành đường vượt khoảng khoá | Medium | High | CAP-10: khoảng khoá đi theo đồng hồ, không theo phiên — xem OQ-5 | Người chơi |

## 11. Release & Launch Readiness

### 11.1 Release Horizon

| Horizon | Capabilities | Target | Status |
|---------|--------------|--------|--------|
| Now | CAP-tilt-meter-01 → 11 (P0) | Chưa chốt lịch | **CAP-01 chờ OQ-1, CAP-09 chờ OQ-2** |
| Next | CAP-tilt-meter-12 → 14 (P1) | Chưa chốt lịch | planned |
| Next (khoá) | CAP-tilt-meter-15 (P1) | Chưa chốt lịch | blocked by OQ-3 |
| Later | — | — | Không có P2 |

> Feature này cần **ít nhất 5 phiên** dữ liệu trước khi bắt đầu chạy, và **khoảng 30 phiên** trước khi mức
> thường của người chơi thực sự ổn định. Giữa hai mốc đó cơ chế có chạy nhưng còn thô — đây là ràng buộc
> nghiệp vụ, không phải giới hạn kỹ thuật.

### 11.2 Launch Readiness

| Workstream | Must-pass criteria | Status | Guardrail metric (threshold → decision) |
|------------|--------------------|--------|-----------------------------------------|
| Đường thoát bất khả xâm phạm | Dựng trạng thái quá nóng, rồi ngay trong lúc đó thoát khẩn cấp — cTrader demo không còn vị thế nào. Cùng lúc, một lệnh **mở** phải bị từ chối | ⬜ | Một lần lệnh đóng bị chậm hoặc bị từ chối → **tắt hẳn feature** ngay, không chờ sửa |
| Không trừ điểm | Ép chỉ số lên mức quá nóng trong khi giữ nguyên mọi hành vi đặt lệnh — điểm quy trình **không đổi** so với lần chạy tâm lý bình thường | ⬜ | Điểm đổi → tách hẳn tilt khỏi mọi đầu vào của điểm trước khi dùng tiếp |
| Mức ấm miễn phí | Ở mức ấm, thao tác bắn vẫn là bấm nhả, không thêm bước nào | ⬜ | Mức ấm có giá → hạ về đúng "chỉ một dòng chữ", vì đây là cơ chế bảo vệ M3 |
| Đường ra khỏi khoá | Ghi memo trong lúc bị khoá → chỉ số **giảm**. Bấm "đã đọc" → chỉ số **không đổi**, khoá còn nguyên | ⬜ | Bấm nút cũng hạ được chỉ số → cơ chế tự vô hiệu hoá, sửa trước khi dùng |
| Không kẹt trong khoá | Ngắt mạng giữa khoảng khoá rồi nối lại — phần còn lại đúng bằng thời gian đã trôi. Đồng hồ không dùng được → **cho phép giao dịch** | ⬜ | Bị kẹt một lần → chuyển sang fail-open tuyệt đối cho tới khi sửa |
| Năm phiên đầu im lặng | Với lịch sử dưới 5 phiên, dựng chuỗi hành vi lẽ ra phải đẩy lên mức nóng — chỉ báo vẫn trung tính, thao tác bắn vẫn là bấm nhả | ⬜ | **Chỉ chạy được trong 5 phiên đầu tiên** — bỏ lỡ thì mất luôn cách kiểm chứng, nên làm ngay buổi đầu |
| Tắt là sạch | Sau khi tắt, dựng lại chuỗi hành vi của mức nóng — không dòng cảnh báo nào, không thay đổi nào trong thao tác bắn | ⬜ | Còn sót dấu vết → sửa, vì "tắt được hoàn toàn" là lời hứa giữ lòng tin |

## 12. Open Questions

* [ ] **OQ-1** *(kế thừa URD OQ-4 — URD đánh dấu "ưu tiên, chốt trước `/srs`")*: Ma sát có áp cho thao tác
  **sửa mức cắt lỗ / chốt lời** không? **Chặn CAP-01 chốt.** Nới cắt lỗ ra xa sau một lệnh thua là hành vi
  tilt điển hình, nhưng siết bảo vệ vào gần lại là hành vi **phòng vệ** nên cản là sai.
  🔶 **Tạm quyết:** **không siết** — giữ nguyên tắc chỉ cản việc mở lệnh mới.
  *Nếu sai:* CAP-01 phải phân biệt được hai chiều của một thao tác sửa, và đó là phần khó nhất của cả
  feature. Đây là **khoảng trống duy nhất còn hở của ranh giới an toàn**, và nó đang hở đúng cái cửa mà một
  người đang tilt hay dùng nhất để tự làm hại mình thêm.

* [ ] **OQ-2** *(kế thừa URD OQ-9 — "ưu tiên, chốt trước `/srs`", chung với `voice-journal`)*: Đường ra sớm
  khỏi khoảng khoá phải luôn dùng được. Ba tình huống làm nó biến mất: đang vũ trang, đã tắt hẳn giọng nói,
  và không có mic. **Chặn CAP-09.**
  🔶 **Tạm quyết:** đường ghi memo **bằng bàn phím luôn mở trong lúc bị khoá** — `voice-journal` đã coi bàn
  phím là đường **ngang hàng**, không phải bản hạ cấp. Cả hai đường đều không dùng được thì màn khoá **nói
  thẳng** lần này chỉ còn cách chờ hết giờ, thay vì mời một việc không làm được.
  *Nếu sai:* khoá 5 phút thành hình phạt thuần trong đúng những tình huống người chơi ít quyền lực nhất.

* [ ] **OQ-3** *(kế thừa URD OQ-10)*: Có chấp nhận một **chế độ diễn tập** cho phép đặt thẳng mức trạng thái
  không? **Chặn CAP-15.** Không có nó thì hai ranh giới quan trọng nhất của feature (CAP-01, CAP-02) chỉ kiểm
  được bằng cách dựng hành vi thật — tốn cả một buổi và phụ thuộc thị trường.

* [ ] **OQ-4** *(kế thừa URD OQ-5)*: Ba ngưỡng chia bốn mức là số cố định hay người chơi tự chỉnh được sau
  khi có dữ liệu? Cho chỉnh thì nới ngưỡng thành **đường lách hợp pháp** của CAP-08/09; không cho chỉnh thì
  ngưỡng sai là hỏng cả cơ chế.

* [ ] **OQ-5** *(kế thừa URD OQ-6)*: Hai phiên cách nhau vài giờ trong cùng một ngày thì **chỉ số** có mang
  sang không? (Khoảng **khoá** thì đã chốt là có — CAP-10.)

* [ ] **OQ-6** *(kế thừa URD OQ-11)*: Trong **5 phiên đầu** — im lặng hoàn toàn, hay vẫn chạy bằng các thành
  phần hành vi như nguồn thiết kế? Im lặng thì mất bảo vệ đúng tuần dễ tilt nhất; chạy thì có thể chấm sai
  khi chưa hiểu gì về người chơi. 🔶 **Tạm quyết:** im lặng hoàn toàn (đã phản ánh vào M1/M2 baseline
  4 phiên). *Nếu sai:* người chơi mất bảo vệ đúng giai đoạn dễ tilt nhất.

* [ ] **OQ-7** *(kế thừa URD OQ-7)*: Ghi một memo hạ chỉ số **bao nhiêu**? Nếu một memo luôn đủ để ra khỏi
  mức quá nóng ngay lập tức thì nó thành **thao tác lách** chứ không còn là can thiệp — đặc biệt khi hệ
  thống không đọc nội dung.

* [ ] **OQ-8** *(kế thừa URD OQ-8)*: Deck của `process-score` có **hiện hai con số M1/M2** thành xu hướng
  nhiều tháng không, hay người chơi đọc thô từ dữ liệu phiên trong ba tháng đầu? Cần một dòng cascade sang
  `process-score` nếu chọn vế đầu.

* [ ] **OQ-9** *(kế thừa URD OQ-12 — `ai-desk` đã trả lời)*: Câu AI nói ở mức nóng thuộc `ai-desk`, nhưng
  `ai-desk-prd.md` OQ-5 đã **tạm quyết không nhận** nghĩa vụ đó. Vậy mức nóng có phần AI nói không, hay
  feature này tự viết wording của mình? 🔶 **Tạm quyết:** feature này **tự viết wording**, không phụ thuộc
  AI — đúng ràng buộc "không mô hình ngôn ngữ nào trong phép tính", và cũng tránh được việc AI phán xét
  trạng thái tâm lý.

---

> **Nguồn:** `tilt-meter-urd.md` (14 nhu cầu, 6 journey, 20 tình huống ngoại lệ, 3 thước đo, 13 giả định) ·
> bốn tài liệu nền `docs/_shared/` · ranh giới nhận từ `order-execution`, `voice-journal`,
> `playbook-grading`, `process-score`, `trade-replay`, `ai-desk`. **Chưa có BRD**.
>
> **🔶 Bốn quyết định thay user:** OQ-1 (không siết thao tác sửa SL/TP), OQ-2 (bàn phím là đường ra), OQ-6
> (5 phiên đầu im lặng), OQ-9 (tự viết wording, không dùng AI). **URD đánh dấu OQ-1 và OQ-2 là "phải chốt
> trước `/srs`"** — em đã tạm quyết theo hướng an toàn nhất và ghi rõ hệ quả nếu sai, nhưng cả hai vẫn cần
> người chơi xác nhận vì chúng chạm ranh giới an toàn.
