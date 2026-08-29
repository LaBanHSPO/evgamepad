---
type: srs
feature: reports-export
status: draft
updated: 2026-08-29
links:
  - docs/reports-export/reports-export-urd.md
  - docs/reports-export/reports-export-prd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/process-score/srs/process-score-spec.md
  - docs/daily-journal/srs/daily-journal-spec.md
  - docs/voice-journal/srs/voice-journal-spec.md
  - docs/trade-replay/srs/trade-replay-spec.md
  - docs/tilt-meter/srs/tilt-meter-spec.md
---

# reports-export — Software Requirements Specification

## 1. Scope

Đặc tả **lối ra của dữ liệu** — báo cáo đọc được, bản xuất mang đi được, gói sao lưu, và đường xoá sạch có
chủ ý — cộng **màn cài đặt an toàn**, lối vào duy nhất được phép đổi cấu hình mà **không chạm được vào bất
kỳ chốt an toàn nào**.

**Trong phạm vi:** báo cáo theo kỳ tự chọn, mở đầu bằng quy trình, phụ lục kết quả mặc định tắt · lưu báo
cáo thành tệp đọc được · xuất JSON tự đủ nghĩa và CSV phẳng · gói sao lưu đầy đủ kèm bản kê có mã kiểm tra ·
khôi phục có điều kiện và kiểm trước khi động vào dữ liệu hiện tại · xoá sạch có chủ ý · màn cài đặt chỉ đổi
được thứ an toàn · cảnh báo dung lượng · vết ghi nhận không có nội dung · ba thao tác nặng cần xác nhận gần
đây.

**Ngoài phạm vi:** **nhập lịch sử giao dịch từ cTrader, MT5 hay bất kỳ công cụ nào — dứt khoát không tồn
tại** · tính toán bất kỳ số liệu nào (`process-score`, `daily-journal`) · đổi **chốt an toàn** (demo/thật,
đăng nhập sàn, địa chỉ lắng nghe, quyền công cụ AI, trọng số các trục) · sửa luật playbook
(`playbook-grading`) · sửa triết lý và nguyên tắc (`daily-journal`) · xoá riêng dữ liệu giọng nói
(`voice-journal`) · gỡ một ảnh hoặc ghi chú vừa đính (`daily-journal`) · thư viện loại lỗi
(`execution-learning`, *chưa có URD*) · chia sẻ, đồng bộ đám mây, gửi báo cáo qua email, hay bất kỳ đường nào
**sản phẩm tự gửi dữ liệu đi** · nhắc sao lưu định kỳ · giao diện sáng và giao diện di động.

> **Đây là feature duy nhất chạm được toàn bộ dữ liệu sản phẩm cùng một lúc** — nên cũng là feature duy nhất
> có thể **làm mất sạch** hoặc **làm rò rỉ hết**. Hai nghĩa vụ kéo ngược nhau và **cả hai đều phải giữ**:
> *mang dữ liệu ra thật dễ*, và *không bao giờ mang theo bí mật, không bao giờ xoá nhầm*.
>
> **Feature này không tính bất kỳ con số nào của riêng nó.** Báo cáo **render lại** đúng con số
> `process-score` và `daily-journal` đã chốt. **Lệch nghĩa là báo cáo sai, không phải deck sai.**
>
> **Ràng buộc sản phẩm giữ được nằm ở lúc TẠO tệp**, không phải sau đó. Tệp đã ở trên máy người chơi thì nó
> đi đâu là quyết định của người chơi — và **gói đã tạo nằm ngoài vòng kiểm soát của sản phẩm**.

## 2. Actors & Stakeholders

| Actor | Loại | Mục tiêu | Trong scope? |
|-------|------|----------|--------------|
| **Người chơi** | người | Cầm được dữ liệu của mình ra khỏi sản phẩm, giữ nó an toàn, đổi được thiết lập vô hại **mà không đụng máy chủ** | Có |
| **Trợ lý AI ngoài** | ngoài | **Nơi nhận** một tệp mà người chơi chủ động đưa cho | **Không phải người dùng.** Sản phẩm **không gửi đi đâu, không kết nối tới nó, không biết nó là ai** |
| **`process-score`** | hệ thống | **Tính** điểm quy trình và mọi số liệu tổng hợp; báo cáo render lại | **Không** — chỉ đọc |
| **`daily-journal`** | hệ thống | **Tính** số liệu cấp ngày; và sở hữu quy tắc "một ngày là một buổi tối" mà kỳ báo cáo phải dùng | **Không** — chỉ đọc |
| **`voice-journal`** | hệ thống | Sở hữu bản ghi âm, bản chép, và **đường xoá riêng giọng nói** | **Không** — ranh giới, xem OQ-1 |
| **`trade-replay`** | hệ thống | Sở hữu tape đã đóng băng — một phần của gói sao lưu | **Không** — nguồn dữ liệu |
| **`playbook-grading`** · **`tilt-meter`** | hệ thống | Sở hữu trình sửa playbook · mục bật/tắt đo tâm lý — cài đặt **dẫn sang**, không dựng bản sao | **Không** — ranh giới |
| **`execution-learning`** | hệ thống | **Định nghĩa** loại lỗi mà báo cáo render lại | **Không** — **chưa có URD** |
| **Sàn cTrader / Spotware** | ngoài | — | **Không liên quan.** Không dữ liệu nào của feature này đi tới sàn, và **không dữ liệu nào từ sàn được nhập vào** |

## 3. Functional Requirements (FR)

### 3.1 Báo cáo

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-reports-export-001 | Báo cáo theo **kỳ tự chọn** | Một tuần · một tháng · một khoảng ngày tuỳ chọn · hoặc **một phiên** | P1 | demo | URD UN-001 |
| FR-reports-export-002 | Kỳ báo cáo dùng quy tắc **"một ngày là một buổi tối"** | Không cắt theo ngày lịch — nếu không, **cùng một khoảng ngày sẽ ra hai kết quả khác nhau** giữa báo cáo và bản đồ nhiệt | P1 | test | URD Mục 7 · `daily-journal` FR-003 |
| FR-reports-export-003 | Báo cáo **mở đầu bằng quy trình** | Bìa quy trình → bản đồ nhiệt → điểm quy trình → mức tuân thủ → các lỗi sai → lát cắt theo playbook | P1 | demo | URD UN-002 |
| FR-reports-export-004 | Lát cắt playbook ở phần quy trình **chỉ gồm số lệnh và mức tuân thủ** | Kỳ vọng theo R, MFE/MAE, hiệu suất trung bình và bảng theo kiểu setup là **con số kết quả** — chúng thuộc phụ lục | P1 | test | URD UN-002 |
| FR-reports-export-005 | **Phụ lục kết quả mặc định TẮT** | Người chơi phải **chủ động tích** thì nó mới có trong tệp. Không tích thì trong tệp **không có một đồng nào** | P1 | test | URD UN-003 |
| FR-reports-export-006 | **Không preference nào bật vĩnh viễn được phụ lục** | Mục "mặc định báo cáo" trong cài đặt **không bao gồm** phụ lục kết quả. Phụ lục **luôn khởi tạo ở trạng thái tắt cho mỗi lần tạo**; bật một lần rồi quên thì **cú bấm có chủ ý đã biến thành cú bấm một lần** | P1 | test | URD UN-003 |
| FR-reports-export-007 | Lưu báo cáo thành **một tệp đọc được ngay trên máy** | Bằng chính trình duyệt đang mở; **không thành phần nào phải thêm vào máy chủ**, và tệp mở được ở bất cứ đâu | P1 | demo | URD UN-004 |
| FR-reports-export-008 | Tệp in ra **đọc được trên nền sáng** | Bản để in là **một bản riêng**, không phải ảnh chụp màn hình nền tối; bảng **không bị cắt ngang trang** | P1 | test | URD Mục 6 |
| FR-reports-export-009 | Báo cáo **render lại** con số đã chốt, không tính lại | Nếu hai nơi lệch nhau thì **lỗi nằm ở báo cáo, không phải ở deck** | P1 | test | URD Mục 3 · `process-score` FR-053 |
| FR-reports-export-010 | Dòng miễn trừ **có mặt cả trong tệp báo cáo** | Vì tệp đó **rời khỏi sản phẩm và có thể được đọc ngoài mọi ngữ cảnh** | P1 | kiểm tra | URD Mục 3 |

### 3.2 Xuất dữ liệu

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-reports-export-011 | Xuất JSON **đầy đủ ngữ cảnh** | Phiên · kế hoạch trước phiên · điểm chấm từng lệnh · phần nhìn lại · điểm quy trình · phân tích · thông tin về các tệp đính kèm | P0 | demo | URD UN-005 |
| FR-reports-export-012 | Bản xuất JSON **tự đủ nghĩa** | Chứa phần **tự mô tả**: tên trường · đơn vị · thang điểm · **múi giờ của các mốc thời gian** — đủ để hiểu **mà không cần hỏi ai** | P0 | test | URD UN-005 · A-02 |
| FR-reports-export-013 | Xuất **CSV phẳng** | Dữ kiện từng lệnh cộng các chiều nhìn lại đã dàn phẳng, mở được bằng bảng tính | P2 | demo | URD UN-006 |
| FR-reports-export-014 | CSV không vỡ khi mở bằng bảng tính | **Chữ tiếng Việt hiện đúng**; memo nhiều dòng và dấu phẩy trong chữ **không làm lệch cột** | P2 | test | URD Mục 6 |
| FR-reports-export-015 | Giới hạn được kỳ xuất | Bản xuất nhiều tháng vẫn tải về được **mà trình duyệt không treo**; người chơi giới hạn được kỳ xuất như khi tạo báo cáo | P1 | test | URD Mục 6 |
| FR-reports-export-016 | Người chơi **biết trước trong tệp có gì** | Trước khi xuất, người chơi biết bản xuất chứa những phần nào — đặc biệt với phần riêng tư nhất (bản chép giọng nói) | P0 | demo | URD Mục 6 — xem OQ-6 |

### 3.3 Không mang theo bí mật

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-reports-export-017 | Bản xuất **không chứa bí mật** | Không giá trị biến môi trường · không token · không cấu hình gốc · **không đường dẫn tuyệt đối trên máy chủ** | P0 | test | URD UN-007 |
| FR-reports-export-018 | Ràng buộc này **kiểm được, không phải một lời hứa** | Kiểm bằng **tìm chuỗi** trong tệp thật: token, biến môi trường, tên miền máy chủ, đường dẫn tuyệt đối | P0 | test | URD UN-007 |
| FR-reports-export-019 | Gói sao lưu **không chứa** thứ thay thế được hoặc bí mật | Mô hình chép lời · ảnh Docker · bộ nhớ đệm · biến môi trường · token. **Thứ thay thế được thì không cần chép; thứ bí mật thì không được chép** | P0 | test | URD UN-010 |
| FR-reports-export-020 | Ràng buộc giữ được nằm ở **lúc tạo tệp** | Sau khi tệp đã ở trên máy người chơi, việc nó đi đâu là **quyết định của người chơi**. Sản phẩm **không tự gửi dữ liệu đi đâu cả** | P0 | kiểm tra | URD Mục 7 |

### 3.4 Gói sao lưu

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-reports-export-021 | Gói sao lưu **đầy đủ** | Dữ liệu nhật ký **cộng** bản ghi âm, ảnh biểu đồ và tape đã đóng băng. **Thiếu một trong số đó thì replay và nhật ký giọng nói khôi phục về sẽ rỗng** | P0 | test | URD UN-008 |
| FR-reports-export-022 | **Bản kê** với tên, kích thước và mã kiểm tra từng phần | Đối chiếu được **mà không phải khôi phục thật** | P0 | test | URD UN-009 |
| FR-reports-export-023 | Bản kê **phản ánh đúng thứ thật sự có trong gói** | Một tệp đính kèm mất trên đĩa nhưng còn tên trong nhật ký → việc tạo gói **nói rõ phần nào thiếu** thay vì lặng lẽ bỏ qua | P0 | test | URD Mục 6 · A-07 |
| FR-reports-export-024 | Gói **luôn là một lát cắt nhất quán** | Hoặc **chờ các việc nền xong** (chép lời, đóng băng tape) rồi mới chụp, hoặc **bị từ chối kèm nêu rõ việc đang chạy**. **Không bao giờ tạo ra một gói nửa vời** | P0 | test | URD UN-024 |
| FR-reports-export-025 | Hết chỗ giữa lúc đang dựng gói | Dừng lại khi chạm ngưỡng dung lượng tạm, **xoá phần dở dang**, và **nói rõ là chưa có gói nào** | P0 | test | URD Mục 6 |
| FR-reports-export-026 | Đã xoá riêng giọng nói trước đó rồi mới sao lưu | Gói **phản ánh đúng thứ đang có**, và **bản kê nói rõ** — không đọc nhầm thành một gói thiếu | P1 | test | URD Mục 6 — xem OQ-1 |

### 3.5 Khôi phục

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-reports-export-027 | Khôi phục **có điều kiện** | Chỉ chạy khi **phiên đã khoá**, **không còn vị thế mở**, và **không có việc chép lời hay đóng băng tape nào đang chạy**. Không đủ điều kiện → **bị từ chối kèm lý do cụ thể** | P0 | test | URD UN-011 |
| FR-reports-export-028 | Kiểm **trước khi** động vào dữ liệu hiện tại | Bản kê · mã kiểm tra · tính tương thích · **các đường dẫn bên trong gói** đều được kiểm trước | P0 | test | URD UN-012 |
| FR-reports-export-029 | Gói bị sửa tay bị **từ chối trước khi mở ra** | Đường dẫn lạ (tuyệt đối, lùi ra ngoài, liên kết mềm, trùng tên) · phần tử kiểu lạ · phần bung ra lớn bất thường — **cả ba loại, và từ chối trước khi mở gói, không phải sau** | P0 | test | URD Mục 6 |
| FR-reports-export-030 | Hỏng ở bất kỳ bước nào thì dữ liệu hiện tại **nguyên vẹn** | Mở lại **vẫn là nhật ký cũ, đầy đủ, như chưa từng bấm** | P0 | test | URD UN-012 |
| FR-reports-export-031 | Bản mới dựng riêng, kiểm xong mới đổi chỗ | Mất điện hoặc đứt kết nối giữa chừng → mở lại **vẫn là dữ liệu cũ** | P0 | test | URD Journey 4 · Mục 6 |
| FR-reports-export-032 | Kiểm **chỗ trống trước**, từ chối sớm | Không đủ cho cả bản đang có, bản đang dựng và ảnh chụp lùi → **từ chối sớm kèm con số cần bao nhiêu**, không bắt đầu rồi chết giữa chừng | P0 | test | URD Mục 6 |
| FR-reports-export-033 | Đối chiếu **bằng con số** sau khi khôi phục | Số lượng bản ghi và mã kiểm tra tệp đính kèm **khớp bản kê**, và **kết quả hiện ra cho người chơi xem** | P0 | test | URD UN-013 |
| FR-reports-export-034 | Lệch thì **nêu rõ phần lệch** | Không báo một dòng "thành công" khi số lượng không khớp | P0 | test | URD Mục 6 |
| FR-reports-export-035 | **Chỉ nhận gói do chính sản phẩm này tạo ra** | Tệp không phải gói của sản phẩm (bản xuất của một công cụ khác) → **bị từ chối**, vì **không đường nhập nào tồn tại** | P0 | test | URD UN-021 |
| FR-reports-export-036 | Gói của phiên bản dữ liệu **không tương thích** | Kiểm tính tương thích trước; không tương thích thì **từ chối kèm lý do**. Mức hỗ trợ nâng lên phiên bản mới hơn: xem OQ-8 | P0 | test | URD Mục 6 |
| FR-reports-export-037 | Khôi phục **nói rõ nó sẽ chạm vào những gì** trước khi chạy | Đặc biệt với các preference — chưa chốt chúng thuộc nhóm bị thay hay nhóm được giữ | P0 | demo | URD Mục 6 — xem OQ-5 |

### 3.6 Xoá sạch

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-reports-export-038 | Xoá sạch cần **hai điều kiện cùng đạt** | **Gõ đúng câu xác nhận** **và** **giữ nút hai giây** | P1 | test | URD UN-014 |
| FR-reports-export-039 | Từ chối khi còn phiên hoặc vị thế đang chạy | Kèm điều kiện để làm được — **cùng mức bảo vệ** mà `voice-journal` đặt cho đường xoá riêng của nó | P1 | test | URD UN-014 · `voice-journal` FR-045 |
| FR-reports-export-040 | **Mời sao lưu trước** khi xoá | Giao diện mời tạo gói và **nói rõ gói đó sẽ nằm ở đâu trên máy**; người chơi tự quyết có làm hay không | P1 | demo | URD UN-015 |
| FR-reports-export-041 | Sau lời xác nhận cuối **không có bản sao ẩn nào** | Từ chối lời mời sao lưu rồi xoá sạch là **lựa chọn có ý thức và được tôn trọng** — không giữ bản sao "phòng khi hối hận" | P1 | test | URD UN-015 |
| FR-reports-export-042 | Xoá xong thì **dọn cả chỗ trống** | Dữ liệu, bản ghi âm, ảnh và tape bị xoá và chỗ trống được dọn | P1 | test | URD UN-016 |
| FR-reports-export-043 | Sau xoá sạch chỉ còn bốn thứ | Cấu hình · mô hình · phần mềm · thông tin đăng nhập — **và một vết ghi nhận không có nội dung**. **Không nội dung nhật ký hay ghi chú riêng nào còn sót lại** | P1 | test | URD UN-016 |
| FR-reports-export-044 | Nói rõ **gói sao lưu cũ có thể làm sống lại dữ liệu đã xoá** | Gói đã tạo nằm **ngoài vòng kiểm soát của sản phẩm** — và lời mời sao lưu ở FR-040 **tạo ra chính bản sao đó** | P1 | demo | URD Mục 6 — xem OQ-1 |

### 3.7 Màn cài đặt an toàn

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-reports-export-045 | Danh sách thứ **đổi được** | Biểu tượng (trong danh sách máy chủ cho phép) · khung thời gian biểu đồ · lịch buổi tối và múi giờ · hiệu chỉnh tay cầm · rung · micro và nút giữ để nói · giọng đọc · mặc định báo cáo | P1 | demo | URD UN-018 · **bỏ *hạn giữ nhật ký* 2026-08-29** |
| FR-reports-export-046 | **Chốt an toàn không xuất hiện trong giao diện** | Chế độ demo/thật · thông tin đăng nhập sàn · địa chỉ lắng nghe · quyền công cụ của AI · trọng số các trục điểm — **không có mặt**, kể cả ở dạng chỉ đọc có thể gây hiểu nhầm là sửa được | P1 | test | URD UN-019 |
| FR-reports-export-047 | Chốt an toàn sống **ngoài cơ sở dữ liệu**, sai thì sản phẩm không khởi động | Đó là lý do chúng cố tình không có mặt trong giao diện | P1 | kiểm tra | URD UN-019 |
| FR-reports-export-048 | Gửi thay đổi chứa khoá thuộc nhóm cấm | **Từ chối cả gói thay đổi** — **không âm thầm bỏ qua khoá cấm rồi báo thành công**; người chơi sẽ tưởng thứ mình gửi đã được nhận | P1 | test | URD Mục 6 |
| FR-reports-export-049 | Validate preference | Giá trị vô lý (khung giờ ngược, biểu tượng ngoài danh sách máy chủ cho phép) → **từ chối tại chỗ kèm lý do**; giá trị cũ giữ nguyên | P1 | test | URD Mục 6 |
| FR-reports-export-050 | Tài khoản cTrader là **danh tính chỉ đọc** | Nhìn thấy được, **không sửa được, không thêm được tài khoản thứ hai** | P1 | test | URD UN-020 |
| FR-reports-export-051 | **Dẫn sang** trình sửa của feature sở hữu | Trình sửa playbook (`playbook-grading`) và trình sửa triết lý/nguyên tắc (`daily-journal`). **Không dựng lại một trình sửa riêng** | P1 | demo | URD UN-022 |
| FR-reports-export-052 | Preference giữ được sau khi khởi động lại | Đổi một preference an toàn rồi khởi động lại: giá trị mới **phải còn** | P1 | test | URD Journey 6 |

### 3.8 Dung lượng và vết ghi nhận

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-reports-export-053 | **Cảnh báo dung lượng** khi chỗ trống xuống dưới ngưỡng | Kèm **con số cụ thể**, đủ sớm để còn kịp sao lưu và dọn | P1 | test | URD UN-017 |
| FR-reports-export-054 | **Không nhắc sao lưu định kỳ** | Không có "đã bao nhiêu ngày kể từ lần sao lưu gần nhất" — **mọi cơ chế nhắc theo nhịp đều là thứ cộng dồn theo thời gian mà `README.md` đã cấm** | P1 | test | URD UN-017 |
| FR-reports-export-055 | Bỏ qua cảnh báo nhiều lần | Cảnh báo **lặp lại khi mở phần dữ liệu**, nhưng **không leo thang thành lời nhắc theo nhịp** | P1 | test | URD Mục 6 |
| FR-reports-export-056 | Vết ghi nhận **không có nội dung** | Mọi thao tác dữ liệu để lại một vết: **chỉ hành động, thời điểm, số lượng**. Để tra cứu — và **không được biến thành lời nhắc** | P1 | kiểm tra | URD Mục 3 |

### 3.9 Thao tác nặng và loại trừ lẫn nhau

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-reports-export-057 | Ba thao tác nặng cần **một lần xác nhận gần đây** | Tải gói sao lưu · khôi phục · xoá sạch — **không chạy được chỉ vì cửa sổ trình duyệt đang mở sẵn** | P0 | test | URD UN-025 |
| FR-reports-export-058 | Mức chặt **tăng dần** | Tải gói nhẹ nhất; xoá sạch nặng nhất (câu xác nhận **cộng** giữ hai giây) | P0 | kiểm tra | URD UN-025 |
| FR-reports-export-059 | Gói sao lưu chứa **toàn bộ giọng nói cá nhân** | Nên nó **không được nằm sau đúng một cú bấm** | P0 | kiểm tra | URD UN-025 |
| FR-reports-export-060 | **Tại một thời điểm chỉ một thao tác dữ liệu chạy được** | Tạo gói · khôi phục · xuất · xoá sạch **loại trừ lẫn nhau**. Thao tác thứ hai bị từ chối kèm nêu rõ việc đang chạy và khi nào xong | P0 | test | URD Mục 7 |
| FR-reports-export-061 | Đây là ràng buộc **an toàn**, không phải giới hạn hiệu năng | Hai thao tác chồng nhau có thể gây **mất dữ liệu không lấy lại được** | P0 | kiểm tra | URD Mục 7 |
| FR-reports-export-062 | **Không đường nhập dữ liệu nào từ bên ngoài** | Không nhập lịch sử cTrader, MT5, CSV hay bất kỳ công cụ nào — **không endpoint nào tồn tại** | P0 | test | URD UN-021 |
| FR-reports-export-063 | Báo cáo và cài đặt **mở bằng tay cầm** từ menu an toàn | Việc chọn kỳ, tích phụ lục và xử lý tệp thì dùng chuột và bàn phím — đây là **bề mặt ngoài phiên** | P1 | demo | URD UN-023 |
| FR-reports-export-064 | Mở menu an toàn **huỷ ARM và khoá mở lệnh mới** | Nên mở báo cáo hay cài đặt giữa phiên là **một hành động có giá**, và người chơi **phải biết trước cái giá đó** | P1 | test | URD UN-023 · `order-execution` FR-052 |

### 3.10 Trạng thái thiếu dữ liệu trong báo cáo

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-reports-export-065 | Kỳ báo cáo **không có phiên nào** | Báo cáo vẫn tạo được và **nói rõ kỳ này không có phiên nào**, thay vì các bảng rỗng không giải thích | P1 | test | URD Mục 6 |
| FR-reports-export-066 | Kỳ chỉ có một hai phiên | In kèm **số phiên** bên cạnh mọi con số tổng hợp, và **giữ nguyên trạng thái "chưa đủ phiên"** của các chỉ số cần mẫu lớn đúng như deck đang hiện | P1 | test | URD Mục 6 |
| FR-reports-export-067 | Kỳ **không phải một tháng trọn** | Cho tới khi OQ-4 chốt: báo cáo kỳ tuỳ chọn **chỉ liệt kê con số cấp phiên** đã chốt và **nói rõ kỳ này không có số tổng hợp** — **feature này không tự gộp** | P1 | test | URD Mục 6 |
| FR-reports-export-068 | Kỳ chạm tới một **phiên chưa đóng** | Phiên chưa đóng **không xuất hiện**, hoặc xuất hiện kèm ghi rõ **chưa đóng, chưa có điểm** — không dựng một bìa quy trình rỗng trông như một buổi tối tệ | P1 | test | URD Mục 6 |
| FR-reports-export-069 | Playbook đã ngừng dùng nằm trong kỳ | Báo cáo vẫn hiện nó với **đầy đủ lịch sử** của kỳ đó — cùng cách deck đang làm | P1 | test | URD Mục 6 |
| FR-reports-export-070 | **Phần lỗi sai có thể trống ở ngày ra mắt** | `execution-learning` chưa tồn tại → báo cáo **nói rõ điều đó** thay vì để một mục rỗng | P1 | test | URD A-07 |
| FR-reports-export-071 | Trọng số đã đổi giữa kỳ báo cáo | Báo cáo **ghi rõ đang dùng bộ trọng số nào**, và **tính lại toàn bộ theo bộ hiện tại** — nhất quán với cách deck làm | P1 | test | URD Mục 6 — xem OQ-9 |

## 4. Non-Functional Requirements (NFR)

| ID | Category | Requirement | Priority | Acceptance |
|----|----------|-------------|----------|------------|
| NFR-reports-export-001 | security | **Không bản xuất hay gói nào chứa** giá trị biến môi trường, token, cấu hình gốc, hay đường dẫn tuyệt đối trên máy chủ | P0 | test — **tìm chuỗi** trong tệp thật, mọi bản xuất và mọi gói, không có ngoại lệ |
| NFR-reports-export-002 | security | **Không đường nào sản phẩm tự gửi dữ liệu đi** — không chia sẻ, không đồng bộ đám mây, không email | P0 | phân tích — soát mọi đường ra của dữ liệu |
| NFR-reports-export-003 | security | **Không endpoint nhập dữ liệu nào tồn tại** — khôi phục chỉ nhận gói do chính sản phẩm tạo | P0 | test — đưa một tệp lạ, kiểm bị từ chối |
| NFR-reports-export-004 | security | Ba thao tác nặng đòi **một lần xác nhận gần đây**, không dựa vào việc cửa sổ đang mở sẵn | P0 | test |
| NFR-reports-export-005 | security | **Chốt an toàn sống ngoài cơ sở dữ liệu**; sai thì sản phẩm không khởi động. Chúng **không có mặt trong giao diện cài đặt** | P0 | test — rà toàn màn cài đặt; gửi thẳng thay đổi chứa khoá cấm ở tầng dưới |
| NFR-reports-export-006 | data integrity | **Khôi phục hỏng ở bất kỳ bước nào thì dữ liệu hiện tại nguyên vẹn** | P0 | test — bốn cách hỏng, mỗi lần kiểm nhật ký hiện tại còn đầy đủ |
| NFR-reports-export-007 | data integrity | Gói sao lưu **luôn là một lát cắt nhất quán** — không bao giờ chụp giữa lúc một việc nền còn dang dở | P0 | test — tạo gói giữa lúc đang chép lời, kiểm hoặc chờ hoặc từ chối |
| NFR-reports-export-008 | data integrity | **Tại một thời điểm chỉ một thao tác dữ liệu chạy được.** Đây là ràng buộc an toàn, không phải giới hạn hiệu năng | P0 | test — chạy hai thao tác chồng nhau, kiểm cái thứ hai bị từ chối |
| NFR-reports-export-009 | correctness | Feature này **không tính bất kỳ số liệu nào**; báo cáo render lại con số `process-score` và `daily-journal` đã chốt | P0 | test — đối chiếu con số báo cáo với deck; lệch nghĩa là **báo cáo sai** |
| NFR-reports-export-010 | reliability | Feature này chết hoàn toàn **không** làm giảm khả năng mở, đóng, thoát vị thế | P0 | Diễn tập: tắt hẳn feature rồi chạy trọn chuỗi mở phiên → vào lệnh → đóng lệnh |
| NFR-reports-export-011 | usability | Bản xuất JSON **tự mô tả**: tên trường · đơn vị · thang điểm · múi giờ — đủ để một bên thứ ba hiểu **mà không cần hỏi ai** | P0 | test — đọc chính tệp, kiểm có phần tự mô tả |
| NFR-reports-export-012 | usability | Lưu báo cáo dùng **chính trình duyệt đang mở**; không thành phần nào phải thêm vào máy chủ | P1 | kiểm tra |
| NFR-reports-export-013 | privacy | Gói sao lưu chứa **dữ liệu giọng nói cá nhân** và nằm trên máy người chơi. Nơi lưu, cách bảo vệ và cách xoá phải rõ ràng | P0 | kiểm tra | Project profile — Compliance; xem OQ-7 |
| NFR-reports-export-014 | privacy | **Gói đã tạo nằm ngoài vòng kiểm soát của sản phẩm.** Xoá sạch không với tới được các gói đã nằm trên máy người chơi | P0 | kiểm tra — và người chơi phải được nói rõ điều này (FR-044) |
| NFR-reports-export-015 | compatibility | Chỉ Chrome desktop, **chỉ nền tối**. Không giao diện sáng, không giao diện di động — **trừ bản để in** (FR-008) | P0 | kiểm tra |
| NFR-reports-export-016 | compliance | Dòng miễn trừ demo / giải trí / không phải lời khuyên có mặt **cả trong tệp báo cáo xuất ra** | P0 | kiểm tra |
| NFR-reports-export-017 | usability | Giao diện tiếng Anh; tài liệu nghiệp vụ tiếng Việt | P0 | kiểm tra |

## 5. Business Rules

| ID | Rule | Trigger | Implements FR | Source |
|----|------|---------|---------------|--------|
| BR-reports-export-001 | **Không bản xuất hay gói nào mang theo bí mật.** Ràng buộc giữ được nằm ở **lúc tạo tệp**, không phải sau đó | Tạo bản xuất · tạo gói | FR-017, FR-019, FR-020 · NFR-001 | URD UN-007, UN-010 |
| BR-reports-export-002 | **Thứ thay thế được thì không cần chép; thứ bí mật thì không được chép** | Dựng gói sao lưu | FR-019 | URD UN-010 |
| BR-reports-export-003 | Gói **luôn là một lát cắt nhất quán**: hoặc chờ việc nền xong, hoặc từ chối. **Không bao giờ tạo ra một gói nửa vời** | Tạo gói khi còn việc nền | FR-024, FR-025 · NFR-007 | URD UN-024 |
| BR-reports-export-004 | **Kiểm trước khi động vào dữ liệu hiện tại.** Hỏng ở bất kỳ bước nào thì mở lại vẫn là nhật ký cũ, đầy đủ | Khôi phục | FR-028..FR-032 · NFR-006 | URD UN-012 |
| BR-reports-export-005 | Khôi phục **chỉ nhận gói do chính sản phẩm này tạo ra**. **Không đường nhập nào tồn tại** | Đưa một tệp để khôi phục | FR-035, FR-062 · NFR-003 | URD UN-021 |
| BR-reports-export-006 | Đối chiếu **bằng con số** sau khôi phục, và **kết quả hiện ra cho người chơi xem** — không báo một dòng "thành công" | Khôi phục xong | FR-033, FR-034 | URD UN-013 |
| BR-reports-export-007 | Xoá sạch cần **hai điều kiện cùng đạt**: gõ đúng câu xác nhận **và** giữ nút hai giây | Xoá sạch | FR-038 | URD UN-014 |
| BR-reports-export-008 | **Sau lời xác nhận cuối không có bản sao ẩn nào.** Từ chối lời mời sao lưu là lựa chọn có ý thức và được tôn trọng | Xoá sạch | FR-041 | URD UN-015 |
| BR-reports-export-009 | **Gói đã tạo nằm ngoài vòng kiểm soát của sản phẩm** — một gói cũ khôi phục về sẽ mang theo cả những thứ đã cố ý xoá sau đó | Xoá sạch · xoá riêng giọng nói · khôi phục | FR-044 · NFR-014 | URD Mục 7 — xem OQ-1 |
| BR-reports-export-010 | **Phụ lục kết quả luôn khởi tạo TẮT cho mỗi lần tạo báo cáo**; không preference nào bật vĩnh viễn được nó | Tạo báo cáo | FR-005, FR-006 | URD UN-003 |
| BR-reports-export-011 | Cú bấm có chủ ý cho tiền **chuyển về lúc tạo tệp**, vì một tệp tĩnh **không có tab để bấm lúc đọc** | Tạo báo cáo | FR-005 | URD UN-003 (chốt 2026-08-28) |
| BR-reports-export-012 | **Chốt an toàn không có mặt trong giao diện**, kể cả ở dạng chỉ đọc gây hiểu nhầm là sửa được | Mở màn cài đặt | FR-046, FR-047 · NFR-005 | URD UN-019 |
| BR-reports-export-013 | Thay đổi chứa khoá cấm → **từ chối cả gói**, không âm thầm bỏ qua rồi báo thành công | Gửi thay đổi cài đặt | FR-048 | URD Mục 6 |
| BR-reports-export-014 | **Chỉ dẫn sang** trình sửa của feature sở hữu; **không dựng bản sao thứ hai** | Sửa playbook · sửa nguyên tắc | FR-051 | URD UN-022 |
| BR-reports-export-015 | **Không nhắc sao lưu định kỳ.** Cảnh báo dung lượng lặp lại khi mở phần dữ liệu nhưng **không leo thang thành lời nhắc theo nhịp** | Chỗ trống dưới ngưỡng | FR-054, FR-055 | URD UN-017 (chốt 2026-08-28) |
| BR-reports-export-016 | Vết ghi nhận **chỉ có hành động, thời điểm, số lượng** — và không được biến thành lời nhắc | Mọi thao tác dữ liệu | FR-056 | URD Mục 3 |
| BR-reports-export-017 | **Tại một thời điểm chỉ một thao tác dữ liệu chạy được** — ràng buộc an toàn, không phải hiệu năng | Hai thao tác chồng nhau | FR-060, FR-061 · NFR-008 | URD Mục 7 |
| BR-reports-export-018 | **Feature này không tính số liệu nào.** Lệch giữa báo cáo và deck nghĩa là **báo cáo sai, không phải deck sai** | Render con số trong báo cáo | FR-009 · NFR-009 | URD Mục 3 |
| BR-reports-export-019 | **Feature này không được tự gộp** số tổng hợp cho kỳ không phải một tháng trọn | Báo cáo kỳ tuỳ chọn | FR-067 | URD Mục 7 — xem OQ-4 |
| BR-reports-export-020 | Kỳ báo cáo dùng quy tắc **"một ngày là một buổi tối"** của `daily-journal`, không cắt theo ngày lịch | Chọn kỳ báo cáo | FR-002 | URD Mục 7 |

## 6. Error Matrix

| Error ID | Title | Trigger | Severity | Related FR | Screen state | Recovery |
|----------|-------|---------|----------|------------|--------------|----------|
| E-reports-export-001 | **Bản xuất hoặc gói chứa bí mật** | Lọc sót | **critical** | FR-017, FR-019 | — | **Không hoàn tác được** — tệp đã ra ngoài không thu về được. Dừng toàn bộ việc xuất và sao lưu cho tới khi sửa |
| E-reports-export-002 | **Hết chỗ giữa lúc đang dựng gói** | Ổ đầy | **critical** | FR-025 | Dừng khi chạm ngưỡng, **xoá phần dở dang**, nói rõ **chưa có gói nào** | Một gói dở dang **trông như gói thật** — tin vào nó là mất dữ liệu |
| E-reports-export-003 | **Tạo gói giữa lúc phiên đang chạy hoặc còn việc nền** | Chép lời / đóng băng tape đang chạy | **critical** | FR-024 | Hoặc chờ xong rồi chụp, hoặc **từ chối kèm nêu rõ việc đang chạy và khi nào xong** | Một gói nửa vời **trông y hệt một gói đủ**; cái giá chỉ lộ ra lúc cần khôi phục |
| E-reports-export-004 | Một tệp đính kèm mất trên đĩa nhưng còn tên trong nhật ký | Dữ liệu lệch | major | FR-023 | Việc tạo gói **nói rõ phần nào thiếu** | Bản kê phản ánh đúng thứ **thật sự có** trong gói |
| E-reports-export-005 | **Gói sao lưu sai mã kiểm tra** | Gói hỏng | **critical** | FR-028, FR-030 | **Từ chối trước khi động vào dữ liệu hiện tại**, chỉ rõ phần nào không khớp | Nhật ký hiện tại nguyên vẹn |
| E-reports-export-006 | **Gói bị sửa tay** — đường dẫn lạ, phần tử kiểu lạ, phần bung ra lớn bất thường | Gói bị can thiệp | **critical** | FR-029 | **Từ chối trước khi mở gói ra**, không phải sau — cả ba loại | Ghi đè ra ngoài chỗ của nó, hoặc làm đầy ổ ngay lúc khôi phục |
| E-reports-export-007 | Gói của **phiên bản dữ liệu không tương thích** | Gói quá cũ | major | FR-036 | Kiểm tương thích trước; **từ chối kèm lý do** | Mức hỗ trợ nâng lên phiên bản mới hơn: xem OQ-8 |
| E-reports-export-008 | Đưa **một tệp không phải gói của sản phẩm này** | Bản xuất của công cụ khác | major | FR-035 | **Bị từ chối** | **Không đường nhập nào tồn tại** |
| E-reports-export-009 | **Khôi phục khi chỗ trống không đủ** | Ổ gần đầy | **critical** | FR-032 | **Từ chối sớm kèm con số cần bao nhiêu** | Không bắt đầu rồi chết giữa chừng — mà đó chính là lúc hay phải khôi phục nhất |
| E-reports-export-010 | **Khôi phục hỏng giữa chừng** | Mất điện, đứt kết nối | **critical** | FR-031 | Dữ liệu hiện tại giữ nguyên cho tới khi bản mới dựng xong và kiểm xong | Mở lại **vẫn là dữ liệu cũ, đầy đủ** |
| E-reports-export-011 | Bấm khôi phục khi **còn vị thế mở hoặc phiên đang chạy** | Điều kiện chưa đạt | major | FR-027 | **Bị từ chối**, kèm nêu rõ điều kiện còn thiếu | Dữ liệu bị thay giữa lúc đang giao dịch |
| E-reports-export-012 | Bấm khôi phục khi **đang có việc chép lời hoặc đóng băng tape** | Việc nền đang chạy | major | FR-027 | **Bị từ chối** cho tới khi việc nền xong | Cùng mức bảo vệ như với vị thế mở — một bản ghi âm đang chép dở sẽ ghi đè dữ liệu vừa khôi phục |
| E-reports-export-013 | **Khôi phục xong nhưng số lượng không khớp bản kê** | Gói thiếu | major | FR-033, FR-034 | Kết quả đối chiếu **hiện ra cho người chơi xem**, phần lệch được nêu rõ | Không báo một dòng "thành công" |
| E-reports-export-014 | **Khôi phục một gói cũ lên máy đang dùng** | Dựng máy chủ mới rồi khôi phục | major | FR-037 | Chưa chốt preference thuộc nhóm bị thay hay được giữ → khôi phục **phải nói rõ nó sẽ chạm vào những gì trước khi chạy** | Xem OQ-5 — **cả hai câu đều không hoàn tác được** |
| E-reports-export-015 | **Hai thao tác dữ liệu chạy chồng nhau** | Xoá sạch giữa lúc dựng gói · khôi phục giữa lúc xuất · hai tab cùng khôi phục | **critical** | FR-060 | Thao tác thứ hai **bị từ chối** kèm nêu rõ việc đang chạy và khi nào xong | **Hậu quả là mất dữ liệu không lấy lại được** |
| E-reports-export-016 | **Tải gói sao lưu chỉ bằng một cú bấm** | Không có cửa | **critical** | FR-057, FR-059 | Cần **một lần xác nhận gần đây**, không dựa vào việc cửa sổ đang mở sẵn | **Toàn bộ giọng nói cá nhân rời khỏi máy chủ** |
| E-reports-export-017 | Bấm xoá sạch khi **còn phiên hoặc vị thế đang chạy** | Điều kiện chưa đạt | major | FR-039 | **Bị từ chối**, kèm điều kiện để làm được | Cùng mức bảo vệ mà `voice-journal` đặt cho đường xoá riêng |
| E-reports-export-018 | **Gõ sai câu xác nhận, hoặc không giữ đủ hai giây** | Xoá nhầm | major | FR-038 | **Không có gì bị xoá**; hai điều kiện phải **cùng đạt** | — |
| E-reports-export-019 | Từ chối lời mời sao lưu rồi xoá sạch | Người chơi chọn không sao lưu | minor | FR-041 | **Không có bản sao ẩn nào** được giữ để "phòng khi hối hận" | Đây là lựa chọn có ý thức và được tôn trọng |
| E-reports-export-020 | **Gói sao lưu cũ làm sống lại dữ liệu đã cố ý xoá** | Đã xoá riêng giọng nói rồi khôi phục gói cũ hơn | major | FR-044 | Người chơi phải được nói rõ ở **đúng hai chỗ**: lúc xoá riêng giọng nói và lúc xoá sạch | Lời mời sao lưu ở bước xoá sạch **tạo ra chính bản sao đó**. Xem OQ-1 |
| E-reports-export-021 | Đã xoá riêng giọng nói trước đó, rồi sao lưu | Gói có bản chép mà không có tiếng | minor | FR-026 | Gói phản ánh đúng thứ đang có; **bản kê nói rõ** | Không đọc nhầm thành một gói thiếu |
| E-reports-export-022 | **Xoá sạch xong, không rõ các thiết lập còn hay mất** | Preference nằm cùng chỗ dữ liệu | major | FR-043 | Chưa chốt — FR-043 hiện chỉ khẳng định **nội dung nhật ký** không còn sót | Xem OQ-5 |
| E-reports-export-023 | **Gửi thay đổi cài đặt chứa khoá thuộc nhóm cấm** | Can thiệp ở tầng dưới | **critical** | FR-048 | **Từ chối cả gói thay đổi** | **Không âm thầm bỏ qua khoá cấm rồi báo thành công** — người chơi sẽ tưởng thứ mình gửi đã được nhận |
| E-reports-export-024 | Đổi một preference sang **giá trị vô lý** | Khung giờ ngược, biểu tượng ngoài danh sách cho phép | minor | FR-049 | **Từ chối tại chỗ kèm lý do**; giá trị cũ giữ nguyên | Cấu hình hỏng làm hỏng phiên sau |
| E-reports-export-025 | *(đã đóng 2026-08-29)* Hạn giữ nhật ký mâu thuẫn với "giữ vô hạn" | — | — | — | **Không còn tình huống này**: mục *hạn giữ nhật ký* đã bị bỏ khỏi FR-045 | **Không tồn tại cơ chế tự xoá nào** trong sản phẩm. Giữ dòng để không tái dùng mã lỗi |
| E-reports-export-026 | **Ổ đĩa hết chỗ giữa một phiên đang chạy** | Cảnh báo tới quá muộn | **critical** | FR-053 | Cảnh báo phải tới **đủ sớm** để không bao giờ rơi vào tình huống này | **Cái hỏng đầu tiên là một buổi tối đang giao dịch.** Ngưỡng và nơi hiện: xem OQ-3 |
| E-reports-export-027 | Bỏ qua cảnh báo dung lượng nhiều lần | Vẫn đi tới chỗ hết chỗ | minor | FR-055 | Lặp lại khi mở phần dữ liệu, **không leo thang thành lời nhắc theo nhịp** | Không có "đã bao nhiêu ngày kể từ" |
| E-reports-export-028 | **Kỳ báo cáo không có phiên nào** | Kỳ trống | minor | FR-065 | Báo cáo **vẫn tạo được** và nói rõ kỳ này không có phiên nào | Thay vì các bảng rỗng không giải thích |
| E-reports-export-029 | Kỳ chỉ có một hai phiên | Mẫu nhỏ | minor | FR-066 | In kèm **số phiên** bên cạnh mọi con số tổng hợp; giữ nguyên trạng thái "chưa đủ phiên" của deck | Các con số trung bình trông như kết luận |
| E-reports-export-030 | **Kỳ không phải một tháng trọn** | Báo cáo tuần hoặc khoảng tuỳ chọn | major | FR-067 | Chỉ liệt kê con số **cấp phiên** đã chốt và **nói rõ kỳ này không có số tổng hợp** | **Feature này không được tự gộp.** Xem OQ-4 |
| E-reports-export-031 | Kỳ chạm tới **một phiên chưa đóng** | Phiên đang chạy | minor | FR-068 | Phiên chưa đóng không xuất hiện, hoặc kèm ghi rõ **chưa đóng, chưa có điểm** | Không dựng một bìa quy trình rỗng trông như một buổi tối tệ |
| E-reports-export-032 | **Trọng số các trục đã đổi giữa kỳ báo cáo** | Hiệu chuẩn giữa kỳ | minor | FR-071 | Báo cáo **ghi rõ đang dùng bộ trọng số nào** và tính lại toàn bộ theo bộ hiện tại | Một tệp trộn hai thước đo mà người đọc không biết. Xem OQ-9 |
| E-reports-export-033 | **Số liệu trong báo cáo lệch so với deck** | Báo cáo tự tính | major | FR-009 | **Chỉ có một nơi tính**; báo cáo render lại đúng con số đó | **Lệch nghĩa là báo cáo sai, không phải deck sai** |
| E-reports-export-034 | Playbook đã ngừng dùng nằm trong kỳ | Sách đã bỏ | minor | FR-069 | Báo cáo vẫn hiện nó với **đầy đủ lịch sử** của kỳ đó | Cùng cách deck đang làm |
| E-reports-export-035 | **Phần lỗi sai trống ở ngày ra mắt** | `execution-learning` chưa tồn tại | minor | FR-070 | Báo cáo **nói rõ điều đó** | Thay vì để một mục rỗng |
| E-reports-export-036 | **Tích phụ lục kết quả rồi đưa tệp cho người khác** | Lựa chọn của người chơi | minor | FR-005 | Đây là **hệ quả của một lựa chọn có chủ ý**, không phải sự cố | Ràng buộc sản phẩm giữ là **không tự đưa tiền vào tệp**, không phải kiểm soát tệp sau khi đã tạo |
| E-reports-export-037 | **Đặt "mặc định báo cáo" rồi tạo báo cáo mới** | Preference bật sẵn phụ lục | major | FR-006 | Phụ lục **luôn khởi tạo tắt**; mặc định báo cáo không chạm tới nó, và **màn cài đặt nói rõ vì sao** | Bật một lần rồi quên thì **cú bấm có chủ ý đã thành cú bấm một lần** |
| E-reports-export-038 | Lưu báo cáo từ giao diện **chỉ có nền tối** | In ra đen kịt | minor | FR-008 | Tệp đọc được trên nền sáng; bảng **không bị cắt ngang trang** | Bản để in là **một bản riêng**, không phải ảnh chụp màn hình |
| E-reports-export-039 | **Bản xuất JSON quá lớn** sau nhiều tháng | Nhiều dữ liệu | minor | FR-015 | Vẫn tải về được mà trình duyệt không treo; **giới hạn được kỳ xuất** | — |
| E-reports-export-040 | **Bản CSV mở bằng bảng tính bị vỡ cột hoặc sai chữ** | Ký tự đặc biệt | minor | FR-014 | Chữ tiếng Việt đúng; memo nhiều dòng và dấu phẩy trong chữ không lệch cột | Bản xuất phẳng thành vô dụng đúng lúc muốn dùng |
| E-reports-export-041 | **Bản xuất chứa bản chép giọng nói** | Chưa chốt phạm vi | major | FR-016 | Chưa chốt — dù chốt thế nào, người chơi phải **biết trước khi xuất là trong tệp có gì** | **Phần riêng tư nhất trong toàn bộ nhật ký.** Xem OQ-6 |
| E-reports-export-042 | Mở báo cáo hoặc cài đặt **giữa phiên** | Mở từ menu an toàn | minor | FR-064 | **Huỷ ARM và khoá mở lệnh mới** — người chơi phải **biết trước cái giá đó** | Đóng lại thì mọi thứ trở về bình thường |

## 7. Success Criteria

| ID | Outcome nghiệp vụ | Đo bằng | Mốc đạt |
|----|-------------------|---------|---------|
| SC-reports-export-01 | *(ranh giới tuyệt đối)* **Không tệp nào rời khỏi sản phẩm mang theo bí mật** | Với mỗi bản xuất và mỗi gói tạo ra trong kỳ: **tìm chuỗi** token, biến môi trường, tên miền máy chủ, đường dẫn tuyệt đối | **0 lần**, không có ngoại lệ. **Một lần dính là hỏng** — và không hoàn tác được |
| SC-reports-export-02 | **Gói sao lưu thật sự khôi phục được**, không chỉ tạo ra được | Mỗi quý chạy **vòng tròn đầy đủ** trên dữ liệu bỏ đi được: sao lưu → đổi vài thứ → khôi phục → đối chiếu số lượng và mã kiểm tra với bản kê | Khớp **100%**. **Không diễn tập được coi như không đạt** — *một gói chưa từng khôi phục thử thì chưa phải một bản sao lưu* |
| SC-reports-export-03 | **Bản xuất đủ để một góc nhìn ngoài trả lời câu hỏi dài hạn** | Đưa bản xuất cho một trợ lý AI ngoài chưa biết gì và hỏi **ba câu**: tháng nào tuân thủ tốt nhất · loại lỗi nào lặp lại nhiều nhất · điểm quy trình có xu hướng gì | **Cả ba trả lời được chỉ từ tệp.** Phép thử không tất định nên đi kèm **vế tất định**: đọc chính tệp kiểm có phần tự mô tả |
| SC-reports-export-04 | *(ba vế tuyệt đối)* **Những thứ không được phép xuất hiện thì không bao giờ xuất hiện** | Rà tệp báo cáo mỗi lần đổi phần báo cáo; rà màn cài đặt mỗi lần đổi giao diện; rà nơi lưu sau mỗi lần xoá sạch | **0 tệp** có con số tiền khi không tích phụ lục · **0 khoá** chốt an toàn trong màn cài đặt · **0 nội dung nhật ký** còn sót sau xoá sạch |
| SC-reports-export-05 | *(ranh giới)* **Khôi phục hỏng không làm mất dữ liệu đang có** | Bốn cách hỏng: sai mã kiểm tra · đường dẫn lạ · phiên bản không tương thích · còn vị thế mở. Cộng hai: tệp không phải gói của sản phẩm · chỗ trống không đủ | **Cả sáu bị từ chối trước khi dữ liệu hiện tại thay đổi**, và sau mỗi lần từ chối nhật ký hiện tại **nguyên vẹn** |
| SC-reports-export-06 | *(ranh giới)* Báo cáo **không dựng định nghĩa thứ hai** cho bất kỳ số liệu nào | Đối chiếu con số trong tệp báo cáo với đúng con số deck đang hiện cho kỳ đó | **Trùng khít.** Lệch nghĩa là **báo cáo sai** |

> **SC-01 và SC-03 kéo ngược nhau, và đó là chủ ý.** SC-03 muốn bản xuất mang theo **càng nhiều ngữ cảnh
> càng tốt**; SC-01 canh chừng đúng cái giá phải trả nếu "nhiều ngữ cảnh hơn" lặng lẽ trở thành "mang theo
> cả những thứ không được mang". **Mỗi lần bản xuất giàu thêm là một lần SC-01 phải được chạy lại.**
>
> **SC-04 phủ ba nhu cầu Critical mà trước đó không thước đo nào chạm tới** (FR-005, FR-046, FR-043).
>
> **Giới hạn đã biết.** SC-02 đo được rằng gói *khôi phục được*, nhưng **không đo được rằng gói được tạo đủ
> thường xuyên**. Vế đó phụ thuộc hoàn toàn vào **thói quen thủ công** của người chơi, và **thứ duy nhất
> nhắc là cảnh báo dung lượng** — vì mọi lời nhắc theo nhịp đều bị cấm.
>
> **Bẫy tự kiểm:** quý đầu **không diễn tập được SC-02 lần nào** thì coi giả định "sao lưu thủ công là đủ an
> toàn" là **sai**, và đặt lại chính quyết định không-nhắc-định-kỳ — thay vì để nó lặng lẽ trôi qua.

## 8. Data Entities (tóm tắt — chi tiết ở `reports-export-erd.md`)

| Entity | Ý nghĩa nghiệp vụ | Thông tin nghiệp vụ cần lưu |
|--------|-------------------|------------------------------|
| **Gói sao lưu** | Một lát cắt nhất quán của toàn bộ dữ liệu | Thời điểm tạo · phiên bản dữ liệu · **bản kê** · kích thước · **các phần thiếu (nếu có) và vì sao** |
| **Bản kê** | Danh mục kiểm được của một gói | Với mỗi phần: **tên · kích thước · mã kiểm tra**. **Phản ánh đúng thứ thật sự có trong gói**, không phải thứ đáng lẽ phải có |
| **Preference an toàn** | Các thiết lập người chơi đổi được | Biểu tượng · khung thời gian · lịch buổi tối và múi giờ · hiệu chỉnh tay cầm · rung · micro và nút giữ để nói · giọng đọc · mặc định báo cáo. **Chưa chốt nhóm này bị thay hay được giữ khi khôi phục** — xem OQ-5 |
| **Vết ghi nhận thao tác dữ liệu** | Dấu vết để tra cứu | **Chỉ hành động · thời điểm · số lượng.** **Không có nội dung**, và **không được biến thành lời nhắc** |
| **Cấu hình báo cáo của một lần tạo** | Lựa chọn cho một tệp cụ thể | Kỳ · **phụ lục kết quả có được tích không (luôn khởi tạo TẮT)** · bộ trọng số đang dùng |

> **Không có entity nào lưu số liệu tổng hợp, điểm quy trình, hay định nghĩa loại lỗi** — feature này
> **không tính con số nào của riêng nó** (NFR-009). Đó là ranh giới, không phải một thiếu sót.
>
> **Không có entity nào lưu chốt an toàn** — chúng sống **ngoài cơ sở dữ liệu** và sai thì sản phẩm không
> khởi động (FR-047).

## 9. Flows (tóm tắt — chi tiết ở `reports-export-flows.md`)

| Flow | Tóm tắt | Nguồn |
|------|---------|-------|
| Cuối tháng tạo một báo cáo | Mở báo cáo bằng tay cầm → chọn kỳ → **phụ lục đang tắt sẵn**, không đụng vào → tạo, xem trước, lưu thành tệp → mở tệp: bìa quy trình trước, **không một đồng nào** | URD Journey 1 |
| Xuất dữ liệu đưa cho trợ lý AI ngoài | Chọn xuất JSON → nhận tệp có phiên, kế hoạch, điểm chấm, nhìn lại, điểm quy trình, phân tích, thông tin đính kèm → đưa cho trợ lý → **trả lời được mà không phải hỏi lại "cột này nghĩa là gì"** | URD Journey 2 |
| Sao lưu trước một thay đổi lớn | Bấm tạo gói (cần xác nhận gần đây) → gói dựng và tải về: nhật ký + ghi âm + ảnh + tape → **bản kê ghi tên, kích thước, mã kiểm tra từng phần** → chép sang ổ khác | URD Journey 3 |
| Khôi phục sau khi mất dữ liệu | Đóng phiên, không còn vị thế → bấm khôi phục, chọn gói → **kiểm trước**: bản kê, mã kiểm tra, tương thích, đường dẫn → dựng bản mới riêng, kiểm xong mới đổi chỗ → **đối chiếu bằng con số và hiện ra cho người chơi xem** | URD Journey 4 |
| Xoá sạch dữ liệu một cách có chủ ý | Chọn xoá sạch → **được mời sao lưu trước**, nói rõ gói sẽ nằm ở đâu → gõ đúng câu xác nhận, giữ nút hai giây → xoá và dọn chỗ trống → còn lại cấu hình, mô hình, phần mềm, đăng nhập, **và một vết ghi nhận không có nội dung** | URD Journey 5 |
| Đổi một thiết lập vô hại | Mở cài đặt bằng tay cầm → đổi thứ mình cần → **rà khắp màn hình: không chốt an toàn nào** → tài khoản cTrader hiện ra để xem, không sửa được → muốn sửa playbook thì **bấm vào đường dẫn sang**, không có trình sửa thứ hai ở đây | URD Journey 6 |
| Nhận cảnh báo sắp hết chỗ | Chỗ trống xuống dưới ngưỡng → **cảnh báo kèm con số cụ thể** → người chơi tạo gói rồi tự quyết dọn gì → ngoài cảnh báo này **sản phẩm không nhắc gì thêm** | URD Journey 7 |

## 10. Screens (tóm tắt — chi tiết ở `ascii-wireframe/`)

| Màn hình | Vai trò | Ghi chú ranh giới |
|----------|---------|-------------------|
| **Trình tạo báo cáo** | Chọn kỳ · **ô tích phụ lục kết quả (luôn tắt sẵn)** · xem trước · lưu tệp | Mở bằng tay cầm từ menu an toàn; thao tác bằng chuột. Con số render lại từ deck, **không tính lại** |
| **Tệp báo cáo** (bề mặt rời khỏi sản phẩm) | Bìa quy trình → bản đồ nhiệt → điểm → tuân thủ → lỗi sai → lát cắt playbook → *(phụ lục kết quả nếu tích)* | **Bản để in là bản riêng**, đọc được trên nền sáng. **Dòng miễn trừ có mặt trong tệp** |
| **Trình xuất dữ liệu** | Chọn JSON hoặc CSV · giới hạn kỳ · **cho biết trước trong tệp có gì** | Lọc bí mật xảy ra **trước khi** tệp được tạo |
| **Quản lý sao lưu** | Tạo gói · tải về · khôi phục · **kết quả đối chiếu sau khôi phục** | Ba thao tác nặng cần **xác nhận gần đây**; **một thao tác dữ liệu tại một thời điểm** |
| **Xoá sạch** | Mời sao lưu → câu xác nhận → giữ hai giây | **Nói rõ gói cũ có thể làm sống lại dữ liệu đã xoá** |
| **Màn cài đặt an toàn** | Chỉ preference an toàn · tài khoản chỉ đọc · **đường dẫn sang** trình sửa playbook và nguyên tắc | **Chốt an toàn không có mặt**, kể cả ở dạng chỉ đọc. `tilt-meter` và `voice-journal` đặt mục bật/tắt của mình lên đây |

## 11. Constraints, Dependencies & Assumptions

**Constraints (ràng buộc áp đặt — có source/owner):**

| Ràng buộc | Source / Owner |
|-----------|----------------|
| **Feature này không tính số liệu của riêng nó** — render lại con số `process-score` và `daily-journal` đã chốt | URD Mục 7 |
| **Không có đường nhập dữ liệu từ bên ngoài**; khôi phục chỉ nhận gói do chính sản phẩm tạo | URD UN-021 |
| **Chốt an toàn sống ngoài cơ sở dữ liệu**, sai thì sản phẩm không khởi động — **cố tình không có mặt trong giao diện** | URD Mục 7 · `README.md` |
| **Ràng buộc giữ được nằm ở lúc tạo tệp.** Sau khi tệp ở trên máy người chơi, nó đi đâu là quyết định của người chơi | URD Mục 7 |
| **Gói sao lưu đã tạo nằm ngoài vòng kiểm soát của sản phẩm** — xoá sạch không với tới được | URD Mục 7 |
| **Tại một thời điểm chỉ một thao tác dữ liệu chạy được** — ràng buộc an toàn, không phải hiệu năng | URD Mục 7 |
| Kỳ báo cáo dùng quy tắc **"một ngày là một buổi tối"**, không cắt theo ngày lịch | URD Mục 7 · `daily-journal` FR-003 |
| **Gói sao lưu chứa dữ liệu giọng nói cá nhân** | `docs/_shared/project-profile.md` — Compliance |
| Mở menu an toàn **huỷ ARM và khoá mở lệnh mới** | `docs/_shared/operating-environment.md` |
| Chỉ Chrome desktop, **chỉ nền tối** — trừ bản để in | URD Mục 7 |
| **Báo cáo không phải lời khuyên đầu tư** — dòng miễn trừ có mặt cả trong tệp | `docs/_shared/project-profile.md` |

**Dependencies (deliverable do bên khác sở hữu):**

| Phụ thuộc | Owner | Blocks nếu chưa sẵn |
|-----------|-------|---------------------|
| Điểm quy trình, mức tuân thủ, mọi số liệu tổng hợp đã chốt | `process-score` | FR-003, FR-009 — và **không được tự tính thay** |
| Bản đồ nhiệt, số liệu cấp ngày, quy tắc "một ngày là một buổi tối" | `daily-journal` | FR-002, FR-003 |
| **Cách tính số tổng hợp cho kỳ không phải một tháng trọn** | `process-score` | FR-067 — xem OQ-4 |
| Bản ghi âm · ảnh biểu đồ · tape đã đóng băng để đóng gói | `voice-journal` · `daily-journal` · `trade-replay` | FR-021 — **thiếu thì khôi phục về sẽ rỗng** |
| **Ranh giới với đường xoá riêng giọng nói** | `voice-journal` (FR-044) | FR-044, FR-026 — xem OQ-1 |
| Định nghĩa loại lỗi để render phần lỗi sai | `execution-learning` — **chưa có URD** | FR-070 |
| Menu an toàn làm chỗ mở báo cáo và cài đặt | `order-execution` (FR-052) | FR-063, FR-064 |
| Trình sửa playbook · trình sửa nguyên tắc để **dẫn sang** | `playbook-grading` · `daily-journal` | FR-051 — **không được dựng bản sao** |
| Mục bật/tắt của `tilt-meter` và `voice-journal` | `tilt-meter` (FR-043) · `voice-journal` (FR-052) | FR-045 — hai feature đó không có chỗ để tắt |

**Assumptions (tin là đúng — nêu hệ quả nếu sai):**

| Giả định | Invalidate {X} nếu sai |
|----------|------------------------|
| Xuất dữ liệu **chủ yếu để đưa cho trợ lý AI ngoài**, nên JSON là ưu tiên số một (URD A-01, **đã xác nhận**) | Ưu tiên đảo ngược: FR-013/FR-014 (CSV) cần thiết kế kỹ hơn FR-011/FR-012. **Ba tháng đầu không xuất lần nào thì chính giá trị của feature cần xem lại** |
| Bản xuất JSON **tự đủ nghĩa** (URD A-02) | FR-012 không đạt → **mục đích chính của việc xuất coi như hỏng**; xuất xong vẫn phải giải thích thủ công từng trường |
| Người chơi sao lưu **thủ công** và điều đó đủ an toàn (URD A-03 🔶) | Không sao lưu suốt nhiều tháng rồi mất sạch — **đúng rủi ro feature này sinh ra để chặn, nhưng bị chặn bởi chính quyết định không nhắc**. Bẫy tự kiểm ở Mục 7 |
| Ngưỡng cảnh báo dung lượng đặt được ở mức **đủ sớm** (URD A-04) | FR-053 vô dụng nếu quá muộn, thành tiếng ồn nếu quá sớm. **Cái hỏng đầu tiên là một buổi tối đang giao dịch.** Xem OQ-3 |
| Báo cáo lấy **đúng con số** deck đã chốt (URD A-05) | FR-009 sai → hai nơi lệch nhau, người chơi **mất niềm tin vào cả báo cáo lẫn deck** |
| Hai đường xoá là **độc lập, không đá nhau** (URD A-06) | FR-044, FR-026 sai → hoặc **xoá thiếu**, hoặc người chơi **tưởng đã xoá hết mà chưa**. Xem OQ-1 |
| Feature này ship **sau** chín feature nguồn (URD A-07) | Báo cáo và gói bao gồm phần chưa tồn tại — **dễ đọc nhầm một gói thiếu thành một gói đủ**. Đổi lại FR-023 giữ bản kê luôn đúng |
| Ba thước đo **kiểm được bằng công cụ sẵn có** (URD A-08 🔶) | Phải dựng thêm cơ chế đo → SC-01..03 thành **phạm vi phát sinh** chứ không phải cách kiểm chứng |

## 12. Open Questions

> **Số OQ đánh riêng cho từng tài liệu.** `OQ-3` của SRS này không nhất thiết là `OQ-3` của PRD cùng feature.
> Neo ổn định để đối chiếu là **số OQ của URD** ghi trong ngoặc *(kế thừa URD OQ-x)*.

* [ ] **OQ-1** *(kế thừa URD OQ-5, chung với `voice-journal` OQ-3)*: Đường **xoá sạch** ở đây và đường **xoá
  riêng giọng nói** của `voice-journal` phân định thế nào? Xoá sạch **gọi lại** đường kia hay tự xoá phần
  giọng nói? Hai lời xác nhận có **khác nhau đủ để không bấm nhầm**? Và vế thứ ba: `voice-journal` hứa "xoá
  là mất hẳn", nhưng **một gói sao lưu cũ khôi phục về sẽ mang giọng nói đó quay lại** — người chơi được nói
  điều này **ở đâu và lúc nào**, khi chính lời mời sao lưu ở FR-040 **tạo ra bản sao đó**?
  **Chặn FR-044, FR-026.** Em **không tạm quyết** — nó chạm nghĩa vụ về dữ liệu cá nhân.

* [x] **OQ-2** *(kế thừa URD OQ-2, chung với `daily-journal`)*: Mục *hạn giữ nhật ký* trong màn cài đặt
  mâu thuẫn với ràng buộc nhật ký **giữ vô hạn**.
  **Resolved 2026-08-29: bỏ hẳn mục *hạn giữ nhật ký*.** Lý do: nó mâu thuẫn với **hai** quyết định đã chốt (`daily-journal` giữ vô hạn · `voice-journal` bản ghi âm không tự hết hạn); phép tính dung lượng không ủng hộ nó (~20 phiên/tháng, chữ và ảnh không đáng kể, giọng nói "ở mức không đáng kể"); và thứ duy nhất phình thật là **tape** — mà tape nay thuộc `order-execution` nên hạn giữ tape là cấu hình của tape, không phải của nhật ký. Thay thế: **cảnh báo dung lượng + xoá thủ công**, vốn đã là thiết kế.
  **Đóng luôn** `daily-journal` OQ-5 và hai OQ gốc ở URD của cả hai feature.

* [ ] **OQ-3** *(kế thừa URD OQ-3)*: Ngưỡng cảnh báo dung lượng là bao nhiêu, và cảnh báo **hiện ở đâu**?
  Chỉ khi mở phần dữ liệu thì **có thể quá muộn**; hiện lên màn hình chính giữa phiên thì **vi phạm nguyên
  tắc màn hình chính chỉ có thứ cần cho việc giao dịch**. **Chặn FR-053.**
  *Ứng viên nháp để chốt nhanh:* cảnh báo khi chỗ trống còn đủ cho khoảng **20 phiên nữa**.

* [ ] **OQ-4** *(kế thừa URD OQ-8, chung với `process-score`)*: **Ai tính số tổng hợp cho một kỳ không phải
  một tháng trọn?** FR-001 hứa báo cáo cho một tuần và một khoảng ngày tuỳ chọn, nhưng `process-score` mới
  định nghĩa số tổng hợp ở mức **tháng** và **phiên**, còn `daily-journal` đã đẩy toàn bộ số liệu nhiều
  phiên sang đó. Mở rộng `process-score` cho kỳ tuỳ chọn, hay báo cáo kỳ tuỳ chọn **chỉ liệt kê con số cấp
  phiên**? **Feature này không được tự gộp** (BR-019). **Chặn FR-067.**

* [ ] **OQ-5** *(kế thừa URD OQ-9)*: Khôi phục có **đè các thiết lập hiện tại** không, và xoá sạch có xoá
  luôn chúng không? Nguồn đặt preference **cùng chỗ với dữ liệu nhật ký**, nên **cả hai thao tác đều chạm
  tới chúng**. Kịch bản thật: dựng máy chủ mới, khôi phục gói cũ, rồi **máy mới bị đặt lại theo hiệu chỉnh
  tay cầm của máy cũ**.
  🔶 **Tạm quyết:** chừng nào chưa chốt, FR-037 buộc việc khôi phục **nói rõ nó sẽ chạm vào những gì trước
  khi chạy**. *Cả hai câu đều không hoàn tác được.*

* [ ] **OQ-6** *(kế thừa URD OQ-4)*: Bản xuất có kèm **bản chép giọng nói** không, và có kèm chính **tệp âm
  thanh** không? Mục đích đã chốt là đưa cho trợ lý AI ngoài đọc — **bản chép làm bản xuất giàu nghĩa hơn
  hẳn**, nhưng nó cũng là **phần riêng tư nhất trong toàn bộ nhật ký**. Dù chốt thế nào, FR-016 buộc người
  chơi **biết trước khi xuất là trong tệp có gì**.

* [ ] **OQ-7** *(kế thừa URD OQ-1)*: Gói sao lưu có được **đặt mật khẩu hoặc mã hoá** không? Nó chứa dữ liệu
  giọng nói cá nhân và nằm trên máy người chơi, có thể chép sang ổ ngoài. Không mã hoá thì đơn giản hơn nhiều
  nhưng **bản ghi âm nằm trần trong một tệp ai cầm cũng mở được**.

* [ ] **OQ-8** *(kế thừa URD OQ-6)*: Khôi phục một gói cũ lên **phiên bản sản phẩm mới hơn** — nâng được tới
  mức nào? Gói cũ bao nhiêu phiên bản thì còn nâng được, và **quá mức đó thì sản phẩm nói gì**? Từ chối im
  lặng nghĩa là **một gói để lâu sẽ hết dùng được mà không ai biết trước**. Ảnh hưởng FR-036.

* [ ] **OQ-9** *(kế thừa URD OQ-7)*: Báo cáo cho một kỳ mà **trọng số các trục đã đổi giữa kỳ** — tính lại
  toàn bộ theo trọng số hiện tại, hay giữ nguyên con số lúc đó và ghi chú?
  🔶 **Tạm quyết:** **tính lại toàn bộ theo bộ hiện tại** (FR-071), nhất quán với `process-score` FR-040, và
  báo cáo **ghi rõ đang dùng bộ trọng số nào**.
  *Nếu sai:* một tệp trộn hai thước đo mà người đọc không biết.

---

> **Nguồn:** `reports-export-urd.md` (25 nhu cầu, 7 journey, **38 tình huống ngoại lệ** — nhiều nhất trong
> chín feature, 4 thước đo, 8 giả định) · `reports-export-prd.md` (18 capability) · bốn tài liệu nền
> `docs/_shared/` · ranh giới nhận từ **cả tám feature kia** cộng `execution-learning` (chưa có URD).
> **Chưa có BRD**.
>
> **🔶 Ba quyết định thay user:** OQ-2 (không bật mặc định cơ chế tự xoá), OQ-5 (khôi phục nói rõ chạm gì),
> OQ-9 (tính lại theo trọng số hiện tại). **OQ-1, OQ-4, OQ-6, OQ-7 em cố ý không quyết** — chúng chạm nghĩa
> vụ về dữ liệu cá nhân và ranh giới sở hữu giữa các feature.
>
> **Tầng 2–4 chưa sinh:** `reports-export-flows.md`, `-states.md`, `-erd.md`, use case, user story, AC.
