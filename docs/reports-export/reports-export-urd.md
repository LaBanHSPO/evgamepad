---
type: urd
feature: reports-export
status: draft
updated: 2026-08-28
links: ["docs/_shared/project-profile.md", "docs/_shared/system-overview.md", "docs/_shared/definitions.md", "docs/_shared/operating-environment.md", "docs/daily-journal/daily-journal-urd.md", "docs/process-score/process-score-urd.md", "docs/voice-journal/voice-journal-urd.md", "docs/trade-replay/trade-replay-urd.md", "docs/playbook-grading/playbook-grading-urd.md", "docs/order-execution/order-execution-urd.md", "docs/tilt-meter/tilt-meter-urd.md", "docs/ai-desk/ai-desk-urd.md"]
---

# reports-export — User Requirements Document

## 1. Purpose

Ghi lại nhu cầu của người chơi quanh **lối ra của dữ liệu** — và quanh **lối vào duy nhất được phép
đổi cấu hình**.

Tám feature kia sinh ra dữ liệu; feature này là nơi duy nhất dữ liệu đó **rời khỏi màn hình**: một
báo cáo đọc được cho cả một tháng, một bản xuất mang đi được, một gói sao lưu để sống sót qua một ổ
đĩa hỏng, và một đường xoá sạch có chủ ý. Kèm theo là **màn cài đặt an toàn** — nơi đổi được biểu
tượng, khung giờ, hiệu chỉnh tay cầm, rung, micro và mặc định báo cáo, mà **không chạm được vào bất
kỳ chốt an toàn nào**.

Điểm mấu chốt: đây là feature duy nhất chạm được **toàn bộ** dữ liệu sản phẩm cùng một lúc. Nên nó
cũng là feature duy nhất có thể **làm mất sạch** hoặc **làm rò rỉ hết**. Hai nghĩa vụ của nó kéo
ngược nhau và cả hai đều phải giữ: **mang dữ liệu ra thật dễ**, và **không bao giờ mang theo bí mật,
không bao giờ xoá nhầm**.

Feature này **không tính bất kỳ con số nào của riêng nó**. Báo cáo render lại đúng những con số
`process-score` và `daily-journal` đã chốt; nó không dựng một định nghĩa thứ hai cho mức tuân thủ,
điểm quy trình hay bất kỳ số liệu nào.

### User Problem & Current Experience

| User | Current Situation | Problem | User Consequence | Evidence |
|---|---|---|---|---|
| Người chơi | Cuối tháng muốn nhìn lại một quãng dài; thứ duy nhất có là deck và bảng lịch sử trên màn hình | Không có gì cầm ra khỏi màn hình — không đọc rời được, không lưu lại được một lát cắt của tháng đó | Việc nhìn lại phải làm ngay trước máy, và một tháng đã qua không để lại bản chụp nào để so với tháng sau | Observed: `phase-13` ("report builder selects week, month, custom period, or one session") |
| Người chơi | Muốn nhờ một trợ lý AI ngoài đọc dữ liệu dài hạn để tìm thói quen mà chính mình không thấy | Dữ liệu nằm trong một máy chủ riêng, không có đường lấy ra ở dạng một tệp đưa cho ai đó đọc | Copilot trong sản phẩm chỉ nhìn được thứ nó được cấp; góc nhìn ngoài — thứ hữu ích nhất khi tự mình đã quen mắt — là bất khả thi | Confirmed 2026-08-28 (người chơi chốt mục đích xuất dữ liệu) |
| Người chơi | Toàn bộ nhật ký nằm trên **một** VPS, và nhật ký **giữ vô hạn, không bao giờ tự xoá thứ gì** | Không có bản sao thứ hai của bất cứ thứ gì | Một ổ đĩa hỏng xoá sạch nhiều tháng bằng chứng về chất lượng quyết định — đúng thứ tài sản mà cả sản phẩm này tồn tại để tích luỹ | Observed: `daily-journal-urd.md` ("Nhật ký không bao giờ tự xoá thứ gì... giữ vô hạn"), `phase-13` (backup/restore) |
| Người chơi | Nhật ký chứa **dữ liệu cá nhân**: giọng nói, ảnh biểu đồ, ghi chú riêng | Không có đường chủ động xoá sạch — chỉ có xoá từng thứ tại chỗ đính | Không trả lời được câu hỏi cơ bản nhất về dữ liệu của mình: "muốn xoá hết thì làm thế nào" | Observed: `docs/_shared/project-profile.md` mục Compliance ("cần nêu rõ nơi lưu và cách xoá"), `phase-13` (delete-all) |
| Người chơi | Cấu hình sống trong YAML và biến môi trường trên máy chủ | Đổi một thứ hoàn toàn vô hại — thêm một biểu tượng, dời khung giờ, tắt rung — phải vào máy chủ sửa tệp | Mỗi lần chỉnh một preference nhỏ là một lần mở đúng tệp chứa các chốt an toàn ra sửa; sai một dòng thì hỏng thứ khác | Observed: `phase-13` ("`/settings` edits safe preferences only"), `README.md` (danh sách khoá boot-fail) |
| Người chơi | Ổ đĩa đầy dần theo mỗi bản ghi âm, mỗi ảnh, mỗi tape đóng băng | Không ai nói gì cho tới lúc hết chỗ | Ràng buộc "giữ vô hạn" gặp một giới hạn vật lý trong im lặng, và cái hỏng đầu tiên sẽ là một phiên đang chạy | Observed: `daily-journal-urd.md` ("phải được cảnh báo dung lượng **trước khi** hết chỗ") |

## 2. User Types

| Tier | User Type | Context | Primary Goal | Pain Points |
|---|---|---|---|---|
| primary | **Người chơi** | Ngoài phiên giao dịch — cuối tháng ngồi tổng kết, hoặc một buổi dọn dẹp: tạo báo cáo, xuất dữ liệu, sao lưu, chỉnh cài đặt. Ngồi trước màn hình với chuột và bàn phím | Cầm được dữ liệu của mình ra khỏi sản phẩm, giữ nó an toàn, và đổi được các thiết lập vô hại mà không phải đụng vào máy chủ | Không có gì rời khỏi màn hình; không có bản sao nào; không có đường xoá; đổi một preference phải SSH |

> **Không có secondary user.** Công cụ cá nhân một người dùng.
> **Trợ lý AI ngoài không phải người dùng của sản phẩm** — nó là *nơi nhận* một tệp mà người chơi
> chủ động đưa cho. Sản phẩm không gửi đi đâu cả, không kết nối tới nó, không biết nó là ai.
> **Sàn cTrader/Spotware không liên quan tới feature này** — không dữ liệu nào của feature này đi tới
> sàn, và không dữ liệu nào từ sàn được nhập vào (xem Mục 3, Out of Scope).

## 3. Scope Boundaries

### In Scope

* **Báo cáo theo kỳ tự chọn**: một tuần, một tháng, một khoảng ngày tuỳ chọn, hoặc **một phiên**.
* **Báo cáo mở đầu bằng quy trình**: bìa quy trình, bản đồ nhiệt, điểm quy trình, mức tuân thủ, các lỗi sai, và lát cắt theo playbook **chỉ gồm số lệnh và mức tuân thủ**. Kỳ vọng theo R, MFE/MAE, hiệu suất trung bình và toàn bộ bảng theo kiểu setup là **con số kết quả** — chúng nằm trong phụ lục kết quả, đúng ranh giới `process-score` đã đặt cho deck.
* **Phụ lục kết quả tiền mặc định TẮT** — người chơi phải chủ động tích khi tạo báo cáo thì nó mới có trong tệp. *(Chốt 2026-08-28 — đây là câu trả lời cho OQ-6 của `process-score`: quy tắc "tiền nằm sau một cú bấm có chủ ý" áp cho một tệp tĩnh bằng cách chuyển cú bấm đó về **lúc tạo tệp** thay vì lúc đọc tệp.)*
* **Mục "mặc định báo cáo" trong cài đặt KHÔNG bao gồm phụ lục kết quả.** Phụ lục luôn khởi tạo ở trạng thái tắt cho **mỗi lần** tạo báo cáo; không preference nào bật vĩnh viễn được nó. Bật một lần rồi quên thì cú bấm có chủ ý đã biến thành cú bấm một lần — đúng thứ ràng buộc này sinh ra để chặn.
* **Lưu báo cáo thành một tệp đọc được ngay trên máy người chơi**, bằng chính trình duyệt đang mở — không cần cài thêm gì trên máy chủ, và tệp mở được ở bất cứ đâu.
* **Xuất JSON đầy đủ ngữ cảnh**: phiên, kế hoạch trước phiên, điểm chấm từng lệnh, phần nhìn lại, điểm quy trình, phân tích, và thông tin về các tệp đính kèm. Đây là **định dạng ưu tiên số một**, vì mục đích đã chốt là đưa cho một trợ lý AI ngoài đọc — nó phải tự đủ nghĩa mà không cần người chơi giải thích thêm.
* **Xuất CSV phẳng**: dữ kiện từng lệnh cộng các chiều nhìn lại đã dàn phẳng, mở được bằng bảng tính.
* **Không bản xuất nào mang theo bí mật** — không giá trị biến môi trường, không token, không cấu hình gốc, không đường dẫn tuyệt đối trên máy chủ.
* **Gói sao lưu đầy đủ**: dữ liệu nhật ký cộng bản ghi âm, ảnh biểu đồ và tape đã đóng băng — kèm **bản kê từng phần với kích thước và mã kiểm tra**.
* **Gói sao lưu không chứa** mô hình chép lời, ảnh Docker, bộ nhớ đệm, biến môi trường hay token — thứ thay thế được thì không cần chép, thứ bí mật thì không được chép.
* **Gói sao lưu luôn là một lát cắt nhất quán**, dù tạo lúc nào — không gói nào được chụp giữa lúc một việc chép lời hay đóng băng tape còn dang dở.
* **Thao tác nặng cần một lần xác nhận gần đây**: tải gói sao lưu, khôi phục và xoá sạch không dựa vào việc cửa sổ trình duyệt đang mở sẵn.
* **Mọi thao tác dữ liệu để lại một vết ghi nhận không có nội dung** — chỉ hành động, thời điểm, số lượng. Vết này để tra cứu, và **không được** biến thành lời nhắc "đã bao lâu kể từ lần sao lưu gần nhất".
* **Khôi phục có điều kiện**: chỉ chạy khi phiên đã khoá, không còn vị thế mở, và không có việc chép lời hay đóng băng tape nào đang chạy.
* **Khôi phục hỏng thì dữ liệu hiện tại không suy suyển** — kiểm bản kê, mã kiểm tra và tính tương thích **trước khi** động vào bất cứ thứ gì đang có. Hỏng ở bất kỳ bước nào thì mở lại vẫn là nhật ký cũ, đầy đủ, như chưa từng bấm.
* **Đối chiếu được sau khi khôi phục**: số lượng và mã kiểm tra khớp với bản kê trong gói.
* **Xoá sạch có chủ ý**: cần gõ đúng câu xác nhận **và** giữ nút hai giây; bị từ chối khi còn phiên hoặc vị thế đang chạy; xoá xong thì dọn cả chỗ trống.
* **Được mời sao lưu trước khi xoá**, nhưng **sau lời xác nhận cuối cùng thì không có bản sao ẩn nào** được giữ lại.
* **Cảnh báo dung lượng trước khi hết chỗ** — và **không nhắc sao lưu định kỳ**. *(Chốt 2026-08-28 — mọi cơ chế nhắc theo nhịp đều là thứ cộng dồn theo thời gian mà `README.md` đã cấm.)*
* **Màn cài đặt chỉ đổi được thứ an toàn**: biểu tượng được bật trong danh sách máy chủ cho phép, khung thời gian biểu đồ, lịch buổi tối và múi giờ, hiệu chỉnh tay cầm, rung, micro và nút giữ để nói, giọng đọc, hạn giữ nhật ký, mặc định báo cáo.
* **Tài khoản cTrader là một danh tính chỉ đọc** — nhìn thấy được, không sửa được, không thêm được tài khoản thứ hai.
* **Báo cáo và cài đặt là hai đích trong menu an toàn**, mở bằng tay cầm theo đúng hợp đồng điều hướng chung; việc tạo báo cáo, chọn kỳ và xử lý tệp thì làm bằng chuột và bàn phím.
* Mọi bề mặt giữ nguyên dòng chữ demo / giải trí / không phải lời khuyên — **kể cả trong tệp báo cáo xuất ra**, vì tệp đó rời khỏi sản phẩm và có thể được đọc ngoài mọi ngữ cảnh.

### Out of Scope

* **Nhập lịch sử giao dịch từ cTrader, MT5 hay bất kỳ công cụ nào** — dứt khoát không tồn tại. Khôi phục chỉ nhận **gói sao lưu do chính sản phẩm này tạo ra**.
* **Sửa luật playbook** → feature `playbook-grading`. Màn cài đặt chỉ **dẫn sang** trình sửa của feature đó, không dựng bản sao thứ hai.
* **Sửa triết lý và nguyên tắc cá nhân** → feature `daily-journal`. Cùng nguyên tắc chỉ-dẫn-sang.
* **Đổi bất kỳ chốt an toàn nào**: chế độ demo/thật, thông tin đăng nhập sàn, địa chỉ lắng nghe, quyền công cụ của AI, trọng số các trục điểm. Những thứ này sống ngoài cơ sở dữ liệu và **sai thì sản phẩm không khởi động** — chúng cố tình không có mặt trong giao diện.
* **Tính toán bất kỳ số liệu nào** → `process-score` và `daily-journal`. Báo cáo **render lại** con số đã chốt; nếu hai nơi lệch nhau thì lỗi nằm ở báo cáo, không phải ở deck.
* **Xoá riêng dữ liệu giọng nói** → feature `voice-journal` có đường xoá riêng của nó. Đường xoá sạch ở đây xoá **mọi thứ**, bao gồm cả giọng nói — hai đường phải không đá nhau (xem OQ-5).
* **Gỡ một ảnh hoặc một ghi chú vừa đính** → làm tại chỗ đính, thuộc `daily-journal`.
* **Thư viện các loại lỗi sai và xu hướng lỗi** → feature `execution-learning` *(tách khỏi `daily-journal` 2026-08-28, chưa có URD)*. Báo cáo chỉ **render lại** phần lỗi sai của feature đó; nó không định nghĩa loại lỗi nào.
* **Chia sẻ, đồng bộ đám mây, gửi báo cáo qua email, hay bất kỳ đường nào sản phẩm tự gửi dữ liệu đi.** Tệp được tạo ra và nằm lại trên máy người chơi; đưa nó cho ai là việc của người chơi.
* **Giao diện sáng và giao diện di động** — sản phẩm chỉ có Chrome desktop, chỉ nền tối.

## 4. User Needs

| ID | User | Context / Trigger | User Need | Expected Outcome | Importance | Evidence |
|---|---|---|---|---|---|---|
| UN-001 | Người chơi | Cuối tháng, cuối tuần, hoặc muốn xem lại đúng một buổi tối cụ thể | Chọn được **kỳ** mình muốn nhìn lại, không bị ép vào một kỳ cố định | Báo cáo tạo được cho một tuần, một tháng, một khoảng ngày tuỳ chọn, hoặc **một phiên**. Số tổng hợp cho kỳ **không phải một tháng trọn** hiện chưa có feature nào sở hữu cách tính — xem OQ-8 | High | Observed: `phase-13` ("selects week, month, custom period, or one session") |
| UN-002 | Người chơi | Mở báo cáo vừa tạo ra | Thấy **quy trình trước**, đúng như khi mở deck | Báo cáo mở đầu bằng bìa quy trình rồi tới bản đồ nhiệt, điểm quy trình, mức tuân thủ, lỗi sai, và lát cắt theo playbook **chỉ gồm số lệnh và mức tuân thủ**. Kỳ vọng theo R, MFE/MAE, hiệu suất trung bình và bảng theo kiểu setup thuộc phụ lục kết quả, không nằm ở phần quy trình | High | Observed: `phase-13` ("process-first cover, heatmap, Process Score, adherence, mistakes, playbook/setup cuts") |
| UN-003 | Người chơi | Đang chọn nội dung cho báo cáo sắp tạo | Con số tiền **không tự có mặt** trong tệp; muốn có thì phải tự tích | Phụ lục kết quả **mặc định tắt**. Không tích thì trong tệp không có một đồng nào. Cú bấm có chủ ý chuyển về lúc **tạo** tệp, vì một tệp tĩnh không có tab để bấm lúc đọc. Mục "mặc định báo cáo" trong cài đặt **không bật sẵn được** phụ lục — nó khởi tạo tắt cho mỗi lần tạo | Critical | Confirmed 2026-08-28 (người chơi chốt, đóng OQ-6 của `process-score`). Nền: `phase-13` ("optional Outcome appendix"), `README.md` ("money sits behind a deliberate tab click") |
| UN-004 | Người chơi | Vừa dựng xong báo cáo và muốn giữ lại | Lưu thành một tệp đọc được, mở được ở bất cứ đâu, không phải cài gì thêm | Báo cáo lưu được thành **PDF** ngay từ trình duyệt đang mở, bằng chính chức năng lưu-thành-PDF của trình duyệt; không thành phần nào phải thêm vào máy chủ để in ra được nó | High | Observed: `phase-13` ("dedicated print stylesheet and the browser's Save as PDF flow. No Chromium/Puppeteer binary is added") |
| UN-005 | Người chơi | Muốn nhờ một trợ lý AI ngoài đọc dữ liệu dài hạn và chỉ ra thói quen mình không tự thấy | Một bản xuất **tự đủ nghĩa**, đọc là hiểu, không cần người chơi giải thích thêm | Bản xuất JSON mang đủ ngữ cảnh: phiên, kế hoạch trước phiên, điểm chấm từng lệnh, phần nhìn lại, điểm quy trình, phân tích và thông tin về tệp đính kèm — đủ để trả lời câu hỏi dài hạn mà không phải hỏi lại | Critical | Confirmed 2026-08-28 (người chơi chốt mục đích xuất dữ liệu). Nền: `phase-13` ("sessions, plans, grades, reviews, scores, analyses, and attachment metadata") |
| UN-006 | Người chơi | Muốn tự cắt lát dữ liệu theo cách sản phẩm chưa hỗ trợ | Một bản xuất phẳng mở được bằng bảng tính | Bản xuất CSV chứa dữ kiện từng lệnh cộng các chiều nhìn lại đã dàn phẳng | Medium | Observed: `phase-13` ("streamed CSV export contains trade facts and flattened review dimensions") |
| UN-007 | Người chơi | Sắp đưa một tệp xuất cho một trợ lý AI ngoài — nghĩa là cho một bên thứ ba | Chắc chắn tệp đó **không mang theo bí mật nào** | Bản xuất không chứa giá trị biến môi trường, token, cấu hình gốc hay đường dẫn tuyệt đối trên máy chủ. Đây là ràng buộc phải kiểm được, không phải một lời hứa | Critical | Observed: `phase-13` ("exports never include env values, OAuth/WS/webhook/API tokens, raw config secrets, or absolute VPS paths"), `README.md` ("Neither is committed, baked into an image, exported, or included in backups") |
| UN-008 | Người chơi | Nghĩ tới việc ổ đĩa hỏng và mất nhiều tháng bằng chứng | Một gói sao lưu **đầy đủ**, không chỉ có dữ liệu bảng | Gói sao lưu gồm dữ liệu nhật ký cộng bản ghi âm, ảnh biểu đồ và tape đã đóng băng — nếu thiếu một trong số đó thì replay và nhật ký giọng nói khôi phục về sẽ rỗng | Critical | Observed: `phase-13` ("consistent SQLite backup plus voice audio, chart attachments, and trade tapes") |
| UN-009 | Người chơi | Có một gói sao lưu nằm đó nhiều tháng và tự hỏi nó còn dùng được không | Kiểm được gói còn nguyên vẹn **trước khi** cần tới nó | Mỗi phần trong gói có tên, kích thước và mã kiểm tra ghi trong một bản kê; đối chiếu được mà không phải khôi phục thật | High | Observed: `phase-13` ("every archive member has path, size, and SHA-256 in the manifest") |
| UN-010 | Người chơi | Gói sao lưu nằm trên máy cá nhân, có thể chép sang ổ ngoài | Gói **không mang theo bí mật**, và không phình vì những thứ tải lại được | Mô hình chép lời, ảnh Docker, bộ nhớ đệm, biến môi trường và token không nằm trong gói | Critical | Observed: `phase-13` ("Whisper models, Docker images, caches, `.env`, and tokens are excluded because they are replaceable or secret") |
| UN-011 | Người chơi | Bấm khôi phục | Không bao giờ khôi phục được **giữa lúc đang giao dịch** | Khôi phục chỉ chạy khi phiên đã khoá, không còn vị thế mở, và không có việc chép lời hay đóng băng tape nào đang chạy. Không đủ điều kiện thì bị từ chối kèm lý do cụ thể | Critical | Observed: `phase-13` ("allowed only while the session is locked, no position is open, and no transcription/tape job is running") |
| UN-012 | Người chơi | Khôi phục từ một gói hoá ra bị hỏng | **Không mất luôn cả dữ liệu đang có** | Bản kê, mã kiểm tra, tính tương thích và các đường dẫn trong gói được kiểm **trước khi** động vào dữ liệu hiện tại. Hỏng ở bất kỳ bước nào thì dữ liệu hiện tại nguyên vẹn như chưa từng bấm | Critical | Observed: `phase-13` ("Validate manifest, checksums, schema compatibility, and archive paths before changing current data"; "Failure leaves current data untouched") |
| UN-013 | Người chơi | Khôi phục xong và muốn biết nó thật sự đủ | Đối chiếu được **bằng con số**, không phải tin vào một dòng "thành công" | Sau khi khôi phục, số lượng bản ghi và mã kiểm tra của các tệp đính kèm khớp với bản kê trong gói | High | Observed: `phase-13` ("Successful restore reproduces row counts and attachment hashes from the backup manifest") |
| UN-014 | Người chơi | Quyết định xoá sạch dữ liệu | Không thể xoá nhầm bằng một cú bấm | Xoá sạch cần **gõ đúng câu xác nhận** cộng **giữ nút hai giây**, và bị từ chối khi còn phiên hoặc vị thế đang chạy | Critical | Observed: `phase-13` ("requires the exact confirmation phrase plus a two-second gamepad/keyboard hold, refuses while a position or session is active") |
| UN-015 | Người chơi | Đang ở bước cuối của xoá sạch | Được **mời sao lưu trước**, nhưng khi đã xác nhận thì phải là xoá thật | Giao diện mời tạo gói sao lưu trước khi xoá; sau lời xác nhận cuối cùng **không có bản sao ẩn nào** được giữ lại | High | Observed: `phase-13` ("offers backup before delete but never creates a hidden recovery copy after the final confirmation") |
| UN-016 | Người chơi | Sau khi xoá sạch | Không còn nội dung nhật ký hay ghi chú riêng nào sót lại | Dữ liệu, bản ghi âm, ảnh và tape bị xoá và chỗ trống được dọn. Chỉ còn lại cấu hình, mô hình, phần mềm, thông tin đăng nhập, và **một vết ghi nhận không có nội dung** — chỉ hành động, thời điểm và số lượng | Critical | Observed: `phase-13` ("no journal content or personal note remains"; "audit rows contain action/time/counts only") |
| UN-017 | Người chơi | Nhật ký giữ vô hạn và ổ đĩa đầy dần theo từng bản ghi âm, ảnh, tape | Được cảnh báo **trước khi** hết chỗ, chứ không phát hiện lúc mọi thứ đã hỏng | Cảnh báo dung lượng khi chỗ trống xuống dưới một ngưỡng, đủ sớm để còn kịp sao lưu và dọn. **Không nhắc sao lưu định kỳ** — không có "đã bao nhiêu ngày kể từ lần sao lưu gần nhất" | High | Confirmed 2026-08-28 (người chơi chốt, đóng OQ-9 của `daily-journal`). Nền: `daily-journal-urd.md` ("phải được cảnh báo dung lượng **trước khi** hết chỗ"), `README.md` ("nothing that accumulates across sessions") |
| UN-018 | Người chơi | Muốn đổi một thứ vô hại: thêm biểu tượng, dời khung giờ, tắt rung, đổi nút giữ để nói | Đổi được ngay trong sản phẩm, **không phải vào máy chủ sửa tệp** | Màn cài đặt đổi được: biểu tượng trong danh sách máy chủ cho phép, khung thời gian biểu đồ, lịch buổi tối và múi giờ, hiệu chỉnh tay cầm, rung, micro và nút giữ để nói, giọng đọc, hạn giữ nhật ký, mặc định báo cáo | High | Observed: `phase-13` (danh sách safe preferences) |
| UN-019 | Người chơi | Ở trong màn cài đặt | **Không vô tình chạm được vào một chốt an toàn nào** | Chế độ demo/thật, thông tin đăng nhập sàn, địa chỉ lắng nghe, quyền công cụ của AI và trọng số các trục điểm **không xuất hiện trong giao diện**. Chúng sống ngoài cơ sở dữ liệu và sai thì sản phẩm không khởi động | Critical | Observed: `phase-13` ("no broker credentials, live-mode switch, secrets, bind address, or AI order permission appear in the UI"; "Hard safety invariants remain YAML/env boot-fails") |
| UN-020 | Người chơi | Nhìn phần tài khoản trong cài đặt | Tài khoản là **một danh tính chỉ đọc**, không phải một thứ để cấu hình | Tài khoản cTrader đang dùng nhìn thấy được, không sửa được, và không thêm được tài khoản thứ hai | Critical | Observed: `phase-13` ("the configured cTrader account is a read-only identity. No second account can be added") |
| UN-021 | Người chơi | Suốt quá trình dùng sản phẩm | Mọi dòng trong sổ đều là thứ mình **thật sự đã làm bằng tay cầm** | Không tồn tại đường nhập lịch sử giao dịch từ cTrader, MT5 hay công cụ nào khác. Khôi phục chỉ nhận gói do chính sản phẩm này tạo | High | Observed: `phase-13` ("cTrader/MT5/broker-history import is explicitly out of scope"; "No MT5, broker-history, CSV, or general trade import endpoint exists") |
| UN-022 | Người chơi | Ở trong cài đặt và muốn sửa một luật playbook hoặc một nguyên tắc cá nhân | Chỉ có **một** chỗ sửa mỗi thứ, không có bản sao thứ hai | Cài đặt **dẫn sang** trình sửa playbook và trình sửa nguyên tắc cá nhân của các feature sở hữu chúng, không dựng lại một trình sửa riêng | Medium | Observed: `phase-13` ("playbook editing links to phase 7; philosophy/principles links to phase 12. Do not duplicate either editor") |
| UN-023 | Người chơi | Mở báo cáo hoặc cài đặt sau khi rời tay cầm | Mở bằng **tay cầm** từ menu an toàn, thao tác bằng chuột | Báo cáo và cài đặt là hai đích trong menu an toàn, theo đúng hợp đồng điều hướng chung; việc chọn kỳ, tích phụ lục và xử lý tệp thì dùng chuột và bàn phím — đây là màn hình ngoài phiên, không phải màn hình thao tác nhanh. Mở menu an toàn **huỷ ARM và khoá mở lệnh mới** — nên mở báo cáo hay cài đặt giữa phiên là một hành động có giá, và người chơi phải biết trước cái giá đó | Medium | Observed: `docs/_shared/definitions.md` (hợp đồng điều hướng menu an toàn), `phase-13` (`GameOverlay` thêm đích settings/report) |

| UN-024 | Người chơi | Bấm tạo gói sao lưu, có thể ngay sau một cảnh báo dung lượng giữa phiên | Gói tạo ra **luôn là một lát cắt nhất quán**, không bao giờ là một bản nửa vời | Việc tạo gói hoặc chờ các việc nền (chép lời, đóng băng tape) xong rồi mới chụp, hoặc bị từ chối kèm nêu rõ việc đang chạy. Một gói nửa vời trông y hệt một gói đủ, và cái giá của nhầm lẫn đó chỉ lộ ra đúng lúc cần khôi phục | Critical | Observed: `phase-13` ("a **consistent** SQLite backup") |
| UN-025 | Người chơi | Bấm tải gói sao lưu, khôi phục, hoặc xoá sạch | Ba thao tác nặng nhất không chạy được chỉ vì cửa sổ trình duyệt đang mở sẵn | Mỗi thao tác đòi **một lần xác nhận gần đây**, mức chặt tăng dần: tải gói nhẹ nhất, xoá sạch nặng nhất (câu xác nhận cộng giữ hai giây). Gói sao lưu chứa **toàn bộ giọng nói cá nhân** — nó không được nằm sau đúng một cú bấm | Critical | Observed: `phase-13` Security ("Backup download and destructive routes require the existing bearer plus recent re-auth/confirmation") |

## 5. Prioritized User Journeys

### Journey 1: Cuối tháng tạo một báo cáo để nhìn lại

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Hết một tháng, muốn một bản nhìn lại đọc được và giữ lại được
* __Expected outcome:__ Có một tệp báo cáo mở đầu bằng quy trình, và trong tệp **không có một đồng nào** vì người chơi không tích phụ lục
* __Related needs:__ UN-001, UN-002, UN-003, UN-004, UN-023

1) Người chơi mở báo cáo từ menu an toàn bằng tay cầm.
2) Chọn kỳ là tháng vừa rồi.
3) Phụ lục kết quả **đang tắt sẵn**; người chơi không đụng vào nó.
4) Tạo báo cáo, xem trước, rồi lưu thành tệp trên máy mình.
5) Mở tệp ra: mở đầu là bìa quy trình, rồi bản đồ nhiệt, điểm quy trình, mức tuân thủ, lỗi sai, các lát cắt theo playbook và kiểu setup.

__Independent verification:__ Tạo báo cáo một tháng mà **không tích gì thêm**; rà toàn bộ tệp — không
được có bất kỳ con số tiền nào, kể cả trong chú thích và phần chân trang. Kiểm chiều ngược: tích phụ
lục rồi tạo lại — phụ lục kết quả phải xuất hiện, và phải nằm **sau** toàn bộ các trang quy trình.
Kiểm riêng lát cắt theo playbook trong phần quy trình: chỉ được có số lệnh và mức tuân thủ, **không**
có kỳ vọng theo R hay hiệu suất trung bình. Kiểm chiều ngược ở cài đặt: đặt "mặc định báo cáo" rồi
tạo báo cáo mới — phụ lục vẫn phải ở trạng thái tắt. Đối chiếu điểm quy trình trong tệp với đúng con
số deck đang hiện cho tháng đó — hai nơi phải trùng khít. Không cần journey nào khác để xác nhận.

### Journey 2: Xuất dữ liệu đưa cho một trợ lý AI ngoài đọc

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Muốn một góc nhìn ngoài về thói quen dài hạn mà chính mình đã quen mắt không thấy
* __Expected outcome:__ Có một tệp tự đủ nghĩa để đưa cho một bên thứ ba đọc, và tệp đó **không mang theo bí mật nào**
* __Related needs:__ UN-005, UN-007, UN-006

1) Người chơi chọn xuất dữ liệu và chọn định dạng JSON.
2) Nhận một tệp chứa phiên, kế hoạch trước phiên, điểm chấm từng lệnh, phần nhìn lại, điểm quy trình, phân tích và thông tin về tệp đính kèm.
3) Đưa tệp cho một trợ lý AI ngoài và hỏi về thói quen dài hạn.
4) Trợ lý trả lời được mà không phải hỏi lại "cột này nghĩa là gì" — tệp tự giải thích được.

__Independent verification:__ Xuất một bản JSON rồi **tìm chuỗi** trong tệp: không được có token, giá
trị biến môi trường, tên miền máy chủ hay đường dẫn tuyệt đối. Kiểm mặt nội dung: đưa tệp cho một
trợ lý AI ngoài chưa biết gì về sản phẩm và hỏi ba câu — tháng nào tuân thủ tốt nhất, loại lỗi sai
lặp lại nhiều nhất, và điểm quy trình có xu hướng gì — nó phải trả lời được chỉ từ tệp. Phép thử này phụ
thuộc mô hình nên **không tất định**; vế tất định đi kèm là đọc chính tệp: nó phải chứa phần tự mô tả
— tên trường, đơn vị, thang điểm, múi giờ của các mốc thời gian — đủ để hiểu mà không cần hỏi ai.
Kiểm bản CSV riêng: mở bằng bảng tính, chữ tiếng Việt không vỡ, memo nhiều dòng và dấu phẩy trong
chữ không làm lệch cột. Đây là journey phải hoạt động kể cả khi phần báo cáo chưa có.

### Journey 3: Sao lưu trước một thay đổi lớn

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Sắp nâng cấp máy chủ, hoặc đơn giản là muốn có một bản sao vì đã lâu chưa có
* __Expected outcome:__ Có một gói sao lưu đầy đủ, kiểm được toàn vẹn, và không mang theo bí mật
* __Related needs:__ UN-008, UN-009, UN-010

1) Người chơi bấm tạo gói sao lưu.
2) Gói được dựng và tải về máy: dữ liệu nhật ký cộng bản ghi âm, ảnh biểu đồ, tape đã đóng băng.
3) Trong gói có một bản kê ghi tên, kích thước và mã kiểm tra của từng phần.
4) Người chơi chép gói sang một ổ khác và yên tâm.

__Independent verification:__ Tạo một gói rồi mở bản kê ra: mọi phần trong gói phải có mặt trong bản
kê với mã kiểm tra khớp. Đếm chéo: số bản ghi âm và số ảnh trong gói phải khớp với số đang có trong
nhật ký. Kiểm chiều ngược quan trọng nhất: tìm chuỗi trong toàn bộ gói — **không được có** token,
biến môi trường, hay mô hình chép lời.

### Journey 4: Khôi phục sau khi mất dữ liệu

* __User:__ Người chơi · __Importance:__ Critical
* __Trigger:__ Ổ đĩa hỏng, hoặc dựng lại máy chủ từ đầu
* __Expected outcome:__ Nhật ký trở lại đúng như lúc sao lưu, và người chơi **kiểm được là nó đủ**
* __Related needs:__ UN-011, UN-012, UN-013

1) Người chơi đóng phiên, chắc chắn không còn vị thế mở, rồi bấm khôi phục và chọn gói.
2) Gói được kiểm trước: bản kê, mã kiểm tra, tính tương thích, các đường dẫn bên trong.
3) Bản dữ liệu mới được dựng riêng, kiểm xong mới đổi chỗ cho bản đang có.
4) Sau khi xong, số lượng bản ghi và mã kiểm tra của các tệp đính kèm được đối chiếu với bản kê và hiện ra cho người chơi xem.
5) Mở nhật ký: các buổi tối cũ, bản ghi âm và tape đều còn.

__Independent verification:__ Chạy vòng tròn đầy đủ — sao lưu, đổi vài thứ trên dữ liệu bỏ đi được,
khôi phục, rồi đối chiếu số lượng và mã kiểm tra với bản kê: phải khớp hoàn toàn. Kiểm chiều ngược
theo bốn cách hỏng: gói sai mã kiểm tra, gói có đường dẫn lạ, gói của một phiên bản dữ liệu không
tương thích, và bấm khôi phục khi còn vị thế mở — **cả bốn phải bị từ chối trước khi dữ liệu hiện
tại thay đổi**, và sau mỗi lần từ chối nhật ký hiện tại phải nguyên vẹn. Thêm hai phép thử: đưa một
tệp **không phải gói của sản phẩm này** (bản xuất của một công cụ khác) — phải bị từ chối, vì không
đường nhập nào tồn tại; và chạy khôi phục khi chỗ trống không đủ cho cả bản đang có lẫn bản đang
dựng — phải bị từ chối sớm kèm con số cần bao nhiêu, không bắt đầu rồi chết giữa chừng.

### Journey 5: Xoá sạch dữ liệu một cách có chủ ý

* __User:__ Người chơi · __Importance:__ High — mức journey **thấp hơn mức của ba nhu cầu nó gắn tới (đều Critical) là có chủ ý**: việc này hiếm khi xảy ra, nhưng khi xảy ra thì không hoàn tác được, nên cơ chế phải đúng ở mức Critical còn tần suất thì không
* __Trigger:__ Muốn bắt đầu lại từ đầu, hoặc muốn xoá dữ liệu cá nhân khỏi máy chủ
* __Expected outcome:__ Dữ liệu bị xoá thật, sau một chuỗi hành động không thể làm nhầm
* __Related needs:__ UN-014, UN-015, UN-016

1) Người chơi mở phần quản lý dữ liệu và chọn xoá sạch.
2) Sản phẩm **mời tạo một gói sao lưu trước**, và nói rõ gói đó sẽ nằm ở đâu trên máy; người chơi tự quyết có làm hay không.
3) Người chơi gõ đúng câu xác nhận, rồi giữ nút hai giây.
4) Dữ liệu, bản ghi âm, ảnh và tape bị xoá; chỗ trống được dọn.
5) Còn lại: cấu hình, mô hình, phần mềm, thông tin đăng nhập, và một vết ghi nhận chỉ có hành động, thời điểm, số lượng.

__Independent verification:__ Xoá sạch rồi rà lại toàn bộ nơi lưu — **không được còn** một dòng nhật
ký, một bản ghi âm, một ảnh hay một ghi chú riêng nào; vết ghi nhận còn lại phải **không chứa nội
dung gì**. Kiểm chiều ngược: bấm xoá khi còn phiên hoặc vị thế đang chạy — phải bị từ chối; gõ sai
câu xác nhận — phải bị từ chối; gõ đúng nhưng không giữ đủ hai giây — phải bị từ chối. Và kiểm điều
quan trọng nhất: sau khi xoá xong, tìm khắp máy chủ **không được có bản sao ẩn nào**.

### Journey 6: Đổi một thiết lập vô hại mà không đụng vào máy chủ

* __User:__ Người chơi · __Importance:__ High
* __Trigger:__ Muốn thêm một biểu tượng, dời khung giờ buổi tối, hoặc tắt rung
* __Expected outcome:__ Đổi được ngay trong sản phẩm, và **không có cách nào chạm tới một chốt an toàn**
* __Related needs:__ UN-018, UN-019, UN-020, UN-022, UN-023

1) Người chơi mở cài đặt từ menu an toàn bằng tay cầm.
2) Đổi thứ mình cần: biểu tượng, khung thời gian, lịch buổi tối, hiệu chỉnh tay cầm, rung, micro, giọng đọc, mặc định báo cáo.
3) Rà khắp màn hình: không thấy chế độ demo/thật, không thấy thông tin đăng nhập, không thấy địa chỉ lắng nghe, không thấy quyền công cụ của AI.
4) Tài khoản cTrader hiện ra để xem, không sửa được, không thêm được cái thứ hai.
5) Muốn sửa luật playbook thì bấm vào đường dẫn sang trình sửa của playbook — không có trình sửa thứ hai ở đây.

__Independent verification:__ Rà toàn bộ màn hình cài đặt tìm bất kỳ thứ gì thuộc nhóm chốt an toàn —
**phải không tồn tại**. Đổi một preference an toàn rồi khởi động lại: giá trị mới phải còn. Kiểm
chiều ngược ở tầng dưới: gửi thẳng một thay đổi chứa khoá thuộc nhóm cấm — phải bị từ chối, không
được âm thầm bỏ qua khoá đó rồi báo thành công.

### Journey 7: Nhận cảnh báo sắp hết chỗ

* __User:__ Người chơi · __Importance:__ Medium
* __Trigger:__ Ổ đĩa đầy dần sau nhiều tháng ghi âm, ảnh và tape
* __Expected outcome:__ Biết trước khi hết chỗ, còn kịp sao lưu và dọn
* __Related needs:__ UN-017, UN-008

1) Chỗ trống xuống dưới ngưỡng.
2) Người chơi nhận một cảnh báo dung lượng, kèm con số cụ thể.
3) Người chơi tạo gói sao lưu rồi tự quyết dọn gì.
4) Ngoài cảnh báo này, sản phẩm **không nhắc gì thêm** — không có lời nhắc sao lưu theo nhịp.

__Independent verification:__ Dựng tình huống chỗ trống dưới ngưỡng — cảnh báo phải xuất hiện kèm con
số thật. Kiểm chiều ngược: rà toàn sản phẩm tìm bất kỳ lời nhắc nào dựa trên "đã bao nhiêu lâu kể
từ lần sao lưu gần nhất" — **phải không tồn tại ở đâu cả**, vì đó là một thứ cộng dồn theo thời gian.

## 6. User Exceptions & Edge Conditions

| Situation | User Impact | Expected User-facing Outcome | Related Journey / Need |
|---|---|---|---|
| **Kỳ báo cáo không có phiên nào** | Một tệp trống trông như lỗi | Báo cáo vẫn tạo được và **nói rõ kỳ này không có phiên nào**, thay vì các bảng rỗng không giải thích | J1 / UN-001 |
| **Kỳ báo cáo chỉ có một hai phiên** | Các con số trung bình trông như kết luận | Báo cáo in kèm **số phiên** bên cạnh mọi con số tổng hợp, và giữ nguyên trạng thái "chưa đủ phiên" của các chỉ số cần mẫu lớn đúng như deck đang hiện | J1 / UN-002 |
| **Trọng số các trục điểm đã đổi giữa kỳ báo cáo** | Một tệp trộn hai thước đo mà người đọc không biết | Báo cáo ghi rõ đang dùng bộ trọng số nào; phương án đang nghiêng là **tính lại toàn bộ theo bộ trọng số hiện tại**, nhất quán với cách deck đã chốt ở `process-score` Journey 6. Xem OQ-7 | J1 / UN-002 |
| **Tích phụ lục kết quả rồi đưa tệp cho người khác** | Con số tiền rời khỏi sản phẩm cùng tệp | Đây là hệ quả của một lựa chọn có chủ ý của người chơi, không phải sự cố. Ràng buộc mà sản phẩm giữ là **không tự đưa tiền vào tệp**, không phải kiểm soát tệp sau khi đã tạo | J1 / UN-003 |
| **Bản xuất JSON quá lớn sau nhiều tháng** | Trình duyệt treo hoặc tệp không mở nổi | Bản xuất nhiều tháng vẫn tải về được mà trình duyệt không treo, và người chơi giới hạn được kỳ xuất như khi tạo báo cáo | J2 / UN-005 |
| **Bản CSV mở bằng bảng tính bị vỡ cột hoặc sai chữ** | Bản xuất phẳng thành vô dụng đúng lúc muốn dùng | Chữ tiếng Việt hiện đúng; memo nhiều dòng và dấu phẩy trong chữ không làm lệch cột | J2 / UN-006 |
| **Kỳ báo cáo không phải một tháng trọn** (một tuần, một khoảng ngày tuỳ chọn) | Feature này tự gộp số liệu là phá ràng buộc lõi "không tự tính con số nào" | Cho tới khi OQ-8 chốt, báo cáo kỳ tuỳ chọn chỉ liệt kê con số **cấp phiên** đã chốt và nói rõ là kỳ này không có số tổng hợp — không tự gộp lấy | J1 / UN-001 |
| **Kỳ báo cáo chạm tới một phiên chưa đóng** | Bìa quy trình rỗng vì buổi tối đó chưa có điểm | Phiên chưa đóng không xuất hiện, hoặc xuất hiện kèm ghi rõ **chưa đóng, chưa có điểm** — không dựng một bìa quy trình rỗng trông như một buổi tối tệ | J1 / UN-002 |
| **Lưu báo cáo ra tệp từ một giao diện chỉ có nền tối** | Tệp in ra đen kịt hoặc bảng bị cắt ngang trang | Tệp đọc được trên nền sáng và bảng không bị cắt ngang trang — bản để in là một bản riêng, không phải ảnh chụp màn hình nền tối | J1 / UN-004 |
| **Đặt "mặc định báo cáo" rồi tạo báo cáo mới** | Một preference lặng lẽ bật sẵn phụ lục tiền cho mọi tệp sau đó | Phụ lục kết quả **luôn khởi tạo tắt**; mặc định báo cáo không chạm tới nó, và màn cài đặt nói rõ vì sao | J1, J6 / UN-003, UN-018 |
| **Bản xuất chứa bản chép giọng nói** | Nội dung riêng tư rời khỏi sản phẩm cùng tệp đưa cho bên thứ ba | Chưa chốt bản chép và tệp âm thanh có nằm trong bản xuất hay không — xem OQ-4. Dù chốt thế nào, người chơi phải **biết trước khi xuất** là trong tệp có gì | J2 / UN-005, UN-007 |
| **Một tệp đính kèm bị mất trên đĩa nhưng vẫn còn tên trong nhật ký** | Gói sao lưu thiếu một phần mà không ai biết | Việc tạo gói **nói rõ phần nào thiếu** thay vì lặng lẽ bỏ qua; bản kê phản ánh đúng thứ thật sự có trong gói | J3 / UN-008, UN-009 |
| **Hết chỗ giữa lúc đang dựng gói sao lưu** | Một gói dở dang trông như gói thật, tin vào nó là mất dữ liệu | Việc tạo gói dừng lại khi chạm ngưỡng dung lượng tạm, **xoá phần dở dang**, và nói rõ là chưa có gói nào | J3, J7 / UN-008, UN-017 |
| **Gói sao lưu sai mã kiểm tra** | Khôi phục từ một gói hỏng | **Bị từ chối trước khi động vào dữ liệu hiện tại**, kèm chỉ rõ phần nào không khớp | J4 / UN-012 |
| **Gói bị sửa tay**: đường dẫn lạ (tuyệt đối, lùi ra ngoài, liên kết mềm, trùng tên), phần tử kiểu lạ, hoặc phần bung ra lớn bất thường | Ghi đè ra ngoài chỗ của nó, hoặc làm đầy ổ đĩa ngay lúc khôi phục | **Bị từ chối trước khi mở gói ra**, không phải sau — cả ba loại | J4 / UN-012 |
| **Tạo gói sao lưu giữa lúc phiên đang chạy, hoặc còn việc chép lời / đóng băng tape** | Gói nửa vời trông y hệt gói đủ; chỉ lộ ra lúc cần khôi phục | Hoặc chờ việc nền xong rồi mới chụp, hoặc từ chối kèm nêu rõ việc đang chạy và khi nào xong. Không bao giờ tạo ra một gói nửa vời | J3, J7 / UN-024 |
| **Khôi phục khi chỗ trống không đủ** cho cả bản đang có, bản đang dựng và ảnh chụp lùi | Khôi phục chết giữa chừng đúng lúc ổ đã đầy — mà đó chính là lúc hay phải khôi phục nhất | Kiểm chỗ trống **trước**, từ chối sớm kèm con số cần bao nhiêu | J4, J7 / UN-012, UN-017 |
| **Hai thao tác dữ liệu chạy chồng nhau** (xoá sạch trong lúc đang dựng gói, khôi phục trong lúc đang xuất, hai tab cùng chạy khôi phục) | Hậu quả là mất dữ liệu không lấy lại được | Tại một thời điểm chỉ **một** thao tác dữ liệu chạy được; thao tác thứ hai bị từ chối kèm nêu rõ việc đang chạy và khi nào xong | J3, J4, J5 / UN-011, UN-012 |
| **Khôi phục một gói cũ lên máy đang dùng** | Không rõ hiệu chỉnh tay cầm, khung giờ, mặc định báo cáo hiện tại có bị đặt lại theo máy cũ không — kịch bản thật là dựng máy chủ mới rồi khôi phục | Chưa chốt preference thuộc nhóm bị thay hay nhóm được giữ — xem OQ-9. Chừng nào chưa chốt, việc khôi phục phải **nói rõ nó sẽ chạm vào những gì** trước khi chạy | J4, J6 / UN-012, UN-018 |
| **Xoá sạch xong, không rõ các thiết lập còn hay mất** | Xoá xong máy về một trạng thái lạ, phải hiệu chỉnh lại tay cầm từ đầu | Chưa chốt — cùng OQ-9. UN-016 hiện chỉ khẳng định **nội dung nhật ký** không còn sót lại | J5 / UN-016 |
| **Tải gói sao lưu chỉ bằng một cú bấm** | Toàn bộ giọng nói cá nhân rời khỏi máy chủ mà không có cửa nào | Cần một lần xác nhận gần đây, không dựa vào việc cửa sổ đang mở sẵn | J3 / UN-025 |
| **Gói sao lưu cũ làm sống lại dữ liệu đã cố ý xoá** | Đã xoá riêng giọng nói theo đường của `voice-journal`, rồi khôi phục một gói cũ hơn — giọng nói quay về | Gói đã tạo nằm **ngoài vòng kiểm soát của sản phẩm**, đúng như tệp xuất. Người chơi phải được nói rõ điều này ở đúng hai chỗ: lúc xoá riêng giọng nói và lúc xoá sạch (lời mời sao lưu ở J5 tạo ra chính bản sao đó) — xem OQ-5 | J4, J5 / UN-015 |
| **Gói của một phiên bản dữ liệu không tương thích** | Khôi phục xong thì nhật ký hỏng theo cách khó thấy | Kiểm tính tương thích trước; không tương thích thì từ chối kèm lý do. Mức hỗ trợ khôi phục lên phiên bản mới hơn còn chưa chốt — xem OQ-6 | J4 / UN-012 |
| **Bấm khôi phục khi còn vị thế mở hoặc phiên đang chạy** | Dữ liệu bị thay giữa lúc đang giao dịch | **Bị từ chối**, kèm nêu rõ điều kiện còn thiếu | J4 / UN-011 |
| **Bấm khôi phục khi đang có việc chép lời hoặc đóng băng tape chạy nền** | Một bản ghi âm đang chép dở ghi đè lên dữ liệu vừa khôi phục | **Bị từ chối** cho tới khi việc nền xong — cùng mức bảo vệ như với vị thế mở | J4 / UN-011 |
| **Khôi phục hỏng giữa chừng** (mất điện, đứt kết nối) | Nhật ký kẹt ở trạng thái nửa vời | Dữ liệu hiện tại được giữ nguyên cho tới khi bản mới dựng xong và kiểm xong; hỏng giữa chừng thì mở lại vẫn là dữ liệu cũ, đầy đủ | J4 / UN-012 |
| **Khôi phục xong nhưng số lượng không khớp bản kê** | Người chơi tin là đã khôi phục đủ trong khi thiếu | Kết quả đối chiếu **hiện ra cho người chơi xem**, và phần lệch được nêu rõ thay vì báo một dòng "thành công" | J4 / UN-013 |
| **Bấm xoá sạch khi còn phiên hoặc vị thế đang chạy** | Xoá giữa lúc đang giao dịch, không lấy lại được | **Bị từ chối**, kèm điều kiện để làm được — cùng mức bảo vệ mà `voice-journal` đặt cho đường xoá riêng của nó | J5 / UN-014 |
| **Gõ sai câu xác nhận, hoặc không giữ đủ hai giây** | Xoá nhầm | Không có gì bị xoá; hai điều kiện phải cùng đạt | J5 / UN-014 |
| **Từ chối lời mời sao lưu rồi xoá sạch** | Mất hết không lấy lại được | Đây là lựa chọn có chủ ý của người chơi và được tôn trọng — **không có bản sao ẩn nào** được giữ để "phòng khi hối hận" | J5 / UN-015 |
| **Đã xoá riêng dữ liệu giọng nói trước đó, rồi sao lưu** | Gói có bản chép mà không có tiếng, dễ đọc nhầm là gói thiếu | Gói phản ánh đúng thứ đang có, và bản kê nói rõ. Ranh giới giữa hai đường xoá còn cần chốt — xem OQ-5 | J3, J5 / UN-008 |
| **Gửi một thay đổi cài đặt chứa khoá thuộc nhóm cấm** | Một chốt an toàn bị đổi qua đường vòng | **Bị từ chối cả gói thay đổi**, không được âm thầm bỏ qua khoá cấm rồi báo thành công — người chơi sẽ tưởng thứ mình gửi đã được nhận | J6 / UN-019 |
| **Đổi một preference sang giá trị vô lý** (khung giờ ngược, biểu tượng ngoài danh sách máy chủ cho phép) | Cấu hình hỏng làm hỏng phiên sau | Bị từ chối tại chỗ kèm lý do; giá trị cũ giữ nguyên | J6 / UN-018 |
| **Hạn giữ nhật ký trong cài đặt mâu thuẫn với "nhật ký giữ vô hạn"** | Hai tài liệu hứa hai điều ngược nhau; người chơi có thể vô tình bật một cơ chế tự xoá | Chưa chốt — xem OQ-2. Chừng nào chưa chốt thì **không cơ chế tự xoá nào được bật mặc định** | J6 / UN-018 |
| **Ổ đĩa hết chỗ giữa một phiên đang chạy** | Cái hỏng đầu tiên là một buổi tối đang giao dịch | Cảnh báo phải tới **đủ sớm** để không bao giờ rơi vào tình huống này; ngưỡng và nơi hiện cảnh báo còn chưa chốt — xem OQ-3 | J7 / UN-017 |
| **Người chơi bỏ qua cảnh báo dung lượng nhiều lần** | Vẫn đi tới chỗ hết chỗ | Cảnh báo lặp lại khi mở phần dữ liệu, nhưng **không leo thang thành lời nhắc theo nhịp** — không có "đã bao nhiêu ngày kể từ" | J7 / UN-017 |
| **Playbook đã ngừng dùng nằm trong kỳ báo cáo** | Lát cắt theo playbook mất một phần lịch sử | Báo cáo vẫn hiện nó với đầy đủ lịch sử của kỳ đó — cùng cách deck đang làm | J1 / UN-002 |
| **Số liệu trong báo cáo lệch so với deck** | Người chơi không biết tin con số nào | Chỉ có một nơi tính; báo cáo render lại đúng con số đó. Lệch nghĩa là báo cáo sai, không phải deck sai | J1 / UN-002 |

## 7. User-side Constraints

* **Báo cáo và cài đặt mở bằng tay cầm, thao tác bằng chuột và bàn phím.** Đây là bề mặt ngoài phiên; không thiết kế việc chọn kỳ, tích phụ lục hay xử lý tệp cho tay cầm.
* **Feature này không tính số liệu của riêng nó.** Nó render lại con số `process-score` và `daily-journal` đã chốt, và đóng gói dữ liệu tám feature kia sinh ra.
* **Không có đường nhập dữ liệu từ bên ngoài.** Khôi phục chỉ nhận gói do chính sản phẩm này tạo ra; không có nhập lịch sử sàn dưới bất kỳ hình thức nào.
* **Chốt an toàn sống ngoài cơ sở dữ liệu và sai thì sản phẩm không khởi động** — nên chúng cố tình không có mặt trong giao diện cài đặt, kể cả ở dạng chỉ đọc có thể gây hiểu nhầm là sửa được.
* **Tệp xuất ra rời khỏi vòng kiểm soát của sản phẩm.** Ràng buộc mà sản phẩm giữ được nằm ở **lúc tạo tệp**: không tự đưa tiền vào, không bao giờ đưa bí mật vào. Sau khi tệp đã ở trên máy người chơi, việc nó đi đâu là quyết định của người chơi.
* **Gói sao lưu chứa dữ liệu giọng nói cá nhân** và nằm trên máy người chơi. Nơi lưu, cách bảo vệ và cách xoá phải rõ ràng (`docs/_shared/project-profile.md`, mục Compliance). Xem OQ-1.
* **Tại một thời điểm chỉ một thao tác dữ liệu chạy được** — tạo gói, khôi phục, xuất và xoá sạch loại trừ lẫn nhau. Đây là ràng buộc an toàn, không phải giới hạn hiệu năng.
* **Kỳ báo cáo dùng đúng quy tắc "một ngày là một buổi tối" của `daily-journal`**, không cắt theo ngày lịch — nếu không, cùng một khoảng ngày sẽ ra hai kết quả khác nhau giữa báo cáo và bản đồ nhiệt. Mốc gom cụ thể còn treo ở OQ-6 của `daily-journal`.
* **Gói sao lưu đã tạo nằm ngoài vòng kiểm soát của sản phẩm**, đúng như tệp xuất. Xoá sạch không với tới được các gói đã nằm trên máy người chơi — và một gói cũ khôi phục về sẽ mang theo cả những thứ đã cố ý xoá sau đó.
* Chỉ chạy trên Chrome desktop, chỉ nền tối. Không giao diện sáng, không giao diện di động.
* Chỉ tài khoản demo. **Báo cáo không phải lời khuyên đầu tư** — dòng chữ demo / giải trí / không phải lời khuyên phải có mặt cả trong tệp báo cáo, vì tệp đó có thể được đọc ngoài mọi ngữ cảnh.
* Giao diện sản phẩm bằng tiếng Anh; tài liệu nghiệp vụ bằng tiếng Việt.

## 8. Assumptions & Validation

| ID | Assumption | Impact if Wrong | Validation Status | Next Action |
|---|---|---|---|---|
| A-01 | Xuất dữ liệu **chủ yếu để đưa cho một trợ lý AI ngoài đọc**, nên JSON đủ ngữ cảnh là ưu tiên số một và CSV phẳng là thứ yếu | Nếu thực tế lại dùng bảng tính là chính, ưu tiên đảo ngược: CSV cần được thiết kế kỹ hơn JSON | **Đã xác nhận** 2026-08-28 (người chơi chốt) | Kiểm lại sau ba lần dùng thật: bản nào thực sự được mở. Đọc cùng chu kỳ quý của Mục 9 — ba tháng đầu không xuất lần nào thì chính giá trị của feature này cần xem lại, không chỉ thứ tự ưu tiên định dạng |
| A-02 | Bản xuất JSON **tự đủ nghĩa** để một trợ lý AI chưa biết gì về sản phẩm đọc hiểu | Xuất xong vẫn phải giải thích thủ công từng trường — mục đích chính của việc xuất coi như hỏng | Chưa xác nhận — `phase-13` liệt kê *nội dung* bản xuất nhưng không nói gì về việc nó có tự giải thích được không | Thử ba câu hỏi chuẩn ở USC-003 ngay lần xuất đầu tiên, kèm vế tất định: đọc chính tệp xem có phần tự mô tả (tên trường, đơn vị, thang điểm, múi giờ) không |
| A-03 | Người chơi sao lưu **thủ công**, không theo lịch, và điều đó đủ an toàn | Không sao lưu suốt nhiều tháng rồi mất sạch — đúng rủi ro mà feature này sinh ra để chặn, nhưng bị chặn bởi chính quyết định không nhắc | 🔶 Quyết định thay user 2026-08-28 — người chơi chốt **không nhắc sao lưu định kỳ**; việc sao lưu hoàn toàn thủ công là hệ quả trực tiếp mà nguồn không nói ra | Cảnh báo dung lượng là lời nhắc duy nhất còn lại. **Bẫy tự kiểm:** quý đầu không diễn tập được USC-002 lần nào thì coi A-03 là sai và đặt lại quyết định không-nhắc-định-kỳ, thay vì để nó lặng lẽ trôi qua |
| A-04 | Ngưỡng cảnh báo dung lượng đặt được ở mức đủ sớm để còn kịp sao lưu và dọn | Cảnh báo tới quá muộn thì vô dụng; quá sớm thì thành tiếng ồn và bị bỏ qua | Chưa xác nhận — chưa có số liệu về tốc độ đầy của ổ đĩa; `voice-journal` Mục 7 ghi dung lượng giọng nói tăng ở mức không đáng kể, nên phần phình chủ yếu đến từ ảnh và tape | Đo dung lượng sinh ra mỗi tối trong 10 phiên đầu rồi đặt ngưỡng. Ứng viên nháp để OQ-3 chốt nhanh: cảnh báo khi chỗ trống còn đủ cho khoảng **20 phiên nữa** |
| A-05 | Báo cáo lấy đúng con số `process-score` và `daily-journal` đã chốt, không tính lại | Hai nơi lệch nhau thì người chơi mất niềm tin vào cả báo cáo lẫn deck | Chưa xác nhận — suy từ ràng buộc "chỉ deck tính" đã chốt ở `process-score` | Đối chiếu con số báo cáo với deck khi viết SRS |
| A-06 | Đường xoá sạch ở đây và đường **xoá riêng giọng nói** của `voice-journal` là hai đường độc lập, không đá nhau | Hai đường chồng nhau thì hoặc xoá thiếu, hoặc người chơi tưởng đã xoá hết mà chưa | Chưa xác nhận — `voice-journal-urd.md` A-06 đã ghi rõ cần thông báo cho feature này khi viết SRS | Chốt cùng OQ-5 khi viết SRS |
| A-07 | Feature này ship **sau** chín feature nguồn — tám feature đã có URD, cộng `execution-learning` (tách 2026-08-28, **chưa có URD**) là nguồn của phần lỗi sai trong báo cáo | Ship sớm thì báo cáo và gói sao lưu bao gồm những phần chưa tồn tại — dễ đọc nhầm một gói thiếu thành một gói đủ | Đây là hệ quả trực tiếp của việc feature không sinh dữ liệu của riêng nó; `phase-13` phụ thuộc phase 12 | Bản kê luôn phản ánh đúng thứ thật sự có trong gói, dù ship theo thứ tự nào. Phần lỗi sai của báo cáo có thể trống ở ngày ra mắt và báo cáo phải nói rõ điều đó thay vì để một mục rỗng |
| A-08 | Ba thước đo ở Mục 9 **kiểm được bằng chính công cụ sẵn có** (tìm chuỗi trong tệp, đối chiếu bản kê, đặt ba câu hỏi cho một trợ lý AI ngoài), không cần thêm cơ chế đo nào trong sản phẩm | Nếu phải dựng thêm cơ chế đo, ba thước đo này trở thành phạm vi phát sinh chứ không phải cách kiểm chứng | 🔶 Quyết định thay user 2026-08-28 — người chơi chưa được hỏi về cách đo; ba cách trên chọn theo hướng không thêm phạm vi | Xác nhận khi viết SRS |

## 9. User Success Criteria

| ID | User Outcome | Baseline | Target | Measurement | Review Period |
|---|---|---|---|---|---|
| USC-001 | **Không tệp nào rời khỏi sản phẩm mang theo bí mật** | Có sẵn: hiện chưa có tệp nào rời khỏi sản phẩm, nên mốc gốc là **0 lần rò rỉ** | **0 lần** — mọi bản xuất và mọi gói sao lưu, không có ngoại lệ. Đây là thước đo tuyệt đối, không phải xu hướng | Với mỗi bản xuất và mỗi gói tạo ra trong kỳ: tìm chuỗi token, biến môi trường, tên miền máy chủ và đường dẫn tuyệt đối. Một lần dính là hỏng | Hằng quý, và bắt buộc trước lần đầu đưa tệp cho bất kỳ bên thứ ba nào |
| USC-002 | **Gói sao lưu thật sự khôi phục được**, không chỉ tạo ra được | **Chưa có** — xác lập bằng lần diễn tập vòng tròn đầu tiên | Mỗi quý diễn tập một vòng sao lưu rồi khôi phục trên dữ liệu bỏ đi được: **số lượng và mã kiểm tra khớp 100%** với bản kê. Không diễn tập được coi như không đạt — một gói chưa từng khôi phục thử thì chưa phải một bản sao lưu | Chạy vòng tròn đầy đủ, đọc kết quả đối chiếu, ghi lại quý nào đạt. **Không diễn tập được trong quý đầu là một kết quả, không phải một khoảng trống** — nó chứng minh A-03 sai | Hằng quý |
| USC-003 | **Bản xuất đủ để một góc nhìn ngoài trả lời được câu hỏi dài hạn** | **Chưa có** — xác lập bằng lần xuất đầu tiên | Đưa bản xuất cho một trợ lý AI ngoài chưa biết gì về sản phẩm và hỏi ba câu: tháng nào tuân thủ tốt nhất, loại lỗi sai nào lặp lại nhiều nhất, điểm quy trình có xu hướng gì. **Cả ba trả lời được chỉ từ tệp**, không phải hỏi lại người chơi | Chạy đúng ba câu hỏi đó, đếm số câu trả lời được mà không cần giải thích thêm. Phép thử này không tất định (đổi mô hình là đổi kết quả) nên đi kèm một vế tất định: đọc chính tệp và kiểm nó có phần tự mô tả — tên trường, đơn vị, thang điểm, múi giờ của các mốc thời gian | Hằng quý |
| USC-004 | **Những thứ không được phép xuất hiện thì không bao giờ xuất hiện** | Có sẵn: **0** ở cả ba vế | **0 tệp** có con số tiền khi người chơi không tích phụ lục · **0 khoá** thuộc nhóm chốt an toàn xuất hiện trong màn cài đặt · **0 nội dung nhật ký** còn sót sau xoá sạch. Ba vế tuyệt đối như USC-001, phủ ba nhu cầu Critical (UN-003, UN-019, UN-016) mà trước đó không thước đo nào chạm tới | Rà tệp báo cáo mỗi lần đổi phần báo cáo; rà màn cài đặt mỗi lần đổi giao diện; rà nơi lưu sau mỗi lần xoá sạch | Hằng quý, và bắt buộc sau mỗi lần đổi ba bề mặt đó |

> **USC-001 và USC-003 kéo ngược nhau, và đó là chủ ý.** USC-003 muốn bản xuất mang theo càng nhiều
> ngữ cảnh càng tốt; USC-001 canh chừng đúng cái giá phải trả nếu "nhiều ngữ cảnh hơn" lặng lẽ trở
> thành "mang theo cả những thứ không được mang". **Phải đọc cùng nhau** — mỗi lần bản xuất giàu
> thêm là một lần USC-001 phải được chạy lại.
>
> **Giới hạn đã biết.** USC-002 đo được rằng gói *khôi phục được*, nhưng không đo được rằng gói
> *được tạo đủ thường xuyên*. Vế đó phụ thuộc hoàn toàn vào thói quen thủ công của người chơi (xem
> A-03), và thứ duy nhất nhắc là cảnh báo dung lượng.

## 10. Open Questions

* [x] OQ đã chốt 2026-08-28: phạm vi feature gồm cả màn cài đặt an toàn; phụ lục kết quả tiền mặc định tắt và phải tự tích (đóng OQ-6 của `process-score`); mục đích xuất dữ liệu là đưa cho trợ lý AI ngoài đọc nên JSON là ưu tiên; chỉ cảnh báo dung lượng, không nhắc sao lưu định kỳ (đóng OQ-9 của `daily-journal`).
* [ ] OQ-1: Gói sao lưu có được đặt mật khẩu hoặc mã hoá không? Nó chứa **dữ liệu giọng nói cá nhân** và nằm trên máy người chơi, có thể chép sang ổ ngoài. Không mã hoá thì đơn giản hơn nhiều nhưng bản ghi âm nằm trần trong một tệp ai cầm cũng mở được.
* [ ] OQ-2: **Mâu thuẫn xuyên tài liệu.** Cài đặt có mục *hạn giữ nhật ký* (`phase-13`), trong khi `daily-journal-urd.md` đã chốt **nhật ký giữ vô hạn, không bao giờ tự xoá thứ gì**. Hai điều này không thể cùng đúng. Bỏ mục hạn giữ, hay giữ nó như một cơ chế mặc định tắt mà người chơi tự bật? **Chốt trước khi thiết kế giao diện cho nó** — nhiều khả năng câu trả lời là bỏ hẳn, và khi đó mọi công dựng màn hình cho nó là công thừa. Cùng OQ-11 của `daily-journal`.
* [ ] OQ-3: Ngưỡng cảnh báo dung lượng là bao nhiêu, và cảnh báo hiện ở đâu? Chỉ khi mở phần dữ liệu thì có thể quá muộn; hiện lên màn hình chính giữa phiên thì vi phạm nguyên tắc màn hình chính chỉ có thứ cần cho việc giao dịch. Xem A-04.
* [ ] OQ-4: Bản xuất có kèm **bản chép giọng nói** không, và có kèm chính **tệp âm thanh** không? Mục đích đã chốt là đưa cho một trợ lý AI ngoài đọc — bản chép làm bản xuất giàu nghĩa hơn hẳn, nhưng nó cũng là phần riêng tư nhất trong toàn bộ nhật ký.
* [ ] OQ-5: Đường **xoá sạch** ở đây và đường **xoá riêng giọng nói** của `voice-journal` phân định thế nào để không đá nhau? Xoá sạch có gọi lại đường của `voice-journal`, hay tự xoá phần giọng nói? Và hai lời xác nhận có khác nhau đủ để không bấm nhầm cái này thành cái kia? Và vế thứ ba: `voice-journal` UN-010 hứa "xoá là mất hẳn", nhưng một gói sao lưu cũ khôi phục về sẽ mang giọng nói đó quay lại — người chơi được nói điều này ở đâu và lúc nào? Xem A-06 và `voice-journal-urd.md` A-06.
* [ ] OQ-6: Khôi phục một gói cũ lên một phiên bản sản phẩm **mới hơn** — nâng được tới mức nào? Nguồn `phase-13` đã chọn hướng **nâng một bản chép tạm lên rồi mới đổi chỗ**, nên câu còn lại là: gói cũ bao nhiêu phiên bản thì còn nâng được, và quá mức đó thì sản phẩm nói gì với người chơi? Từ chối im lặng nghĩa là một gói để lâu sẽ hết dùng được mà không ai biết trước.
* [ ] OQ-8: **Ai tính số tổng hợp cho một kỳ không phải một tháng trọn?** UN-001 hứa báo cáo cho một tuần và một khoảng ngày tuỳ chọn, nhưng `process-score` mới định nghĩa số tổng hợp ở mức **tháng** và mức **phiên**, còn `daily-journal` đã đẩy toàn bộ số liệu nhiều phiên sang đó. Mở rộng `process-score` cho kỳ tuỳ chọn, hay báo cáo kỳ tuỳ chọn chỉ liệt kê con số cấp phiên? Feature này **không được tự gộp** — đó là ràng buộc lõi ở Mục 7.
* [ ] OQ-9: Khôi phục có **đè các thiết lập hiện tại** không, và xoá sạch có xoá luôn chúng không? Nguồn `phase-13` đặt các preference nằm cùng chỗ với dữ liệu nhật ký, nên cả hai thao tác đều chạm tới chúng. Kịch bản thật: dựng máy chủ mới, khôi phục gói cũ, rồi máy mới bị đặt lại theo hiệu chỉnh tay cầm của máy cũ. Cả hai câu đều không hoàn tác được.
* [ ] OQ-7: Báo cáo cho một kỳ mà **trọng số các trục điểm đã đổi giữa kỳ** — tính lại toàn bộ theo trọng số hiện tại (nhất quán với cách deck làm), hay giữ nguyên con số lúc đó và ghi chú? Xem `process-score` Journey 6.

---

> **Lịch sử review.** Bản đầu 2026-08-28 (`/urd`), nguồn `phase-13` cộng 4 quyết định người chơi.
> Review bởi `@senior-ba` (6 blocking, 15 warning, 6 suggestion) và `@po-reviewer` (2 warning,
> 3 suggestion) cùng ngày; toàn bộ findings đã áp. Bốn câu mà review nêu ra nhưng người chơi chưa trả
> lời được ghi thành OQ-8, OQ-9 và mở rộng OQ-5, OQ-6 — không tự chốt.
