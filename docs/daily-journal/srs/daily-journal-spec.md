---
type: srs
feature: daily-journal
status: draft
updated: 2026-08-29
links:
  - docs/daily-journal/daily-journal-urd.md
  - docs/daily-journal/daily-journal-prd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/srs/order-execution-spec.md
  - docs/voice-journal/srs/voice-journal-spec.md
  - docs/playbook-grading/srs/playbook-grading-spec.md
  - docs/process-score/process-score-urd.md
  - docs/trade-replay/trade-replay-urd.md
---

# daily-journal — Software Requirements Specification

## 1. Scope

Đặc tả **hai đầu của một buổi tối giao dịch**: nghi thức chuẩn bị trước khi mở khoá phiên, và bản ghi trung
thực đọc lại được sau khi đóng phiên — cộng với các bề mặt duyệt lại (một ngày, một tháng, một nhóm lệnh,
một lệnh cụ thể).

**Trong phạm vi:** màn "hôm nay" làm điểm vào và điểm về · năm mục sẵn sàng (chỉ để tự biết) · tự chấm 1–5
đầu/cuối phiên · kế hoạch của ngày và bản chụp bất biến tại lệnh đầu tiên · bốn đồng hồ phiên thị trường ·
máy tính cỡ lệnh (áp chỉ dàn bản xem trước) · bản đồ nhiệt tháng tô theo quy trình · lọc lịch sử nhiều
chiều · mười lệnh gần nhất · chi tiết một lệnh · đính ảnh biểu đồ · triết lý và nguyên tắc cá nhân · hai bất
biến: chữ người chơi không sửa được dữ kiện sàn, và không thao tác nhật ký nào phát ra được lệnh.

**Ngoài phạm vi:** học từ chất lượng thực thi — đối chiếu kế hoạch với thứ đã làm, phân nhóm
có-kế-hoạch/bốc-đồng, thư viện loại lỗi và xu hướng lỗi (**`execution-learning`**, *chưa có URD*) · tính
điểm quy trình và **mọi con số so sánh nhiều phiên, kể cả gộp điểm nhiều phiên trong một buổi tối**
(`process-score`) · hạn mức, khoá/mở khoá phiên (`order-execution`) · ghi âm và chép lời
(`voice-journal`) · tua lại tape (`trade-replay`) · chấm luật playbook (`playbook-grading`) · đo trạng thái
tâm lý (`tilt-meter`) · tư vấn và kế hoạch do AI soạn (`ai-desk`) · báo cáo, xuất dữ liệu, sao lưu, xoá toàn
bộ, màn cài đặt (`reports-export`) · nhiều tài khoản · nhập lịch sử từ sàn khác · bản di động · giao diện
sáng · lấy ảnh biểu đồ tự động.

> **Hai bất biến của tài liệu này:**
> 1. **Chữ người chơi viết không bao giờ sửa được sự thật từ sàn.** Nhận xét thêm vào được; giá khớp, thời
>    điểm và lãi lỗ do sàn tính thì không.
> 2. **Không thao tác nhật ký nào phát ra được một lệnh**, và nhật ký không bao giờ làm chậm đường đặt lệnh.
>
> **Nguyên tắc một-nơi-tính-một-nơi-đọc:** nhật ký **cấp bằng chứng** cho `process-score` và **đọc lại** con
> số deck đã chốt. Nó **không tự tính con số nào** — kể cả việc gộp điểm nhiều phiên trong một buổi tối.

## 2. Actors & Stakeholders

| Actor | Loại | Mục tiêu | Trong scope? |
|-------|------|----------|--------------|
| **Người chơi — trước phiên** | người | Bước vào buổi tối đã biết mình định làm gì | Có |
| **Người chơi — sau phiên** | người | Bước ra với bản ghi mà sáng mai đọc lại vẫn hiểu | Có |
| **Sàn cTrader / Spotware** | ngoài | **Nguồn sự thật** cho dữ kiện khớp lệnh, thời điểm, lãi lỗ | Có — là nguồn bất khả xâm phạm |
| **`order-execution`** | hệ thống | Sở hữu vòng đời phiên, bản xem trước trên HUD, hàm quy đổi và làm tròn khối lượng | **Không** — ranh giới tích hợp |
| **`process-score`** | hệ thống | **Tính** điểm quy trình và mọi con số nhiều phiên; nhật ký chỉ **đọc** | **Không** — chỉ đọc |
| **`voice-journal`** | hệ thống | Đặt nội dung memo và ba thao tác nghe/sửa/xoá lên khung chi tiết một lệnh | **Không** — mượn khung |
| **`playbook-grading`** | hệ thống | Đặt bản ghi điểm lên khung chi tiết một lệnh | **Không** — mượn khung |
| **`trade-replay`** | hệ thống | Nhận đường dẫn từ chi tiết một lệnh sang màn tua lại | **Không** — ranh giới |
| **`execution-learning`** | hệ thống | **Định nghĩa** loại lỗi; nhật ký chỉ hiển thị và lọc theo | **Không** — **chưa có URD** |
| **AI desk** | hệ thống | Đọc **số liệu tổng hợp** của nhật ký | **Không.** Không bao giờ viết, sửa hay xoá một dòng nhật ký nào |

## 3. Functional Requirements (FR)

### 3.1 Màn "hôm nay" và định nghĩa một buổi tối

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-daily-journal-001 | Màn "hôm nay" là **cùng một màn** cho điểm vào và điểm về | Trước phiên là nơi chuẩn bị; sau phiên là nơi đáp xuống. Một màn, hai thời điểm | P0 | demo | URD UN-001, UN-009 |
| FR-daily-journal-002 | Đóng phiên thì **tự đáp xuống** "hôm nay" | Sau khi đóng phiên, màn hình tự đáp xuống "hôm nay" với dữ liệu buổi vừa xong **đã có sẵn** — người chơi không phải tự tìm đường vào | P0 | test | URD UN-009 — xem OQ-2 |
| FR-daily-journal-003 | **Một "ngày" là một buổi tối giao dịch**, không phải một ngày lịch | Phiên bắt đầu tối hôm trước và đóng sau nửa đêm vẫn thuộc **buổi tối đã bắt đầu nó**. Đóng phiên lúc 2 giờ sáng rồi mở "hôm nay" vẫn thấy đúng buổi tối vừa xong, **không phải một ngày trống** | P0 | test | URD Mục 3 — xem OQ-7 |
| FR-daily-journal-004 | Ngày tính theo giờ địa phương của người chơi | Mốc gom một buổi tối dùng giờ địa phương | P0 | kiểm tra | URD Mục 3 |
| FR-daily-journal-005 | Một buổi tối có thể có nhiều phiên | Ngày có nhiều phiên thì mở ngày ra mới tách từng phiên | P0 | demo | URD Mục 3 |

### 3.2 Nghi thức chuẩn bị

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-daily-journal-006 | Năm mục sẵn sàng | Người chơi tự soát năm mục: ngủ/năng lượng · bình tĩnh · tập trung · chấp nhận hạn mức tối nay · đã xem kế hoạch và tin. Mỗi mục có/không kèm ghi chú tuỳ ý | P0 | demo | URD UN-001 |
| FR-daily-journal-007 | Mức sẵn sàng **không bao giờ chặn** | Kết quả **chỉ để tự biết**. Bỏ trống hết vẫn mở khoá phiên và vào lệnh được; **không cảnh báo nào biến thành rào chặn** | P0 | test | URD UN-002 |
| FR-daily-journal-008 | Bỏ trống ghi là **không có dữ liệu**, không quy về 0 | Những chỗ cần dữ liệu đó ghi rõ **không có dữ liệu**, không quy về 0 và không tính như một thiếu sót của người chơi | P0 | test | URD Mục 6 |
| FR-daily-journal-009 | Tự chấm 1–5 đầu và cuối phiên, bằng tay cầm | Hai lần bấm là xong; **bỏ qua được** và bỏ qua **không bị hiểu là điểm kém** | P1 | demo | URD UN-008 |
| FR-daily-journal-010 | Nhật ký là **nguồn thu** bằng chứng, không phải nơi đọc lại | Mục sẵn sàng, tự chấm đầu/cuối buổi, và việc xác nhận kế hoạch trước lệnh đầu tiên đều **do feature này thu và giữ**; `process-score` đọc chúng và **không được mở một luồng thu thứ hai** | P0 | kiểm tra | URD Mục 7 · `process-score` A-04 |

### 3.3 Kế hoạch của ngày và bản chụp

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-daily-journal-011 | Nội dung kế hoạch của tối nay | Người chơi viết: luận điểm · cặp theo dõi · vùng giá quan trọng · **điều gì làm luận điểm sai** · sự kiện rủi ro · nhãn phân loại · ghi chú | P0 | demo | URD UN-004 |
| FR-daily-journal-012 | Nội dung do **người chơi viết**, hệ thống không tự sửa | Hệ thống được phép gợi ý ở nơi khác, nhưng **không bao giờ tự sửa hay tự đè lên chữ của người chơi** | P0 | test | URD Mục 3 |
| FR-daily-journal-013 | Chụp lại kế hoạch **tại thời điểm lệnh đầu tiên** | Bản chụp đó **không sửa được nữa** | P0 | test | URD UN-017 |
| FR-daily-journal-014 | Viết thêm sau lệnh đầu **hiện ra là viết thêm** | Người chơi vẫn viết thêm được, nhưng phần thêm hiển thị **tách bạch kèm thời điểm** — để mai đọc lại phân biệt được điều mình tin **trước** khi vào lệnh với điều mình nghĩ **sau** khi đã biết kết quả | P0 | test | URD UN-017 |
| FR-daily-journal-015 | Không mất chữ khi mất kết nối hoặc đóng nhầm tab | Chữ đã gõ không mất; quay lại viết tiếp từ chỗ dừng | P0 | test | URD Mục 6 |
| FR-daily-journal-016 | Mở hai tab sửa cùng một buổi tối | **Không âm thầm mất chữ** — bản đang mở biết là đã cũ và **nói ra trước khi ghi đè** | P0 | test | URD Mục 6 |
| FR-daily-journal-017 | Đọc kế hoạch AI **cạnh** kế hoạch mình tự viết | Hai bản nằm riêng, **luôn phân biệt được nguồn**; chữ người chơi không bị AI sửa | P2 | demo | URD UN-019 · `ai-desk` FR-032 |
| FR-daily-journal-018 | Đính ảnh biểu đồ đã tự chụp | Đính được vào kế hoạch của ngày hoặc vào một lệnh cụ thể. Ảnh nằm cạnh chữ, mở lại vẫn còn | P1 | demo | URD UN-005 |
| FR-daily-journal-019 | Validate ảnh đính | Ảnh quá lớn hoặc sai định dạng → **báo ngay giới hạn cụ thể và từ chối rõ ràng**; không âm thầm bỏ qua | P1 | test | URD Mục 6 |
| FR-daily-journal-020 | Cảnh báo dung lượng trước khi hết chỗ | Cho biết đang dùng bao nhiêu chỗ **trước khi** hết, không phải lúc đã hỏng | P1 | test | URD Mục 6 · `reports-export` UN-017 |

### 3.4 Bốn đồng hồ phiên thị trường

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-daily-journal-021 | Bốn đồng hồ phiên | Sydney · Tokyo · London · New York, chạy theo **giờ thật của từng nơi** | P1 | demo | URD UN-003 |
| FR-daily-journal-022 | Mỗi thành phố đổi giờ theo lịch **của chính nó** | London, New York và Sydney đều có mốc đổi riêng và **không cùng ngày**; chỉ **Tokyo không bao giờ đổi** | P1 | test | URD UN-003 |
| FR-daily-journal-023 | Đúng cả trong cửa sổ lệch mùa | Trong cửa sổ 2–3 tuần mà châu Âu đã đổi còn Mỹ thì chưa, khoảng cách London–New York **khác thường lệ** và bốn đồng hồ vẫn phải đọc đúng | P1 | test | URD Mục 6 |

### 3.5 Máy tính cỡ lệnh

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-daily-journal-024 | Đầu vào máy tính cỡ lệnh | Vốn · mức rủi ro (bằng tiền hoặc phần trăm) · cặp · giá vào · giá dừng lỗ | P1 | demo | URD UN-006 |
| FR-daily-journal-025 | Hiện **cả số yêu cầu và số đã làm tròn** | Thấy cả số yêu cầu lẫn số đã làm tròn **theo bước nhảy của sàn**, kèm **rủi ro thật bằng tiền** và **hạn mức đang áp** | P1 | demo | URD UN-006 |
| FR-daily-journal-026 | Nêu rõ số vốn lấy từ đâu, vào lúc nào | Hiện rõ **số vốn đang dùng và lấy lúc nào**; lệch nhiều so với tài khoản thật thì **nói ra trước khi cho áp** | P1 | test | URD Mục 6 |
| FR-daily-journal-027 | Áp giá trị **chỉ dàn bản xem trước** | Áp xong **chỉ có bản xem trước trên màn chính thay đổi**; vẫn cần `LT+RT` mới có lệnh | P1 | test | URD UN-007 |
| FR-daily-journal-028 | Giá dừng lỗ trùng hoặc sai phía | **Không hiện cỡ lệnh**; nói rõ vì sao và **không cho áp** sang màn chính | P1 | test | URD Mục 6 |
| FR-daily-journal-029 | Không quy đổi được sang tiền tài khoản | Mất kết nối, thị trường đóng, hoặc cặp không định giá bằng USD → nói thẳng **"chưa tính được"** kèm lý do. **Không bao giờ hiện một con số ước lượng** | P1 | test | URD Mục 6 |
| FR-daily-journal-030 | Giá chạy xa sau khi áp | Bản xem trước nói rõ nó tính ở **mức giá nào, lúc nào**; giá chạy quá xa thì **nói ra trước khi người chơi bắn** | P1 | test | URD Mục 6 |

### 3.6 Quy trình đứng trước tiền

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-daily-journal-031 | Màn mặc định nói về quy trình | Mọi lối vào nhật ký mở ra ở trạng thái nói về quy trình | P0 | demo | URD UN-010 |
| FR-daily-journal-032 | Tiền nằm sau **một lần bấm có chủ ý** | Lãi lỗ bằng tiền chỉ hiện sau một thao tác bật có chủ ý — ở **mọi** lối vào, không có ngoại lệ | P0 | kiểm tra | URD UN-010 |

### 3.7 Bản đồ nhiệt và duyệt lại

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-daily-journal-033 | Bản đồ nhiệt tháng, **mỗi ô là một buổi tối** | Nhìn một tháng trong một hình, **mặc định tô theo quy trình**, không tô theo tiền | P1 | demo | URD UN-011 |
| FR-daily-journal-034 | Ngày **chủ động đứng ngoài** đọc ra là một quyết định | Trạng thái **hợp lệ** — không phải điểm 0, không phải thiếu dữ liệu | P1 | test | URD Mục 6 — xem OQ-1 |
| FR-daily-journal-035 | Ngày **thị trường đóng** phân biệt với ngày đứng ngoài | Hiện là thị trường đóng, **không phải một lựa chọn của người chơi**, và **không nằm trong mẫu số của bất kỳ tỉ lệ nào** | P1 | test | URD Mục 6 — xem OQ-1 |
| FR-daily-journal-036 | Buổi có nhiều phiên: chỉ hiển thị con số deck cung cấp | Ô nói rõ buổi đó có mấy phiên và **chỉ hiển thị con số do `process-score` cung cấp cho cả buổi**. Nhật ký **không tự gộp điểm nhiều phiên**. Chưa có con số cấp buổi thì ô **hiện từng phiên** thay vì bịa một điểm trung bình | P1 | test | URD Mục 6 · D-02 — xem OQ-3 |
| FR-daily-journal-037 | Chưa đủ phiên để nói được điều gì có nghĩa | Nói thẳng **"chưa đủ dữ liệu"** kèm số phiên hiện có, thay vì in một con số tự tin | P1 | test | URD Mục 6 |
| FR-daily-journal-038 | Mở một ngày từ bản đồ nhiệt | Ngày mở ra thấy: số phiên · số lệnh · mức sẵn sàng · điểm quy trình đã chốt · tự chấm · kế hoạch đã viết · các lỗi đã gắn · các lệnh của ngày đó | P1 | demo | URD UN-011, Journey 4 |
| FR-daily-journal-039 | Ngày không giao dịch vẫn mở được | Mở ra và **đọc ra là không giao dịch**, không phải một đêm điểm thấp | P1 | test | URD Journey 4 |
| FR-daily-journal-040 | Mười lệnh gần nhất hiện sẵn | Mỗi lệnh đủ để nhận ra nó và **mở thẳng vào chi tiết** | P1 | demo | URD UN-018 |
| FR-daily-journal-041 | Lọc lịch sử nhiều chiều cùng lúc | Kỳ (tuần/tháng/khoảng tự chọn) · playbook · cặp · khung thời gian · mua/bán · phiên thị trường · phân loại kế hoạch · **loại lỗi** · thắng/thua/hoà | P1 | demo | URD UN-012 |
| FR-daily-journal-042 | Mọi lệnh trả về thoả **tất cả** điều kiện | Không lẫn lệnh ngoài điều kiện đã chọn; đổi một điều kiện thì danh sách đổi theo đúng hướng dự đoán | P1 | test | URD Journey 5 |
| FR-daily-journal-043 | Chiều "loại lỗi" phụ thuộc `execution-learning` | Nhật ký **hiển thị và lọc** theo lỗi đã được gắn, nhưng **không định nghĩa, không tự suy ra, không chấm**. Chưa có nguồn thì chiều đó ghi **"không có dữ liệu"** và các chiều khác vẫn chạy | P1 | test | URD Mục 3 — xem OQ-4 |

### 3.8 Chi tiết một lệnh

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-daily-journal-044 | Đủ bối cảnh ở **một chỗ** | Một màn có: **kế hoạch bất biến lúc vào** · dữ kiện khớp và đóng từ sàn · các lần sửa SL/TP · kết quả chấm luật · memo · ảnh đính · lỗi đã gắn · **đường dẫn sang bản tua lại** | P0 | demo | URD UN-013 |
| FR-daily-journal-045 | Trả lời được ba câu mà không rời màn | Không rời màn này vẫn trả lời được: **lúc đó định làm gì · đã làm gì · sàn ghi nhận gì** | P0 | demo | URD Journey 6 |
| FR-daily-journal-046 | Là **khung** cho nội dung của feature khác | Màn này cho `voice-journal` mượn chỗ đặt ba thao tác nghe/sửa/xoá memo, `playbook-grading` đặt bản ghi điểm, `execution-learning` đặt lỗi đã gắn | P0 | kiểm tra | `voice-journal` A-07 |
| FR-daily-journal-047 | Lệnh không có bản tua lại | Chi tiết lệnh **vẫn mở đủ mọi phần khác**; phần tua lại **nói rõ không có** | P0 | test | URD Mục 6 |
| FR-daily-journal-048 | Ngày cũ có trước khi một tính năng tồn tại | Cột đó ghi **"không có dữ liệu"**, **không suy đoán ngược** và không tính như một thiếu sót của người chơi | P0 | test | URD Mục 6 |

### 3.9 Hai bất biến

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-daily-journal-049 | Chữ người chơi **không sửa được dữ kiện từ sàn** | Nhận xét thêm vào được, nhưng **giá khớp, thời điểm và lãi lỗ do sàn tính không bao giờ đổi theo** | P0 | test | URD UN-014 |
| FR-daily-journal-050 | Người chơi muốn sửa một dữ kiện từ sàn | **Không sửa được**, và **nói rõ vì sao**: nhận xét thêm vào được, dữ kiện thì không | P0 | test | URD Mục 6 |
| FR-daily-journal-051 | Sự kiện từ sàn về muộn sau khi đã đóng phiên | Ngày **tự cập nhật** khi dữ kiện về; người chơi **không phải sửa tay và không được phép sửa** dữ kiện đó | P0 | test | URD Mục 6 |
| FR-daily-journal-052 | Không thao tác nhật ký nào phát ra được lệnh | Nhật ký chạy trên **đường riêng, chậm nhất**, tách khỏi đường đặt lệnh | P0 | test | URD UN-015 · `system-overview.md` |
| FR-daily-journal-053 | Mở nhật ký giữa phiên | Huỷ ARM và khoá **mở lệnh mới**, **nói rõ ngay lúc mở**. **Đóng vị thế và thoát khẩn cấp vẫn luôn được phép.** Đóng nhật ký lại thì mọi thứ trở về bình thường, **không có gì bị khoá kéo dài** | P0 | test | URD Mục 6 · `order-execution` FR-029, FR-052 |
| FR-daily-journal-054 | AI desk chỉ **đọc số liệu tổng hợp** | AI desk **không bao giờ viết, sửa hay xoá** một dòng nhật ký nào | P0 | test | URD Mục 2 |

### 3.10 Triết lý và nguyên tắc

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-daily-journal-055 | Viết triết lý giao dịch và nguyên tắc cốt lõi | Có một chỗ cố định để đọc lại **trước những đêm khó**, sửa được khi suy nghĩ thay đổi | P2 | demo | URD UN-016 · D-01 |
| FR-daily-journal-056 | Nguyên tắc bất khả xâm phạm với AI | Chữ nguyên tắc giữ **nguyên văn từng ký tự** qua một phiên đầy đủ; **AI desk không sửa được** | P2 | test | URD Journey 7 |

### 3.11 Thiết bị và ràng buộc thao tác

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-daily-journal-057 | Ngoài phiên dùng chuột và bàn phím bình thường | Viết kế hoạch, ghi chú, đính ảnh, lọc lịch sử đều là việc làm khi **không đang giao dịch** | P0 | kiểm tra | URD Mục 7 |
| FR-daily-journal-058 | Trong phiên chỉ tay cầm, và phải ngắn | Hiện chưa có thao tác nhật ký nào bắt buộc phải làm giữa phiên — tự chấm diễn ra **trước khi mở khoá** và **sau khi đóng phiên**. Nếu về sau có thao tác giữa phiên thì nó **phải làm được bằng tay cầm và phải ngắn** | P0 | kiểm tra | URD Mục 7 — xem OQ-6 |
| FR-daily-journal-059 | Tài khoản là nhãn chỉ đọc | Nhật ký hiển thị tài khoản đang xem như một **nhãn chỉ đọc**, không phải một bộ chọn | P0 | kiểm tra | URD Mục 7 |

## 4. Non-Functional Requirements (NFR)

| ID | Category | Requirement | Priority | Acceptance |
|----|----------|-------------|----------|------------|
| NFR-daily-journal-001 | performance | Khi nhật ký **đang mở**, độ trễ từ lúc bấm tới lúc sàn xác nhận vẫn nằm trong ngân sách ở `system-overview.md` | P0 | Đo độ trễ đặt lệnh trong **hai điều kiện** — nhật ký đóng và nhật ký đang mở — mỗi lần thêm màn nhật ký mới |
| NFR-daily-journal-002 | performance | Nhật ký chạy trên **journal path** — đường chậm nhất, **không bao giờ đi trên order socket** | P0 | phân tích | `system-overview.md` |
| NFR-daily-journal-003 | reliability | Feature này chết hoàn toàn **không** làm giảm khả năng mở, đóng, thoát vị thế | P0 | Diễn tập: tắt hẳn nhật ký rồi chạy trọn chuỗi mở phiên → vào lệnh → đóng lệnh |
| NFR-daily-journal-004 | data integrity | **Dữ kiện từ sàn là bất biến** trong mọi đường ghi của feature này. Không tồn tại thao tác nào sửa được giá khớp, thời điểm, hoặc lãi lỗ do sàn tính | P0 | test — thử mọi đường ghi, kiểm dữ kiện sàn không đổi |
| NFR-daily-journal-005 | data integrity | Bản chụp kế hoạch tại lệnh đầu tiên **bất biến sau thời điểm chụp** | P0 | test — sửa kế hoạch sau lệnh đầu, mở lại: bản chụp y nguyên |
| NFR-daily-journal-006 | data integrity | Nhật ký **không bao giờ tự xoá thứ gì**. Chữ, ảnh và bản ghi giữ **vô hạn** | P0 | kiểm tra — **không tồn tại cơ chế tự xoá nào trong sản phẩm** (mục *hạn giữ nhật ký* đã bỏ 2026-08-29) |
| NFR-daily-journal-007 | correctness | Bốn đồng hồ dùng lịch đổi giờ **riêng của từng thành phố**, không suy ra từ một mốc chung | P0 | test — dựng dữ liệu tại từng mốc đổi giờ của London, New York, Sydney |
| NFR-daily-journal-008 | usability | Nghi thức chuẩn bị làm xong trong **vài phút**, không phải một biểu mẫu dài | P0 | demo |
| NFR-daily-journal-009 | usability | **Không con số tiền nào** ở trạng thái mặc định của bất kỳ màn nào thuộc feature này | P0 | kiểm tra — rà từng lối vào sau mỗi lần đổi giao diện |
| NFR-daily-journal-010 | privacy | Nội dung nhật ký là **dữ liệu cá nhân** — chữ viết, ảnh, và memo giọng nói. Người chơi phải biết nó nằm ở đâu và xoá bằng cách nào | P0 | kiểm tra | Project profile — Compliance |
| NFR-daily-journal-011 | compatibility | Chỉ Chrome desktop, **giao diện tối**, một tài khoản demo duy nhất. Không bản di động, không giao diện sáng | P0 | kiểm tra |
| NFR-daily-journal-012 | compliance | Mọi bề mặt giữ dòng chữ demo / giải trí / không phải lời khuyên đầu tư | P0 | kiểm tra |
| NFR-daily-journal-013 | usability | Giao diện tiếng Anh; tài liệu nghiệp vụ tiếng Việt | P0 | kiểm tra |

## 5. Business Rules

| ID | Rule | Trigger | Implements FR | Source |
|----|------|---------|---------------|--------|
| BR-daily-journal-001 | **Chữ người chơi không bao giờ sửa được dữ kiện từ sàn.** Nhận xét thêm vào được; giá khớp, thời điểm, lãi lỗ thì không | Mọi đường ghi | FR-049, FR-050, FR-051 · NFR-004 | URD UN-014 |
| BR-daily-journal-002 | **Không thao tác nhật ký nào phát ra được lệnh.** Mở nhật ký huỷ ARM và khoá mở lệnh mới; **đóng vị thế và thoát khẩn cấp vẫn luôn được phép** | Mở nhật ký giữa phiên | FR-052, FR-053 | URD UN-015 · `order-execution` FR-029 |
| BR-daily-journal-003 | **Mức sẵn sàng chỉ để tự biết, không bao giờ chặn** mở khoá phiên hay một lệnh | Soát hoặc bỏ trống mục sẵn sàng | FR-007 | URD UN-002 |
| BR-daily-journal-004 | **Một "ngày" là một buổi tối giao dịch**, không phải ngày lịch. Phiên vắt qua nửa đêm thuộc buổi tối **đã bắt đầu nó** | Gom dữ liệu theo ngày | FR-003, FR-004 | URD Mục 3 |
| BR-daily-journal-005 | Kế hoạch **chụp bất biến tại lệnh đầu tiên**; phần viết thêm sau đó hiển thị tách bạch kèm thời điểm | Lệnh đầu tiên khớp | FR-013, FR-014 · NFR-005 | URD UN-017 |
| BR-daily-journal-006 | **Một nơi tính, một nơi đọc.** Nhật ký đọc con số `process-score` đã chốt và **không tự tính con số nào — kể cả gộp điểm nhiều phiên trong một buổi** | Tô bản đồ nhiệt · mở một ngày | FR-036 | URD D-02 |
| BR-daily-journal-007 | Nhật ký là **nguồn thu** bằng chứng cho deck; `process-score` **không được mở luồng thu thứ hai** | Thu mục sẵn sàng · tự chấm · xác nhận kế hoạch | FR-010 | URD Mục 7 · `process-score` A-04 |
| BR-daily-journal-008 | **Ngày không giao dịch là dữ liệu hợp lệ**, không phải dữ liệu thiếu — và phân biệt được với ngày thị trường đóng | Tô bản đồ nhiệt · tính tỉ lệ | FR-034, FR-035, FR-039 | URD A-03 |
| BR-daily-journal-009 | Ngày **thị trường đóng không nằm trong mẫu số** của bất kỳ tỉ lệ nào | Tính mọi tỉ lệ theo ngày | FR-035 | URD Mục 6 |
| BR-daily-journal-010 | Thiếu dữ liệu ghi là **"không có dữ liệu"**, **không quy về 0** và không suy đoán ngược | Mục bỏ trống · ngày cũ trước khi tính năng tồn tại | FR-008, FR-048 | URD Mục 6 |
| BR-daily-journal-011 | **Quy trình đứng trước tiền ở mọi lối vào**; tiền sau một lần bấm có chủ ý | Mở bất kỳ màn nhật ký nào | FR-031, FR-032 · NFR-009 | URD UN-010 |
| BR-daily-journal-012 | **Áp cỡ lệnh chỉ dàn bản xem trước**; vẫn cần `LT+RT` mới có lệnh | Áp giá trị sang màn chính | FR-027 | URD UN-007 |
| BR-daily-journal-013 | Không quy đổi được thì **nói "chưa tính được"**, **không bao giờ hiện một con số ước lượng** | Mất kết nối · thị trường đóng · cặp không định giá bằng USD | FR-029 | URD Mục 6 |
| BR-daily-journal-014 | Nhật ký **không bao giờ tự xoá thứ gì**; đổi lại phải cảnh báo dung lượng **trước khi** hết chỗ | Luôn luôn | FR-020 · NFR-006 | URD Mục 7 — xem OQ-5 |
| BR-daily-journal-015 | Nhật ký **hiển thị và lọc** theo lỗi đã gắn, nhưng **không định nghĩa, không tự suy ra, không chấm** | Lọc theo loại lỗi | FR-043 | URD Mục 3 |

## 6. Error Matrix

| Error ID | Title | Trigger | Severity | Related FR | Screen state | Recovery |
|----------|-------|---------|----------|------------|--------------|----------|
| E-daily-journal-001 | **Một tối chủ động đứng ngoài** | Người chơi quyết định không giao dịch | **critical** | FR-034 | Đọc ra là một **quyết định** — trạng thái hợp lệ, không phải điểm 0, không phải thiếu dữ liệu | Đọc nhầm thành "đêm tệ" là **phá đúng nguyên tắc lớn nhất của sản phẩm** — xem OQ-1 |
| E-daily-journal-002 | Ngày thị trường đóng | Cuối tuần, ngày lễ | major | FR-035 | Hiện là **thị trường đóng**, không phải một lựa chọn của người chơi | **Không nằm trong mẫu số** của bất kỳ tỉ lệ nào |
| E-daily-journal-003 | Bỏ trống toàn bộ mục sẵn sàng và tự chấm | Người chơi bỏ qua nghi thức | minor | FR-007, FR-008 | Vào phiên **bình thường**; chỗ cần dữ liệu ghi **"không có dữ liệu"** | Không quy về 0, không tính là thiếu sót |
| E-daily-journal-004 | Chưa đủ phiên để nói được điều gì có nghĩa | Tháng đầu | minor | FR-037 | Nói thẳng **"chưa đủ dữ liệu"** kèm số phiên hiện có | **Không in một con số tự tin** từ mẫu quá nhỏ |
| E-daily-journal-005 | Buổi tối còn lệnh mở lúc đóng phiên | Vị thế qua đêm | minor | FR-036 | Buổi đã đóng phiên **luôn có điểm quy trình ngay**; chỉ phần kết quả bằng tiền còn cập nhật sau | **Không** có trạng thái "đang chờ chốt", **không** có số tạm |
| E-daily-journal-006 | Một lệnh không có bản tua lại | Tape thiếu hoặc quá hạn giữ | minor | FR-047 | Chi tiết lệnh vẫn mở đủ mọi phần khác; phần tua lại **nói rõ không có** | Không màn hỏng, không lỗi |
| E-daily-journal-007 | Ảnh đính quá lớn hoặc sai định dạng | Người chơi đính ảnh không hợp lệ | minor | FR-019 | Báo ngay **giới hạn cụ thể** và từ chối rõ ràng | **Không âm thầm bỏ qua** — đính xong tưởng đã lưu, hôm sau mất |
| E-daily-journal-008 | Ảnh tích tụ làm đầy chỗ lưu | Nhiều tháng đính ảnh | major | FR-020 | Cho biết đang dùng bao nhiêu chỗ **trước khi** hết | Không phải lúc đã hỏng |
| E-daily-journal-009 | Mất kết nối hoặc đóng nhầm tab khi đang viết kế hoạch | Sự cố giữa lúc gõ | major | FR-015 | Chữ đã gõ **không mất** | Quay lại viết tiếp từ chỗ dừng |
| E-daily-journal-010 | Mở hai tab và sửa cùng một buổi tối | Hai cửa sổ cùng mở | major | FR-016 | Bản đang mở **biết là đã cũ và nói ra trước khi ghi đè** | **Không âm thầm mất chữ** |
| E-daily-journal-011 | **Đêm rơi đúng mốc đổi giờ mùa** | Tuần đổi giờ của London/NY/Sydney | major | FR-022, FR-023 | Mỗi thành phố đổi theo lịch của **chính nó**; bốn đồng hồ vẫn đọc đúng | Ngồi vào bàn lệch một tiếng là hệ quả; **mỗi mốc là một cơ hội kiểm chứng không lặp lại** |
| E-daily-journal-012 | Sự kiện từ sàn về muộn sau khi đã đóng phiên | Dữ kiện chậm | major | FR-051 | Ngày **tự cập nhật** khi dữ kiện về | Người chơi **không phải sửa tay và không được phép sửa** |
| E-daily-journal-013 | **Mở nhật ký giữa phiên khi đang có vị thế** | Bấm mở từ menu an toàn | major | FR-053 | Huỷ ARM và khoá **mở lệnh mới**, nói rõ ngay lúc mở. **Đóng vị thế và thoát khẩn cấp vẫn luôn được phép** | Đóng nhật ký lại → mọi thứ trở về bình thường, **không có gì bị khoá kéo dài** |
| E-daily-journal-014 | Ngày cũ có trước khi một tính năng tồn tại | Chưa có playbook, chưa có memo | minor | FR-048 | Cột đó ghi **"không có dữ liệu"** | **Không suy đoán ngược**, không tính như một thiếu sót của người chơi |
| E-daily-journal-015 | Sửa kế hoạch sau khi đã biết kết quả | Viết thêm sau lệnh đầu | major | FR-013, FR-014 | Bản chụp trước lệnh đầu **không đổi**; phần viết thêm hiển thị **tách bạch kèm thời điểm** | Nếu không, sáng mai người chơi tin nhầm là mình đã nghĩ thế từ đầu |
| E-daily-journal-016 | Giá dừng lỗ trùng hoặc sai phía so với giá vào | Nhập sai vào máy tính cỡ lệnh | minor | FR-028 | **Không hiện cỡ lệnh**; nói rõ vì sao và **không cho áp** | Con số vô nghĩa nhưng trông vẫn như một con số — nguy hiểm hơn không có |
| E-daily-journal-017 | Không quy đổi được sang tiền tài khoản | Mất kết nối · thị trường đóng · cặp không định giá bằng USD | major | FR-029 | Nói thẳng **"chưa tính được"** kèm lý do | **Không bao giờ hiện một con số ước lượng** |
| E-daily-journal-018 | Số vốn đang dùng đã cũ so với tài khoản thật | Vốn thay đổi sau lần lấy gần nhất | major | FR-026 | Hiện rõ **số vốn đang dùng và lấy lúc nào**; lệch nhiều thì **nói ra trước khi cho áp** | Rủi ro thật lệch khỏi rủi ro đã định — đúng thứ máy tính này sinh ra để chống |
| E-daily-journal-019 | Áp cỡ lệnh xong nhưng chưa bắn, giá đã chạy xa | Chờ lâu giữa áp và bắn | minor | FR-030 | Bản xem trước nói rõ nó tính ở mức giá nào, lúc nào; chạy quá xa thì **nói ra trước khi bắn** | — |
| E-daily-journal-020 | Người chơi muốn sửa một dữ kiện từ sàn | Kỳ vọng sai về quyền của mình | minor | FR-050 | **Không sửa được**, và **nói rõ vì sao** | Nhận xét thêm vào được, dữ kiện thì không |
| E-daily-journal-021 | Buổi tối có hai phiên trở lên | Nhiều phiên một ngày | major | FR-036 | Ô nói rõ buổi đó có mấy phiên; chỉ hiển thị con số **do `process-score` cung cấp cho cả buổi** | Chưa có con số cấp buổi → ô **hiện từng phiên**, **không bịa một điểm trung bình**. Xem OQ-3 |
| E-daily-journal-022 | Phiên bắt đầu tối hôm trước, đóng sau nửa đêm | Buổi vắt qua nửa đêm | major | FR-003 | Cả phiên thuộc **buổi tối đã bắt đầu nó**; "hôm nay" sau khi đóng phiên **luôn là buổi tối vừa xong** | Không phải một ngày trống |
| E-daily-journal-023 | Chưa có nguồn định nghĩa loại lỗi | `execution-learning` chưa tồn tại | minor | FR-043 | Chiều "loại lỗi" ghi **"không có dữ liệu"**; các chiều lọc khác vẫn chạy | Xem OQ-4 |

## 7. Success Criteria

| ID | Outcome nghiệp vụ | Đo bằng | Mốc đạt |
|----|-------------------|---------|---------|
| SC-daily-journal-01 | Buổi tối bắt đầu có chuẩn bị thay vì bắt đầu giữa chừng | Đếm số phiên có bản ghi chuẩn bị gắn với nó, trên tổng số phiên | **≥ 80%** số phiên trong tháng |
| SC-daily-journal-02 | Một quyết định cũ dựng lại được, không phải đoán | Đếm số lệnh mở ra thấy đủ **kế hoạch lúc vào + dữ kiện sàn + ít nhất một dấu vết lý do**. **Nguồn chưa tồn tại hoặc đang tắt thì loại khỏi mẫu số và ghi rõ đang đo trên mấy nguồn** | **≥ 90%** số lệnh trong tháng |
| SC-daily-journal-03 | *(ranh giới)* Quy trình đứng trước tiền ở mọi lối vào | Rà lại **từng lối vào** nhật ký sau mỗi lần đổi giao diện | **100%** màn mặc định không hiển thị con số tiền nào trước một lần bấm có chủ ý |
| SC-daily-journal-04 | *(ranh giới)* Nhật ký không bao giờ chạm được vào đường đặt lệnh | Đo độ trễ đặt lệnh trong **hai điều kiện** — nhật ký đóng và nhật ký đang mở; ghi nhận sự cố phát lệnh khi xảy ra | **0** trường hợp thao tác nhật ký phát ra lệnh hoặc sửa lệnh; độ trễ vẫn trong ngân sách `system-overview.md` |
| SC-daily-journal-05 | Trả lời được "tháng qua đêm nào tôi giữ được quy trình" mà không phải lục | Người chơi tự trả lời có/không một lần mỗi tháng khi nhìn lại tháng vừa xong | Chỉ ra được đêm đó **ngay từ bản đồ nhiệt**, không phải mở từng ngày để dò |
| SC-daily-journal-06 | Giờ phiên thị trường không bao giờ lệch | Đối chiếu bốn đồng hồ với giờ thật **ngay sau mỗi mốc đổi giờ** | **0** lần đọc sai, kể cả trong cửa sổ châu Âu đã đổi mà Mỹ thì chưa |

> **SC-02 cố ý loại nguồn chưa tồn tại khỏi mẫu số.** Ba tháng đầu, `voice-journal` và `playbook-grading` có
> thể chưa chạy — tính chúng vào mẫu số thì con số đo **thứ tự phát hành**, không đo thói quen người chơi.
> Cùng nguyên tắc với `process-score` UN-015.
>
> **SC-06 chỉ đo được khoảng 6 lần một năm**, và mỗi mốc đổi giờ là **một cơ hội không lặp lại** — bỏ lỡ một
> mốc là mất một phép kiểm chứng cho tới lần sau.
>
> **SC-01 tới SC-05 đọc từ dữ liệu của chính feature này**, đo được ngay khi feature chạy.

## 8. Data Entities (tóm tắt — chi tiết ở `daily-journal-erd.md`)

| Entity | Ý nghĩa nghiệp vụ | Thông tin nghiệp vụ cần lưu |
|--------|-------------------|------------------------------|
| **Buổi tối** | Một ngày trong nhật ký — **không phải một ngày lịch** | Ngày (giờ địa phương) · các phiên thuộc buổi này · trạng thái: có giao dịch / chủ động đứng ngoài / **thị trường đóng** |
| **Bản ghi chuẩn bị** | Nghi thức trước phiên | Thuộc buổi tối nào · năm mục sẵn sàng (có/không + ghi chú) · thời điểm ghi |
| **Tự chấm** | Trạng thái người chơi tự khai | Thuộc phiên nào · **đầu phiên hay cuối phiên** · giá trị 1–5 · **hoặc đã bỏ qua** |
| **Kế hoạch của ngày** | Luận điểm người chơi viết trước phiên | Thuộc buổi tối nào · luận điểm · cặp theo dõi · vùng giá quan trọng · **điều gì làm luận điểm sai** · sự kiện rủi ro · nhãn phân loại · ghi chú |
| **Bản chụp kế hoạch** | Bản đóng băng tại lệnh đầu tiên | Thuộc kế hoạch nào · nội dung tại thời điểm chụp · **thời điểm chụp**. **Bất biến** |
| **Phần viết thêm** | Chữ viết sau lệnh đầu tiên | Thuộc kế hoạch nào · nội dung · **thời điểm viết** — luôn hiển thị tách bạch với bản chụp |
| **Ảnh đính** | Ảnh biểu đồ người chơi tự chụp | Đính vào kế hoạch của ngày hay một lệnh · kích thước · định dạng · thời điểm đính |
| **Triết lý và nguyên tắc** | Cách chơi người chơi tự khai, ngoài phiên | Nội dung **nguyên văn** · thời điểm sửa gần nhất. **AI desk không sửa được** |
| **Kết quả tính cỡ lệnh** | Một lần dùng máy tính cỡ lệnh | Vốn đang dùng + **thời điểm lấy vốn** · mức rủi ro · cặp · giá vào · giá dừng · **số yêu cầu** · **số đã làm tròn** · rủi ro thật bằng tiền · hạn mức đang áp · **giá tại thời điểm tính** |

> **Không có entity nào lưu điểm quy trình, con số tổng hợp nhiều phiên, hay định nghĩa loại lỗi** — đó là
> ranh giới (BR-006, BR-015), không phải một thiếu sót. Nhật ký **đọc** chúng từ `process-score` và
> `execution-learning`.
>
> **Dữ kiện khớp lệnh từ sàn cũng không phải entity của feature này** — nó thuộc `order-execution` và là
> **bất biến** ở đây (BR-001).

## 9. Flows (tóm tắt — chi tiết ở `daily-journal-flows.md`)

| Flow | Tóm tắt | Nguồn |
|------|---------|-------|
| Mở đầu một buổi tối | Mở "hôm nay" (bốn đồng hồ đang chạy) → soát năm mục sẵn sàng → tự chấm đầu phiên → viết luận điểm, đính ảnh, đọc kế hoạch AI → sang màn chính mở khoá phiên. **Mở khoá thành công kể cả khi bỏ trống hết** | URD Journey 1 |
| Tính cỡ lệnh rồi vẫn phải xác nhận hai tay | Nhập vốn/rủi ro/cặp/giá → đọc số yêu cầu, số sàn nhận, rủi ro thật, hạn mức → áp sang màn chính → vũ trang → `LT+RT`. **Giữa bước áp và bước bắn, bên sàn không thấy gì** | URD Journey 2 |
| Đóng phiên và đọc lại buổi tối | Đóng phiên → màn hình **tự đáp xuống** "hôm nay" → tự chấm cuối phiên → đọc lại buổi tối → muốn xem tiền thì bấm thêm một lần có chủ ý | URD Journey 3 |
| Nhìn lại một tháng | Mở nhật ký, chọn kỳ theo tháng → đọc bản đồ nhiệt tô theo quy trình → chọn một ngày đáng chú ý → ngày mở ra đủ nội dung | URD Journey 4 |
| Truy một câu hỏi qua lịch sử | Mở lịch sử → đặt nhiều điều kiện cùng lúc → đọc danh sách trả về → mở một lệnh xem chi tiết | URD Journey 5 |
| Mở lại một lệnh cũ để hiểu vì sao | Mở lệnh từ danh sách gần nhất hoặc lịch sử → đọc kế hoạch lúc vào và dữ kiện sàn **cạnh nhau** → xem sửa bảo vệ, điểm luật, memo, ảnh → sang bản tua lại nếu muốn | URD Journey 6 |
| Ghi lại triết lý và nguyên tắc | Mở phần triết lý → viết hoặc sửa một nguyên tắc → lưu. Chạy một phiên đầy đủ rồi mở lại: **nguyên văn từng ký tự** | URD Journey 7 |

## 10. Screens (tóm tắt — chi tiết ở `ascii-wireframe/`)

| Màn hình | Vai trò | Ghi chú ranh giới |
|----------|---------|-------------------|
| **"Hôm nay"** | Điểm vào trước phiên **và** điểm về sau phiên: bốn đồng hồ · năm mục sẵn sàng · tự chấm · kế hoạch của ngày | Sau khi đóng phiên **tự đáp xuống đây**. Mở đầu bằng quy trình, tiền sau một lần bấm |
| **Bản đồ nhiệt tháng** | Mỗi ô một buổi tối, **mặc định tô theo quy trình** | Chỉ hiển thị con số `process-score` cung cấp; **không tự gộp**. Ngày đứng ngoài và ngày thị trường đóng phải đọc khác nhau |
| **Chi tiết một ngày** | Số phiên · số lệnh · mức sẵn sàng · điểm quy trình đã chốt · tự chấm · kế hoạch · lỗi đã gắn · các lệnh | Ngày không giao dịch **vẫn mở được** và đọc ra là không giao dịch |
| **Lịch sử lệnh** | Mười lệnh gần nhất + bộ lọc nhiều chiều | Chiều "loại lỗi" phụ thuộc `execution-learning` |
| **Chi tiết một lệnh** | Kế hoạch bất biến · dữ kiện sàn · sửa SL/TP · điểm luật · memo · ảnh · lỗi · link tua lại | **Là khung cho ba feature khác mượn chỗ** (`voice-journal`, `playbook-grading`, `execution-learning`). Trả lời được ba câu mà không rời màn |
| **Máy tính cỡ lệnh** | Vốn · rủi ro · cặp · giá vào/dừng → số yêu cầu + số làm tròn + rủi ro thật + hạn mức | **Áp chỉ dàn bản xem trước** trên HUD của `order-execution`; vẫn cần `LT+RT` |
| **Triết lý và nguyên tắc** | Chỗ cố định đọc lại trước những đêm khó | Bề mặt ngoài phiên. **AI desk không sửa được** |

## 11. Constraints, Dependencies & Assumptions

**Constraints (ràng buộc áp đặt — có source/owner):**

| Ràng buộc | Source / Owner |
|-----------|----------------|
| **Chữ người chơi không sửa được dữ kiện từ sàn** | URD UN-014 |
| **Không thao tác nhật ký nào phát ra được lệnh**; nhật ký chạy trên journal path, chậm nhất | URD UN-015 · `docs/_shared/system-overview.md` |
| Mở nhật ký từ menu an toàn giữa phiên **huỷ ARM và khoá mở lệnh mới** | `docs/_shared/operating-environment.md` (ràng buộc 4) |
| **Một nơi tính, một nơi đọc** — nhật ký không tự tính con số nào, kể cả gộp điểm nhiều phiên | URD D-02 |
| Nhật ký **là nguồn thu** bằng chứng cho `process-score`, không chỉ nơi đọc điểm | URD Mục 7 |
| **Nhật ký không bao giờ tự xoá thứ gì** — giữ vô hạn; đổi lại phải cảnh báo dung lượng trước khi hết chỗ | URD Mục 7 — mâu thuẫn với *hạn giữ nhật ký* **đã giải bằng cách bỏ hẳn mục đó** (2026-08-29) |
| Ngoài phiên dùng chuột và bàn phím; trong phiên chỉ tay cầm và phải ngắn | URD Mục 7 |
| **Ảnh biểu đồ phải tự chụp và lưu sẵn trong máy** — không có đường lấy tự động từ TradingView hay nguồn giá không chính thức | URD Mục 7 |
| Chrome desktop, **giao diện tối**, một tài khoản demo duy nhất | URD Mục 7 |
| Nội dung nhật ký là **dữ liệu cá nhân** | `docs/_shared/project-profile.md` — Compliance |

**Dependencies (deliverable do bên khác sở hữu):**

| Phụ thuộc | Owner | Blocks nếu chưa sẵn |
|-----------|-------|---------------------|
| Vòng đời phiên (mở, đóng, khoá) | `order-execution` (FR-001..FR-008) | FR-001..FR-005 |
| Khoảnh khắc **lệnh đầu tiên khớp** | `order-execution` (FR-021) | FR-013 — bản chụp không biết chốt lúc nào |
| Bản xem trước trên HUD | `order-execution` (FR-013) | FR-027 |
| Hàm quy đổi và **làm tròn theo bước nhảy sàn** | `order-execution` (FR-010) | FR-025 |
| Luật huỷ ARM khi mở menu an toàn | `order-execution` (FR-018, FR-052) | FR-053 |
| Dữ kiện khớp và đóng lệnh | Sàn cTrader/Spotware | FR-044, FR-049 |
| **Điểm quy trình đã chốt** | `process-score` | FR-036, FR-038 — bản đồ nhiệt không có gì để tô |
| **Điểm ở mức buổi tối** khi một buổi có nhiều phiên | `process-score` | FR-036 — xem OQ-3 |
| Nội dung memo + ba thao tác nghe/sửa/xoá | `voice-journal` (FR-037, FR-041) | Một phần nội dung của FR-044 |
| Kết quả chấm luật của một lệnh | `playbook-grading` (FR-044) | Một phần nội dung của FR-044 |
| Đường dẫn sang bản tua lại | `trade-replay` | FR-044, FR-047 |
| **Định nghĩa loại lỗi** | `execution-learning` — **chưa có URD** | FR-043 — xem OQ-4 |
| Kế hoạch phiên AI đã lưu | `ai-desk` (FR-032) | FR-017 |
| Cảnh báo dung lượng | `reports-export` (UN-017) | FR-020 |

**Assumptions (tin là đúng — nêu hệ quả nếu sai):**

| Giả định | Invalidate {X} nếu sai |
|----------|------------------------|
| **Ngày không giao dịch là dữ liệu hợp lệ**, không phải dữ liệu thiếu (URD A-03) | BR-008 sai; bản đồ nhiệt và mọi số trung bình hiểu sai những đêm đứng ngoài — **phá nguyên tắc lớn nhất của sản phẩm**. Xem OQ-1 |
| Người chơi review **ngay trong buổi tối đó** (URD A-04) | FR-002 sai; "hôm nay" không còn là điểm về, và **toàn bộ mô hình màn hình chính phải xoay trục quanh việc chọn ngày cũ**. Xem OQ-2 |
| Khoảng **20 phiên mỗi tháng** (URD A-05) | Nhiều hơn nhiều lần thì FR-041 và FR-033 cần cách tổ chức khác |
| Người chơi muốn đọc kế hoạch của ngày **cạnh từng lệnh** (URD A-06) | Phần liên kết lệnh với luận điểm là công thừa. Xem OQ-4 |
| Bốn đồng hồ đổi giờ theo lịch **riêng của từng thành phố**; chỉ Tokyo không đổi | NFR-007 sai; người chơi ngồi vào bàn lệch một tiếng trong cửa sổ 2–3 tuần mỗi năm |

## 12. Open Questions

> **Số OQ đánh riêng cho từng tài liệu.** `OQ-3` của SRS này không nhất thiết là `OQ-3` của PRD cùng feature.
> Neo ổn định để đối chiếu là **số OQ của URD** ghi trong ngoặc *(kế thừa URD OQ-x)*.

* [ ] **OQ-1** *(kế thừa URD OQ-1)*: Một ngày **không giao dịch** hiện màu gì trên bản đồ nhiệt để không bao
  giờ bị đọc nhầm thành đêm tệ — cùng thang màu quy trình, một màu trung tính riêng, hay một ký hiệu riêng?
  Và phải phân biệt được với ngày **thị trường đóng**. **Chặn FR-033..035.** Em **không tạm quyết** — nó
  chạm đúng nguyên tắc lớn nhất của sản phẩm ("một buổi tối đứng ngoài có kỷ luật là một buổi tối tốt").

* [ ] **OQ-2** *(kế thừa URD A-04)*: Người chơi review **ngay trong buổi tối đó** hay vài ngày sau?
  **Chặn FR-002.** Nếu review muộn thì "hôm nay" không còn là điểm về và toàn bộ mô hình màn hình chính phải
  xoay trục quanh việc chọn ngày cũ. **Đây là quyết định tổ chức thông tin — để trôi sang giai đoạn wireframe
  là muộn.**

* [ ] **OQ-3** *(kế thừa URD OQ-7, chung với `process-score`)*: `process-score` có cung cấp điểm ở mức **buổi
  tối** không, hay chỉ mức **phiên**? **Chặn FR-036.**
  🔶 **Tạm quyết:** chưa có con số cấp buổi thì ô nhiệt **hiện từng phiên** thay vì bịa một điểm trung bình —
  đúng ràng buộc BR-006. *Nếu sai (deck có cấp buổi):* ô nhiệt đơn giản hơn, không mất gì.

* [ ] **OQ-4** *(kế thừa URD OQ-3, OQ-4)*: Việc **gắn một lệnh với luận điểm của ngày** thuộc feature nào —
  ở đây hay `execution-learning`? Và `execution-learning` giữ slug đó không, URD của nó viết trước hay sau?
  **Ảnh hưởng FR-043 và phạm vi FR-044.** Để muộn thì hai feature dễ dựng trùng cùng một đường liên kết.

* [x] **OQ-5** *(kế thừa URD OQ-11, chung với `reports-export`)*: Mục *hạn giữ nhật ký* trong màn cài đặt
  mâu thuẫn với NFR-006 ở đây.
  **Resolved 2026-08-29: bỏ hẳn mục *hạn giữ nhật ký*.** Lý do: nó mâu thuẫn với **hai** quyết định đã chốt (`daily-journal` giữ vô hạn · `voice-journal` bản ghi âm không tự hết hạn); phép tính dung lượng không ủng hộ nó (~20 phiên/tháng, chữ và ảnh không đáng kể, giọng nói "ở mức không đáng kể"); và thứ duy nhất phình thật là **tape** — nay thuộc `order-execution`, nên hạn giữ tape là cấu hình của tape chứ không phải của nhật ký. Thay thế: **cảnh báo dung lượng + xoá thủ công**, vốn đã là thiết kế.
  **NFR-006 vì vậy không còn mâu thuẫn nào** — không tồn tại cơ chế tự xoá nào trong sản phẩm.

* [ ] **OQ-6** *(kế thừa URD OQ-2)*: Giữa phiên có cần **ghi chú nhanh bằng tay cầm** không, ngoài tự chấm
  1–5 và memo giọng nói? Nếu có thì hình thức nào chịu được ràng buộc "ngắn và bằng tay cầm" của FR-058?

* [ ] **OQ-7** *(kế thừa URD OQ-6)*: Quy tắc "buổi tối vắt qua nửa đêm thuộc ngày bắt đầu" (FR-003) có đúng
  với cả phiên Sydney/Tokyo không, hay mốc gom phải theo **khung giờ phiên người chơi tự đặt** ở
  `order-execution`?

* [ ] **OQ-8** *(kế thừa URD OQ-5, chung với `voice-journal` OQ-3)*: Kế hoạch của ngày, ghi chú và nguyên
  tắc có **tìm theo chữ** được không? `voice-journal` đã chốt memo thì **không**. Nếu cả nhóm này cũng
  không, thì với dữ liệu giữ vô hạn (NFR-006), thứ đã viết ra chỉ tìm lại được qua **ngày** hoặc qua **lệnh**.

* [ ] **OQ-9** *(kế thừa URD OQ-8, chung với `trade-replay` và `process-score`)*: Những lần **tự huỷ không
  dẫn tới lệnh nào** hiện ở đâu? Ứng viên tự nhiên là chi tiết một buổi tối ở đây, nhưng con số cộng dồn đã
  chốt thuộc `process-score`. **Cần chốt một lần cho cả ba tài liệu.**

* [ ] **OQ-10** *(kế thừa URD OQ-10)*: Gỡ **một** ảnh hoặc một ghi chú vừa đính — gỡ hẳn, hay đánh dấu đã gỡ
  mà vẫn giữ vết? Ảnh hưởng FR-018 và NFR-006.

* [ ] **OQ-11** *(mới — hệ quả thứ tự phát hành)*: `daily-journal` ra **trước hay sau** `process-score`?
  FR-006, FR-009, FR-013 là ba nguồn bằng chứng cho hai trục của deck; ra sau nghĩa là deck ra mắt với
  **3/5 trục**. Xem `process-score` A-06.

---

> **Nguồn:** `daily-journal-urd.md` (19 nhu cầu, 7 journey, 20 tình huống ngoại lệ, 6 thước đo, 2 quyết định
> đã chốt + 4 giả định) · `daily-journal-prd.md` (16 capability) · bốn tài liệu nền `docs/_shared/` · ranh
> giới nhận từ `order-execution`, `process-score`, `voice-journal`, `playbook-grading`, `trade-replay`,
> `ai-desk`, `reports-export`, `execution-learning`.
>
> **🔶 Hai quyết định thay user:** OQ-3 (ô nhiệt hiện từng phiên khi chưa có con số cấp buổi) và OQ-5 (không
> bật mặc định cơ chế tự xoá). **OQ-1 và OQ-2 em cố ý không quyết** — cái đầu chạm nguyên tắc lớn nhất của
> sản phẩm, cái sau là quyết định tổ chức thông tin.
>
> **Tầng 2–4 chưa sinh:** `daily-journal-flows.md`, `-states.md`, `-erd.md`, use case, user story, AC.
