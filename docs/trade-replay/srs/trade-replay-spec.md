---
type: srs
feature: trade-replay
status: draft
updated: 2026-08-29
links:
  - docs/trade-replay/trade-replay-urd.md
  - docs/trade-replay/trade-replay-prd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/srs/order-execution-spec.md
  - docs/voice-journal/srs/voice-journal-spec.md
  - docs/playbook-grading/srs/playbook-grading-spec.md
  - docs/tilt-meter/srs/tilt-meter-spec.md
  - docs/daily-journal/srs/daily-journal-spec.md
---

# trade-replay — Software Requirements Specification

## 1. Scope

Đặc tả **màn tua lại một vị thế đã đóng qua bối cảnh thị trường lúc đó**, điều khiển bằng chính tay cầm đã
dùng để giao dịch — cùng **dải sự kiện** biến việc xem biểu đồ thành huấn luyện: mỗi lần vũ trang, mỗi lần
tự huỷ, lần bắn, lúc sàn xác nhận, mỗi lần dời mức bảo vệ, mỗi memo, mỗi tín hiệu, và mỗi lần mức tâm lý đổi
vùng.

**Trong phạm vi:** tua tới lui bằng cần analog, đổi độ
rộng khung nhìn, phát/dừng/đổi tốc độ · dải sự kiện đọc được từng cái · điểm vào, điểm ra, hai mốc giá đi xa
nhất đúng chiều · nghe lại memo đúng khoảnh khắc đã nói · ghi memo mới lúc xem lại · đặt kết quả chấm luật
cạnh dòng thời gian · chuyển lệnh trước/sau trong cùng phiên · bản rút gọn khi không còn bối cảnh · mở
replay bất cứ lúc nào · ghi nhận mỗi lần mở xem lại.

**Ngoài phạm vi:** ghi âm và chép lời (`voice-journal`) · nội dung chấm luật (`playbook-grading`) · tính
điểm quy trình (`process-score`) · bảng lịch sử, bản đồ nhiệt, chi tiết một ngày, nguyên tắc cá nhân
(`daily-journal`) · so sánh thực tế với kế hoạch và xu hướng lỗi (`execution-learning`, *chưa có URD*) · so
sánh nhiều lệnh, thống kê theo playbook (`process-score`) · đo trạng thái tâm lý (`tilt-meter`) · tư vấn và
diễn giải mới (`ai-desk`) · sao lưu, xuất dữ liệu, xoá toàn bộ (`reports-export`) · **lưu bối cảnh cho một
lần đứng ngoài không dẫn tới lệnh nào** *(chốt 2026-08-28: không lưu)* · **việc đóng băng bối cảnh** — chuyển sang `order-execution` FR-059..063 (chốt 2026-08-29), feature này **chỉ đọc** tape · **tua lại cả buổi tối như một dòng
liên tục** · **mô phỏng "nếu lúc đó tôi làm khác thì sao"**.

> **Ranh giới của tài liệu này có hai nửa, và nửa thứ hai quan trọng hơn:**
> 1. **Không lệnh nào phát ra được từ màn xem lại.** Bị khoá: **mở lệnh mới** và **sửa mức bảo vệ**.
> 2. **Đường thoát không bao giờ bị khoá.** Không bị khoá: **đóng một vị thế đã chọn**, và **thoát khẩn cấp**
>    — kế thừa bất biến của `order-execution`. Người chơi đang ôm vị thế **không bao giờ bị dồn vào chỗ chỉ
>    còn cách đóng sạch mọi thứ**.
>
> **Bối cảnh đã lưu là dữ liệu quá khứ, không phải mô phỏng.** Replay chiếu lại điều đã xảy ra, không dựng
> ra điều chưa xảy ra.

## 2. Actors & Stakeholders

| Actor | Loại | Mục tiêu | Trong scope? |
|-------|------|----------|--------------|
| **Người chơi** | người | Nhìn lại một lệnh đủ rõ để rút ra được điều gì đó, **không rời tay cầm và không đọc bảng số** | Có |
| **Bộ đóng băng bối cảnh** | hệ thống | Lưu bối cảnh quanh mỗi lệnh khi lệnh đóng | **Không** — thuộc `order-execution` (chốt 2026-08-29). Feature này **chỉ đọc** tape |
| **`order-execution`** | hệ thống | Sở hữu bản ghi lệnh, định nghĩa phiên, đường thoát, và thông báo lệnh vừa đóng | **Không** — ranh giới tích hợp |
| **`voice-journal`** | hệ thống | Sở hữu cơ chế ghi âm; bản ghi âm phải **nghe lại và tua được** | **Không** — ranh giới |
| **`playbook-grading`** | hệ thống | Cấp kết quả chấm luật theo `cid` | **Không** — chỉ đọc |
| **`tilt-meter`** | hệ thống | Cấp sự kiện đổi mức kèm mốc thời gian | **Không** — chỉ đọc |
| **`daily-journal`** | hệ thống | Là **đường vào** dẫn tới replay (lịch sử, chi tiết một lệnh) | **Không** — ranh giới |
| **`process-score`** | hệ thống | Đọc "đã mở replay" ở **mức phiên**; feature này ghi ở **mức từng lệnh** | **Không** — hai mức khác nhau, không mâu thuẫn |
| **Sàn cTrader / Spotware** | ngoài | Nguồn của dữ liệu giá đã lưu | Có — ranh giới |
| **AI desk** | hệ thống | — | **Không.** Replay **dựng lại sự kiện đã ghi, không diễn giải chúng**; không diễn giải mới nào được tạo ra lúc xem lại |

## 3. Functional Requirements (FR)

### 3.1 Ranh giới an toàn

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-trade-replay-001 | Khoá mở lệnh mới và sửa mức bảo vệ | Suốt thời gian ở màn xem lại, **mở lệnh mới** và **sửa mức bảo vệ** bị khoá | P0 | test | URD UN-002 |
| FR-trade-replay-002 | **Không khoá đóng vị thế và thoát khẩn cấp** | **Đóng một vị thế đã chọn** và **thoát khẩn cấp** không bao giờ bị khoá — kế thừa bất biến `order-execution` FR-029. Người chơi đang ôm vị thế **không bao giờ bị dồn vào chỗ chỉ còn cách đóng sạch mọi thứ** | P0 | test | URD UN-002 · `order-execution` FR-029 |
| FR-trade-replay-003 | Bấm nút vào lệnh trong lúc xem lại | **Không lệnh nào được chuẩn bị và không gì gửi đi**; **im lặng bỏ qua** chứ không hiện cảnh báo gây hoang mang | P0 | test | URD Mục 6 |
| FR-trade-replay-004 | Thoát khẩn cấp **thoát luôn khỏi màn xem lại** | Đóng vị thế **và** thoát về màn chính, để người chơi **tự mắt xác nhận mọi thứ đã phẳng** | P0 | test | URD OQ-2 resolved |
| FR-trade-replay-005 | Khoá nhả đúng khi thoát | Thoát khỏi màn xem lại thì khả năng đặt lệnh trở lại **nguyên vẹn ngay lập tức** | P0 | test | URD Journey 2, Journey 8 |
| FR-trade-replay-006 | Không diễn giải mới lúc xem lại | Replay **dựng lại sự kiện đã ghi**. Tín hiệu đã sinh ra lúc đó hiện lại như sự kiện; **không diễn giải mới nào được tạo ra** | P0 | kiểm tra | URD Mục 3 |

### 3.2 Bối cảnh đã đóng băng — **do `order-execution` cấp**

> **Chốt 2026-08-29: việc đóng băng bối cảnh chuyển sang `order-execution`** (FR-059..FR-063). Feature này
> **chỉ đọc** tape. `phase-02` vốn đã đặt vòng đệm ở đó; một vòng đệm chạy liên tục trên luồng giá **là** đang
> ở trên order socket, mà journal path bị cấm đi trên đó; và quan trọng nhất — **tape tích luỹ từ phiên đầu
> tiên** thay vì chỉ tồn tại từ ngày feature này ship (thứ bảy trong chín).
>
> **`FR-trade-replay-007` đến `FR-trade-replay-011` đã nghỉ hưu** và **không tái dùng mã** (theo
> `naming-conventions.md`: ID không reuse khi delete). Nội dung của chúng nay là `order-execution`
> FR-059..FR-063. Cửa sổ 5 phút và hạn giữ tape trở thành **tham số của `order-execution`** — xem
> `order-execution` OQ-9 và OQ-10.

### 3.3 Tua và điều khiển

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-trade-replay-012 | Tua tới lui bằng **cần analog trái** | Đầu phát bám theo tay | P0 | demo | URD UN-001 |
| FR-trade-replay-013 | Đổi độ rộng khung nhìn bằng **cần phải** | Lúc thì thấy cả cửa sổ, lúc thì soi kỹ quanh điểm vào | P0 | demo | URD UN-001 |
| FR-trade-replay-014 | Phát/dừng và đổi tốc độ bằng nút | Bốn mức: **chậm một nửa · thường · gấp đôi · gấp bốn** | P0 | demo | URD Mục 3 |
| FR-trade-replay-015 | Đầu phát không có độ trễ nhận ra được | Và **không vị trí nào trong cửa sổ phải chờ tải** | P0 | test | URD UN-001 |
| FR-trade-replay-016 | Toàn bộ thao tác xem lại làm bằng tay cầm | **Không thao tác nào bắt buộc phải dùng chuột hay bàn phím** | P0 | demo | URD Mục 7 |
| FR-trade-replay-017 | Mất focus cửa sổ giữa lúc xem lại | Đầu phát **và tiếng cùng dừng lại**, giữ nguyên vị trí; quay lại thì tiếp tục **đúng chỗ đó** | P0 | test | URD Mục 6 |

### 3.4 Dải sự kiện

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-trade-replay-018 | Chín loại sự kiện trên cùng dải thời gian | Mỗi lần **vũ trang** · mỗi lần **tự huỷ** · lần **bắn** · lúc **sàn xác nhận** · mỗi lần **dời mức bảo vệ** · mỗi **memo** · mỗi **tín hiệu** · mỗi lần **mức tâm lý đổi vùng** | P0 | demo | URD UN-011 |
| FR-trade-replay-019 | **Mỗi sự kiện đọc được là gì** khi tua tới nó | Không chỉ thấy có một dấu ở đó. **Đây là thứ làm nó thành huấn luyện chứ không phải xem biểu đồ** | P0 | demo | URD UN-011 |
| FR-trade-replay-020 | Lần tự huỷ nằm **đúng chỗ của nó** | Hiện như một sự kiện có **mốc thời gian thật**, không phải một khoảng trống — kể cả khi nó xảy ra hàng chục giây trước lần bắn | P0 | test | URD UN-003 |
| FR-trade-replay-021 | Sự kiện nằm trong cửa sổ của nhiều lệnh | Hai lệnh mở gần nhau, cửa sổ chồng nhau → sự kiện hiện ở **mọi lệnh mà nó rơi vào cửa sổ**, nhưng **nói rõ nó không thuộc riêng lệnh đang xem** | P0 | test | URD Mục 6 |

### 3.5 Mốc giá

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-trade-replay-022 | Điểm vào và điểm ra trên dải thời gian | Hiện tại đúng thời điểm | P0 | demo | URD UN-001 |
| FR-trade-replay-023 | Hai mốc giá đi xa nhất, **đo đúng chiều lệnh** | Chỗ giá đi xa nhất **theo hướng mình** và **ngược hướng mình**, hiện tại đúng thời điểm chạm. **Lệnh mua và lệnh bán không được đo lẫn chiều** | P0 | test | URD UN-004 |
| FR-trade-replay-024 | Điểm vào/ra lấy từ **bản ghi lệnh**, không suy ra từ biểu đồ | Chi tiết vào lệnh có thể nhỏ hơn một nến của bối cảnh đã lưu. **Nến là bối cảnh, mốc là sự thật** | P0 | test | URD UN-013 |

### 3.6 Trạng thái suy giảm

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-trade-replay-025 | Trạng thái **"đang thu nốt phần sau lúc đóng"** | Nói rõ đang thu nốt, **còn khoảng bao lâu nữa**; **tự hiện ra khi xong**, không bắt mở lại | P0 | test | URD Mục 6 |
| FR-trade-replay-026 | Trạng thái **"bối cảnh không còn"** | Bản rút gọn dựng từ bản ghi lệnh: điểm vào, điểm ra, khối lượng, kết quả. **Không bao giờ trắng màn, không bao giờ báo lỗi** | P0 | test | URD UN-006 |
| FR-trade-replay-027 | Hai thông điệp phải **khác nhau rõ** | "Đang thu nốt" và "bối cảnh không còn" là hai trạng thái khác hẳn nhau và **phải đọc ra khác hẳn nhau** | P0 | test | URD UN-006, Mục 6 |
| FR-trade-replay-028 | Phần đuôi bối cảnh bị cụt | Tắt máy hoặc đóng phiên trước khi thu đủ → hiện đúng phần đã có và **tua bình thường trong phạm vi đó**; nói rõ phần sau ngắn hơn 5 phút, **không báo lỗi** | P0 | test | URD Mục 6 |
| FR-trade-replay-029 | Bối cảnh quá hạn giữ | Lệnh cũ quá hạn rơi về bản rút gọn như FR-026, và **người chơi biết trước điều đó** thay vì phát hiện lúc cần | P1 | kiểm tra | URD Mục 6 — xem OQ-5 |
| FR-trade-replay-030 | Mất kết nối giữa lúc đang xem lại | Phần đã tải **vẫn tua được**; nói rõ không lấy thêm được lệnh khác cho tới khi kết nối lại. **Mất kết nối lúc ôn tập không phải sự cố giao dịch** | P0 | test | URD Mục 6 |
| FR-trade-replay-031 | Phiên không có lệnh nào để xem lại | Nói rõ phiên này chưa có lệnh nào — **đó không phải lỗi cũng không phải thiếu sót** — và **chỉ đường tới các lệnh của những phiên trước** | P0 | test | URD Mục 6 |
| FR-trade-replay-032 | Lần tự huỷ nằm ngoài cửa sổ của mọi lệnh | Vẫn được **ghi nhận là đã xảy ra**, nhưng không tua lại được bối cảnh — **nói rõ vì sao**, thay vì im lặng như chưa từng có | P0 | test | URD Mục 6 (chốt 2026-08-28) — xem OQ-6 |

### 3.7 Memo trong màn xem lại

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-trade-replay-033 | Nghe lại memo **đúng khoảnh khắc đã nói** | Tiếng tự phát khi đầu phát đi qua chỗ đã ghi; **dừng và quay lại đúng chỗ** khi tua đi nơi khác | P1 | test | URD UN-005 |
| FR-trade-replay-034 | Mốc thời gian memo là mốc chuẩn | Mỗi lần tua là **khớp lại**, không trôi dần sau nhiều lần tua | P1 | test | URD Mục 6 |
| FR-trade-replay-035 | Tắt tiếng từ tốc độ gấp đôi trở lên | Thay vì phát méo | P1 | test | URD Mục 6 |
| FR-trade-replay-036 | Lệnh không có ghi âm | **Không hiện dấu memo và không hiện điều khiển tiếng**; mọi thứ khác y nguyên. **Không ô trống hay nút chết** | P1 | test | URD Mục 6 |
| FR-trade-replay-037 | Có tiếng nhưng phần chép chữ hỏng | Tiếng **vẫn phát bình thường tại đúng chỗ**; nói rõ chỉ phần chữ thiếu | P1 | test | URD Mục 6 |
| FR-trade-replay-038 | Dấu memo còn nhưng bản ghi âm đã bị xoá | Dấu memo **vẫn hiện đúng mốc** kèm phần chữ nếu còn; chỗ nghe lại nói rõ **tiếng không còn và vì sao**. Phần tua lại **không bị ảnh hưởng** | P1 | test | URD Mục 6 |
| FR-trade-replay-039 | Ghi một memo mới ngay trong lúc xem lại | Bằng **chính cặp nút giữ vẫn dùng để ghi âm ở mọi nơi khác** — cơ bắp không phải học lại | P1 | demo | URD UN-008 (OQ-1 resolved) |
| FR-trade-replay-040 | Đích gắn memo là **lệnh đang xem** | **Ghi đè** luật "gắn vào vị thế đang mở" của `voice-journal` — vì đích đến phải là **thứ người chơi đang nhìn thấy**. Áp cả khi đang có một vị thế **khác** đang mở | P1 | test | URD UN-008, A-05 · `voice-journal` FR-021 |
| FR-trade-replay-041 | Phân biệt memo lúc vào lệnh với memo lúc xem lại | Hai loại **luôn phân biệt được, ở mọi nơi chúng xuất hiện**: một cái là **lý do**, một cái là **bài học** | P1 | test | URD UN-008 |
| FR-trade-replay-042 | Nhãn memo trên dải thời gian | Hiện **bản đang có hiệu lực** — bản người chơi đã sửa nếu có, không thì bản máy chép | P1 | kiểm tra | `voice-journal` BR-007 — xem OQ-7 |

### 3.8 Chấm luật, chuyển lệnh, và ghi nhận

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-trade-replay-043 | Kết quả chấm luật **trên cùng màn hình** | Luật nào đạt, luật nào không, có sạch hay không — **không phải mở nơi khác rồi ghép lại bằng trí nhớ** | P1 | demo | URD UN-007 |
| FR-trade-replay-044 | Lệnh không có điểm chấm | Playbook đã ngừng dùng, hoặc lệnh ngoài kế hoạch → nói rõ lệnh này **không có điểm hoặc thuộc nhóm ngoài kế hoạch**; **phần tua lại không phụ thuộc vào điểm** | P1 | test | URD Mục 6 |
| FR-trade-replay-045 | Chuyển lệnh trước/sau **trong cùng phiên** | Theo định nghĩa phiên của `order-execution`, **không phải cùng ngày lịch** — kể cả khi phiên vắt qua nửa đêm | P1 | test | URD UN-009 |
| FR-trade-replay-046 | Không dùng cặp nút giữ để ghi âm | Thao tác chuyển lệnh **không** dùng cặp nút đã gán cho ghi âm | P1 | kiểm tra | URD OQ-1 resolved |
| FR-trade-replay-047 | Ở hai đầu thì dừng lại | Đi tới đi lui qua các lệnh của một phiên: ở hai đầu **dừng lại**, **không nhảy sang phiên khác** | P1 | test | URD Journey 6 |
| FR-trade-replay-048 | Chuyển lệnh dừng hẳn tiếng của lệnh trước | Bối cảnh mới hiện ra, đầu phát về đầu, **tiếng của lệnh trước dừng hẳn** | P1 | test | URD Journey 6 |
| FR-trade-replay-049 | Ghi nhận **mỗi lần mở xem lại: lệnh nào, lúc nào** | **Feature này tạo ra bản ghi đó**; `process-score` và `daily-journal` chỉ đọc | P1 | kiểm tra | URD UN-012, A-08 (🔶) — xem OQ-3 |
| FR-trade-replay-050 | **Mở là tính**, không điều kiện phụ | Không đếm chuỗi, không huy hiệu, không cấp độ gắn với việc xem lại. Feature này **không được đặt thêm điều kiện nào** lên việc trục Review ghi nhận | P1 | test | URD UN-012 · `process-score` |

### 3.9 Đường vào và mở giữa phiên

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-trade-replay-051 | Mở replay **bất cứ lúc nào** | Kể cả khi đang có vị thế mở. **Vào thẳng, không phải xác nhận thêm bước nào** | P0 | demo | URD UN-010 (OQ-3 resolved) |
| FR-trade-replay-052 | Một dòng thông báo khi đang có vị thế mở | Nói rõ: **mở lệnh mới và sửa mức bảo vệ tạm khoá; đóng vị thế và thoát khẩn cấp vẫn dùng được** — để lựa chọn là **chủ động chứ không phải bất ngờ** | P0 | demo | URD UN-010 |
| FR-trade-replay-053 | Một vị thế khác đóng trong lúc đang xem lại | Được báo như bình thường **mà không đá người chơi ra khỏi màn đang xem** | P0 | test | URD Mục 6 |
| FR-trade-replay-054 | Mở thẳng từ thông báo lệnh vừa đóng | Không phải đi vòng qua danh sách. **Nội dung thông báo thuộc `order-execution`**; feature này nhận **việc dẫn từ đó sang đây** | P2 | demo | URD Mục 3 — xem OQ-2 |
| FR-trade-replay-055 | Thoát ra quay về **chỗ vừa đi vào** | Người chơi không bị đẩy về một màn khác với màn đã mở replay | P1 | test | URD Journey 1 |

## 4. Non-Functional Requirements (NFR)

| ID | Category | Requirement | Priority | Acceptance |
|----|----------|-------------|----------|------------|
| NFR-trade-replay-001 | performance | Đầu phát bám theo cần analog **không có độ trễ nhận ra được** | P0 | Gạt cần liên tục, quan sát đầu phát; không cảm nhận được trễ |
| NFR-trade-replay-002 | performance | **Không vị trí nào trong cửa sổ phải chờ tải** | P0 | Tua ngẫu nhiên khắp cửa sổ 10 lần, không lần nào phải đợi |
| NFR-trade-replay-003 | performance | Replay chạy trên **journal path** — đường học hỏi, chậm nhất, **không bao giờ đi chung với đường đặt lệnh** | P0 | phân tích | `system-overview.md` |
| NFR-trade-replay-004 | reliability | Feature này chết hoàn toàn **không** làm giảm khả năng mở, đóng, thoát vị thế | P0 | Diễn tập: tắt hẳn replay rồi chạy trọn chuỗi mở phiên → vào lệnh → đóng lệnh |
| NFR-trade-replay-005 | reliability | **Không tồn tại đường nào** phát ra một lệnh mở hoặc một lệnh sửa bảo vệ từ màn xem lại | P0 | test — bấm mọi tổ hợp vào lệnh trong suốt thời gian màn mở; kiểm cTrader demo không có vị thế mới và không có thay đổi bảo vệ nào |
| NFR-trade-replay-006 | reliability | **Đóng vị thế và thoát khẩn cấp không bao giờ bị khoá**, không chậm hơn, không thêm bước | P0 | test — thứ tự bắt buộc: thử mở lệnh trước (phải bị chặn), rồi mới thoát khẩn cấp |
| NFR-trade-replay-007 | correctness | Hai mốc giá đi xa nhất đo **đúng chiều lệnh**; đo lẫn chiều là **lỗi bất đối xứng âm thầm** | P0 | test — kiểm bằng **một lệnh mua và một lệnh bán**, không phải chỉ một chiều |
| NFR-trade-replay-008 | correctness | Điểm vào và điểm ra lấy từ **bản ghi lệnh**, không suy ra từ nến | P0 | test — dựng một lệnh có chi tiết vào nhỏ hơn một nến, kiểm mốc vẫn đúng chỗ |
| NFR-trade-replay-009 | correctness | Tiếng memo **không trôi dần** sau nhiều lần tua qua tua lại | P1 | test — tua qua lại 10 lần, tiếng vẫn bắt đầu đúng mốc |
| NFR-trade-replay-010 | usability | **Toàn bộ thao tác xem lại làm bằng tay cầm** — không thao tác nào bắt buộc dùng chuột hay bàn phím | P0 | demo — chạy một vòng xem lại không chạm chuột |
| NFR-trade-replay-011 | usability | Mất focus cửa sổ → **việc xem lại tạm dừng**, không chạy tiếp trong nền | P0 | test |
| NFR-trade-replay-012 | data integrity | **Buổi không có lệnh nào thì không lưu gì cả** — không có kho dữ liệu nào phình ra sau một tối đứng ngoài | P0 | test — chạy một phiên không lệnh, kiểm không có bối cảnh nào được ghi |
| NFR-trade-replay-013 | privacy | Bản ghi âm là **dữ liệu giọng nói cá nhân**; nơi lưu, hạn giữ và cách xoá thuộc `voice-journal` và `reports-export` | P0 | kiểm tra | URD Mục 7 |
| NFR-trade-replay-014 | compatibility | Chỉ Chrome desktop, tay cầm qua dongle 2.4G, cửa sổ phải đang focus | P0 | kiểm tra |
| NFR-trade-replay-015 | compliance | **Việc xem lại không phải lời khuyên đầu tư** — nó chỉ chiếu lại điều đã xảy ra | P0 | kiểm tra | Project profile |
| NFR-trade-replay-016 | usability | Giao diện tiếng Anh; tài liệu nghiệp vụ tiếng Việt | P0 | kiểm tra |

## 5. Business Rules

| ID | Rule | Trigger | Implements FR | Source |
|----|------|---------|---------------|--------|
| BR-trade-replay-001 | Ở màn xem lại: **khoá mở lệnh mới và sửa mức bảo vệ**; **không khoá đóng vị thế và thoát khẩn cấp** | Vào màn xem lại | FR-001, FR-002 | URD UN-002 · `order-execution` FR-029 |
| BR-trade-replay-002 | Thoát khẩn cấp **đóng vị thế và thoát luôn khỏi màn xem lại** về màn chính | Bấm thoát khẩn cấp khi đang xem lại | FR-004 | URD OQ-2 resolved |
| BR-trade-replay-003 | Bấm nút vào lệnh khi đang xem lại → **im lặng bỏ qua**, không cảnh báo gây hoang mang | Bấm tổ hợp vào lệnh | FR-003 | URD Mục 6 |
| BR-trade-replay-004 | **Nến là bối cảnh, mốc là sự thật** — điểm vào/ra luôn lấy từ bản ghi lệnh | Vẽ mốc trên biểu đồ | FR-024 · NFR-008 | URD UN-013 |
| BR-trade-replay-005 | Mốc giá đi xa nhất đo **đúng chiều lệnh**; đo lẫn chiều là lỗi bất đối xứng âm thầm | Tính hai mốc | FR-023 · NFR-007 | URD UN-004 |
| BR-trade-replay-006 | **Buổi không lệnh nào thì không lưu gì cả**; và **không lưu bối cảnh cho lần đứng ngoài** không dẫn tới lệnh | Kết thúc phiên · lần tự huỷ | FR-009, FR-010 | URD UN-014 · Mục 3 |
| BR-trade-replay-007 | **"Đang thu nốt" và "bối cảnh không còn" là hai trạng thái khác nhau** và phải đọc ra khác hẳn nhau | Mở một lệnh vừa đóng · mở một lệnh cũ | FR-025, FR-026, FR-027 | URD UN-006 |
| BR-trade-replay-008 | Đang ở màn xem lại thì đích gắn memo là **lệnh đang xem** — **ghi đè** luật của `voice-journal` | Ghi memo trong màn xem lại | FR-040 | URD A-05 · `voice-journal` BR-005 |
| BR-trade-replay-009 | Memo lúc vào lệnh và memo lúc xem lại **luôn phân biệt được**: một cái là **lý do**, một cái là **bài học** | Hiển thị memo ở bất kỳ đâu | FR-041 | URD UN-008 |
| BR-trade-replay-010 | Chuyển lệnh trước/sau theo **phiên**, không theo ngày lịch — kể cả khi phiên vắt qua nửa đêm | Chuyển lệnh | FR-045, FR-047 | URD UN-009 · `order-execution` FR-007 |
| BR-trade-replay-011 | **Mở màn replay là đủ** để trục Review ghi nhận; feature này **không được đặt thêm điều kiện nào** | Mở màn xem lại | FR-050 | URD Mục 3 (chốt 2026-08-28) |
| BR-trade-replay-012 | **Feature này ghi bản ghi "lệnh nào đã xem lại, lúc nào"** ở mức từng lệnh; `process-score` đọc ở mức phiên. Hai mức khác nhau **không mâu thuẫn** | Mỗi lần mở xem lại | FR-049 | URD A-08 (🔶) · `process-score` OQ-8 resolved |
| BR-trade-replay-013 | Sự kiện rơi vào cửa sổ nhiều lệnh thì **hiện ở mọi lệnh đó**, nhưng nói rõ **không thuộc riêng lệnh đang xem** | Hai lệnh mở gần nhau | FR-021 | URD Mục 6 |
| BR-trade-replay-014 | **Replay chiếu lại điều đã xảy ra, không dựng ra điều chưa xảy ra.** Không mô phỏng, không diễn giải mới | Luôn luôn | FR-006 | URD Mục 7 |

## 6. Error Matrix

| Error ID | Title | Trigger | Severity | Related FR | Screen state | Recovery |
|----------|-------|---------|----------|------------|--------------|----------|
| E-trade-replay-001 | **Bấm nút vào lệnh trong lúc đang xem lại** | Tay vẫn trên tay cầm, bấm quen | **critical** | FR-003 | Không lệnh nào được chuẩn bị, không gì gửi đi; **im lặng bỏ qua** | Rủi ro lớn nhất của feature: một lệnh thật bay ra từ màn ôn tập |
| E-trade-replay-002 | **Cần thoát khẩn cấp trong lúc đang xem lại** | Thị trường chạy ngược | **critical** | FR-002, FR-004 | Thoát khẩn cấp **không bao giờ bị khoá**; đóng vị thế **và thoát luôn** về màn chính | Kẹt trong màn ôn tập giữa lúc thị trường chạy ngược là kịch bản nguy hiểm nhất |
| E-trade-replay-003 | **Muốn đóng một vị thế cụ thể trong lúc xem lại** | Chỉ muốn đóng một cái | major | FR-002 | Đóng một vị thế đã chọn **không bị khoá** | Không bị dồn vào chỗ phải đóng cả những vị thế không muốn đóng |
| E-trade-replay-004 | **Lệnh vừa đóng, phần sau chưa thu xong** | Mở replay ngay sau khi lệnh đóng | major | FR-025 | Nói rõ **đang thu nốt**, còn khoảng bao lâu; **tự hiện ra khi xong** | Câu chữ **phải khác hẳn** thông điệp "bối cảnh không còn" — đọc nhầm là tưởng mất dữ liệu |
| E-trade-replay-005 | Lệnh không còn bối cảnh đã lưu | Lệnh cũ hơn ngày bắt đầu lưu, hoặc quá hạn giữ | major | FR-026, FR-029 | Bản rút gọn dựng từ bản ghi lệnh; nói rõ **bối cảnh không còn** | **Không trắng màn, không báo lỗi**; chuyển sang lệnh khác vẫn chạy |
| E-trade-replay-006 | Phần đuôi bối cảnh bị cụt | Tắt máy hoặc đóng phiên trước khi thu đủ | minor | FR-028 | Hiện đúng phần đã có, tua bình thường trong phạm vi đó; nói rõ phần sau ngắn hơn | **Không báo lỗi** |
| E-trade-replay-007 | Lệnh không có ghi âm | Người chơi không ghi memo | minor | FR-036 | **Không hiện dấu memo và không hiện điều khiển tiếng** | Không ô trống hay nút chết |
| E-trade-replay-008 | Có tiếng nhưng phần chép chữ hỏng | Chép lời thất bại | minor | FR-037 | Tiếng **vẫn phát bình thường tại đúng chỗ**; nói rõ chỉ phần chữ thiếu | Bản ghi sống sót qua việc chuyển chữ |
| E-trade-replay-009 | Dấu memo còn nhưng bản ghi âm đã bị xoá | Người chơi đã xoá memo | minor | FR-038 | Dấu vẫn hiện đúng mốc kèm chữ nếu còn; chỗ nghe lại nói rõ **tiếng không còn và vì sao** | Phần tua lại **không bị ảnh hưởng** |
| E-trade-replay-010 | Tiếng lệch khỏi hình sau nhiều lần tua | Tua qua lại nhiều | minor | FR-034 · NFR-009 | **Mốc thời gian memo là mốc chuẩn**; mỗi lần tua là khớp lại | Từ tốc độ gấp đôi trở lên thì **tắt tiếng** thay vì phát méo |
| E-trade-replay-011 | Nến bối cảnh thô hơn khoảnh khắc khớp lệnh | Chi tiết vào lệnh nhỏ hơn một nến | major | FR-024 | Điểm vào/ra lấy từ bản ghi lệnh, **luôn vẽ đúng chỗ dù nến thô** | **Nến là bối cảnh, mốc là sự thật** |
| E-trade-replay-012 | **Đang có vị thế mở mà vào màn xem lại** | Mở replay giữa phiên | major | FR-051, FR-052 | **Một dòng thông báo** ngay khi vào: mở lệnh mới và sửa bảo vệ đang khoá, **đóng vị thế và thoát khẩn cấp vẫn dùng được** | Vào thẳng, **không thêm bước xác nhận** |
| E-trade-replay-013 | Một vị thế khác đóng trong lúc đang xem lại | Lệnh khác kết thúc | minor | FR-053 | Được báo như bình thường, **không đá người chơi ra khỏi màn đang xem** | Xem xong vào lệnh mới đóng đó là việc riêng |
| E-trade-replay-014 | **Ghi memo trong lúc đang có một vị thế khác mở** | Ghi memo khi xem lại | major | FR-040 | Đích gắn memo là **lệnh đang xem**, không phải vị thế đang chạy | Đây là **ngoại lệ có chủ ý**; nếu sai thì bài học về lệnh này nằm trong bản ghi của lệnh khác và **không ai phát hiện ra** |
| E-trade-replay-015 | Memo lúc xem lại lẫn với memo lúc vào lệnh | Một lệnh có cả hai loại | minor | FR-041 | Hai loại **luôn phân biệt được ở mọi nơi** | Đọc lại tưởng lúc vào lệnh đã biết điều mà thực ra nhận ra sau |
| E-trade-replay-016 | Một sự kiện nằm trong cửa sổ của nhiều lệnh | Hai lệnh mở gần nhau | minor | FR-021 | Hiện ở mọi lệnh mà nó rơi vào cửa sổ, nhưng **nói rõ không thuộc riêng lệnh đang xem** | Đọc lại tưởng hai lần huỷ khác nhau |
| E-trade-replay-017 | Bối cảnh còn nhưng **không có kết quả chấm luật** | Playbook đã ngừng dùng, hoặc lệnh ngoài kế hoạch | minor | FR-044 | Nói rõ lệnh này **không có điểm** hoặc thuộc nhóm ngoài kế hoạch | **Phần tua lại không phụ thuộc vào điểm** |
| E-trade-replay-018 | Mất kết nối tới máy chủ giữa lúc đang xem lại | Mạng đứt | minor | FR-030 | Phần đã tải **vẫn tua được**; nói rõ không lấy thêm được lệnh khác | **Mất kết nối lúc ôn tập không phải sự cố giao dịch** |
| E-trade-replay-019 | Cửa sổ Chrome mất focus giữa lúc đang xem lại | Chuyển sang app khác | minor | FR-017 | Đầu phát **và tiếng cùng dừng**, giữ nguyên vị trí | Quay lại thì tiếp tục đúng chỗ đó |
| E-trade-replay-020 | **Phiên không có lệnh nào để xem lại** | Một tối đứng ngoài | minor | FR-031 | Nói rõ phiên này chưa có lệnh nào — **không phải lỗi cũng không phải thiếu sót** — và **chỉ đường tới các lệnh phiên trước** | Một tối đứng ngoài vẫn xem lại được bài học cũ |
| E-trade-replay-021 | **Lần tự huỷ nằm ngoài cửa sổ của mọi lệnh** | Huỷ xa mọi lệnh có thật | minor | FR-032 | Vẫn được **ghi nhận là đã xảy ra**, nhưng không tua lại được bối cảnh — **nói rõ vì sao** | Thay vì im lặng như chưa từng có. Bề mặt hiển thị: xem OQ-6 |
| E-trade-replay-022 | Xem lại một lệnh của nhiều tháng trước | Quá hạn giữ bối cảnh | minor | FR-029 | Rơi về bản rút gọn như E-005, và **người chơi biết trước điều đó** | Thay vì phát hiện lúc cần. Xem OQ-5 |

## 7. Success Criteria

| ID | Outcome nghiệp vụ | Đo bằng | Mốc đạt |
|----|-------------------|---------|---------|
| SC-trade-replay-01 | Xem lại trở thành **thói quen thật**, không phải tính năng dùng một lần rồi quên | Đếm số lệnh đã được mở xem lại trên tổng số lệnh đã đóng, đọc cuối tháng **theo đường xu hướng nhiều tháng**, không so đúng một mốc | **Không giảm dần theo tháng**, và sau 3 tháng vẫn ở mức người chơi thấy đáng giữ (chưa có sàn tuyệt đối — xem OQ-4) |
| SC-trade-replay-02 | Xem lại diễn ra **khi bối cảnh còn nóng** | Trung vị khoảng cách từ lúc lệnh đóng tới lần xem lại đầu tiên, **đọc kèm thời lượng xem trung vị** | Giảm so với baseline sau 3 tháng |
| SC-trade-replay-03 | Xem lại dẫn tới **điều rút ra được nói thành lời** | Đếm số lệnh có ít nhất một memo thuộc loại "ghi lúc xem lại" | Tăng so với baseline sau 3 tháng |
| SC-trade-replay-04 | *(ranh giới)* Không lệnh nào phát ra từ màn xem lại | Suốt thời gian màn mở, bấm mọi tổ hợp vào lệnh; kiểm cTrader demo | **0** vị thế mới và **0** thay đổi mức bảo vệ |
| SC-trade-replay-05 | *(ranh giới)* Đường thoát không bao giờ bị khoá | Với một vị thế đang mở: **trước tiên** thử mở lệnh mới (phải bị chặn), **sau đó** mới thoát khẩn cấp | Thoát thành công 100% lần thử. **Thứ tự bắt buộc** — làm ngược thì việc khoá phiên sau thoát khẩn cấp che mất điều đang cần kiểm |
| SC-trade-replay-06 | Mốc giá đo đúng chiều | Kiểm bằng **một lệnh mua và một lệnh bán**, đối chiếu với bản ghi lệnh trên cTrader demo | 100% đúng chiều, cả hai loại lệnh |

> **Ba thước đo đầu có một sàn cứng không tránh được:** một lệnh chỉ tua lại được **sau khi phần sau lúc
> đóng thu xong** (FR-011). SC-02 không bao giờ xuống dưới mốc đó — **giới hạn của thiết kế, không phải của
> thói quen người chơi**.
>
> **Ba thước đo đầu đọc từ bản ghi do chính feature này tạo ra** (FR-049), nhưng **được tổng hợp thành xu
> hướng ở `daily-journal` và `process-score`**.
>
> **Giới hạn đã biết.** SC-01..03 đo **việc xem lại có diễn ra hay không**, không đo **việc xem lại có làm
> người chơi giao dịch tốt hơn hay không**. Điều thứ hai chỉ đọc được qua điểm quy trình, và ngay cả ở đó
> cũng khó tách phần đóng góp của riêng replay khỏi các feature khác.
>
> **SC-02 đọc kèm thời lượng xem trung vị** để việc mở-rồi-thoát-ngay không tự động thành "tiến bộ" — cơ chế
> hiện tại chỉ **đo** chứ không **ngăn** (URD A-07).

## 8. Data Entities (tóm tắt — chi tiết ở `trade-replay-erd.md`)

| Entity | Ý nghĩa nghiệp vụ | Thông tin nghiệp vụ cần lưu |
|--------|-------------------|------------------------------|
| **Bối cảnh đã đóng băng** | Dữ liệu thị trường quanh một lệnh | Thuộc lệnh nào (`cid`) · mốc đầu và mốc cuối cửa sổ · dữ liệu giá trong cửa sổ · **trạng thái: đang thu nốt / đủ / cụt đuôi / không còn** · thời điểm đóng băng |
| **Sự kiện trên dải thời gian** | Một việc đã xảy ra trong cửa sổ | Mốc thời gian · **loại** (vũ trang / tự huỷ / bắn / sàn xác nhận / dời bảo vệ / memo / tín hiệu / đổi mức tâm lý) · **nhãn đọc được** · thuộc riêng lệnh này hay **rơi vào cửa sổ của nhiều lệnh** |
| **Mốc giá của một lệnh** | Điểm vào, điểm ra, hai mốc đi xa nhất | `cid` · giá vào + thời điểm · giá ra + thời điểm · **mốc xa nhất theo hướng lệnh** · **mốc xa nhất ngược hướng** · **chiều lệnh** (quyết định cách đo) |
| **Lần mở xem lại** | Mỗi lần người chơi mở một lệnh ra xem | **Lệnh nào · lúc nào** · thời lượng xem. **Feature này tạo ra bản ghi này**; `process-score` và `daily-journal` chỉ đọc |

> **Bản ghi lệnh, memo, kết quả chấm luật, và sự kiện đổi mức tâm lý đều không phải entity của feature này** —
> chúng thuộc `order-execution`, `voice-journal`, `playbook-grading`, `tilt-meter`. Feature này **đọc và đặt
> chúng lên dải thời gian**.
>
> **Không có entity nào lưu bối cảnh cho một lần đứng ngoài** không dẫn tới lệnh (BR-006) — đó là ranh giới
> đã chốt, không phải một thiếu sót.

## 9. Flows (tóm tắt — chi tiết ở `trade-replay-flows.md`)

| Flow | Tóm tắt | Nguồn |
|------|---------|-------|
| Tua lại một lệnh vừa đóng | Mở từ thông báo hoặc danh sách → nếu chưa thu xong thì nói rõ đang chờ → bối cảnh hiện kèm điểm vào/ra và hai mốc xa nhất → điểm luật hiện cùng màn → gạt cần tua, bấm phát, đổi tốc độ → thoát về **chỗ vừa đi vào** | URD Journey 1 |
| Không có lệnh nào bay ra từ màn xem lại | Vào màn → bấm tổ hợp vẫn dùng để mở lệnh → **không gì được chuẩn bị, không gì gửi đi** → thoát ra, khả năng đặt lệnh trở lại nguyên vẹn | URD Journey 2 |
| Nhìn lại lần mình đã đứng ngoài | Mở lệnh đã bắn → tua ngược về phần trước lúc mở → dải sự kiện hiện **lần vũ trang rồi lần huỷ tại đúng mốc thời gian**, mỗi cái đọc được là gì | URD Journey 3 |
| Nghe lại lời mình nói lúc vào lệnh | Mở lệnh có ghi âm → cho chạy → tới đúng chỗ tiếng tự phát → tua đi nơi khác tiếng dừng, tua về **khớp lại đúng chỗ** | URD Journey 4 |
| Ghi lại điều rút ra ngay khi nhận ra | Đang xem lại và nhận ra điều gì đó → ghi memo bằng **chính cặp nút vẫn dùng để ghi âm** → memo gắn vào **lệnh đang xem**, đánh dấu rõ là ghi lúc xem lại | URD Journey 5 |
| Đi qua các lệnh của một phiên | Mở lệnh đầu → chuyển thẳng sang lệnh kế → bối cảnh mới hiện, đầu phát về đầu, **tiếng lệnh trước dừng hẳn** → ở hai đầu **dừng lại, không nhảy sang phiên khác** | URD Journey 6 |
| Xem lại một lệnh không còn bối cảnh | Mở lệnh cũ → bản rút gọn: điểm vào, điểm ra, khối lượng, kết quả → nói rõ **bối cảnh không còn**, khác hẳn "đang thu nốt" → chuyển lệnh vẫn chạy | URD Journey 7 |
| Xem lại giữa phiên khi đang có vị thế mở | Vào thẳng, không xác nhận thêm → **một dòng thông báo** nói rõ khoá gì, còn dùng được gì → xem xong thoát → khả năng thao tác trở lại **ngay lập tức** | URD Journey 8 |

## 10. Screens (tóm tắt — chi tiết ở `ascii-wireframe/`)

| Màn hình | Vai trò | Ghi chú ranh giới |
|----------|---------|-------------------|
| **Màn xem lại một lệnh** | Biểu đồ bối cảnh · điểm vào/ra · hai mốc xa nhất · **dải sự kiện** · điều khiển tua/phát/tốc độ · khối điểm luật | **Toàn bộ thao tác bằng tay cầm.** Vào thẳng khi đang có vị thế mở, kèm một dòng thông báo |
| **Trạng thái "đang thu nốt"** | Nói rõ còn khoảng bao lâu, tự hiện ra khi xong | **Phải đọc khác hẳn** trạng thái "bối cảnh không còn" |
| **Bản rút gọn (không còn bối cảnh)** | Điểm vào · điểm ra · khối lượng · kết quả | **Không trắng màn, không báo lỗi.** Chuyển lệnh vẫn chạy |
| **Dòng thông báo khi có vị thế mở** | Khoá gì · còn dùng được gì | Để lựa chọn là **chủ động chứ không phải bất ngờ** |
| **Khối điểm luật** | Luật nào đạt, luật nào không | Nội dung thuộc `playbook-grading`; feature này chỉ **đặt nó cạnh dòng thời gian** |

## 11. Constraints, Dependencies & Assumptions

**Constraints (ràng buộc áp đặt — có source/owner):**

| Ràng buộc | Source / Owner |
|-----------|----------------|
| **Không lệnh nào phát ra được từ màn xem lại**; nhưng **đóng vị thế và thoát khẩn cấp không bao giờ bị khoá** | URD UN-002 · `order-execution` FR-029 |
| Xem lại là việc trên **đường học hỏi**, không phải đường đặt lệnh — chậm hơn, không bao giờ đi chung | `docs/_shared/system-overview.md` |
| **Toàn bộ thao tác xem lại làm bằng tay cầm** | URD Mục 7 |
| Bối cảnh **chỉ có quanh những lệnh đã đóng**, và chỉ tua được sau khi phần sau lúc đóng thu xong | URD Mục 7 |
| **Một buổi tối không giao dịch không để lại gì để tua** — đó là **chủ ý**, không phải thiếu sót cần khắc phục | URD Mục 7 |
| **Bối cảnh đã lưu là dữ liệu quá khứ, không phải mô phỏng** | URD Mục 7 |
| **Mở màn replay là đủ** để trục Review tính; feature này không được đặt thêm điều kiện | URD Mục 3 (chốt 2026-08-28) |
| Chỉ Chrome desktop, dongle 2.4G, cửa sổ phải đang focus; mất focus thì việc xem lại **tạm dừng** | URD Mục 7 |
| **Việc xem lại không phải lời khuyên đầu tư** | `docs/_shared/project-profile.md` |

**Dependencies (deliverable do bên khác sở hữu):**

| Phụ thuộc | Owner | Blocks nếu chưa sẵn |
|-----------|-------|---------------------|
| **Tape (bối cảnh đã đóng băng) + trạng thái thu** | `order-execution` (FR-059..FR-063) | FR-012..FR-017, FR-025..FR-029 — **tape tích luỹ từ phiên đầu nên không blocks lịch ra mắt** |
| Bản ghi lệnh (`cid`, giá vào/ra, khối lượng, chiều) | `order-execution` | FR-022, FR-024, FR-026 |
| Định nghĩa **phiên** kể cả khi vắt qua nửa đêm | `order-execution` (FR-007) | FR-045, FR-047 |
| Đường thoát để **không** khoá | `order-execution` (FR-029) | Không có gì để kiểm chứng FR-002 |
| Thông báo lệnh vừa đóng + phần dẫn đường sang | `order-execution` (FR-039) | FR-054 — xem OQ-2 |
| Bản ghi âm **nghe lại và tua được** | `voice-journal` (FR-057) | FR-033, FR-034 |
| Cơ chế ghi âm + ngoại lệ đích gắn memo | `voice-journal` (FR-021) | FR-039, FR-040 |
| Kết quả chấm luật theo `cid` | `playbook-grading` (FR-044) | FR-043 |
| Sự kiện đổi mức tâm lý kèm mốc thời gian | `tilt-meter` (FR-048) | Một loại sự kiện của FR-018 |
| Đường vào từ lịch sử và chi tiết một lệnh | `daily-journal` (FR-044) | Đường vào chính; FR-054 là đường còn lại và nó đang blocked |
| Bề mặt đọc ba thước đo thành xu hướng | `process-score` + `daily-journal` | SC-01..03 — bản ghi vẫn sinh ra, chỉ chưa ai đọc |

**Assumptions (tin là đúng — nêu hệ quả nếu sai):**

| Giả định | Invalidate {X} nếu sai |
|----------|------------------------|
| ~~Việc đóng băng bối cảnh thuộc feature này~~ (URD A-01) | **Đã giải 2026-08-29: thuộc `order-execution`.** Feature này là **màn đọc dữ liệu có sẵn**, không phải màn đọc cộng hạ tầng ghi |
| Khoá áp cho **mở lệnh mới và sửa bảo vệ**, không áp cho đóng và thoát khẩn cấp (URD A-02) | Người chơi **bị kẹt trong màn ôn tập** — rủi ro lớn hơn nhiều so với bắn nhầm. **Đã xác nhận**; nêu lại như một bất biến có test riêng |
| Người chơi **không cần** xem lại cả buổi như một dòng liên tục (URD A-04) | **Cách lưu bối cảnh đổi hoàn toàn** — hiện chỉ lưu quanh từng lệnh. Xem OQ-9 |
| Người chơi chấp nhận lần đứng ngoài **ngoài cửa sổ của mọi lệnh** không tua lại được (URD A-06) | Phải quay lại lưu bối cảnh cho cả lần huỷ — **đảo ngược FR-010**. Đã xác nhận 2026-08-28 |
| **Mở màn replay là đủ** để trục Review ghi nhận, và không bị lợi dụng (URD A-07) | Thành thói quen mở rồi thoát để lấy điểm → trục Review mất ý nghĩa. **Cơ chế hiện tại chỉ đo chứ không ngăn** — theo dõi qua SC-02 |
| **Feature này tạo ra bản ghi "lệnh nào đã xem lại, lúc nào"** (URD A-08 🔶) | `process-score` chỉ lưu ở mức phiên, không đủ cho SC-01 (đếm theo lệnh) và SC-02 (cần mốc thời gian). **Không ai nhận thì cả ba thước đo không đo được.** Xem OQ-3 |
| Cửa sổ **5 phút trước / 5 phút sau** là đủ (URD A-09) | Ngắn quá thì không thấy bối cảnh dẫn tới setup; dài quá thì tốn chỗ mà không ai xem tới. Xem OQ-8 |

## 12. Open Questions

> **Số OQ đánh riêng cho từng tài liệu.** `OQ-3` của SRS này không nhất thiết là `OQ-3` của PRD cùng feature.
> Neo ổn định để đối chiếu là **số OQ của URD** ghi trong ngoặc *(kế thừa URD OQ-x)*.

* [x] **OQ-1** *(kế thừa URD A-01)*: Việc **tự đóng băng bối cảnh quanh mỗi lệnh** thuộc feature này hay
  `order-execution`?
  **Resolved 2026-08-29: `order-execution` sở hữu.** Bốn lý do: (1) `phase-02` — nguồn mà chính URD dẫn cho
  UN-014 — vốn đã đặt vòng đệm ở đó; (2) `system-overview.md` cấm journal path đi trên order socket, mà một
  vòng đệm chạy liên tục trên luồng giá **là** đang ở trên đó; (3) luồng giá đã nằm sẵn trong tiến trình của
  `order-execution` nên không cần người đăng ký thứ hai; (4) **quyết định nhất** — feature này ship thứ bảy
  trong chín, nên nếu nó sở hữu việc đóng băng thì **mọi lệnh trước ngày nó ship vĩnh viễn không có tape**,
  và replay ra mắt bằng một màn rỗng.
  **Feature này trở lại đúng bản chất "màn đọc"**, và FR-012..FR-017 hết bị chặn.

* [ ] **OQ-2** *(kế thừa URD OQ-8, chung với `order-execution` OQ-7)*: Mở thẳng màn xem lại **từ thông báo
  lệnh vừa đóng** — nội dung thông báo thuộc `order-execution`, đường dẫn sang thuộc feature này.
  **Chặn FR-054.**
  🔶 **Tạm quyết:** `order-execution` **nhận** phần dẫn đường (đã ghi vào `order-execution` OQ-7 và để chỗ
  trong FR-039 của nó).
  *Nếu sai:* mất **đường vào nóng nhất, đúng đường SC-02 đặt cược**.

* [ ] **OQ-3** *(kế thừa URD A-08)*: `process-score` xác nhận rằng **feature này** tạo ra bản ghi "lệnh nào
  đã được xem lại, lúc nào" (FR-049) chứ?
  🔶 **Tạm quyết:** **có**. `process-score` chỉ lưu ở mức **phiên**, không đủ cho SC-01 (đếm theo lệnh) và
  SC-02 (cần mốc thời gian).
  *Nếu sai / nếu không ai nhận:* **cả ba thước đo SC-01..03 không đo được ở đâu cả.**

* [ ] **OQ-4** *(kế thừa URD OQ-5)*: SC-01 có **sàn tối thiểu tuyệt đối** không (vd "ít nhất 3 trên 10
  lệnh"), hay chỉ cần không giảm dần? Không có sàn thì SC-01 vẫn đạt kể cả khi tỷ lệ tuyệt đối rất thấp — và
  khi đó **không đọc được feature có đáng công sức bỏ ra hay không**.

* [ ] **OQ-5** *(kế thừa URD OQ-6)*: Bối cảnh đã lưu **giữ bao lâu** trước khi lệnh rơi về bản rút gọn
  (FR-029)?
  *Lưu ý — tiền đề của câu hỏi này đã đổi:* nguồn nêu bối cảnh ~2 năm, dài hơn hạn giữ bản ghi âm ~1 năm, nên
  "sẽ có giai đoạn tua được hình mà không còn tiếng". Nhưng `voice-journal` FR-058 đã chốt bản ghi âm **giữ
  vô thời hạn**. Cần **đối chiếu lại** trước khi trả lời.

* [ ] **OQ-6** *(kế thừa URD OQ-7, chung với `daily-journal` OQ-9)*: Lần tự huỷ **nằm ngoài cửa sổ của mọi
  lệnh** (FR-032) hiện ra ở đâu để người chơi "vẫn được ghi nhận là đã xảy ra"? Bề mặt đó thuộc
  `daily-journal` hay feature này? **Cần chốt một lần cho cả ba tài liệu** (cùng `process-score`).

* [ ] **OQ-7** *(kế thừa URD OQ-10)*: Nhãn memo trên dải thời gian (FR-042) hiện **bản máy chép** hay **bản
  người chơi đã sửa**?
  🔶 **Tạm quyết:** hiện **bản đang có hiệu lực** — bản đã sửa nếu có, không thì bản máy chép. Nhất quán với
  `voice-journal` BR-007 (bản sửa ghi đè bản máy chép, bản ghi âm là bản gốc).
  *Nếu sai:* nhãn trên dải thời gian nói khác nội dung người chơi đọc ở nơi khác.

* [x] **OQ-8** *(kế thừa URD A-09)*: Cửa sổ **5 phút trước / 5 phút sau** có đủ không?
  **Chuyển sang `order-execution` OQ-9 (2026-08-29)** — cửa sổ nay là tham số của bên sinh ra tape.

* [x] **OQ-9** *(kế thừa URD OQ-4)*: Có cần xem lại **cả buổi tối như một dòng liên tục** không?
  **Chuyển sang `order-execution` OQ-9 (2026-08-29)** — câu trả lời quyết định cách lưu tape, mà việc lưu nay
  thuộc bên đó. Feature này chỉ cần biết tape có sẵn ở dạng nào.

---

> **Nguồn:** `trade-replay-urd.md` (14 nhu cầu, 8 journey, 23 tình huống ngoại lệ, 3 thước đo, 9 giả định) ·
> `trade-replay-prd.md` (13 capability) · bốn tài liệu nền `docs/_shared/` · ranh giới nhận từ
> `order-execution`, `voice-journal`, `playbook-grading`, `tilt-meter`, `daily-journal`, `process-score`,
> `ai-desk`, `reports-export`.
>
> **🔶 Ba quyết định thay user:** OQ-2, OQ-3, OQ-7 — mỗi cái kèm hệ quả nếu sai. **OQ-1 em cố ý không
> quyết**: nó quyết định feature này to gấp đôi hay không, URD đã đánh dấu "không để trôi", và ba OQ khác
> (OQ-8, OQ-9, và một phần OQ-5) đều nên chốt cùng nó.
>
> **Tầng 2–4 chưa sinh:** `trade-replay-flows.md`, `-states.md`, `-erd.md`, use case, user story, AC.
