---
type: urd
feature: tilt-meter
status: draft
updated: 2026-08-28
links: ["[[docs/_shared/project-profile.md]]", "[[docs/_shared/system-overview.md]]", "[[docs/_shared/definitions.md]]", "[[docs/_shared/operating-environment.md]]", "[[docs/order-execution/order-execution-urd.md]]", "[[docs/playbook-grading/playbook-grading-urd.md]]", "[[docs/voice-journal/voice-journal-urd.md]]", "[[docs/process-score/process-score-urd.md]]", "[[docs/trade-replay/trade-replay-urd.md]]", "[[docs/daily-journal/daily-journal-urd.md]]", "[[docs/ai-desk/ai-desk-urd.md]]"]
---

# tilt-meter — User Requirements Document

## 1. Purpose

Ghi lại nhu cầu của người chơi quanh việc **nhận ra mình đang ở trạng thái xấu ngay lúc nó đang
diễn ra** — đọc từ chính hành vi trên tay cầm, không phải từ một bản tự chấm sau phiên — và quanh
việc điều đó **bị cản đúng một chỗ duy nhất: lúc mở lệnh mới**.

Sản phẩm thiết kế sẵn những thứ chặn người chơi — hạn mức rủi ro, chốt an toàn khi vắng mặt — nhưng tất cả
đều dựa trên **một luật do chính người chơi đặt ra trước phiên**. Feature này là thứ duy nhất làm chậm
người chơi lại dựa trên **một nhận định về trạng thái hiện tại của họ**. Vì vậy
hai ranh giới sinh ra cùng lúc với nó, và quan trọng ngang nhu cầu chính: **nó không bao giờ được
chạm vào đường thoát**, và **nó không bao giờ được trừ điểm ai**. Một cơ chế cản người ở sai chỗ thì
nguy hiểm; một cơ chế mắng người thì bị tắt sau hai tuần. Cả hai đều là thất bại.

### User Problem & Current Experience

| User | Current Situation | Problem | User Consequence | Evidence |
|---|---|---|---|---|
| Người chơi | Công cụ nhật ký hiện có yêu cầu tự chấm trạng thái cảm xúc **sau khi phiên đã xong** | Đánh giá bằng trí nhớ đã bị kết quả nhuộm màu — thắng thì nhớ là bình tĩnh, thua thì nhớ là mất kiểm soát | Con số thu được nói về cảm giác lúc nhìn lại, không nói gì về lúc ra quyết định | **Assumption** — xem A-11. Nguồn chỉ chứng minh Edgewonk làm theo cách đó (`phase-09`), **không** chứng minh người chơi này đang dùng nó |
| Người chơi | Vào lại 40 giây sau một lệnh thua, khối lượng gấp đôi mức thường, sáu lần đóng-mở chốt trước một lần vũ trang | Đây là những hành vi **đo được** đi ngay trước một buổi tối tệ, nhưng không có gì đánh dấu chúng lúc chúng đang xảy ra | Buổi tối trôi theo đà xấu; người chơi chỉ nhận ra khi nhìn lại, lúc không còn sửa được | **Assumption** — xem A-11. `phase-09` nêu đây là **loại hành vi** cơ chế nhắm tới, không phải quan sát về chính người chơi này |
| Người chơi | Công cụ giao dịch chỉ có hai mức: im lặng, hoặc cấm | Không có gì nằm giữa "không nhắc gì" và "khoá tài khoản" | Hoặc không được cảnh báo, hoặc bị cảnh báo theo cách khó chịu tới mức tắt luôn cơ chế | Observed: `phase-09` (thang 4 band; "a warning that costs nothing is one you keep listening to") |
| Người chơi | Các hệ thống chấm điểm kỷ luật thường trừ điểm khi phát hiện trạng thái xấu | Bị phạt vì mười phút tệ trong một buổi ba tiếng | Công cụ trở thành nơi bị mắng — đúng thứ mà cả sản phẩm này sinh ra để tránh | Observed: `phase-09` ("Taxing the evening for a bad ten minutes would reintroduce the punishment this whole plan exists to avoid") |

> **Về nhãn nguồn.** `phase-09` là tài liệu **kế hoạch xây dựng**, không phải quan sát người chơi. Nó
> chứng minh được *cơ chế định làm gì và vì sao*, không chứng minh được *người chơi này đang gặp đúng
> vấn đề đó*. Hai dòng đầu vì vậy mang nhãn `Assumption` — nếu sai thì cơ chế đo đúng nhưng đo một
> thứ không xảy ra. Xem A-11.

## 2. User Types

| Tier | User Type | Context | Primary Goal | Pain Points |
|---|---|---|---|---|
| primary | **Người chơi** | Tay đặt trên tay cầm, trong phiên, thường sau một chuỗi kết quả xấu — đúng lúc khả năng tự đánh giá kém nhất | Được cản lại đúng lúc mình đang trượt, mà không mất quyền thoát và không bị chấm điểm nhân cách | Không tự nhận ra mình đang tilt; sợ công cụ khoá mất đường thoát; sợ bị công cụ phán xét |

> **Không có secondary user.** Công cụ cá nhân một người dùng. **AI desk không tham gia tính chỉ số**
> — nguồn nêu rõ không có mô hình ngôn ngữ nào nằm trong phép tính. AI desk chỉ **đọc** được mức và
> nguyên nhân chính ở dạng tổng hợp, không đọc được từng mẫu. *Nội dung* câu nó nói ở mức nóng thuộc
> `ai-desk`, không thuộc URD này — và `ai-desk-urd.md` hiện chưa nhận nghĩa vụ đó, xem OQ-12.
> Sàn cTrader/Spotware là actor hệ thống. Xem `docs/_shared/project-profile.md`.

## 3. Scope Boundaries

### In Scope

* Hệ thống đọc trạng thái người chơi từ **hành vi quan sát được trên tay cầm**: số lần đóng-mở chốt an toàn trước một lần vũ trang, số lần đảo hướng mua-bán khi đang vũ trang, nhịp bấm nút, số bước đổi khối lượng, thời gian từ lúc vũ trang tới lúc bắn, thời gian ngồi im. **Không suy đoán cảm xúc từ bất kỳ nguồn nào khác.**
* Hệ thống dùng thêm **dữ liệu đã có sẵn trong nhật ký, không phát sinh việc ghi mới**: thời gian kể từ lệnh thua gần nhất, số lệnh thua trong buổi, khối lượng lệnh sắp vào so với mức thường của phiên, nhịp mở lệnh, và số luật playbook không đạt trong ba lần bắn gần nhất.
* Mọi mốc so sánh là **mức thường của chính người chơi**, tính trên 30 phiên gần nhất — không có chuẩn của đám đông nào được áp lên người chơi.
* Chỉ số rơi vào **một trong bốn mức**: bình thường / ấm / nóng / quá nóng. Mỗi mức một hệ quả khác nhau; chỉ mức thấp nhất là im lặng hoàn toàn. Ngoài bốn mức đó còn **một trạng thái hiển thị riêng — trung tính** — nghĩa là chưa đủ dữ liệu để nói gì; nó đọc khác hẳn mức bình thường và không bao giờ sinh ma sát.
* Màn hình chính **luôn nêu tên hành vi đang đẩy chỉ số lên bằng một câu người đọc hiểu được** ("vừa vào lại 40 giây sau một lệnh thua"), không bao giờ chỉ hiện một con số trần.
* **Mức ấm không tốn của người chơi thứ gì** — chỉ thêm một dòng chữ, thao tác bắn không đổi.
* **Mức nóng siết thao tác bắn**: phải giữ nút xác nhận một khoảng ngắn thay vì bấm nhả. Màn xác nhận nêu thêm lý do và mức rủi ro của lệnh này.
* **Mức quá nóng khoá việc mở lệnh mới trong 5 phút**, kèm đồng hồ đếm ngược và lời mời ghi một memo. Đường ra sớm duy nhất là **ghi memo — bằng giọng nói hoặc bằng bàn phím** (chốt 2026-08-28), và đường đó **phải dùng được trong suốt thời gian bị khoá**. Không có đường ra nào dùng được thì màn khoá nói thẳng là lần này chỉ còn cách chờ hết giờ, thay vì mời một việc không làm được (🔶 xem A-10, OQ-9).
* **Ma sát chỉ áp cho việc MỞ lệnh.** Đóng vị thế, thoát khẩn cấp, nút thoát trên màn hình, và tự khoá phiên **không bao giờ** bị chạm tới, ở bất kỳ mức nào.
* **Chỉ số không bao giờ là đầu vào của điểm quy trình** — nó không trừ điểm buổi tối của người chơi.
* Người chơi **tắt được hoàn toàn** cơ chế này; tắt rồi thì không còn dấu vết nào của nó trên màn hình.
* Dưới **5 phiên** chưa đủ dữ liệu để có mức thường riêng → chỉ báo hiện **trung tính**, không đoán bừa. Giai đoạn đó cơ chế **không sinh ma sát nào** — 🔶 quyết định thay user, nguồn chỉ giới hạn thành phần tính chứ không tắt ma sát (xem A-12, OQ-11). Mức thường chỉ thực sự ổn định quanh **30 phiên**.
* **Khoảng khoá đi theo đồng hồ, không theo phiên** — đóng phiên rồi mở phiên mới, hoặc tự khoá rồi mở khoá lại, đều không rút ngắn nó. Chỉ số thì vẫn bắt đầu lại từ trung tính mỗi phiên (🔶 xem A-05).
* Chỉ số **không bao giờ được lưu như một đặc điểm của con người**; nó là trạng thái của phiên, cộng với các mẫu ghi lại để nhìn lại sau. Số lệnh thua liên tiếp là **đầu vào**, không bao giờ được hiện ra như một chuỗi thành tích ngược.
* Mỗi lệnh giữ lại **mức tilt tại thời điểm bắn**, để sau này đối chiếu được quyết định với trạng thái lúc ra quyết định.
* **Mỗi lần chỉ số đổi mức được ghi lại** kèm mốc thời gian và hành vi đã đẩy nó lên — để `trade-replay` đặt được nó đúng chỗ trên dải thời gian của một lệnh.
* Mỗi phiên giữ lại **hai con số phục vụ Mục 9**: số lần mở lệnh trong vòng 60 giây sau một lần đóng lỗ, và số lệnh có khối lượng từ gấp đôi mức thường của phiên trở lên. Cơ chế vốn đã tính cả hai để chấm điểm — đây chỉ là việc giữ chúng lại theo phiên, để hai thước đo không phụ thuộc vào việc feature khác có kịp lịch hay không.
* **Mỗi lần người chơi bật hoặc tắt cơ chế được ghi lại kèm ngày** — không có nó thì thước đo "còn dùng hay đã bỏ" ở Mục 9 không có nguồn số.

### Out of Scope

* **Trạng thái giọng nói** (nhịp nói, độ lớn) — **chốt 2026-08-28: người chơi bỏ hẳn khỏi phạm vi.** Nguồn `phase-09` có đề xuất thành phần này ở mức đóng góp nhỏ nhất và tự nhận là phần yếu nhất; quyết định là chỉ đo hành vi tay cầm và dữ liệu nhật ký. Việc ghi âm và chép lời vẫn thuộc `voice-journal`; feature này chỉ dùng **sự kiện "đã ghi một memo"**, không dùng nội dung và không phân tích âm thanh.
* **Phân loại cảm xúc, phát hiện từ ngữ tiêu cực, chấm điểm nội dung lời nói, hay bất kỳ mô hình ngôn ngữ nào trong phép tính** → ngoài phạm vi vĩnh viễn. Đây là ranh giới nguỵ khoa học mà nguồn nêu rõ là không được vượt.
* **Bảng nhìn lại các mức tilt theo phiên và tương quan với mức tuân thủ luật** → feature `process-score`. URD này tạo ra dữ liệu; nơi đọc nó thành xu hướng là deck.
* **Điểm quy trình 5 trục** thuộc feature `process-score`. Tilt không bao giờ là một trục và không bao giờ là đầu vào của bất kỳ trục nào. Ràng buộc này chỉ giữ được nhờ một quyết định cụ thể: tập "điều kiện đứng ngoài" mà `process-score` dùng để cộng điểm cho một lần tự huỷ **không bao gồm mức tâm lý** — dù nguồn `phase-11` có liệt kê nó trong đó. Chốt 2026-08-28; xem `process-score` A-09 và OQ-10.
* **Hạn mức rủi ro và việc từ chối lệnh vì vượt hạn mức** → feature `order-execution`. Tilt **thêm ma sát**, nó không phải một hạn mức và không dùng chung cách nói với hạn mức.
* **Chốt an toàn khi người chơi vắng mặt** (mất tay cầm, mất focus, mất kết nối) → `order-execution`. Hai cơ chế cùng chỉ chạm việc mở lệnh nhưng xử sự **ngược nhau khi mất tín hiệu**, xem Mục 6.
* **Bộ đếm số lần tự huỷ** → `order-execution`. **Chấm luật playbook** → `playbook-grading`; feature này chỉ **tiêu thụ** kết quả chấm như một tín hiệu.
* **Nhận diện setup, tư vấn, tín hiệu, phân tích thị trường** → `ai-desk`.
* **Nghi thức chuẩn bị trước phiên và tự đánh giá đầu buổi** → `daily-journal`. Người chơi tự khai trạng thái là một việc khác hẳn với việc hệ thống đo hành vi.
* **Tua lại một lệnh qua tape** → `trade-replay`. Feature đó *hiện lại* các lần đổi mức như một sự kiện trên dải thời gian; feature này chỉ chịu trách nhiệm sinh ra chúng.
* **Báo cáo, xuất dữ liệu, sao lưu** → `reports-export`.

## 4. User Needs

| ID | User | Context / Trigger | User Need | Expected Outcome | Importance | Evidence |
|---|---|---|---|---|---|---|
| UN-001 | Người chơi | Bất kỳ lúc nào, đặc biệt khi chỉ số đang ở mức cao nhất và thị trường đang chạy nhanh | **Đường thoát không bao giờ bị cơ chế này chạm tới** | Đóng vị thế, thoát khẩn cấp, nút thoát trên màn hình, và tự khoá phiên hoạt động y hệt như khi chỉ số ở mức thấp nhất — không chậm hơn một phần nghìn giây, không thêm một bước nào. Không tồn tại cách cấu hình nào bật được việc cản đường thoát | Critical | Observed: `phase-09` ("Tilt can only ever slow down an open ... never gate, delay, or add friction to a close, a panic flatten, the HUD Flatten button, or a session lock"); README (boot-fail on `tilt.gate_close`) |
| UN-002 | Người chơi | Cuối mỗi buổi, khi xem lại mình đã làm ăn thế nào | **Không bao giờ bị trừ điểm vì đã có mười phút xấu** | Trạng thái tâm lý không xuất hiện trong bất kỳ phép tính điểm nào. Một buổi có lúc quá nóng nhưng người chơi đã dừng lại đúng lúc thì được chấm **tốt**, vì dừng lại đúng lúc chính là hành vi cần khen | Critical | Observed: `phase-09` ("Tilt is never an input to the Process Score"); `phase-11` ("tilt is not an input ... renders as a session retrospective") |
| UN-003 | Người chơi | Vừa thua vài lệnh, đang chuẩn bị vào lại ngay với khối lượng lớn hơn | Bị cản lại **đúng lúc còn kịp**, chứ không được nhắc sau khi đã vào | Mức nóng buộc phải giữ nút xác nhận thay vì bấm nhả — đủ để một cú bấm bốc đồng không đi qua được. Mức quá nóng khoá việc mở lệnh mới trong 5 phút | Critical | Observed: `phase-09` (bảng band và ma sát); Confirmed 2026-08-28 (người chơi chốt không có đường vượt cooldown) |
| UN-004 | Người chơi | Ngay khi chỉ số vượt mức bình thường | Biết **vì sao** mình bị đánh giá là đang xấu, bằng một câu chứ không phải một con số | Màn hình luôn nêu tên hành vi đang đẩy chỉ số lên nhiều nhất, bằng lời mô tả chính việc mình vừa làm. Nhờ vậy một cảnh báo sai **nhìn là biết sai ngay** thay vì trở thành một phán xét không cãi được | High | Observed: `phase-09` ("every component is a nameable behaviour ... renders the top contributor as a sentence, never a bare number alone") |
| UN-005 | Người chơi | Suốt phiên | Chỉ bị so với **chính mình**, không bị so với một chuẩn nào bên ngoài | Mọi mốc so sánh lấy từ 30 phiên gần nhất của chính người chơi. Người chơi vốn bấm nhanh không vì thế mà luôn bị coi là đang tilt | High | Observed: `phase-09` ("all baselines are the player's own rolling medians"; "never a population claim") |
| UN-006 | Người chơi | Suốt phiên | Chỉ số phải dựa trên **việc mình đã thực sự làm**, không phải trên một suy đoán về cảm xúc | Mọi thành phần đều là một hành vi đếm được trên tay cầm hoặc một dữ kiện có sẵn trong nhật ký. Không có phân loại cảm xúc, không có phân tích từ ngữ, không có mô hình ngôn ngữ nào trong phép tính | High | Observed: `phase-09` ("no keyword scoring, no profanity detection, no affect classification, no LLM in the score"); Confirmed 2026-08-28 (bỏ thành phần giọng nói) |
| UN-007 | Người chơi | Đang bị khoá mở lệnh ở mức quá nóng | Đường ra sớm là **kể ra mình đang làm gì**, không phải bấm một nút cho xong | Ghi một memo trong lúc bị khoá làm chỉ số hạ xuống thật sự. Bấm "đã đọc" chỉ **tắt dòng cảnh báo trên màn hình** và không làm thay đổi chỉ số — vì nếu bấm một nút cũng hạ được điểm thì cơ chế tự vô hiệu hoá | High | Confirmed 2026-08-28 (người chơi chốt). Nền: `phase-09` ("narrating it is the intervention ... the productive alternative is rewarded rather than the door merely being locked") |
| UN-008 | Người chơi | Chỉ số mới nhích lên khỏi mức bình thường | Được nhắc mà **không mất gì cả** | Mức ấm chỉ thêm một dòng chữ và đổi màu chỉ báo; thao tác bắn không đổi một chút nào. Một lời nhắc không tốn gì là lời nhắc còn được nghe sau ba tháng | Medium | Observed: `phase-09` ("**none** — a warning that costs nothing is one you keep listening to") |
| UN-009 | Người chơi | Những phiên đầu tiên, khi chưa có đủ lịch sử để biết đâu là mức thường của mình | Không bị chấm bừa khi hệ thống chưa hiểu gì về mình | Dưới 5 phiên, chỉ báo hiện trung tính và không sinh ma sát nào. Hệ thống nói rõ là đang còn học, thay vì đưa ra một con số không có cơ sở | Medium | Nền: `phase-09` (dưới 5 phiên chỉ dùng các thành phần hành vi; chỉ báo hiện trung tính thay vì đoán). **Việc không sinh ma sát nào là 🔶 quyết định thay user 2026-08-28** — nguồn giới hạn thành phần tính, không tắt ma sát. Xem A-12 |
| UN-010 | Người chơi | Sau một thời gian dùng, nếu thấy cơ chế cảnh báo sai quá nhiều | Tắt được hẳn, không phải sống chung với một thứ mình không tin | Tắt xong thì cơ chế biến mất hoàn toàn: không chỉ báo, không dòng cảnh báo, không ma sát, không khoá; không phần nào sót lại "để tham khảo". Việc tắt có hiệu lực **từ phiên sau** — một khoảng khoá đang chạy vẫn chạy hết. Đó là cái giá của việc không để nút tắt thành đường vượt khoảng chờ (🔶 xem A-08) | Medium | Observed: `phase-09` (`tilt.enabled: false` removes it entirely) |
| UN-011 | Người chơi | Suốt quá trình dùng sản phẩm | Không bị biến thành một hồ sơ tâm lý | Chỉ số sống trong phiên; không có con số nào tích lại thành một nhãn dán lên người chơi. Số lệnh thua liên tiếp được dùng để tính nhưng **không bao giờ hiện ra như một chuỗi**. Thứ không tích luỹ là **chỉ số** và mọi cách trình bày nó thành chuỗi hay cấp độ; **mức thường của chính người chơi thì có tích luỹ** qua 30 phiên — nhưng nó là thước để so, không phải nhãn dán lên người chơi | Medium | Observed: `phase-09` ("never persisted as a trait"; "`consecutiveLossesTonight` ... never rendered as a streak"); README ("nothing that accumulates across sessions") |
| UN-012 | Người chơi | Sau phiên, khi mở lại một lệnh cụ thể | Biết được lúc bấm nút đó mình đang ở trạng thái nào | Mỗi lệnh giữ lại mức tilt tại thời điểm bắn. Đây là thứ biến một cảm giác mơ hồ ("hôm đó mình vào lệnh lúc đang cay") thành một dữ kiện đối chiếu được | Medium | Observed: `phase-09` (`tilt_at_entry` frozen onto every fire) |
| UN-013 | Người chơi | Mất kết nối rồi vào lại giữa lúc đang bị khoá | Không bị kẹt trong một cái khoá mà hệ thống không còn tính đúng được nữa | Khoảng khoá được tính lại từ mốc bắt đầu. Nếu đồng hồ không còn tin được thì hệ thống **cho phép giao dịch** — cố ý ngược với chốt an toàn khi vắng mặt, vì cái kia phòng việc không có người, còn cái này chỉ là một nhận định về trạng thái | Medium | Observed: `phase-09` ("cooldown fails open on reconnect ... deliberately the opposite of the dead-man") |
| UN-014 | Người chơi | Đang tua lại một lệnh cũ để học | Thấy được lúc nào trong buổi tối đó trạng thái mình đổi, và vì hành vi gì | Mỗi lần chỉ số đổi mức được ghi lại kèm mốc thời gian và hành vi đã đẩy nó lên, đủ để `trade-replay` đặt nó đúng chỗ trên dải thời gian cạnh các sự kiện khác | Medium | Observed: `trade-replay-urd.md` UN-011 (Critical — liệt kê lần đổi vùng trạng thái là một trong các sự kiện bắt buộc trên dải thời gian); `phase-10` |

## 5. Prioritized User Journeys

### Journey 1: Thoát được kể cả khi đang ở mức tệ nhất

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Đang có vị thế mở, chỉ số đã ở mức quá nóng và việc mở lệnh mới đang bị khoá
* __Expected outcome:__ Vị thế đóng được ngay, đúng như khi chỉ số ở mức thấp nhất
* __Related needs:__ UN-001, UN-003

1) Người chơi đang bị khoá mở lệnh mới ở mức quá nóng.
2) Giá chạy ngược, người chơi quyết định thoát.
3) Bấm đóng vị thế — hoặc thoát khẩn cấp nếu muốn đóng tất cả.
4) Lệnh đóng đi thẳng tới sàn, không thêm bước xác nhận nào, không phải chờ hết khoảng khoá.

__Independent verification:__ Dựng trạng thái quá nóng bằng **hành vi thật** — vài lệnh thua liên
tiếp rồi vào lại nhanh với khối lượng gấp đôi, cho tới khi đồng hồ đếm ngược hiện lên — rồi trong
chính lúc đó bấm thoát khẩn cấp; kiểm tra trên cTrader demo phải thấy không còn vị thế nào. Kiểm
thêm chiều ngược ngay tại đó: một lệnh **mở** phải bị từ chối. Hai kết quả trái ngược trên cùng một
trạng thái chính là bằng chứng của ranh giới. Đây là journey phải hoạt động kể cả khi mọi thứ khác
của feature hỏng.

> Dựng bằng hành vi thật tốn cả một buổi và phụ thuộc thị trường, nên ranh giới an toàn quan trọng
> nhất của feature lại là thứ khó kiểm nhất. Một chế độ diễn tập cho phép đặt thẳng mức để tự kiểm
> sẽ giải quyết việc này — xem OQ-10.

### Journey 2: Chuỗi thua rồi vào lại to gấp đôi

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Vừa đóng lệnh thua thứ hai trong buổi, và trong vòng một phút đã vũ trang lại với khối lượng gấp đôi mức thường
* __Expected outcome:__ Người chơi thấy đúng tên hành vi mình vừa làm và phải giữ nút để bắn, đủ để cú bấm bốc đồng không tự đi qua
* __Related needs:__ UN-003, UN-004, UN-005, UN-006, UN-012, UN-014

1) Người chơi đóng lệnh thua thứ hai.
2) Trong vòng một phút, tăng khối lượng lên gấp đôi và vũ trang lại.
3) Chỉ báo chuyển sang mức nóng, kèm một câu nêu đúng hành vi đang đẩy nó lên.
4) Màn xác nhận hiện thêm lý do đó và mức rủi ro của chính lệnh này.
5) Người chơi phải **giữ** nút xác nhận thay vì bấm nhả; trong lúc giữ, còn kịp đổi ý.

__Independent verification:__ Dựng đúng chuỗi trên (hai lệnh thua, vào lại trong vòng một phút, khối
lượng gấp đôi mức thường của phiên); chỉ báo phải sang mức nóng và câu lý do phải nêu **việc tăng
khối lượng sau thua**, đối chiếu được với chính các con số của phiên. Trong cùng thời điểm đó, đo lại
thao tác **đóng** một vị thế — nó phải không đổi gì cả. Sau khi lệnh đi, mở lại chính lệnh đó phải
thấy mức tilt tại thời điểm bắn được giữ nguyên, và thấy lần đổi mức vừa rồi nằm đúng chỗ
trên dải thời gian kèm tên hành vi đã gây ra nó. Không cần journey nào khác để xác nhận.

### Journey 3: Bị khoá, và kể ra lý do để mở sớm

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Chỉ số chạm mức quá nóng; việc mở lệnh mới bị khoá 5 phút
* __Expected outcome:__ Người chơi hoặc chờ hết khoảng khoá, hoặc ghi một memo và thấy chỉ số hạ xuống thật
* __Related needs:__ UN-007, UN-003, UN-004, UN-013

1) Chỉ số chạm mức quá nóng; đồng hồ đếm ngược hiện lên kèm lời mời ghi một memo.
2) Người chơi thử vũ trang — việc mở lệnh bị từ chối, kèm lý do đang trong khoảng chờ.
3) Người chơi giữ nút ghi âm và nói ra mình đang định làm gì.
4) Chỉ số hạ xuống; **nếu** xuống dưới mức quá nóng thì việc mở lệnh mở lại trước khi hết 5 phút (một memo có luôn đủ để vượt ngưỡng hay không: xem OQ-7).
5) Nếu chỉ bấm "đã đọc" thay vì ghi memo, dòng cảnh báo biến mất — nhưng **đồng hồ đếm ngược và câu nêu lý do bị khoá vẫn còn** cho tới khi hết khoá; chỉ số **không đổi**.
6) Mất kết nối rồi vào lại giữa chừng: đồng hồ tính tiếp đúng phần thời gian còn lại.

__Independent verification:__ Ghi lại chỉ số ngay trước và ngay sau khi ghi một memo trong lúc bị
khoá — nó phải **giảm**. Lặp lại đúng tình huống đó nhưng chỉ bấm "đã đọc": chỉ số phải **không đổi**
và khoá phải còn nguyên — cùng với đồng hồ và câu lý do. Hai lần đo trái ngược nhau chính là bằng
chứng của UN-007; phép kiểm này chỉ nói về **chỉ số**, không nói về việc khoá có mở ra hay không.
Kiểm riêng UN-013: ngắt mạng giữa khoảng khoá rồi nối lại — phần còn lại phải đúng bằng thời gian
đã trôi. Dựng thêm trường hợp đồng hồ không dùng được: việc mở lệnh phải **được phép**, và người
chơi phải thấy rõ điều đó vừa xảy ra.

### Journey 4: Được nhắc mà không mất gì

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Chỉ số nhích lên mức ấm — vài lần đóng-mở chốt nhiều hơn thường lệ
* __Expected outcome:__ Người chơi nhận ra mình đang do dự hơn bình thường, và vẫn giao dịch y như cũ
* __Related needs:__ UN-008, UN-004

1) Chỉ báo chuyển sang mức ấm, kèm một dòng nêu hành vi đang đẩy nó lên.
2) Người chơi đọc dòng đó.
3) Vũ trang và bắn — thao tác giống hệt như lúc chỉ số ở mức bình thường.

__Independent verification:__ Ở mức ấm, đo lại chính thao tác bắn: phải vẫn là bấm nhả, không phải
giữ, và không có bước nào thêm vào. Khác biệt duy nhất so với mức bình thường là màu chỉ báo và một
dòng chữ.

### Journey 5: Những phiên đầu tiên, khi hệ thống chưa biết gì về mình

* __User:__ Người chơi · __Importance:__ Medium
* __Trigger:__ Phiên thứ nhất tới thứ tư của người chơi
* __Expected outcome:__ Không bị chấm bừa, và hiểu vì sao chỉ báo chưa nói gì
* __Related needs:__ UN-009, UN-005

1) Người chơi mở phiên đầu tiên.
2) Chỉ báo hiện trung tính và nói rõ chưa đủ dữ liệu để biết mức thường của người chơi.
3) Người chơi giao dịch bình thường; không có ma sát nào phát sinh dù thao tác nhanh hay chậm.
4) Sau vài phiên, hệ thống bắt đầu có mức thường riêng và chỉ báo mới thực sự hoạt động.

__Independent verification:__ Với lịch sử dưới 5 phiên, cố ý dựng một chuỗi hành vi lẽ ra phải đẩy
lên mức nóng (thua rồi vào lại nhanh, khối lượng lớn); chỉ báo vẫn phải trung tính và thao tác bắn
vẫn phải là bấm nhả. **Phép kiểm này chỉ chạy được trong 5 phiên đầu tiên** — bỏ lỡ thì UN-009 mất
cách kiểm chứng, nên làm ngay buổi đầu.

### Journey 6: Không tin nữa và tắt hẳn

* __User:__ Người chơi · __Importance:__ Medium
* __Trigger:__ Sau một thời gian, người chơi thấy cảnh báo sai quá nhiều lần
* __Expected outcome:__ Cơ chế biến mất hoàn toàn, sản phẩm còn lại vẫn chạy đủ
* __Related needs:__ UN-010, UN-004, UN-002, UN-011

1) Người chơi tắt cơ chế trong phần cài đặt — tắt được bất cứ lúc nào, có hiệu lực từ phiên sau.
2) Phiên sau, màn hình không còn chỉ báo, không còn dòng cảnh báo.
3) Không có ma sát nào ở bất kỳ mức nào; mọi thao tác trở về mặc định.
4) Mọi phần còn lại của sản phẩm — chấm luật, ghi âm, chấm điểm buổi — chạy nguyên vẹn.

__Independent verification:__ Sau khi tắt, dựng lại đúng chuỗi hành vi của Journey 2; không được có
bất kỳ thay đổi nào trong thao tác bắn và không có dòng cảnh báo nào xuất hiện. Đồng thời kiểm tra
điểm quy trình của buổi vẫn tính được đầy đủ — bằng chứng rằng tilt chưa bao giờ là đầu vào của nó.
Không màn hình nào được hiện số buổi hay số lần đã tilt như một chuỗi tích luỹ — phần này kiểm được
ngay. Phép kiểm chặt hơn — hai buổi giống hệt nhau trừ tilt phải cho **cùng một điểm quy trình** —
chỉ chạy được khi `process-score` đã có; đó là phép kiểm **chung của hai feature** (xem
`process-score` J8), URD này không sở hữu nó.

## 6. User Exceptions & Edge Conditions

> **Luật chung khi nhiều cơ chế cùng chạm việc mở lệnh:** màn hình nêu **mọi** lý do đang có hiệu
> lực, không giấu bớt cái nào. Nhưng khi một cơ chế khác **đã xử lý xong** tình huống (vd mất tay cầm
> đã tự huỷ vũ trang), tilt **không nói thêm gì** — người chơi chỉ nghe một lời giải thích.

| Situation | User Impact | Expected User-facing Outcome | Related Journey / Need |
|---|---|---|---|
| **Mất kết nối rồi vào lại giữa lúc đang bị khoá** | Nguy cơ kẹt trong một cái khoá mà hệ thống không còn tính đúng được | Khoảng khoá tính lại từ mốc bắt đầu và đếm tiếp phần còn lại. Nếu đồng hồ không tin được thì **cho phép giao dịch** — cố ý ngược với chốt an toàn khi vắng mặt của `order-execution`, và người chơi thấy rõ điều đó đã xảy ra | J3 / UN-013, UN-001 |
| **Đang ở trạng thái đã vũ trang đúng lúc chỉ số chạm mức quá nóng** | Vũ trang thì không ghi memo được (luật của `voice-journal`), mà không ghi memo thì không có đường ra sớm — kẹt trọn 5 phút | Trạng thái vũ trang bị huỷ ngay khi khoá bắt đầu, để đường ghi memo mở ra. Lần huỷ này **không tính là một lần tự huỷ** — nó không phải quyết định của người chơi. Người chơi thấy rõ vì sao vũ trang biến mất | J3 / UN-007, UN-003 |
| **Đang bị khoá mà giọng nói đã tắt, mic bị từ chối, hoặc máy không có mic** | Màn khoá mời làm một việc không làm được | Đường memo bằng bàn phím luôn có mặt và được nêu ngay trên màn khoá — `voice-journal` đã coi bàn phím là đường **ngang hàng**, không phải bản hạ cấp. Cả hai đường đều không dùng được thì màn khoá nói thẳng lần này chỉ còn cách chờ hết giờ | J3 / UN-007, UN-010 |
| **Đang bị khoá mà cần thoát một vị thế đang lỗ nhanh** | Đây là kịch bản nguy hiểm duy nhất của cả feature | Thoát bình thường, không chờ, không thêm bước. Nếu có bất kỳ trường hợp nào một lệnh đóng bị chậm hoặc bị từ chối, đó là lỗi phải sửa ngay chứ không phải một tình huống chấp nhận được | J1 / UN-001 |
| **Mất tay cầm hoặc mất focus cửa sổ khi đang ở mức nóng** | Hai cơ chế cùng chạm việc mở lệnh, dễ chồng lời | Trạng thái vũ trang bị huỷ theo luật của `order-execution`; feature này **không thêm gì** và không nói thêm gì. Người chơi chỉ thấy một lý do, không phải hai | J2 / UN-001 |
| **Buổi chưa có lệnh thua nào** | Thành phần "vào lại sau thua" không có gì để tính | Thành phần đó không áp; chỉ số được tính trên những gì thật sự đo được, và không vì thiếu một thành phần mà tự động thấp đi hay cao lên | J2, J5 / UN-005, UN-006 |
| **Phiên mới chỉ có một hai lệnh** | "Khối lượng gấp đôi mức thường của phiên" chưa có nghĩa | Thành phần khối lượng hoãn lại cho tới khi đủ mẫu trong phiên; người chơi không bị chấm là tăng khối lượng chỉ vì lệnh thứ hai to hơn lệnh đầu | J2, J5 / UN-005, UN-009 |
| **Ngồi im rất lâu rồi mới bắn một lệnh** | Nhịp bấm thấp bất thường, dễ bị hiểu nhầm là bất thường | Ngồi im không phải là tín hiệu xấu; chỉ có nhịp bấm **cao hơn mức thường** mới đẩy chỉ số lên. Một buổi kiên nhẫn phải cho chỉ số thấp | J4 / UN-005, UN-006 |
| **Chưa khai playbook nào, hoặc việc chấm luật chưa có** | Thành phần "luật không đạt trong ba lần bắn gần nhất" câm | Thành phần đó không áp; chỉ số tính trên những gì thật sự đo được và không vì thiếu nó mà tự thấp đi hay cao lên. Câu nêu lý do không bao giờ nhắc tới luật khi chưa có luật nào | J2 / UN-005, UN-006 |
| **Hết 5 phút mà chỉ số vẫn ở mức quá nóng** | Bị khoá lại ngay, cảm giác như bị phạt không có điểm dừng | Khoá lại được, nhưng màn hình nói rõ đây là lần khoá thứ mấy trong buổi và hành vi nào đang giữ chỉ số ở đó. Khoảng khoá **không dài thêm** theo số lần — không có leo thang hình phạt | J3 / UN-003, UN-004, UN-008 |
| **Ghi memo trong lúc bị khoá nhưng nội dung không liên quan** | Có thể thành đường lách | Chỉ số vẫn hạ. Hệ thống **không đọc nội dung memo** — đó chính là ranh giới đã chốt ở Mục 3, và hệ quả của nó được chấp nhận có ý thức (xem A-06). Việc dừng lại để nói ra một điều gì đó đã là một khoảng nghỉ | J3 / UN-006, UN-007 |
| **Vừa bị hạn mức rủi ro chặn, vừa đang trong khoảng khoá của tilt** | Không hiểu mình bị chặn vì cái gì | Nói rõ cả hai và phân biệt rõ: hạn mức là **luật do chính mình đặt**, khoảng khoá là **một nhận định về trạng thái**. Hai thứ không dùng chung một câu và không lẫn vào nhau | J3 / UN-003, và `order-execution` UN-004 |
| **Mất tay cầm hoặc mất focus một lúc lâu rồi quay lại** | Bị siết thao tác bắn vì một trạng thái đã cũ — đúng loại cảnh báo sai khiến người chơi tắt cơ chế | Không có dữ liệu hành vi mới thì chỉ số **nguội dần theo thời gian** thay vì đứng yên; vắng đủ lâu thì bắt đầu lại từ trung tính và nói rõ vì sao. Khoảng khoá đang chạy không bị ảnh hưởng bởi việc này | J2, J4 / UN-005, UN-006 |
| **Đổi cặp giao dịch liên tục trong vài phút** | Một tín hiệu thật, nhưng dễ bị chấm quá tay | Được ghi nhận như một tín hiệu, nhưng **một mình nó không đủ** đẩy lên mức nóng; câu nêu lý do phải nêu đúng nó thay vì nêu một hành vi khác | J2 / UN-004, UN-006 |
| **Mở phiên mới ngay sau một phiên tệ** | Trạng thái xấu của buổi trước có thể bị mang theo | **Chỉ số** bắt đầu lại từ mức trung tính mỗi phiên; không có gì tích luỹ qua đêm (xem A-05, OQ-6). Khoảng khoá thì không theo phiên — xem dòng dưới | J5 / UN-011 |
| **Đóng phiên rồi mở phiên mới, hoặc tự khoá rồi mở khoá lại, trong lúc khoảng khoá đang chạy** | Mở phiên mới là đường vượt khoảng chờ còn dễ hơn nút tắt | Phần thời gian khoá còn lại vẫn được thi hành ở phiên mới, kèm câu nói rõ vì sao. Chỉ số thì vẫn bắt đầu lại từ trung tính — hai thứ khác nhau (🔶 xem A-05) | J3, J5 / UN-003, UN-013 |
| **Giữ nút xác nhận nhưng nhả sớm ở mức nóng** | Tưởng đã bắn nhưng thật ra chưa | Không có lệnh nào phát sinh; trạng thái vũ trang **không mất**, và màn hình nói rõ cần giữ đủ lâu. Nhả sớm **không** bị tính là một lần tự huỷ — nhả tay giữa chừng không phải một quyết định không-vào, và bộ đếm của `order-execution` chỉ đếm quyết định của người chơi (🔶 xem A-13) | J2 / UN-003, và `order-execution` UN-006 |
| **Vũ trang rồi huỷ liên tục trong lúc đang bị khoá** | Khoảng khoá thành chỗ farm điểm chọn lọc | Các lần huỷ đó vẫn đếm như mọi lần huỷ chủ động khác; việc quy chúng ra điểm đã có trần ở `process-score` (UN-008), URD này không thêm luật riêng | J3 / UN-003, và `process-score` UN-008 |
| **Chỉ số ở mức nóng trong lúc người chơi đang sửa mức cắt lỗ / chốt lời** | Không rõ thao tác sửa có bị siết như thao tác mở không | Cho tới khi OQ-4 được chốt, thao tác sửa mức bảo vệ **không bị siết** — giữ đúng nguyên tắc của nguồn là chỉ cản việc mở lệnh mới. Nếu sau này chốt ngược lại thì phải phân biệt được **nới cắt lỗ ra xa** (hành vi cần cản) với **siết bảo vệ vào gần** (hành vi phòng vệ, không bao giờ được cản) | J1, J2 / UN-001, UN-003 |
| **Đang bị khoá mà muốn mở một lệnh ngược chiều để giảm rủi ro của vị thế đang có** | Ý định phòng vệ nhưng vẫn là một lệnh mở | Vẫn bị khoá — mọi lệnh mở đều bị khoá như nhau, vì hệ thống không đọc được ý định. Màn hình chỉ rõ đường giảm rủi ro **không bị chạm** vẫn còn nguyên: đóng bớt vị thế hoặc thoát khẩn cấp | J1, J3 / UN-001, UN-003 |
| **Người chơi tắt cơ chế ngay giữa lúc đang bị khoá** | Có thể thành đường lách khoảng chờ | Việc tắt chỉ có hiệu lực từ phiên sau; khoảng khoá đang chạy không bị xoá bởi thao tác tắt. Xem A-08 | J6 / UN-010 |
| **Cơ chế bị tắt, rồi bật lại sau vài tuần** | Mức thường của người chơi có thể đã cũ | Dùng lại 30 phiên gần nhất đang có; nếu quá ít mẫu còn dùng được thì quay về trạng thái trung tính như người mới, thay vì tính trên dữ liệu đã lỗi thời | J5, J6 / UN-005, UN-009 |

## 7. User-side Constraints

* **Hệ thống chỉ biết những gì xảy ra trên tay cầm và trong nhật ký.** Một cuộc gọi khó chịu trước phiên, một đêm mất ngủ — những thứ đó nằm ngoài tầm quan sát và sẽ không bao giờ được đo. Chỉ số này đo **hành vi**, không đo con người.
* **Cần ít nhất 5 phiên** trước khi cơ chế bắt đầu chạy — khoảng một tuần theo nhịp một phiên mỗi tối — và **khoảng 30 phiên** trước khi mức thường của chính người chơi thực sự ổn định. Giữa hai mốc đó cơ chế có chạy nhưng còn thô.
* Chỉ chạy trên Chrome desktop; người chơi phải giữ cửa sổ ở trạng thái focus trong suốt phiên (kế thừa ràng buộc của `order-execution`).
* Chỉ tài khoản demo. **Chỉ số này không phải chẩn đoán tâm lý và không phải lời khuyên đầu tư** — nó chỉ nói rằng hành vi vừa rồi khác mức thường của chính người chơi.
* Dữ liệu hành vi **không rời khỏi máy chủ của chính người chơi**; AI desk chỉ đọc được ở dạng tổng hợp, không đọc được từng mẫu.
* Giao diện sản phẩm bằng tiếng Anh; tài liệu nghiệp vụ bằng tiếng Việt.

## 8. Assumptions & Validation

| ID | Assumption | Impact if Wrong | Validation Status | Next Action |
|---|---|---|---|---|
| A-01 | 5 phút là đủ để nguội mà không bị cảm nhận thành hình phạt | Quá ngắn thì vô tác dụng; quá dài thì người chơi tắt hẳn cơ chế (UN-010 thành đường thoát thường xuyên) | Chưa xác nhận — con số lấy từ `phase-09` (`tilt.cooldown_s: 300`) | Đo sau 10 phiên đầu: số lần bị khoá, số lần ghi memo để ra sớm, số lần tắt cơ chế |
| A-02 | Giữ nút một khoảng ngắn (nguồn đề xuất 750 ms) là mức ma sát cảm nhận được mà không gây bực | Quá ngắn thì không cản được cú bấm bốc đồng; quá dài thì phá nhịp thao tác của cả sản phẩm | Chưa xác nhận — suy từ `phase-09` | Thử vài mức khi có sản phẩm; đây là số cần người chơi cảm nhận, không quyết được trên giấy |
| A-03 | Ba ngưỡng chia bốn mức (nguồn đề xuất 0.35 / 0.60 / 0.80) hợp với chính người chơi này | Lệch ngưỡng thì hoặc luôn ở mức ấm (mất tác dụng cảnh báo), hoặc hay chạm mức nóng oan | Chưa xác nhận — con số lấy từ `phase-09`, chưa có dữ liệu thật của người chơi nào | Xem lại sau một tháng dữ liệu; xem OQ-5 về việc có cho chỉnh ngưỡng không |
| A-04 | Bỏ thành phần giọng nói không làm chỉ số kém nhạy đi đáng kể | Nếu các thành phần hành vi không đủ nhạy, cơ chế bỏ sót đúng những lúc cần nhất | **Đã chốt quyết định** 2026-08-28 (người chơi chốt bỏ khỏi phạm vi); phần đóng góp của nó dồn về các thành phần hành vi. Nhưng *bản thân giả định* — rằng bỏ nó đi chỉ số vẫn đủ nhạy — thì **chưa kiểm được**, vì chưa có phiên nào chạy thật | Nếu sau 3 tháng chỉ số bỏ sót rõ rệt, mở lại bằng một CR chứ không âm thầm thêm vào |
| A-05 | **Chỉ số** chỉ sống trong phiên, nhưng **khoảng khoá đi theo đồng hồ** và sống qua ranh giới phiên | Nếu khoảng khoá cũng reset theo phiên thì đóng-mở phiên là đường vượt khoá dễ hơn cả nút tắt, và quyết định "không có đường vượt" mất hiệu lực. Nếu chỉ số cũng sống qua phiên thì hai phiên cách vài giờ bị tính chung, trái nguyên tắc không-tích-luỹ | 🔶 Quyết định thay user 2026-08-28 — `phase-09` chỉ nói "per-session state", không phân biệt chỉ số với khoảng khoá | Xác nhận với người chơi; xem OQ-6 |
| A-06 | Ghi một memo trong lúc bị khoá luôn được coi là một hành động có ý thức, hệ thống không xét nội dung | Người chơi có thể ghi một memo rỗng để mở khoá sớm, và cơ chế mất răng | 🔶 Quyết định thay user 2026-08-28 — hệ quả trực tiếp của ranh giới không-đọc-nội-dung ở Mục 3, giao với quyết định "chỉ memo mới hạ điểm" | Theo dõi 10 phiên đầu; nếu memo rỗng thành thói quen thì xem lại OQ-7 chứ không phải xem lại ranh giới |
| A-07 | Người chơi nhận ra một cảnh báo sai **là sai** nhờ câu nêu lý do | Nếu câu đó khó hiểu hoặc chung chung, cảnh báo sai trở thành một phán xét không cãi được và người chơi mất lòng tin | Chưa xác nhận — suy từ `phase-09` ("so a wrong one is obviously wrong") | Kiểm khi có sản phẩm: mỗi lần vào mức nóng, người chơi có nói được câu đó đúng hay sai không |
| A-08 | Việc tắt cơ chế chỉ có hiệu lực từ phiên sau, không xoá được khoảng khoá đang chạy | Nếu tắt là mở khoá ngay thì UN-010 trở thành đường lách chính thức của UN-003 | 🔶 Quyết định thay user 2026-08-28 — `phase-09` nói `tilt.enabled: false` gỡ sạch cơ chế nhưng không nói gì về việc tắt giữa lúc đang bị khoá | Xác nhận với người chơi khi viết SRS |
| A-09 | Feature này **tự giữ hai con số** của USC-001/USC-002 theo phiên, nên hai thước đo không phụ thuộc lịch của feature khác | Nếu không tự giữ thì cả hai không đo được ở đâu cả: `process-score` tuyên bố **không sinh dữ liệu của riêng nó**, và bề mặt deck của nó không có hai con số này | 🔶 Quyết định thay user 2026-08-28 — sửa sau review; trước đó doc giả định sai rằng `process-score` sẽ sinh ra chúng | Cascade một dòng sang `process-score` Mục 3 nếu muốn hiện chúng trên deck; xem OQ-8 |
| A-10 | Đường ghi memo luôn dùng được trong lúc bị khoá — giọng nói hoặc bàn phím | Nếu cả hai đường đều đóng (đã tắt giọng nói, không mic, và không có đường bàn phím lúc bị khoá) thì quyết định "không có đường vượt" biến thành kẹt trọn 5 phút không lối thoát — đúng cảm giác bị phạt mà feature sinh ra để tránh | 🔶 Quyết định thay user 2026-08-28 — phụ thuộc `voice-journal` (UN-011 bàn phím ngang hàng, UN-013 tắt được hẳn, OQ-8 chưa chốt việc ghi memo lúc đang vũ trang) | Chốt cùng `voice-journal` OQ-8; xem OQ-9 |
| A-11 | Người chơi này thực sự có các hành vi tiền-tilt mà Mục 1 mô tả (vào lại nhanh sau thua, tăng khối lượng, do dự nhiều lần) | Nếu không, cơ chế đo đúng nhưng đo một thứ không xảy ra — chỉ số nằm im ở mức bình thường suốt và feature vô dụng chứ không có hại | Chưa xác nhận — `phase-09` mô tả **loại hành vi** cơ chế nhắm tới, không quan sát chính người chơi này | Đọc lại sau 10 phiên đầu: chỉ số có bao giờ rời mức bình thường không |
| A-12 | Dưới 5 phiên nên **im lặng hoàn toàn** thay vì chạy bằng các thành phần hành vi như nguồn thiết kế | Nếu sai, người chơi mất bảo vệ đúng tuần đầu — giai đoạn làm quen và dễ tilt nhất | 🔶 Quyết định thay user 2026-08-28 — nguồn chỉ giới hạn thành phần tính dưới 5 phiên, **không** tắt ma sát | Xác nhận với người chơi; xem OQ-11 |
| A-13 | Nhả sớm nút xác nhận không phải một lần tự huỷ | Nếu tính là tự huỷ thì mỗi lần trượt tay ở mức nóng lại được khen là kỷ luật, và bộ đếm mất ý nghĩa | 🔶 Quyết định thay user 2026-08-28 — `order-execution` UN-006 nói bộ đếm chỉ tính **quyết định của người chơi**, nhả tay giữa chừng không phải một quyết định | Xác nhận khi viết SRS, cùng lúc với `process-score` UN-008 |

## 9. User Success Criteria

| ID | User Outcome | Baseline | Target | Measurement | Review Period |
|---|---|---|---|---|---|
| USC-001 | Người chơi ít vào lại ngay sau một lệnh thua hơn | **Chưa có** — xác lập số trung bình mỗi phiên từ **4 phiên đầu**, giai đoạn cơ chế chưa hoạt động (xem A-12). Lấy baseline từ 10 phiên đầu sẽ trộn 6 phiên đã có ma sát vào mốc gốc | Số lần mở lệnh trong vòng 60 giây sau một lần đóng lỗ, tính trung bình mỗi phiên, thấp hơn baseline sau 3 tháng | Đếm số lần mở lệnh thoả điều kiện trên, chia cho số phiên, đọc cuối mỗi tháng. **Đọc kèm tổng số lệnh mỗi phiên** — giảm vì giao dịch ít hẳn đi thì không tính là tiến bộ | Hằng quý |
| USC-002 | Người chơi ít mở lệnh với khối lượng vọt lên bất thường hơn | **Chưa có** — xác lập tỷ lệ trung bình từ **4 phiên đầu**, giai đoạn cơ chế chưa hoạt động (xem A-12) | Tỷ lệ lệnh có khối lượng từ gấp đôi mức thường của phiên trở lên, thấp hơn baseline sau 3 tháng | Đếm số lệnh thoả điều kiện trên tổng số lệnh, đọc cuối mỗi tháng. **Đọc kèm mức thường của phiên theo tháng** — nếu chính mức thường đó bò lên thì tỷ lệ đẹp mà hành vi không đổi | Hằng quý |
| USC-003 | Người chơi vẫn còn bật cơ chế này sau 3 tháng | **Không cần baseline** — đây là điều kiện sống còn, không phải xu hướng | Cơ chế ở trạng thái bật ở cuối tháng thứ ba, và không có giai đoạn tắt kéo dài quá một phiên | Ghi nhận mọi lần đổi trạng thái bật/tắt kèm ngày; người chơi nêu lý do nếu muốn, không bắt buộc. Đọc cuối mỗi tháng | Hằng tháng |

> **Hai con số của USC-001 và USC-002 do chính feature này giữ theo phiên** (xem A-09 và Mục 3) — nên
> hai thước đo đọc được ngay cả khi `process-score` chưa có. Việc **hiện chúng thành xu hướng nhiều
> tháng** trên deck thì vẫn thuộc `process-score`; xem OQ-8.
>
> **USC-003 là thước đo canh gác hai cái kia.** Một cơ chế bị tắt thì USC-001 và USC-002 vẫn có thể
> đẹp lên vì lý do khác, và con số sẽ nói dối. Ba thước đo phải đọc cùng nhau.
>
> **Giới hạn đã biết:** cả ba đo *hành vi giảm đi*, không đo *quyết định tốt lên*. Người chơi vào lại
> ít hơn vì đã bình tĩnh hơn, và người chơi vào lại ít hơn vì đã chán, cho ra cùng một con số.

## 10. Open Questions

* [x] OQ-1: Ở mức quá nóng, người chơi có đường vượt qua khoảng chờ 5 phút không? — **Resolved 2026-08-28:** không có đường vượt. Chỉ hai cách: chờ hết giờ, hoặc ghi một memo để hạ chỉ số xuống dưới ngưỡng.
* [x] OQ-2: "Bấm đã đọc" có hạ chỉ số như ghi memo không? — **Resolved 2026-08-28:** không. Bấm đã đọc chỉ tắt dòng cảnh báo trên màn hình; chỉ có ghi memo mới hạ chỉ số. Nếu bấm một nút cũng hạ được thì cơ chế tự vô hiệu hoá.
* [x] OQ-3: Thành phần trạng thái giọng nói có nằm trong phạm vi không? — **Resolved 2026-08-28:** bỏ hẳn. Chỉ đo hành vi trên tay cầm và dữ liệu nhật ký; phần đóng góp của nó dồn về các thành phần hành vi. Mở lại thì phải qua một CR.
* [ ] OQ-4 **(ưu tiên — chốt trước `/srs`)**: Ma sát có áp cho thao tác **sửa mức cắt lỗ / chốt lời** không? Nguồn chỉ quy định cho mở, đóng, thoát khẩn cấp và khoá phiên. Nới cắt lỗ ra xa sau một lệnh thua là hành vi tilt điển hình, nhưng siết mức bảo vệ lại chính là hành vi phòng vệ nên cản là sai. Đây là khoảng trống duy nhất của ranh giới an toàn, và nó đang bỏ ngỏ **đúng cái cửa** mà một người đang tilt hay dùng nhất để tự làm hại mình thêm. Mặc định tạm "không siết" ở Mục 6 phải là lựa chọn có ý thức của người chơi, không phải hệ quả của việc chưa ai quyết.
* [ ] OQ-5: Ba ngưỡng chia bốn mức là số cố định hay người chơi tự chỉnh được sau khi có dữ liệu? Cho chỉnh thì nới ngưỡng trở thành đường lách hợp pháp của UN-003; không cho chỉnh thì A-03 sai là hỏng cả cơ chế.
* [ ] OQ-6: Hai phiên cách nhau vài giờ trong cùng một ngày thì chỉ số có mang sang không? Xem A-05.
* [ ] OQ-7: Ghi một memo hạ chỉ số **bao nhiêu**? Nguồn nói giảm một nửa các thành phần gần đây. Nếu một memo luôn đủ để ra khỏi mức quá nóng ngay lập tức thì nó thành thao tác lách chứ không còn là can thiệp — đặc biệt khi hệ thống không đọc nội dung (A-06).
* [ ] OQ-8: Hai con số của USC-001/USC-002 giờ do chính feature này giữ theo phiên. Deck của `process-score` có **hiện chúng ra** như một xu hướng nhiều tháng không, hay người chơi đọc thô từ dữ liệu phiên trong ba tháng đầu? Cần một dòng cascade sang `process-score` Mục 3 nếu chọn vế đầu. Xem A-09.
* [ ] OQ-9 **(ưu tiên — chốt trước `/srs`, cùng `voice-journal` OQ-8)**: Đường ra sớm khỏi khoảng khoá phải luôn dùng được. Ba tình huống làm nó biến mất: đang vũ trang (`voice-journal` không cho ghi âm lúc đó), đã tắt hẳn giọng nói, và không có mic. Chấp nhận kẹt trọn 5 phút trong các trường hợp đó, hay bắt buộc phải có một đường ghi memo không-lời (gõ chữ ngắn) luôn mở trong lúc bị khoá? Xem A-10.
* [ ] OQ-10: Có chấp nhận một **chế độ diễn tập** cho phép đặt thẳng mức trạng thái, để tự kiểm hai ranh giới UN-001 và UN-002 mà không phải dựng bằng hành vi thật cả buổi? Không có nó thì ranh giới an toàn quan trọng nhất của feature là thứ khó kiểm nhất.
* [ ] OQ-11: Trong **5 phiên đầu** — im lặng hoàn toàn (không ma sát), hay vẫn chạy bằng các thành phần hành vi như nguồn thiết kế? Im lặng thì mất bảo vệ đúng tuần dễ tilt nhất; chạy thì có thể chấm sai khi chưa hiểu gì về người chơi. Xem A-12.
* [ ] OQ-12: Câu mà AI desk nói ở mức nóng — nội dung của nó thuộc `ai-desk`, nhưng `ai-desk-urd.md` hiện **không nhắc gì tới tilt**. Nghĩa vụ này có được nhận không, hay bỏ hẳn phần AI nói ở mức nóng?

---

> **Lịch sử review:** chốt OQ-1, OQ-2, OQ-3 ngày 2026-08-28 (`/urd`, người chơi trả lời trực tiếp).
> Review bởi `@senior-ba` (6 blocking, 17 warning, 7 suggestion) và `@po-reviewer` (0 blocking,
> 3 warning, 2 suggestion) cùng ngày. Findings đã áp vào Mục 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 và sinh
> thêm UN-014, A-10 đến A-13, bốn tình huống ngoại lệ (đang vũ trang khi chạm mức quá nóng · không
> có đường ghi memo · đóng-mở phiên trong lúc bị khoá · hết khoá mà vẫn quá nóng) và OQ-9 đến OQ-12.
> **OQ-4 và OQ-9 phải chốt trước khi viết `/srs`** — cả hai đều chạm ranh giới an toàn.
