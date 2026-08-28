---
type: urd
feature: voice-journal
status: draft
updated: 2026-08-28
links: ["docs/_shared/project-profile.md", "docs/_shared/system-overview.md", "docs/_shared/definitions.md", "docs/_shared/operating-environment.md", "docs/order-execution/order-execution-urd.md", "docs/ai-desk/ai-desk-urd.md", "docs/playbook-grading/playbook-grading-urd.md"]
---

# voice-journal — User Requirements Document

## 1. Purpose

Ghi lại nhu cầu của người chơi quanh việc **dùng giọng nói làm cách duy nhất để nói chuyện với sản
phẩm trong lúc hai tay đang bận** — nói ra lý do vào lệnh, hỏi coach một câu, và nghe câu trả lời —
và quanh việc điều đó không bao giờ được phép chạm tới đường đặt lệnh.

Feature này tồn tại vì một giới hạn vật lý rất đơn giản: hai tay đang cầm tay cầm thì không gõ phím
được. Cái mất đi không phải là chữ, mà là **suy nghĩ thật tại thời điểm ra quyết định** — thứ duy
nhất giải thích được vì sao tối nay mình vào lệnh đó. Vì vậy nhu cầu trung tâm ở đây không phải "có
thêm một ô ghi chú" mà là **"nói ra được lúc đang nóng, và bản ghi đó không bao giờ mất"**.

### User Problem & Current Experience

| User | Current Situation | Problem | User Consequence | Evidence |
|---|---|---|---|---|
| Người chơi | Đang giao dịch, hai tay đặt trên tay cầm, mắt trên biểu đồ | Không có cách nào ghi lại lý do vào lệnh mà không rời tay | Lý do vào lệnh không bao giờ được ghi — nó chỉ tồn tại trong đầu vài phút rồi tan | `phase-08` ("You cannot type a journal while trading. You can talk.") |
| Người chơi | Sau phiên, ngồi viết lại nhật ký từ trí nhớ | Ký ức đã bị kết quả lệnh nhuộm màu — lệnh lãi thì nhớ mình tự tin, lệnh lỗ thì nhớ mình đã ngờ ngợ | Nhật ký ghi một câu chuyện dựng lại sau, không phải suy nghĩ thật lúc đó; nhìn lại không học được gì đúng | **Assumption** — xem A-01 |
| Người chơi | Muốn hỏi ý kiến giữa phiên khi thấy một tình huống lạ | Gõ câu hỏi cho AI desk phải rời tay khỏi tay cầm | Hoặc không hỏi, hoặc hỏi xong thì cơ hội đã trôi | `phase-08` ("Point the desk at an AI tab first and the same gesture asks the coach a question instead"), `ai-desk-urd.md` UN-006 |
| Người chơi | Công cụ nhật ký hiện có (Edgewonk, TradeZella) đều nhập bằng bàn phím, sau phiên | Ghi nhật ký thành một công việc riêng cần ngồi xuống làm | Dễ bỏ dở sau vài tuần, và khi đó không còn gì để nhìn lại | **Assumption** — xem A-08. Nguồn chỉ chứng minh hai công cụ đó tồn tại và nhập bằng bàn phím (`README.md`, `docs/_shared/project-profile.md`), **không** chứng minh người chơi này sẽ bỏ dở |
| Người chơi | Coach có nhận xét, nhưng nhận xét đó nằm dưới dạng chữ trên màn hình | Đang dán mắt vào biểu đồ thì không đọc được chữ ở chỗ khác | Lời khuyên tới đúng lúc nhưng không tới được người chơi | **Assumption** — xem A-11. Nền: `phase-08` (Coach TTS), `ai-desk-urd.md` Mục 3 |

> **Về nhãn nguồn.** `plans/260824-1506-evening-forex-gold-gamepad/phase-08-...` là **tài liệu kế
> hoạch xây dựng** — nó mô tả thứ định làm, không phải quan sát hành vi người chơi thật. Những dòng
> dẫn `phase-08` ở trên và ở Mục 4 là **thiết kế đã được người chơi chấp nhận khi lập kế hoạch**,
> không phải bằng chứng thực nghiệm. Chỗ nào là suy đoán về hành vi thì mang nhãn `Assumption` và
> có một dòng tương ứng ở Mục 8.

## 2. User Types

| Tier | User Type | Context | Primary Goal | Pain Points |
|---|---|---|---|---|
| primary | **Người chơi** | Vừa là người nói (trong phiên, tay trên tay cầm, không rảnh mắt), vừa là người đọc lại (ngoài phiên, trước màn hình, có chuột và bàn phím) | Nói ra lý do vào lệnh ngay lúc nó còn thật, rồi tìm lại được nó khi ngồi nhìn lại | Không gõ được lúc đang giao dịch; ký ức viết lại sau đã méo; sợ công cụ ghi âm làm hỏng nhịp đặt lệnh |

> **Không có secondary user.** Công cụ cá nhân một người dùng. **AI desk là actor hệ thống**: nó
> nhận bản chép lời khi người chơi chủ động hỏi, và luôn nhận nội dung đó như **lời của người dùng**,
> không bao giờ như mệnh lệnh điều khiển. Sàn cTrader/Spotware không tham gia feature này.
> Xem `docs/_shared/project-profile.md`.

## 3. Scope Boundaries

### In Scope

* Người chơi ghi lý do vào lệnh bằng **một cử chỉ giữ-để-nói trên tay cầm**: giữ, nói, thả ra là xong — không có thao tác xác nhận, không có màn hình nào phải đóng. Tổ hợp nút cụ thể xem Mục 7.
* Lời nói được **chép thành chữ tự động**, và việc chép đó chạy ngay trên máy chủ của mình — dữ liệu giọng nói không đi ra ngoài.
* Bản ghi **gắn đúng vào vị thế đang được chọn trên màn hình**; không có vị thế nào mở thì gắn vào phiên và vào lệnh vừa đóng gần nhất trong chính phiên đó.
* **Cùng cử chỉ đó hỏi coach** khi người chơi đang mở một tab tư vấn — không phải học thêm nút nào, và đích đến nhìn thấy được trên màn hình *trước khi* nói.
* Người chơi biết mình đang ghi âm và còn bao nhiêu giây; thả nút xong thì biết bản chép đang chạy và khi nào xong.
* **Giọng nói không bao giờ mở, sửa, đóng được một lệnh, và không điều hướng được** — đây là ranh giới cứng, không phải quy ước. Cấu hình gán nhầm cử chỉ nói vào một nút thuộc đường đặt lệnh thì sản phẩm **không khởi động**.
* **Chép lời hỏng thì bản ghi âm vẫn còn và vẫn gắn với lệnh** — giá trị huấn luyện sống sót kể cả khi việc chép chữ thất bại hoàn toàn.
* Người chơi **sửa lại bản chép sai bằng bàn phím ngoài phiên**, không phải sửa lúc đang giao dịch. Bản đã sửa **ghi đè** bản máy chép; bản ghi âm luôn là bản gốc để đối chiếu. *(Chốt 2026-08-28)*
* Người chơi **nghe được lời khuyên của coach đọc thành tiếng** — mặc định tắt, bật tắt được, và tự câm khi đang vũ trang hoặc đang bắn.
* Bàn phím là **đường thay thế ngang hàng** để ghi memo khi tay cầm không dùng được.
* Người chơi **xoá được từng bản ghi lẻ**, và có một **đường xoá sạch riêng cho dữ liệu giọng nói** — xoá cả tiếng lẫn chữ, không đụng phần nhật ký còn lại. Xoá là mất hẳn, không hoàn tác. *(Chốt 2026-08-28)*
* **Nghe lại, sửa và xoá một memo diễn ra ngay tại nơi người chơi xem lại một lệnh.** Màn hình đó thuộc feature `daily-journal`; feature này chỉ sở hữu **nội dung memo và ba thao tác nghe / sửa / xoá** đặt trên đó. *(Chốt 2026-08-28)*
* Người chơi **tắt hẳn được tính năng giọng nói**, và phần còn lại của sản phẩm không đổi gì.

> **Phạm vi mới so với kế hoạch.** Đường **xoá sạch riêng cho giọng nói** chưa có trong
> `phase-13` — kế hoạch mới chỉ có một nút xoá sạch toàn sản phẩm (xoá cả nhật ký, ảnh đính kèm,
> tape). Đây là phạm vi phát sinh từ quyết định 2026-08-28 và cần được `reports-export` biết tới
> khi viết SRS, để hai đường xoá không đá nhau.

### Out of Scope

* **Màn hình xem lại một lệnh** (cái khung chứa mọi thứ về một lệnh) → feature `daily-journal`. URD này chỉ đặt nội dung memo và ba thao tác nghe/sửa/xoá lên khung đó.
* **Tua lại một lệnh qua tape và nghe memo phát đúng mốc thời gian đã nói** → feature `trade-replay`. URD này chỉ nhận ranh giới: bản ghi âm phải **nghe lại và tua được**, không phải nghe một mạch từ đầu.
* **Tìm kiếm memo theo chữ trên toàn bộ nhật ký** → feature `daily-journal`. *(Chốt 2026-08-28 — memo mở qua chính lệnh gắn với nó.)*
* **Nội dung lời khuyên, tín hiệu, phân tích, và việc soạn ra câu ngắn để đọc** → feature `ai-desk`. URD này nhận **nhu cầu được nghe**, và nhận ranh giới lời người chơi nói ra không bao giờ thành mệnh lệnh cho AI.
* **Chấm điểm lệnh theo luật playbook** → feature `playbook-grading`. Bản ghi âm không tham gia chấm điểm.
* **Nghi thức chuẩn bị trước phiên, tự đánh giá đầu và cuối buổi, tổng kết ngày** → feature `daily-journal`.
* **Xuất dữ liệu, sao lưu, báo cáo, và đường xoá sạch toàn sản phẩm** → feature `reports-export`.
* **Toàn bộ đường đặt lệnh** — vũ trang, bắn, đóng, hạn mức, khoá phiên → feature `order-execution`.
* **Đặt lệnh bằng giọng nói.** Không nằm trong sản phẩm này ở bất kỳ phiên bản nào — đó chính là ranh giới UN-002 và UN-014 bảo vệ.
* **Điều hướng menu bằng giọng nói.**
* **Ghi âm liên tục suốt phiên.** Chỉ ghi khi người chơi chủ động giữ nút.
* Nhận dạng giọng nói để phân biệt người nói — sản phẩm chỉ có một người dùng.

## 4. User Needs

| ID | User | Context / Trigger | User Need | Expected Outcome | Importance | Evidence |
|---|---|---|---|---|---|---|
| UN-001 | Người chơi | Vừa vào một lệnh, lý do vẫn còn rõ trong đầu, hai tay đang trên tay cầm | Nói ra lý do đó **mà không rời tay và không rời mắt khỏi biểu đồ** | Giữ cử chỉ nói, nói, thả ra là xong. Không có nút xác nhận, không có hộp thoại phải đóng, không có bước đặt tên. Toàn bộ việc ghi nhật ký một lệnh gói trong đúng một cử chỉ đã có sẵn trên tay cầm | Critical | `phase-08` ("Hold `LB + RB`, say why you took it, let go") |
| UN-002 | Người chơi | Mọi lúc, kể cả lúc đang ghi âm giữa một tình huống căng | Chắc chắn rằng **giọng nói không bao giờ đặt, sửa, đóng được một lệnh** | Không tồn tại đường nào biến lời nói thành lệnh — kể cả khi người chơi nói đúng câu "mua vàng ngay". Ranh giới này không phụ thuộc vào cách người chơi nói, cũng không phụ thuộc vào việc bản chép lời có đúng hay không | Critical | `phase-08` ("It cannot place, close, modify, or navigate") |
| UN-003 | Người chơi | Việc chép lời thất bại — quá tải, quá giờ, hoặc hỏng hẳn | **Không mất lời mình đã nói**, dù không có chữ nào được chép ra | Bản ghi âm vẫn được lưu, vẫn gắn đúng lệnh, vẫn nghe lại được; chỗ đáng lẽ là chữ thì nói rõ là chưa chép được, chứ không biến bản ghi thành một dòng trống. Người chơi mở lệnh đó ra vẫn nghe lại được chính giọng mình | Critical | `phase-08` ("the audio is still stored and still linked to the trade ... this is the most important row in this table") |
| UN-004 | Người chơi | Nói xong một memo giữa phiên đang có vị thế mở | Memo **gắn đúng vào lệnh mình đang nghĩ tới**, không phải một lệnh nào khác | Memo gắn vào **vị thế đang được chọn trên màn hình** — cùng khái niệm "vị thế đang chọn" mà `order-execution` UN-013 đã dùng khi có nhiều vị thế. Màn hình cho thấy memo sẽ gắn vào đâu **trước khi người chơi mở miệng**. Không có vị thế nào mở thì gắn vào phiên và vào lệnh vừa đóng gần nhất **trong chính phiên đó** | High | `phase-08` (bảng routing), `order-execution-urd.md` UN-013 (khái niệm vị thế đang chọn) |
| UN-005 | Người chơi | Giữa phiên, thấy một tình huống muốn hỏi ý kiến | Hỏi coach **bằng chính cử chỉ đã dùng để ghi memo**, và biết trước lời mình nói sẽ đi đâu | Cùng một cử chỉ; đích đến do tab đang mở quyết định, và tab đó **hiện trên màn hình trước khi người chơi mở miệng**. Đích đến **chốt tại thời điểm bắt đầu nói** — đổi tab giữa chừng không đổi nơi câu đó tới, nên không bao giờ có chuyện nói xong mới biết vừa nói vào đâu (🔶 xem A-12) | High | `phase-08` ("routing needs **zero new bindings** ... which is on screen before you speak") |
| UN-006 | Người chơi | Đang ghi âm hoặc đang chờ chép lời thì có cơ hội vào lệnh | Việc ghi âm **không bao giờ được làm chậm hay cản một lệnh** | Ghi âm và chép lời chạy song song với đường đặt lệnh, không bao giờ nằm trên nó. Vào thế chuẩn bị bắn giữa lúc đang ghi âm thì memo **được gửi đi trọn vẹn**, không bị vứt bỏ, và thao tác vào lệnh không bị chặn lại chờ nó. Máy chủ đang bận chép lời cũng không làm chậm một lệnh | Critical | `phase-08` ("Voice is never on the order path"; "graceful stop-and-submit, never a discard"), `system-overview.md` (journal path) |
| UN-007 | Người chơi | Trong lúc giữ nút nói | Biết chắc mình **đang được ghi**, và biết còn bao nhiêu thời gian | Có dấu hiệu rõ ràng đang ghi âm cùng đồng hồ đếm ngược tới giới hạn khoảng một phút; hết giờ thì dừng và gửi đi phần đã nói, không cắt cụt im lặng. Đây là thứ giữ cho hành trình quan trọng nhất (J1) không **cảm thấy** hỏng dù phía sau lưu đúng | Critical | `phase-08` (`voice.max_seconds: 60`, "client stops with a visible countdown") |
| UN-008 | Người chơi | Ngoài phiên, đọc lại một memo và thấy máy chép sai | **Sửa lại được câu chữ** cho đúng thứ mình đã nói | Sửa bằng chuột và bàn phím ngoài phiên; trong lúc giao dịch không có thao tác sửa nào cả. Bản đã sửa ghi đè bản máy chép; bản ghi âm luôn giữ nguyên làm bản gốc. **Đây là việc thường xuyên, không phải thỉnh thoảng** — hệ quả trực tiếp của quyết định OQ-1, nên cách sửa phải nhanh gọn cho hàng chục memo, không phải một hộp thoại nặng cho một trường hợp hiếm | High | Confirmed 2026-08-28 (người chơi chốt) |
| UN-009 | Người chơi | Coach có một nhận xét, mắt đang dán vào biểu đồ | **Nghe** được nhận xét đó thay vì phải đọc | Lời khuyên đọc thành tiếng, **mặc định tắt** và bật tắt được bất cứ lúc nào; **tự câm khi đang vũ trang hoặc đang bắn**; và không bao giờ đọc ra một con số tiền — đúng luật chung của sản phẩm. Nhận xét bị ngắt giữa chừng thì bỏ hẳn, không đọc lại | Medium | **Assumption** — xem A-11. Nền thiết kế: `phase-08` ("default `off`", "auto-mute while `ARMED` or `FIRE`", "never speak a dollar figure") |
| UN-010 | Người chơi | Nghe lại một memo và thấy không muốn giữ; hoặc muốn dọn sạch toàn bộ giọng nói của mình | **Xoá được** — cả lẻ từng cái lẫn sạch toàn bộ | Xoá được một memo ngay tại chỗ nghe lại nó, và có một đường xoá sạch **riêng cho dữ liệu giọng nói** — xoá cả bản ghi âm lẫn bản chép, không đụng phần nhật ký còn lại. **Xoá là mất hẳn, không hoàn tác**, nên thao tác xoá phải có chủ đích rõ ràng và bị từ chối khi đang trong phiên hoặc còn vị thế mở | High | Confirmed 2026-08-28 (người chơi chốt). Nền: `docs/_shared/project-profile.md` (compliance — phải nêu rõ nơi lưu và cách xoá) |
| UN-011 | Người chơi | Tay cầm hết pin, rút dongle, hoặc đang ngồi gần bàn phím | Ghi memo được **mà không cần tay cầm** | Bàn phím là đường thay thế **ngang hàng**, không phải đường phụ hạ cấp — vì giọng nói không nằm trên đường đặt lệnh nên không có lý do gì bắt nó phụ thuộc tay cầm | Medium | `phase-08` ("keyboard `V` hold is an equal-status fallback ... this is what keeps the feature alive when the dongle is out") |
| UN-012 | Người chơi | Một lệnh đóng mà chưa có memo nào | **Không bị nhắc, không bị đánh dấu thiếu sót** | Ghi memo là hoàn toàn tự nguyện. Không có thông báo, không có dấu đỏ, không có ô trống chờ điền. Một lệnh không memo là một lệnh bình thường | Medium | Confirmed 2026-08-28 (người chơi chốt) |
| UN-013 | Người chơi | Không muốn dùng giọng nói, hoặc máy không có mic | **Tắt hẳn được** mà không mất gì khác | Tắt tính năng thì phần còn lại của sản phẩm chạy y nguyên — đặt lệnh, chấm điểm, AI desk đều không đổi. Các memo cũ vẫn đọc lại được | Medium | `phase-08` ("`voice.enabled: false` removes the feature; nothing else depends on it") |
| UN-014 | Người chơi | Lúc khởi động sản phẩm, sau khi ai đó (hoặc chính mình) sửa cấu hình | Ranh giới "giọng nói không chạm đường đặt lệnh" được **hệ thống tự bảo vệ**, không dựa vào việc mình nhớ | Cấu hình gán cử chỉ nói vào một nút thuộc đường đặt lệnh thì sản phẩm **từ chối khởi động** thay vì chạy với ràng buộc đã hỏng — và nói rõ **nút nào sai, sửa thế nào**, ở nơi người chơi đang đứng, không phải chỉ trong nhật ký kỹ thuật | Critical | `phase-08` ("enforced by a config boot-fail ... not by convention"; "`voice.bindings: [RT]` refuses to boot") |
| UN-015 | Người chơi | Ngay sau khi thả nút nói | Biết **việc chép lời đang chạy**, thay vì một khoảng im lặng không rõ hệ thống còn sống hay không | Có dấu hiệu cho biết đang chép lời và nó biến mất khi chữ hiện ra. Nếu chép lời hỏng thì dấu hiệu đó chuyển thành trạng thái "chưa chép được" (UN-003), không bao giờ treo mãi | High | `phase-08` ("the HUD shows a 'transcribing…' pill, not a hung request") |

## 5. Prioritized User Journeys

### Journey 1: Nói ra lý do vào lệnh, giữa phiên

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Vừa vào một lệnh, lý do còn rõ trong đầu
* __Expected outcome:__ Lý do đó được giữ lại, gắn đúng lệnh, và tìm lại được sau phiên
* __Related needs:__ UN-001, UN-004, UN-006, UN-007, UN-012, UN-015

1) Người chơi giữ cử chỉ nói; dấu hiệu ghi âm hiện lên cùng đồng hồ đếm ngược, và màn hình cho thấy memo sẽ gắn vào vị thế nào.
2) Nói ra lý do vào lệnh, mắt vẫn trên biểu đồ.
3) Thả nút. Không phải xác nhận gì, không phải đóng gì.
4) Một dấu hiệu cho biết đang chép lời; ít lâu sau chữ hiện ra.
5) Memo nằm cùng chỗ với vị thế đang được chọn.

__Independent verification:__ Ghi một memo trong lúc đang có một vị thế mở, nói một câu đủ đặc
trưng để không lẫn được. Mở bản ghi của **đúng lệnh đó** ra sau đó — phải thấy memo, nghe lại được
đúng câu vừa nói, và bản chép chữ tương ứng. Kiểm thêm hai vế trong cùng lần chạy: **(a)** không có
bước nào đòi rời tay khỏi tay cầm; **(b)** đóng một lệnh khác **không** có memo — không thông báo
nào, không dấu thiếu sót nào xuất hiện (UN-012). Không cần journey nào khác để xác nhận.

### Journey 2: Máy chép lời chết, lời nói vẫn còn

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Việc chép lời quá tải, quá giờ, hoặc hỏng hẳn
* __Expected outcome:__ Người chơi vẫn nghe lại được chính giọng mình; chỉ mất phần chữ
* __Related needs:__ UN-003, UN-004, UN-015

1) Người chơi ghi một memo như bình thường.
2) Việc chép lời thất bại.
3) Dấu hiệu "đang chép lời" chuyển thành **chưa chép được** — không phải một dòng trống, không phải một thông báo lỗi kỹ thuật, và không treo mãi.
4) Bản ghi âm vẫn ở đó, vẫn gắn đúng lệnh, vẫn bấm nghe lại được.

__Independent verification:__ Làm việc chép lời hỏng có chủ đích rồi ghi một memo. Mở lệnh tương
ứng — phải nghe lại được đúng câu vừa nói, và trạng thái "chưa chép được" phải đọc ra rõ ràng.
Đây là journey phải hoạt động kể cả khi mọi thứ khác của feature hỏng.

### Journey 3: Hỏi coach bằng chính cử chỉ đó

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Giữa phiên, thấy một tình huống muốn hỏi, tay không rời tay cầm được
* __Expected outcome:__ Câu hỏi tới được coach, và câu trả lời quay về; không có lệnh nào bị ảnh hưởng
* __Related needs:__ UN-005, UN-001, UN-002, UN-014

1) Người chơi mở tab tư vấn trên bàn làm việc — tab đang mở nhìn thấy được trên màn hình.
2) Giữ cử chỉ nói và nói câu hỏi.
3) Lời nói đi tới coach như một câu hỏi, không phải như một memo.
4) Câu trả lời quay về đúng chỗ vẫn dùng để đọc lời khuyên.

__Independent verification:__ Cùng một cử chỉ, hai bối cảnh. Mở tab tư vấn rồi nói — phải ra một
câu trả lời. Đóng bàn làm việc rồi nói cùng câu đó — phải ra một memo gắn với lệnh, **không** ra
câu trả lời. Hai kết quả khác nhau trên cùng một thao tác chính là bằng chứng đích đến do tab quyết
định. Kiểm thêm: nói một câu mang hình thức mệnh lệnh đặt lệnh, kiểm trên cTrader demo phải **không**
có vị thế nào mới.

### Journey 4: Sửa lại bản chép sai, sau phiên

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Đọc lại memo và thấy máy chép sai — với giọng nói trộn Việt–Anh thì đây là chuyện thường xuyên
* __Expected outcome:__ Câu chữ đúng lại, và bản gốc vẫn còn để đối chiếu
* __Related needs:__ UN-008, UN-003

1) Ngoài phiên, người chơi mở lại một lệnh cũ và đọc memo của nó.
2) Thấy câu chữ sai.
3) Sửa lại bằng bàn phím, đủ nhanh để làm được cho nhiều memo liên tiếp trong một lần ngồi.
4) Bản đã sửa ghi đè bản máy chép; bản ghi âm giữ nguyên không đụng tới.

__Independent verification:__ Sửa một memo, đóng lại, mở lại — phải thấy đúng câu đã sửa. Bấm nghe
lại — phải vẫn nghe đúng câu gốc chưa sửa. Kiểm chiều ngược: trong lúc đang giao dịch, không tồn tại
đường nào dẫn tới thao tác sửa này.

### Journey 5: Xoá một memo, hoặc xoá sạch giọng nói

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Nghe lại thấy không muốn giữ, hoặc muốn dọn sạch toàn bộ dữ liệu giọng nói của mình
* __Expected outcome:__ Thứ đã xoá biến mất thật, và phần còn lại của nhật ký không hỏng
* __Related needs:__ UN-010, UN-004

1) Người chơi mở một memo và chọn xoá nó.
2) Vì không có hoàn tác, thao tác xoá đòi một hành động **có chủ đích rõ ràng** — không phải một cú bấm lướt qua.
3) Memo biến khỏi mọi nơi nó từng xuất hiện, cả tiếng lẫn chữ.
4) Đường xoá sạch toàn bộ giọng nói nằm trong cài đặt, dùng cùng mức cửa như trên, và **bị từ chối khi đang trong phiên hoặc còn vị thế mở**.
5) Lệnh từng có memo đó vẫn tra ra được bình thường, chỉ là không còn memo.

__Independent verification:__ Xoá một memo rồi mở lại chính lệnh đó — bản ghi lệnh vẫn còn nguyên,
memo không còn cả tiếng lẫn chữ, và không chỗ nào hiện ra lỗi. Riêng đường xoá sạch chỉ kiểm được
bằng dữ liệu bỏ đi (hoặc trên một bản dựng thử), vì nó phá luôn dữ liệu mà J1, J2, J4 cần — đừng
chạy nó trên nhật ký thật.

### Journey 6: Nghe coach đọc thành tiếng

* __User:__ Người chơi · __Importance:__ Medium
* __Trigger:__ Người chơi bật đọc thành tiếng và coach có một nhận xét
* __Expected outcome:__ Nghe được lời khuyên mà không phải rời mắt khỏi biểu đồ, và nó không bao giờ nói chen vào lúc đang bắn
* __Related needs:__ UN-009

1) Người chơi bật đọc thành tiếng (mặc định là tắt).
2) Coach có một nhận xét; nó được đọc lên.
3) Người chơi vũ trang một lệnh — giọng đọc **câm ngay**.
4) Nhận xét bị ngắt giữa chừng **không được đọc lại** — nó vẫn còn dưới dạng chữ để đọc bằng mắt. Chỉ nhận xét **mới** mới được đọc lên.

__Independent verification:__ Bật đọc thành tiếng, chờ một nhận xét, rồi vũ trang giữa lúc đang đọc
— tiếng phải tắt ngay, và sau khi thoát khỏi trạng thái vũ trang thì **không** tự đọc lại câu vừa
bị ngắt. Kiểm chiều ngược: cài mặc định của một máy mới phải là **tắt** — checkpoint này chỉ chạy
được lúc dựng máy lần đầu.

## 6. User Exceptions & Edge Conditions

| Situation | User Impact | Expected User-facing Outcome | Related Journey / Need |
|---|---|---|---|
| **Cấu hình gán cử chỉ nói vào một nút thuộc đường đặt lệnh** | Ranh giới an toàn quan trọng nhất bị phá bởi một dòng cấu hình sai | Sản phẩm **không khởi động**, và nói rõ **nút nào sai cùng cách sửa** ở nơi người chơi đang đứng — không chỉ trong nhật ký kỹ thuật | J3 / UN-014, UN-002 |
| **Mic bị từ chối, không có mic, hoặc trình duyệt không hỗ trợ** | Nhấn giữ nút mà không có gì xảy ra, không hiểu vì sao | Chức năng nói bị vô hiệu hoá **một cách nhìn thấy được**, kèm lý do bằng lời thường ("chưa cho phép mic" / "máy không có mic"). Mọi thứ khác chạy nguyên vẹn; bàn làm việc vẫn nhận câu hỏi gõ tay | J1, J3 / UN-007, UN-013 |
| **Mic biến mất giữa lúc đang nói** (rút tai nghe, thiết bị ngắt) | Đang nói dở thì mất tiếng mà vẫn tưởng đang được ghi | Dừng ngay và nói rõ đã mất mic; **phần đã nói được giữ lại và gửi đi**, không vứt bỏ cả memo | J1 / UN-003, UN-007 |
| **Giữ nút nói trong lúc đang vũ trang, hoặc đang giữ chốt an toàn** | Đúng khoảnh khắc lý do còn nóng nhất thì lại bị từ chối im lặng | **Không vào ghi âm**, nhưng người chơi thấy rõ là chưa ghi được và **lúc nào thì ghi được** — không phải một cú bấm rơi vào hư không. Có nên cho nói lúc đang vũ trang không thì xem OQ-8 | J1 / UN-001, UN-006 |
| **Vào thế chuẩn bị bắn giữa lúc đang ghi âm** | Sợ mất memo, hoặc sợ memo cản mất lệnh | Memo **được gửi đi trọn vẹn**, và thao tác vào lệnh đi bình thường không chờ nó. Không phải chọn giữa hai thứ | J1 / UN-006, UN-002 |
| **Vào lệnh trong lúc máy chủ đang chép lời** (không phải đang ghi âm) | Đây mới là lúc máy chủ bận nhất, nên là lúc dễ làm chậm lệnh nhất | Lệnh đi với đúng tốc độ như khi không có memo nào đang chép. Không có cảnh báo, không có bước chờ | J1 / UN-006 |
| **Mất mạng hoặc gửi bản ghi thất bại** | Vừa nói xong một câu quan trọng thì mất luôn | Hệ thống tự thử gửi lại; vẫn hỏng thì **giao bản ghi âm cho người chơi giữ lại** thay vì vứt đi, và nói rõ là chưa lưu được | J1 / UN-003 |
| **Nói quá thời lượng cho phép** | Đang nói dở thì bị cắt giữa câu mà không biết | Đồng hồ đếm ngược cho thấy sắp hết; tới giới hạn thì **dừng và gửi đi phần đã nói**, không vứt bỏ. Người chơi giữ nút tiếp lần nữa để nói phần còn lại | J1 / UN-007 |
| **Bấm nhầm rồi thả ngay, memo gần như rỗng** | Memo rác gắn vào lệnh, và làm phồng chính con số mà USC-001 đo | Một lần giữ quá ngắn **không tạo memo nào** và cũng không báo lỗi — coi như chưa từng bấm | J1 / UN-001, USC-001 |
| **Bấm nhầm một nút bumper thay vì giữ cả cặp** | Biểu đồ nhảy khung thời gian giữa lúc đang định nói | Bấm một nút vẫn là đổi khung thời gian như cũ, và **không** khởi động ghi âm. Giữ cả cặp mới vào ghi âm, và khi đó khung thời gian **không** đổi | J1 / UN-001 |
| **Đổi tab bàn làm việc giữa lúc đang giữ nút nói** | Nói xong mới biết câu đó vừa đi đâu — đúng thứ UN-005 hứa không xảy ra | Đích đến **chốt tại thời điểm bắt đầu nói**; đổi tab giữa chừng không đổi nơi câu đó tới. Màn hình vẫn cho thấy đích đến đã chốt trong suốt lúc nói (🔶 xem A-12) | J3 / UN-005 |
| **Từ hai vị thế mở trở lên** | Memo gắn nhầm lệnh, và người chơi không biết cho tới khi xem lại | Memo gắn vào **vị thế đang được chọn**, và màn hình cho thấy rõ nó sẽ gắn vào cái nào **trước khi** người chơi mở miệng | J1 / UN-004 |
| **Ghi memo đầu phiên, khi chưa lệnh nào đóng và chưa vị thế nào mở** | Không có gì để gắn vào | Memo gắn vào **phiên**, và hiện rõ nó đang gắn vào phiên chứ không vào lệnh nào | J1 / UN-004 |
| **Lệnh vừa đóng gần nhất đã cách đây quá lâu** | Memo lúc 23h gắn vào lệnh đóng lúc 20h thì vô nghĩa | "Lệnh vừa đóng gần nhất" chỉ tính trong **phiên hiện tại và trong một khoảng đủ gần**; quá khoảng đó thì gắn vào phiên như trên (🔶 xem A-13 — khoảng cụ thể chốt khi viết SRS) | J1 / UN-004 |
| **Coach đang không dùng được, mà lời nói lại đang hướng vào tab tư vấn** | Nói xong một câu hỏi rồi mất luôn, không ai trả lời | Câu đó **hạ xuống thành memo** kèm một dòng cho biết coach đang không dùng được — không bao giờ rơi mất | J3 / UN-005, UN-003 |
| **Bản chép sai câu chữ** | Đọc lại memo không hiểu mình đã nói gì | Bản chép chỉ để đọc lướt; **bản ghi âm mới là bản gốc**, luôn nghe lại được. Sai thì sửa lại bằng bàn phím ngoài phiên. Với giọng trộn Việt–Anh thì đây là trạng thái **thường gặp, không phải ngoại lệ** | J4 / UN-008, UN-003 |
| **Nhiều memo nói liên tiếp trong thời gian ngắn** | Cái sau chen mất cái trước, hoặc máy đơ | Các memo xếp hàng và lần lượt được chép; vượt quá sức chứa thì nói rõ là hiện chưa nhận thêm, thay vì im lặng nuốt mất. Bản ghi âm của mọi memo đã nhận đều được giữ | J1 / UN-003, UN-015 |
| **Chạm trần số memo cho phép trong một giờ** | Đang muốn nói thì bị chặn mà không hiểu vì sao | Nói rõ đã chạm trần và khi nào nói tiếp được. Con số này người chơi biết trước hay chỉ hiện lúc chạm thì xem OQ-7 | J1 / UN-007 |
| **Máy chủ không đủ sức chép lời** | Mất tính năng, hoặc chất lượng tụt, mà không biết vì sao | Hệ thống **tự hạ mức chất lượng chép lời** và nói rõ đang chạy ở mức nào; trường hợp xấu nhất là tự tắt hẳn phần chép lời và nói rõ vì sao — ghi âm vẫn chạy. Không bao giờ âm thầm chậm đi | J1, J2 / UN-013, UN-003 |
| **Đèn báo đang ghi âm hiện suốt phiên** | Cảm giác bị nghe lén cả buổi tối | Chọn được kiểu chỉ mở mic đúng lúc nhấn nút, đổi lại mỗi lần nhấn chậm hơn một chút. Đây là lựa chọn của người chơi, không phải mặc định áp đặt | J1 / UN-007 |
| **Tay cầm hết pin hoặc rút dongle giữa phiên** | Mất luôn khả năng ghi memo cho tới khi tìm được pin | Vẫn ghi memo được bằng bàn phím với đúng cách dùng (giữ để nói, thả để gửi) — đường ngang hàng, không phải bản hạ cấp | J1 / UN-011 |
| **Nhận xét của coach bị ngắt giữa chừng vì có nhận xét mới hoặc vì vũ trang** | Nghe được nửa câu rồi mất, không rõ còn gì phía sau | Câu bị ngắt **không đọc lại**, nhưng vẫn còn nguyên dưới dạng chữ để đọc bằng mắt | J6 / UN-009 |
| **Xoá một memo đang được nơi khác dùng tới** (vd một lệnh cũ đang mở xem) | Sợ xoá memo làm hỏng bản ghi lệnh | Lệnh vẫn nguyên vẹn và vẫn tra ra được; chỉ phần memo biến mất. Không có bản ghi nào khác hỏng theo | J5 / UN-010 |
| **Bấm xoá sạch giọng nói giữa lúc đang có phiên hoặc còn vị thế mở** | Xoá nhầm giữa lúc đang giao dịch, không lấy lại được | **Bị từ chối**, kèm lý do và điều kiện để làm được — cùng mức bảo vệ mà `reports-export` đặt cho đường xoá sạch toàn sản phẩm | J5 / UN-010 |
| **Tắt hẳn tính năng giọng nói** | Sợ tắt xong thì nhật ký cũ hỏng theo | Các memo cũ vẫn đọc lại và nghe lại được; chỉ không ghi thêm được nữa. Đặt lệnh, chấm điểm, AI desk không đổi gì | J1 / UN-013 |

## 7. User-side Constraints

* **Chỉ chạy trên Chrome desktop**, và người chơi phải cho phép dùng mic **một lần** trong cài đặt trước khi nói được lần đầu (kế thừa ràng buộc môi trường của `order-execution`).
* **Cử chỉ giữ-để-nói hiện là giữ đồng thời cặp nút vai (`LB+RB`)**, hoặc giữ một phím trên bàn phím. Tổ hợp này **có thể đổi sang cặp nút sau lưng** nếu tay cầm hỗ trợ — đây là ràng buộc hiện tại, không phải một phần của nhu cầu.
* **Phải giữ nút liên tục tới khi nói xong**, có thể tới khoảng một phút. Không thoải mái thì bàn phím là đường ngang hàng (UN-011). Xem A-09.
* **Một lần nói giới hạn khoảng một phút** — nói dài hơn phải chia thành nhiều lần.
* **Có trần số memo trong một giờ.** Nói liên tục quá nhiều sẽ chạm trần và phải chờ. Xem OQ-7.
* **Chất lượng chép lời phụ thuộc sức máy chủ.** Máy yếu thì hệ thống tự hạ mức chất lượng; máy quá yếu thì **tự tắt phần chép lời** — khi đó vẫn ghi âm được và vẫn nghe lại được, chỉ không có chữ. Xem A-10.
* **Bản chép cho giọng trộn Việt–Anh sẽ sai khá nhiều.** Đây là đánh đổi đã chọn (OQ-1): bản ghi âm là bản chính, bản chép là thứ đọc lướt và sửa tay khi cần.
* **Bản ghi âm giữ lại vô thời hạn** — không tự hết hạn. Chỉ mất khi người chơi chủ động xoá. Dung lượng tăng dần theo tháng nhưng ở mức không đáng kể.
* **Dữ liệu giọng nói không rời khỏi máy chủ của người chơi.** Không có đường gửi ra dịch vụ ngoài, kể cả khi cấu hình sai.
* **Memo mở qua chính lệnh gắn với nó**, không tìm được bằng cách gõ một cụm từ. Muốn tìm theo chữ thì đó là việc của `daily-journal`.
* Chỉ tài khoản demo. Nội dung memo và lời coach đọc ra **không phải lời khuyên đầu tư**.

## 8. Assumptions & Validation

| ID | Assumption | Impact if Wrong | Validation Status | Next Action |
|---|---|---|---|---|
| A-01 | Ký ức viết lại sau phiên bị kết quả lệnh làm méo, nên nói ngay lúc vào lệnh mới giữ được suy nghĩ thật | Nếu viết lại sau phiên cũng đủ tốt, toàn bộ lý do tồn tại của feature yếu đi — chỉ còn tiện lợi, không còn cần thiết | Chưa xác nhận — suy từ `phase-08` (đặt việc nói ngay tại thời điểm vào lệnh) và từ thực hành nhật ký giao dịch nói chung | Đối chiếu sau 10 phiên: so memo nói lúc vào lệnh với ghi chú viết lại sau phiên cùng lệnh đó |
| A-02 | Bản chép chữ chủ yếu để **đọc lướt**; nghe lại bản ghi âm mới là cách đọc kỹ | Nếu người chơi thực tế chỉ đọc chữ và gần như không bao giờ nghe lại, bản chép sai trở thành hỏng nghiêm trọng chứ không phải phiền nhẹ — và quyết định OQ-1 phải xét lại | Chưa xác nhận — suy từ `phase-08` ("the audio is retained and is the real record"). Quyết định OQ-1 (2026-08-28) đứng trên chính giả định này | Theo dõi số lần nghe lại so với số lần chỉ đọc chữ, sau 10 phiên |
| A-03 | Người chơi chấp nhận đợi khoảng chục giây để có chữ sau khi thả nút | Nếu thấy quá lâu và bỏ thói quen ghi memo, feature mất tác dụng dù chạy đúng | Chưa xác nhận — `phase-08` ước tính 7–11 giây cho một memo 10 giây và nêu đúng rủi ro này | Đo thời gian thật khi có sản phẩm; quá lâu thì hạ mức chất lượng chép lời |
| A-04 | Bản chép cho giọng trộn Việt–Anh tuy sai nhiều nhưng vẫn đủ để **nhận ra memo nói về chuyện gì** khi đọc lướt | Nếu sai tới mức đọc không ra gì, bản chép thành vô dụng và UN-008 biến thành việc gõ lại toàn bộ memo bằng tay — nặng tới mức người chơi sẽ bỏ | **Đã xác nhận hướng xử lý** 2026-08-28 (OQ-1: chấp nhận chép kém, bản ghi âm là bản chính). Mức sai thật thì chưa đo | Thu 20 câu giọng thật rồi chấm theo thang của USC-004, trước khi khoá cách sửa ở SRS |
| A-05 | Xoá là mất hẳn, không có thùng rác và không hoàn tác | Lỡ tay xoá nhầm một memo quan trọng thì không lấy lại được | **Đã xác nhận** 2026-08-28 (OQ-2) — bù lại bằng cửa xác nhận có chủ đích và việc từ chối xoá khi đang trong phiên | Không còn hành động; kiểm lại nếu người chơi báo đã xoá nhầm |
| A-06 | "Xoá sạch giọng nói" xoá **cả bản ghi âm lẫn bản chép**, và là một đường riêng của feature này | Nếu người chơi hiểu là chỉ xoá tiếng, họ sẽ bất ngờ khi mất luôn nội dung nhật ký giọng nói | **Đã xác nhận** 2026-08-28 (OQ-4 + quyết định đường xoá riêng) | Thông báo cho `reports-export` khi viết SRS để hai đường xoá không đá nhau |
| A-07 | Màn hình xem lại một lệnh — nơi đặt ba thao tác nghe / sửa / xoá memo — **thuộc `daily-journal`** | Nếu `daily-journal` trượt lịch hoặc dựng màn hình đó khác đi, ba journey J1, J4, J5 mất chỗ đứng | **Đã xác nhận** 2026-08-28 — đây là **phụ thuộc liên feature**, không phải giả định nội bộ | Chốt giao diện giữa hai feature khi viết SRS của `daily-journal` |
| A-08 | Người chơi sẽ bỏ dở việc ghi nhật ký bằng bàn phím sau vài tuần, nên giọng nói là cách duy nhất giữ được thói quen | Nếu thực ra họ vẫn duy trì được nhật ký gõ tay, USC-001 mất mốc so sánh và giá trị của feature nhỏ hơn tưởng | Chưa xác nhận — nguồn chỉ chứng minh Edgewonk/TradeZella nhập bằng bàn phím, không chứng minh hành vi của người chơi này | Ghi nhận trong 10 phiên đầu xem có ghi chú gõ tay nào không |
| A-09 | Người chơi giữ được cặp nút vai tới khoảng một phút mà không khó chịu | Nếu mỏi tay thì người chơi ngừng ghi memo — USC-001 tụt, và bàn phím (UN-011) trở thành đường chính chứ không phải dự phòng | Chưa xác nhận — `phase-08` nêu đúng rủi ro này với tín hiệu hỏng cụ thể ("the player stops recording memos") | Đo trong 10 phiên đầu; mỏi thì đổi sang cặp nút sau lưng |
| A-10 | Máy chủ hiện có đủ sức chép lời ở mức chất lượng dùng được | Máy yếu thì hệ thống tự hạ mức, và trường hợp xấu nhất là mất hẳn phần chữ — feature còn lại chỉ là ghi âm | Chưa xác nhận — `phase-08` mô tả bậc thang tự hạ cấp và yêu cầu việc hạ cấp phải nhìn thấy được | Đo sức máy thật lúc dựng; kết quả quyết định mức mặc định. Xem OQ-9 |
| A-11 | Người chơi thật sự muốn **nghe** lời khuyên hơn là đọc nó | Nếu bật thử rồi tắt luôn, toàn bộ nhánh đọc-thành-tiếng (UN-009, J6) là công sức bỏ đi | Chưa xác nhận — không có xác nhận trực tiếp nào từ người chơi; `phase-08` cũng để mặc định **tắt**, tức chính kế hoạch cũng chưa chắc | Bật thử hai tuần và xem có tự tắt lại không — xem USC-006 |
| A-12 | Đích đến của lời nói (memo hay câu hỏi cho coach) chốt tại **thời điểm bắt đầu nói** | Nếu chốt lúc thả nút, người chơi có thể đổi tab giữa chừng rồi ngạc nhiên vì câu đi sai chỗ — trái thẳng lời hứa của UN-005 | 🔶 Quyết định thay user 2026-08-28 — `phase-08` chỉ nói đích đến nhìn thấy trước khi nói, không nói chốt lúc nào | Xác nhận với người chơi khi viết SRS |
| A-13 | "Lệnh vừa đóng gần nhất" chỉ tính trong phiên hiện tại và trong một khoảng thời gian đủ gần | Không có giới hạn thì một memo cuối buổi có thể gắn vào một lệnh đóng từ nhiều giờ trước, làm hỏng ý nghĩa của chính memo đó | 🔶 Quyết định thay user 2026-08-28 — `phase-08` chỉ nói "the last closed trade", không nêu giới hạn | Chốt khoảng thời gian cụ thể khi viết SRS |

## 9. User Success Criteria

| ID | User Outcome | Baseline | Target | Measurement | Review Period |
|---|---|---|---|---|---|
| USC-001 | Người chơi thật sự dùng giọng nói để ghi lý do vào lệnh, thay vì bỏ sau vài tuần | **Chưa có** — sản phẩm chưa viết code; xác lập tỷ lệ trung bình từ 10 phiên đầu | Tỷ lệ lệnh có ít nhất một memo cao hơn baseline sau 3 tháng, **và tỷ lệ của tháng thứ 3 không thấp hơn tháng thứ 1 quá 10 điểm phần trăm**. Vế thứ hai mới là thứ đáng lo — nhật ký nào cũng dễ dùng tốt trong hai tuần đầu | Đếm số lệnh có memo trên tổng số lệnh, đọc cuối mỗi tháng, kèm đường xu hướng theo tháng. Memo quá ngắn không tính vào tử số | Hằng quý |
| USC-002 | Lời đã nói **không bao giờ mất**, kể cả khi việc chép chữ hỏng | **Không cần baseline** — đây là ràng buộc tuyệt đối, không phải xu hướng | 100% memo đã ghi vẫn nghe lại được và vẫn gắn đúng lệnh, kể cả những memo có phần chữ thất bại. Một trường hợp mất là một lỗi phải sửa, không phải một con số phần trăm để cải thiện | Đối chiếu **hai nguồn độc lập**: số lần thả nút sau khi nói (đếm được ngay trên màn hình lúc ghi) so với số memo có mặt khi mở lại lệnh. Đọc cuối mỗi phiên — nếu chỉ đếm memo đã lưu thì memo mất trước khi lưu sẽ vô hình | Hằng tháng |
| USC-003 | Giọng nói không bao giờ ảnh hưởng tới việc đặt lệnh | **Không cần baseline** — đây là ranh giới, không phải xu hướng | Không lần nào một thao tác đặt lệnh **bị chặn, phải bấm lại, hoặc nhận phản hồi rung muộn tới mức người chơi nhận ra** khi trùng thời điểm với một memo đang ghi hoặc đang chép. Và không lệnh nào phát sinh từ lời nói | Đếm số lần như trên, đọc cuối mỗi tháng | Hằng tháng |
| USC-004 | Bản chép đủ để đọc lướt nhận ra memo nói về chuyện gì, không phải lúc nào cũng bật nghe | **Chưa có** — xác lập từ 20 memo đầu | **Ít nhất 70% trong 20 memo gần nhất** tự chấm ở mức "đúng ý" hoặc "sai nhưng đoán ra". Dưới ngưỡng này nghĩa là quyết định OQ-1 (chấp nhận chép kém) không đứng vững và phải mở lại | Người chơi tự chấm 20 memo gần nhất theo ba mức "đúng ý / sai nhưng đoán ra / không hiểu gì" | Hằng quý |
| USC-005 | Việc nói không làm hỏng nhịp thao tác trên tay cầm | **Chưa có** — xác lập cảm nhận chủ quan từ 10 phiên đầu | Người chơi không thấy phải chọn giữa "ghi memo" và "kịp vào lệnh"; số memo bị bỏ dở vì sợ lỡ nhịp tiến về không | Đếm số lần vào thế chuẩn bị bắn khi đang ghi âm và kết quả của chúng, kèm ghi nhận chủ quan cuối phiên | Hằng quý |
| USC-006 | Nhánh đọc-thành-tiếng có thật sự được dùng, hay chỉ nằm đó | **Không cần baseline** — mặc định là tắt, nên mọi lần bật đều là tín hiệu | Sau một tháng dùng thật, đọc-thành-tiếng vẫn được bật ở đa số phiên. Nếu người chơi bật rồi tắt lại ngay trong cùng phiên từ 3 lần trở lên, coi như nhánh này không đáng giữ và đưa ra quyết định bỏ hay làm lại | Đếm số phiên có bật, và số lần bật rồi tắt lại trong cùng phiên | Một lần sau tháng đầu, rồi hằng quý |

> **Về ranh giới đo lường.** USC-001 tới USC-005 đọc từ dữ liệu của chính feature này nên đo được
> ngay khi feature chạy — không phải chờ feature khác. USC-004 phải **tự chấm tay** chứ không đo tự
> động được, vì "đọc lướt có hiểu không" là phán đoán của người đọc (xem A-02).
>
> **Nếu USC-001 tụt dần.** Quyết định "không nhắc khi lệnh đóng chưa có memo" (UN-012) đã bỏ đi đòn
> bẩy duy nhất để giữ tỷ lệ này. Nên khi tỷ lệ giảm, phương án ứng phó là **làm cử chỉ dễ hơn**
> (đổi sang cặp nút sau lưng, hoặc dùng bàn phím theo UN-011) — không phải thêm nhắc nhở.

## 10. Open Questions

* [x] OQ-1: Nói trộn Việt–Anh thì chép lời bằng cách nào? — **Resolved 2026-08-28:** giữ cách chép lời hiện tại và **chấp nhận bản chép kém**; bản ghi âm là bản chính, bản chép là thứ đọc lướt và sửa tay khi cần. Hệ quả đã áp: UN-008 nêu rõ sửa là việc thường xuyên, USC-004 đặt ngưỡng 70% làm mốc xét lại quyết định này, A-04 ghi lại đánh đổi.
* [x] OQ-2: Xoá một memo có hoàn tác được không? — **Resolved 2026-08-28:** không hoàn tác, không thùng rác; bù lại thao tác xoá phải có chủ đích rõ ràng và bị từ chối khi đang trong phiên hoặc còn vị thế mở.
* [x] OQ-3: Sửa bản chép xong có giữ lại bản máy chép không? — **Resolved 2026-08-28:** ghi đè luôn. Bản ghi âm vẫn là bản gốc để đối chiếu.
* [x] OQ-4: "Xoá sạch toàn bộ dữ liệu giọng nói" nghĩa là gì? — **Resolved 2026-08-28:** xoá **cả tiếng lẫn chữ**, qua một đường riêng của feature này, không đụng phần nhật ký còn lại.
* [x] OQ-5: Bản ghi âm giữ bao lâu thì tự hết hạn? — **Resolved 2026-08-28:** **không tự hết hạn**, giữ vô thời hạn. Chỉ mất khi người chơi chủ động xoá.
* [x] OQ-6: Memo có tìm kiếm được theo chữ không? — **Resolved 2026-08-28:** không. Memo mở qua chính lệnh gắn với nó; việc tìm kiếm toàn nhật ký thuộc `daily-journal`. USC-004 đã được viết lại theo đúng phạm vi này.
* [ ] OQ-7: Trần số memo trong một giờ là bao nhiêu, và người chơi có cần biết trước con số đó không, hay chỉ hiện lúc chạm trần? `ai-desk` đã chọn cho câu hỏi tương tự là **phải biết trước**; nên thống nhất hai feature.
* [ ] OQ-8: Có nên cho ghi memo trong lúc đang vũ trang không? Hiện thiết kế chặn, nhưng đó đúng là khoảnh khắc lý do vào lệnh còn nóng nhất. Mở ra thì phải chứng minh nó không đụng gì tới đường đặt lệnh.
* [ ] OQ-9: Ngưỡng sức máy tối thiểu để bật phần chép lời là bao nhiêu, và dưới ngưỡng đó thì mặc định là tự hạ mức hay tắt hẳn? Xem A-10.

---

> **Lịch sử review:** chốt OQ-1 tới OQ-6 cùng hai câu hỏi ranh giới với `daily-journal` và
> `reports-export` ngày 2026-08-28 (`/urd` Phase E). Review bởi `@senior-ba` (5 blocking,
> 13 warning, 6 suggestion) và `@po-reviewer` (0 blocking, 4 warning, 3 suggestion) cùng ngày;
> findings đã áp vào Mục 1, 3, 4, 5, 6, 7, 8, 9 và sinh thêm UN-014, UN-015, A-08 tới A-13,
> USC-006, OQ-7, OQ-8, OQ-9.
