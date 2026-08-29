---
type: srs
feature: voice-journal
status: draft
updated: 2026-08-29
links:
  - docs/voice-journal/voice-journal-urd.md
  - docs/voice-journal/voice-journal-prd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/srs/order-execution-spec.md
  - docs/ai-desk/srs/ai-desk-spec.md
  - docs/tilt-meter/srs/tilt-meter-spec.md
  - docs/daily-journal/daily-journal-urd.md
  - docs/trade-replay/trade-replay-urd.md
---

# voice-journal — Software Requirements Specification

## 1. Scope

Đặc tả **giọng nói làm cách duy nhất để nói chuyện với sản phẩm trong lúc hai tay đang bận**: một cử chỉ
giữ-để-nói ghi lại lý do vào lệnh, cùng cử chỉ đó hỏi coach, lời nói được chép thành chữ ngay trên máy chủ
của người chơi — và tất cả **không bao giờ chạm tới đường đặt lệnh**.

**Trong phạm vi:** cử chỉ giữ-để-nói trên tay cầm và trên bàn phím · chép lời tự động chạy tại chỗ · gắn
memo vào vị thế đang chọn · đổi đích sang coach theo tab đang mở · dấu hiệu đang ghi âm + đếm ngược · dấu
hiệu đang chép lời · giữ bản ghi âm khi chép lời hỏng · sửa bản chép ngoài phiên · xoá một memo và xoá sạch
riêng dữ liệu giọng nói · đọc lời khuyên thành tiếng · tắt hẳn tính năng.

**Ngoài phạm vi:** **đặt lệnh bằng giọng nói** — không nằm trong sản phẩm ở bất kỳ phiên bản nào · điều
hướng menu bằng giọng nói · ghi âm liên tục suốt phiên · nhận dạng người nói · màn hình xem lại một lệnh
(`daily-journal`) · tìm memo theo chữ trên toàn nhật ký (`daily-journal`) · nội dung lời khuyên và việc soạn
câu để đọc (`ai-desk`) · phát memo đúng mốc thời gian trên tape (`trade-replay`) · chấm điểm lệnh
(`playbook-grading`) · đường xoá sạch **toàn sản phẩm**, xuất dữ liệu, sao lưu (`reports-export`).

> **Ranh giới cứng của tài liệu này:** *giọng nói không bao giờ mở, sửa, đóng được một lệnh, và không điều
> hướng được.* Đây **không phải quy ước** — cấu hình gán cử chỉ nói vào một nút thuộc đường đặt lệnh thì
> **sản phẩm không khởi động** (NFR-006).
>
> **Dòng quan trọng nhất của cả feature:** *chép lời hỏng thì bản ghi âm vẫn còn và vẫn gắn với lệnh.* Giá
> trị huấn luyện phải sống sót kể cả khi việc chép chữ thất bại hoàn toàn.

## 2. Actors & Stakeholders

| Actor | Loại | Mục tiêu | Trong scope? |
|-------|------|----------|--------------|
| **Người chơi — vai người nói** | người | Nói ra lý do vào lệnh mà không rời tay, không rời mắt khỏi biểu đồ | Có |
| **Người chơi — vai người đọc lại** | người | Tìm lại điều mình đã nói và sửa chỗ máy chép sai | Có |
| **Bộ chép lời** | hệ thống | Chuyển lời nói thành chữ, **chạy trên máy chủ của chính người chơi** | Có |
| **`order-execution`** | hệ thống | Sở hữu "vị thế đang chọn" và đường đặt lệnh mà giọng nói không bao giờ chạm | **Không** — ranh giới tích hợp |
| **`ai-desk`** | hệ thống | Đích đến thứ hai của cử chỉ; nhận bản chép như **lời của người dùng**, không bao giờ như mệnh lệnh | **Không** — ranh giới |
| **`tilt-meter`** | hệ thống | Nhận **sự kiện "đã ghi một memo"** làm đường ra sớm khỏi khoảng khoá | **Không** — chỉ nhận sự kiện, **không bao giờ nhận nội dung** |
| **`daily-journal`** | hệ thống | Sở hữu màn hình xem lại một lệnh — khung để đặt ba thao tác nghe/sửa/xoá lên | **Không** — ranh giới |
| **`trade-replay`** | hệ thống | Phát bản ghi âm đúng mốc thời gian; **ghi đè luật gắn memo** khi đang ở màn xem lại | **Không** — ranh giới |
| **`reports-export`** | hệ thống | Sở hữu đường xoá sạch **toàn sản phẩm**, khác đường xoá riêng giọng nói ở đây | **Không** — ranh giới |

## 3. Functional Requirements (FR)

### 3.1 Ghi memo bằng cử chỉ

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-voice-journal-001 | Cử chỉ giữ-để-nói | Giữ cử chỉ, nói, thả ra là xong. **Không nút xác nhận, không hộp thoại phải đóng, không bước đặt tên.** Toàn bộ việc ghi nhật ký một lệnh gói trong đúng một cử chỉ đã có sẵn trên tay cầm | P0 | demo | URD UN-001 |
| FR-voice-journal-002 | Tổ hợp nút là ràng buộc hiện tại, không phải nhu cầu | Cử chỉ hiện là giữ đồng thời **cặp nút vai**, hoặc giữ một phím trên bàn phím. Có thể đổi sang cặp nút sau lưng nếu tay cầm hỗ trợ | P0 | kiểm tra | URD Mục 7 |
| FR-voice-journal-003 | Bấm một nút vai vẫn là đổi khung thời gian | Bấm **một** nút vai vẫn đổi khung thời gian như cũ và **không** khởi động ghi âm. Giữ **cả cặp** mới vào ghi âm, và khi đó khung thời gian **không** đổi | P0 | test | URD Mục 6 |
| FR-voice-journal-004 | Giữ quá ngắn không tạo memo | Một lần giữ quá ngắn **không tạo memo nào** và cũng **không báo lỗi** — coi như chưa từng bấm | P0 | test | URD Mục 6 |
| FR-voice-journal-005 | Không ghi âm khi đang vũ trang hoặc đang giữ chốt an toàn | **Không vào ghi âm**, nhưng người chơi thấy rõ là chưa ghi được và **lúc nào thì ghi được** — không phải một cú bấm rơi vào hư không | P0 | test | URD Mục 6 — xem OQ-2 |
| FR-voice-journal-006 | Giới hạn một lần nói khoảng một phút | Tới giới hạn thì **dừng và gửi đi phần đã nói**, không cắt cụt im lặng và không vứt bỏ. Người chơi giữ nút tiếp lần nữa để nói phần còn lại | P0 | test | URD UN-007 |
| FR-voice-journal-007 | Ghi âm chỉ khi chủ động giữ nút | **Không ghi âm liên tục suốt phiên.** Chỉ ghi khi người chơi chủ động giữ cử chỉ | P0 | kiểm tra | URD Mục 3 |
| FR-voice-journal-008 | Chọn kiểu chỉ mở mic lúc nhấn nút | Người chơi chọn được kiểu **chỉ mở mic đúng lúc nhấn nút**, đổi lại mỗi lần nhấn chậm hơn một chút. Đây là **lựa chọn của người chơi**, không phải mặc định áp đặt | P0 | demo | URD Mục 6 |

### 3.2 Ranh giới an toàn

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-voice-journal-009 | Giọng nói không mở, sửa, đóng được một lệnh | Không tồn tại đường nào biến lời nói thành lệnh — **kể cả khi người chơi nói đúng câu "mua vàng ngay"**. Ranh giới này không phụ thuộc cách người chơi nói, cũng không phụ thuộc việc bản chép lời có đúng hay không | P0 | test | URD UN-002 |
| FR-voice-journal-010 | Giọng nói không điều hướng được | Không thao tác điều hướng menu nào phát ra được từ lời nói | P0 | test | URD Mục 3 |
| FR-voice-journal-011 | Cấu hình sai thì sản phẩm không khởi động | Cấu hình gán cử chỉ nói vào một nút thuộc đường đặt lệnh → **sản phẩm từ chối khởi động**, và nói rõ **nút nào sai, sửa thế nào**, ở nơi người chơi đang đứng — không phải chỉ trong nhật ký kỹ thuật | P0 | test | URD UN-014 |
| FR-voice-journal-012 | Bản chép là **lời của người dùng**, không phải mệnh lệnh | Bản chép gửi tới `ai-desk` luôn được nhận như lời của người dùng. Một câu mang hình thức mệnh lệnh **không** làm đổi hành vi của bàn làm việc | P0 | test | URD Mục 2 · `ai-desk` FR-004 |
| FR-voice-journal-013 | Không bao giờ làm chậm hay cản một lệnh | Ghi âm và chép lời chạy **song song** với đường đặt lệnh, không bao giờ nằm trên nó | P0 | test | URD UN-006 |
| FR-voice-journal-014 | Vào thế chuẩn bị bắn giữa lúc đang ghi âm | Memo **được gửi đi trọn vẹn**, không bị vứt bỏ, và thao tác vào lệnh **không bị chặn lại chờ nó**. Người chơi không phải chọn giữa hai thứ | P0 | test | URD UN-006 |
| FR-voice-journal-015 | Vào lệnh trong lúc máy chủ đang chép lời | Lệnh đi với **đúng tốc độ** như khi không có memo nào đang chép. Không cảnh báo, không bước chờ. Đây mới là lúc máy chủ bận nhất, nên là lúc dễ làm chậm lệnh nhất | P0 | test | URD Mục 6 |

### 3.3 Đích gắn memo

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-voice-journal-016 | Gắn vào **vị thế đang chọn** | Memo gắn vào vị thế đang được chọn trên màn hình — **cùng khái niệm** mà `order-execution` FR-041 định nghĩa | P0 | test | URD UN-004 |
| FR-voice-journal-017 | Đích đến thấy được **trước khi mở miệng** | Màn hình cho thấy memo sẽ gắn vào đâu **trước khi** người chơi bắt đầu nói | P0 | demo | URD UN-004 |
| FR-voice-journal-018 | Không có vị thế mở thì gắn vào phiên | Gắn vào **phiên** và vào **lệnh vừa đóng gần nhất trong chính phiên đó** | P0 | test | URD UN-004 |
| FR-voice-journal-019 | Giới hạn "lệnh vừa đóng gần nhất" | Chỉ tính trong **phiên hiện tại** và trong **một khoảng đủ gần**; quá khoảng đó thì gắn vào phiên | P0 | test | URD Mục 6 (🔶 A-13) — xem OQ-5 |
| FR-voice-journal-020 | Ghi memo đầu phiên | Chưa lệnh nào đóng và chưa vị thế nào mở → memo gắn vào **phiên**, và hiện rõ nó đang gắn vào phiên chứ không vào lệnh nào | P0 | test | URD Mục 6 |
| FR-voice-journal-021 | Ngoại lệ ở màn xem lại | Đang ở màn xem lại của `trade-replay`, đích gắn memo là **lệnh đang xem**, **ghi đè** luật FR-016 — vì đích đến phải là thứ người chơi đang nhìn thấy | P1 | test | `trade-replay` UN-008, A-05 — xem OQ-6 |
| FR-voice-journal-022 | Phân biệt memo lúc vào lệnh với memo lúc xem lại | Hai loại **luôn phân biệt được**, ở mọi nơi chúng xuất hiện: một cái là **lý do**, một cái là **bài học** | P1 | test | `trade-replay` UN-008 |

### 3.4 Chép lời và trạng thái

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-voice-journal-023 | Chép lời chạy trên máy chủ của chính người chơi | Dữ liệu giọng nói **không đi ra ngoài**. Không có đường gửi ra dịch vụ ngoài, **kể cả khi cấu hình sai** | P0 | kiểm tra | URD Mục 3 · Mục 7 |
| FR-voice-journal-024 | Dấu hiệu đang ghi âm và đồng hồ đếm ngược | Có dấu hiệu rõ ràng đang ghi âm cùng đồng hồ đếm ngược tới giới hạn | P0 | demo | URD UN-007 |
| FR-voice-journal-025 | Dấu hiệu đang chép lời | Sau khi thả nút, có dấu hiệu cho biết đang chép lời; nó **biến mất khi chữ hiện ra** | P0 | demo | URD UN-015 |
| FR-voice-journal-026 | Không bao giờ treo | Chép lời hỏng → dấu hiệu chuyển thành **"chưa chép được"**, **không bao giờ treo mãi** và không phải một thông báo lỗi kỹ thuật | P0 | test | URD UN-015, UN-003 |
| FR-voice-journal-027 | **Chép lời hỏng thì bản ghi âm vẫn còn** | Bản ghi âm vẫn được lưu, vẫn gắn đúng lệnh, vẫn **nghe lại được**. Chỗ đáng lẽ là chữ thì nói rõ là chưa chép được, chứ **không** biến bản ghi thành một dòng trống | P0 | test | URD UN-003 |
| FR-voice-journal-028 | Tự hạ mức chất lượng khi máy yếu | Hệ thống **tự hạ mức** chất lượng chép lời và **nói rõ đang chạy ở mức nào**; xấu nhất là tự tắt hẳn phần chép lời và nói rõ vì sao — **ghi âm vẫn chạy**. **Không bao giờ âm thầm chậm đi** | P0 | test | URD Mục 6 — xem OQ-4 |
| FR-voice-journal-029 | Nhiều memo liên tiếp | Các memo **xếp hàng** và lần lượt được chép; vượt sức chứa thì nói rõ hiện chưa nhận thêm, thay vì im lặng nuốt mất. Bản ghi âm của **mọi memo đã nhận** đều được giữ | P0 | test | URD Mục 6 |
| FR-voice-journal-030 | Trần số memo trong một giờ | Chạm trần thì nói rõ và cho biết khi nào nói tiếp được. Người chơi **biết trước con số này** | P0 | demo | URD Mục 7 — xem OQ-1 |
| FR-voice-journal-031 | Mất mạng hoặc gửi bản ghi thất bại | Hệ thống tự thử gửi lại; vẫn hỏng thì **giao bản ghi âm cho người chơi giữ lại** thay vì vứt đi, và nói rõ là chưa lưu được | P0 | test | URD Mục 6 |
| FR-voice-journal-032 | Mic biến mất giữa lúc đang nói | Dừng ngay và nói rõ đã mất mic; **phần đã nói được giữ lại và gửi đi**, không vứt bỏ cả memo | P0 | test | URD Mục 6 |
| FR-voice-journal-033 | Mic bị từ chối, không có mic, hoặc trình duyệt không hỗ trợ | Chức năng nói bị vô hiệu hoá **một cách nhìn thấy được**, kèm lý do bằng lời thường. Mọi thứ khác chạy nguyên vẹn; bàn làm việc vẫn nhận câu hỏi gõ tay | P0 | test | URD Mục 6 |

### 3.5 Hỏi coach bằng cùng cử chỉ

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-voice-journal-034 | Cùng cử chỉ, đích do tab quyết định | Đang mở một tab tư vấn của `ai-desk` → cùng cử chỉ gửi câu hỏi tới coach thay vì tạo memo. **Không phải học thêm nút nào** | P1 | test | URD UN-005 |
| FR-voice-journal-035 | Đích đến chốt **tại thời điểm bắt đầu nói** | Đổi tab giữa chừng **không** đổi nơi câu đó tới. Màn hình vẫn cho thấy đích đến đã chốt trong suốt lúc nói | P1 | test | URD UN-005 (🔶 A-12) |
| FR-voice-journal-036 | Coach không dùng được thì hạ xuống thành memo | Lời nói hướng vào tab tư vấn mà coach đang offline → câu đó **hạ xuống thành memo** kèm một dòng cho biết coach đang không dùng được. **Không bao giờ rơi mất** | P1 | test | URD Mục 6 |

### 3.6 Sửa bản chép

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-voice-journal-037 | Sửa bằng bàn phím, ngoài phiên | Sửa bằng chuột và bàn phím **ngoài phiên**; trong lúc giao dịch **không có** thao tác sửa nào cả | P1 | test | URD UN-008 |
| FR-voice-journal-038 | Bản đã sửa ghi đè bản máy chép | Bản đã sửa **ghi đè** bản máy chép; **bản ghi âm luôn giữ nguyên làm bản gốc** để đối chiếu | P1 | test | URD UN-008 (OQ-3 resolved) |
| FR-voice-journal-039 | Sửa phải nhanh gọn cho nhiều memo | Với giọng trộn Việt–Anh, sửa là **việc thường xuyên** — cách sửa phải đủ nhanh để làm được cho **hàng chục memo** trong một lần ngồi, không phải một hộp thoại nặng cho một trường hợp hiếm | P1 | demo | URD UN-008 |
| FR-voice-journal-040 | Bản chép chỉ để đọc lướt | Bản chép là thứ đọc lướt; **bản ghi âm mới là bản gốc**, luôn nghe lại được. Với giọng trộn Việt–Anh, chép sai là **trạng thái thường gặp, không phải ngoại lệ** | P1 | kiểm tra | URD Mục 6 (OQ-1 resolved) |

### 3.7 Xoá

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-voice-journal-041 | Xoá một memo tại chỗ nghe lại nó | Người chơi xoá được một memo ngay tại chỗ nghe lại nó | P1 | demo | URD UN-010 |
| FR-voice-journal-042 | Xoá đòi hành động có chủ đích rõ ràng | Vì **không có hoàn tác**, thao tác xoá đòi một hành động có chủ đích rõ ràng — không phải một cú bấm lướt qua | P1 | test | URD UN-010 (OQ-2 resolved) |
| FR-voice-journal-043 | Xoá là mất hẳn | Memo biến khỏi **mọi nơi** nó từng xuất hiện, **cả tiếng lẫn chữ**. Không thùng rác, không hoàn tác | P1 | test | URD UN-010 |
| FR-voice-journal-044 | Đường xoá sạch **riêng cho dữ liệu giọng nói** | Xoá cả bản ghi âm lẫn bản chép, **không đụng phần nhật ký còn lại**. Đây là đường riêng của feature này, khác đường xoá sạch toàn sản phẩm | P1 | test | URD UN-010 (OQ-4 resolved) — xem OQ-3 |
| FR-voice-journal-045 | Từ chối xoá khi đang trong phiên hoặc còn vị thế mở | **Bị từ chối**, kèm lý do và điều kiện để làm được — cùng mức bảo vệ mà `reports-export` đặt cho đường xoá sạch toàn sản phẩm | P1 | test | URD Mục 6 |
| FR-voice-journal-046 | Xoá memo không làm hỏng bản ghi lệnh | Lệnh từng có memo đó vẫn tra ra được bình thường, chỉ là không còn memo. **Không bản ghi nào khác hỏng theo** | P1 | test | URD Mục 6 |
| FR-voice-journal-047 | Nói rõ gói sao lưu cũ có thể làm sống lại giọng nói đã xoá | Người chơi được nói rõ điều này tại **chính thời điểm xoá** — gói sao lưu đã tạo nằm ngoài vòng kiểm soát của sản phẩm | P1 | demo | `reports-export` Mục 6 — xem OQ-3 |

### 3.8 Đọc thành tiếng và tắt tính năng

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-voice-journal-048 | Đọc lời khuyên thành tiếng, **mặc định tắt** | Lời khuyên của coach đọc thành tiếng; **mặc định tắt** và bật tắt được bất cứ lúc nào | P2 | demo | URD UN-009 — xem OQ-7 |
| FR-voice-journal-049 | Tự câm khi đang vũ trang hoặc đang bắn | Giọng đọc **câm ngay** khi người chơi vũ trang hoặc bắn | P2 | test | URD UN-009 |
| FR-voice-journal-050 | Câu bị ngắt không đọc lại | Nhận xét bị ngắt giữa chừng **không được đọc lại** — nó vẫn còn dưới dạng chữ để đọc bằng mắt. Chỉ nhận xét **mới** mới được đọc lên | P2 | test | URD Journey 6 |
| FR-voice-journal-051 | Không bao giờ đọc ra một con số tiền | Giọng đọc **không bao giờ** phát ra một con số tiền — đúng luật chung của sản phẩm | P2 | test | URD UN-009 · `order-execution` FR-047 |
| FR-voice-journal-052 | Tắt hẳn tính năng giọng nói | Tắt xong thì phần còn lại của sản phẩm chạy **y nguyên** — đặt lệnh, chấm điểm, AI desk đều không đổi. **Các memo cũ vẫn đọc lại và nghe lại được**; chỉ không ghi thêm được nữa | P1 | test | URD UN-013 |
| FR-voice-journal-053 | Không nhắc khi lệnh đóng chưa có memo | Ghi memo là **hoàn toàn tự nguyện**. Không thông báo, không dấu đỏ, không ô trống chờ điền. Một lệnh không memo là một lệnh bình thường | P0 | test | URD UN-012 |

### 3.9 Bàn phím và cấp sự kiện cho feature khác

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-voice-journal-054 | Bàn phím là đường **ngang hàng** | Ghi memo bằng bàn phím với **đúng cách dùng** (giữ để nói, thả để gửi) — đường ngang hàng, **không phải bản hạ cấp**. Đây là thứ giữ feature sống khi dongle bị rút | P0 | demo | URD UN-011 |
| FR-voice-journal-055 | Đường bàn phím dùng được **trong lúc `tilt-meter` khoá** | Đường ghi memo bằng bàn phím phải dùng được trong suốt khoảng khoá của `tilt-meter`, kể cả khi đã tắt giọng nói hoặc không có mic | P0 | test | `tilt-meter` FR-036 — xem OQ-2 |
| FR-voice-journal-056 | Cấp **sự kiện "đã ghi một memo"**, không cấp nội dung | `tilt-meter` nhận sự kiện này làm đường ra sớm khỏi khoảng khoá. Nó **không bao giờ** nhận nội dung memo | P0 | kiểm tra | `tilt-meter` FR-033, FR-035 |
| FR-voice-journal-057 | Bản ghi âm nghe lại và **tua được** | Bản ghi âm phải nghe lại và tua được, không phải nghe một mạch từ đầu — để `trade-replay` phát nó đúng mốc thời gian | P1 | kiểm tra | `trade-replay` UN-005 |
| FR-voice-journal-058 | Bản ghi âm giữ **vô thời hạn** | Không tự hết hạn. Chỉ mất khi người chơi **chủ động xoá** | P1 | kiểm tra | URD Mục 7 (OQ-5 resolved) |

## 4. Non-Functional Requirements (NFR)

| ID | Category | Requirement | Priority | Acceptance |
|----|----------|-------------|----------|------------|
| NFR-voice-journal-001 | performance | Thao tác đặt lệnh **không chậm hơn ở mức người chơi nhận ra** khi trùng thời điểm với một memo đang ghi hoặc đang chép | P0 | Đo thời gian từ lúc bấm xác nhận tới lúc rung, hai điều kiện: có và không có memo đang chép |
| NFR-voice-journal-002 | performance | Chép một memo khoảng 10 giây hoàn tất trong khoảng **chục giây** | P1 | Đo thời gian thật khi có sản phẩm; quá lâu thì hạ mức chất lượng (FR-028) |
| NFR-voice-journal-003 | reliability | **100% memo đã ghi vẫn nghe lại được và vẫn gắn đúng lệnh**, kể cả những memo có phần chữ thất bại | P0 | Đối chiếu **hai nguồn độc lập**: số lần thả nút sau khi nói, so với số memo có mặt khi mở lại lệnh |
| NFR-voice-journal-004 | reliability | Feature này chết hoàn toàn **không** làm giảm khả năng mở, đóng, thoát vị thế | P0 | Diễn tập: tắt hẳn feature rồi chạy trọn chuỗi mở phiên → vào lệnh → đóng lệnh |
| NFR-voice-journal-005 | reliability | Việc hạ mức chất lượng chép lời phải **nhìn thấy được**; không bao giờ âm thầm chậm đi | P0 | test — ép máy chủ quá tải, kiểm người chơi thấy rõ đang chạy ở mức nào |
| NFR-voice-journal-006 | security | Cấu hình gán cử chỉ nói vào một nút thuộc đường đặt lệnh → **sản phẩm không khởi động**, nêu rõ nút nào sai và cách sửa | P0 | test — dựng cấu hình sai, kiểm sản phẩm từ chối khởi động |
| NFR-voice-journal-007 | privacy | **Dữ liệu giọng nói không rời khỏi máy chủ của người chơi.** Không có đường gửi ra dịch vụ ngoài, **kể cả khi cấu hình sai** | P0 | kiểm tra — soát mọi đường ra của dữ liệu âm thanh |
| NFR-voice-journal-008 | privacy | Bản ghi âm là **dữ liệu giọng nói cá nhân**; nơi lưu và cách xoá phải nêu rõ cho người chơi | P0 | kiểm tra | Project profile — Compliance |
| NFR-voice-journal-009 | usability | Cách sửa bản chép phải đủ nhanh cho **hàng chục memo** trong một lần ngồi | P1 | demo — sửa 10 memo liên tiếp, đo cảm nhận |
| NFR-voice-journal-010 | usability | Bàn phím là đường **ngang hàng**, không phải bản hạ cấp — cùng cách dùng, cùng kết quả | P0 | demo |
| NFR-voice-journal-011 | data integrity | Bản ghi âm là **bản gốc bất biến**; bản chép có thể bị ghi đè, bản ghi âm thì không | P0 | test — sửa bản chép, bấm nghe lại: vẫn đúng câu gốc |
| NFR-voice-journal-012 | compatibility | Chỉ Chrome desktop; người chơi phải cho phép dùng mic **một lần** trong cài đặt trước khi nói được lần đầu | P0 | kiểm tra |
| NFR-voice-journal-013 | compliance | Nội dung memo và lời coach đọc ra **không phải lời khuyên đầu tư** | P0 | kiểm tra | Project profile |
| NFR-voice-journal-014 | usability | Giao diện tiếng Anh; tài liệu nghiệp vụ tiếng Việt | P0 | kiểm tra |

## 5. Business Rules

| ID | Rule | Trigger | Implements FR | Source |
|----|------|---------|---------------|--------|
| BR-voice-journal-001 | **Giọng nói không bao giờ mở, sửa, đóng được một lệnh và không điều hướng được** — cưỡng chế lúc khởi động, không phải bằng quy ước | Khởi động · mọi lần nói | FR-009, FR-010, FR-011 | URD UN-002, UN-014 |
| BR-voice-journal-002 | **Chép lời hỏng thì bản ghi âm vẫn còn và vẫn gắn với lệnh.** Bản ghi âm là bản gốc; bản chép chỉ để đọc lướt | Chép lời thất bại | FR-027, FR-040 | URD UN-003 |
| BR-voice-journal-003 | Giọng nói **không bao giờ nằm trên đường đặt lệnh**. Vào thế bắn giữa lúc đang ghi → memo được gửi trọn vẹn, lệnh không chờ nó | Ghi âm/chép lời trùng thời điểm với một lệnh | FR-013, FR-014, FR-015 | URD UN-006 |
| BR-voice-journal-004 | Memo gắn vào **vị thế đang chọn**; không có vị thế mở thì gắn vào phiên và lệnh vừa đóng gần nhất **trong chính phiên đó**, trong một khoảng đủ gần | Mỗi lần ghi memo | FR-016, FR-018, FR-019 | URD UN-004 |
| BR-voice-journal-005 | Đang ở màn xem lại thì đích là **lệnh đang xem** — ngoại lệ có chủ ý của BR-004 | Ghi memo trong màn xem lại | FR-021 | `trade-replay` A-05 (🔶) |
| BR-voice-journal-006 | Đích đến của lời nói **chốt tại thời điểm bắt đầu nói**; đổi tab giữa chừng không đổi nơi câu đó tới | Đổi tab trong lúc đang giữ nút | FR-035 | URD (🔶 A-12) |
| BR-voice-journal-007 | Bản đã sửa **ghi đè** bản máy chép; bản ghi âm **luôn giữ nguyên** | Sửa bản chép | FR-038 · NFR-011 | URD OQ-3 resolved |
| BR-voice-journal-008 | **Xoá là mất hẳn** — không thùng rác, không hoàn tác. Bù lại bằng cửa xác nhận có chủ đích và việc từ chối xoá khi đang trong phiên | Xoá một memo · xoá sạch giọng nói | FR-042, FR-043, FR-045 | URD OQ-2 resolved |
| BR-voice-journal-009 | Bản ghi âm giữ **vô thời hạn**; chỉ mất khi người chơi chủ động xoá | Luôn luôn | FR-058 | URD OQ-5 resolved |
| BR-voice-journal-010 | **Không nhắc khi lệnh đóng chưa có memo.** Ghi memo hoàn toàn tự nguyện | Lệnh đóng | FR-053 | URD UN-012 |
| BR-voice-journal-011 | Giọng đọc **tự câm** khi đang vũ trang hoặc đang bắn, và **không bao giờ đọc ra một con số tiền** | Coach có nhận xét trong lúc ARM/FIRE | FR-049, FR-051 | URD UN-009 |
| BR-voice-journal-012 | `tilt-meter` nhận **sự kiện "đã ghi một memo"**, **không bao giờ** nhận nội dung memo | Ghi memo trong khoảng khoá | FR-056 | `tilt-meter` BR-006 |
| BR-voice-journal-013 | Bàn phím là đường **ngang hàng**; nó phải dùng được cả trong lúc `tilt-meter` khoá | Tay cầm hỏng · đang bị khoá | FR-054, FR-055 | URD UN-011 · `tilt-meter` FR-036 |
| BR-voice-journal-014 | Bản chép gửi tới `ai-desk` luôn là **lời của người dùng**, không bao giờ là mệnh lệnh | Hỏi coach | FR-012 | `ai-desk` BR-003 |

## 6. Error Matrix

| Error ID | Title | Trigger | Severity | Related FR | Screen state | Recovery |
|----------|-------|---------|----------|------------|--------------|----------|
| E-voice-journal-001 | **Cấu hình gán cử chỉ nói vào nút đường đặt lệnh** | Cấu hình sai | **critical** | FR-011 | **Sản phẩm không khởi động**; nói rõ nút nào sai và cách sửa **ở nơi người chơi đang đứng** | Ranh giới an toàn quan trọng nhất bị phá bởi một dòng cấu hình — không được phép chạy với ràng buộc đã hỏng |
| E-voice-journal-002 | Chép lời thất bại | Quá tải, quá giờ, hoặc hỏng hẳn | **critical** | FR-026, FR-027 | Dấu hiệu chuyển thành **"chưa chép được"** — không phải dòng trống, không phải lỗi kỹ thuật, **không treo mãi** | **Bản ghi âm vẫn ở đó, vẫn gắn đúng lệnh, vẫn nghe lại được.** Đây là dòng quan trọng nhất của cả feature |
| E-voice-journal-003 | Mic bị từ chối, không có mic, hoặc trình duyệt không hỗ trợ | Chưa cấp quyền, hoặc thiếu thiết bị | major | FR-033 | Chức năng nói vô hiệu hoá **nhìn thấy được**, kèm lý do bằng lời thường | Mọi thứ khác chạy nguyên vẹn; bàn phím (FR-054) và câu hỏi gõ tay vẫn dùng được |
| E-voice-journal-004 | Mic biến mất giữa lúc đang nói | Rút tai nghe, thiết bị ngắt | major | FR-032 | Dừng ngay và nói rõ đã mất mic | **Phần đã nói được giữ lại và gửi đi**, không vứt bỏ cả memo |
| E-voice-journal-005 | Giữ nút nói khi đang vũ trang hoặc đang giữ chốt an toàn | Bấm đúng khoảnh khắc lý do còn nóng nhất | minor | FR-005 | **Không vào ghi âm**, nhưng thấy rõ chưa ghi được và **lúc nào thì ghi được** | Không phải một cú bấm rơi vào hư không. Xem OQ-2 |
| E-voice-journal-006 | Vào thế chuẩn bị bắn giữa lúc đang ghi âm | Cơ hội xuất hiện lúc đang nói | minor | FR-014 | Memo **được gửi trọn vẹn**; thao tác vào lệnh đi bình thường | Không phải chọn giữa hai thứ |
| E-voice-journal-007 | Mất mạng hoặc gửi bản ghi thất bại | Mạng đứt sau khi thả nút | major | FR-031 | Tự thử gửi lại; vẫn hỏng thì **giao bản ghi âm cho người chơi giữ lại** | Nói rõ là chưa lưu được, không vứt đi |
| E-voice-journal-008 | Nói quá thời lượng cho phép | Vượt giới hạn khoảng một phút | minor | FR-006 | Đồng hồ đếm ngược cho thấy sắp hết; tới giới hạn thì **dừng và gửi phần đã nói** | Giữ nút tiếp lần nữa để nói phần còn lại |
| E-voice-journal-009 | Bấm nhầm rồi thả ngay, memo gần như rỗng | Giữ quá ngắn | minor | FR-004 | **Không tạo memo nào** và cũng không báo lỗi | Coi như chưa từng bấm — memo rác làm phồng chính con số SC-01 đo |
| E-voice-journal-010 | Bấm nhầm một nút vai thay vì giữ cả cặp | Trượt tay | minor | FR-003 | Vẫn là đổi khung thời gian như cũ; **không** khởi động ghi âm | Giữ cả cặp mới vào ghi âm, và khi đó khung thời gian **không** đổi |
| E-voice-journal-011 | Đổi tab bàn làm việc giữa lúc đang giữ nút nói | Trượt tay hoặc đổi ý | minor | FR-035 | Đích đến **chốt tại thời điểm bắt đầu nói**; màn hình vẫn cho thấy đích đã chốt | Không bao giờ có chuyện nói xong mới biết vừa nói vào đâu |
| E-voice-journal-012 | Từ hai vị thế mở trở lên | Nhiều vị thế cùng lúc | major | FR-016, FR-017 | Memo gắn vào **vị thế đang chọn**; màn hình cho thấy rõ **trước khi** người chơi mở miệng | Gắn nhầm là lỗi **không ai phát hiện ra** cho tới khi xem lại |
| E-voice-journal-013 | Ghi memo đầu phiên, chưa lệnh nào đóng và chưa vị thế nào mở | Đầu buổi | minor | FR-020 | Memo gắn vào **phiên**, và hiện rõ nó đang gắn vào phiên | — |
| E-voice-journal-014 | Lệnh vừa đóng gần nhất đã cách quá lâu | Memo lúc 23h, lệnh đóng lúc 20h | minor | FR-019 | Gắn vào **phiên** thay vì lệnh đó | Khoảng cụ thể chốt ở OQ-5 |
| E-voice-journal-015 | Coach offline mà lời nói hướng vào tab tư vấn | AI desk không dùng được | minor | FR-036 | Câu đó **hạ xuống thành memo** kèm dòng cho biết coach đang không dùng được | **Không bao giờ rơi mất** |
| E-voice-journal-016 | Bản chép sai câu chữ | Giọng trộn Việt–Anh | minor | FR-040 | Bản chép chỉ để đọc lướt; **bản ghi âm mới là bản gốc** | Sửa lại bằng bàn phím ngoài phiên. Đây là **trạng thái thường gặp, không phải ngoại lệ** |
| E-voice-journal-017 | Nhiều memo nói liên tiếp trong thời gian ngắn | Nói dồn dập | minor | FR-029 | Các memo **xếp hàng**; vượt sức chứa thì nói rõ hiện chưa nhận thêm | Bản ghi âm của **mọi memo đã nhận** đều được giữ — không im lặng nuốt mất |
| E-voice-journal-018 | Chạm trần số memo trong một giờ | Nói quá nhiều | minor | FR-030 | Nói rõ đã chạm trần và khi nào nói tiếp được | Người chơi **biết trước** con số — xem OQ-1 |
| E-voice-journal-019 | Máy chủ không đủ sức chép lời | Phần cứng yếu | major | FR-028 | **Tự hạ mức** và nói rõ đang chạy ở mức nào; xấu nhất tự tắt phần chép lời và nói rõ vì sao | **Ghi âm vẫn chạy.** Không bao giờ âm thầm chậm đi |
| E-voice-journal-020 | Đèn báo ghi âm hiện suốt phiên | Mic mở liên tục | minor | FR-008 | Chọn được kiểu chỉ mở mic đúng lúc nhấn nút | Lựa chọn của người chơi, không phải mặc định áp đặt |
| E-voice-journal-021 | Tay cầm hết pin hoặc rút dongle giữa phiên | Mất tay cầm | major | FR-054 | Vẫn ghi memo được bằng bàn phím với **đúng cách dùng** | Đường **ngang hàng**, không phải bản hạ cấp. Đây cũng là đường ra khỏi khoá của `tilt-meter` |
| E-voice-journal-022 | Nhận xét của coach bị ngắt giữa chừng | Vũ trang, hoặc có nhận xét mới | minor | FR-050 | Câu bị ngắt **không đọc lại**, nhưng vẫn còn dưới dạng chữ | Chỉ nhận xét **mới** mới được đọc lên |
| E-voice-journal-023 | Xoá một memo đang được nơi khác dùng tới | Một lệnh cũ đang mở xem | minor | FR-046 | Lệnh vẫn nguyên vẹn và vẫn tra ra được; chỉ phần memo biến mất | **Không bản ghi nào khác hỏng theo** |
| E-voice-journal-024 | Bấm xoá sạch giọng nói khi đang có phiên hoặc còn vị thế mở | Xoá nhầm lúc đang giao dịch | major | FR-045 | **Bị từ chối**, kèm lý do và điều kiện để làm được | Cùng mức bảo vệ mà `reports-export` đặt cho đường xoá sạch toàn sản phẩm |
| E-voice-journal-025 | Tắt hẳn tính năng giọng nói | Người chơi không dùng nữa | minor | FR-052 | Memo cũ **vẫn đọc lại và nghe lại được**; chỉ không ghi thêm được nữa | Đặt lệnh, chấm điểm, AI desk không đổi gì |

## 7. Success Criteria

| ID | Outcome nghiệp vụ | Đo bằng | Mốc đạt |
|----|-------------------|---------|---------|
| SC-voice-journal-01 | Người chơi thật sự dùng giọng nói, thay vì bỏ sau vài tuần | Đếm số lệnh có memo trên tổng số lệnh, đọc cuối tháng **kèm đường xu hướng theo tháng**. Memo quá ngắn không tính vào tử số | Cao hơn baseline sau 3 tháng, **và** tỷ lệ tháng 3 không thấp hơn tháng 1 quá 10 điểm phần trăm |
| SC-voice-journal-02 | *(ràng buộc tuyệt đối)* Lời đã nói **không bao giờ mất** | Đối chiếu **hai nguồn độc lập**: số lần thả nút sau khi nói, so với số memo có mặt khi mở lại lệnh. Chỉ đếm memo đã lưu thì memo mất **trước khi** lưu sẽ vô hình | 100%, kể cả memo có phần chữ thất bại. **Một trường hợp mất là một lỗi phải sửa**, không phải một con số phần trăm để cải thiện |
| SC-voice-journal-03 | *(ranh giới)* Giọng nói không bao giờ ảnh hưởng việc đặt lệnh | Đếm số lần một thao tác đặt lệnh bị chặn, phải bấm lại, hoặc nhận phản hồi rung **muộn tới mức người chơi nhận ra**, khi trùng thời điểm với memo đang ghi hoặc đang chép | 0 lần, **và** 0 lệnh phát sinh từ lời nói |
| SC-voice-journal-04 | Bản chép đủ để đọc lướt nhận ra memo nói về chuyện gì | Người chơi **tự chấm tay** 20 memo gần nhất theo ba mức: đúng ý / sai nhưng đoán ra / không hiểu gì | **≥ 70%** ở hai mức đầu. **Dưới ngưỡng nghĩa là quyết định chấp nhận bản chép kém không đứng vững và phải mở lại** |
| SC-voice-journal-05 | Việc nói không làm hỏng nhịp thao tác trên tay cầm | Đếm số lần vào thế chuẩn bị bắn khi đang ghi âm và kết quả của chúng, kèm ghi nhận chủ quan cuối phiên | Người chơi không thấy phải chọn giữa "ghi memo" và "kịp vào lệnh"; số memo bỏ dở vì sợ lỡ nhịp **tiến về không** |
| SC-voice-journal-06 | Nhánh đọc-thành-tiếng có thật sự được dùng, hay chỉ nằm đó | Đếm số phiên có bật, và số lần bật rồi tắt lại trong cùng phiên | Sau một tháng vẫn bật ở đa số phiên. **Bật rồi tắt lại trong cùng phiên ≥ 3 lần → coi như nhánh này không đáng giữ** |

> **SC-01 tới SC-05 đọc từ dữ liệu của chính feature này**, nên đo được ngay khi feature chạy — không phải
> chờ feature khác. Đây là điểm khác biệt so với `playbook-grading` và `tilt-meter`.
>
> **SC-04 phải tự chấm tay, không đo tự động được** — "đọc lướt có hiểu không" là phán đoán của người đọc.
>
> **Nếu SC-01 tụt dần, phương án ứng phó là làm cử chỉ dễ hơn — không phải thêm nhắc nhở.** FR-053 đã bỏ đi
> đòn bẩy duy nhất để giữ tỷ lệ này, và đó là lựa chọn có ý thức.
>
> **SC-06 là thước đo duy nhất hỏi "tính năng này có đáng tồn tại không"** thay vì "nó chạy tốt không". Đó
> là lý do FR-048..051 ở P2.

## 8. Data Entities (tóm tắt — chi tiết ở `voice-journal-erd.md`)

| Entity | Ý nghĩa nghiệp vụ | Thông tin nghiệp vụ cần lưu |
|--------|-------------------|------------------------------|
| **Memo** | Một lần người chơi nói ra điều gì đó | Thời điểm bắt đầu và kết thúc nói · **đích gắn** (vị thế nào / phiên nào / lệnh đang xem nào) · **loại: lý do lúc vào lệnh hay bài học lúc xem lại** · trạng thái chép lời · đường vào (tay cầm hay bàn phím) |
| **Bản ghi âm** | Bản gốc bất biến của một memo | Thuộc memo nào · thời lượng · **giữ vô thời hạn** · nghe lại và **tua được** · nằm trên máy chủ của chính người chơi |
| **Bản chép** | Chữ đọc lướt của một memo | Thuộc memo nào · nội dung máy chép · **nội dung người chơi đã sửa (ghi đè)** · trạng thái: đã chép / chưa chép được / đang chép · mức chất lượng đã dùng |
| **Câu hỏi tới coach** | Một lần lời nói đi tới `ai-desk` thay vì thành memo | Thuộc memo/lượt nói nào · tab đang mở lúc **bắt đầu nói** · đã hạ xuống thành memo hay chưa (khi coach offline) |
| **Sự kiện "đã ghi một memo"** | Tín hiệu cấp cho `tilt-meter` | Thời điểm · phiên nào. **Không chứa nội dung memo** |
| **Trạng thái tính năng** | Bật/tắt giọng nói và đọc-thành-tiếng | Bật hay tắt · thời điểm đổi · **số lần bật rồi tắt lại trong cùng phiên** (nguồn số cho SC-06) |

> **Không có entity "nội dung memo gửi cho tilt-meter"** — đó là ranh giới, không phải một thiếu sót
> (FR-056, BR-012).

## 9. Flows (tóm tắt — chi tiết ở `voice-journal-flows.md`)

| Flow | Tóm tắt | Nguồn |
|------|---------|-------|
| Nói ra lý do vào lệnh, giữa phiên | Giữ cử chỉ → dấu hiệu ghi âm + đếm ngược + **đích đến hiện trước khi nói** → nói → thả → dấu hiệu chép lời → chữ hiện ra → memo nằm cùng chỗ với vị thế đang chọn | URD Journey 1 |
| Máy chép lời chết, lời nói vẫn còn | Ghi memo bình thường → chép lời thất bại → dấu hiệu chuyển thành **"chưa chép được"** → bản ghi âm vẫn ở đó, vẫn gắn đúng lệnh, vẫn bấm nghe lại được | URD Journey 2 |
| Hỏi coach bằng chính cử chỉ đó | Mở tab tư vấn → giữ cử chỉ và nói → lời đi tới coach **như một câu hỏi**, không phải memo → câu trả lời quay về đúng chỗ đọc lời khuyên | URD Journey 3 |
| Sửa lại bản chép sai, sau phiên | Ngoài phiên mở lại một lệnh cũ → đọc memo → sửa bằng bàn phím, đủ nhanh cho nhiều memo → bản đã sửa ghi đè, **bản ghi âm giữ nguyên** | URD Journey 4 |
| Xoá một memo, hoặc xoá sạch giọng nói | Mở memo → chọn xoá → hành động **có chủ đích rõ ràng** → memo biến khỏi mọi nơi, cả tiếng lẫn chữ. Đường xoá sạch nằm trong cài đặt, **bị từ chối khi đang trong phiên hoặc còn vị thế mở** | URD Journey 5 |
| Nghe coach đọc thành tiếng | Bật (mặc định tắt) → coach có nhận xét, được đọc lên → người chơi vũ trang → giọng đọc **câm ngay** → câu bị ngắt **không đọc lại** | URD Journey 6 |

## 10. Screens (tóm tắt — chi tiết ở `ascii-wireframe/`)

| Màn hình | Vai trò | Ghi chú ranh giới |
|----------|---------|-------------------|
| **Dấu hiệu ghi âm trên HUD** | Đang ghi · đồng hồ đếm ngược · **đích đến memo sẽ gắn vào** | Trên HUD do `order-execution` sở hữu. Đích đến phải hiện **trước khi người chơi mở miệng** |
| **Dấu hiệu đang chép lời** | Cho biết việc chép đang chạy | Biến mất khi chữ hiện ra, hoặc chuyển thành "chưa chép được". **Không bao giờ treo** |
| **Khối memo trong màn xem lại một lệnh** | Nghe lại · sửa · xoá | Khung màn hình thuộc `daily-journal`; feature này chỉ sở hữu **nội dung memo và ba thao tác** |
| **Trang sửa bản chép** | Sửa nhanh cho nhiều memo trong một lần ngồi | Bề mặt **ngoài phiên**, chuột và bàn phím. Trong lúc giao dịch **không có đường nào dẫn tới đây** |
| **Mục xoá sạch giọng nói trong cài đặt** | Đường xoá riêng dữ liệu giọng nói | Màn cài đặt thuộc `reports-export`. **Khác** đường xoá sạch toàn sản phẩm — xem OQ-3 |
| **Mục bật/tắt giọng nói và đọc-thành-tiếng** | Bật/tắt hai nhánh độc lập | Cũng nằm trong màn cài đặt. Đọc-thành-tiếng **mặc định tắt** |

## 11. Constraints, Dependencies & Assumptions

**Constraints (ràng buộc áp đặt — có source/owner):**

| Ràng buộc | Source / Owner |
|-----------|----------------|
| **Giọng nói không bao giờ mở, sửa, đóng được một lệnh và không điều hướng được** — cưỡng chế lúc khởi động | URD UN-002, UN-014 |
| **Dữ liệu giọng nói không rời khỏi máy chủ của người chơi**, kể cả khi cấu hình sai | URD Mục 7 |
| Chỉ Chrome desktop; phải cho phép dùng mic **một lần** trong cài đặt trước khi nói lần đầu | URD Mục 7 · `docs/_shared/operating-environment.md` |
| Cử chỉ hiện là **cặp nút vai** hoặc một phím bàn phím; có thể đổi sang cặp nút sau lưng | URD Mục 7 — ràng buộc hiện tại, không phải nhu cầu |
| **Một lần nói giới hạn khoảng một phút**; nói dài hơn phải chia nhiều lần | URD Mục 7 |
| **Có trần số memo trong một giờ** | URD Mục 7 — xem OQ-1 |
| Chất lượng chép lời **phụ thuộc sức máy chủ**; máy yếu thì tự hạ mức, quá yếu thì tự tắt phần chép chữ | URD Mục 7 |
| **Bản chép cho giọng trộn Việt–Anh sẽ sai khá nhiều** — đánh đổi đã chọn | URD Mục 7 (OQ-1 resolved) |
| **Bản ghi âm giữ vô thời hạn**, chỉ mất khi người chơi chủ động xoá | URD Mục 7 (OQ-5 resolved) |
| **Memo mở qua chính lệnh gắn với nó**, không tìm được bằng cách gõ một cụm từ | URD Mục 7 (OQ-6 resolved) |
| Nội dung memo và lời coach đọc ra **không phải lời khuyên đầu tư** | `docs/_shared/project-profile.md` |

**Dependencies (deliverable do bên khác sở hữu):**

| Phụ thuộc | Owner | Blocks nếu chưa sẵn |
|-----------|-------|---------------------|
| Khái niệm **"vị thế đang chọn"** | `order-execution` (FR-041) | FR-016, FR-017 |
| Đường đặt lệnh để **không** nằm trên nó | `order-execution` | Không có gì để kiểm chứng FR-013..015 |
| Tab tư vấn làm đích đến thứ hai | `ai-desk` (FR-033) | FR-034..036 |
| Nội dung lời khuyên để đọc thành tiếng | `ai-desk` (FR-040, FR-042) | FR-048..051 |
| **Màn hình xem lại một lệnh** làm khung cho ba thao tác nghe/sửa/xoá | `daily-journal` | FR-037, FR-041 — **ba journey mất chỗ đứng nếu thiếu** |
| Màn cài đặt làm chỗ đặt nút bật/tắt và xoá sạch giọng nói | `reports-export` | FR-044, FR-052 |
| Ranh giới với đường xoá sạch **toàn sản phẩm** | `reports-export` | FR-044, FR-047 — xem OQ-3 |
| Màn xem lại của replay để áp ngoại lệ đích gắn memo | `trade-replay` | FR-021, FR-022 |
| Máy chủ đủ sức chép lời | Người chơi (hạ tầng) | FR-028 — xem OQ-4 |

**Assumptions (tin là đúng — nêu hệ quả nếu sai):**

| Giả định | Invalidate {X} nếu sai |
|----------|------------------------|
| Ký ức viết lại sau phiên bị kết quả lệnh làm méo (URD A-01) | **Toàn bộ lý do tồn tại của feature yếu đi** — chỉ còn tiện lợi, không còn cần thiết |
| Bản chép chủ yếu để **đọc lướt**; nghe lại mới là cách đọc kỹ (URD A-02) | FR-040 và BR-002 mất cơ sở; bản chép sai thành **hỏng nghiêm trọng** chứ không phải phiền nhẹ, và quyết định chấp nhận chép kém phải xét lại |
| Người chơi chấp nhận đợi khoảng chục giây để có chữ (URD A-03) | NFR-002 không đủ; người chơi bỏ thói quen ghi memo và SC-01 tụt |
| Bản chép cho giọng trộn Việt–Anh **vẫn đủ để nhận ra memo nói về gì** (URD A-04) | FR-037..039 biến thành việc **gõ lại toàn bộ memo bằng tay** — nặng tới mức người chơi sẽ bỏ |
| Người chơi sẽ bỏ dở nhật ký gõ tay sau vài tuần (URD A-08) | SC-01 mất mốc so sánh; giá trị feature nhỏ hơn tưởng |
| Người chơi giữ được cặp nút vai tới khoảng một phút mà không khó chịu (URD A-09) | FR-002 phải đổi sang cặp nút sau lưng; FR-054 (bàn phím) trở thành **đường chính** chứ không phải dự phòng |
| Máy chủ đủ sức chép lời ở mức dùng được (URD A-10) | FR-028 phải tự tắt phần chép chữ; feature còn lại chỉ là ghi âm — xem OQ-4 |
| Người chơi **thật sự muốn nghe** lời khuyên hơn là đọc (URD A-11) | FR-048..051 là công sức bỏ đi — xem OQ-7 |
| Đích đến chốt tại **thời điểm bắt đầu nói** (URD A-12 🔶) | BR-006 sai; người chơi đổi tab giữa chừng rồi ngạc nhiên vì câu đi sai chỗ — trái thẳng lời hứa của FR-034 |
| "Lệnh vừa đóng gần nhất" chỉ tính trong phiên và trong một khoảng đủ gần (URD A-13 🔶) | FR-019 không đủ chặt; memo cuối buổi gắn vào lệnh đóng từ nhiều giờ trước — xem OQ-5 |
| Màn hình xem lại một lệnh thuộc `daily-journal` (URD A-07) | **Là phụ thuộc liên feature đã xác nhận**, không phải giả định. `daily-journal` dựng khung khác đi thì FR-037, FR-041 phải thiết kế lại |

## 12. Open Questions

> **Số OQ đánh riêng cho từng tài liệu.** `OQ-3` của SRS này không nhất thiết là `OQ-3` của PRD
> cùng feature. Neo ổn định để đối chiếu là **số OQ của URD** ghi trong ngoặc *(kế thừa URD OQ-x)*.

* [ ] **OQ-1** *(kế thừa URD OQ-7, chung với `ai-desk` OQ-1)*: Trần số memo trong một giờ là bao nhiêu, và
  người chơi có cần **biết trước** con số đó không?
  🔶 **Tạm quyết:** **phải biết trước** (FR-030) — thống nhất với `ai-desk` FR-037 cho câu hỏi tương đương.
  *Nếu sai:* người chơi bị chặn bất ngờ đúng lúc muốn nói nhất.

* [ ] **OQ-2** *(kế thừa URD OQ-8, chung với `tilt-meter` OQ-2)*: Có nên cho ghi memo **trong lúc đang vũ
  trang** không? Hiện FR-005 chặn, nhưng đó đúng là khoảnh khắc lý do vào lệnh còn nóng nhất.
  🔶 **Tạm quyết:** **giữ nguyên việc chặn**. Lý do chính để mở đã bớt cấp bách vì `tilt-meter` FR-030 huỷ
  ARM ngay khi khoảng khoá bắt đầu — nên tình huống "đang vũ trang mà cần ghi memo để thoát khoá" tự giải.
  *Nếu sai:* mất đúng khoảnh khắc giá trị nhất của cả feature. Mở ra thì **phải chứng minh nó không đụng gì
  tới đường đặt lệnh**, và đó là công việc thật, không phải một dòng cấu hình.

* [ ] **OQ-3** *(kế thừa URD A-06, chung với `reports-export` OQ-5)*: Đường **xoá sạch giọng nói** (FR-044)
  và đường **xoá sạch toàn sản phẩm** phân định thế nào để không đá nhau? Xoá sạch toàn sản phẩm có gọi lại
  đường này, hay tự xoá phần giọng nói? Hai lời xác nhận có khác nhau đủ để không bấm nhầm?
  Và vế thứ ba: BR-008 hứa "xoá là mất hẳn", nhưng **một gói sao lưu cũ khôi phục về sẽ mang giọng nói đó
  quay lại** — FR-047 nói điều này lúc xoá, nhưng chưa chốt ai nói ở phía `reports-export`.
  **Chặn FR-044, FR-047.**

* [ ] **OQ-4** *(kế thừa URD OQ-9)*: Ngưỡng sức máy tối thiểu để bật phần chép lời là bao nhiêu, và dưới
  ngưỡng đó thì mặc định là **tự hạ mức** hay **tắt hẳn**? Ảnh hưởng FR-028.

* [ ] **OQ-5** *(kế thừa URD A-13)*: "Lệnh vừa đóng gần nhất" (FR-019) tính trong khoảng thời gian bao lâu?
  🔶 **Tạm quyết:** có một giới hạn, con số cụ thể chốt khi thiết kế màn hình — nhưng **phải có**, vì không
  giới hạn thì memo lúc 23h gắn vào lệnh đóng lúc 20h, làm hỏng ý nghĩa của chính memo đó.

* [ ] **OQ-6** *(`trade-replay` OQ-9 hỏi ngược sang đây)*: Ngoại lệ FR-021 — đang ở màn xem lại thì memo gắn
  vào **lệnh đang xem** thay vì vị thế đang mở.
  🔶 **Tạm quyết:** **nhận ngoại lệ này** (FR-021, BR-005); đích đến phải là thứ người chơi đang nhìn thấy.
  *Nếu sai:* một bài học về lệnh này nằm trong bản ghi của lệnh khác, và **không ai phát hiện ra**.

* [ ] **OQ-7** *(kế thừa URD A-11)*: Người chơi **thật sự muốn nghe** lời khuyên hơn là đọc nó không?
  **Chặn FR-048..051.** Chính nguồn cũng để mặc định tắt, tức kế hoạch cũng chưa chắc. SC-06 là thước đo trả
  lời câu này — em **không tạm quyết**, vì nó quyết định một nhánh có tồn tại hay không.

---

> **Nguồn:** `voice-journal-urd.md` (15 nhu cầu, 6 journey, 25 tình huống ngoại lệ, 6 thước đo, 13 giả định) ·
> `voice-journal-prd.md` (13 capability) · bốn tài liệu nền `docs/_shared/` · ranh giới nhận từ
> `order-execution`, `ai-desk`, `tilt-meter`, `daily-journal`, `trade-replay`, `reports-export`.
>
> **🔶 Bốn quyết định thay user:** OQ-1, OQ-2, OQ-5, OQ-6 — mỗi cái kèm hệ quả nếu sai. **OQ-3 và OQ-7 em cố
> ý không quyết** — cái đầu chạm nghĩa vụ về dữ liệu cá nhân và cần `reports-export` cùng chốt; cái sau
> quyết định một nhánh có tồn tại hay không.
>
> **Tầng 2–4 chưa sinh:** `voice-journal-flows.md`, `-states.md`, `-erd.md`, use case, user story, AC.
