---
type: urd
feature: process-score
status: draft
updated: 2026-08-28
links: ["[[docs/_shared/project-profile.md]]", "[[docs/_shared/system-overview.md]]", "[[docs/_shared/definitions.md]]", "[[docs/_shared/operating-environment.md]]", "[[docs/playbook-grading/playbook-grading-urd.md]]", "[[docs/ai-desk/ai-desk-urd.md]]", "[[docs/order-execution/order-execution-urd.md]]", "[[docs/daily-journal/daily-journal-urd.md]]", "[[docs/trade-replay/trade-replay-urd.md]]", "[[docs/voice-journal/voice-journal-urd.md]]", "[[docs/tilt-meter/tilt-meter-urd.md]]"]
---

# process-score — User Requirements Document

## 1. Purpose

Ghi lại nhu cầu của người chơi quanh **một con số duy nhất cho buổi tối, dựng trên chất lượng
quyết định thay vì trên tiền** — và quanh bề mặt nhìn lại nơi con số đó sống: deck.

Điểm mấu chốt của feature này không phải "chấm điểm cho vui" mà là một tính chất rất cụ thể:
**với cùng mức chuẩn bị và nhìn lại, một tối đứng ngoài đúng lúc không bao giờ chấm thấp hơn một tối giao dịch tốt.** Mọi thứ khác — năm
trục, biểu đồ radar, bảng theo playbook, tab kết quả tiền bạc nằm sau một cú bấm có chủ ý — đều tồn
tại để bảo vệ tính chất đó khỏi bị bào mòn.

Feature này **không sinh ra dữ liệu nào của riêng nó**. Nó đọc bằng chứng do **bảy** feature khác
tạo ra (điểm playbook, chất lượng cơ hội, hạn mức rủi ro, memo, replay, chuẩn bị trước phiên, và
trạng thái tâm lý) rồi gộp phần lớn chúng thành một câu trả lời cho câu hỏi mà không nơi nào khác
trả lời được: **"tôi có đang khá lên không."** Riêng trạng thái tâm lý chỉ được đọc **để kể lại buổi
tối** — nó không đi vào phép gộp.

### User Problem & Current Experience

| User | Current Situation | Problem | User Consequence | Evidence |
|---|---|---|---|---|
| Người chơi | Kết thúc mỗi tối, con số duy nhất nói về buổi tối đó là lãi lỗ | Tiền phần lớn do thị trường quyết, không do chất lượng quyết định quyết | Tối chơi ẩu mà lãi vẫn đọc là "thắng"; tối kỷ luật mà tape chết vẫn đọc là "thua" — học sai bài mỗi tối | Observed: `phase-11` ("win rate and profit factor are outcome, and chasing them is exactly the outcome anxiety this plan exists to treat") |
| Người chơi | Tối thị trường không cho cơ hội nào, đứng ngoài cả buổi | Sổ trống trông y hệt một buổi bỏ bê — không có gì ghi nhận việc đứng ngoài là một quyết định | Sinh áp lực phải giao dịch để "có gì đó trong sổ" — chính là cơ chế đẻ ra lệnh rác | Observed: `phase-06` ("markets do not offer equal opportunity every night; a flat evening in a dead tape is a good evening, and the deck must say so") |
| Người chơi | Công cụ benchmark (TradeZella) cho một điểm tổng để đuổi theo | Cơ chế trò chơi đúng nhưng đầu vào sai — điểm dựng trên tỷ lệ thắng và profit factor | Đuổi theo con số hoá ra vẫn là đuổi theo kết quả, đúng thứ cần chữa | Observed: `phase-11` ("the same number to chase ... the right game mechanic and the wrong inputs") |
| Người chơi | Bằng chứng về chất lượng quyết định nằm rải rác sáu nơi: điểm playbook ở từng lệnh, bộ đếm tự huỷ trên màn chính, tilt trong phiên, memo, replay, check-in | Không nơi nào gộp chúng lại; mỗi mảnh chỉ nói về một khoảnh khắc | Không trả lời được câu hỏi duy nhất đáng hỏi — "tháng này tôi có khá hơn tháng trước không" | Suy từ `phase-11` (phụ thuộc phase 4, 6, 7, 8, 9, 10) |
| Người chơi | Các công cụ chấm điểm thường kèm chuỗi ngày, cấp độ, huy hiệu | Mọi cơ chế cộng dồn xuyên phiên đều tạo áp lực không được bỏ một tối nào | Sẽ giao dịch trong một tape chết chỉ để không đứt chuỗi — đúng hành vi feature này sinh ra để chặn | Observed: `README.md` ("No streaks, no levels, no badges, no leaderboards, and nothing that accumulates across sessions") |

## 2. User Types

| Tier | User Type | Context | Primary Goal | Pain Points |
|---|---|---|---|---|
| primary | **Người chơi** | Sau khi đóng phiên, rời tay cầm, ngồi trước màn hình với chuột và bàn phím — hoặc cuối tháng khi muốn nhìn lại một quãng dài | Biết mình có đang ra quyết định tốt hơn không, bằng một thước đo mà thị trường không quyết hộ | Chỉ có tiền làm thước đo; tối đứng ngoài trông như thất bại; bằng chứng rải rác không gộp được thành xu hướng |

> **Không có secondary user.** Công cụ cá nhân một người dùng.
> **AI desk là actor hệ thống, không phải người dùng** — copilot đọc được các trục để huấn luyện
> **đọc được** các trục để huấn luyện, nhưng **không tính bất kỳ con số nào hiện trên deck** và không đặt được lệnh.
> Sàn cTrader/Spotware là nguồn sự thật cho tiền. Xem `docs/_shared/project-profile.md`.

## 3. Scope Boundaries

### In Scope

* Người chơi nhận **một điểm quy trình cho mỗi buổi tối**, dựng trên năm trục chỉ-về-quy-trình: tuân thủ playbook, tính chọn lọc, kỷ luật rủi ro, chuẩn bị, nhìn lại. Trọng số cộng lại đúng 1.00.
* **Với cùng mức chuẩn bị và nhìn lại, tối đứng ngoài đúng lúc không bao giờ chấm thấp hơn tối giao dịch tốt.** Bộ số minh hoạ: tape chết không lệnh nào, chuẩn bị và nhìn lại đầy đủ, chấm **100**; tối giao dịch tốt với một luật playbook hụt và một lần bắn thiếu mức cắt lỗ chấm **98**. Đây là tính chất phải giữ, không phải hệ quả tình cờ — nhưng nó là bất đẳng thức **giữa hai buổi cùng mức chuẩn bị và nhìn lại**, không phải lời hứa rằng mọi tối đứng ngoài đều chấm 100.
* **Trục không có bằng chứng thì rơi khỏi công thức**, phần trọng số còn lại được chia lại. Không lệnh nào thì trục tuân thủ và kỷ luật rủi ro không có mẫu số — chúng hiện thành **vòng gạch đứt "không áp dụng"** trên radar, không phải nan quạt bằng 0.
* Điểm được **chốt ngay khi đóng phiên**, không chờ lệnh giữ qua đêm ngã ngũ — bốn trục (tuân thủ, chọn lọc, kỷ luật rủi ro, chuẩn bị) đã có đủ bằng chứng tại **thời điểm bắn**, còn trục **nhìn lại** chốt tại thời điểm đóng phiên với bộ tiểu mục có mặt lúc đó. Không có điểm sống để nhìn giữa phiên, và điểm không bao giờ xuất hiện trên màn hình chính lúc đang giao dịch.
* Người chơi **tự mở deck khi muốn xem** — không có bảng điểm tự bật ra lúc đóng phiên.
* Mở deck **giữa lúc phiên còn chạy không bị chặn**, nhưng mỗi lần mở như vậy **được ghi lại** — đó chính là số liệu USC-001 cần để canh chừng rủi ro lớn nhất của feature. Vì deck mở từ menu an toàn, việc mở nó **huỷ trạng thái vũ trang và khoá mở lệnh mới** cho tới khi đóng deck (luật của `order-execution`), và màn hình nói rõ điều đó ngay lúc mở.
* **Biểu đồ radar năm trục** để biết tối nay yếu ở đâu, chứ không chỉ biết một con số.
* **Panel quy trình là màn mặc định** khi mở deck: xu hướng tuân thủ, số lần từ chối, chất lượng cơ hội của buổi tối, điểm tự chấm đầu/cuối buổi đối chiếu với tuân thủ, và chênh lệch tháng này so tháng trước.
* **Tab kết quả tiền bạc nằm sau một cú bấm có chủ ý**: lãi theo %, Sharpe kèm cỡ mẫu, profit factor, R trung bình, tỷ lệ thắng, sụt vốn tối đa, bảng theo kiểu setup. **Không đồng nào nhìn thấy được trước cú bấm đó.**
* **Bảng thống kê theo playbook**: số lệnh, mức tuân thủ, kỳ vọng theo R, MFE/MAE trung bình, hiệu suất trung bình — con số quy trình để mặc định, con số kết quả nằm sau cùng cú bấm trên.
* **Tilt hiện như một hồi tưởng của buổi tối** — các dải trạng thái, nguyên nhân chính, đối chiếu với mức tuân thủ chứ không với lãi lỗ. **Tilt không bao giờ là đầu vào của điểm.**
* **Phân bố điểm theo tháng kèm số phiên** — không bao giờ là chuỗi ngày, không bao giờ là "đã bao nhiêu ngày kể từ".
* Mọi con số trên deck **truy ngược được về đầu vào của nó**; đổi trọng số thì lịch sử được tính lại từ chính các đầu vào đã lưu.
* Mẫu ít thì **nói thẳng là mẫu ít** thay vì in một con số tự tin.
* Copilot **huấn luyện được một trục có tên cụ thể** và vẫn không có công cụ ghi hay đặt lệnh nào.
* Deck **mở bằng tay cầm** từ menu an toàn; **đọc, lọc và đổi tab bằng chuột và bàn phím**.
* **Định nghĩa "điều kiện đứng ngoài" dùng để quy điểm thuộc feature này** — đó là danh sách đóng các hoàn cảnh làm một lần tự huỷ được tính là huỷ đúng lúc. Các feature khác chỉ **báo trạng thái của mình** (sắp có tin, chênh lệch giá vượt trần, ngoài khung giờ, không playbook nào đủ luật); việc gộp chúng thành một cờ là việc của feature này. Danh sách cụ thể: xem OQ-10.
* Mọi panel giữ nguyên dòng chữ demo / giải trí / không phải lời khuyên.

> **Năm trục dựng trên bằng chứng của feature nào** — bảng này là căn cứ để đọc luật "tiểu mục thiếu bằng chứng thì rơi ra" ở Mục 6, và để đánh giá A-06.
>
> | Trục | Bằng chứng | Feature cấp bằng chứng |
> |---|---|---|
> | Tuân thủ | Kết quả chấm luật playbook mỗi lần bắn | `playbook-grading` |
> | Chọn lọc | Chất lượng cơ hội của phiên · số lệnh · số lần huỷ đúng lúc | `ai-desk` · `order-execution` |
> | Kỷ luật rủi ro | Kết quả kiểm hạn mức tại mỗi lần bắn | `order-execution` |
> | Chuẩn bị | Kế hoạch đã xác nhận trước lệnh đầu · tự chấm đầu buổi · có chọn playbook · có memo | `daily-journal` · `playbook-grading` · `voice-journal` |
> | Nhìn lại | Tự chấm cuối buổi · memo · đã mở replay · checklist đã trả lời | `daily-journal` · `voice-journal` · `trade-replay` · `playbook-grading` |
* **Mọi số liệu so sánh nhiều phiên** — tháng này so tháng trước, phân bố điểm, bảng theo playbook, số lần từ chối đọc theo tháng, và các chỉ số kết quả — thuộc feature này. *(Chốt 2026-08-28 — ba nguồn đặt ba chỗ khác nhau: `phase-06` ở deck hiệu năng, `phase-11` ở radar, `phase-12` ở bảng tổng của nhật ký. `daily-journal` chỉ **đọc** điểm đã chốt để tô bản đồ nhiệt, không tự tính lại.)*

### Out of Scope

* **Chấm điểm từng lệnh theo luật playbook** thuộc feature `playbook-grading`. URD này chỉ **tiêu thụ** kết quả đó làm trục tuân thủ; nó không định nghĩa luật, không chấm, không sửa điểm của một lệnh.
* **Bàn làm việc AI, giọng huấn luyện và mọi khả năng hỏi-đáp của copilot** thuộc feature `ai-desk`. Feature này chỉ **cấp các trục** cho copilot đọc; ràng buộc "không ghi, không đặt lệnh" là ràng buộc kế thừa từ `ai-desk`.
* **Đo trạng thái tâm lý và ma sát thích ứng** thuộc feature `tilt-meter`. URD này chỉ nhận phần **hiển thị hồi tưởng**, và nhận ràng buộc "tilt không được là đầu vào điểm".
* **Sinh ra chỉ số chất lượng cơ hội** thuộc feature `ai-desk`. URD này chỉ **đọc** con số đó để tính trục chọn lọc.
* **Hạn mức rủi ro và việc thi hành chúng** → feature `order-execution`. Trục kỷ luật rủi ro chấm lại **đúng bộ luật mà gateway đã thi hành**, không dựng một định nghĩa thứ hai.
* **Bộ đếm tự huỷ theo phiên trên màn hình chính** → feature `order-execution`, và nó đếm **mọi** lần tự huỷ chủ động. URD này chỉ nhận phần **quy ra điểm**, và chỉ quy trên **tập con** những lần huỷ xảy ra lúc đang có điều kiện đứng ngoài. *(Chốt 2026-08-28 — một bộ đếm gốc, hai cách đọc; không có bộ đếm thứ hai.)*
* **Ghi âm và chuyển lời nói thành văn bản** thuộc feature `voice-journal`. Ở đây memo chỉ là **bằng chứng** của trục nhìn lại.
* **Tua lại lệnh qua tape** thuộc feature `trade-replay`, và feature đó ghi chi tiết **từng lần mở, từng lệnh**. Ở đây "đã mở replay" chỉ là **bằng chứng ở mức phiên** (có ít nhất một lần mở). Hai mức lưu khác nhau nhưng không mâu thuẫn. *(Chốt 2026-08-28.)*
* **Thu điểm tự chấm đầu/cuối buổi và nghi thức chuẩn bị trước phiên** thuộc feature `daily-journal`. Deck **render** những dòng đó, tuyệt đối **không mở một luồng thu thập thứ hai**.
* **Báo cáo, xuất dữ liệu, sao lưu** thuộc feature `reports-export` (`docs/reports-export/reports-export-urd.md`).
* Chia sẻ, xếp hạng hoặc so sánh điểm với bất kỳ ai — sản phẩm chỉ có một người dùng.

## 4. User Needs

| ID | User | Context / Trigger | User Need | Expected Outcome | Importance | Evidence |
|---|---|---|---|---|---|---|
| UN-001 | Người chơi | Đóng phiên xong, muốn biết tối nay ra sao | Một con số cho buổi tối dựng trên **quyết định**, không phải trên tiền | Một điểm quy trình duy nhất, tổng hợp từ năm trục chỉ-về-quy-trình. Tỷ lệ thắng, profit factor, lãi lỗ và R **không phải là trục** — không con số kết quả nào tham gia vào điểm này | Critical | Observed: `phase-11` ("win rate, profit factor, P/L and R **are not axes**. Every input is process-side") |
| UN-002 | Người chơi | Tối thị trường không cho cơ hội nào, đứng ngoài cả buổi | Được chấm **ít nhất bằng** một tối giao dịch tốt có cùng mức chuẩn bị và nhìn lại, chứ không bị chấm là buổi trống | So hai buổi **cùng mức chuẩn bị và nhìn lại**, buổi đứng ngoài không bao giờ chấm thấp hơn. Bộ số minh hoạ: tape chết không lệnh nào + chuẩn bị và nhìn lại đầy đủ chấm **100**; tối giao dịch tốt với một luật playbook hụt và một lần bắn thiếu cắt lỗ chấm **98**. Bỏ chuẩn bị thì tối đứng ngoài cũng tụt điểm — đứng ngoài không phải tấm vé miễn phí | Critical | Observed: `phase-11` ("a correctly-declined evening scores at least as well as a well-traded one"; các mốc 100 / 98 / 70 / 65) |
| UN-003 | Người chơi | Buổi tối không có lệnh nào, nên hai trục không có gì để chấm | Không bị chấm 0 vì **thiếu bằng chứng**, và cũng không được cho điểm miễn phí vì không làm gì | Trục không có mẫu số **rơi khỏi công thức**, phần trọng số còn lại chia lại. Trên radar nó hiện thành **vòng gạch đứt "không áp dụng"**, không phải nan quạt bằng 0 — nhìn một cái là biết đây là "không có dữ liệu" chứ không phải "làm tệ" | Critical | Observed: `phase-11` ("scoring them 0 punishes standing down (forbidden); scoring them 100 is free points ... drop vacuous axes and renormalise"; "dashed n/a ring, never as a zero spoke") |
| UN-004 | Người chơi | Trong lúc phiên còn đang chạy | Không có một con số sống nào để nhìn giữa phiên | Điểm chỉ được tính khi **đóng phiên**; không tồn tại điểm tạm thời, và điểm **không bao giờ xuất hiện trên màn hình chính**. Không có gì để làm mới, không có gì để canh — nếu có, chính điểm này sẽ thay chỗ lãi lỗ làm nỗi lo mới | Critical | Observed: `phase-11` (rủi ro số 1: "the score becomes the anxiety P/L used to be ... computed at session close only and lives on the deck, never on the HUD; there is no live score to watch") |
| UN-005 | Người chơi | Suốt quá trình dùng sản phẩm, tháng này qua tháng khác | Không có gì cộng dồn xuyên phiên | Không chuỗi ngày, không cấp độ, không huy hiệu, không "đã bao nhiêu ngày kể từ". Xu hướng theo tháng hiện dưới dạng **phân bố kèm số phiên**, là thứ đọc để hiểu chứ không phải thứ để giữ cho khỏi đứt | Critical | Observed: `phase-11` ("No streaks. No levels. No cross-session accumulator exists anywhere in the schema"), `README.md` (quyết định đã khoá). **Đọc lại nhiều phiên để so sánh không phải là cộng dồn** — thứ bị cấm là con số chạy dài không bao giờ đặt lại và tạo áp lực không được đứt |
| UN-006 | Người chơi | Mở deck ra sau một buổi tối | Thấy quy trình trước, và **không thấy đồng nào** cho tới khi tự bấm sang | Deck mở ra ở panel quy trình. Con số tiền chỉ hiện sau một cú bấm có chủ ý sang tab kết quả. Không thông báo nào mang theo con số tiền | Critical | Observed: `phase-06` ("Opening `/deck` lands on the **process** panel; no dollar figure is visible until a tab is clicked"; "outcome numbers never appear on the process panel, and never in a notification") |
| UN-007 | Người chơi | Vừa đọc điểm tổng và muốn biết vì sao nó như vậy | Biết tối nay **yếu ở trục nào**, không chỉ biết một con số | Biểu đồ radar năm trục cho thấy hình dạng buổi tối. Đông cứng trong một tape giàu cơ hội (**70**) đọc ra khác hẳn giao dịch quá tay trong một tape chết (**65**) — và chính tên trục nói ra sự khác nhau đó | High | Observed: `phase-11` ("radar chart of the five axes"; "Lower, and the axis names why — timidity is a smaller sin than recklessness") |
| UN-008 | Người chơi | Tự huỷ nhiều lần trong lúc đang có điều kiện đứng ngoài | Việc tự kiềm chế được cộng điểm, nhưng **không farm được** | Mỗi lần tự huỷ trong lúc đang có điều kiện đứng ngoài cộng thêm vào trục chọn lọc, nhưng phần cộng có **trần**, và trục chọn lọc không vượt quá 100. Huỷ hàng chục lần cũng không mua thêm được điểm nào. Bộ đếm trên màn hình chính vẫn đếm **mọi** lần tự huỷ — trục này chỉ quy điểm trên tập con có điều kiện đứng ngoài, nên mỗi lần huỷ phải ghi kèm lúc đó có điều kiện đứng ngoài hay không. **Tập điều kiện dùng để quy điểm KHÔNG bao gồm mức tâm lý** (chốt 2026-08-28) — nếu bao gồm, tilt sẽ đi vào điểm qua cửa sau và phá lời hứa ở UN-014. Xem A-09 | High | Observed: `phase-11` ("`declineCredit` caps at 15 so cancels cannot be farmed; Selectivity cannot exceed 100") |
| UN-009 | Người chơi | Nhìn một con số bất kỳ trên deck và tự hỏi nó ở đâu ra | Truy ngược được mọi con số về đầu vào của nó | Buổi tối lưu lại **các đầu vào của từng trục**, không chỉ lưu điểm tổng. Nhờ vậy đổi trọng số thì lịch sử được tính lại từ chính các đầu vào đó, và mọi con số trên deck đối chiếu được | High | Observed: `phase-11` ("store the axis **inputs**, not just the total, so a weight change recomputes retroactively and every number on the deck is auditable") |
| UN-010 | Người chơi | Suốt quá trình dùng deck | Điểm là kết quả tính toán xác định, không phải ý kiến của một mô hình | Cùng một dữ liệu luôn cho ra cùng một điểm. **Không mô hình ngôn ngữ nào tính một con số hiện trên deck**; copilot chỉ được kể lại những con số deck đã tính ra | High | Observed: `phase-11` ("the score is a **pure function over rows** ... No LLM computes a number that appears on the deck"), `phase-06` (cùng nguyên tắc) |
| UN-011 | Người chơi | Tháng đầu tiên dùng sản phẩm, mới có vài phiên | Được nói thẳng là **chưa đủ dữ liệu**, thay vì nhận một con số tự tin từ mẫu quá nhỏ | Các chỉ số cần mẫu lớn (Sharpe) hiện trạng thái "chưa đủ phiên" khi dưới ngưỡng, và **luôn in kèm cỡ mẫu** bên cạnh con số. Với nhịp **giả định** khoảng 20 phiên một tháng (xem `daily-journal` A-05), hai tháng Sharpe đầu là nhiễu và deck phải nói ra điều đó | High | Observed: `phase-06` ("renders a **"not enough sessions yet"** state below `deck.min_sessions_for_sharpe` (default 30) ... the first two months of Sharpe are noise and the deck must say so rather than print a confident number") |
| UN-012 | Người chơi | Cuối tháng, muốn biết cách chơi nào thực sự sinh lợi thế | So sánh được các playbook với nhau | Bảng theo playbook: số lệnh, mức tuân thủ, kỳ vọng theo R, MFE/MAE trung bình, hiệu suất trung bình. Con số quy trình hiện mặc định; con số kết quả nằm sau cùng cú bấm có chủ ý như mọi con số tiền khác | High | Observed: `phase-11` ("per-playbook stats table ... Process figures default; outcome figures stay behind phase 6's existing deliberate tab click") |
| UN-013 | Người chơi | Cuối tháng, muốn trả lời "tôi có khá lên không" | Thấy tháng này so với tháng trước, trên các số liệu quy trình | Chênh lệch tháng này so tháng trước hiện cho mức tuân thủ, tỷ lệ từ chối, điểm tự chấm trung bình — và phân bố điểm quy trình kèm số phiên. Đây là câu trả lời chính cho "tôi có đang khá lên không" | High | Observed: `phase-06` ("**this month vs last month** ... the primary "am I improving?" answer"), `phase-11` ("month-over-month ProcessScore **distribution** with n") |
| UN-014 | Người chơi | Nhìn lại một buổi tối đã trôi qua và muốn hiểu trạng thái mình lúc đó | Thấy tilt như một câu chuyện của buổi tối, **không phải như một lời phán xét** | Các dải tilt trong phiên, nguyên nhân chính, đối chiếu với **mức tuân thủ** chứ không với lãi lỗ. Tilt **không bao giờ là đầu vào của điểm** — nó giải thích, không trừng phạt | Medium | Observed: `phase-11` ("tilt is a retrospective here, never a score input"; "correlated against adherence (not against P/L)"), `phase-09` ("still not as a score input") |
| UN-015 | Người chơi | Đã tắt tính năng ghi âm, hoặc máy không có micro dùng được | Không bị trừ điểm vì một tính năng mình chủ động không dùng | Các tiểu mục dựa vào memo **rơi khỏi trục và trục được chuẩn hoá lại** khi ghi âm bị tắt hoặc không khả dụng. Nhưng nếu ghi âm sẵn sàng mà người chơi bỏ qua, đó vẫn là một thiếu sót thật và được tính là thiếu | Medium | Observed: `phase-11` ("do not punish a supported degradation mode ... If voice was available and the player skipped it, the sub-item remains a genuine miss") |
| UN-016 | Người chơi | Muốn xem deck ngay sau khi rời tay cầm | Mở deck **bằng tay cầm**, nhưng đọc nó bằng chuột | Deck là một đích trong menu an toàn, mở được bằng tay cầm mà không phải rời tay đi tìm chuột. Việc đọc bảng, lọc, đổi tab thì dùng chuột và bàn phím — đây là màn hình nhìn lại, không phải màn hình thao tác nhanh | Medium | Confirmed 2026-08-28 (người chơi chốt). Nền: `phase-06` (`/deck` trong cùng app web), `docs/_shared/definitions.md` (hợp đồng điều hướng chung của menu an toàn) |
| UN-017 | Người chơi | Đã biết mình yếu trục nào và muốn được huấn luyện đúng chỗ đó | Hỏi copilot về **một trục có tên**, và nhận lời khuyên đúng trục đó | Copilot đọc được các trục và huấn luyện được trục người chơi nêu tên. Nó vẫn **chỉ đọc**: không đặt lệnh, không đóng lệnh, không ghi được gì, và không tự tính ra con số nào | Medium | Observed: `phase-11` ("copilot `get_progress` extended with the axes so it can coach a specific axis"; "re-assert the copilot still has no write or order tool") |

## 5. Prioritized User Journeys

### Journey 1: Đóng phiên rồi mở deck xem tối nay ra sao

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Vừa đóng phiên giao dịch, rời tay cầm, muốn biết buổi tối vừa rồi ra sao
* __Expected outcome:__ Người chơi đọc được một điểm quy trình cho buổi tối và biết nó dựng từ đâu, mà không nhìn thấy một con số tiền nào
* __Related needs:__ UN-001, UN-004, UN-006, UN-007, UN-009, UN-015, UN-016

1) Phiên đóng; điểm được chốt lặng lẽ ngay lúc đó. Không có gì bật ra.
2) Người chơi mở deck từ menu an toàn bằng tay cầm khi mình muốn.
3) Deck mở ra ở panel quy trình — điểm tối nay, radar năm trục, số lần từ chối, chất lượng cơ hội của buổi tối.
4) Người chơi nhìn radar, thấy trục nào kéo điểm xuống.
5) Không có con số tiền nào trong toàn bộ màn hình này.

__Independent verification:__ Chạy một phiên rồi đóng. Mở deck: phải thấy đúng một điểm cho buổi
tối và năm trục. Rà toàn bộ panel quy trình — **không được có bất kỳ con số tiền nào**, kể cả trong
radar và các bảng. Kiểm chiều ngược: trong lúc phiên còn chạy, không nơi nào trên màn hình chính
hiện điểm, và deck không có điểm cho buổi tối đang chạy. Không cần journey nào khác để xác nhận.

### Journey 2: Tối tape chết, đứng ngoài cả buổi

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Thị trường không cho cơ hội nào cả buổi; người chơi không vào lệnh nào
* __Expected outcome:__ Buổi tối được chấm **100** — không thấp hơn một tối giao dịch tốt cùng mức chuẩn bị — và người chơi hiểu vì sao
* __Related needs:__ UN-002, UN-003, UN-008

1) Suốt buổi, chất lượng cơ hội ở mức thấp; người chơi vũ trang vài lần rồi tự huỷ.
2) Đóng phiên không lệnh nào.
3) Mở deck: điểm tối nay là **100**.
4) Radar cho thấy trục tuân thủ và kỷ luật rủi ro là **vòng gạch đứt "không áp dụng"** — không phải nan quạt bằng 0.
5) Trục chọn lọc đạt tối đa: số lệnh nằm đúng trong dải kỳ vọng của một tape chết, cộng thêm phần thưởng cho các lần tự huỷ.

__Independent verification:__ Dựng hai buổi tối **cùng mức chuẩn bị và nhìn lại (đều đầy đủ)** —
buổi A tape chết không lệnh nào, buổi B tape bình thường với đúng một luật playbook hụt và một lần
bắn thiếu mức cắt lỗ. A phải chấm **100**, B phải chấm **98**. Kiểm rộng: với **mọi** cặp buổi cùng
mức chuẩn bị và nhìn lại, buổi đứng ngoài không bao giờ chấm thấp hơn. Đây là journey phải hoạt động
kể cả khi mọi thứ khác của feature hỏng.

### Journey 3: Muốn xem tiền — phải tự bấm sang

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Người chơi muốn biết tháng này lãi lỗ ra sao
* __Expected outcome:__ Xem được đầy đủ số liệu kết quả, nhưng chỉ sau một hành động có chủ ý của chính mình
* __Related needs:__ UN-006, UN-011

1) Deck đang mở ở panel quy trình.
2) Người chơi bấm sang tab kết quả — một thao tác có chủ ý, không phải mặc định.
3) Thấy lãi theo %, profit factor, R trung bình, tỷ lệ thắng, sụt vốn tối đa, bảng theo kiểu setup.
4) Sharpe hiện kèm cỡ mẫu; chưa đủ phiên thì nói "chưa đủ phiên" thay vì in một con số.
5) Quay lại panel quy trình, các con số tiền biến mất hoàn toàn.

__Independent verification:__ Mở deck và **không bấm gì** — rà toàn màn hình, không được có con số
tiền nào. Bấm sang tab kết quả — phải thấy chúng. Kiểm mẫu nhỏ: dựng một tháng chỉ có 2 phiên,
Sharpe phải đọc là "chưa đủ phiên", **không** được ra một con số.

### Journey 4: Nhìn radar tìm trục yếu rồi hỏi copilot đúng trục đó

* __User:__ Người chơi · __Importance:__ Medium
* __Trigger:__ Điểm tối nay thấp hơn thường lệ và người chơi muốn biết nên sửa gì
* __Expected outcome:__ Người chơi biết trục nào yếu và nhận được lời khuyên đúng trục đó
* __Related needs:__ UN-007, UN-017, UN-010

1) Người chơi nhìn radar, thấy một trục lõm rõ so với các trục khác.
2) Hỏi copilot về đúng trục đó bằng tên của nó.
3) Copilot trả lời dựa trên chính các trục deck đã tính, không tự bịa ra con số mới.
4) Người chơi biết cụ thể phải làm gì khác đi ở buổi sau.

__Independent verification:__ Dựng một buổi tối có đúng một trục thấp rõ rệt; hỏi copilot về trục
đó — câu trả lời phải nêu đúng con số radar đang hiện. Kiểm chiều ngược: yêu cầu copilot đặt lệnh
hoặc sửa một điểm — **phải không làm được**, vì nó không có công cụ nào để ghi.

### Journey 5: Cuối tháng nhìn lại — tháng này so tháng trước

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Hết một tháng, muốn biết mình có khá lên không
* __Expected outcome:__ Có câu trả lời dựa trên số liệu quy trình, kèm số phiên để biết mẫu đủ hay chưa
* __Related needs:__ UN-013, UN-005, UN-011

1) Người chơi mở deck và xem phần so sánh theo tháng.
2) Thấy chênh lệch tháng này so tháng trước trên mức tuân thủ, tỷ lệ từ chối, điểm tự chấm trung bình.
3) Thấy phân bố điểm quy trình của tháng, **kèm số phiên**.
4) Không thấy bất kỳ chuỗi ngày, cấp độ hay con số cộng dồn nào.

__Independent verification:__ Dựng hai tháng dữ liệu; phần so sánh phải hiện chênh lệch cho cả ba
số liệu quy trình và phân bố điểm kèm số phiên. Kiểm chiều ngược: rà toàn deck tìm bất kỳ thứ gì
cộng dồn xuyên phiên — chuỗi ngày, cấp độ, "đã bao nhiêu ngày kể từ" — **phải không tồn tại ở đâu cả**.

### Journey 6: Đổi trọng số rồi lịch sử tính lại

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Sau vài tháng, người chơi thấy một trục đang được cân quá nặng hoặc quá nhẹ so với thực tế của mình
* __Expected outcome:__ Trọng số mới áp cho cả lịch sử, nên các tháng vẫn so sánh được với nhau
* __Related needs:__ UN-009, UN-013

1) Người chơi đổi trọng số của các trục.
2) Bộ trọng số mới phải cộng lại đúng 1.00; không đúng thì hệ thống **không chạy** và nói rõ vì sao.
3) Điểm của các buổi tối cũ được tính lại từ chính các đầu vào đã lưu.
4) Xu hướng theo tháng vẫn đọc được, vì mọi tháng đang được chấm bằng cùng một thước.

__Independent verification:__ Ghi lại điểm của một buổi tối cũ; đổi trọng số; mở lại đúng buổi tối
đó — điểm phải đổi theo đúng công thức mới, tính từ các đầu vào cũ không đổi. Kiểm chiều ngược: đặt
bộ trọng số cộng lại không bằng 1.00 — hệ thống phải từ chối chạy, không được âm thầm tự chuẩn hoá.

### Journey 7: So sánh xem playbook nào thực sự chạy

* __User:__ Người chơi · __Importance:__ Medium
* __Trigger:__ Có vài playbook đang dùng song song và muốn biết cái nào đáng giữ
* __Expected outcome:__ So sánh được các playbook với nhau, quy trình trước, kết quả sau
* __Related needs:__ UN-012, UN-006

1) Người chơi mở bảng theo playbook trên panel quy trình.
2) Thấy với mỗi playbook: số lệnh, mức tuân thủ — các con số quy trình.
3) Muốn xem kỳ vọng theo R và các con số kết quả thì bấm sang tab kết quả như mọi con số tiền khác.
4) Playbook đã ngừng dùng vẫn tra ra được với lịch sử của nó.

__Independent verification:__ Dựng dữ liệu cho hai playbook; bảng phải hiện đúng số lệnh và mức
tuân thủ của từng cái ở panel quy trình, và **không** hiện kỳ vọng theo R ở đó. Ngừng dùng một
playbook rồi mở lại bảng — lịch sử của nó vẫn còn.

### Journey 8: Xem lại trạng thái tâm lý của một buổi tối

* __User:__ Người chơi · __Importance:__ Medium
* __Trigger:__ Một buổi tối có cảm giác lệch nhịp và người chơi muốn hiểu chuyện gì đã xảy ra
* __Expected outcome:__ Thấy tilt diễn biến ra sao trong buổi tối đó và nó đi cùng mức tuân thủ thế nào
* __Related needs:__ UN-014, UN-007

1) Người chơi mở phần hồi tưởng tilt của một buổi tối.
2) Thấy các dải trạng thái theo thời gian trong phiên và các nguyên nhân chính.
3) Thấy tilt được đặt cạnh **mức tuân thủ**, không đặt cạnh lãi lỗ.
4) Nhận ra mối liên hệ giữa trạng thái mình và chất lượng tuân thủ.

__Independent verification:__ Mở một buổi tối có tilt cao; phần hồi tưởng phải hiện các dải trạng
thái và đối chiếu với mức tuân thủ. Kiểm chiều ngược quan trọng nhất: **ép chỉ số tâm lý lên mức quá nóng**
(không chờ nó tự lên) trong khi giữ nguyên mọi hành vi đặt lệnh của buổi tối — điểm quy trình phải
không đổi so với lần chạy cùng hành vi mà tâm lý ở mức bình thường. Đây là cách duy nhất dựng được
phép so sánh, vì đầu vào của tilt chồng lấn chính đầu vào của trục tuân thủ và kỷ luật rủi ro.

## 6. User Exceptions & Edge Conditions

| Situation | User Impact | Expected User-facing Outcome | Related Journey / Need |
|---|---|---|---|
| **Không lệnh nào cả buổi** | Hai trục không có mẫu số; chấm 0 thì phạt việc đứng ngoài, chấm 100 thì cho điểm miễn phí | Hai trục đó **rơi khỏi công thức**, trọng số còn lại chia lại; radar hiện vòng gạch đứt "không áp dụng". Trục nhìn lại đổi sang bộ tiểu mục không phụ thuộc lệnh (tự chấm cuối buổi, có memo, có mở lại một lệnh cũ) | J2 / UN-002, UN-003 |
| **Đông cứng trong một tape giàu cơ hội** (cơ hội tốt nhưng không vào lệnh nào) | Nếu chỉ nhìn "không lệnh nào" thì trông giống hệt tối đứng ngoài đúng lúc | Với cùng mức chuẩn bị và nhìn lại đầy đủ, chấm **70** — thấp hơn rõ rệt so với 100 của tape chết, và trục chọn lọc là nơi nói ra điều đó. Sự rụt rè là lỗi nhẹ hơn sự liều lĩnh, và điểm phải phản ánh đúng thứ tự đó | J2, J4 / UN-002, UN-007 |
| **Giao dịch quá tay trong một tape chết** | Nhiều lệnh trong buổi tối không đáng giao dịch | Với bộ bằng chứng của nguồn (tuân thủ 80, kỷ luật rủi ro 70, nhìn lại 60), chấm **65** — đúng mức tầm thường. Trục chọn lọc bị kéo xuống vì số lệnh nằm xa dải kỳ vọng | J2, J4 / UN-002, UN-007 |
| **Mở deck giữa lúc phiên còn chạy** | Nguy cơ đúng thứ feature này sinh ra để tránh — một con số để canh giữa phiên | **Không có điểm cho buổi tối đang chạy** — xem được phần lịch sử và xu hướng, nhưng buổi hôm nay chưa tồn tại cho tới khi đóng phiên. **Không bị chặn**, vì chặn thì phải đẻ thêm một trạng thái khoá và người chơi có lý do chính đáng để mở giữa phiên. Đổi lại, mỗi lần mở như vậy được ghi lại làm số liệu cho USC-001 | J1 / UN-004 |
| **Chỉ có đúng một lệnh, và lệnh đó rất tệ** | Lo rằng việc chia lại trọng số làm một buổi tối tệ trông đẹp | Chia lại trọng số **chỉ xảy ra khi không có lệnh nào**. Một lệnh đã đủ cho trục tuân thủ và kỷ luật rủi ro có mẫu số thật, nên buổi tối đó bị chấm đúng như nó tệ | J1 / UN-003 |
| **Huỷ hàng chục lần trong một buổi** | Có thể farm điểm bằng cách vũ trang rồi huỷ liên tục | Phần cộng cho việc tự huỷ có **trần**, và trục chọn lọc không vượt quá 100. Chỉ những lần huỷ trong lúc **đang có điều kiện đứng ngoài** mới được tính | J2 / UN-008 |
| **AI desk im lặng cả buổi, không có chỉ số chất lượng cơ hội** | Trục chọn lọc — trục làm nên toàn bộ tính chất "đứng ngoài chấm tốt" — mất đầu vào | Còn nhãn mức của phiên thì chuyển sang cách đọc thô ba mức (chết / bình thường / giàu cơ hội) và **nói rõ đang dùng cách đọc thô** — công thức không đổi, chỉ độ phân giải giảm. Không còn gì cả thì trục chọn lọc **rơi khỏi công thức** như mọi trục thiếu bằng chứng, và deck nói rõ điểm đang thiếu trục chọn lọc | J2 / UN-002, UN-010 |
| **Chỉ số chất lượng cơ hội không quy về thang 0–1 một cách có cơ sở** | Trục chọn lọc dựng trên một con số tuỳ tiện | Dùng ba mức thô như trên và ghi rõ trong cấu hình, thay vì bịa hằng số để có một con số trông đẹp | J2 / UN-002, UN-010 |
| **Tắt ghi âm, hoặc máy không có micro dùng được** | Bị trừ điểm vì một tính năng mình chủ động không dùng | Các tiểu mục dựa vào memo rơi khỏi trục và trục được chuẩn hoá lại. Nhưng ghi âm sẵn sàng mà bỏ qua thì vẫn tính là thiếu | J1 / UN-015 |
| **Phiên đầu tiên, chưa có lệnh cũ nào để tua lại** | Tiểu mục "đã mở replay" thành một yêu cầu không thể đạt | Tiểu mục đó rơi ra và trục được chuẩn hoá lại — buổi đầu tiên không bị bắt làm một việc bất khả thi | J1 / UN-003, UN-015 |
| **Bộ trọng số cấu hình không cộng lại bằng 1.00** | Mọi điểm sẽ sai mà không ai biết | Hệ thống **không chạy** và nói rõ vì sao. Không âm thầm tự chuẩn hoá, vì như vậy người chơi sẽ tin vào một thước đo khác với thứ mình nghĩ mình đã đặt | J6 / UN-009 |
| **Đổi trọng số giữa chừng** | Các tháng chấm bằng hai thước khác nhau, so sánh vô nghĩa | Điểm cũ được tính lại từ các đầu vào đã lưu, nên mọi tháng luôn đang được chấm bằng cùng một thước | J5, J6 / UN-009, UN-013 |
| **Tháng chưa đủ số phiên cho các chỉ số cần mẫu lớn** | Một con số tự tin dựng trên mẫu quá nhỏ | Hiện trạng thái "chưa đủ phiên" thay vì con số, và luôn in kèm cỡ mẫu bên cạnh mọi con số loại này | J3, J5 / UN-011 |
| **Bỏ qua điểm tự chấm đầu/cuối buổi nhiều phiên liền** | Một phần xu hướng mất dữ liệu | Deck lùi về hiển thị phần tuân thủ và **không nhắc nhở** — việc tự chấm vốn là tuỳ chọn, hai lần bấm, bỏ được | J5 / UN-013 |
| **Còn lệnh mở lúc đóng phiên** | Không rõ điểm chốt lúc nào, hoặc chốt bằng dữ liệu chưa đủ | Điểm vẫn **chốt ngay khi đóng phiên**: bốn trục quy trình chấm tại thời điểm bắn nên đã có đủ bằng chứng. Chỉ các con số **kết quả** ở tab tiền mới chờ lệnh ngã ngũ và cập nhật sau — việc đó **không đụng tới điểm**, nên xu hướng theo tháng không thủng lỗ | J1 / UN-004, UN-009 |
| **Phiên kết thúc bất thường** (mất điện, đóng trình duyệt, mất kết nối) | Buổi tối có thể không bao giờ được chấm, tạo lỗ hổng trong xu hướng | Buổi tối vẫn được chốt điểm từ những gì đã ghi được, và **nói rõ phiên kết thúc bất thường** để người chơi không đọc nhầm một buổi ngắn thành một buổi kém | J1, J5 / UN-009, UN-013 |
| **Một luật playbook không kiểm được** (thiếu dữ liệu lúc chấm) | Trục tuân thủ có thể bị lệch mà người chơi không biết | Luật đó không nằm trong mẫu số của trục tuân thủ — đúng như `playbook-grading` đã định nghĩa. Deck **không** dựng một định nghĩa tuân thủ thứ hai | J1 / UN-010 |
| **Tilt không có dữ liệu** (mất tay cầm giữa phiên, hoặc chưa có tính năng đo tilt) | Phần hồi tưởng trống, dễ đọc nhầm là "không tilt" | Phần hồi tưởng nói rõ **không có dữ liệu**, không hiện một dải phẳng trông như trạng thái tốt. Điểm quy trình không đổi, vì tilt vốn không phải đầu vào | J8 / UN-014 |
| **Các feature nguồn chưa có** (chưa có playbook, chưa có memo, chưa có replay, chưa có bản chụp kế hoạch) | Phần lớn trục không có bằng chứng, điểm dựng trên một hai trục | Áp đúng luật đã có, không cần luật riêng: **tiểu mục thiếu bằng chứng rơi ra và trục chuẩn hoá lại; rơi hết tiểu mục thì cả trục rơi** thành "không áp dụng" — giống hệt cách xử lý khi tắt ghi âm. Deck nói rõ **điểm đang dựa trên mấy trục** để người chơi không đọc nhầm một con số mỏng thành một đánh giá đầy đủ. Xem A-06 | J1 / UN-003, UN-009, UN-015 |
| **Cùng một số liệu tháng xuất hiện ở hai nơi** (deck và bảng tổng của nhật ký) | Hai con số lệch nhau thì người chơi không biết tin cái nào | Chỉ deck tính; nhật ký đọc lại **đúng con số đó**. Không có định nghĩa thứ hai ở bất kỳ đâu | J5 / UN-010, UN-013 |
| **Trả lời checklist tự-đánh-giá sau khi phiên đã đóng** | Mẫu số trục tuân thủ đổi sau khi điểm đã chốt — cùng một buổi tối cho hai con số khác nhau | Điểm đã chốt **không** tính lại: trục tuân thủ chỉ đọc phần hệ thống tự kiểm tại thời điểm bắn. Câu trả lời muộn làm giàu bản ghi của **lệnh**, không đụng tới điểm của **buổi**; deck nói rõ điểm dựng trên phần tự kiểm (🔶 xem A-10) | J1 / UN-009, UN-010 |
| **Số liệu tiền trên deck lệch với tài khoản trên sàn** | Không biết tin bên nào, mất niềm tin vào cả tab kết quả | Deck **luôn** lấy con số của sàn làm chuẩn và không tự dựng lại từ các lần khớp; lệch thì nói rõ đang lệch và chỉ về sàn, không âm thầm hiện con số của mình | J3 / UN-010 |
| **Mở deck khi chưa có phiên nào đã đóng** (ngày đầu tiên) | Một khung điểm rỗng trông như hỏng | Nói rõ **chưa có phiên nào**, và chỉ đường tới việc chạy phiên đầu — không hiện khung điểm rỗng, không hiện 0 | J1, J5 / UN-011 |
| **Một tháng không có lệnh nào** | Các chỉ số kết quả chia cho 0 — profit factor, tỷ lệ thắng, R trung bình không xác định | Chúng đọc là **không áp dụng**, không hiện 0 và không hiện vô cực. Điểm quy trình của tháng đó vẫn đọc bình thường — đó chính là điểm mấu chốt của feature | J3, J5 / UN-011, UN-002 |
| **Người chơi đã tắt hẳn tính năng đo tâm lý** | `tilt-meter` hứa tắt rồi thì không còn dấu vết nào trên màn hình | Phần hồi tưởng **biến mất khỏi deck**, không để lại chỗ trống. Khác hẳn trường hợp *mất dữ liệu* ở hàng dưới — cái đó vẫn nói rõ là không có dữ liệu | J8 / UN-014 |
| **Playbook đã ngừng dùng** | Lịch sử của nó có thể biến mất khỏi bảng so sánh | Bảng theo playbook vẫn tra ra được nó với đầy đủ lịch sử — deck không bao giờ mất một tháng vì một playbook bị bỏ | J7 / UN-012 |

## 7. User-side Constraints

* **Deck mở bằng tay cầm, đọc bằng chuột và bàn phím** (người chơi chốt 2026-08-28). Đây là màn hình nhìn lại sau phiên, không phải màn hình thao tác nhanh — nên không thiết kế mọi thao tác đọc bảng cho tay cầm.
* **Điểm chỉ tồn tại sau khi đóng phiên.** Không có cách nào xem điểm của buổi tối đang chạy — đây là ràng buộc có chủ ý, không phải giới hạn kỹ thuật.
* **Feature này không sinh dữ liệu của riêng nó.** Nó đọc bằng chứng từ `playbook-grading`, `ai-desk`, `order-execution`, `voice-journal`, `trade-replay`, `tilt-meter` và `daily-journal`. Nguồn nào chưa có thì trục tương ứng rơi ra (xem A-06).
* **Trọng số các trục, số lệnh tối đa kỳ vọng và độ rộng dải là cấu hình**, và tháng đầu tiên là tạm — chưa hiệu chuẩn cho người chơi này (xem A-01).
* **Deck không được thi hành gì.** Nó không chặn lệnh, không đổi hạn mức, không sửa điểm của một lệnh. Nó chỉ đọc và trình bày.
* Chỉ chạy trên Chrome desktop; deck nằm trong cùng ứng dụng web (kế thừa ràng buộc của `order-execution`).
* Chỉ tài khoản demo. **Điểm quy trình không phải lời khuyên đầu tư** — mọi panel giữ nguyên dòng chữ demo / giải trí / không phải lời khuyên.
* Giao diện sản phẩm bằng tiếng Anh; tài liệu nghiệp vụ bằng tiếng Việt.

## 8. Assumptions & Validation

| ID | Assumption | Impact if Wrong | Validation Status | Next Action |
|---|---|---|---|---|
| A-01 | Số lệnh tối đa kỳ vọng (mặc định 6) và dải ±1 hợp với nhịp giao dịch thật của người chơi này | Trục chọn lọc hoặc luôn dính 100, hoặc không bao giờ với tới — trục quan trọng nhất mất tác dụng phân biệt | Chưa xác nhận — `phase-11` nêu đúng rủi ro này ("uncalibrated for this player") | Cả hai là cấu hình và các đầu vào đều được lưu; đọc lại sau tháng đầu rồi hiệu chuẩn |
| A-02 | Chỉ số chất lượng cơ hội quy về được thang 0–1 có cơ sở, không cần hằng số tuỳ tiện | Trục chọn lọc hạ xuống ba mức thô; độ phân giải giảm nhưng tính chất "đứng ngoài chấm tốt" vẫn giữ | Chưa xác nhận — phụ thuộc `ai-desk`; `phase-04` đã dự phòng sẵn phương án ba mức. **Thêm một điều kiện chưa ai nhận:** trục chọn lọc cần chỉ số **trung bình cả phiên**, mà `ai-desk` mới chỉ cam kết *hiện nhãn mức*, chưa cam kết **ghi lại** một chuỗi số suốt phiên để lấy trung bình | Chốt khi `ai-desk` có sản phẩm; ghi rõ trong cấu hình đang dùng cách nào. Xem OQ-11 |
| A-03 | Người chơi chấp nhận **một con số duy nhất** làm thước đo buổi tối, và con số đó không thay chỗ lãi lỗ làm nỗi lo mới | Toàn bộ cơ chế phản tác dụng — feature sinh ra để chữa lo âu lại tạo ra một nguồn lo âu mới | Chưa kiểm được cho tới khi dùng thật. `phase-11` xếp đây là rủi ro số một; USC-001 chính là thước đo nó | Theo dõi số lần mở deck giữa phiên trong 10 phiên đầu; tăng dần thì đặt lại thiết kế |
| A-04 | Điểm tự chấm đầu/cuối buổi do feature khác thu; deck chỉ hiển thị | Nếu deck phải tự thu, nó cần một luồng nhập liệu — mở rộng phạm vi đáng kể và vi phạm nguyên tắc "không luồng thu thứ hai" | Chưa xác nhận — suy từ `phase-06` ("Render the phase 3 check-in rows in the trends; do not create a second capture flow") | Xác nhận ranh giới với `daily-journal` khi viết SRS |
| A-05 | Bốn trục quy trình có đủ bằng chứng **tại thời điểm bắn**, nên điểm chốt được ngay khi đóng phiên dù còn lệnh giữ qua đêm | Nếu một trục quy trình thật sự cần lệnh đóng mới chấm được, điểm sẽ chốt bằng dữ liệu thiếu | **Đã xác nhận cách xử lý** 2026-08-28 (OQ-1). Việc từng tiểu mục có thật sự chấm được tại thời điểm bắn thì phải soát lại từng cái khi viết SRS | Soát từng tiểu mục của năm trục khi viết SRS; cái nào cần lệnh đóng thì tách ra như con số kết quả |
| A-06 | Khi người chơi bắt đầu dùng deck thật, **bảy** nguồn bằng chứng đã có mặt | Giữ nguyên thứ tự kế hoạch hiện tại thì `daily-journal` — nguồn của điểm tự chấm và bản chụp kế hoạch — ra sau feature này, nên **ngày ra mắt điểm chỉ có 3/5 trục** (chuẩn bị 0.15 + nhìn lại 0.10 = 25% trọng số rơi ra). Đó là trạng thái mặc định lúc ra mắt, không phải tình huống hiếm | Chưa xác nhận — hệ quả trực tiếp của việc feature không sinh dữ liệu của riêng nó, cộng với quyết định 2026-08-28 đưa việc thu điểm tự chấm về `daily-journal` | Hoặc đổi thứ tự để `daily-journal` ra trước, hoặc chấp nhận ra mắt với 3/5 trục và để deck nói rõ con số dựa trên mấy trục |
| A-07 | Trục tuân thủ đọc **đúng bộ luật mà gateway đã thi hành**, không có định nghĩa thứ hai | Deck báo một lệnh phá luật mà gateway đã cho qua — người chơi mất niềm tin vào cả hai | Chưa xác nhận — `phase-06` nêu đúng rủi ro này ("One rule set, imported from phase 2 risk, not re-implemented") | Đối chiếu với `order-execution` và `playbook-grading` khi viết SRS |
| A-08 | Ngưỡng "bao nhiêu lần mở deck giữa phiên là đáng lo" tự lộ ra từ mốc gốc 10 phiên đầu, không cần đặt trước | Đặt sai ngưỡng thì USC-001 hoặc báo động giả liên tục, hoặc không bao giờ kêu | **Đã xác nhận cách lấy số** 2026-08-28 (OQ-4: ghi lại mỗi lần mở deck khi phiên đang chạy). Ngưỡng thì chưa có và cố ý chưa đặt | Đọc phân bố sau 10 phiên đầu rồi mới đặt ngưỡng |
| A-09 | Tập "điều kiện đứng ngoài" dùng để quy điểm **không** bao gồm mức tâm lý | Nếu bao gồm, tilt đi vào trục chọn lọc qua cửa sau: cùng một lần huỷ, tâm lý cao thì được cộng điểm, tâm lý thấp thì không. Lời hứa "tilt không bao giờ là đầu vào" (UN-014, và `tilt-meter` Mục 3) sẽ sai, và checkpoint của J8 sẽ trượt | **Đã chốt 2026-08-28** (người chơi chọn giữ lời hứa). Nguồn `phase-11` liệt kê `tilt >= 0.60` **trong** tập điều kiện đứng ngoài, nên nguồn tự mâu thuẫn với chính lời hứa của nó; lời hứa thắng vì cả hai feature đang dùng nó làm checkpoint kiểm chứng | **Cái giá đã chấp nhận:** tự huỷ *vì biết mình đang nóng* — hành vi kỷ luật nhất — không được cộng điểm chọn lọc, trừ khi cùng lúc có hoàn cảnh khác. Theo dõi xem điều này có làm người chơi thấy bị bỏ sót không; có thì đặt lại ở OQ-10 |
| A-10 | Câu trả lời checklist muộn **không** làm tính lại điểm đã chốt | Nếu có tính lại, cùng một buổi tối cho hai con số khác nhau tuỳ lúc đọc — phá đúng tính chất OQ-1 vừa chốt | 🔶 Quyết định thay user 2026-08-28 — `playbook-grading` cho phép trả lời muộn hoặc bỏ hẳn, nguồn không nói việc đó có chạm điểm buổi không | Xác nhận khi viết SRS, cùng `playbook-grading` UN-009 |

## 9. User Success Criteria

| ID | User Outcome | Baseline | Target | Measurement | Review Period |
|---|---|---|---|---|---|
| USC-001 | Điểm quy trình **không trở thành nỗi lo mới** thay chỗ lãi lỗ | **Chưa có** — xác lập số lần mở deck giữa phiên và số lệnh trung bình mỗi tối từ 10 phiên đầu | Số lần mở deck **giữa phiên** không tăng theo tháng, **đồng thời** số lệnh trung bình mỗi tối không tăng theo tháng khi chất lượng cơ hội trung bình không đổi. **Chưa có ngưỡng tuyệt đối** và cố ý chưa đặt — để phân bố 10 phiên đầu tự nói (xem A-08) | Đếm số lần mở deck trong lúc phiên còn chạy — deck ghi lại mỗi lần mở như vậy (chốt 2026-08-28) — đọc cuối mỗi tháng, đặt cạnh số lệnh trung bình mỗi tối và chất lượng cơ hội trung bình. Ba số liệu đọc cùng nhau: số lệnh tăng mà cơ hội cũng tăng thì không phải tín hiệu xấu. Đọc kèm **tỷ lệ phiên có mở deck sau khi đóng phiên** — tỷ lệ này tụt về 0 thì USC-001 đẹp vì bỏ bê chứ không phải vì bình tĩnh | Đọc hằng tháng, kết luận hằng quý |
| USC-002 | Điểm quy trình trung bình **đi lên**, không phải đi lên nhờ nới thước | **Chưa có** — xác lập điểm trung bình từ 10 phiên đầu | Điểm quy trình trung bình theo tháng cao hơn mốc gốc sau 3 tháng, **đồng thời** mọi tháng đem so đều đã được tính lại bằng **cùng một bộ trọng số** | Đọc điểm trung bình theo tháng kèm **số phiên** và **phiên bản trọng số đang dùng**. Đổi trọng số giữa kỳ thì so lại toàn bộ lịch sử bằng bộ mới trước khi kết luận — nếu không, việc nới trọng số một trục dễ đạt sẽ tự động trông như tiến bộ. **Lá chắn này chưa phủ hết:** trục chọn lọc phụ thuộc số lệnh kỳ vọng và độ rộng dải — cấu hình riêng của feature, không phải trọng số — nên nới chúng vẫn là một đường làm đẹp điểm mà vế "cùng một bộ trọng số" không chặn được (xem OQ-7) | Đọc hằng tháng, kết luận hằng quý |
| USC-003 | Người chơi **tự tin và vui hơn** khi giao dịch — đây là thước đo **cấp sản phẩm** (xem `docs/_shared/project-profile.md`) mà feature này đọc hộ, không truy về một nhu cầu riêng của nó | **Chưa có** — xác lập điểm tự chấm đầu/cuối buổi trung bình từ 10 phiên đầu | Điểm tự chấm **cuối buổi** trung bình cao hơn mốc gốc sau 3 tháng, đọc cạnh điểm quy trình chứ không cạnh lãi lỗ | Đọc điểm tự chấm trung bình theo tháng, kèm **tỷ lệ phiên có tự chấm** — tỷ lệ này tụt thì con số trung bình mất ý nghĩa (chỉ còn những tối thấy vui mới buồn bấm) | Đọc hằng tháng, kết luận hằng quý |

> **USC-001 và USC-002 kéo ngược nhau, và đó là chủ ý.** USC-002 muốn điểm đi lên; USC-001 canh
> chừng đúng cái giá phải trả nếu người chơi bắt đầu đuổi theo con số đó. **Phải đọc cùng nhau** —
> USC-002 đạt trong khi USC-001 xấu đi thì feature đang thất bại chứ không phải thành công.
>
> **Giới hạn đã biết.** Cả ba thước đo đọc từ chính dữ liệu do sản phẩm sinh ra, nên chúng đo *sự
> nhất quán của quy trình*, không đo *chất lượng của quy trình*. Cụ thể: USC-002 chặn được việc nới
> trọng số (vế "cùng một bộ trọng số"), nhưng **không** chặn được việc hạ chuẩn ở tầng dưới — nới
> luật playbook làm trục tuân thủ đẹp lên. Vế phòng thủ cho việc đó nằm ở `playbook-grading`
> (USC-002 của URD đó), và hai thước đo cần đọc cùng nhau.

## 10. Open Questions

* [x] OQ đã chốt 2026-08-28: phạm vi feature gộp cả deck (`phase-06` + `phase-11`); deck mở bằng tay cầm và đọc bằng chuột; điểm chốt lặng lẽ, người chơi tự mở deck khi muốn; ba thước đo thành công ở Mục 9.
* [x] OQ-1: Còn lệnh mở lúc đóng phiên thì điểm chốt khi nào? — **Resolved:** chốt **ngay khi đóng phiên**, không chờ. Bốn trục quy trình chấm tại thời điểm bắn nên đã có đủ bằng chứng; chỉ các con số kết quả ở tab tiền mới chờ lệnh ngã ngũ và cập nhật sau, và việc đó không đụng tới điểm. Xu hướng theo tháng vì vậy không bao giờ thủng lỗ. Xem A-05 — từng tiểu mục của năm trục vẫn cần soát lại khi viết SRS.
* [x] OQ-2: Mở deck giữa phiên có nên bị hạn chế thêm không? — **Resolved:** **không chặn.** Chặn thì phải đẻ thêm một trạng thái khoá, mà người chơi có lý do chính đáng để mở giữa phiên (xem lại bảng theo playbook chẳng hạn). Giữ nguyên luật "buổi hôm nay chưa tồn tại trên deck cho tới khi đóng phiên", và bù lại bằng việc đếm ở OQ-4.
* [x] OQ-3: Bộ đếm tự huỷ tính mọi lần huỷ hay chỉ khi đang có điều kiện đứng ngoài? — **Resolved:** **một bộ đếm gốc, hai cách đọc.** Bộ đếm trên màn hình chính giữ nguyên luật rộng của `order-execution` UN-006 (đếm mọi lần tự huỷ chủ động); trục chọn lọc chỉ quy điểm trên **tập con** những lần huỷ xảy ra lúc đang có điều kiện đứng ngoài. Không có bộ đếm thứ hai — chỉ cần mỗi lần huỷ ghi kèm lúc đó có điều kiện đứng ngoài hay không. Đóng luôn OQ-8 của `playbook-grading`.
* [x] OQ-4: Số lần mở deck giữa phiên có được ghi lại không, bao nhiêu là đáng lo? — **Resolved:** **có ghi lại** — đó là số liệu USC-001 cần, không ghi thì thước đo của rủi ro lớn nhất không đo được. Ngưỡng thì **cố ý chưa đặt**: để phân bố 10 phiên đầu tự nói. Xem A-08.
* [x] OQ-5: Chưa có `daily-journal` thì trục chuẩn bị rơi cả trục hay một tiểu mục? — **Resolved:** áp đúng luật đã có, không cần luật riêng — tiểu mục thiếu bằng chứng rơi ra và trục chuẩn hoá lại; rơi hết tiểu mục thì cả trục rơi thành "không áp dụng". Giống hệt cách xử lý khi tắt ghi âm.
* [x] OQ-8: Ranh giới với `daily-journal` và mức lưu "đã mở replay" — **Resolved:** `daily-journal` OQ-1 đóng lại bằng quyết định 2026-08-28 ở Mục 3 (mọi số liệu so sánh nhiều phiên thuộc feature này; nhật ký chỉ đọc lại). Về replay: `trade-replay` ghi chi tiết **từng lần mở, từng lệnh**; feature này chỉ đọc ở mức **phiên** (có ít nhất một lần mở) — hai mức lưu khác nhau nhưng không mâu thuẫn.
* [x] OQ-6 đã chốt 2026-08-28: **có** — điểm quy trình nằm trong cả báo cáo lẫn bản xuất dữ liệu. Ràng buộc "tiền nằm sau một cú bấm có chủ ý" áp cho một tệp tĩnh bằng cách chuyển cú bấm đó về **lúc tạo tệp**: phụ lục kết quả tiền **mặc định tắt**, người chơi phải tự tích thì tệp mới có con số tiền. Xem `docs/reports-export/reports-export-urd.md` UN-003.
* [ ] OQ-7: Hiệu chuẩn lại số lệnh tối đa kỳ vọng và độ rộng dải — làm khi nào và dựa trên bao nhiêu phiên? Đổi giữa chừng thì các tháng cũ có được tính lại như khi đổi trọng số không? Xem A-01.
* [ ] OQ-9: Feature này có cung cấp điểm ở mức **buổi tối** không, hay chỉ mức **phiên**? Nguồn chỉ định nghĩa điểm theo phiên. Một buổi tối có hai phiên trở lên thì bản đồ nhiệt của `daily-journal` phải tô bằng một con số — quy tắc gộp nhiều phiên thành một ô thuộc feature nào? (`daily-journal` OQ-7 đang hỏi ngược về đây.)
* [ ] OQ-10: Danh sách đóng "điều kiện đứng ngoài" dùng để quy điểm gồm đúng những hoàn cảnh nào — sắp có tin, chênh lệch giá vượt trần, ngoài khung giờ, không playbook nào đủ luật? **Mức tâm lý đã bị loại** khỏi tập này (A-09, chốt 2026-08-28) — câu còn lại là danh sách bốn hoàn cảnh kia đã đủ chưa, và có hoàn cảnh nào nên thêm không.
* [ ] OQ-11: `ai-desk` có **ghi lại** chỉ số chất lượng cơ hội suốt phiên không, hay chỉ hiện nhãn mức? Trục chọn lọc cần mức **trung bình cả phiên**; `ai-desk` OQ-3 mới chỉ cam kết phần hiển thị.
* [ ] OQ-12: Hình thức thể hiện năm trục — biểu đồ radar (theo nguồn) hay một bảng năm dòng có cùng thông tin? Với một người dùng, bảng rẻ hơn nhiều; chốt lúc vẽ wireframe.

---

> **Lịch sử review:** chốt OQ-1, OQ-2, OQ-3, OQ-4, OQ-5, OQ-8 ngày 2026-08-28 (`/urd` Phase E), kèm
> cascade sang `order-execution` và `playbook-grading`. Review bởi `@senior-ba` (6 blocking,
> 16 warning, 6 suggestion) và `@po-reviewer` (0 blocking, 4 warning, 2 suggestion) cùng ngày;
> findings đã áp vào Mục 1, 2, 3, 4, 5, 6, 8, 9, 10 và sinh thêm A-09, A-10, OQ-10, OQ-11, OQ-12,
> bảng "Năm trục dựng trên bằng chứng của feature nào" ở Mục 3, và 5 tình huống mới ở Mục 6.
