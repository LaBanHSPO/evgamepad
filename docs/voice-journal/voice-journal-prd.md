---
type: prd
feature: voice-journal
status: draft
updated: 2026-08-29
links:
  - docs/voice-journal/voice-journal-urd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/srs/order-execution-spec.md
  - docs/ai-desk/srs/ai-desk-spec.md
  - docs/tilt-meter/srs/tilt-meter-spec.md
---

# voice-journal — Product Requirements Document

## 1. Product Overview

`voice-journal` tồn tại vì một giới hạn vật lý rất đơn giản: **hai tay đang cầm tay cầm thì không gõ phím
được**. Cái mất đi không phải là chữ, mà là **suy nghĩ thật tại thời điểm ra quyết định** — thứ duy nhất
giải thích được vì sao tối nay mình vào lệnh đó.

Feature này biến giọng nói thành cách duy nhất để nói chuyện với sản phẩm trong lúc hai tay đang bận: nói ra
lý do vào lệnh, hỏi coach một câu, và nghe câu trả lời — và **không bao giờ được phép chạm tới đường đặt
lệnh**.

**Gap neo:** Hiện tại lý do vào lệnh chỉ tồn tại trong đầu vài phút rồi tan, vì không có cách nào ghi lại mà
không rời tay. Nhật ký viết lại sau phiên thì đã bị kết quả lệnh nhuộm màu — lệnh lãi thì nhớ mình tự tin,
lệnh lỗ thì nhớ mình đã ngờ ngợ. Sau feature này: giữ một cử chỉ, nói, thả ra là xong — không nút xác nhận,
không hộp thoại phải đóng, không bước đặt tên.

> **Mệnh đề trung tâm không phải "có thêm một ô ghi chú" mà là "nói ra được lúc đang nóng, và bản ghi đó
> không bao giờ mất".** Đó là lý do capability quan trọng thứ ba của feature này là *chép lời hỏng thì bản
> ghi âm vẫn còn* — nguồn gọi nó là **dòng quan trọng nhất trong cả bảng**.

## 2. Goals

### 2.1 Goals

* **Ghi lại lý do vào lệnh mà không rời tay và không rời mắt khỏi biểu đồ** — trọn bộ gói trong đúng một cử
  chỉ đã có sẵn trên tay cầm (trace UN-001).
* **Giọng nói không bao giờ đặt, sửa, đóng được một lệnh, và không điều hướng được** — ranh giới cứng, được
  hệ thống tự bảo vệ chứ không dựa vào việc người chơi nhớ (trace UN-002, UN-014).
* **Lời đã nói không bao giờ mất**, kể cả khi việc chép chữ thất bại hoàn toàn (trace UN-003, USC-002).
* **Việc ghi âm không bao giờ làm chậm hay cản một lệnh** (trace UN-006, USC-003).
* **Memo gắn đúng vào lệnh người chơi đang nghĩ tới**, và người chơi thấy đích đến **trước khi mở miệng**
  (trace UN-004).
* **Ghi memo là hoàn toàn tự nguyện** — không nhắc, không dấu đỏ, không ô trống chờ điền (trace UN-012).

### 2.2 Non-goals

* **KHÔNG** đặt lệnh bằng giọng nói. Không nằm trong sản phẩm ở **bất kỳ phiên bản nào** — đó chính là ranh
  giới CAP-02 bảo vệ.
* **KHÔNG** điều hướng menu bằng giọng nói. **KHÔNG** ghi âm liên tục suốt phiên — chỉ ghi khi người chơi
  chủ động giữ nút.
* **KHÔNG** nhắc nhở khi một lệnh đóng mà chưa có memo. Không thông báo, không dấu đỏ, không ô trống chờ
  điền. Một lệnh không memo là một lệnh bình thường. *(Quyết định có ý thức: nó bỏ đi đòn bẩy duy nhất để
  giữ tỷ lệ M1 — xem ghi chú Mục 7.)*
* **KHÔNG** sở hữu màn hình xem lại một lệnh → `daily-journal`. Feature này chỉ đặt **nội dung memo và ba
  thao tác nghe / sửa / xoá** lên khung đó.
* **KHÔNG** tìm kiếm memo theo chữ trên toàn nhật ký → `daily-journal`. Memo mở qua chính lệnh gắn với nó.
* **KHÔNG** nội dung lời khuyên, tín hiệu, phân tích, và việc soạn ra câu ngắn để đọc → `ai-desk`. Feature
  này nhận **nhu cầu được nghe**, và nhận ranh giới lời người chơi nói ra không bao giờ thành mệnh lệnh.
* **KHÔNG** phát memo đúng mốc thời gian trên tape → `trade-replay`. Feature này chỉ nhận ranh giới: bản ghi
  âm phải **nghe lại và tua được**.
* **KHÔNG** chấm điểm lệnh (`playbook-grading`) · nghi thức trước phiên (`daily-journal`) · xuất dữ liệu,
  sao lưu, và **đường xoá sạch toàn sản phẩm** (`reports-export`).
* **KHÔNG** nhận dạng giọng nói để phân biệt người nói — sản phẩm chỉ có một người dùng.

## 3. Personas

| Persona | Mô tả (1 dòng) | Nhu cầu chính | Nguồn |
|---------|----------------|---------------|-------|
| Người chơi — vai **người nói** | Trong phiên, tay trên tay cầm, **không rảnh mắt** | Nói ra lý do vào lệnh ngay lúc nó còn thật | URD Mục 2, UN-001, UN-007 |
| Người chơi — vai **người đọc lại** | Ngoài phiên, trước màn hình, có chuột và bàn phím | Tìm lại được điều mình đã nói, và sửa được chỗ máy chép sai | URD Mục 2, UN-008, UN-010 |

> Đây là **một người ở hai bối cảnh**, không phải hai persona — và cách chia này quyết định toàn bộ phân công
> thiết bị: nói bằng tay cầm trong phiên, sửa và xoá bằng chuột ngoài phiên. **AI desk là actor hệ thống**:
> nó nhận bản chép lời khi người chơi chủ động hỏi, và luôn nhận nội dung đó như **lời của người dùng**,
> không bao giờ như mệnh lệnh.

## 4. Capabilities

| ID | Capability | Priority | Rationale (vì sao tier này) | Traces to | Bóc ~N story | Done when (product outcome) | Sẵn sàng |
|----|------------|----------|-----------------------------|-----------|--------------|-----------------------------|----------|
| CAP-voice-journal-01 | Ghi memo bằng một cử chỉ giữ-để-nói trên tay cầm | P0 | Lõi giá trị feature; và cả feature tồn tại vì đúng giới hạn vật lý này | UN-001 | ~6 | Người chơi giữ, nói, thả ra là xong — không nút xác nhận, không hộp thoại, không bước đặt tên | ✅ |
| CAP-voice-journal-02 | Ranh giới cứng: giọng nói không đặt/sửa/đóng lệnh và không điều hướng | P0 | Điều kiện tồn tại. Và nó phải được **hệ thống tự bảo vệ**, không dựa vào việc người chơi nhớ | UN-002, UN-014 | ~4 | Cấu hình gán cử chỉ nói vào một nút thuộc đường đặt lệnh → **sản phẩm không khởi động**, và nói rõ nút nào sai cùng cách sửa | ✅ |
| CAP-voice-journal-03 | Chép lời hỏng thì bản ghi âm vẫn còn và vẫn gắn đúng lệnh | P0 | Nguồn gọi đây là **dòng quan trọng nhất trong cả bảng**. Giá trị huấn luyện phải sống sót kể cả khi chép chữ thất bại hoàn toàn | UN-003 | ~5 | Người chơi mở lệnh đó ra vẫn **nghe lại được chính giọng mình**; chỗ đáng lẽ là chữ thì nói rõ chưa chép được | ✅ |
| CAP-voice-journal-04 | Không bao giờ làm chậm hay cản một lệnh | P0 | Nếu ghi âm nằm trên đường đặt lệnh thì một tính năng nhật ký đã trở thành rủi ro giao dịch | UN-006 | ~4 | Vào thế chuẩn bị bắn giữa lúc đang ghi âm: memo **được gửi trọn vẹn**, và thao tác vào lệnh **không bị chặn chờ nó** | ✅ |
| CAP-voice-journal-05 | Memo gắn đúng vị thế đang chọn, và đích đến thấy được trước khi nói | P0 | Gắn nhầm lệnh là lỗi **không ai phát hiện ra** cho tới khi xem lại — lúc đó đã muộn | UN-004 | ~5 | Màn hình cho thấy memo sẽ gắn vào đâu **trước khi người chơi mở miệng** | ✅ |
| CAP-voice-journal-06 | Dấu hiệu đang ghi âm và đồng hồ đếm ngược | P0 | Đây là thứ giữ cho hành trình quan trọng nhất **không cảm thấy hỏng** dù phía sau lưu đúng | UN-007 | ~3 | Người chơi biết chắc mình đang được ghi và còn bao nhiêu thời gian | ✅ |
| CAP-voice-journal-07 | Dấu hiệu đang chép lời, không bao giờ treo | P0 | Một khoảng im lặng không rõ hệ thống còn sống hay không sẽ làm người chơi mất tin vào cả feature | UN-015 | ~3 | Có dấu hiệu đang chép lời; nó biến mất khi chữ hiện ra, hoặc chuyển thành "chưa chép được" — **không bao giờ treo mãi** | ✅ |
| CAP-voice-journal-08 | Bàn phím là đường thay thế **ngang hàng** | P0 | Giọng nói không nằm trên đường đặt lệnh nên không có lý do gì bắt nó phụ thuộc tay cầm. **Đây là thứ giữ feature sống khi dongle bị rút** | UN-011 | ~3 | Người chơi ghi memo được bằng bàn phím với đúng cách dùng (giữ để nói, thả để gửi) | ✅ |
| CAP-voice-journal-09 | Hỏi coach bằng **chính cử chỉ đó** | P1 | Không phải học thêm nút nào là giá trị thật, nhưng vòng hỏi-đáp vẫn chạy được bằng cách gõ | UN-005 | ~5 | Cùng một cử chỉ; đích đến do tab đang mở quyết định và **chốt tại thời điểm bắt đầu nói** | ✅ |
| CAP-voice-journal-10 | Sửa lại bản chép sai bằng bàn phím, ngoài phiên | P1 | Với giọng trộn Việt–Anh đây là **việc thường xuyên, không phải thỉnh thoảng** — hệ quả trực tiếp của quyết định chấp nhận chép kém | UN-008 | ~4 | Người chơi sửa nhanh gọn cho **hàng chục memo** trong một lần ngồi; bản ghi âm giữ nguyên làm bản gốc | ✅ |
| CAP-voice-journal-11 | Xoá một memo, và xoá sạch riêng dữ liệu giọng nói | P1 | Nghĩa vụ về dữ liệu cá nhân; nhưng chỉ có nghĩa sau khi đã tích luỹ được vài chục memo | UN-010 | ~5 | Thứ đã xoá biến mất thật, cả tiếng lẫn chữ, và phần còn lại của nhật ký không hỏng | ⚠️ chờ OQ-3 (ranh giới với đường xoá sạch của `reports-export`) |
| CAP-voice-journal-12 | Tắt hẳn tính năng giọng nói | P1 | Người chơi phải ra được khỏi một tính năng mình không dùng; nhưng v1 chưa có gì để tắt | UN-013 | ~2 | Tắt xong thì phần còn lại của sản phẩm chạy y nguyên, và các memo cũ vẫn đọc lại được | ✅ |
| CAP-voice-journal-13 | Nghe coach đọc thành tiếng | P2 | **Nhu cầu nền chưa được người chơi xác nhận** — và chính nguồn cũng để mặc định **tắt**, tức kế hoạch cũng chưa chắc. M6 sinh ra để hỏi nó có đáng giữ không | UN-009 | ~5 | Người chơi nghe được lời khuyên mà không rời mắt khỏi biểu đồ, và nó tự câm khi đang vũ trang hoặc đang bắn | 🔒 blocked by OQ-4 |

> **P0 = 8 capability, chỉ vượt ngưỡng 7 một cái** — và tám cái này là **một cử chỉ duy nhất cộng các điều
> kiện để nó đáng tin**: ghi được (01), không phá gì (02, 04), không mất (03), gắn đúng chỗ (05), người chơi
> biết chuyện gì đang xảy ra (06, 07), và vẫn dùng được khi tay cầm hỏng (08). Bỏ bất kỳ cái nào thì người
> chơi **ngừng ghi memo** — và đó là tín hiệu hỏng mà chính nguồn nêu ra.
>
> **CAP-13 ở P2 là một quyết định có ý thức, không phải sự bỏ quên.** Nó là nhánh duy nhất của feature mà
> cả người chơi lẫn tài liệu kế hoạch đều chưa chắc có cần hay không.

## 5. Upstream Traceability

| Capability | Traces to | Product outcome | Success metric |
|------------|-----------|-----------------|----------------|
| CAP-01, CAP-06, CAP-08 | UN-001, UN-007, UN-011 | Lý do vào lệnh được giữ lại ngay lúc còn thật | M1 Tỷ lệ lệnh có memo |
| CAP-03, CAP-07 | UN-003, UN-015 | Lời đã nói không bao giờ mất | M2 Memo mất |
| CAP-02, CAP-04 | UN-002, UN-014, UN-006 | Giọng nói không bao giờ chạm đường đặt lệnh | M3 Lần giọng nói ảnh hưởng đặt lệnh |
| CAP-05 | UN-004 | Memo nằm đúng chỗ người chơi sẽ tìm nó | M2 (mẫu số) |
| CAP-10 | UN-008 | Bản chép đủ để đọc lướt nhận ra memo nói về gì | M4 Chất lượng bản chép |
| CAP-04, CAP-06 | UN-006, UN-007 | Không phải chọn giữa "ghi memo" và "kịp vào lệnh" | M5 Nhịp thao tác |
| CAP-13 | UN-009 | Nghe được lời khuyên mà không rời mắt khỏi biểu đồ | M6 Đọc-thành-tiếng có được dùng không |
| CAP-09, CAP-11, CAP-12 | UN-005, UN-010, UN-013 | Cùng một cử chỉ hai đích đến · dọn được dữ liệu của mình · ra được khỏi tính năng | — |

## 6. Key Capability Interactions

* **Ghi một memo:** CAP-01 (giữ cử chỉ) → CAP-06 (dấu hiệu + đếm ngược) → CAP-05 xác định đích **trước khi
  nói** → thả ra → CAP-07 (dấu hiệu chép lời) → chữ hiện ra, **hoặc** CAP-03 giữ bản ghi âm và đọc là "chưa
  chép được".
* **Hỏi coach:** cùng cử chỉ CAP-01, nhưng CAP-09 đổi đích theo tab đang mở của `ai-desk` — và **đích chốt
  tại thời điểm bắt đầu nói**, nên đổi tab giữa chừng không đổi nơi câu đó tới.
* **Va chạm với đường đặt lệnh:** CAP-04 đảm bảo hai chiều — vào thế chuẩn bị bắn giữa lúc đang ghi âm thì
  memo **được gửi trọn vẹn** chứ không bị vứt; và máy chủ đang bận chép lời cũng **không làm chậm** một lệnh.
* **Tay cầm hỏng:** CAP-08 thay chỗ CAP-01 với đúng cách dùng, không phải một bản hạ cấp.
* **Ranh giới ra ngoài:** `tilt-meter` dùng **sự kiện "đã ghi một memo"** làm đường ra sớm khỏi khoảng khoá —
  nó **không bao giờ nhận nội dung memo**; `daily-journal` sở hữu khung màn hình mà CAP-10 và CAP-11 đặt ba
  thao tác nghe/sửa/xoá lên; `trade-replay` phát bản ghi âm đúng mốc thời gian và **ghi đè luật gắn memo của
  CAP-05** khi đang ở màn xem lại; `reports-export` sở hữu đường xoá sạch **toàn sản phẩm**, khác đường xoá
  riêng giọng nói của CAP-11.

## 7. Success Metrics

| Metric | Baseline | Target | Measurement Method | Timeframe |
|--------|----------|--------|--------------------|-----------|
| M1 Tỷ lệ lệnh có memo | Chưa có — xác lập tỷ lệ trung bình từ 10 phiên đầu | Cao hơn baseline sau 3 tháng, **và tỷ lệ tháng thứ 3 không thấp hơn tháng thứ 1 quá 10 điểm phần trăm** | Đếm số lệnh có memo trên tổng số lệnh, đọc cuối tháng, **kèm đường xu hướng theo tháng**. Memo quá ngắn không tính vào tử số | Hằng quý |
| M2 Memo mất | **Không cần baseline** — ràng buộc tuyệt đối, không phải xu hướng | 100% memo đã ghi vẫn nghe lại được và vẫn gắn đúng lệnh, kể cả những memo có phần chữ thất bại | Đối chiếu **hai nguồn độc lập**: số lần thả nút sau khi nói (đếm ngay trên màn hình lúc ghi) so với số memo có mặt khi mở lại lệnh. **Chỉ đếm memo đã lưu thì memo mất trước khi lưu sẽ vô hình** | Hằng tháng |
| M3 Lần giọng nói ảnh hưởng đặt lệnh | **Không cần baseline** — ranh giới, không phải xu hướng | 0 lần một thao tác đặt lệnh bị chặn, phải bấm lại, hoặc nhận phản hồi rung **muộn tới mức người chơi nhận ra**, khi trùng thời điểm với một memo đang ghi hoặc đang chép. Và 0 lệnh phát sinh từ lời nói | Đếm số lần như trên, đọc cuối tháng | Hằng tháng |
| M4 Chất lượng bản chép | Chưa có — xác lập từ 20 memo đầu | **≥ 70% trong 20 memo gần nhất** tự chấm ở mức "đúng ý" hoặc "sai nhưng đoán ra" | Người chơi tự chấm 20 memo gần nhất theo ba mức: đúng ý / sai nhưng đoán ra / không hiểu gì | Hằng quý |
| M5 Nhịp thao tác | Chưa có — xác lập cảm nhận chủ quan từ 10 phiên đầu | Người chơi không thấy phải chọn giữa "ghi memo" và "kịp vào lệnh"; số memo bỏ dở vì sợ lỡ nhịp **tiến về không** | Đếm số lần vào thế chuẩn bị bắn khi đang ghi âm và kết quả của chúng, kèm ghi nhận chủ quan cuối phiên | Hằng quý |
| M6 Đọc-thành-tiếng có được dùng không | **Không cần baseline** — mặc định là tắt, nên **mọi lần bật đều là tín hiệu** | Sau một tháng dùng thật, đọc-thành-tiếng vẫn được bật ở đa số phiên | Đếm số phiên có bật, và số lần bật rồi tắt lại trong cùng phiên. **Bật rồi tắt lại trong cùng phiên ≥ 3 lần → coi như nhánh này không đáng giữ** | Một lần sau tháng đầu, rồi hằng quý |

> **M4 phải tự chấm tay, không đo tự động được** — "đọc lướt có hiểu không" là phán đoán của người đọc.
> **Ngưỡng 70% chính là mốc xét lại quyết định chấp nhận bản chép kém**; dưới ngưỡng thì quyết định đó không
> đứng vững và phải mở lại.
>
> **Nếu M1 tụt dần, phương án ứng phó là làm cử chỉ dễ hơn — không phải thêm nhắc nhở.** Quyết định "không
> nhắc khi lệnh đóng chưa có memo" đã bỏ đi đòn bẩy duy nhất để giữ tỷ lệ này, và đó là **lựa chọn có ý
> thức**: một nhật ký nhắc nhở là một nhật ký bị bỏ.
>
> **M6 là thước đo duy nhất hỏi "tính năng này có đáng tồn tại không"** thay vì "nó chạy tốt không". Đó là
> lý do CAP-13 ở P2.

## 8. Dependencies

| Dependency | Owner | Status | Needed-by | Impact if Late |
|------------|-------|--------|-----------|----------------|
| Khái niệm **"vị thế đang chọn"** | `order-execution` (FR-041) | On Track | Cùng lúc CAP-05 | Memo không biết gắn vào đâu khi có nhiều vị thế |
| Chuỗi vũ trang–bắn để **không** nằm trên nó | `order-execution` | On Track | Cùng lúc CAP-04 | Không có gì để kiểm chứng ranh giới quan trọng thứ hai |
| Máy chủ đủ sức chép lời | Người chơi (hạ tầng) | At Risk | Cùng lúc CAP-07 | Tự hạ mức chất lượng, xấu nhất là tắt hẳn phần chép chữ — ghi âm vẫn chạy |
| Mic và quyền dùng mic trên Chrome | Người chơi | On Track | Cùng lúc CAP-01 | CAP-08 (bàn phím) là đường thay thế ngang hàng, nên không chặn cả feature |
| Tab tư vấn để làm đích đến thứ hai của cử chỉ | `ai-desk` (FR-033) | On Track | Cùng lúc CAP-09 | CAP-09 lùi lại; ghi memo vẫn chạy bình thường |
| **Màn hình xem lại một lệnh** làm khung cho ba thao tác nghe/sửa/xoá | `daily-journal` | **At Risk** | Cùng lúc CAP-10, CAP-11 | **Ba journey J1, J4, J5 mất chỗ đứng** — đây là phụ thuộc liên feature, không phải giả định nội bộ |
| Ranh giới với đường xoá sạch **toàn sản phẩm** | `reports-export` | **Blocked** | Trước khi CAP-11 vào Next | Hai đường xoá đá nhau: hoặc xoá thiếu, hoặc người chơi tưởng đã xoá hết mà chưa — xem OQ-3 |
| Nội dung lời khuyên để đọc thành tiếng | `ai-desk` | At Risk | Cùng lúc CAP-13 | CAP-13 đã ở P2 và bị khoá, nên không ảnh hưởng lịch |

## 9. Assumptions & Validation

| Assumption | Impact if Wrong | Validation | Status |
|------------|-----------------|------------|--------|
| Ký ức viết lại sau phiên bị kết quả lệnh làm méo, nên nói ngay lúc vào lệnh mới giữ được suy nghĩ thật | **Toàn bộ lý do tồn tại của feature yếu đi** — chỉ còn tiện lợi, không còn cần thiết | Đối chiếu sau 10 phiên: so memo nói lúc vào lệnh với ghi chú viết lại sau phiên cùng lệnh đó | Open (URD A-01) |
| Bản chép chữ chủ yếu để **đọc lướt**; nghe lại bản ghi âm mới là cách đọc kỹ | Nếu người chơi chỉ đọc chữ và gần như không nghe lại, bản chép sai thành **hỏng nghiêm trọng** chứ không phải phiền nhẹ — và quyết định chấp nhận chép kém phải xét lại | Theo dõi số lần nghe lại so với số lần chỉ đọc chữ, sau 10 phiên | Open (URD A-02) |
| Người chơi chấp nhận đợi khoảng chục giây để có chữ sau khi thả nút | Thấy quá lâu và bỏ thói quen ghi memo → feature mất tác dụng dù chạy đúng | Đo thời gian thật khi có sản phẩm; quá lâu thì hạ mức chất lượng chép lời | Open (URD A-03) |
| Bản chép cho giọng trộn Việt–Anh **vẫn đủ để nhận ra memo nói về chuyện gì** khi đọc lướt | Sai tới mức đọc không ra gì → CAP-10 biến thành việc **gõ lại toàn bộ memo bằng tay**, nặng tới mức người chơi sẽ bỏ | Thu 20 câu giọng thật rồi chấm theo thang của M4 | Open (URD A-04 — hướng xử lý đã chốt, mức sai thật thì chưa đo) |
| Xoá là mất hẳn, không thùng rác, không hoàn tác | Lỡ tay xoá nhầm một memo quan trọng thì không lấy lại được | Bù lại bằng cửa xác nhận có chủ đích và việc từ chối xoá khi đang trong phiên | **Confirmed** 2026-08-28 (URD A-05) |
| "Xoá sạch giọng nói" xoá **cả bản ghi âm lẫn bản chép**, qua một đường riêng của feature này | Người chơi hiểu là chỉ xoá tiếng → bất ngờ khi mất luôn nội dung nhật ký giọng nói | Thông báo cho `reports-export` để hai đường xoá không đá nhau | **Confirmed** 2026-08-28 (URD A-06) — nhưng ranh giới hai đường vẫn treo ở OQ-3 |
| Màn hình xem lại một lệnh **thuộc `daily-journal`** | `daily-journal` trượt lịch hoặc dựng khung khác đi → ba journey mất chỗ đứng | Chốt giao diện giữa hai feature khi viết SRS của `daily-journal` | **Confirmed** 2026-08-28 (URD A-07) — là phụ thuộc liên feature, không phải giả định |
| Người chơi sẽ bỏ dở nhật ký gõ tay sau vài tuần, nên giọng nói là cách duy nhất giữ được thói quen | M1 mất mốc so sánh và giá trị của feature nhỏ hơn tưởng | Ghi nhận trong 10 phiên đầu xem có ghi chú gõ tay nào không | Open (URD A-08) |
| Người chơi giữ được cặp nút vai tới khoảng một phút mà không khó chịu | Mỏi tay → ngừng ghi memo; M1 tụt và CAP-08 trở thành đường chính chứ không phải dự phòng | Đo trong 10 phiên đầu; mỏi thì đổi sang cặp nút sau lưng | Open (URD A-09) |
| Máy chủ hiện có đủ sức chép lời ở mức chất lượng dùng được | Máy yếu → tự hạ mức, xấu nhất là mất hẳn phần chữ; feature còn lại chỉ là ghi âm | Đo sức máy thật lúc dựng | Open (URD A-10 → OQ-5) |
| Người chơi **thật sự muốn nghe** lời khuyên hơn là đọc nó | Toàn bộ nhánh đọc-thành-tiếng là công sức bỏ đi | Bật thử hai tuần và xem có tự tắt lại không — chính là M6 | Open (URD A-11 → OQ-4) |
| Đích đến của lời nói **chốt tại thời điểm bắt đầu nói** | Chốt lúc thả nút → người chơi đổi tab giữa chừng rồi ngạc nhiên vì câu đi sai chỗ, trái thẳng lời hứa của CAP-09 | Xác nhận với người chơi | Open (URD A-12 🔶) |
| "Lệnh vừa đóng gần nhất" chỉ tính trong phiên hiện tại và trong một khoảng đủ gần | Không có giới hạn thì memo lúc 23h gắn vào lệnh đóng lúc 20h — làm hỏng ý nghĩa của chính memo đó | Chốt khoảng thời gian cụ thể | Open (URD A-13 🔶 → OQ-6) |

## 10. Product Risks

| Risk | Probability | Impact | Mitigation | Owner |
|------|-------------|--------|------------|-------|
| **Người chơi bỏ thói quen ghi memo sau vài tuần** — nhật ký nào cũng dễ dùng tốt trong hai tuần đầu | High | High | M1 đo **đường xu hướng theo tháng**, không so một mốc. Ứng phó là **làm cử chỉ dễ hơn** (đổi sang cặp nút sau lưng, hoặc dùng bàn phím) — **không phải thêm nhắc nhở** | Người chơi |
| Bản chép sai nhiều tới mức CAP-10 thành việc gõ lại toàn bộ | High | High | M4 đặt ngưỡng 70% làm mốc **xét lại chính quyết định chấp nhận chép kém**; đo bằng 20 câu giọng thật trước khi khoá cách sửa | Người chơi |
| Mỏi tay khi giữ cặp nút vai tới một phút | Medium | Medium | CAP-08 là đường **ngang hàng**, không phải hạ cấp; đổi sang cặp nút sau lưng nếu tay cầm hỗ trợ | Người chơi |
| Máy chủ không đủ sức chép lời | Medium | Medium | Tự hạ mức chất lượng **và nói rõ đang chạy ở mức nào**; xấu nhất tắt hẳn phần chép chữ — **ghi âm vẫn chạy**. Không bao giờ âm thầm chậm đi | Người chơi |
| **Gói sao lưu cũ làm sống lại giọng nói đã cố ý xoá** | Medium | High | Người chơi phải được nói rõ điều này ở **đúng hai chỗ**: lúc xoá riêng giọng nói và lúc xoá sạch toàn sản phẩm. Gói đã tạo nằm ngoài vòng kiểm soát — xem OQ-3 | Người chơi |
| `daily-journal` trượt lịch → ba journey mất chỗ đứng | Medium | Medium | Chốt giao diện giữa hai feature sớm; trong lúc chờ, CAP-10/CAP-11 vẫn dựng được logic, chỉ thiếu khung để đặt lên | Người chơi |
| Cảm giác bị nghe lén cả buổi tối vì đèn báo mic bật suốt phiên | Low | Medium | Cho chọn kiểu **chỉ mở mic đúng lúc nhấn nút**, đổi lại mỗi lần nhấn chậm hơn một chút. Đây là lựa chọn của người chơi, không phải mặc định áp đặt | Người chơi |

## 11. Release & Launch Readiness

### 11.1 Release Horizon

| Horizon | Capabilities | Target | Status |
|---------|--------------|--------|--------|
| Now | CAP-voice-journal-01 → 08 (P0) | Chưa chốt lịch | planned — sau `order-execution` |
| Next | CAP-voice-journal-09, 10, 12 (P1) | Chưa chốt lịch | planned |
| Next (khoá) | CAP-voice-journal-11 (P1) | Chưa chốt lịch | blocked by OQ-3 |
| Later | CAP-voice-journal-13 (P2) | Chưa chốt lịch | blocked by OQ-4 |

> **`tilt-meter` phụ thuộc CAP-01 và CAP-08 ở mức chặn.** Đường ra sớm khỏi khoảng khoá của feature đó dựa
> hoàn toàn vào sự kiện "đã ghi một memo" — và đặc biệt vào **đường bàn phím** (CAP-08) khi không có mic.

### 11.2 Launch Readiness

| Workstream | Must-pass criteria | Status | Guardrail metric (threshold → decision) |
|------------|--------------------|--------|-----------------------------------------|
| Ranh giới không-chạm-lệnh | Nói một câu mang hình thức mệnh lệnh đặt lệnh; kiểm cTrader demo **không** có vị thế nào mới. Dựng cấu hình gán cử chỉ nói vào nút đường đặt lệnh — sản phẩm **phải từ chối khởi động** | ⬜ | Một lệnh phát sinh từ lời nói → **dừng feature ngay**; đây là sự cố nghiêm trọng nhất có thể xảy ra |
| Lời nói không mất | Làm việc chép lời hỏng có chủ đích rồi ghi một memo; mở lệnh tương ứng phải **nghe lại được đúng câu vừa nói** | ⬜ | Một memo mất → dừng dùng feature để ghi nhật ký cho tới khi sửa; **một trường hợp mất là một lỗi, không phải một con số phần trăm** |
| Không cản đường đặt lệnh | Vào thế chuẩn bị bắn giữa lúc đang ghi âm; và vào lệnh trong lúc máy chủ đang chép lời | ⬜ | Lệnh chậm hơn ở mức người chơi nhận ra → tách hẳn ghi âm và chép lời khỏi đường đặt lệnh trước khi dùng tiếp |
| Gắn đúng lệnh | Với hai vị thế mở, ghi một memo và kiểm nó nằm ở **vị thế đang chọn** | ⬜ | Gắn nhầm → tắt tính năng gắn tự động, bắt chọn tay, vì gắn nhầm là lỗi không ai phát hiện ra |
| Đường bàn phím ngang hàng | Rút dongle rồi ghi memo bằng bàn phím với đúng cách dùng (giữ để nói, thả để gửi) | ⬜ | Không dùng được → **`tilt-meter` mất đường ra khỏi khoảng khoá**; phải sửa trước khi feature đó dùng được |
| Chất lượng bản chép | Thu 20 câu giọng thật, tự chấm theo ba mức của M4 | ⬜ | Dưới 70% → quyết định chấp nhận chép kém **không đứng vững**, phải mở lại trước khi khoá cách sửa ở CAP-10 |

## 12. Open Questions

* [ ] OQ-1 *(kế thừa URD OQ-7, chung với `ai-desk` OQ-1)*: Trần số memo trong một giờ là bao nhiêu, và người
  chơi có cần **biết trước** con số đó không? `ai-desk` đã chọn "phải biết trước" cho câu tương đương — nên
  thống nhất hai feature.
* [ ] OQ-2 *(kế thừa URD OQ-8, chung với `tilt-meter` OQ-2)*: Có nên cho ghi memo **trong lúc đang vũ trang**
  không? Hiện thiết kế chặn, nhưng đó đúng là khoảnh khắc lý do vào lệnh còn nóng nhất. Mở ra thì phải chứng
  minh nó không đụng gì tới đường đặt lệnh. 🔶 **Tạm quyết:** giữ nguyên chặn — `tilt-meter` FR-030 đã giải
  tình huống khó nhất (huỷ ARM khi khoá bắt đầu), nên lý do chính để mở đã bớt cấp bách.
* [ ] OQ-3 *(kế thừa URD A-06, chung với `reports-export` OQ-5)*: Đường **xoá sạch giọng nói** của feature
  này và đường **xoá sạch toàn sản phẩm** phân định thế nào để không đá nhau? Và vế thứ ba: CAP-11 hứa "xoá là
  mất hẳn", nhưng **một gói sao lưu cũ khôi phục về sẽ mang giọng nói đó quay lại** — người chơi được nói điều
  này ở đâu và lúc nào? **Chặn CAP-11.**
* [ ] OQ-4 *(kế thừa URD A-11)*: Người chơi **thật sự muốn nghe** lời khuyên hơn là đọc nó không? **Chặn
  CAP-13.** Chính nguồn cũng để mặc định tắt, tức kế hoạch cũng chưa chắc. M6 là thước đo trả lời câu này.
* [ ] OQ-5 *(kế thừa URD OQ-9)*: Ngưỡng sức máy tối thiểu để bật phần chép lời là bao nhiêu, và dưới ngưỡng
  đó thì mặc định là **tự hạ mức** hay **tắt hẳn**?
* [ ] OQ-6 *(kế thừa URD A-13)*: "Lệnh vừa đóng gần nhất" tính trong khoảng thời gian bao lâu? Không có giới
  hạn thì một memo cuối buổi có thể gắn vào một lệnh đóng từ nhiều giờ trước.
* [ ] OQ-7 *(`trade-replay` OQ-9 hỏi ngược sang đây)*: Khi đang ở màn xem lại, memo mới gắn vào **lệnh đang
  xem** thay vì vị thế đang mở — đây là **ngoại lệ của CAP-05**. 🔶 **Tạm quyết:** **nhận ngoại lệ này**;
  đích đến phải là thứ người chơi đang nhìn thấy. *Nếu sai:* một bài học về lệnh này nằm trong bản ghi của
  lệnh khác, và **không ai phát hiện ra**.

---

> **Nguồn:** `voice-journal-urd.md` (15 nhu cầu, 6 journey, 25 tình huống ngoại lệ, 6 thước đo, 13 giả định) ·
> bốn tài liệu nền `docs/_shared/` · ranh giới nhận từ `order-execution`, `ai-desk`, `tilt-meter`,
> `daily-journal`, `trade-replay`, `reports-export`. **Chưa có BRD**.
>
> **🔶 Hai quyết định thay user:** OQ-2 (giữ nguyên việc chặn ghi memo lúc đang vũ trang) và OQ-7 (nhận ngoại
> lệ gắn memo ở màn xem lại). **OQ-3 và OQ-4 em cố ý không quyết** — cái đầu chạm nghĩa vụ về dữ liệu cá
> nhân, cái sau quyết định một nhánh có tồn tại hay không.
