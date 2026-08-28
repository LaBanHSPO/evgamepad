---
type: urd
feature: order-execution
status: in-review
updated: 2026-08-28
links: ["[[project-profile]]", "[[system-overview]]", "[[definitions]]", "[[operating-environment]]", "[[ai-desk-urd]]", "[[playbook-grading-urd]]"]
---

# order-execution — User Requirements Document

## 1. Purpose

Ghi lại nhu cầu của người chơi quanh việc đưa một ý định giao dịch từ tay cầm tới tài khoản demo
cTrader **một cách an toàn và biết chắc kết quả** — và quan trọng không kém, quanh việc **không**
đưa nó đi.

Feature này là đường đi nóng của sản phẩm: mọi thứ khác (AI desk, nhật ký, chấm điểm) đứng bên lề nó.
Vì vậy nhu cầu trung tâm ở đây không phải "vào lệnh nhanh" mà là **"không bao giờ vào một lệnh mình
không thực sự muốn, và luôn biết mình đang ở đâu"**.

### User Problem & Current Experience

| User | Current Situation | Problem | User Consequence | Evidence |
|---|---|---|---|---|
| Người chơi | Giao dịch demo bằng cTrader web/desktop với chuột | Không có ma sát nào chặn một cú click bốc đồng — một cú nhấp là một lệnh | Vào lệnh khi chưa thực sự quyết định; sau phiên không phân biệt được lệnh có kế hoạch với lệnh bốc đồng | Confirmed (người chơi xác nhận 2026-08-28) |
| Người chơi | Giao diện broker hiển thị lãi/lỗ bằng tiền, luôn hiện | Số tiền đập vào mắt khi đang có vị thế, kéo sự chú ý khỏi quy trình | Đóng lệnh sớm khi đang xanh, gồng lệnh khi đang đỏ — quyết định bị tiền dẫn dắt thay vì bị luật dẫn dắt | Observed: `README.md`, `story.md` §1; `plans/.../phase-03` |
| Người chơi | Việc **từ chối** một setup không để lại dấu vết nào trong công cụ hiện tại | Kỷ luật là thứ vô hình — không được đếm, không được thấy | Không có phản hồi tích cực nào cho hành vi đúng nhất trong giao dịch; sự tự kiềm chế cảm thấy như "không làm gì" thay vì như một chiến thắng | Observed: `story.md` §1 |
| Người chơi | Thao tác bằng chuột trên nhiều cửa sổ | Đứt đoạn giữa lúc nhìn biểu đồ và lúc thao tác đặt lệnh | Mất nhịp quan sát tape ở đúng thời điểm cần quan sát nhất | Assumption — xem A-06 Mục 8 |

## 2. User Types

| Tier | User Type | Context | Primary Goal | Pain Points |
|---|---|---|---|---|
| primary | **Người chơi** | Một buổi tối, một mình, trước màn hình desktop với tay cầm 8BitDo trong tay. Tài khoản demo, không có tiền thật | Ra được những quyết định mình tự hào vào sáng hôm sau — kể cả (và nhất là) những quyết định *không vào lệnh* | Bốc đồng; bị tiền phân tán; không thấy kỷ luật của mình được ghi nhận; sợ lỡ tay khi thao tác |

> **Không có secondary user.** Công cụ cá nhân một người dùng. AI desk và sàn cTrader/Spotware là
> **actor hệ thống**, không phải người dùng — xem `docs/_shared/project-profile.md`.

## 3. Scope Boundaries

### In Scope

* Người chơi mở, khoá và mở khoá lại một phiên giao dịch, và tự đặt hạn mức ràng buộc chính mình trước khi bắt đầu. Phiên kết thúc khi người chơi tự đóng **hoặc** khi hết khung giờ đã đặt; hạn mức được đặt lại ở phiên kế tiếp.
* Người chơi chọn cặp tiền, khối lượng, khung thời gian mà không có rủi ro vô tình vào lệnh.
* Người chơi vũ trang (ARM) một hướng, xem lại nó, rồi **hoặc bắn hoặc từ chối** — và việc từ chối chủ động được đếm.
* Người chơi biết chắc chắn một lệnh đã tới sàn hay chưa, kể cả khi phản hồi chậm hoặc mất.
* Người chơi thấy dữ liệu thị trường (giá, biểu đồ, tình trạng vị thế) đủ để ra quyết định, và biết khi nào dữ liệu đó không còn đáng tin.
* Người chơi chọn đúng vị thế muốn tác động khi có nhiều vị thế đang mở.
* Người chơi sửa mức bảo vệ (SL/TP) của một vị thế đang mở mà không sợ thao tác đó tự gửi đi.
* Người chơi đóng một vị thế theo kế hoạch, hoặc thoát toàn bộ khẩn cấp, **kể cả khi tay cầm hoặc kết nối đã hỏng**.
* Người chơi biết ngay khi một vị thế kết thúc mà không do mình bấm, và biết vì sao.
* Người chơi mở menu/cài đặt giữa phiên mà không có khả năng mở nhầm một lệnh.
* Người chơi thấy trạng thái vị thế của mình bằng đơn vị rủi ro thay vì bằng tiền, theo mặc định.

### Out of Scope

* **Đo trạng thái tâm lý và ma sát thích ứng** (bao gồm cả việc quyết định khi nào siết độ trễ xác nhận) → feature `tilt-meter`.
* **Nghi thức chuẩn bị trước phiên và tự đánh giá đầu/cuối buổi** (check-in 1–5) → feature `daily-journal`. URD này chỉ nhận phần **hạn mức + khoá phiên**.
* **Nơi cộng dồn số lần từ chối qua nhiều phiên** → feature `process-score` *(chốt 2026-08-28)*. URD này chỉ nhận bộ đếm **theo phiên** trên màn hình chính, và nó giữ nguyên luật rộng của UN-006: đếm **mọi** lần tự huỷ chủ động. `process-score` chỉ quy điểm trên **tập con** những lần huỷ xảy ra lúc đang có điều kiện đứng ngoài — nên mỗi lần huỷ cần ghi kèm lúc đó có điều kiện đứng ngoài hay không. Một bộ đếm gốc, hai cách đọc; không có bộ đếm thứ hai.
* **Tư vấn, tín hiệu, phân tích của AI desk** → feature `ai-desk`.
* **Ghi âm lý do vào lệnh** → feature `voice-journal`.
* **Chấm điểm lệnh theo luật playbook** → feature `playbook-grading`.
* **Tua lại lệnh qua tape** → feature `trade-replay`.
* **Báo cáo, xuất dữ liệu, sao lưu** → feature `reports-export`.
* Giao dịch tiền thật, lệnh chờ (pending order), đóng một phần vị thế.

## 4. User Needs

| ID | User | Context / Trigger | User Need | Expected Outcome | Importance | Evidence |
|---|---|---|---|---|---|---|
| UN-001 | Người chơi | Bất kỳ lúc nào tay đang đặt trên tay cầm | Không bao giờ phát sinh một lệnh mà mình không chủ động quyết định | Không có lệnh nào vào sàn do lỡ tay, giữ nút, cần analog trôi, hay bấm nhầm tổ hợp | Critical | Observed: `phase-03` ("analog sticks never submit orders", "held buttons do not spray orders") |
| UN-002 | Người chơi | Ngay sau khi bấm xác nhận | Biết chắc lệnh đã tới sàn hay chưa, không bao giờ ở trạng thái mơ hồ | Nhận phản hồi rõ ràng cho: đã khớp, bị từ chối, hoặc *chưa rõ*. Khi chưa rõ, **quyền mở lệnh mới bị khoá** và trạng thái cuối cùng tự hiện ra khi kết nối ổn định, người chơi không phải tự đi kiểm tra. Người chơi vẫn được chủ động bỏ qua để mở lại quyền bắn, sau một cảnh báo nêu rõ rủi ro có hai vị thế thay vì một | Critical | Observed: `phase-03` ("block new fire until cid resolves"); bỏ-qua-mở-lại-quyền-bắn: Confirmed 2026-08-28 (OQ-3) |
| UN-003 | Người chơi | Đang có vị thế mở thì tay cầm hết pin, rút dongle, tab mất focus, hoặc mạng rớt | Luôn thoát được vị thế bất kể thiết bị hay kết nối hỏng | Có ít nhất một đường đóng vị thế không phụ thuộc tay cầm; lệnh mở mới bị khoá nhưng lệnh đóng và thoát khẩn cấp thì không | Critical | Observed: `phase-03` (HUD Flatten không cần pad), `phase-02` ("3s silence → opens reject; close/panic still allowed") |
| UN-004 | Người chơi | Trước khi bắt đầu một buổi | Tự ràng buộc mình bằng hạn mức do chính mình đặt, khi đầu còn tỉnh | Khai được hai loại ràng buộc, và hệ thống giữ chúng thay mình khi đầu không còn tỉnh. **Loại thi hành** — khung giờ phiên, khối lượng tối đa, số vị thế tối đa, mức lỗ tối đa của phiên — hệ thống **từ chối** hành động vượt quá. **Loại chỉ cảnh báo** — ngưỡng báo trước sự kiện tin (xem `ai-desk` UN-002) — hệ thống **nói rõ nhưng không bao giờ từ chối** một lệnh vì nó; quyền quyết định vẫn của người chơi. Mỗi ô hạn mức được xét độc lập: sửa theo hướng **siết chặt** có hiệu lực ngay và chỉ chi phối hành động mới (không ép đóng vị thế đang có); sửa theo hướng **nới lỏng** chỉ có hiệu lực từ phiên sau | Critical | Confirmed 2026-08-28 (OQ-2); phạm vi phiên: Confirmed 2026-08-28 (OQ-1) |
| UN-005 | Người chơi | Đang có vị thế mở | Không bị con số tiền kéo sự chú ý khỏi quy trình | Lãi/lỗ hiển thị theo **đơn vị rủi ro (R)** làm mặc định; muốn xem tiền phải qua một thao tác bật có chủ ý | High | Observed: `README.md`, `phase-03` |
| UN-006 | Người chơi | Vừa vũ trang một hướng rồi **chủ động** quyết định không vào (nhả chốt hoặc bấm huỷ, trong lúc còn giữ được quyền quyết định) | Thấy sự tự kiềm chế của mình được ghi nhận như một thành tích, không phải như sự vắng mặt | Bộ đếm tăng lên ngay và hiển thị nổi bật **theo phiên**. Huỷ vũ trang do mất tay cầm, mất focus cửa sổ, hoặc do mở menu **không** làm tăng bộ đếm — chỉ quyết định của người chơi mới được tính | High | Observed: `story.md` §1, `phase-03` ("Cancelling an arm **during a stand-down condition** increments the stood-down counter") |
| UN-007 | Người chơi | Vị thế đang mở, muốn dời mức cắt lỗ hoặc chốt lời | Sửa mức bảo vệ mà không sợ thao tác chỉnh tay tự gửi đi | Thao tác chỉnh chỉ tạo ra một **bản xem trước**; nó chỉ tới sàn sau một lần xác nhận hai tay riêng biệt | High | Observed: `phase-03` ("an SL/TP edit only stages a modify preview"), `phase-02` |
| UN-008 | Người chơi | Suốt phiên | Thực hiện được **trên tay cầm** trọn bộ thao tác của một phiên, không phải chuyển sang chuột giữa chừng | Làm được bằng tay cầm: chọn cặp, khối lượng, khung thời gian, vũ trang, bắn, huỷ, chọn vị thế, đóng vị thế, **thoát khẩn cấp**, **khoá/mở khoá phiên**, mở menu, và **mở bàn làm việc AI rồi đặt câu hỏi** (xem `ai-desk` Journey 4). Danh sách này là đóng | High | Observed: `phase-03` (bản đồ nút đầy đủ). Phần *tiện lợi thuần* (chọn cặp / khối lượng / khung thời gian) dựa trên A-06 chưa xác nhận — xem Mục 8 |
| UN-009 | Người chơi | Cần mở cài đặt hoặc xem thông tin giữa phiên | Vào menu mà không có khả năng vô tình mở một lệnh | Mở menu tự huỷ trạng thái đã vũ trang và khoá việc mở lệnh mới; điều hướng trong menu về nguyên tắc không phát ra được lệnh nào | Medium | Observed: `phase-03` (GameOverlay "cannot emit intent.open or intent.modify") |
| UN-010 | Người chơi | Ngoài khung giờ đã tự đặt, hoặc đã chạm mức lỗ tối đa của phiên | Được chặn lại đúng lúc mình dễ phá luật nhất | Hệ thống từ chối mở lệnh mới và nói rõ đã chạm hạn mức nào; việc đóng vị thế đang có vẫn luôn được phép | Medium | Observed: `phase-02` ("ICT session window; daily loss close-only") |
| UN-011 | Người chơi | Sau khi thoát khẩn cấp, hoặc sau khi tự khoá phiên giữa chừng | Hiểu rõ mình đang bị khoá, ra khỏi khoá bằng cách nào, và việc ra khỏi khoá **không** xoá sạch ràng buộc mình đã tự đặt | Trạng thái khoá hiện rõ và nói rõ cái gì còn dùng được. Mở khoá lại được trong cùng phiên bằng một thao tác có chủ ý, nhưng **hạn mức đã tiêu không được đặt lại** — lỗ đã lỗ, thời gian đã trôi | Critical | Observed: `phase-03` (`View` = session lock/unlock). Quy tắc không-reset: 🔶 quyết định thay user 2026-08-28 |
| UN-012 | Người chơi | Vị thế kết thúc mà không do mình bấm — chạm cắt lỗ, chạm chốt lời, hoặc bị sàn đóng | Biết ngay điều đó vừa xảy ra và biết vì sao, không phát hiện muộn khi nhìn lại màn hình | Thông báo rõ ràng ngay khi vị thế biến mất, kèm lý do và kết quả. Nếu người chơi vừa xác nhận đóng hoặc sửa cho một vị thế **đã không còn tồn tại**, hệ thống nói rõ "vị thế không còn" thay vì im lặng hoặc báo lỗi mơ hồ | Critical | Suy từ `phase-02` (position_event fill/SL/TP/close, trade_closed row). 🔶 bổ sung sau review `@senior-ba` |
| UN-013 | Người chơi | Có từ hai vị thế mở trở lên | Chọn đúng vị thế mình muốn tác động, và biết chắc mình đang tác động vào cái nào | Thấy danh sách vị thế đang mở; vị thế đang được chọn hiện rõ ràng; mọi thao tác đóng hoặc sửa bảo vệ đều nêu rõ nó áp cho vị thế nào trước khi xác nhận | High | Suy từ UN-004 ("số vị thế tối đa" ngụ ý > 1). 🔶 bổ sung sau review `@senior-ba` |

## 5. Prioritized User Journeys

### Journey 1: Mở phiên và vào lệnh đầu tiên

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Bắt đầu buổi tối, muốn bắt đầu giao dịch
* __Expected outcome:__ Có một vị thế demo đúng hướng, đúng khối lượng, đúng cặp, và người chơi biết chắc nó đã tồn tại trên sàn
* __Related needs:__ UN-001, UN-002, UN-004, UN-008

1) Người chơi mở phiên và xác nhận hạn mức của mình cho buổi tối này.
2) Chọn cặp tiền và khối lượng bằng tay cầm.
3) Giữ chốt an toàn bằng một tay, vũ trang một hướng bằng tay kia.
4) Xem lại bản tóm tắt lệnh sắp gửi, gồm mức bảo vệ dự kiến và rủi ro tương ứng.
5) Xác nhận bằng thao tác hai tay.
6) Nhận phản hồi rung và hiển thị cho biết lệnh đã khớp.

__Independent verification:__ Mở giao diện cTrader demo bằng đường khác và thấy đúng một vị thế mới,
đúng cặp, đúng hướng, đúng khối lượng. Không cần bất kỳ journey nào khác để xác nhận điều này.

### Journey 2: Thoát khẩn cấp khi mọi thứ hỏng

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Đang có vị thế mở thì tay cầm mất kết nối, hoặc người chơi hoảng và muốn ra khỏi thị trường ngay
* __Expected outcome:__ Không còn vị thế nào mở, và phiên bị khoá lại
* __Related needs:__ UN-003, UN-008, UN-011

1) Người chơi nhận ra cần thoát ngay.
2) Dùng nút thoát khẩn cấp trên tay cầm — hoặc, nếu tay cầm đã hỏng, dùng nút thoát trên màn hình bằng chuột hoặc bàn phím.
3) Hệ thống đóng toàn bộ vị thế rồi khoá phiên.
4) Người chơi thấy xác nhận rằng không còn gì đang mở, và thấy rõ mình đang ở trạng thái khoá.

__Independent verification:__ Rút dongle rồi bấm nút thoát trên màn hình; kiểm tra trên cTrader demo
thấy không còn vị thế nào. Journey được kiểm chứng độc lập nhất — nó phải hoạt động cả khi mọi
journey khác đã hỏng.

### Journey 3: Từ chối một setup

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Đã vũ trang một hướng, nhìn lại và thấy setup không đạt tiêu chuẩn của mình
* __Expected outcome:__ Không có lệnh nào được gửi, và sự từ chối đó được đếm và hiển thị như một điểm cộng
* __Related needs:__ UN-001, UN-006

1) Người chơi đang ở trạng thái đã vũ trang, và vẫn đang giữ được quyền quyết định.
2) Người chơi nhả chốt an toàn, hoặc bấm huỷ.
3) Trạng thái vũ trang biến mất; không có gì được gửi đi.
4) Bộ đếm số lần từ chối của phiên tăng thêm một, hiển thị nổi bật trên màn hình.

__Independent verification:__ Đếm số lần từ chối trên màn hình trước và sau; đối chiếu với cTrader
demo để xác nhận không có lệnh nào phát sinh trong khoảng đó. Đồng thời kiểm tra ngược: rút dongle
khi đang vũ trang, bộ đếm **không** được tăng. Journey mang giá trị cốt lõi của sản phẩm — kiểm
chứng được mà không cần vào lệnh nào.

### Journey 4: Mất kết nối khi đang có vị thế

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Mạng rớt, tab bị ẩn, hoặc tay cầm rớt kết nối trong lúc đang có vị thế mở
* __Expected outcome:__ Người chơi hiểu ngay mình đang ở trạng thái nào và làm gì được, không bị mất vị thế trong im lặng
* __Related needs:__ UN-002, UN-003, UN-010, UN-011

1) Sự cố xảy ra.
2) Màn hình chuyển sang trạng thái khoá rõ ràng, nói rõ cái gì còn dùng được.
3) Việc mở lệnh mới bị chặn; việc đóng vị thế và thoát khẩn cấp vẫn dùng được.
4) Khi kết nối trở lại, người chơi thấy đúng tình trạng vị thế thật trên sàn, kể cả khi nó đã thay đổi lúc mất kết nối.
5) Nếu có một lệnh đã gửi mà chưa rõ kết quả, trạng thái cuối cùng của nó tự hiện ra; quyền mở lệnh mới vẫn khoá cho tới khi sáng tỏ, hoặc cho tới khi người chơi chủ động bỏ qua sau cảnh báo.

__Independent verification:__ Ngắt mạng khi đang có vị thế, thử mở lệnh mới (phải bị từ chối), thử
đóng vị thế (phải được phép); nối lại mạng và so tình trạng hiển thị với cTrader demo.

### Journey 5: Đóng vị thế theo kế hoạch

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Vị thế đã đạt điều kiện thoát mà người chơi đặt ra từ đầu — chốt lời, cắt lỗ chủ động, hoặc hết lý do giữ
* __Expected outcome:__ Vị thế đã chọn được đóng hoàn toàn, người chơi thấy kết quả bằng đơn vị rủi ro
* __Related needs:__ UN-005, UN-008, UN-012, UN-013

1) Người chơi quyết định thoát.
2) Nếu có nhiều vị thế mở, chọn đúng vị thế muốn đóng — màn hình cho thấy rõ đang chọn cái nào.
3) Xác nhận đóng bằng thao tác trên tay cầm.
4) Vị thế biến mất khỏi danh sách; kết quả hiện ra theo đơn vị rủi ro (R), tiền vẫn nằm sau một thao tác bật.

__Independent verification:__ Với hai vị thế mở, đóng một cái; kiểm tra trên cTrader demo thấy đúng
cái đó biến mất và cái còn lại nguyên vẹn.

### Journey 6: Sửa mức bảo vệ của vị thế đang mở

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Vị thế đã đi được một đoạn, người chơi muốn dời cắt lỗ hoặc chốt lời
* __Expected outcome:__ Mức bảo vệ mới có hiệu lực trên sàn, và người chơi đã chủ động xác nhận nó
* __Related needs:__ UN-007, UN-009, UN-013

1) Người chơi mở menu an toàn — trạng thái vũ trang (nếu có) bị huỷ, việc mở lệnh mới bị khoá.
2) Chọn vị thế cần sửa nếu có nhiều hơn một.
3) Chỉnh mức cắt lỗ hoặc chốt lời; màn hình cho thấy rủi ro và mục tiêu tương ứng thay đổi theo.
4) Áp dụng thay đổi — hệ thống chỉ tạo ra một bản xem trước đang chờ, chưa gửi đi.
5) Người chơi quay lại màn hình chính và xác nhận bằng thao tác hai tay.
6) Mức bảo vệ mới có hiệu lực trên sàn.

__Independent verification:__ Kiểm tra trên cTrader demo thấy mức SL/TP mới; và kiểm tra rằng khi
dừng ở bước 4 (không làm bước 5) thì mức trên sàn **không** đổi.

## 6. User Exceptions & Edge Conditions

| Situation | User Impact | Expected User-facing Outcome | Related Journey / Need |
|---|---|---|---|
| Rút dongle hoặc hết pin tay cầm khi đang vũ trang | Mất quyền điều khiển giữa một thao tác nhạy cảm | Trạng thái vũ trang bị huỷ ngay, không chờ; báo mất tay cầm; đường thoát bằng chuột/phím hiện rõ. Bộ đếm từ chối **không** tăng | J2, J4 / UN-001, UN-006 |
| Tab mất focus | Không còn nhìn thấy thị trường nhưng vị thế vẫn sống | Trạng thái vũ trang bị huỷ ngay; mở lệnh mới bị khoá; quay lại thấy rõ mình bị khoá và vì sao. Bộ đếm từ chối **không** tăng | J4 / UN-001, UN-006, UN-009 |
| Kết nối im lặng quá ngưỡng khi đang có vị thế | Nguy cơ "mù" trong khi tiền đang chạy | Tự khoá mở lệnh mới; đóng vị thế và thoát khẩn cấp vẫn được phép | J4 / UN-003 |
| Đã gửi lệnh nhưng không có phản hồi trong thời gian hợp lý | Không biết mình có vị thế hay không — trạng thái nguy hiểm nhất | Nói rõ "chưa rõ kết quả", **không** đoán bừa; mở lệnh mới bị khoá; trạng thái cuối tự hiện ra khi kết nối ổn định. Người chơi bỏ qua được, sau cảnh báo nêu rõ rủi ro hai vị thế | J1, J4 / UN-002 |
| **Vị thế đóng do chạm SL/TP hoặc bị sàn đóng** | Vị thế biến mất mà người chơi không bấm gì | Thông báo ngay kèm lý do và kết quả; không để người chơi tự phát hiện | J5 / UN-012 |
| **Xác nhận đóng/sửa cho vị thế vừa không còn tồn tại** | Thao tác rơi vào khoảng trống | Nói rõ "vị thế không còn" và vì sao, thay vì im lặng hoặc báo lỗi mơ hồ | J5, J6 / UN-012 |
| Sàn bảo trì hoặc không phản hồi | Không giao dịch được | Báo trạng thái bảo trì và khoá mở lệnh; **không** hiển thị giá bịa | J4 / UN-002 |
| **Giá ngừng cập nhật dù kết nối vẫn còn** | Nguy hiểm hơn mất kết nối — người chơi bắn theo một mức giá đã chết | Đánh dấu rõ dữ liệu giá là cũ và chặn mở lệnh mới cho tới khi giá sống lại | J1 / UN-002 |
| Chạm mức lỗ tối đa của phiên | Đúng lúc người chơi dễ gỡ gạc nhất | Từ chối mở lệnh mới, nói rõ đã chạm hạn mức nào; đóng vị thế vẫn được phép | J4 / UN-004, UN-010 |
| **Hết khung giờ phiên khi vẫn còn vị thế mở** | Nguy cơ để vị thế qua đêm không người trông | Chuyển sang chỉ-được-đóng và cảnh báo rõ còn vị thế mở; **không** tự đóng thay người chơi. Phiên chỉ thực sự kết thúc khi không còn vị thế nào | J4, J5 / UN-010, UN-011 |
| Ngoài khung giờ phiên đã tự đặt | Cám dỗ giao dịch ngoài kế hoạch | Từ chối mở lệnh mới kèm lý do; đóng vị thế vẫn được phép | J1 / UN-004, UN-010 |
| **Không mở được phiên vì tài khoản chưa sẵn sàng** (chưa kết nối được sàn, phiên đăng nhập hết hạn, tài khoản không phải demo) | Ngồi xuống đúng giờ mà không bắt đầu được | Nói rõ lý do cụ thể và việc cần làm tiếp; **không** vào trạng thái nửa vời trông như đã sẵn sàng | J1 / UN-004 |
| **Chưa có dữ liệu giá lúc vừa mở phiên** | Không có gì để ra quyết định | Nói rõ đang chờ dữ liệu; mở lệnh bị chặn cho tới khi có giá | J1 / UN-002 |
| **Bấm đóng hoặc thoát khẩn cấp khi không có vị thế nào** | Thao tác rơi vào khoảng trống | Xác nhận nhẹ nhàng "không có gì để đóng"; không báo lỗi, không đổi trạng thái khoá ngoài dự kiến | J2, J5 / UN-003 |
| **Khối lượng không hợp lệ** (dưới mức tối thiểu, sai bước nhảy của sàn, hoặc vượt chính hạn mức mình đặt) | Lệnh không thể thực hiện được | Chặn ngay tại chỗ trước khi vũ trang, nói rõ giới hạn hợp lệ là bao nhiêu | J1 / UN-004 |
| **Mức bảo vệ không hợp lệ** (đặt về phía sai, hoặc quá sát giá hiện tại) | Bảo vệ vô nghĩa hoặc bị sàn từ chối | Chặn tại bản xem trước và nói rõ vì sao, trước khi tới bước xác nhận | J6 / UN-007 |
| **Khung giờ phiên nhập ngược** (giờ kết thúc trước giờ bắt đầu) | Hạn mức tự đặt trở nên vô nghĩa | Chặn khi lưu và nói rõ chỗ sai | J1 / UN-004 |
| **Ngưỡng cảnh báo tin không hợp lệ** (bằng 0, âm, hoặc dài hơn cả phiên) | Cảnh báo hoặc không bao giờ kêu, hoặc kêu suốt | Chặn khi lưu và nói rõ khoảng hợp lệ. Chưa khai thì dùng mặc định 15 phút | J1 / UN-004 |
| **Siết hạn mức xuống dưới trạng thái đang có** (hạ khối lượng/số vị thế tối đa thấp hơn cái đang mở) | Có thể tưởng hệ thống sẽ ép đóng bớt | Hạn mức mới chỉ chi phối hành động mới; vị thế đang có không bị ép đóng; nói rõ điều đó khi lưu | J1 / UN-004 |
| Giữ nút vũ trang quá lâu | Nguy cơ phát sinh hàng loạt lệnh | Đúng một lệnh cho một lần xác nhận | J1 / UN-001 |
| Cần analog bị trôi khi để yên | Nguy cơ vào lệnh không chủ ý | Cần analog không bao giờ gửi được lệnh; chúng chỉ đổi bản xem trước | J1, J6 / UN-001, UN-007 |
| Bấm nhầm tổ hợp hai nút vai khi định đổi khung thời gian | Thao tác không như mong đợi | Xấu nhất chỉ là đổi nhầm khung nhìn biểu đồ — không bao giờ ảnh hưởng tới một vị thế | J1 / UN-001 |
| Mở menu trong lúc đang vũ trang | Có thể quên mất mình đang vũ trang | Trạng thái vũ trang bị huỷ khi menu mở; người chơi thấy rõ. Bộ đếm từ chối **không** tăng | J6 / UN-006, UN-009 |
| Bấm xác nhận hai lần do sốt ruột | Nguy cơ vào hai vị thế thay vì một | Chỉ một vị thế được tạo; lần bấm thừa không sinh thêm gì | J1 / UN-001, UN-002 |

## 7. User-side Constraints

* Người chơi phải giữ cửa sổ Chrome ở trạng thái focus trong suốt phiên — mất focus là mất quyền mở lệnh. Ràng buộc này phải được nhắc rõ cho người chơi.
* Tay cầm nối qua dongle 2.4G là đường chính; dây USB là dự phòng. **Bluetooth không dùng được** vì máy hiện tại chưa đạt phiên bản hệ điều hành yêu cầu.
* Chỉ chạy trên Chrome desktop. Rung tay cầm có thể không có trên trình duyệt khác — khi đó phản hồi bằng hình ảnh là chính thức.
* Chỉ tài khoản demo. Người chơi không được kỳ vọng bất kỳ hành vi nào liên quan tới tiền thật.
* Giao diện sản phẩm bằng tiếng Anh; tài liệu nghiệp vụ bằng tiếng Việt.
* Người chơi ở nhà, kết nối tới máy chủ đặt xa — độ trễ đường truyền là điều kiện sống chung, không phải lỗi.

## 8. Assumptions & Validation

| ID | Assumption | Impact if Wrong | Validation Status | Next Action |
|---|---|---|---|---|
| A-01 | Danh sách cặp tiền (XAUUSD, EURUSD, GBPUSD, USDJPY) người chơi sửa được trong Settings | Nếu cố định, UN-008 hẹp lại và mất một nhu cầu tuỳ biến | Chưa xác nhận — suy từ `phase-03` bước 11 | Hỏi người chơi khi viết SRS |
| A-02 | "Luôn thoát được" nghĩa là đóng được vị thế **không cần tay cầm** | Nếu bắt buộc phải có tay cầm, UN-003 không thoả | Chưa xác nhận — suy từ `phase-03` ("HUD Flatten button that does not need the pad") | Xác nhận khi thiết kế màn hình |
| A-03 | Người chơi chơi một mình, không có ai xem cùng hoặc review realtime | Nếu có vai trò thứ hai, User Types thiếu một tier | Chưa xác nhận | Xác nhận với người chơi |
| A-04 | Một phiên = một buổi tối, một phiên mỗi ngày; hạn mức lỗ gắn với **phiên**, không cộng dồn theo ngày lịch | Nếu chạy nhiều phiên trong một ngày, người chơi có thể lách hạn mức lỗ bằng cách mở phiên mới | **Đã xác nhận một phần** — OQ-1 chốt phiên kết thúc khi tự đóng hoặc hết khung giờ. Việc *không* cộng dồn theo ngày là 🔶 quyết định thay user | Chốt số phiên tối đa mỗi ngày, và có trần lỗ theo ngày hay không, khi viết SRS |
| A-05 | Người chơi chấp nhận đánh đổi độ trễ đường truyền để lấy khả năng chạy liên tục | Nếu không, cả kiến trúc máy chủ từ xa bị đặt lại vấn đề | Observed: `README.md` nêu rõ đây là đánh đổi có chủ ý | Không cần hành động |
| A-06 | Thao tác bằng chuột trên nhiều cửa sổ làm đứt nhịp quan sát, nên "không rời tay khỏi tay cầm" là nhu cầu thật | Phần *tiện lợi thuần* của UN-008 (chọn cặp / khối lượng / khung thời gian bằng pad) mất cơ sở và nên hạ xuống Medium | Chưa xác nhận — người chơi chưa nói trực tiếp | Hỏi người chơi trước khi chốt phạm vi bản đồ nút |
| A-07 | Người chơi luôn mở được giao diện cTrader bằng một đường độc lập để kiểm chứng | **Toàn bộ Independent verification của Mục 5 và USC-003/USC-004 mất khả năng kiểm chứng** | Chưa xác nhận; căng với ràng buộc "giữ Chrome focus suốt phiên" ở Mục 7 | Xác nhận cách kiểm chứng (máy khác? điện thoại?) trước khi chốt USC |

## 9. User Success Criteria

| ID | User Outcome | Baseline | Target | Measurement | Review Period |
|---|---|---|---|---|---|
| USC-001 | Không có lệnh nào vào sàn mà người chơi không chủ động quyết định | **Chưa có** — xác lập từ 10 phiên đầu | 0 lệnh ngoài ý muốn mỗi tháng | Đối chiếu số lệnh trên cTrader demo với **số lần xác nhận hai tay do sản phẩm ghi lại** — mỗi lệnh phải khớp đúng một lần xác nhận. Không dựa vào trí nhớ | Hằng tháng |
| USC-002 | Tỷ lệ tự kiềm chế tăng lên theo thời gian | **Chưa có** — xác lập tỷ lệ trung bình từ 10 phiên đầu | **Tỷ lệ từ chối = số lần huỷ chủ động ÷ số lần vũ trang** cao hơn baseline sau 3 tháng, **đồng thời** tổng số lần vũ trang mỗi phiên không tăng bất thường so với baseline | Bộ đếm theo phiên trên màn hình, đọc cuối mỗi phiên. Dùng tỷ lệ thay số tuyệt đối để không thưởng cho việc vũ trang bừa rồi huỷ lấy điểm | Hằng quý |
| USC-003 | Người chơi luôn thoát được vị thế kể cả khi thiết bị hoặc kết nối hỏng | **Chưa có** — chưa có sản phẩm để đo | 100% lần thử thoát trong tình huống sự cố thành công, trong vòng 10 giây kể từ lúc quyết định thoát | Diễn tập có chủ ý mỗi tháng: rút dongle / ẩn tab / ngắt mạng khi đang có vị thế, rồi bấm thoát và bấm giờ | Hằng tháng |
| USC-004 | Người chơi không bao giờ hoang mang về trạng thái lệnh của mình | **Chưa có** — chưa có sản phẩm để đo | 0 lần phải mở cTrader ở nơi khác **vì hoang mang không biết lệnh có tồn tại không**. Các lần kiểm chứng có kế hoạch (diễn tập USC-003, verification của Mục 5) không tính | Người chơi ghi nhận mỗi lần đi kiểm tra chéo ngoài kế hoạch, cuối mỗi phiên | Hằng tháng |
| USC-005 | Hạn mức người chơi tự đặt thực sự được thi hành | **Chưa có** — chưa có sản phẩm để đo | 0 lệnh được mở ngoài khung giờ đã khai hoặc sau khi đã chạm mức lỗ tối đa của phiên | Đối chiếu dấu thời gian của từng lệnh trên cTrader demo với khung giờ và hạn mức đã khai cho phiên đó | Hằng tháng |

## 10. Open Questions

* [x] OQ-1: Một "phiên" kết thúc theo cách nào? — **Resolved:** cả hai — người chơi tự đóng, hoặc hết khung giờ đã đặt. Hạn mức gắn với phiên và đặt lại ở phiên kế tiếp.
* [x] OQ-2: Sửa hạn mức giữa phiên có hiệu lực ngay không? — **Resolved:** siết chặt có hiệu lực ngay; nới lỏng chỉ áp dụng từ phiên sau.
* [x] OQ-3: Lệnh "chưa rõ kết quả" gỡ thế nào? — **Resolved:** hệ thống tự đối chiếu với sàn khi kết nối ổn định; người chơi được chủ động bỏ qua sau khi đọc cảnh báo.
* [x] OQ-4: Bộ đếm từ chối đặt lại theo chu kỳ nào? — **Resolved:** hiển thị theo phiên trên màn hình chính, tổng cộng dồn thuộc feature khác.
* [ ] OQ-5: Một ngày chạy được tối đa mấy phiên, và có trần lỗ theo **ngày** đứng trên trần lỗ theo **phiên** không? Không có trần ngày thì mở phiên mới là cách lách hạn mức lỗ. Xem A-04.
* [ ] OQ-6: Mở khoá phiên sau khi thoát khẩn cấp cần thao tác nặng tới đâu — một cú tap như nguồn `phase-03` mô tả, hay phải qua một bước có chủ ý hơn? Một tap thì trạng thái khoá gần như không có sức răn đe. Xem UN-011.
* [ ] OQ-7: Người chơi kiểm chứng độc lập bằng thiết bị nào, khi Mục 7 yêu cầu giữ Chrome focus suốt phiên? Xem A-07.

---

> **Cập nhật 2026-08-28 (cascade từ `ai-desk`):** `UN-004` tách rõ hạn mức **thi hành** với ngưỡng
> **chỉ cảnh báo**, và nhận thêm ngưỡng báo trước sự kiện tin (OQ-2 của `ai-desk`). `UN-008` bổ sung
> thao tác mở bàn làm việc AI vào danh sách nút đóng. Mục 6 thêm một dòng cho ngưỡng tin không hợp lệ.
>
> **Lịch sử review:** chốt OQ-1..4 ngày 2026-08-28 (`/urd` Phase E). Review bởi `@senior-ba`
> (block: 7 blocking, 11 warning) và `@po-reviewer` (revise: 5 warning) cùng ngày; findings đã áp
> vào Mục 3, 4, 5, 6, 8, 9 và sinh thêm UN-011..013, Journey 5, USC-005, OQ-5..7.
