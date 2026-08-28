---
type: urd
feature: trade-replay
status: draft
updated: 2026-08-28
links: ["[[docs/_shared/project-profile.md]]", "[[docs/_shared/system-overview.md]]", "[[docs/_shared/definitions.md]]", "[[docs/_shared/operating-environment.md]]", "[[docs/order-execution/order-execution-urd.md]]", "[[docs/playbook-grading/playbook-grading-urd.md]]", "[[docs/voice-journal/voice-journal-urd.md]]"]
---

# trade-replay — User Requirements Document

## 1. Purpose

Ghi lại nhu cầu của người chơi quanh việc **biến một vị thế đã đóng thành một bài học** — tua lại
chính lệnh của mình qua bối cảnh thị trường lúc đó, bằng đúng cây cần analog đã dùng để vào lệnh.

Feature này nằm hoàn toàn trên đường học hỏi, chậm nhất trong ba đường của hệ thống, và **không bao
giờ đặt được một lệnh**. Vì vậy nhu cầu trung tâm ở đây không phải "vẽ lại biểu đồ cho đẹp" mà là
**"thấy lại quyết định của mình đúng thứ tự nó đã xảy ra — cả những quyết định không dẫn tới lệnh
nào"**. Cái làm nó thành huấn luyện chứ không phải xem biểu đồ chính là dải sự kiện: lần vũ trang đã
huỷ, lần bắn, lần dời mức bảo vệ, câu nói lúc đó, và mức tâm lý đang ở đâu.

### User Problem & Current Experience

| User | Current Situation | Problem | User Consequence | Evidence |
|---|---|---|---|---|
| Người chơi | Lệnh đóng xong chỉ còn lại con số lãi lỗ trong lịch sử tài khoản | Bối cảnh biến mất cùng lúc với vị thế — giá lúc đó đi thế nào, mình đã đắn đo bao lâu, đều không tra lại được | Không học được gì từ một lệnh cụ thể; chỉ nhớ được cảm giác thắng thua, thứ đánh lừa nhiều nhất | Observed: `phase-10` ("the review surface that turns a closed position into a lesson") |
| Người chơi | Những lần vũ trang rồi tự huỷ không để lại dấu vết nào ngoài một con số đếm | Quyết định **không vào lệnh** — thứ chiếm phần lớn một buổi tối tốt — trở thành khoảng trống trong bản ghi | Chỉ nhìn lại được những lần đã bấm, nên vô tình chỉ học từ hành động chứ không học từ sự kiềm chế | Observed: `story.md` ("Standing down is in the record as an event, not as a gap in it") |
| Người chơi | Lý do vào lệnh, nếu có ghi âm, nằm tách rời khỏi biểu đồ | Nghe lại lời mình nói mà không biết lúc đó giá đang làm gì | Không đối chiếu được điều mình *nghĩ* đang xảy ra với điều *thật sự* đang xảy ra — đúng chỗ sai lệch cần nhìn thấy nhất | Observed: `phase-10` ("hear the memo you recorded play at the moment you recorded it") |
| Người chơi | Công cụ nhật ký hiện có (TradeZella) có tua lại lệnh, nhưng bằng chuột trên một màn hình khác | Việc xem lại diễn ra trên phần cứng khác với lúc giao dịch, thành một việc hành chính phải nhớ mới làm | Xem lại thành việc bỏ dở; vòng lặp học hỏi đứt ngay chỗ đáng lẽ khép lại | Observed: `phase-10` ("TradeZella's trade replay, **on the hardware you already trade with**"); `docs/_shared/project-profile.md` (benchmark) |

## 2. User Types

| Tier | User Type | Context | Primary Goal | Pain Points |
|---|---|---|---|---|
| primary | **Người chơi** | Ngồi trước Chrome desktop, tay cầm trong tay — có thể ngay sau khi một lệnh vừa đóng, giữa phiên, hoặc sau khi đã đóng phiên | Nhìn lại một lệnh đủ rõ để rút ra được điều gì đó, mà không phải rời tay cầm và không phải đọc bảng số | Bối cảnh mất theo vị thế; lần đứng ngoài không để lại gì để xem; lời mình nói và biểu đồ nằm hai nơi |

> **Không có secondary user.** Công cụ cá nhân một người dùng. **AI desk không tham gia vào việc xem
> lại** — replay dựng lại sự kiện đã ghi, không diễn giải chúng. Sàn cTrader/Spotware là actor hệ
> thống, chỉ là nguồn của dữ liệu giá đã lưu. Xem `docs/_shared/project-profile.md`.

## 3. Scope Boundaries

### In Scope

* Hệ thống **tự đóng băng bối cảnh thị trường quanh mỗi lệnh** khi lệnh đóng — khoảng **5 phút trước lúc mở và 5 phút sau lúc đóng** (xem A-09). Người chơi không phải bật, không phải bấm gì, và **một buổi tối không có lệnh nào thì không lưu gì cả**. *(Việc đóng băng này chỉ tồn tại để phục vụ replay nên thuộc feature này — xem A-01, phải chốt trước khi viết SRS vì nó quyết định feature này là "màn đọc dữ liệu có sẵn" hay "màn đọc **cộng** hạ tầng ghi liên tục".)*
* Người chơi mở lại **một lệnh đã đóng** và tua tới lui qua bối cảnh đó **bằng cần analog trái**; **đổi được độ rộng khung nhìn bằng cần phải** để lúc thì thấy cả cửa sổ, lúc thì soi kỹ quanh điểm vào; phát/dừng và đổi **tốc độ phát** (chậm một nửa · thường · gấp đôi · gấp bốn) bằng nút.
* Người chơi thấy trên cùng một dải thời gian: **điểm vào, điểm ra, chỗ giá đi xa nhất theo hướng mình và ngược hướng mình**.
* Người chơi thấy **dải sự kiện** đúng thứ tự đã xảy ra, **mỗi sự kiện đọc được là gì** khi tua tới nó: mỗi lần vũ trang, mỗi lần tự huỷ, lần bắn, lúc sàn xác nhận, mỗi lần dời mức bảo vệ, mỗi memo, mỗi tín hiệu, và mỗi lần mức tâm lý đổi vùng.
* Người chơi **nghe lại memo của chính mình đúng khoảnh khắc đã nói**, tiếng đi theo đầu phát khi tua.
* Người chơi thấy **kết quả chấm luật của lệnh này trên cùng một màn hình** — luật nào đạt, luật nào không, có sạch hay không; không phải mở nơi khác rồi ghép lại bằng trí nhớ. *(Nội dung điểm thuộc `playbook-grading`; feature này chỉ đặt nó cạnh dòng thời gian.)*
* Người chơi **chuyển sang lệnh trước / lệnh sau trong cùng phiên** mà không phải quay ra danh sách.
* Người chơi mở thẳng màn xem lại **từ thông báo một lệnh vừa đóng**, không phải đi vòng qua danh sách. *(Nội dung thông báo vẫn thuộc `order-execution`; feature này chỉ nhận việc dẫn từ đó sang đây — xem OQ-8.)*
* Người chơi **ghi âm một memo mới ngay trong lúc xem lại**, gắn vào lệnh đang xem và phân biệt được với memo đã ghi lúc vào lệnh. *(Cơ chế ghi âm thuộc `voice-journal`; feature này nhận **nhu cầu ghi lại điều rút ra tại đúng chỗ nhận ra nó** — xem UN-008 về đích gắn memo.)*
* **Không có lệnh nào phát ra được từ màn xem lại.** Bị khoá: **mở lệnh mới và sửa mức bảo vệ**. **Không bị khoá: đóng một vị thế đã chọn, và thoát khẩn cấp** — kế thừa bất biến của `order-execution` UN-003.
* Người chơi mở replay **vào bất cứ lúc nào**, kể cả khi đang có vị thế mở, và được nói rõ đang khoá gì bằng **một dòng thông báo**, vào thẳng không phải xác nhận thêm (chốt 2026-08-28).
* Lệnh cũ **không còn bối cảnh đã lưu** vẫn mở ra được ở dạng rút gọn — điểm vào, điểm ra, kết quả — **không bao giờ trắng màn và không bao giờ báo lỗi**.

### Out of Scope

* **Ghi âm và chuyển lời nói thành văn bản** thuộc feature `voice-journal`. URD này chỉ nhận việc *phát lại* memo đúng thời điểm, và *nhu cầu* ghi thêm một memo lúc xem lại.
* **Nội dung chấm luật playbook** (luật nào, chấm ra sao) thuộc feature `playbook-grading`. URD này chỉ nhận việc **đặt kết quả đó cạnh dòng thời gian**.
* **Điểm quy trình 5 trục, trong đó trục Review tiêu thụ việc "đã xem lại"** thuộc feature `process-score`. URD này chỉ nhận **ranh giới**: mở màn replay là đủ để tính (chốt 2026-08-28), nên feature này không được đặt thêm điều kiện nào lên việc đó.
* **Bảng lịch sử lệnh, bản đồ nhiệt theo ngày, chi tiết một ngày** thuộc feature `daily-journal`. Đó là các *đường vào* dẫn tới replay, không phải replay.
* **So sánh thực tế với kế hoạch, xu hướng lỗi** thuộc feature `execution-learning` *(tách khỏi `daily-journal` 2026-08-28)*.
* **So sánh nhiều lệnh với nhau, thống kê theo playbook** thuộc `process-score`; **nguyên tắc cá nhân** thuộc `daily-journal` *(chốt 2026-08-28)*. Replay xem **một** lệnh tại một thời điểm.
* **Đo trạng thái tâm lý** thuộc feature `tilt-meter`. URD này chỉ *hiện lại* mức tâm lý đã ghi như một sự kiện trên dải thời gian.
* **Tư vấn, tín hiệu, phân tích** thuộc feature `ai-desk`. Tín hiệu đã sinh ra lúc đó hiện lại như sự kiện; **không có diễn giải mới nào được tạo ra lúc xem lại**.
* **Sao lưu, xuất dữ liệu, xoá toàn bộ** (bối cảnh đã lưu nằm trong gói sao lưu) thuộc feature `reports-export`.
* **Lưu bối cảnh cho một lần đứng ngoài không dẫn tới lệnh nào** — chốt 2026-08-28: không lưu. Lần tự huỷ chỉ hiện lại khi nó rơi vào cửa sổ quanh một lệnh có thật.
* Tua lại **cả buổi tối như một dòng liên tục** — replay đi theo từng lệnh, không theo phiên. *(Xem OQ-4.)*

## 4. User Needs

| ID | User | Context / Trigger | User Need | Expected Outcome | Importance | Evidence |
|---|---|---|---|---|---|---|
| UN-001 | Người chơi | Một lệnh vừa đóng, hoặc đang nhìn lại một lệnh cũ | Tua lại chính lệnh đó qua bối cảnh thị trường lúc nó xảy ra | Cửa sổ khoảng 5 phút trước lúc mở và 5 phút sau lúc đóng đều có mặt. Đầu phát **bám theo tay cầm không có độ trễ nhận ra được, và không vị trí nào trong cửa sổ phải chờ tải**. Đổi được độ rộng khung nhìn để lúc thì thấy cả cửa sổ, lúc thì soi kỹ quanh điểm vào. **Phần sau lúc đóng cần một khoảng để thu xong trước khi tua được, và người chơi được nói rõ điều đó** thay vì thấy như dữ liệu bị mất | Critical | Observed: `phase-10` ("scrub ... with the left stick"; cửa sổ `[opened_at − 300s, closed_at + 300s]`); `phase-02` (việc đóng băng chạy tại `closed_at + post_roll_s`) |
| UN-002 | Người chơi | Mọi lúc đang ở màn xem lại | **Không có bất kỳ lệnh nào phát ra được từ đây** | Bị khoá suốt thời gian ở màn này: **mở lệnh mới và sửa mức bảo vệ**. **Không bị khoá: đóng một vị thế đã chọn, và thoát khẩn cấp** — kế thừa bất biến của `order-execution` UN-003; người chơi đang ôm vị thế không bao giờ bị dồn vào chỗ chỉ còn cách đóng sạch mọi thứ | Critical | Observed: `phase-10` ("the order FSM is **hard `LOCKED`**"; "No order can be placed from the replay route"); `order-execution-urd.md` UN-003; `phase-02` ("close/panic still allowed") |
| UN-003 | Người chơi | Đang tua lại một lệnh | Thấy lần vũ trang mình đã huỷ nằm đúng chỗ của nó trên dòng thời gian | Lần tự huỷ hiện như một sự kiện có mốc thời gian thật, không phải một khoảng trống — kể cả khi nó xảy ra hàng chục giây trước lần bắn. *(Đây là trường hợp sắc nét nhất của dải sự kiện ở UN-011, không phải một năng lực tách rời.)* | Critical | Observed: `phase-10` ("watch the ARM you cancelled forty seconds before you fired"); `story.md` ("in the record as an event, not as a gap in it") |
| UN-004 | Người chơi | Đang tua lại một lệnh | Thấy giá đã đi xa nhất tới đâu theo hướng mình và ngược hướng mình | Cả hai mốc hiện trên biểu đồ tại đúng thời điểm chạm, đo đúng chiều của lệnh — lệnh mua và lệnh bán không được đo lẫn chiều | High | Observed: `phase-10` ("see where MFE and MAE actually sat"; "a long's excursion is measured on the bid and a short's on the ask ... bid-only would be a silent asymmetry bug") |
| UN-005 | Người chơi | Đang tua lại một lệnh đã có ghi âm | Nghe lại lời mình nói **đúng khoảnh khắc đã nói**, không phải nghe rời | Tiếng tự phát khi đầu phát đi qua chỗ đã ghi, dừng và quay lại đúng chỗ khi tua đi nơi khác. Nghe được lời mình rồi nhìn giá lúc đó là cách đối chiếu suy nghĩ với thực tế | Critical | Observed: `phase-10` ("hear the memo ... play at the moment you recorded it"; audio synced to playhead) |
| UN-006 | Người chơi | Lệnh cũ, hoặc lệnh xảy ra trước khi hệ thống bắt đầu lưu bối cảnh | Mở ra vẫn thấy được cái gì đó, không gặp màn trắng hay thông báo lỗi | Bản rút gọn dựng từ dữ liệu lệnh đã đóng: điểm vào, điểm ra, khối lượng, kết quả — nói rõ là không còn bối cảnh, chứ không tỏ ra hỏng. **Trạng thái này phải đọc khác hẳn** với trạng thái "bối cảnh đang thu nốt" của một lệnh vừa đóng | High | Observed: `phase-10` ("degrades to a marker-only static view ...; **it never blanks**") |
| UN-007 | Người chơi | Đang xem lại và muốn hiểu vì sao mình vào lệnh đó | Thấy luật nào đạt, luật nào không, trên cùng màn hình | Kết quả chấm của đúng lệnh này nằm cùng màn hình với dòng thời gian — không phải mở nơi khác rồi ghép lại bằng trí nhớ | High | Observed: `phase-10` ("the phase 7 grade for this cid renders beside the chart"); `playbook-grading-urd.md` UN-014 |
| UN-008 | Người chơi | Đang xem lại và nhận ra điều gì đó | Ghi lại điều rút ra **bằng giọng nói, ngay tại chỗ vừa nhận ra** | Ghi âm được một memo mới gắn với lệnh đang xem, không phải gõ phím. **Khi đang ở màn xem lại, đích gắn memo là lệnh đang xem — đè lên luật "gắn vào vị thế đang mở" của `voice-journal`**, vì đích đến phải là thứ người chơi đang nhìn thấy. Memo này phân biệt rõ với memo đã ghi lúc vào lệnh: một cái là lý do, một cái là bài học | High | Confirmed 2026-08-28 (người chơi chọn "ghi âm một memo mới khi xem lại"). Xung đột với `voice-journal-urd.md` UN-004 — cần cascade, xem A-05 |
| UN-009 | Người chơi | Đang xem một lệnh, muốn xem lệnh kế tiếp trong cùng phiên | Chuyển lệnh trước/sau ngay tại chỗ | Sang được lệnh liền trước hoặc liền sau **của cùng phiên** — theo định nghĩa phiên của `order-execution`, không phải cùng ngày lịch, kể cả khi phiên vắt qua nửa đêm. Thao tác này **không dùng cặp nút giữ để ghi âm** (chốt OQ-1) | High | Observed: `phase-10` ("LB/RB step to the previous and next trade of the same evening") |
| UN-010 | Người chơi | Muốn xem lại ngay khi bối cảnh còn nóng, kể cả khi vẫn đang có vị thế chạy | Mở replay **bất cứ lúc nào**, tự chịu trách nhiệm về việc tạm mất đường mở lệnh mới | Vào được ngay giữa phiên, không phải xác nhận thêm bước nào. Khi đang có vị thế mở, **một dòng thông báo** nói rõ điều gì đang bị khoá và điều gì vẫn dùng được, để lựa chọn là chủ động chứ không phải bất ngờ | High | Confirmed 2026-08-28 (người chơi chọn "mọi lúc, kể cả đang có vị thế mở"; cách nhắc: "một dòng thông báo, vào thẳng") |
| UN-011 | Người chơi | Đang tua lại một lệnh | Thấy đủ chuỗi quyết định, không chỉ lệnh khớp | Trên cùng dòng thời gian: mỗi lần vũ trang, mỗi lần huỷ, lần bắn, lúc sàn xác nhận, mỗi lần dời mức bảo vệ, memo, tín hiệu, và lần mức tâm lý đổi vùng — **mỗi sự kiện đọc được là gì khi tua tới nó**, không chỉ thấy có một dấu ở đó. Đây là thứ làm nó thành huấn luyện chứ không phải xem biểu đồ | Critical | Observed: `phase-10` ("arm, cancel, fire, ack, sl_move, memo, volman_tag, tv_signal, tilt_band_change ... makes it coaching rather than charting"; "hovering or scrubbing onto an event shows its one-line label") |
| UN-012 | Người chơi | Vào và ra khỏi màn xem lại nhiều lần trong một buổi | Việc xem lại **không tự nó tạo thêm áp lực phải giao dịch** | Không đếm chuỗi, không huy hiệu, không cấp độ gắn với việc xem lại. Mở replay chỉ đơn giản được ghi nhận là đã xem — mở là tính, không có điều kiện phụ. **Mỗi lần mở xem lại một lệnh được ghi nhận: lệnh nào, lúc nào. Feature này tạo ra bản ghi đó; `process-score` và `daily-journal` chỉ đọc** | Medium | Confirmed 2026-08-28 ("mở màn replay là tính"); `README.md` ("No streaks, no levels, no badges"). Việc ghi nhận theo từng lệnh: 🔶 xem A-08 |
| UN-013 | Người chơi | Chi tiết vào lệnh nhỏ hơn một nến của bối cảnh đã lưu | Không bị bối cảnh thô làm hiểu sai điểm vào thật | Điểm vào và điểm ra lấy từ chính bản ghi lệnh, không suy ra từ biểu đồ. Nến chỉ là bối cảnh, mốc mới là sự thật | Medium | Observed: `phase-10` ("the fill price and timestamp are drawn from `trade_closed`, not inferred from bars; the bar is context, the marker is truth") |
| UN-014 | Người chơi | Suốt phiên, không cần làm gì cả | Bối cảnh của mỗi lệnh **tự có mặt** để sau này còn tua lại được | Bối cảnh quanh mỗi lệnh được lưu tự động khi lệnh đóng; người chơi không phải bật, không phải nhớ, không phải bấm gì. **Một buổi không có lệnh nào thì không lưu gì cả** — không có kho dữ liệu nào phình ra sau một tối đứng ngoài | Critical | Observed: `phase-02` (ring buffer luôn chạy, chỉ đóng băng quanh lệnh thật); `phase-10` ("a zero-trade evening writes zero tape; there is no firehose to prune"). Quyền sở hữu: 🔶 xem A-01 |

## 5. Prioritized User Journeys

### Journey 1: Tua lại một lệnh vừa đóng

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Một vị thế vừa đóng, người chơi muốn xem lại ngay
* __Expected outcome:__ Người chơi thấy trọn chuỗi từ lúc trước khi mở tới sau khi đóng, biết giá đã đi xa tới đâu về hai phía, và thấy luôn lệnh đó có theo luật của mình không
* __Related needs:__ UN-001, UN-004, UN-007, UN-011, UN-013, UN-014

1) Người chơi mở lệnh vừa đóng từ thông báo lệnh đóng, hoặc từ danh sách lệnh.
2) Nếu phần sau lúc đóng chưa thu xong, màn hình nói rõ đang chờ và tự hiện ra khi xong.
3) Bối cảnh hiện ra kèm điểm vào, điểm ra và hai mốc giá đi xa nhất.
4) Kết quả chấm luật của lệnh này hiện cùng màn hình — luật nào đạt, luật nào không.
5) Gạt cần analog trái để tua tới lui; đầu phát chạy theo tay. Bấm phát để chạy tự động, đổi tốc độ khi muốn xem nhanh hoặc chậm.
6) Thoát ra và quay về chỗ vừa đi vào.

__Independent verification:__ Lấy một lệnh có kết quả đã biết trên cTrader demo; điểm vào và điểm ra
trên màn xem lại phải khớp với bản ghi lệnh, hai mốc giá đi xa nhất phải nằm **đúng chiều** của lệnh
— kiểm bằng một lệnh mua và một lệnh bán, không phải chỉ một chiều — và phần luật đạt/không đạt phải
khớp với bản ghi điểm của `playbook-grading`. Không cần journey nào khác.

### Journey 2: Không có lệnh nào bay ra từ màn xem lại

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Đang ở màn xem lại, tay vẫn đặt trên tay cầm, bấm đúng những nút thường dùng để vào lệnh
* __Expected outcome:__ Không có lệnh mới nào tới sàn
* __Related needs:__ UN-002, UN-010

1) Người chơi vào màn xem lại.
2) Bấm tổ hợp vẫn dùng để mở lệnh.
3) Không có lệnh nào được chuẩn bị, không có gì gửi đi, không có xác nhận nào hiện ra.
4) Thoát ra; khả năng đặt lệnh trở lại nguyên vẹn.

__Independent verification:__ Suốt thời gian màn xem lại đang mở, kiểm trên cTrader demo phải thấy
**không có vị thế mới nào và không có thay đổi mức bảo vệ nào, bất kể bấm gì — ngoài việc đóng vị
thế và thoát khẩn cấp, hai thứ luôn được phép (xem A-02)**. Kiểm chiều ngược: thoát ra rồi bắn một
lệnh thật, phải vào bình thường — chứng minh việc khoá đã nhả đúng. Đây là journey phải đúng kể cả
khi mọi thứ khác của feature hỏng.

### Journey 3: Nhìn lại lần mình đã đứng ngoài

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Nhớ mang máng là tối qua đã suýt vào một lệnh khác trước lệnh đã bắn
* __Expected outcome:__ Lần vũ trang đã huỷ hiện đúng chỗ, đúng giờ, như một quyết định có thật
* __Related needs:__ UN-003, UN-011

1) Người chơi mở lệnh đã bắn hôm đó.
2) Tua ngược về phần trước lúc mở.
3) Dải sự kiện hiện lần vũ trang, rồi lần huỷ, tại đúng mốc thời gian của chúng, mỗi cái đọc được là gì.
4) Người chơi đối chiếu: lúc huỷ giá đang làm gì, và nếu vào thì đã ra sao.

__Independent verification:__ Vũ trang một hướng rồi huỷ, đợi khoảng nửa phút, sau đó vào một lệnh
thật và đóng nó. Trên màn xem lại, lần huỷ phải xuất hiện **trước** lần bắn, cách đúng khoảng thời
gian thật — đối chiếu được với đồng hồ, không phải với trí nhớ.

### Journey 4: Nghe lại lời mình nói lúc vào lệnh

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Xem lại một lệnh đã ghi âm lý do lúc vào
* __Expected outcome:__ Người chơi nghe được lý do của chính mình đồng thời nhìn thấy giá lúc đó
* __Related needs:__ UN-005, UN-001

1) Người chơi mở một lệnh có ghi âm; dòng thời gian đánh dấu chỗ đã nói.
2) Cho chạy; tới đúng chỗ đó tiếng tự phát.
3) Tua đi nơi khác — tiếng dừng; tua về — tiếng khớp lại đúng chỗ.
4) Người chơi so điều mình nói lúc đó với điều thị trường thật sự làm.

__Independent verification:__ Ghi một memo tại một thời điểm biết trước trong một lệnh, sau đó xem
lại: tiếng phải bắt đầu ở đúng mốc đó chứ không ở đầu cửa sổ, và sau vài lần tua qua tua lại vẫn
khớp — không trôi dần.

### Journey 5: Ghi lại điều rút ra ngay khi nhận ra

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Đang tua lại một lệnh cũ **đã có sẵn memo ghi lúc vào lệnh** thì nhận ra mình đã vào sớm hai phút
* __Expected outcome:__ Điều rút ra được nói ra và lưu lại tại đúng lệnh đó, không phải nhớ để ghi sau
* __Related needs:__ UN-008, UN-011

1) Người chơi đang ở màn xem lại và nhận ra điều gì đó.
2) Ghi âm một memo mới bằng **chính cặp nút giữ vẫn dùng để ghi âm ở mọi nơi khác** (chốt OQ-1) — cơ bắp không phải học lại.
3) Memo được gắn vào **lệnh đang xem**, đánh dấu rõ là ghi lúc xem lại chứ không phải lúc vào lệnh.
4) Lần sau mở lại lệnh này, memo đó có mặt cùng memo cũ, phân biệt được hai loại.

__Independent verification:__ Ghi một memo lúc xem lại một lệnh cũ của hôm trước; mở lại lệnh đó phải
thấy đủ hai memo và phân biệt được cái nào ghi lúc nào — kiểm bằng chính mốc thời gian của chúng.
Kiểm thêm trường hợp khó: làm việc này **trong lúc đang có một vị thế khác mở**, memo mới phải gắn
vào lệnh đang xem chứ không phải vị thế đang chạy.

### Journey 6: Đi qua các lệnh của một phiên

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Sau phiên, muốn xem lại tất cả các lệnh của tối nay lần lượt
* __Expected outcome:__ Người chơi đi hết các lệnh mà không phải quay ra vào danh sách mỗi lần
* __Related needs:__ UN-009, UN-001

1) Người chơi mở lệnh đầu tiên của phiên.
2) Xem xong, chuyển thẳng sang lệnh kế tiếp.
3) Bối cảnh mới hiện ra, đầu phát về đầu, tiếng của lệnh trước dừng hẳn.
4) Đi hết phiên rồi thoát.

__Independent verification:__ Một phiên có ba lệnh: đi tới đi lui qua cả ba phải luôn ra đúng ba lệnh
đó theo đúng thứ tự thời gian, và ở hai đầu thì dừng lại chứ không nhảy sang phiên khác. Kiểm bằng
một phiên vắt qua nửa đêm để chắc ranh giới là **phiên**, không phải ngày lịch.

### Journey 7: Xem lại một lệnh không còn bối cảnh

* __User:__ Người chơi · __Importance:__ Medium
* __Trigger:__ Mở một lệnh cũ hơn thời điểm hệ thống bắt đầu lưu bối cảnh, hoặc lệnh có bối cảnh bị thiếu
* __Expected outcome:__ Vẫn thấy được lệnh đó, và biết rõ vì sao không có gì để tua
* __Related needs:__ UN-006

1) Người chơi mở một lệnh cũ.
2) Màn hình hiện bản rút gọn: điểm vào, điểm ra, khối lượng, kết quả.
3) Nói rõ bối cảnh của lệnh này **không còn** — khác hẳn với thông điệp "đang thu nốt" của một lệnh vừa đóng.
4) Chuyển sang lệnh khác vẫn hoạt động bình thường.

__Independent verification:__ Mở một lệnh chắc chắn không có bối cảnh đã lưu: màn hình phải hiện nội
dung thật của lệnh, không phải màn trắng và không phải thông báo lỗi; và việc chuyển sang lệnh liền
kề vẫn chạy. Đối chiếu thông điệp với thông điệp của một lệnh vừa đóng — hai câu phải khác nhau rõ.

### Journey 8: Xem lại giữa phiên khi đang có vị thế mở

* __User:__ Người chơi · __Importance:__ Medium
* __Trigger:__ Một lệnh vừa đóng nhưng một lệnh khác vẫn đang chạy, người chơi vẫn muốn xem ngay
* __Expected outcome:__ Người chơi xem được, biết rõ mình đang tạm mất gì, và không bao giờ mất đường đóng vị thế
* __Related needs:__ UN-010, UN-002

1) Người chơi mở replay trong lúc còn một vị thế đang chạy — vào thẳng, không phải xác nhận thêm.
2) Một dòng thông báo nói rõ: đang có vị thế mở, mở lệnh mới và sửa mức bảo vệ tạm khoá, đóng vị thế và thoát khẩn cấp vẫn dùng được.
3) Người chơi xem xong, thoát ra.
4) Khả năng thao tác trở lại đầy đủ ngay lập tức.

__Independent verification:__ Với một vị thế đang mở, vào màn xem lại; **trước tiên** thử mở một lệnh
mới — phải không có vị thế nào phát sinh. **Sau đó** mới kích hoạt thoát khẩn cấp: vị thế phải đóng
trên cTrader demo và màn xem lại tự thoát về màn chính (chốt OQ-2). Thứ tự này bắt buộc — làm ngược
lại thì việc khoá phiên sau thoát khẩn cấp sẽ che mất điều đang cần kiểm.

## 6. User Exceptions & Edge Conditions

| Situation | User Impact | Expected User-facing Outcome | Related Journey / Need |
|---|---|---|---|
| **Lệnh vừa đóng, phần sau lúc đóng chưa thu xong** | Mở ra ngay thì chưa có gì để tua — dễ tưởng dữ liệu hỏng, hoặc tệ hơn là đọc nhầm thành "bối cảnh không còn" | Nói rõ **đang thu nốt phần sau lúc đóng**, còn khoảng bao lâu nữa; tự hiện ra khi xong, không bắt mở lại. Câu chữ phải khác hẳn thông điệp "bối cảnh không còn" của J7 | J1, J7 / UN-001, UN-006 |
| **Lệnh không còn bối cảnh đã lưu** | Mở ra không có gì để tua | Bản rút gọn dựng từ bản ghi lệnh; nói rõ bối cảnh không còn. Không trắng màn, không báo lỗi | J7 / UN-006 |
| **Phần đuôi bối cảnh bị cụt** (tắt máy hoặc đóng phiên trước khi thu đủ 5 phút sau lúc đóng) | Cửa sổ ngắn hơn bình thường, dễ tưởng dữ liệu hỏng | Hiện đúng phần đã có và tua bình thường trong phạm vi đó; nói rõ phần sau lúc đóng ngắn hơn 5 phút, không báo lỗi | J1 / UN-001 |
| **Lệnh không có ghi âm** | Không có gì để nghe | Không hiện dấu memo và không hiện điều khiển tiếng; mọi thứ khác y nguyên. Không có ô trống hay nút chết | J4 / UN-005 |
| **Có tiếng nhưng phần chuyển thành chữ hỏng** | Tưởng mất luôn cả bản ghi âm | Tiếng vẫn phát bình thường tại đúng chỗ; nói rõ chỉ phần chữ thiếu. Bản ghi sống sót qua việc chuyển chữ | J4 / UN-005 |
| **Dấu memo còn nhưng bản ghi âm đã hết hạn hoặc đã bị xoá** | Bấm vào chỗ có dấu mà không nghe được gì | Dấu memo vẫn hiện đúng mốc kèm phần chữ nếu còn; chỗ nghe lại nói rõ tiếng không còn và vì sao. Phần tua lại không bị ảnh hưởng | J4 / UN-005 |
| **Tiếng lệch khỏi hình sau nhiều lần tua** | Nghe lời mình nói trên một đoạn giá không phải lúc nói | Mốc thời gian của memo là mốc chuẩn; mỗi lần tua là khớp lại. Từ mức tốc độ gấp đôi trở lên thì tắt tiếng thay vì phát méo | J4 / UN-005 |
| **Nến bối cảnh thô hơn khoảnh khắc khớp lệnh** | Điểm vào thật bị nến che, đọc sai chỗ mình đã vào | Điểm vào và điểm ra lấy từ bản ghi lệnh, luôn vẽ đúng chỗ dù nến thô. Nến là bối cảnh, mốc là sự thật | J1 / UN-013 |
| **Bấm nút vào lệnh trong lúc đang xem lại** | Rủi ro lớn nhất của feature: một lệnh thật bay ra từ màn ôn tập | Không lệnh nào được chuẩn bị và không gì gửi đi; im lặng bỏ qua chứ không hiện cảnh báo gây hoang mang | J2 / UN-002 |
| **Đang có vị thế mở mà vào màn xem lại** | Đang cầm rủi ro thật mà không mở được lệnh mới | Một dòng thông báo ngay khi vào: mở lệnh mới và sửa mức bảo vệ đang khoá, **đóng vị thế và thoát khẩn cấp vẫn dùng được**. Vào thẳng, không thêm bước xác nhận (chốt 2026-08-28) | J8 / UN-010 |
| **Muốn đóng một vị thế cụ thể trong lúc đang xem lại** | Chỉ còn cách đóng sạch mọi thứ thì phải đóng cả những vị thế không muốn đóng | Đóng một vị thế đã chọn **không bị khoá** — kế thừa bất biến của `order-execution`. Chỉ mở lệnh mới và sửa mức bảo vệ mới bị khoá | J8 / UN-002 |
| **Cần thoát khẩn cấp trong lúc đang xem lại** | Kẹt trong màn ôn tập giữa lúc thị trường chạy ngược | Thoát khẩn cấp **không bao giờ bị khoá**: đóng vị thế **và thoát luôn khỏi màn xem lại** về màn chính, để người chơi tự mắt xác nhận mọi thứ đã phẳng (chốt OQ-2) | J8 / UN-002, UN-010 |
| **Một vị thế khác đóng trong lúc đang xem lại** | Bỏ lỡ việc một lệnh vừa kết thúc | Được báo như bình thường mà không đá người chơi ra khỏi màn đang xem; xem xong vào lệnh mới đóng đó là việc riêng | J8 / UN-010 |
| **Ghi âm memo trong lúc đang có một vị thế khác mở** | Bài học về lệnh đang xem bị ghi nhầm vào vị thế đang chạy — không ai phát hiện ra | Đích gắn memo là **lệnh đang xem**, không phải vị thế đang mở. Đây là ngoại lệ có chủ ý so với luật chung của `voice-journal` (xem A-05) | J5, J8 / UN-008 |
| **Memo ghi lúc xem lại lẫn với memo ghi lúc vào lệnh** | Đọc lại tưởng lúc vào lệnh đã biết điều mà thực ra nhận ra sau | Hai loại luôn phân biệt được, ở mọi nơi chúng xuất hiện: một cái là lý do lúc vào, một cái là bài học lúc nhìn lại | J5 / UN-008 |
| **Một sự kiện nằm trong cửa sổ của nhiều lệnh** (hai lệnh mở gần nhau, cửa sổ chồng nhau) | Cùng một lần huỷ hiện trên dải sự kiện của cả hai lệnh, đọc lại tưởng hai lần huỷ khác nhau | Sự kiện hiện ở mọi lệnh mà nó rơi vào cửa sổ, nhưng nói rõ nó **không thuộc riêng lệnh đang xem** | J3 / UN-003, UN-011 |
| **Bối cảnh còn nhưng kết quả chấm luật thì không** (lệnh chấm theo playbook đã ngừng dùng, hoặc lệnh ngoài kế hoạch) | Ô điểm trống, tưởng hỏng | Nói rõ lệnh này không có điểm hoặc thuộc nhóm ngoài kế hoạch; phần tua lại không phụ thuộc vào điểm | J1 / UN-007 |
| **Đang xem lại thì kết nối tới máy chủ rớt** | Đang tua dở thì đứng hình | Phần đã tải vẫn tua được; nói rõ không lấy thêm được lệnh khác cho tới khi kết nối lại. Việc mất kết nối lúc ôn tập không phải sự cố giao dịch | J1, J6 / UN-001, UN-009 |
| **Cửa sổ Chrome mất focus giữa lúc đang xem lại** | Tiếng vẫn chạy trong khi người chơi đã nhìn chỗ khác | Đầu phát và tiếng cùng dừng lại, giữ nguyên vị trí; quay lại thì tiếp tục đúng chỗ đó | J1, J4 / UN-001, UN-005 |
| **Phiên không có lệnh nào** | Mở replay ra không có gì | Nói rõ phiên này chưa có lệnh nào để xem lại — **đó không phải lỗi cũng không phải thiếu sót** — và chỉ đường tới các lệnh của những phiên trước, để một tối đứng ngoài vẫn xem lại được bài học cũ | J6 / UN-012 |
| **Lần tự huỷ nằm ngoài cửa sổ của mọi lệnh** | Nhớ là đã huỷ nhưng không tìm thấy đâu để xem | Lần huỷ đó vẫn được ghi nhận là đã xảy ra, nhưng không tua lại được bối cảnh — nói rõ vì sao, thay vì im lặng như chưa từng có (chốt 2026-08-28) | J3 / UN-003 |
| **Xem lại một lệnh của nhiều tháng trước** | Không rõ bối cảnh còn được giữ tới bao giờ | Bối cảnh cũ quá hạn giữ thì rơi về bản rút gọn như J7, và người chơi biết trước điều đó thay vì phát hiện lúc cần. Hạn giữ bối cảnh dài hơn hạn giữ bản ghi âm — xem OQ-6 | J7 / UN-006 |

## 7. User-side Constraints

* **Xem lại là việc trên đường học hỏi, không phải đường đặt lệnh** — nó chậm hơn, và không bao giờ được đi chung đường với lệnh. Kế thừa ranh giới của `docs/_shared/system-overview.md`.
* **Chỉ chạy trên Chrome desktop**, tay cầm nối bằng dongle 2.4G, cửa sổ phải đang focus — kế thừa ràng buộc của `order-execution`. Mất focus thì việc xem lại tạm dừng, không chạy tiếp trong nền.
* **Toàn bộ thao tác xem lại làm bằng tay cầm**: cần trái tua, cần phải đổi độ rộng khung nhìn, nút phát/dừng và đổi tốc độ. Không có thao tác nào bắt buộc phải dùng chuột hay bàn phím.
* **Bối cảnh chỉ có quanh những lệnh đã đóng**, và chỉ tua được sau khi phần sau lúc đóng thu xong. Một buổi tối không giao dịch không để lại gì để tua, và đó là chủ ý — không phải thiếu sót cần khắc phục.
* **Bối cảnh đã lưu là dữ liệu quá khứ, không phải mô phỏng.** Không thử được "nếu lúc đó tôi làm khác thì sao" — replay chiếu lại điều đã xảy ra, không dựng ra điều chưa xảy ra.
* **Bản ghi âm là dữ liệu giọng nói cá nhân**, nằm trên máy chủ riêng và đi cùng gói sao lưu; nơi lưu, hạn giữ và cách xoá thuộc `voice-journal` và `reports-export`.
* Chỉ tài khoản demo. Việc xem lại **không phải lời khuyên đầu tư** — nó chỉ chiếu lại điều đã xảy ra.
* Giao diện sản phẩm bằng tiếng Anh; tài liệu nghiệp vụ bằng tiếng Việt.

## 8. Assumptions & Validation

| ID | Assumption | Impact if Wrong | Validation Status | Next Action |
|---|---|---|---|---|
| A-01 | Việc **tự đóng băng bối cảnh quanh mỗi lệnh** (UN-014) thuộc feature này, không thuộc `order-execution` | Đổi hoàn toàn quy mô công việc: "màn đọc dữ liệu có sẵn" hay "màn đọc **cộng** hạ tầng ghi chạy nền quanh mọi lệnh". Sai chỗ thì cả ước lượng công sức lẫn ranh giới Mục 3 đều lệch | Chưa xác nhận — `order-execution-urd.md` Mục 3 không nhận việc này, mà replay là nơi duy nhất tiêu thụ nó | **Chốt trước khi viết SRS, không để trôi.** Nếu chuyển sang `order-execution` thì UN-014 rời khỏi doc này và thêm một dòng Out of Scope |
| A-02 | Việc khoá khi ở màn xem lại áp cho **mở lệnh mới và sửa mức bảo vệ**, **không** áp cho đóng vị thế và thoát khẩn cấp | Nếu khoá cả hai việc kia, người chơi đang cầm vị thế bị kẹt trong màn ôn tập, hoặc bị dồn vào chỗ chỉ còn cách đóng sạch mọi thứ — rủi ro lớn hơn nhiều so với việc bắn nhầm | **Đã xác nhận** 2026-08-28: hành vi thoát khẩn cấp chốt qua OQ-2 (đóng vị thế và thoát luôn khỏi màn xem lại). Việc "đóng một vị thế đã chọn cũng không bị khoá" là kế thừa bất biến của `order-execution` UN-003, không phải quyết định mới | Nêu lại trong SRS như một bất biến, có test riêng |
| A-03 | Cách nhắc khi vào replay lúc đang có vị thế mở là **một dòng thông báo**, vào thẳng | Nếu người chơi muốn được hỏi lại, cách vào màn xem lại đổi | **Đã xác nhận** 2026-08-28 (người chơi chọn "một dòng thông báo, vào thẳng") | Không còn việc phải làm |
| A-04 | Người chơi **không cần** xem lại cả buổi như một dòng liên tục; xem theo từng lệnh là đủ | Nếu muốn xem cả buổi, cách lưu bối cảnh đổi hoàn toàn — hiện chỉ lưu quanh từng lệnh | Chưa xác nhận — suy từ `phase-10` (mỗi lệnh một cửa sổ) | Hỏi khi viết SRS, xem OQ-4 |
| A-05 | Memo ghi lúc xem lại dùng **chính cơ chế ghi âm** đang có, chỉ khác ở đích gắn: **lệnh đang xem**, không phải vị thế đang mở | `voice-journal-urd.md` UN-004 quy định memo gắn vào vị thế đang mở. Không thống nhất thì một bài học về lệnh này sẽ nằm trong bản ghi của lệnh khác, và không ai phát hiện ra | Chưa xác nhận — mâu thuẫn thật giữa hai URD, phát hiện qua review 2026-08-28 | **Cascade sang `docs/voice-journal/voice-journal-urd.md` UN-004** để nhận ngoại lệ "đang ở màn xem lại thì đích là lệnh đang xem". Chưa làm — xem OQ-9 |
| A-06 | Người chơi chấp nhận rằng lần đứng ngoài **ngoài cửa sổ của mọi lệnh** không tua lại được | Nếu sau vài tháng thấy tiếc những tối đứng ngoài trọn vẹn, phải quay lại lưu bối cảnh cho cả lần huỷ | **Đã xác nhận** 2026-08-28 (người chơi chọn "không cần — chỉ ghi lại là đã huỷ") | Xem lại sau khoảng 20 phiên nếu người chơi hay hỏi tới |
| A-07 | Việc **mở màn replay là đủ** để trục Review ghi nhận sẽ không bị chính người chơi lợi dụng | Nếu thành thói quen mở rồi thoát để lấy điểm, trục Review mất ý nghĩa và điểm quy trình bị thổi lên | **Đã xác nhận cách tính** 2026-08-28 (người chơi chọn "mở là tính"). Việc nó có bị lợi dụng thì chưa kiểm được, và cơ chế hiện tại chỉ **đo** chứ không **ngăn** | Theo dõi qua USC-002; nếu thời lượng xem trung vị tụt về gần 0 thì đặt lại câu hỏi cùng `process-score` |
| A-08 | **Feature này tạo ra bản ghi "lệnh nào đã được xem lại, lúc nào"**; `process-score` và `daily-journal` chỉ đọc | `process-score` chỉ lưu ở mức phiên ("có ít nhất một lần mở replay"), không đủ cho USC-001 (đếm theo lệnh) và USC-002 (cần mốc thời gian). Không ai nhận việc ghi thì cả ba USC không đo được | 🔶 Quyết định thay user 2026-08-28 — nguồn không nói ai ghi bản ghi này; feature này là nơi duy nhất biết lúc nào một lệnh được mở ra xem | Xác nhận khi viết SRS, cùng lúc với `process-score` |
| A-09 | Cửa sổ **5 phút trước lúc mở và 5 phút sau lúc đóng** là đủ cho việc ôn tập | Ngắn quá thì không thấy bối cảnh dẫn tới setup; dài quá thì tốn chỗ mà không ai xem tới | Chưa xác nhận — con số lấy từ `phase-10`, là lựa chọn kỹ thuật chưa được người chơi chốt | Hỏi người chơi khi viết SRS |

## 9. User Success Criteria

| ID | User Outcome | Baseline | Target | Measurement | Review Period |
|---|---|---|---|---|---|
| USC-001 | Việc xem lại trở thành thói quen thật, không phải tính năng dùng một lần rồi quên | **Chưa có** — xác lập tỷ lệ trung bình từ 10 phiên đầu, và ghi nhận rằng giai đoạn này là lúc mới lạ nên tỷ lệ tự nhiên cao | Tỷ lệ lệnh được mở xem lại ít nhất một lần **không giảm dần theo tháng**, và sau 3 tháng vẫn ở mức người chơi thấy đáng giữ. **Chưa có sàn tối thiểu tuyệt đối** — xem OQ-5 | Đếm số lệnh đã được mở xem lại trên tổng số lệnh đã đóng, đọc cuối mỗi tháng **theo đường xu hướng nhiều tháng**, không so đúng một mốc | Hằng quý |
| USC-002 | Xem lại diễn ra khi bối cảnh còn nóng, không phải khi đã quên hết | **Chưa có** — xác lập khoảng cách trung vị từ 10 phiên đầu | Khoảng cách từ lúc lệnh đóng tới lần xem lại đầu tiên giảm so với baseline sau 3 tháng | Đọc trung vị khoảng cách thời gian đó cuối mỗi tháng. Đi kèm **thời lượng xem trung vị** để việc mở rồi thoát ngay không tự động thành "tiến bộ" (xem A-07) | Hằng quý |
| USC-003 | Xem lại dẫn tới điều rút ra được nói thành lời, không chỉ nhìn cho biết | **Chưa có** — xác lập từ 10 phiên đầu, chấp nhận rất có thể bằng 0 | Số lệnh có ít nhất một memo ghi lúc xem lại tăng so với baseline sau 3 tháng | Đếm số lệnh có memo thuộc loại "ghi lúc xem lại", đọc cuối mỗi tháng | Hằng quý |

> **Cả ba thước đo có một sàn cứng không tránh được:** một lệnh chỉ tua lại được sau khi phần sau lúc
> đóng thu xong (khoảng 5 phút). USC-002 không bao giờ xuống dưới mốc đó, và đó là giới hạn của thiết
> kế chứ không phải của thói quen người chơi.
>
> **Cả ba đọc từ bản ghi do feature này tạo ra** (xem A-08) nhưng **được tổng hợp thành xu hướng ở
> `daily-journal` và `process-score`** — feature này không tự đọc được dữ liệu của mình thành xu hướng.
>
> **Giới hạn đã biết.** Ba thước đo này đo **việc xem lại có diễn ra hay không**, không đo **việc xem
> lại có làm người chơi giao dịch tốt hơn hay không**. Điều thứ hai chỉ đọc được qua điểm quy trình
> của `process-score`, và ngay cả ở đó cũng khó tách phần đóng góp của riêng replay khỏi các feature
> khác. Đây là giới hạn chấp nhận được của một công cụ cá nhân một người dùng.

## 10. Open Questions

* [x] OQ-1: Nút nào để ghi âm memo trong màn xem lại, khi `phase-10` gán cặp nút vai cho chuyển lệnh trước/sau còn `phase-08` gán chính cặp đó cho ghi âm? — **Resolved:** giữ nguyên cặp nút giữ để ghi âm như mọi nơi khác trong sản phẩm (cơ bắp không phải học lại); việc chuyển lệnh trước/sau dời sang cặp nút khác, chốt cụ thể khi thiết kế màn hình.
* [x] OQ-2: Bấm thoát khẩn cấp trong lúc đang xem lại thì chuyện gì xảy ra? — **Resolved:** đóng vị thế **và thoát luôn khỏi màn xem lại** về màn chính, để người chơi tự mắt xác nhận mọi thứ đã phẳng.
* [x] OQ-3: Mở replay khi đang có vị thế mở thì được nhắc thế nào? — **Resolved:** một dòng thông báo nói rõ đang khoá gì, vào thẳng, không thêm bước xác nhận.
* [ ] OQ-4: Có cần xem lại **cả buổi tối như một dòng liên tục** không, hay từng lệnh là đủ? Nếu cần thì cách lưu bối cảnh phải đổi. Xem A-04.
* [ ] OQ-5: Tỷ lệ lệnh được xem lại có **sàn tối thiểu tuyệt đối** không (vd "ít nhất 3 trên 10 lệnh"), hay chỉ cần không giảm dần? Không có sàn thì USC-001 vẫn đạt kể cả khi tỷ lệ tuyệt đối rất thấp — và khi đó không đọc được feature có đáng công sức bỏ ra hay không.
* [ ] OQ-6: Bối cảnh đã lưu **giữ bao lâu** trước khi lệnh rơi về bản rút gọn? Nguồn đề xuất khoảng 2 năm, dài hơn hạn giữ bản ghi âm (khoảng 1 năm) — nghĩa là sẽ có giai đoạn tua được hình mà không còn tiếng. Cả hai con số đều là lựa chọn kỹ thuật chưa được người chơi chốt.
* [ ] OQ-7: Lần tự huỷ nằm ngoài cửa sổ của mọi lệnh hiện ra ở đâu để người chơi "vẫn được ghi nhận là đã xảy ra"? Bề mặt đó thuộc `daily-journal` hay thuộc feature này?
* [ ] OQ-8: Việc mở thẳng màn xem lại **từ thông báo lệnh vừa đóng** — nội dung thông báo thuộc `order-execution`, đường dẫn sang thuộc feature này. Cần `order-execution` nhận phần dẫn đường đó, hoặc thống nhất một cách khác. Đây là đường vào nóng nhất, đúng đường USC-002 đặt cược.
* [ ] OQ-9: Cần cascade sang `docs/voice-journal/voice-journal-urd.md` UN-004 để nhận ngoại lệ "đang ở màn xem lại thì memo gắn vào lệnh đang xem". Chưa làm — xem A-05.
* [ ] OQ-10: Nhãn memo trên dải thời gian hiện **bản máy chép** hay **bản người chơi đã sửa** (`voice-journal` cho sửa bản chép)?

---

> **Lịch sử review:** chốt OQ-1, OQ-2, OQ-3 ngày 2026-08-28 (`/urd` Phase E). Review bởi
> `@senior-ba` (4 blocking, 14 warning, 7 suggestion) và `@po-reviewer` (1 blocking, 4 warning,
> 2 suggestion) cùng ngày; findings đã áp vào Mục 3, 4, 5, 6, 7, 8, 9, 10 và sinh thêm UN-014,
> A-08, A-09, OQ-8, OQ-9, OQ-10.
