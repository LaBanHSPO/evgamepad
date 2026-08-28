---
type: urd
feature: playbook-grading
status: draft
updated: 2026-08-28
links: ["[[docs/_shared/project-profile.md]]", "[[docs/_shared/system-overview.md]]", "[[docs/_shared/definitions.md]]", "[[docs/_shared/operating-environment.md]]", "[[docs/order-execution/order-execution-urd.md]]"]
---

# playbook-grading — User Requirements Document

## 1. Purpose

Ghi lại nhu cầu của người chơi quanh việc **biết trước khi bấm** rằng lệnh sắp vào có khớp với chính
luật mình đã viết ra hay không — và quanh việc điều đó **không bao giờ được biến thành rào chặn**.

Feature này đứng sát đường đi nóng nhưng không nằm trên nó: nó đưa một câu hỏi vào đúng khoảnh khắc
người chơi còn quyền không vào lệnh. Vì vậy nhu cầu trung tâm ở đây không phải "chấm điểm cho đẹp
sổ" mà là **"đối chiếu luật đúng lúc còn sửa được, và luật của tôi không bao giờ được phép cấm tôi"**.

### User Problem & Current Experience

| User | Current Situation | Problem | User Consequence | Evidence |
|---|---|---|---|---|
| Người chơi | Luật giao dịch chỉ sống trong đầu, không được viết ra ở đâu | Luật trôi theo tâm trạng — cùng một setup, tối nay đủ tiêu chuẩn, tối mai không | Không có gì để đối chiếu, nên cũng không có gì để cải thiện; mỗi tối bắt đầu lại từ đầu | Observed: `phase-07` ("a playbook is a named setup with explicit rules") |
| Người chơi | Nếu có checklist thì nó nằm trên giấy hoặc trong trí nhớ | Nhớ ra luật **sau** khi đã vào lệnh, lúc không còn sửa được gì | Việc đối chiếu luôn tới muộn — thành hối tiếc thay vì phòng ngừa | Observed: `phase-07` ("graded ... **before** you commit") |
| Người chơi | Công cụ nhật ký hiện có (Edgewonk, TradeZella) chấm điểm sau phiên, bằng bàn phím | Chấm điểm là việc hậu kỳ, tách hẳn khỏi khoảnh khắc ra quyết định | Công cụ trở thành sổ sách để nhìn lại, không phải người huấn luyện đứng cạnh lúc cần | Observed: `README.md` (đoạn journal), `docs/_shared/project-profile.md` (benchmark) |
| Người chơi | Một buổi tối có nhiều kiểu setup khác nhau, tất cả bị gộp chung | Mọi lệnh nằm trong một rổ, không phân biệt được kiểu chơi nào là kiểu nào | Không có gì để về sau trả lời "kiểu setup nào của tôi thực sự hoạt động" — mỗi lệnh không mang nhãn nào cả. *(Feature này giao **nguyên liệu**: mỗi lệnh mang tên playbook và điểm của nó. Việc đối chiếu hiệu quả giữa các playbook thuộc `process-score`.)* | Observed: `phase-07` ("which of my setups actually works") |
| Người chơi | Việc tự kiềm chế đã được đếm (bộ đếm tự huỷ), nhưng không có bối cảnh | Không phân biệt được "tự huỷ một setup rác" với "tự huỷ một setup đúng sách vì sợ" | Hai hành vi trái ngược nhau — một cái là kỷ luật, một cái là do dự — cùng cộng vào một con số | Suy từ `order-execution-urd.md` UN-006 + `phase-07` (chấm điểm theo mỗi lần vũ trang) |

## 2. User Types

| Tier | User Type | Context | Primary Goal | Pain Points |
|---|---|---|---|---|
| primary | **Người chơi** | Vừa là người viết luật (ngoài phiên, trước màn hình, có chuột và bàn phím), vừa là người bị luật đó soi (trong phiên, tay đặt trên tay cầm) | Giao dịch theo sách của chính mình, và biết được mình có làm đúng vậy không — trước khi bấm, chứ không phải sáng hôm sau | Luật vô hình nên không thi hành được; đối chiếu luôn muộn; sợ công cụ quay ra cấm mình vào lệnh |

> **Không có secondary user.** Công cụ cá nhân một người dùng. **AI desk không tham gia chấm điểm** —
> nguồn nêu rõ điểm là kết quả tính toán xác định, không có mô hình ngôn ngữ nào chấm một lệnh.
> Sàn cTrader/Spotware là actor hệ thống. Xem `docs/_shared/project-profile.md`.

## 3. Scope Boundaries

### In Scope

* Người chơi khai một playbook: tên, phương pháp, cặp áp dụng, mô tả bằng lời của chính mình, và một danh sách luật có thứ tự. **Cặp áp dụng được đối chiếu như một luật**, không phải như một bộ lọc — bắn ngoài danh sách cặp thì mất một luật, không bị cản.
* Mỗi luật khai rõ **bắt buộc hay không**, và **hệ thống tự kiểm được hay do người chơi tự trả lời sau lệnh**.
* Người chơi bắt đầu với một bộ playbook mẫu dựng theo các setup M5 quen thuộc — dùng được ngay, sửa được, không phải màn hình trống.
* Người chơi chọn playbook đang dùng **bằng tay cầm**, trong menu an toàn; playbook đang dùng thuộc trạng thái của phiên và hiện rõ trên màn chính.
* Hệ thống chấm điểm **mỗi lần vũ trang và mỗi lần bắn** theo playbook đang chọn — kể cả những lần kết thúc bằng **người chơi tự huỷ**, và những lần **bị hạn mức rủi ro chặn**.
* Người chơi thấy tên playbook, số luật đạt trên tổng, và luật nào không đạt **ngay trên màn xác nhận, trước thao tác cuối cùng**.
* Luật playbook **không bao giờ chặn được một lệnh**; chỉ hạn mức rủi ro mới chặn được.

> **Hai chữ dễ lẫn, dùng nhất quán trong doc này:** *tự huỷ* = người chơi đã vũ trang rồi chủ động không vào; *bị chặn* = hạn mức rủi ro của `order-execution` không cho lệnh đi. Cả hai đều được chấm điểm.
* Người chơi bắn khi chưa chọn playbook — lệnh vẫn đi, được ghi vào nhóm **"ngoài kế hoạch"** và đọc ra đúng như vậy.
* Người chơi trả lời các luật **tự-đánh-giá** bằng một checklist rất ngắn sau khi lệnh đóng; bỏ qua được và bỏ qua không bị trừ.
* Người chơi thấy lại điểm của **một lần tự huỷ, khi setup đó đã đạt đủ luật bắt buộc**.
* Người chơi mở lại **một lệnh đã chấm** và thấy playbook nào chấm nó, từng luật đạt / không đạt / không kiểm được / chưa trả lời. *(Xem lại **một** lệnh thuộc feature này; so sánh **nhiều** lệnh với nhau thuộc `process-score`.)*
* Feature này **đóng góp nội dung vào màn xác nhận do `order-execution` sở hữu** — nó không sở hữu màn đó và không thêm bước nào vào chuỗi xác nhận hai tay.
* Người chơi sửa luật của một playbook giữa phiên mà không làm đổi điểm đã chấm trước đó.
* Người chơi ngừng dùng một playbook mà không mất khả năng tra lại các lệnh cũ đã được nó chấm.

### Out of Scope

* **Thống kê hiệu quả theo từng playbook** (playbook nào thực sự sinh lợi thế: số lệnh, kỳ vọng theo R, MFE/MAE) → feature `process-score`. URD này chỉ tạo ra dữ liệu điểm; nơi đọc và so sánh nó là deck. *(Chốt 2026-08-28 — nguồn `phase-07` và `phase-11` mâu thuẫn về chỗ đặt bảng này.)*
* **Điểm quy trình 5 trục và biểu đồ radar** (trục Adherence tiêu thụ điểm của feature này) → feature `process-score`.
* **Luật rủi ro và việc thi hành chúng** (hạn mức khối lượng, khung giờ, mức lỗ tối đa, số vị thế) → feature `order-execution`. URD này chỉ nhận **ranh giới**: luật playbook không được phép có hệ quả như luật rủi ro.
* **Bộ đếm số lần tự huỷ trên màn chính** → feature `order-execution`. URD này chỉ nhận phần **điểm** gắn với một lần tự huỷ. Bộ đếm đó đếm **mọi** lần tự huỷ chủ động, không phụ thuộc kết quả chấm luật (chốt 2026-08-28, xem OQ-8) — nên điểm playbook là lớp thông tin thêm cho một lần huỷ, không phải điều kiện để nó được đếm.
* **Đo trạng thái tâm lý và ma sát thích ứng** (tilt tiêu thụ điểm như tín hiệu phá luật) → feature `tilt-meter`.
* **Nhận diện setup trên biểu đồ và mọi tư vấn, tín hiệu, phân tích** → feature `ai-desk`. Không có mô hình ngôn ngữ nào chấm một lệnh.
* **Ghi âm lý do vào lệnh** → feature `voice-journal`. **Tua lại lệnh qua tape** → feature `trade-replay`.
* **Nghi thức chuẩn bị trước phiên và tự đánh giá đầu/cuối buổi** → feature `daily-journal`.
* **Báo cáo, xuất dữ liệu, sao lưu** → feature `reports-export`.
* Chia sẻ, nhập hoặc xuất playbook giữa nhiều người dùng — sản phẩm chỉ có một người dùng.

## 4. User Needs

| ID | User | Context / Trigger | User Need | Expected Outcome | Importance | Evidence |
|---|---|---|---|---|---|---|
| UN-001 | Người chơi | Đã vũ trang, đang nhìn màn xác nhận, chưa bấm thao tác cuối | Biết lệnh sắp vào có khớp sách của mình không, **khi vẫn còn quyền không vào** | Màn xác nhận nêu tên playbook đang dùng, số luật đạt trên tổng số luật xét, và luật nào không đạt — đủ ngắn để đọc hết trước khi bấm. **Điểm là một phần của chính màn xác nhận: màn này không mở ra khi chưa có điểm**, nên không tồn tại khoảnh khắc người chơi nhìn thấy nút bấm mà chưa thấy điểm. **Tổng số luật xét** = mọi luật của playbook đang dùng, trừ luật không kiểm được và luật tự-đánh-giá chưa trả lời; kết luận riêng "đạt đủ **luật bắt buộc**" tính trên nhóm bắt buộc trong chính tổng đó (🔶 quyết định thay user) | Critical | Observed: `phase-07` ("visible in the confirm overlay **before you commit**"; mẫu overlay `4/5 rules OK · ✗ price > 1.5 ATR from EMA20`) |
| UN-002 | Người chơi | Mọi lúc, đặc biệt khi một luật do chính mình viết không đạt | Luật do mình viết **không bao giờ được phép chặn lệnh của mình** | Một luật playbook không đạt vẫn cho lệnh đi trọn vẹn; chỉ hạn mức rủi ro mới chặn được. Ranh giới này không phụ thuộc vào cách người chơi khai luật, và không có cách nào khai một luật playbook thành luật chặn | Critical | Observed: `phase-07` ("risk rules are enforced, playbook rules are graded"; "a `scope: 'playbook'` rule **never** rejects an intent") |
| UN-003 | Người chơi | Lần đầu dùng sản phẩm, hoặc sau khi bỏ hết playbook cũ | Có sẵn một quyển sách thật để bắt đầu, không phải một màn hình trống | Bộ playbook mẫu dựng theo các setup M5 quen thuộc (hộp tích luỹ, phá vỡ, kiểm lại sau phá vỡ, phá vỡ giả, phá khối) — dùng được ngay và sửa được thành của mình | High | Observed: `phase-07` ("seed playbooks ... so the player starts with a real book, not an empty one"; "the empty state is the failure state") |
| UN-004 | Người chơi | Luật của mình đổi theo thời gian — chỉnh ngưỡng, thêm hoặc bớt một luật | Sửa được luật mà không làm sai lệch bản ghi cũ | Điểm đã chấm giữ nguyên đúng như lúc chấm — nó là bản ghi của quyết định lúc đó. Luật mới chỉ áp cho các lần vũ trang sau. **Phần hệ thống tự kiểm đóng băng ngay tại thời điểm bắn và không bao giờ đổi**; phần tự-đánh-giá là một lớp ghi thêm sau khi lệnh đóng, và nó **có** làm đổi kết luận "đạt đủ luật bắt buộc" — vì đó chính là việc nó sinh ra để làm (🔶 quyết định thay user) | High | Confirmed 2026-08-28 (người chơi chốt) |
| UN-005 | Người chơi | Bắn khi chưa chọn playbook nào | Không bị chặn, không bị báo lỗi, nhưng cũng không được ghi nhầm là đúng sách | Lệnh vẫn đi bình thường; được ghi vào nhóm **"ngoài kế hoạch"** và đọc ra đúng như vậy ở mọi nơi nhìn lại | High | Observed: `phase-07` (`__unplanned__` fallback, "not a crash and not a block", "reads honestly as unplanned") |
| UN-006 | Người chơi | Trong một buổi có nhiều kiểu setup khác nhau | Đổi playbook đang dùng giữa phiên **bằng tay cầm**, không phải rời tay sang chuột | Chọn được trong menu an toàn bằng D-pad và một nút áp dụng; playbook đang dùng hiện rõ trên màn chính để không bao giờ chấm nhầm sách | High | Observed: `phase-07` ("selectable from the GameOverlay's Playbook destination; D-pad selects and A applies") |
| UN-007 | Người chơi | Suốt phiên | Điểm số là kết quả tính toán, không phải ý kiến của một mô hình | Cùng một bối cảnh luôn cho ra cùng một điểm; AI desk không tham gia chấm, không sửa được điểm, và không giải thích thay luật | High | Observed: `phase-07` ("grading is a **pure function over context**; no LLM grades a trade") |
| UN-008 | Người chơi | Bối cảnh thị trường đổi giữa lúc vũ trang và lúc bấm | Không bị đánh lừa bởi một điểm số đã cũ | Điểm được tính lại tại thời điểm bắn; điểm lúc vũ trang là tham khảo, điểm lúc bắn là bản ghi chính thức. Khi hai lần cho kết quả khác nhau, người chơi thấy được điều đó thay vì chỉ thấy con số cuối | Medium | Observed: `phase-07` ("re-evaluate at FIRE"; "the FIRE grade is authoritative, the ARM grade is advisory") |
| UN-009 | Người chơi | Sau khi một lệnh đóng | Trả lời được những luật chỉ mình mới biết (vd "tôi đã chờ kiểm lại") mà không thấy nặng nề | Checklist **tối đa 3 câu, mỗi câu một thao tác**, hiện **ngay khi lệnh đóng**, lúc bối cảnh còn nóng — nhưng không bao giờ đè lên thao tác đang làm; nhiều lệnh đóng liên tiếp thì xếp hàng, còn tồn đọng thì được gợi lại cuối phiên. Bỏ qua được ở mọi thời điểm. **Bỏ qua không bị tính là sai** — luật chưa trả lời rơi khỏi tổng số luật xét, nên không tốn của người chơi thứ gì | Medium | Observed: `phase-07` ("3-tap post-trade checklist"; "skipping marks them `unknown` — excluded from `required_total` ... never costs the player anything") |
| UN-010 | Người chơi | Vừa chủ động tự huỷ một setup **đã đạt đủ luật bắt buộc** của chính mình | Nhận ra khi nào mình đang bỏ qua cơ hội đúng sách vì sợ, chứ không vì luật | Chỉ khi setup bị tự huỷ đạt đủ luật bắt buộc thì điểm đó mới được hiện lại. Tự huỷ một setup không đạt thì **không nói gì** — đó chính là hành vi đúng. Vì một lần huỷ không bao giờ có "lệnh đóng", kết luận "đạt đủ" ở đây **chỉ tính trên luật hệ thống tự kiểm được**; playbook không còn luật bắt buộc tự-kiểm nào thì không hiện gì | Medium | Nguyên tắc chỉ-hiện-khi-đạt-chuẩn: Confirmed 2026-08-28. Định nghĩa "đạt chuẩn" = đủ luật bắt buộc: 🔶 xem A-05. Nền: `phase-07` ("declines and rejects are gradeable too") |
| UN-011 | Người chơi | Một cách chơi không còn hợp và muốn bỏ | Ngừng dùng một playbook mà không mất lịch sử | Playbook ngừng dùng biến khỏi danh sách chọn; các lệnh cũ vẫn tra ra được đúng tên playbook và đúng điểm đã chấm chúng | Medium | Observed: `phase-07` (`retired_at`; "historical grades keep resolving, so the deck never loses a month") |
| UN-012 | Người chơi | Ngoài phiên, khi ngồi soạn hoặc sửa playbook | Soạn luật ở nơi soạn được thật sự thoải mái, nhưng dùng nó lúc giao dịch thì không phải rời tay cầm | Trang soạn playbook riêng dùng chuột và bàn phím; việc **chọn** playbook lúc đang giao dịch làm hoàn toàn bằng tay cầm. Hai việc này không lẫn vào nhau | Medium | Observed: `phase-07` (`/playbooks` editor + `PlaybookPicker` điều khiển bằng pad). Phân công chuột/tay cầm là suy luận — xem A-01 |
| UN-013 | Người chơi | Có một cách chơi quen thuộc nhưng chưa bao giờ viết nó ra | Biến luật đang nằm trong đầu thành một danh sách máy đối chiếu được | Khai được từng luật, và với mỗi luật tự chọn **bắt buộc hay không** và **hệ thống tự kiểm hay mình tự trả lời sau lệnh**. Đây là bước biến một thói quen thành một thứ có thể đối chiếu | High | Suy từ Mục 1 hàng 1 + `phase-07` (`playbook_rule` có `kind`, `required`, `params`) |
| UN-014 | Người chơi | Sau phiên, khi nhìn lại một lệnh cụ thể | Mở lại một lệnh đã chấm và thấy đủ chuyện gì đã xảy ra lúc đó | Thấy playbook nào chấm nó, và từng luật ở trạng thái nào: đạt / không đạt / không kiểm được / chưa trả lời. Đây cũng là bề mặt để tự kiểm chứng mọi journey của feature | High | Suy từ chính các checkpoint Mục 5 + `phase-07` ("historical grades keep resolving") |

## 5. Prioritized User Journeys

### Journey 1: Vào lệnh và thấy điểm trước khi bấm

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Đã chọn playbook cho buổi tối, thấy một setup và vũ trang một hướng
* __Expected outcome:__ Người chơi bấm nút cuối cùng khi đã biết lệnh này đạt bao nhiêu luật trên tổng, và luật nào không đạt
* __Related needs:__ UN-001, UN-003, UN-006, UN-007, UN-008

1) Người chơi chọn playbook cho buổi tối trong menu an toàn; tên playbook hiện trên màn chính.
2) Thấy một setup và vũ trang một hướng.
3) Màn xác nhận hiện ra kèm tên playbook, số luật đạt trên tổng, và tên luật không đạt.
4) Người chơi đọc con số đó rồi quyết định bấm hay không.
5) Nếu bấm, điểm được tính lại tại thời điểm đó và trở thành bản ghi chính thức của lệnh.

__Independent verification:__ Với một playbook có 5 luật, **đặt tham số của đúng 1 luật sao cho
bối cảnh hiện tại chắc chắn không đạt** (không phải chờ thị trường);
màn xác nhận phải hiện `4/5` và nêu đúng tên luật đó, đối chiếu được với chính bản khai luật. Kiểm
thêm chiều ngược: không có lần vũ trang nào mà màn xác nhận hiện ra kèm ô điểm trống. Không cần bất
kỳ journey nào khác để xác nhận.

### Journey 2: Một luật không đạt — lệnh vẫn đi

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Màn xác nhận báo một luật playbook không đạt, nhưng người chơi vẫn muốn vào
* __Expected outcome:__ Lệnh vào sàn bình thường; điểm ghi lại đúng là có một luật không đạt
* __Related needs:__ UN-002, UN-001

1) Người chơi đang ở màn xác nhận với một luật playbook không đạt.
2) Bấm xác nhận như bình thường.
3) Lệnh đi trọn vẹn tới sàn — không có bước cản, không có cảnh báo chặn, không có xác nhận phụ.
4) Bản ghi của lệnh giữ nguyên sự thật: playbook nào, luật nào không đạt.

__Independent verification:__ Cùng một thao tác, hai bối cảnh. Bối cảnh A vi phạm một **luật
playbook** — kiểm tra trên cTrader demo phải thấy vị thế mới. Bối cảnh B vi phạm một **hạn mức rủi
ro** — lệnh phải bị chặn. Hai kết quả trái ngược trên cùng một thao tác chính là bằng chứng của
ranh giới. Đây là journey phải hoạt động kể cả khi mọi thứ khác của feature hỏng.

### Journey 3: Bắn khi chưa chọn playbook

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Thấy cơ hội trước khi kịp chọn playbook, hoặc cố ý vào một lệnh không thuộc sách nào
* __Expected outcome:__ Lệnh vào sàn, và được ghi trung thực là ngoài kế hoạch
* __Related needs:__ UN-005, UN-002, UN-014

1) Chưa có playbook nào được chọn cho phiên.
2) Người chơi vũ trang và bấm xác nhận.
3) Màn xác nhận nói rõ đang không có playbook nào — không báo lỗi, không cản.
4) Lệnh vào sàn; bản ghi của nó thuộc nhóm "ngoài kế hoạch".

__Independent verification:__ Không chọn playbook rồi bắn; kiểm tra trên cTrader demo thấy vị thế
tồn tại, và mở bản ghi lệnh đó thấy nhóm "ngoài kế hoạch" thay vì tên một playbook bất kỳ.

### Journey 4: Từ chối một setup đạt đủ luật

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Đã vũ trang một setup mà chính luật của mình chấm là đạt, rồi vẫn chủ động huỷ
* __Expected outcome:__ Người chơi biết mình vừa bỏ qua một cơ hội đúng sách, và điều đó được ghi lại
* __Related needs:__ UN-010, UN-001

1) Người chơi vũ trang; màn xác nhận báo đạt đủ luật bắt buộc.
2) Người chơi vẫn chủ động huỷ.
3) Hệ thống cho biết setup vừa huỷ đã đạt đủ luật — hiện **đúng một lần** cho một lần huỷ, tự biến mất, không cần thao tác đóng. Cùng khoảnh khắc đó, bộ đếm tự huỷ của `order-execution` cũng tăng; hai thông tin này phải đọc được như một, không đá nhau.
4) Điểm của lần huỷ đó được lưu lại, mở xem lại được như một lệnh bất kỳ (UN-014).

__Independent verification:__ Đặt tham số các luật bắt buộc sao cho bối cảnh hiện tại chắc chắn
đạt hết, vũ trang rồi huỷ — phải thấy thông tin đó. Đặt lại cho chắc chắn không đạt rồi lặp lại —
**không** được hiện gì. Hai lần chạy đối nhau kiểm
chứng đúng điều kiện.

### Journey 5: Soạn một playbook mới từ một cách chơi quen thuộc

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Nhận ra mình vẫn vào lệnh theo một khuôn nhất định, và muốn viết khuôn đó ra
* __Expected outcome:__ Có một playbook mới dùng được ngay trong phiên tới, với luật do chính mình đặt
* __Related needs:__ UN-013, UN-012, UN-003, UN-006

1) Người chơi mở trang soạn playbook, có thể bắt đầu từ một bản mẫu hoặc từ trang trắng.
2) Đặt tên, chọn cặp áp dụng, viết mô tả bằng lời của mình.
3) Khai từng luật; với mỗi luật chọn bắt buộc hay không, và hệ thống tự kiểm hay mình tự trả lời sau lệnh.
4) Lưu lại; playbook xuất hiện trong menu chọn trên tay cầm ngay khi có ít nhất một luật.
5) Chọn nó trong phiên và thấy chính những luật vừa khai hiện lên ở màn xác nhận.

__Independent verification:__ Soạn một playbook mới với 2 luật, lưu, rồi chọn nó bằng tay cầm; màn
xác nhận ở lần vũ trang kế tiếp phải nêu đúng tên và đúng 2 luật đó. Kiểm chiều ngược: lưu một
playbook chưa khai luật nào — nó **không** được xuất hiện trong menu chọn.

### Journey 6: Sửa luật giữa phiên rồi dùng ngay

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Giữa phiên nhận ra một ngưỡng trong playbook đang quá lỏng hoặc quá chặt
* __Expected outcome:__ Luật mới có hiệu lực cho lệnh sau, và các lệnh đã chấm không bị đụng tới
* __Related needs:__ UN-004, UN-012, UN-006, UN-014

1) Người chơi mở trang soạn playbook và sửa một ngưỡng.
2) Quay lại màn giao dịch; playbook đang dùng vẫn là playbook đó, nay với luật mới.
3) Lần vũ trang tiếp theo được chấm theo luật mới.
4) Mở lại một lệnh đã chấm trước lúc sửa — điểm của nó không đổi.

__Independent verification:__ Ghi lại điểm của một lệnh trước khi sửa; sửa ngưỡng theo hướng làm
lệnh đó đáng lẽ phải fail; mở lại lệnh cũ — điểm phải y nguyên. Đồng thời lệnh mới phải phản ánh
ngưỡng mới.

### Journey 7: Trả lời checklist sau khi lệnh đóng

* __User:__ Người chơi · __Importance:__ Medium
* __Trigger:__ Một vị thế vừa đóng, và playbook của nó có luật tự-đánh-giá
* __Expected outcome:__ Những luật chỉ người chơi biết được trả lời — hoặc được bỏ qua mà không tốn gì
* __Related needs:__ UN-009, UN-014

1) Vị thế đóng.
2) Một checklist rất ngắn hiện ra ngay lúc đó, đúng các luật tự-đánh-giá của playbook đã chấm lệnh đó — chờ nếu người chơi đang bận thao tác khác.
3) Người chơi trả lời, hoặc bỏ qua.
4) Nếu bỏ qua, những luật đó ghi là chưa trả lời và **rơi khỏi tổng số luật xét** — không thành lỗi.

__Independent verification:__ Đóng một lệnh và bỏ qua checklist; mở bản ghi lệnh đó phải thấy các
luật tự-đánh-giá ở trạng thái chưa trả lời, tổng số luật xét nhỏ hơn tương ứng, và **không** luật nào
bị đánh là sai.

### Journey 8: Ngừng dùng một playbook

* __User:__ Người chơi · __Importance:__ Medium
* __Trigger:__ Một cách chơi không còn hợp và người chơi muốn nó biến khỏi danh sách chọn
* __Expected outcome:__ Playbook không còn chọn được, nhưng lịch sử vẫn nguyên vẹn
* __Related needs:__ UN-011, UN-004, UN-014

1) Người chơi đánh dấu ngừng dùng một playbook trong trang soạn.
2) Menu chọn playbook trên tay cầm không còn hiện nó.
3) Các lệnh cũ đã được nó chấm vẫn tra ra đúng tên playbook và đúng điểm.

__Independent verification:__ Ngừng dùng một playbook đang có lệnh cũ; mở menu chọn trên tay cầm —
không thấy nó; mở một lệnh cũ — vẫn thấy đúng tên playbook đó và đúng điểm.

## 6. User Exceptions & Edge Conditions

| Situation | User Impact | Expected User-facing Outcome | Related Journey / Need |
|---|---|---|---|
| **Thiếu dữ liệu để kiểm một luật tự động** (giá đã cũ, chưa đủ nến, AI desk im lặng) | Điểm có thể sai lệch mà người chơi không biết | Luật đó đọc là **không kiểm được** — không tính là đạt, cũng không tính là sai; nó rơi khỏi tổng số luật xét và người chơi thấy rõ nó rơi | J1 / UN-001, UN-007 |
| **Việc chấm điểm chưa xong tại thời điểm vũ trang** | Nguy cơ người chơi bấm khi chưa có thông tin — đúng thứ feature này sinh ra để tránh | Màn xác nhận **không mở ra trước khi có điểm**; không có trạng thái "đang tính" và không đoán bừa một con số. Nếu một luật không chấm được vì thiếu dữ liệu thì nó đọc là không kiểm được, chứ màn xác nhận không vì thế mà mở ra rỗng | J1 / UN-001 |
| **Điểm lúc vũ trang khác điểm lúc bắn** | Người chơi bấm dựa trên một con số, kết quả ghi lại một con số khác | Cả hai lần chấm đều giữ lại; bản ghi nêu rõ điểm nào là chính thức và điểm nào chỉ là tham khảo lúc vũ trang | J1 / UN-008 |
| **Playbook chưa có luật nào** (vừa tạo, soạn dở) | Nếu chọn được thì sẽ chấm 0 trên 0 — con số vô nghĩa trông như hoàn hảo | Lưu được để soạn tiếp sau, nhưng **không hiện trong menu chọn trên tay cầm** cho tới khi có ít nhất một luật. Nhờ vậy cảnh "0/0 đạt hết" không bao giờ xảy ra | J6, J8 / UN-003, UN-012 |
| **Playbook chỉ toàn luật tự-đánh-giá** | Màn xác nhận không có gì để hiện trước khi bấm | Nói rõ playbook này chỉ đối chiếu được sau khi lệnh đóng, thay vì hiện một con số rỗng | J1, J7 / UN-001, UN-009 |
| **Playbook khai áp cho cặp khác cặp đang giao dịch** | Chấm theo một sách không dành cho thị trường này | Coi như **một luật không đạt**, hiện trong cùng con số `n/m` như mọi luật khác; **không** cản lệnh và không sinh thêm loại cảnh báo riêng | J1 / UN-001, UN-002 |
| **Playbook đang dùng bị ngừng dùng ngay giữa phiên** | Đang chấm dở theo một sách vừa bị bỏ | Các lệnh đã chấm giữ nguyên; lần vũ trang tiếp theo chuyển về nhóm "ngoài kế hoạch" và nói rõ vì sao (🔶 xem A-09 — giữ nguyên tới hết phiên cũng là phương án hợp lý) | J3, J8 / UN-005, UN-011 |
| **Sửa luật xong nhưng chưa lưu, rồi quay lại giao dịch** | Tưởng đang chấm theo luật mới, thực ra theo luật cũ | Lệnh vẫn chấm theo luật đã lưu; trạng thái chưa lưu hiện rõ ở trang soạn | J6 / UN-004 |
| **Nhiều lệnh đóng liên tiếp** | Checklist chồng lên nhau giữa lúc còn phải nhìn thị trường | Các checklist xếp hàng theo thứ tự đóng, không cái nào chen ngang thao tác đang làm; cái nào chưa trả lời tới cuối phiên thì được gợi lại một lần, rồi thôi. Bỏ qua hết vẫn là lựa chọn hợp lệ | J7 / UN-009 |
| **Lệnh đóng khi người chơi đã rời máy** | Checklist hiện ra cho một lệnh đã quên mất bối cảnh | Checklist chờ ở hàng đợi và nêu rõ nó thuộc lệnh nào, lúc nào; trả lời muộn hoặc bỏ hẳn đều không bị phạt | J7 / UN-009 |
| **Đặt tên playbook trùng tên một playbook đã có** | Chọn nhầm sách lúc đang giao dịch | Chặn khi lưu và nói rõ tên đã tồn tại — trên tay cầm chỉ nhìn thấy tên, nên tên phải phân biệt được | J5 / UN-013, UN-006 |
| **Tham số của một luật vô lý** (ngưỡng âm, ngưỡng không bao giờ đạt được) | Luật chết — luôn đạt hoặc luôn fail mà người chơi không nhận ra | Chặn ngay tại trang soạn và nói rõ khoảng giá trị hợp lệ, trước khi luật đó kịp chấm một lệnh nào | J5 / UN-013 |
| **Tên hoặc mô tả playbook chứa ký tự đặc biệt** | Chữ mình gõ hiện ra thành thứ khác, và trên tay cầm chỉ nhìn thấy tên nên dễ chọn nhầm sách | Hiện đúng nguyên văn những gì người chơi gõ, ở mọi nơi nó xuất hiện — trang soạn, menu chọn trên tay cầm, màn xác nhận, và bản ghi lệnh cũ | J5, J1 / UN-013, UN-006 |
| **Bắn xong nhưng không rõ lệnh có tới sàn không** | Không biết điểm vừa chấm thuộc về một lệnh có thật hay không | Điểm của lần bắn đó vẫn được giữ và gắn với chính lần bắn đó, kể cả khi kết quả trên sàn còn chưa rõ; nó không biến mất và cũng không tự nhận là đã khớp | J1 / UN-001, UN-014, và `order-execution` UN-002 |
| **Người chơi ngừng dùng hết playbook, danh sách chọn rỗng** | Rơi vĩnh viễn vào nhóm "ngoài kế hoạch" mà không nhận ra | Nói rõ hiện không còn playbook nào chọn được và chỉ đường về trang soạn; mọi lệnh sau đó rơi vào nhóm "ngoài kế hoạch"; **không** tự dựng lại bộ mẫu mà người chơi đã chủ động bỏ | J3, J5, J8 / UN-003, UN-013 |
| **Lần bắn bị hạn mức rủi ro chặn** | Không rõ điểm vừa xem có được ghi lại hay mất luôn | Điểm của lần đó vẫn được ghi và xem lại được; người chơi thấy đồng thời điểm luật playbook và lý do bị hạn mức chặn, hai thứ không lẫn vào nhau | J2 / UN-002, UN-014 |
| **Playbook có luật nhưng không luật nào bắt buộc** | Điều kiện "đạt đủ luật bắt buộc" luôn đúng một cách rỗng — J4 sẽ báo ở mọi lần huỷ và mất hẳn tác dụng | Đọc là **chưa có luật bắt buộc nào để kết luận**, không đọc là đạt; J4 không hiện gì trong trường hợp này | J4 / UN-010, UN-013 |
| **Đổi playbook, hoặc mở menu an toàn, khi đang vũ trang** | Đang chấm dở theo một sách thì mẫu số đổi giữa chừng | Trạng thái vũ trang bị huỷ trước (luật của `order-execution`), nên không có chuyện một lần vũ trang bị chấm bằng hai sách. Lần vũ trang lại là một bản ghi mới, chấm theo sách mới | J1, J6 / UN-006, UN-008 |
| **Sửa hoặc đóng vị thế qua menu an toàn** | Không rõ những thao tác đó có bị chấm điểm không | Chỉ lần vũ trang và lần bắn mới sinh ra điểm; thao tác sửa mức bảo vệ hay đóng vị thế không tạo thêm bản ghi điểm nào | J1 / UN-001 |

## 7. User-side Constraints

* **Soạn playbook cần chuột và bàn phím** (xem A-01) — trang soạn không dùng được bằng tay cầm. Chỉ việc *chọn* playbook lúc giao dịch mới làm bằng tay cầm.
* **Luật tự động chỉ kiểm được những gì hệ thống quan sát được**: giá, đường trung bình, biên độ dao động, chênh lệch giá mua-bán, đồng hồ phiên, số vị thế đang mở, trạng thái quan sát của AI desk. Điều gì nằm ngoài danh sách đó phải khai thành luật tự-đánh-giá và trả lời sau lệnh.
* **Một playbook đang dùng tại một thời điểm** (xem A-02) — muốn chấm theo sách khác thì phải đổi trước khi vũ trang.
* Chỉ chạy trên Chrome desktop; người chơi phải giữ cửa sổ ở trạng thái focus trong suốt phiên (kế thừa ràng buộc của `order-execution`).
* Chỉ tài khoản demo. **Điểm số không phải lời khuyên đầu tư** — nó chỉ nói lệnh này có khớp luật do chính người chơi viết hay không.
* Giao diện sản phẩm bằng tiếng Anh; tài liệu nghiệp vụ bằng tiếng Việt.

## 8. Assumptions & Validation

| ID | Assumption | Impact if Wrong | Validation Status | Next Action |
|---|---|---|---|---|
| A-01 | Người chơi soạn playbook bằng chuột và bàn phím, ngoài lúc giao dịch | UN-012 sai; phải thiết kế cả đường soạn luật bằng tay cầm, tốn kém hơn nhiều | Chưa xác nhận — suy từ `phase-07` (`/playbooks` là trang web riêng, chỉ picker mới điều khiển bằng pad) | Hỏi người chơi khi viết SRS |
| A-02 | Một playbook đang dùng tại một thời điểm | Nếu muốn nhiều playbook cùng lúc, cách chấm và cách hiện điểm đổi hoàn toàn | Chưa xác nhận — suy từ `phase-07` ("the active playbook is part of session state") | Xác nhận trước khi chốt màn chọn playbook |
| A-03 | Danh sách bối cảnh kiểm tự động được là **đóng** (giá, trung bình động, biên độ, chênh lệch giá, đồng hồ phiên, vị thế mở, trạng thái AI desk) | Luật người chơi muốn nhưng không nằm trong danh sách phải hạ xuống thành tự-đánh-giá — có thể gây thất vọng khi soạn | Chưa xác nhận — liệt kê theo `phase-07` | Chốt danh sách khi viết SRS |
| A-04 | Người chơi chấp nhận trả lời checklist **sau khi lệnh đóng**, thay vì ngay lúc vào lệnh | Nếu thấy phiền và bỏ qua mọi lần, toàn bộ nhóm luật tự-đánh-giá thành vô dụng | **Đã xác nhận một phần** — thời điểm hỏi chốt 2026-08-28 (OQ-4: ngay khi đóng, xếp hàng, gợi lại cuối phiên). Việc người chơi chịu trả lời thật thì vẫn chưa kiểm được; `phase-07` nêu đúng rủi ro này ("checklist fatigue") | Theo dõi sau 10 phiên đầu; bỏ qua toàn bộ thì thiết kế lại cách hỏi |
| A-05 | "Đạt chuẩn" ở UN-010 nghĩa là đạt đủ các luật **bắt buộc**, không cần đạt luật không bắt buộc | Nếu người chơi hiểu là đạt *mọi* luật, thông tin ở J4 sẽ hiện quá thường xuyên và mất tác dụng | 🔶 Quyết định thay user 2026-08-28 — người chơi đã chốt *nguyên tắc* chỉ-hiện-khi-đạt-chuẩn, nhưng chưa chốt *định nghĩa* đạt chuẩn | Xác nhận với người chơi |
| A-08 | Feature này **không tự đo được thành công của chính nó** — cả hai USC đọc từ bề mặt thuộc `process-score` | `process-score` trượt lịch thì USC-001/USC-002 không đo được, và feature chạy mà không biết mình có hiệu quả không | Đây là hệ quả trực tiếp của ranh giới đã chốt ở Mục 3 | Chấp nhận, hoặc thống nhất một cách đọc thô tạm thời khi viết SRS |
| A-09 | Playbook đang dùng bị ngừng dùng giữa phiên thì lần vũ trang sau rơi về nhóm "ngoài kế hoạch" | Người chơi có thể bất ngờ mất nhãn playbook giữa buổi; phương án "giữ nguyên tới hết phiên" cũng hợp lý không kém | 🔶 Quyết định thay user 2026-08-28 — `phase-07` chỉ nói ngừng dùng thì ẩn khỏi danh sách chọn, không nói gì về playbook đang hoạt động | Xác nhận với người chơi |
| A-06 | Việc chấm điểm luôn xong kịp để màn xác nhận mở ra được ngay khi người chơi vũ trang | Nếu chấm chậm, màn xác nhận mở muộn — người chơi mất phản hồi tức thì của nút bấm, và nhịp thao tác trên tay cầm bị đứt | **Đã xác nhận cách xử lý** 2026-08-28 (OQ-1: điểm là một phần của màn xác nhận, không có trạng thái "đang tính"). Việc chấm có đủ nhanh để không làm chậm màn xác nhận thì chưa kiểm được | Đo độ trễ mở màn xác nhận khi có sản phẩm; chậm rõ rệt thì đặt lại lựa chọn này |
| A-07 | Người chơi khai luật bằng cách **chọn từ danh sách luật có sẵn rồi đặt tham số**, không viết luật tự do bằng lời | Nếu người chơi kỳ vọng viết luật tự do, phần lớn luật của họ sẽ rơi vào nhóm tự-đánh-giá và mất khả năng hiện trước khi bấm | Chưa xác nhận — suy từ `phase-07` ("`code` references a registry entry, `params` parameterises it") | Xác nhận khi thiết kế trang soạn, xem OQ-6 |

## 9. User Success Criteria

| ID | User Outcome | Baseline | Target | Measurement | Review Period |
|---|---|---|---|---|---|
| USC-001 | Người chơi ngày càng giao dịch theo sách của chính mình, thay vì tuỳ hứng | **Chưa có** — xác lập tỷ lệ trung bình từ 10 phiên đầu | Tỷ lệ lệnh gắn với một playbook (không thuộc nhóm "ngoài kế hoạch") cao hơn baseline sau 3 tháng. **Chưa có sàn tối thiểu** — xem OQ-2 | Đếm số lệnh theo nhóm playbook so với nhóm "ngoài kế hoạch", đọc cuối mỗi tháng. **Không tính vào tử số** những lệnh mà chính luật "cặp nằm trong danh sách playbook khai" không đạt — chọn một playbook đầu phiên rồi bắn mọi thứ dưới nó không làm con số này đẹp lên | Hằng quý |
| USC-002 | Chất lượng tuân thủ luật đi lên, không phải điểm đi lên nhờ nới luật | **Chưa có** — xác lập tỷ lệ trung bình từ 10 phiên đầu | Trong số lệnh có playbook, tỷ lệ đạt đủ **luật bắt buộc** cao hơn baseline sau 3 tháng, **đồng thời** số luật bắt buộc trung bình mỗi playbook không giảm so với baseline | Đọc tỷ lệ đạt đủ luật bắt buộc cuối mỗi tháng, kèm **số luật bắt buộc trung bình** của các playbook đang dùng và **số lần sửa tham số luật theo hướng lỏng hơn** trong kỳ. Ba số liệu đi cùng nhau để việc bớt luật hoặc nới ngưỡng không tự động thành "tiến bộ" | Hằng quý |

> **Cả hai thước đo đọc từ bề mặt thuộc `process-score`** (xem A-08) — feature này tạo ra dữ liệu
> nhưng không tự đọc được nó thành xu hướng.
>
> **Giới hạn đã biết của hai thước đo này.** Cả hai đọc từ chính luật do người chơi tự khai, nên
> chúng đo *sự nhất quán với sách của mình*, không đo *chất lượng của cuốn sách*. Cụ thể: USC-002
> chặn được việc bớt luật cho dễ đạt (vế "số luật bắt buộc trung bình không giảm"), nhưng **không**
> chặn được việc thêm luật bắt buộc gần như luôn đúng để pha loãng một hai luật thật sự khó. Xem OQ-7.

## 10. Open Questions

* [x] OQ-1: Điểm phải hiện trong bao lâu thì coi là "kịp"? — **Resolved:** không đặt ngưỡng thời gian, vì điểm là một phần của chính màn xác nhận — màn này không mở ra khi chưa có điểm. Đổi lại, việc chấm phải đủ nhanh để không làm chậm màn xác nhận (xem A-06).
* [ ] OQ-2: Tỷ lệ lệnh có playbook có sàn tối thiểu không, hay chỉ cần "cao hơn baseline"? Không có sàn thì USC-001 vẫn đạt kể cả khi tỷ lệ tuyệt đối rất thấp.
* [x] OQ-3: Playbook không có luật nào xử thế nào? — **Resolved:** lưu được (để soạn dở rồi quay lại), nhưng không hiện trong menu chọn trên tay cầm cho tới khi có ít nhất một luật. Nên không bao giờ có lệnh nào bị chấm bởi một playbook rỗng.
* [x] OQ-4: Checklist sau lệnh đóng hỏi lúc nào? — **Resolved:** hỏi ngay khi lệnh đóng để bối cảnh còn nóng, nhưng xếp hàng và không bao giờ chen ngang thao tác đang làm; phần còn tồn đọng được gợi lại một lần vào cuối phiên.
* [x] OQ-5: Playbook khai cặp A nhưng bắn cặp B thì sao? — **Resolved:** coi như một luật không đạt, nằm trong cùng con số `n/m`. Không sinh thêm loại cảnh báo riêng, và không cản lệnh.
* [ ] OQ-6: Người chơi có tự khai được một luật kiểu hoàn toàn mới không, hay chỉ chọn từ danh sách luật có sẵn rồi đặt tham số? Xem A-07.
* [ ] OQ-7: Có cần cảnh báo (không chặn) khi một luật bắt buộc **gần như luôn đạt** trong lịch sử không? Không có gì nhắc thì thêm luật dễ là cách làm đẹp USC-002 mà chất lượng thật không đổi. Xem ghi chú giới hạn ở Mục 9.
* [x] OQ-8: Bộ đếm tự huỷ tính **mọi** lần huỷ chủ động hay chỉ khi đang có điều kiện đứng-ngoài? — **Resolved 2026-08-28** (chốt tại `process-score` OQ-3): bộ đếm trên màn chính giữ **luật rộng** — mọi lần tự huỷ chủ động, đúng như `order-execution` UN-006; `process-score` chỉ quy điểm trên **tập con** những lần huỷ xảy ra lúc đang có điều kiện đứng ngoài. Một bộ đếm gốc, hai cách đọc. **Lập luận của UN-010 vẫn đứng vững** — bộ đếm đã ghi nhận mọi lần tự kiềm chế, nên phần điểm gắn với một lần huỷ là lớp thông tin thêm, không phải lớp duy nhất.

---

> **Lịch sử review:** chốt OQ-1, OQ-3, OQ-4, OQ-5 ngày 2026-08-28 (`/urd` Phase E). Review bởi
> `@senior-ba` (block: 6 blocking, 12 warning, 7 suggestion) và `@po-reviewer` (0 blocking,
> 2 warning, 3 suggestion) cùng ngày; findings đã áp vào Mục 1, 3, 4, 5, 6, 7, 8, 9 và sinh thêm
> UN-013, UN-014, Journey 5, A-08, A-09, OQ-7, OQ-8.
