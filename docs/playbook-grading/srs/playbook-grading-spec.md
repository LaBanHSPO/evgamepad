---
type: srs
feature: playbook-grading
status: draft
updated: 2026-08-29
links:
  - docs/playbook-grading/playbook-grading-urd.md
  - docs/playbook-grading/playbook-grading-prd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/srs/order-execution-spec.md
  - docs/process-score/process-score-urd.md
  - docs/tilt-meter/tilt-meter-urd.md
---

# playbook-grading — Software Requirements Specification

## 1. Scope

Đặc tả việc **khai luật giao dịch của người chơi và đối chiếu mỗi lần vũ trang / mỗi lần bắn với chính bộ
luật đó**, kết quả hiện lên màn xác nhận **trước** thao tác cuối cùng — và ranh giới cứng rằng kết quả đó
**không bao giờ chặn được một lệnh**.

**Trong phạm vi:** soạn và sửa playbook (tên, phương pháp, cặp áp dụng, mô tả, danh sách luật có thứ tự) ·
mỗi luật khai rõ bắt buộc-hay-không và tự-kiểm-hay-tự-đánh-giá · bộ playbook mẫu · chọn playbook đang dùng
bằng tay cầm · chấm điểm mỗi lần vũ trang và mỗi lần bắn (kể cả lần tự huỷ và lần bị hạn mức chặn) · hiển
thị `n/m` và luật không đạt trên màn xác nhận · nhóm "ngoài kế hoạch" · checklist tự-đánh-giá sau khi lệnh
đóng · xem lại một lệnh đã chấm · ngừng dùng playbook mà giữ lịch sử.

**Ngoài phạm vi:** thống kê hiệu quả theo playbook và mọi so sánh nhiều lệnh (`process-score`) · điểm quy
trình 5 trục (`process-score`) · hạn mức rủi ro và việc thi hành (`order-execution`) · bộ đếm tự huỷ trên
màn chính (`order-execution`) · đo trạng thái tâm lý (`tilt-meter`) · nhận diện setup, tư vấn, tín hiệu
(`ai-desk`) · ghi âm (`voice-journal`) · tua lại tape (`trade-replay`) · nghi thức trước phiên
(`daily-journal`) · báo cáo và xuất dữ liệu (`reports-export`) · chia sẻ playbook giữa nhiều người dùng.

> **Hai ranh giới quyết định toàn bộ tài liệu này.** (1) **Luật playbook được chấm, luật rủi ro được thi
> hành** — không có cách nào khai một luật playbook thành luật chặn. (2) **Việc chấm là một hàm thuần trên
> bối cảnh** — không mô hình ngôn ngữ nào tham gia, và cùng một bối cảnh luôn cho cùng một điểm.
>
> **Hai chữ dùng nhất quán:** *tự huỷ* = người chơi đã vũ trang rồi chủ động không vào; *bị chặn* = hạn mức
> rủi ro của `order-execution` không cho lệnh đi. **Cả hai đều được chấm điểm.**

## 2. Actors & Stakeholders

| Actor | Loại | Mục tiêu | Trong scope? |
|-------|------|----------|--------------|
| **Người chơi — vai người viết luật** | người | Biến một cách chơi quen thuộc thành danh sách luật máy đối chiếu được | Có |
| **Người chơi — vai người bị luật soi** | người | Biết lệnh sắp bắn có đúng sách không, khi còn quyền không vào | Có |
| **Bộ chấm điểm** | hệ thống | Hàm thuần trên bối cảnh → trạng thái từng luật + `n/m` | Có |
| **`order-execution`** | hệ thống | Sở hữu màn xác nhận, chuỗi vũ trang–bắn, menu an toàn, hạn mức rủi ro | **Không** — là ranh giới tích hợp |
| **`process-score`** | hệ thống | Đọc điểm làm trục tuân thủ; là nơi duy nhất đọc điểm thành xu hướng | **Không** — chỉ đọc |
| **`tilt-meter`** | hệ thống | Đọc số luật không đạt trong ba lần bắn gần nhất làm một tín hiệu | **Không** — chỉ đọc |
| **`trade-replay`** | hệ thống | Đặt kết quả chấm cạnh dòng thời gian của một lệnh | **Không** — chỉ đọc |
| **AI desk** | hệ thống | — | **Không, vĩnh viễn.** Không tham gia chấm, không sửa được điểm, không giải thích thay luật |

## 3. Functional Requirements (FR)

### 3.1 Soạn và quản lý playbook

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-playbook-grading-001 | Khai một playbook | Người chơi khai: tên, phương pháp, **cặp áp dụng**, mô tả bằng lời của chính mình, và một **danh sách luật có thứ tự** | P0 | demo | URD UN-013 |
| FR-playbook-grading-002 | Cặp áp dụng là **một luật**, không phải bộ lọc | Bắn ngoài danh sách cặp đã khai → tính là **một luật không đạt**, nằm trong cùng con số `n/m`. **Không** cản lệnh và **không** sinh thêm loại cảnh báo riêng | P0 | test | URD Mục 3 (OQ-5 resolved) |
| FR-playbook-grading-003 | Mỗi luật khai hai thuộc tính | Mỗi luật khai rõ: **bắt buộc hay không**, và **hệ thống tự kiểm hay người chơi tự trả lời sau lệnh** | P0 | demo | URD UN-013 |
| FR-playbook-grading-004 | Trang soạn dùng chuột và bàn phím | Trang soạn playbook là bề mặt **ngoài phiên**; nó không cần dùng được bằng tay cầm | P0 | kiểm tra | URD UN-012 (dựa A-01) |
| FR-playbook-grading-005 | Validate tên playbook | Chặn khi lưu nếu trùng tên một playbook đã có, và nói rõ tên đã tồn tại — trên tay cầm chỉ nhìn thấy tên, nên tên phải phân biệt được | P0 | test | URD Mục 6 |
| FR-playbook-grading-006 | Validate tham số luật | Chặn **ngay tại trang soạn** khi tham số vô lý (ngưỡng âm, ngưỡng không bao giờ đạt được), nói rõ khoảng giá trị hợp lệ — trước khi luật đó kịp chấm một lệnh nào | P0 | test | URD Mục 6 |
| FR-playbook-grading-007 | Hiển thị nguyên văn ký tự người chơi gõ | Tên và mô tả playbook hiện **đúng nguyên văn** ở mọi nơi: trang soạn, menu chọn trên tay cầm, màn xác nhận, và bản ghi lệnh cũ | P0 | test | URD Mục 6 |
| FR-playbook-grading-008 | Trạng thái chưa lưu hiện rõ | Sửa luật xong nhưng chưa lưu → trạng thái chưa lưu hiện rõ ở trang soạn; lệnh vẫn được chấm theo **luật đã lưu** | P0 | test | URD Mục 6 |
| FR-playbook-grading-009 | Sửa luật không đụng điểm đã chấm | Sửa luật của một playbook **không** làm đổi bất kỳ điểm nào đã chấm. Luật mới chỉ áp cho các lần vũ trang **sau** thời điểm lưu | P0 | test | URD UN-004 |
| FR-playbook-grading-010 | Ngừng dùng một playbook | Playbook đánh dấu ngừng dùng biến khỏi **menu chọn trên tay cầm**; các lệnh cũ vẫn tra ra đúng tên playbook và đúng điểm đã chấm chúng | P1 | demo | URD UN-011 |

### 3.2 Bộ playbook mẫu

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-playbook-grading-011 | Bộ mẫu dựng theo các setup M5 quen thuộc | Sản phẩm khởi tạo với một bộ playbook mẫu (hộp tích luỹ, phá vỡ, kiểm lại sau phá vỡ, phá vỡ giả, phá khối) — **dùng được ngay** và sửa được thành của mình | P0 | demo | URD UN-003 |
| FR-playbook-grading-012 | Không tự dựng lại bộ mẫu đã bị bỏ | Người chơi ngừng dùng hết playbook → nói rõ hiện không còn sách nào chọn được và chỉ đường về trang soạn; mọi lệnh sau đó rơi vào "ngoài kế hoạch". Hệ thống **không** tự dựng lại bộ mẫu người chơi đã chủ động bỏ | P0 | test | URD Mục 6 |

### 3.3 Chọn playbook đang dùng

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-playbook-grading-013 | Chọn playbook bằng tay cầm | Người chơi chọn playbook đang dùng trong **menu an toàn**, bằng D-pad và nút áp dụng, theo hợp đồng điều hướng chung | P0 | demo | URD UN-006 · Definitions |
| FR-playbook-grading-014 | Playbook đang dùng thuộc trạng thái phiên | Playbook đang dùng là một phần trạng thái của **phiên**; nó hiện rõ trên màn chính để không bao giờ chấm nhầm sách | P0 | demo | URD UN-006 |
| FR-playbook-grading-015 | Một playbook đang dùng tại một thời điểm | Tại một thời điểm có đúng một playbook đang dùng, hoặc không có cái nào. Muốn chấm theo sách khác thì đổi **trước khi vũ trang** | P0 | test | URD Mục 7 (dựa A-02) |
| FR-playbook-grading-016 | Playbook chưa có luật nào không xuất hiện trong menu chọn | Playbook lưu được để soạn tiếp, nhưng **không hiện trong menu chọn trên tay cầm** cho tới khi có ít nhất một luật. Nhờ vậy cảnh "0/0 đạt hết" không bao giờ xảy ra | P0 | test | URD OQ-3 resolved |
| FR-playbook-grading-017 | Đổi playbook khi đang vũ trang | Trạng thái vũ trang bị huỷ trước (luật của `order-execution` FR-018), nên **không có** một lần vũ trang nào bị chấm bằng hai sách. Lần vũ trang lại là một bản ghi mới, chấm theo sách mới | P0 | test | URD Mục 6 · `order-execution` FR-018 |

### 3.4 Chấm điểm

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-playbook-grading-018 | Chấm mỗi lần vũ trang và mỗi lần bắn | Hệ thống chấm điểm theo playbook đang dùng tại **mỗi lần vũ trang** và **mỗi lần bắn** | P0 | test | URD Mục 3 |
| FR-playbook-grading-019 | Chấm cả lần tự huỷ và lần bị hạn mức chặn | Lần vũ trang kết thúc bằng **tự huỷ**, và lần bắn **bị hạn mức rủi ro chặn**, đều được chấm và lưu như mọi lần khác | P0 | test | URD Mục 3 · Mục 6 |
| FR-playbook-grading-020 | Điểm là hàm thuần trên bối cảnh | Cùng một bối cảnh luôn cho ra cùng một điểm. **Không mô hình ngôn ngữ nào tham gia**; AI desk không chấm, không sửa được điểm, không giải thích thay luật | P0 | test | URD UN-007 |
| FR-playbook-grading-021 | Điểm lúc bắn là bản ghi chính thức | Điểm được tính lại **tại thời điểm bắn**. Điểm lúc vũ trang là tham khảo; điểm lúc bắn là bản ghi chính thức | P0 | test | URD UN-008 |
| FR-playbook-grading-022 | Giữ cả hai lần chấm khi chúng khác nhau | Điểm lúc vũ trang khác điểm lúc bắn → **giữ lại cả hai**; bản ghi nêu rõ cái nào chính thức và cái nào chỉ tham khảo | P0 | test | URD Mục 6 |
| FR-playbook-grading-023 | Bốn trạng thái của một luật | Mỗi luật ở đúng một trạng thái: **đạt** · **không đạt** · **không kiểm được** (thiếu dữ liệu) · **chưa trả lời** (luật tự-đánh-giá chưa được trả lời) | P0 | test | URD UN-014 · Mục 6 |
| FR-playbook-grading-024 | Định nghĩa "tổng số luật xét" | Tổng số luật xét = **mọi luật của playbook đang dùng, trừ** luật không kiểm được **và** luật tự-đánh-giá chưa trả lời. Luật rơi ra **không** tính là đạt, cũng **không** tính là sai | P0 | test | URD UN-001 |
| FR-playbook-grading-025 | Kết luận "đạt đủ luật bắt buộc" | Kết luận này tính trên **nhóm bắt buộc nằm trong tổng số luật xét** (FR-024) | P0 | test | URD UN-001 (🔶) |
| FR-playbook-grading-026 | Luật không kiểm được hiện rõ là đã rơi ra | Thiếu dữ liệu để kiểm một luật tự động (giá đã cũ, chưa đủ nến, AI desk im lặng) → luật đó đọc là **không kiểm được**, rơi khỏi tổng số luật xét, và **người chơi thấy rõ nó rơi** | P0 | test | URD Mục 6 |
| FR-playbook-grading-027 | Giữ điểm khi kết quả trên sàn chưa rõ | Bắn xong mà chưa rõ lệnh có tới sàn không → điểm của lần bắn đó **vẫn được giữ và gắn với chính lần bắn**; nó không biến mất và **không tự nhận là đã khớp** | P0 | test | URD Mục 6 · `order-execution` FR-023 |
| FR-playbook-grading-028 | Chỉ vũ trang và bắn mới sinh điểm | Thao tác sửa mức bảo vệ hoặc đóng vị thế **không** tạo thêm bản ghi điểm nào | P0 | test | URD Mục 6 |

### 3.5 Hiển thị trên màn xác nhận

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-playbook-grading-029 | Nội dung điểm trên màn xác nhận | Màn xác nhận (do `order-execution` sở hữu) nêu: **tên playbook đang dùng**, **số luật đạt trên tổng số luật xét**, và **tên (các) luật không đạt** — đủ ngắn để đọc hết trước khi bấm | P0 | demo | URD UN-001 |
| FR-playbook-grading-030 | Điểm là một phần của chính màn xác nhận | Màn xác nhận **không mở ra khi chưa có điểm**. **Không** có trạng thái "đang tính" và **không** đoán bừa một con số. Không tồn tại khoảnh khắc người chơi thấy nút bấm mà chưa thấy điểm | P0 | test | URD UN-001 (OQ-1 resolved) · xem OQ-2 |
| FR-playbook-grading-031 | Không thêm bước vào chuỗi xác nhận | Feature này **đóng góp nội dung** vào màn xác nhận; nó **không** thêm bước nào vào chuỗi xác nhận hai tay của `order-execution` | P0 | test | URD Mục 3 |
| FR-playbook-grading-032 | Playbook chỉ toàn luật tự-đánh-giá | Nói rõ playbook này **chỉ đối chiếu được sau khi lệnh đóng**, thay vì hiện một con số rỗng | P0 | test | URD Mục 6 |

### 3.6 Ranh giới không chặn

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-playbook-grading-033 | Luật playbook không bao giờ chặn một lệnh | Một luật playbook không đạt vẫn cho lệnh đi **trọn vẹn**: không bước cản, không cảnh báo chặn, không xác nhận phụ. Chỉ hạn mức rủi ro mới chặn được | P0 | test | URD UN-002 |
| FR-playbook-grading-034 | Không có cách khai luật thành luật chặn | Ranh giới FR-033 **không phụ thuộc cách người chơi khai luật**. Trang soạn không cung cấp bất kỳ lựa chọn nào biến một luật playbook thành luật chặn | P0 | test | URD UN-002 |
| FR-playbook-grading-035 | Điểm và lý do bị chặn không lẫn vào nhau | Lần bắn bị hạn mức chặn → người chơi thấy **đồng thời** điểm luật playbook và lý do bị hạn mức chặn, trình bày tách bạch | P0 | demo | URD Mục 6 |

### 3.7 Nhóm "ngoài kế hoạch"

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-playbook-grading-036 | Bắn khi chưa chọn playbook | Lệnh vẫn đi bình thường. Màn xác nhận nói rõ đang không có playbook nào — **không báo lỗi, không cản** | P0 | test | URD UN-005 |
| FR-playbook-grading-037 | Ghi vào nhóm "ngoài kế hoạch" | Bản ghi của lệnh đó thuộc nhóm **"ngoài kế hoạch"** và đọc ra đúng như vậy ở **mọi nơi nhìn lại** | P0 | test | URD UN-005 |

### 3.8 Checklist tự-đánh-giá sau khi lệnh đóng

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-playbook-grading-038 | Checklist tối đa 3 câu | Checklist gồm **tối đa 3 câu, mỗi câu một thao tác**, đúng các luật tự-đánh-giá của playbook đã chấm lệnh đó | P1 | demo | URD UN-009 |
| FR-playbook-grading-039 | Hiện ngay khi lệnh đóng, không chen ngang | Checklist hiện **ngay khi lệnh đóng** lúc bối cảnh còn nóng, nhưng **không bao giờ đè lên thao tác đang làm** | P1 | test | URD UN-009 (OQ-4 resolved) |
| FR-playbook-grading-040 | Xếp hàng khi nhiều lệnh đóng liên tiếp | Các checklist xếp hàng theo thứ tự đóng; cái nào chưa trả lời tới cuối phiên thì được gợi lại **một lần**, rồi thôi. Mỗi checklist nêu rõ nó thuộc lệnh nào, lúc nào | P1 | test | URD Mục 6 |
| FR-playbook-grading-041 | Bỏ qua không bị trừ | Bỏ qua được ở mọi thời điểm. Luật chưa trả lời **rơi khỏi tổng số luật xét** (FR-024) — không tính là sai, không tốn của người chơi thứ gì | P1 | test | URD UN-009 |
| FR-playbook-grading-042 | Câu trả lời muộn làm đổi kết luận của **lệnh** | Câu trả lời tự-đánh-giá là một lớp ghi thêm sau khi lệnh đóng, và nó **có** làm đổi kết luận "đạt đủ luật bắt buộc" của lệnh đó — vì đó chính là việc nó sinh ra để làm. Phần hệ thống tự kiểm **đóng băng tại thời điểm bắn và không bao giờ đổi** | P1 | test | URD UN-004 (🔶) |
| FR-playbook-grading-043 | Câu trả lời muộn **không** làm tính lại điểm của **buổi** | Điểm quy trình đã chốt của `process-score` không được tính lại vì một câu trả lời muộn. Câu trả lời muộn làm giàu bản ghi của **lệnh**, không đụng tới điểm của **buổi** | P1 | kiểm tra | `process-score` A-10 (🔶) |

### 3.9 Xem lại một lệnh đã chấm

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-playbook-grading-044 | Mở lại một lệnh đã chấm | Người chơi mở một lệnh và thấy: **playbook nào chấm nó**, và **từng luật ở trạng thái nào** trong bốn trạng thái của FR-023 | P0 | demo | URD UN-014 |
| FR-playbook-grading-045 | Lịch sử vẫn tra được sau khi playbook ngừng dùng | Lệnh chấm bởi một playbook đã ngừng dùng vẫn tra ra đúng tên và đúng điểm | P1 | test | URD UN-011 |
| FR-playbook-grading-046 | Điểm của một lần tự huỷ đạt đủ luật bắt buộc | Setup bị tự huỷ **đạt đủ luật bắt buộc** → hiện thông tin đó **đúng một lần** cho một lần huỷ, tự biến mất, không cần thao tác đóng. Tự huỷ một setup **không** đạt thì **không nói gì** — đó chính là hành vi đúng | P1 | test | URD UN-010 |
| FR-playbook-grading-047 | "Đạt đủ" của một lần tự huỷ chỉ tính trên luật tự-kiểm | Vì một lần huỷ không bao giờ có "lệnh đóng", kết luận "đạt đủ" ở FR-046 **chỉ tính trên luật hệ thống tự kiểm được**. Playbook không còn luật bắt buộc tự-kiểm nào → **không hiện gì** | P1 | test | URD UN-010 |
| FR-playbook-grading-048 | Playbook có luật nhưng không luật nào bắt buộc | Điều kiện "đạt đủ luật bắt buộc" đọc là **chưa có luật bắt buộc nào để kết luận**, **không** đọc là đạt. FR-046 không hiện gì trong trường hợp này | P1 | test | URD Mục 6 |
| FR-playbook-grading-049 | Điểm của lần tự huỷ và bộ đếm phải đọc được như một | Cùng khoảnh khắc bộ đếm tự huỷ của `order-execution` tăng, thông tin điểm của FR-046 (nếu có) xuất hiện. Hai thông tin **không đá nhau** | P1 | demo | URD Journey 4 |

## 4. Non-Functional Requirements (NFR)

| ID | Category | Requirement | Priority | Acceptance |
|----|----------|-------------|----------|------------|
| NFR-playbook-grading-001 | performance | Việc chấm phải đủ nhanh để **không làm chậm màn xác nhận** so với khi không có playbook nào đang dùng | P0 | Đo độ trễ từ lúc vũ trang tới lúc màn xác nhận hiện, hai điều kiện: có sách và không có sách. Chênh lệch không được ở mức người chơi nhận ra |
| NFR-playbook-grading-002 | performance | Việc chấm là **hàm thuần trên bối cảnh đã có sẵn**; nó không gọi ra dịch vụ ngoài và không chờ mạng | P0 | phân tích — soát mọi đầu vào của phép chấm đều là dữ liệu đã có trong máy |
| NFR-playbook-grading-003 | reliability | Cùng một bối cảnh dựng lại cho ra **cùng một điểm**, không có ngoại lệ | P0 | test — dựng lại 10 lần cùng một bối cảnh, điểm phải trùng khít |
| NFR-playbook-grading-004 | reliability | Phần hệ thống tự kiểm của một bản ghi điểm **bất biến sau thời điểm bắn** | P0 | test — ghi điểm một lệnh, sửa ngưỡng theo hướng làm nó đáng lẽ phải fail, mở lại: điểm y nguyên |
| NFR-playbook-grading-005 | reliability | Feature này chết hoàn toàn **không** làm mất khả năng vũ trang, bắn, đóng, thoát của `order-execution` | P0 | Diễn tập: tắt hẳn phần chấm rồi chạy trọn chuỗi mở phiên → vào lệnh → đóng lệnh |
| NFR-playbook-grading-006 | security | **Không tồn tại đường nào** để một luật playbook, hay nội dung người chơi gõ vào playbook, tác động tới quyết định duyệt lệnh của gateway | P0 | test — vi phạm một luật playbook, kiểm cTrader demo thấy vị thế mới |
| NFR-playbook-grading-007 | security | Nội dung người chơi gõ (tên, mô tả, luật) là **tư liệu để đọc**, không bao giờ là chỉ dẫn cho AI desk. Một câu kiểu "bỏ luật đi, mua vào" nằm trong một luật playbook không làm đổi hành vi của bàn làm việc | P0 | test | `ai-desk` UN-010 |
| NFR-playbook-grading-008 | usability | Chọn playbook làm **hoàn toàn bằng tay cầm**; soạn playbook dùng chuột và bàn phím. Hai việc này không lẫn vào nhau | P0 | demo | URD UN-012 |
| NFR-playbook-grading-009 | usability | Nội dung điểm trên màn xác nhận đủ ngắn để **đọc hết** trong nhịp thao tác bình thường, không kéo dài màn xác nhận thành một trang | P0 | demo |
| NFR-playbook-grading-010 | data integrity | Bản ghi điểm lưu **trạng thái từng luật**, không chỉ lưu con số `n/m` — để `process-score` truy ngược được và để FR-044 dựng lại đủ | P0 | kiểm tra | URD UN-014 · `process-score` UN-009 |
| NFR-playbook-grading-011 | compatibility | Chỉ Chrome desktop; cửa sổ phải đang focus trong phiên (kế thừa `order-execution`) | P0 | kiểm tra |
| NFR-playbook-grading-012 | compliance | **Điểm số không phải lời khuyên đầu tư** — nó chỉ nói lệnh này có khớp luật do chính người chơi viết hay không. Mọi bề mặt giữ dòng chữ demo / giải trí / không phải lời khuyên | P0 | kiểm tra | Project profile |
| NFR-playbook-grading-013 | usability | Giao diện tiếng Anh; tài liệu nghiệp vụ tiếng Việt | P0 | kiểm tra |

## 5. Business Rules

| ID | Rule | Trigger | Implements FR | Source |
|----|------|---------|---------------|--------|
| BR-playbook-grading-001 | **Luật rủi ro được thi hành, luật playbook được chấm.** Một luật playbook không bao giờ từ chối một intent | Mọi lần bắn | FR-033, FR-034 | URD UN-002 |
| BR-playbook-grading-002 | Cặp áp dụng được đối chiếu **như một luật**, không như một bộ lọc | Bắn cặp ngoài danh sách playbook khai | FR-002 | URD OQ-5 resolved |
| BR-playbook-grading-003 | Tổng số luật xét loại **luật không kiểm được** và **luật tự-đánh-giá chưa trả lời**; luật rơi ra không tính đạt cũng không tính sai | Mọi lần chấm | FR-024, FR-026, FR-041 | URD UN-001, UN-009 |
| BR-playbook-grading-004 | Điểm **lúc bắn** là bản ghi chính thức; điểm lúc vũ trang là tham khảo | Mỗi lần bắn | FR-021, FR-022 | URD UN-008 |
| BR-playbook-grading-005 | Phần hệ thống tự kiểm **đóng băng tại thời điểm bắn**; phần tự-đánh-giá là lớp ghi thêm sau khi lệnh đóng và **có** làm đổi kết luận "đạt đủ luật bắt buộc" của lệnh | Sửa luật · trả lời checklist | FR-009, FR-042 | URD UN-004 (🔶) |
| BR-playbook-grading-006 | Câu trả lời checklist muộn **không** làm tính lại điểm quy trình đã chốt của buổi | Trả lời checklist sau khi phiên đã đóng | FR-043 | `process-score` A-10 (🔶) |
| BR-playbook-grading-007 | Playbook **chưa có luật nào** lưu được nhưng không hiện trong menu chọn trên tay cầm | Lưu playbook rỗng | FR-016 | URD OQ-3 resolved |
| BR-playbook-grading-008 | Kết luận "đạt đủ" cho một **lần tự huỷ** chỉ tính trên luật hệ thống tự kiểm được | Mỗi lần tự huỷ | FR-047, FR-048 | URD UN-010 |
| BR-playbook-grading-009 | Bộ đếm tự huỷ đếm **mọi** lần tự huỷ chủ động, không phụ thuộc kết quả chấm luật. Điểm playbook là **lớp thông tin thêm** cho một lần huỷ, không phải điều kiện để nó được đếm | Mỗi lần tự huỷ | FR-049 | URD OQ-8 resolved · `order-execution` BR-004 |
| BR-playbook-grading-010 | **Không mô hình ngôn ngữ nào chấm một lệnh**, ở bất kỳ phiên bản nào | Mọi lần chấm | FR-020 | URD UN-007 |
| BR-playbook-grading-011 | Một playbook đang dùng tại một thời điểm; đổi sách phải làm **trước khi vũ trang** | Chọn playbook | FR-015, FR-017 | URD Mục 7 (A-02) |
| BR-playbook-grading-012 | Chỉ **vũ trang** và **bắn** sinh ra bản ghi điểm; sửa bảo vệ và đóng vị thế thì không | Thao tác trên vị thế | FR-028 | URD Mục 6 |

## 6. Error Matrix

| Error ID | Title | Trigger | Severity | Related FR | Screen state | Recovery |
|----------|-------|---------|----------|------------|--------------|----------|
| E-playbook-grading-001 | Thiếu dữ liệu để kiểm một luật | Giá đã cũ, chưa đủ nến, hoặc AI desk im lặng | major | FR-026 | Luật đọc là **không kiểm được**, hiện rõ nó đã rơi khỏi tổng | Không phải lỗi người chơi; luật quay lại khi dữ liệu sống lại |
| E-playbook-grading-002 | Playbook chỉ toàn luật tự-đánh-giá | Playbook đang dùng không có luật tự-kiểm nào | minor | FR-032 | Nói rõ playbook này chỉ đối chiếu được sau khi lệnh đóng | Thêm ít nhất một luật tự-kiểm nếu muốn thấy điểm trước khi bấm |
| E-playbook-grading-003 | Playbook chưa có luật nào | Lưu một playbook mới soạn dở | minor | FR-016 | Lưu thành công, kèm ghi chú chưa hiện trong menu chọn | Thêm ít nhất một luật |
| E-playbook-grading-004 | Trùng tên playbook | Lưu với tên đã tồn tại | minor | FR-005 | Chặn khi lưu, nói rõ tên đã tồn tại | Đổi tên |
| E-playbook-grading-005 | Tham số luật vô lý | Ngưỡng âm, hoặc ngưỡng không bao giờ đạt được | minor | FR-006 | Chặn ngay tại trang soạn, nói rõ khoảng hợp lệ | Sửa tham số trước khi luật kịp chấm lệnh nào |
| E-playbook-grading-006 | Không còn playbook nào chọn được | Người chơi ngừng dùng hết playbook | major | FR-012 | Nói rõ hiện không còn sách nào và chỉ đường về trang soạn | Soạn sách mới. **Không** tự dựng lại bộ mẫu đã bị bỏ |
| E-playbook-grading-007 | Playbook đang dùng bị ngừng dùng giữa phiên | Đánh dấu ngừng dùng chính sách đang hoạt động | minor | FR-010 | Các lệnh đã chấm giữ nguyên; lần vũ trang sau nói rõ vì sao đổi trạng thái | Chọn sách khác — xem OQ-6 |
| E-playbook-grading-008 | Sửa luật chưa lưu rồi quay lại giao dịch | Rời trang soạn khi còn thay đổi chưa lưu | minor | FR-008 | Trạng thái chưa lưu hiện rõ ở trang soạn | Lệnh vẫn chấm theo luật đã lưu — không âm thầm dùng luật nháp |
| E-playbook-grading-009 | Bắn khi chưa chọn playbook | Không có sách nào đang dùng | minor | FR-036, FR-037 | Màn xác nhận nói rõ đang không có playbook nào | **Không** báo lỗi, **không** cản; lệnh vào nhóm "ngoài kế hoạch" |
| E-playbook-grading-010 | Lần bắn bị hạn mức rủi ro chặn | Vượt hạn mức của `order-execution` | major | FR-035 | Hiện đồng thời điểm luật playbook và lý do bị chặn, tách bạch | Điểm vẫn được ghi và xem lại được |
| E-playbook-grading-011 | Kết quả trên sàn chưa rõ sau khi bắn | `order-execution` chuyển sang trạng thái "chưa rõ" | major | FR-027 | Điểm giữ nguyên, gắn với chính lần bắn đó | Điểm **không** tự nhận là đã khớp; trạng thái lệnh do `order-execution` gỡ |
| E-playbook-grading-012 | Điểm lúc vũ trang khác điểm lúc bắn | Bối cảnh đổi giữa hai thời điểm | minor | FR-022 | Bản ghi nêu rõ điểm nào chính thức, điểm nào tham khảo | Không phải lỗi; là thông tin người chơi cần thấy |
| E-playbook-grading-013 | Playbook khai cặp khác cặp đang giao dịch | Bắn ngoài danh sách cặp đã khai | minor | FR-002 | Tính là **một luật không đạt** trong cùng `n/m` | **Không** cản, **không** sinh cảnh báo riêng |
| E-playbook-grading-014 | Nhiều lệnh đóng liên tiếp | Hai vị thế trở lên đóng gần nhau | minor | FR-040 | Checklist xếp hàng, không cái nào chen ngang thao tác đang làm | Trả lời sau, hoặc bỏ qua hết — đều hợp lệ |
| E-playbook-grading-015 | Lệnh đóng khi người chơi đã rời máy | Vị thế đóng lúc không có ai ngồi trước màn hình | minor | FR-040 | Checklist chờ ở hàng đợi, nêu rõ thuộc lệnh nào, lúc nào | Trả lời muộn hoặc bỏ hẳn đều không bị phạt |
| E-playbook-grading-016 | Playbook có luật nhưng không luật nào bắt buộc | Mọi luật đều khai là không bắt buộc | minor | FR-048 | Đọc là **chưa có luật bắt buộc nào để kết luận** | FR-046 không hiện gì; thêm luật bắt buộc nếu muốn dùng tính năng đó |
| E-playbook-grading-017 | Tên hoặc mô tả chứa ký tự đặc biệt | Người chơi gõ ký tự ngoài bảng chữ thường | minor | FR-007 | Hiện đúng nguyên văn ở mọi bề mặt | Không phải lỗi — là yêu cầu hiển thị |
| E-playbook-grading-018 | Đổi playbook hoặc mở menu khi đang vũ trang | Bấm `Menu` trong lúc ARM | minor | FR-017 | Trạng thái vũ trang bị huỷ trước (luật `order-execution`) | Lần vũ trang lại là bản ghi mới, chấm theo sách mới |
| E-playbook-grading-019 | Việc chấm chưa xong tại thời điểm vũ trang | Phép chấm chậm bất thường | **critical** | FR-030 | Màn xác nhận **không mở ra** cho tới khi có điểm | Không có trạng thái "đang tính", không đoán bừa. Nếu chậm rõ rệt → đặt lại lựa chọn này, xem OQ-2 |

## 7. Success Criteria

| ID | Outcome nghiệp vụ | Đo bằng | Mốc đạt |
|----|-------------------|---------|---------|
| SC-playbook-grading-01 | Người chơi ngày càng giao dịch theo sách của chính mình | Đếm số lệnh theo nhóm playbook so với nhóm "ngoài kế hoạch". **Không tính vào tử số** lệnh mà chính luật "cặp nằm trong danh sách khai" không đạt | Cao hơn baseline sau 3 tháng (chưa có sàn tối thiểu — xem OQ-1) |
| SC-playbook-grading-02 | Chất lượng tuân thủ đi lên, không phải điểm đi lên nhờ nới luật | Tỷ lệ đạt đủ **luật bắt buộc**, đọc **kèm** số luật bắt buộc trung bình mỗi sách **và** số lần nới tham số luật trong kỳ | Cao hơn baseline sau 3 tháng **và** số luật bắt buộc trung bình không giảm |
| SC-playbook-grading-03 | Luật của người chơi không bao giờ cấm được người chơi | Checkpoint hai bối cảnh trên **cùng một thao tác**: vi phạm luật playbook → vị thế mới xuất hiện trên cTrader demo; vi phạm hạn mức rủi ro → lệnh bị chặn | 0 lần một luật playbook chặn được lệnh — **ranh giới tuyệt đối**, không phải xu hướng |
| SC-playbook-grading-04 | Điểm luôn có mặt đúng lúc còn sửa được | Rà mọi lần vũ trang trong phiên | 0 lần màn xác nhận hiện ra kèm ô điểm trống |
| SC-playbook-grading-05 | Điểm là kết quả tính toán, không phải ý kiến | Dựng lại cùng một bối cảnh 10 lần | 10/10 cho cùng một điểm |
| SC-playbook-grading-06 | Lịch sử điểm bất biến qua mọi lần sửa luật | Ghi điểm một lệnh → sửa ngưỡng làm nó đáng lẽ phải fail → mở lại | Điểm y nguyên, 100% các lần thử |

> **SC-01 và SC-02 đọc từ bề mặt thuộc `process-score`** (URD A-08). Chưa có deck thì đọc thô bằng cách
> đếm tay từ bản ghi lệnh của chính feature này, và ghi rõ đó là số đọc thô — xem OQ-5.
>
> **SC-03 tới SC-06 tự đo được ngay** từ dữ liệu của feature này, không phụ thuộc lịch của feature khác.
> Đây là bốn thước đo giữ cho feature không âm thầm hỏng trong ba tháng chờ deck.

## 8. Data Entities (tóm tắt — chi tiết ở `playbook-grading-erd.md`)

| Entity | Ý nghĩa nghiệp vụ | Thông tin nghiệp vụ cần lưu |
|--------|-------------------|------------------------------|
| **Playbook** | Một cách chơi người chơi tự khai | Tên · phương pháp · danh sách cặp áp dụng · mô tả bằng lời · thứ tự luật · thời điểm tạo · **thời điểm ngừng dùng** (nếu có) |
| **Luật playbook** | Một điều kiện trong sách | Thuộc playbook nào · thứ tự · nội dung/loại luật · tham số · **bắt buộc hay không** · **tự-kiểm hay tự-đánh-giá** · phiên bản luật |
| **Bản ghi điểm** | Kết quả chấm một lần vũ trang hoặc một lần bắn | Thuộc lần vũ trang / lần bắn nào · playbook nào (hoặc **"ngoài kế hoạch"**) · thời điểm · **loại: lúc vũ trang (tham khảo) hay lúc bắn (chính thức)** · số luật đạt · tổng số luật xét · kết luận đạt-đủ-luật-bắt-buộc · kết cục (bắn / tự huỷ / bị hạn mức chặn) |
| **Trạng thái một luật trong một bản ghi** | Từng luật đã ra sao lúc chấm | Luật nào (kèm phiên bản) · trạng thái trong bốn giá trị của FR-023 · có nằm trong tổng số luật xét không · thời điểm đóng băng |
| **Câu trả lời tự-đánh-giá** | Người chơi trả lời một luật chỉ mình biết | Bản ghi điểm nào · luật nào · trả lời · thời điểm trả lời · **đã bỏ qua hay chưa** |
| **Lựa chọn playbook của phiên** | Sách đang dùng tại từng thời điểm trong phiên | Phiên nào · playbook nào · thời điểm bắt đầu dùng · thời điểm thôi dùng |

> **Không có entity "bộ đếm tự huỷ"** — nó thuộc `order-execution`. Feature này chỉ gắn một *Bản ghi điểm*
> có kết cục "tự huỷ" vào cùng khoảnh khắc đó.

## 9. Flows (tóm tắt — chi tiết ở `playbook-grading-flows.md`)

| Flow | Tóm tắt | Nguồn |
|------|---------|-------|
| Vào lệnh và thấy điểm trước khi bấm | Chọn sách trong menu an toàn → vũ trang → màn xác nhận hiện tên sách + `n/m` + luật không đạt → bấm → chấm lại tại thời điểm bắn | URD Journey 1 |
| Một luật không đạt — lệnh vẫn đi | Màn xác nhận báo một luật không đạt → xác nhận như bình thường → lệnh đi trọn vẹn → bản ghi giữ nguyên sự thật | URD Journey 2 |
| Bắn khi chưa chọn playbook | Chưa có sách → vũ trang → màn xác nhận nói rõ không có sách → lệnh đi → bản ghi vào nhóm "ngoài kế hoạch" | URD Journey 3 |
| Từ chối một setup đạt đủ luật | Vũ trang → màn xác nhận báo đạt đủ luật bắt buộc → chủ động huỷ → hiện thông tin đúng một lần → điểm lưu lại, xem lại được | URD Journey 4 |
| Soạn một playbook mới | Mở trang soạn → đặt tên, cặp, mô tả → khai từng luật kèm hai thuộc tính → lưu → xuất hiện trong menu chọn khi có ≥1 luật | URD Journey 5 |
| Sửa luật giữa phiên rồi dùng ngay | Sửa ngưỡng → quay lại màn giao dịch → lần vũ trang sau chấm theo luật mới → lệnh cũ điểm không đổi | URD Journey 6 |
| Trả lời checklist sau khi lệnh đóng | Vị thế đóng → checklist ≤3 câu hiện, xếp hàng nếu bận → trả lời hoặc bỏ qua → luật chưa trả lời rơi khỏi tổng | URD Journey 7 |
| Ngừng dùng một playbook | Đánh dấu ngừng dùng → biến khỏi menu chọn → lệnh cũ vẫn tra ra đúng tên và đúng điểm | URD Journey 8 |

## 10. Screens (tóm tắt — chi tiết ở `ascii-wireframe/`)

| Màn hình | Vai trò | Ghi chú ranh giới |
|----------|---------|-------------------|
| **Trang soạn playbook** | Khai tên, phương pháp, cặp áp dụng, mô tả, danh sách luật; mỗi luật hai thuộc tính | Bề mặt **ngoài phiên**, dùng chuột và bàn phím. **Không** cần dùng được bằng tay cầm |
| **Menu chọn playbook** | Danh sách sách chọn được, điều khiển bằng D-pad + nút áp dụng | Nằm trong **menu an toàn do `order-execution` sở hữu**. Chỉ hiện sách có ≥1 luật và chưa ngừng dùng |
| **Khối điểm trên màn xác nhận** | Tên sách · `n/m` · tên luật không đạt | Feature này **đóng góp nội dung**, `order-execution` **sở hữu màn**. Không thêm bước vào chuỗi xác nhận |
| **Nhãn sách đang dùng trên màn chính** | Cho biết đang chấm theo sách nào | Trên HUD của `order-execution` |
| **Checklist sau lệnh đóng** | Tối đa 3 câu, mỗi câu một thao tác | Không bao giờ đè lên thao tác đang làm; xếp hàng khi nhiều lệnh đóng liên tiếp |
| **Bản ghi điểm của một lệnh** | Sách nào chấm · từng luật ở trạng thái nào | **Bề mặt tự kiểm chứng của cả feature.** Đặt trong màn xem lại một lệnh do `daily-journal` sở hữu; `trade-replay` cũng hiện nó cạnh dòng thời gian |

## 11. Constraints, Dependencies & Assumptions

**Constraints (ràng buộc áp đặt — có source/owner):**

| Ràng buộc | Source / Owner |
|-----------|----------------|
| **Luật playbook không bao giờ chặn được một lệnh**; chỉ hạn mức rủi ro mới chặn được | URD UN-002 · `order-execution` BR-008 |
| **Không mô hình ngôn ngữ nào chấm một lệnh** | URD UN-007 |
| Luật tự động chỉ kiểm được những gì hệ thống quan sát được: giá, đường trung bình, biên độ dao động, chênh lệch giá mua-bán, đồng hồ phiên, số vị thế đang mở, trạng thái quan sát của AI desk. Ngoài danh sách đó phải khai thành luật tự-đánh-giá | URD Mục 7 (A-03) |
| **Một playbook đang dùng tại một thời điểm** | URD Mục 7 (A-02) |
| Soạn playbook cần chuột và bàn phím; chọn playbook làm bằng tay cầm | URD Mục 7 (A-01) |
| Mở menu an toàn **huỷ ARM và khoá mở lệnh mới** | `docs/_shared/operating-environment.md` |
| Chỉ Chrome desktop; giữ cửa sổ focus suốt phiên | `docs/_shared/operating-environment.md` |
| **Điểm số không phải lời khuyên đầu tư** | `docs/_shared/project-profile.md` — Compliance |

**Dependencies (deliverable do bên khác sở hữu):**

| Phụ thuộc | Owner | Blocks nếu chưa sẵn |
|-----------|-------|---------------------|
| Màn xác nhận + chuỗi vũ trang–bắn | `order-execution` (FR-013, FR-014) | FR-029, FR-030, FR-031 |
| Menu an toàn làm chỗ đặt menu chọn sách | `order-execution` (FR-052) | FR-013 |
| Luật huỷ ARM khi mở menu / đổi sách | `order-execution` (FR-018) | FR-017 |
| Bộ đếm tự huỷ và khoảnh khắc nó tăng | `order-execution` (FR-048) | FR-049 |
| Danh sách bối cảnh quan sát được | `order-execution` + `ai-desk` | FR-003 — quyết định luật nào tự-kiểm được, luật nào phải hạ xuống tự-đánh-giá |
| Bề mặt đọc điểm thành xu hướng | `process-score` | SC-01, SC-02 — xem OQ-5 |
| Màn xem lại một lệnh làm chỗ đặt bản ghi điểm | `daily-journal` | FR-044 — cần một khung để đặt lên |

**Assumptions (tin là đúng — nêu hệ quả nếu sai):**

| Giả định | Invalidate {X} nếu sai |
|----------|------------------------|
| Người chơi soạn playbook bằng chuột và bàn phím, ngoài lúc giao dịch (URD A-01) | FR-004 sai; phải thiết kế cả đường soạn luật bằng tay cầm — tốn kém hơn nhiều |
| Một playbook đang dùng tại một thời điểm (URD A-02) | FR-015, BR-011 sai; cách chấm và cách hiện điểm đổi hoàn toàn |
| Danh sách bối cảnh tự-kiểm được là **đóng** (URD A-03) | FR-003 hẹp lại; luật người chơi muốn rơi vào nhóm tự-đánh-giá và mất khả năng hiện trước khi bấm |
| Người chơi chịu trả lời checklist sau khi lệnh đóng (URD A-04) | FR-038..042 thành công sức bỏ đi; nhóm luật tự-đánh-giá vô dụng |
| "Đạt chuẩn" = đạt đủ luật **bắt buộc** (URD A-05 🔶) | FR-046 hiện quá thường xuyên và mất tác dụng — xem OQ-3 |
| Việc chấm đủ nhanh để màn xác nhận mở ngay khi vũ trang (URD A-06) | NFR-001 không đạt; nhịp thao tác đứt, và FR-030 phải đặt lại — xem OQ-2 |
| Người chơi khai luật bằng cách chọn từ danh sách rồi đặt tham số (URD A-07) | FR-001 phải mở rộng sang luật tự do — xem OQ-4 |
| Feature này không tự đo được thành công của chính nó (URD A-08) | SC-01, SC-02 treo cho tới khi `process-score` có — xem OQ-5 |
| Playbook ngừng dùng giữa phiên → lần vũ trang sau về "ngoài kế hoạch" (URD A-09 🔶) | FR-010 phải mô tả hành vi khác — xem OQ-6 |

## 12. Open Questions

> **Số OQ đánh riêng cho từng tài liệu.** `OQ-3` của SRS này không nhất thiết là `OQ-3` của PRD
> cùng feature. Neo ổn định để đối chiếu là **số OQ của URD** ghi trong ngoặc *(kế thừa URD OQ-x)*.

* [ ] **OQ-1** *(kế thừa URD OQ-2)*: SC-01 có **sàn tối thiểu tuyệt đối** không (vd "ít nhất 6/10 lệnh có
  sách"), hay chỉ cần cao hơn baseline?
  🔶 **Tạm quyết:** chỉ cần cao hơn baseline trong ba tháng đầu, **và ghi rõ tỷ lệ tuyệt đối bên cạnh** để
  con số thấp không bị che.
  *Nếu sai:* SC-01 vẫn "đạt" kể cả khi tỷ lệ tuyệt đối rất thấp, và feature trông hiệu quả trong khi không.

* [ ] **OQ-2** *(kế thừa URD A-06)*: Việc chấm có đủ nhanh để FR-030 (màn xác nhận không mở khi chưa có
  điểm) không phá nhịp thao tác không?
  🔶 **Tạm quyết:** giữ FR-030 nguyên vẹn và ràng buộc phép chấm là hàm thuần không gọi ra ngoài
  (NFR-002), coi đó là điều kiện đủ.
  *Nếu sai:* phải chọn giữa hai cái xấu — mở màn xác nhận muộn (đứt nhịp), hoặc mở kèm ô điểm trống (phá
  đúng lý do feature tồn tại). Đo độ trễ ngay phiên đầu.

* [ ] **OQ-3** *(kế thừa URD A-05)*: "Đạt chuẩn" ở FR-046 nghĩa là đạt đủ luật **bắt buộc**, hay đạt **mọi**
  luật? Người chơi đã chốt *nguyên tắc* chỉ-hiện-khi-đạt-chuẩn nhưng chưa chốt *định nghĩa*.
  🔶 **Tạm quyết:** đạt đủ luật **bắt buộc** (FR-025, FR-047).
  *Nếu sai (người chơi hiểu là mọi luật):* FR-046 hiện quá thường xuyên và mất tác dụng cảnh báo.

* [ ] **OQ-4** *(kế thừa URD OQ-6)*: Người chơi tự khai được một **luật kiểu hoàn toàn mới** không, hay chỉ
  chọn từ danh sách luật có sẵn rồi đặt tham số? **Chặn phạm vi FR-001 và FR-006.**
  🔶 **Tạm quyết:** chọn từ danh sách có sẵn rồi đặt tham số — đó là cách duy nhất giữ được NFR-003 (tính
  xác định) và FR-006 (validate tham số).
  *Nếu sai:* phần lớn luật của người chơi rơi vào nhóm tự-đánh-giá và mất khả năng hiện trước khi bấm —
  đúng thứ FR-029 sinh ra để làm.

* [ ] **OQ-5** *(kế thừa URD A-08)*: `process-score` chưa có thì đọc SC-01 và SC-02 bằng cách nào?
  🔶 **Tạm quyết:** đếm tay từ bản ghi lệnh của chính feature này trong ba tháng đầu, **ghi rõ là số đọc thô**.
  *Nếu sai / nếu không làm:* feature chạy ba tháng mà không biết mình có hiệu quả không.

* [ ] **OQ-6** *(kế thừa URD A-09)*: Playbook đang dùng bị **ngừng dùng giữa phiên** → lần vũ trang sau rơi
  về "ngoài kế hoạch", hay giữ nguyên sách đó tới hết phiên? Cả hai hợp lý; em **không tự quyết** vì nó đổi
  thứ người chơi nhìn thấy giữa buổi.

* [ ] **OQ-7** *(kế thừa URD OQ-7)*: Có cần cảnh báo (không chặn) khi một luật bắt buộc **gần như luôn đạt**
  trong lịch sử không? Không có gì nhắc thì thêm luật dễ là cách làm đẹp SC-02 mà chất lượng thật không đổi.
  Đây là lỗ hổng duy nhất SC-02 không tự bịt được.

* [ ] **OQ-8**: Danh sách bối cảnh tự-kiểm được (URD A-03) gồm đúng những gì? **Chặn FR-003** — nó quyết định
  luật nào khai được là tự-kiểm và luật nào buộc phải hạ xuống tự-đánh-giá. Cần chốt cùng `order-execution`
  và `ai-desk`.

---

> **Nguồn:** `playbook-grading-urd.md` (14 nhu cầu, 8 journey, 19 tình huống ngoại lệ, 2 thước đo, 9 giả
> định) · `playbook-grading-prd.md` (14 capability) · bốn tài liệu nền `docs/_shared/` · ranh giới nhận từ
> `order-execution`, `process-score`, `tilt-meter`, `ai-desk`, `daily-journal`, `trade-replay`.
>
> **🔶 Năm quyết định thay user** ở Mục 12 (OQ-1..OQ-5), mỗi cái kèm hệ quả nếu sai. **OQ-6 em cố ý không
> quyết** — nó đổi thứ người chơi nhìn thấy giữa buổi, nên phải là lựa chọn của họ.
>
> **Tầng 2–4 chưa sinh:** `playbook-grading-flows.md`, `-states.md`, `-erd.md`, use case, user story, AC.
