---
type: srs
feature: order-execution
status: draft
updated: 2026-08-28
links:
  - docs/order-execution/order-execution-urd.md
  - docs/order-execution/order-execution-prd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/ai-desk/ai-desk-urd.md
  - docs/playbook-grading/playbook-grading-urd.md
  - docs/tilt-meter/tilt-meter-urd.md
---

# order-execution — Software Requirements Specification

## 1. Scope

Đặc tả **đường đặt lệnh** của sản phẩm: từ lúc người chơi mở phiên và tự khai hạn mức, qua chuỗi vũ trang
— xác nhận hai tay — bắn, tới lúc biết chắc kết quả trên tài khoản demo cTrader; cộng với việc quản lý các
vị thế đang mở, sửa mức bảo vệ, và **luôn thoát ra được** kể cả khi tay cầm hoặc kết nối đã hỏng.

**Trong phạm vi:** vòng đời phiên và hạn mức tự đặt · **vòng đệm giá và việc đóng băng bối cảnh quanh mỗi lệnh** *(chuyển từ `trade-replay` sang 2026-08-29)* · chuỗi vũ trang/bắn với chốt an toàn hai tay · giải
quyết trạng thái kết quả lệnh (khớp / từ chối / chưa rõ) · đường thoát không phụ thuộc tay cầm · trạng thái
khoá và mở khoá · chọn và đóng vị thế · thông báo vị thế kết thúc ngoài ý muốn · bản xem trước sửa SL/TP ·
hiển thị theo đơn vị rủi ro · bộ đếm tự huỷ theo phiên · menu an toàn · phát hiện dữ liệu giá cũ.

**Ngoài phạm vi** (mỗi mục có feature sở hữu riêng): đo trạng thái tâm lý và ma sát thích ứng
(`tilt-meter`) · nghi thức chuẩn bị trước phiên và tự chấm 1–5 (`daily-journal`) · cộng dồn bộ đếm tự huỷ
qua nhiều phiên (`process-score`) · chấm điểm lệnh theo luật playbook (`playbook-grading`) · tư vấn, tín
hiệu, phân tích (`ai-desk`) · ghi âm lý do vào lệnh (`voice-journal`) · **màn tua lại** lệnh qua tape — feature này chỉ **sinh ra** tape, không hiển thị nó
(`trade-replay`) · báo cáo, xuất dữ liệu, sao lưu, màn cài đặt (`reports-export`) · giao dịch tiền thật,
lệnh chờ, đóng một phần vị thế.

> **Ranh giới kiến trúc bất di bất dịch** (`docs/_shared/system-overview.md`): **gateway là thành phần duy
> nhất được phép duyệt một lệnh demo.** Tay cầm và ứng dụng Chrome chỉ **chuẩn bị ý định** (intent).
> Spotware — không phải VPS — là matching engine thật. Không requirement nào trong tài liệu này được mô tả
> như thể client tự đặt được lệnh.

## 2. Actors & Stakeholders

| Actor | Loại | Mục tiêu | Trong scope? |
|-------|------|----------|--------------|
| **Người chơi** | người | Vào và ra khỏi vị thế demo một cách an toàn, biết chắc trạng thái, và không bao giờ vào một lệnh mình không chủ động quyết định | Có — actor chính, duy nhất |
| **Ứng dụng Chrome** | hệ thống | Đọc tay cầm, dựng trạng thái ARM, hiển thị HUD, gửi intent lên gateway | Có |
| **Gateway** | hệ thống | Thành phần **duy nhất** duyệt một lệnh: kiểm hạn mức rủi ro, cấp `cid`, rồi tự gửi sang cTrader Open API | Có |
| **Broker link** | hệ thống | Kết nối cTrader Open API bên trong gateway, dịch lệnh đã duyệt sang thông điệp Open API | Có — ranh giới, không đặc tả nội bộ |
| **Sàn cTrader / Spotware** | ngoài | Matching engine thật; nguồn sự thật cho giá khớp, vị thế, lãi lỗ | Có — là nguồn đối chiếu |
| **Tay cầm 8BitDo Ultimate 2** | ngoài | Thiết bị nhập chính, qua dongle 2.4G | Có — ranh giới |
| **AI desk** | hệ thống | Quan sát và tư vấn bên lề | **Không** — chỉ nhận ràng buộc "không bao giờ chạm đường đặt lệnh" |
| **`playbook-grading`** | hệ thống | Cấp nội dung điểm luật hiện trên màn xác nhận | **Không** — chỉ là ranh giới tích hợp |
| **`tilt-meter`** | hệ thống | Thêm ma sát lên việc **mở** lệnh ở mức nóng/quá nóng | **Không** — chỉ nhận ràng buộc không chạm đường thoát |

## 3. Functional Requirements (FR)

### 3.1 Phiên giao dịch và hạn mức tự đặt

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-order-execution-001 | Kiểm tra sẵn sàng trước khi mở phiên | Trước khi cho mở phiên, hệ thống kiểm: kết nối tới sàn, phiên đăng nhập còn hạn, và tài khoản là **demo**. Bất kỳ điều kiện nào không đạt → từ chối mở phiên, nêu **lý do cụ thể** và việc cần làm tiếp; **không** vào trạng thái nửa vời trông như đã sẵn sàng | P0 | demo | PRD CAP-01 · URD Mục 6 |
| FR-order-execution-002 | Khai hạn mức **thi hành** cho phiên | Người chơi khai bốn hạn mức được hệ thống **từ chối hành động vượt quá**: khung giờ phiên, khối lượng tối đa mỗi lệnh, số vị thế mở tối đa, mức lỗ tối đa của phiên | P0 | demo | URD UN-004 |
| FR-order-execution-003 | Khai ngưỡng **chỉ cảnh báo** | Người chơi khai ngưỡng báo trước sự kiện tin. Hệ thống **nói rõ nhưng không bao giờ từ chối** một lệnh vì nó. Chưa khai → mặc định **15 phút** | P0 | demo | URD UN-004 · `ai-desk` UN-002 |
| FR-order-execution-004 | Validate hạn mức khi lưu | Chặn khi lưu và nêu rõ chỗ sai: khung giờ nhập ngược (kết thúc trước bắt đầu); ngưỡng cảnh báo tin bằng 0, âm, hoặc dài hơn cả phiên | P0 | test | URD Mục 6 |
| FR-order-execution-005 | Sửa hạn mức giữa phiên | Mỗi ô hạn mức xét **độc lập**. Sửa theo hướng **siết chặt** có hiệu lực ngay và chỉ chi phối hành động mới. Sửa theo hướng **nới lỏng** chỉ có hiệu lực từ phiên sau. Với ngưỡng cảnh báo tin: ngưỡng **dài hơn** là siết (áp ngay), ngắn hơn là nới (áp phiên sau) | P0 | test | URD UN-004 (OQ-2 resolved) · `ai-desk` UN-002 |
| FR-order-execution-006 | Siết hạn mức không ép đóng vị thế | Hạ khối lượng tối đa hoặc số vị thế tối đa xuống dưới trạng thái đang có → hạn mức mới chỉ chi phối **hành động mới**; vị thế đang có **không** bị ép đóng. Hệ thống nói rõ điều đó ngay lúc lưu | P0 | test | URD Mục 6 |
| FR-order-execution-007 | Kết thúc phiên | Phiên kết thúc khi người chơi **tự đóng** hoặc khi **hết khung giờ đã đặt**. Hạn mức được đặt lại ở phiên kế tiếp | P0 | demo | URD UN-004 (OQ-1 resolved) |
| FR-order-execution-008 | Hết khung giờ khi còn vị thế mở | Chuyển sang trạng thái **chỉ-được-đóng** và cảnh báo rõ còn vị thế mở. Hệ thống **không** tự đóng thay người chơi. Phiên chỉ thực sự kết thúc khi không còn vị thế nào | P0 | test | URD Mục 6 |
| FR-order-execution-009 | Từ chối mở lệnh khi chạm hạn mức thi hành | Từ chối mở lệnh mới khi: ngoài khung giờ phiên, đã chạm mức lỗ tối đa, khối lượng vượt trần, hoặc đã đạt số vị thế tối đa. Nêu rõ **đã chạm hạn mức nào**. Đóng vị thế đang có **vẫn luôn được phép** | P0 | test | URD UN-010 |
| FR-order-execution-010 | Validate khối lượng trước khi vũ trang | Chặn ngay tại chỗ **trước khi ARM** khi khối lượng dưới mức tối thiểu của sàn, sai bước nhảy của sàn, hoặc vượt hạn mức người chơi tự đặt. Nêu rõ giới hạn hợp lệ là bao nhiêu | P0 | test | URD Mục 6 |

### 3.2 Chuỗi vũ trang → xác nhận → bắn

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-order-execution-011 | Chốt an toàn cấp một (clutch) | Không có gì được phát ra nếu người chơi không đang giữ `LT`. Nhả clutch ở bất kỳ điểm nào của chuỗi → huỷ trạng thái vũ trang | P0 | test | Definitions · URD UN-001 |
| FR-order-execution-012 | Vũ trang một hướng | Trong lúc giữ clutch, `A` vũ trang hướng mua, `B` vũ trang hướng bán. Trạng thái vũ trang **không gửi gì đi** | P0 | demo | URD UN-001 |
| FR-order-execution-013 | Màn xác nhận trước thao tác cuối | Khi vũ trang, hệ thống hiện bản tóm tắt lệnh sắp gửi: cặp, hướng, khối lượng, mức bảo vệ dự kiến, và rủi ro tương ứng theo đơn vị R | P0 | demo | URD Journey 1 |
| FR-order-execution-014 | Xác nhận hai tay để bắn | Lệnh chỉ được gửi khi người chơi giữ clutch và bấm `RT` (`LT+RT`). Đây là cặp xác nhận bắt buộc, không có đường tắt nào | P0 | test | Definitions · URD UN-001 |
| FR-order-execution-015 | Một xác nhận sinh đúng một lệnh | Một lần xác nhận sinh đúng một intent và đúng một vị thế. Giữ nút lâu **không** phát sinh hàng loạt lệnh; bấm xác nhận hai lần do sốt ruột **không** sinh thêm vị thế thứ hai | P0 | test | URD UN-001 · Mục 6 |
| FR-order-execution-016 | Cần analog không bao giờ gửi lệnh | Cần analog chỉ đổi **bản xem trước**. Không tồn tại trạng thái nào mà cần analog phát ra được một lệnh, kể cả khi bị trôi lúc để yên | P0 | test | URD UN-001 |
| FR-order-execution-017 | Huỷ vũ trang **chủ động** | Nhả clutch hoặc bấm huỷ trong lúc còn giữ quyền quyết định → trạng thái vũ trang biến mất, không có gì được gửi đi, và bộ đếm tự huỷ **tăng thêm một** | P0 | demo | URD UN-006 · Journey 3 |
| FR-order-execution-018 | Huỷ vũ trang **bị động** | Mất tay cầm, mất focus cửa sổ, mở menu an toàn, hoặc `tilt-meter` bắt đầu một khoảng khoá → trạng thái vũ trang bị huỷ ngay, và bộ đếm tự huỷ **không tăng** | P0 | test | URD UN-006 · `tilt-meter` Mục 6 |
| FR-order-execution-019 | Bấm nhầm tổ hợp nút vai | Bấm nhầm cặp nút vai khi định đổi khung thời gian: xấu nhất chỉ đổi khung nhìn biểu đồ — không bao giờ ảnh hưởng tới một vị thế | P0 | test | URD Mục 6 |
| FR-order-execution-020 | Ghi lại mỗi lần xác nhận hai tay | Mỗi lần xác nhận được ghi lại kèm dấu thời gian, đủ để đối chiếu một-đối-một với số lệnh trên cTrader demo | P0 | kiểm tra | PRD M1 · URD USC-001 |

### 3.3 Kết quả lệnh

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-order-execution-021 | Ba trạng thái kết quả dứt khoát | Sau khi gửi, mỗi lệnh ở đúng một trong ba trạng thái và trạng thái đó luôn đọc được: **đã khớp**, **bị từ chối**, hoặc **chưa rõ**. Không tồn tại trạng thái thứ tư và không có khoảng lặng | P0 | test | URD UN-002 |
| FR-order-execution-022 | Phản hồi khi khớp | Khi khớp: rung tay cầm và hiển thị xác nhận. Phản hồi này **độc lập** với mọi feature khác và không bao giờ chờ chúng | P0 | demo | URD Journey 1 · `ai-desk` UN-013 |
| FR-order-execution-023 | Xử lý trạng thái "chưa rõ" | Đã gửi mà không có phản hồi trong thời gian hợp lý → nói rõ **"chưa rõ kết quả"**, **không đoán bừa**, và **khoá việc mở lệnh mới**. Đóng vị thế và thoát khẩn cấp vẫn được phép | P0 | test | URD UN-002 |
| FR-order-execution-024 | Tự gỡ trạng thái "chưa rõ" | Khi kết nối ổn định, hệ thống tự đối chiếu với sàn và trạng thái cuối cùng tự hiện ra. Người chơi **không phải tự đi kiểm tra** | P0 | test | URD UN-002 (OQ-3 resolved) |
| FR-order-execution-025 | Chủ động bỏ qua trạng thái "chưa rõ" | Người chơi bỏ qua được để mở lại quyền bắn, **sau một cảnh báo nêu rõ rủi ro có hai vị thế thay vì một**. Mỗi lần bỏ qua được ghi lại | P0 | demo | URD UN-002 (OQ-3 resolved) |
| FR-order-execution-026 | Đối chiếu lại sau khi nối lại kết nối | Khi kết nối trở lại, hệ thống hiển thị đúng tình trạng vị thế **thật trên sàn**, kể cả khi nó đã thay đổi trong lúc mất kết nối | P0 | test | URD Journey 4 |

### 3.4 Đường thoát

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-order-execution-027 | Thoát khẩn cấp trên tay cầm | `Y` đóng **toàn bộ** vị thế ngay, rồi khoá phiên | P0 | demo | Definitions · URD UN-003 |
| FR-order-execution-028 | Đường thoát không cần tay cầm | Nút thoát trên màn hình dùng được bằng chuột hoặc bàn phím, **không phụ thuộc tay cầm**. Đây là đường thoát chính khi dongle bị rút hoặc pin hết | P0 | demo | URD UN-003 (A-02) |
| FR-order-execution-029 | Đường thoát không bao giờ bị chặn | Lệnh **đóng** và **thoát khẩn cấp** không bao giờ bị chặn, làm chậm, hay thêm bước bởi bất kỳ cơ chế nào: hạn mức, trạng thái khoá, trạng thái "chưa rõ", menu an toàn, màn xem lại, hay ma sát của `tilt-meter`. **Không tồn tại cấu hình nào bật được việc cản đường thoát** | P0 | test | URD UN-003 · `tilt-meter` UN-001 · `trade-replay` UN-002 |
| FR-order-execution-030 | Thoát khi không có vị thế nào | Bấm đóng hoặc thoát khẩn cấp khi không có vị thế → xác nhận nhẹ nhàng "không có gì để đóng"; **không** báo lỗi và **không** đổi trạng thái khoá ngoài dự kiến | P0 | test | URD Mục 6 |
| FR-order-execution-031 | Xác nhận sau khi thoát | Sau thoát khẩn cấp, người chơi thấy xác nhận rằng không còn vị thế nào đang mở, và thấy rõ mình đang ở trạng thái khoá | P0 | demo | URD Journey 2 |

### 3.5 Trạng thái khoá

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-order-execution-032 | Tự khoá và mở khoá phiên | `View` khoá phiên giữa chừng, và mở khoá lại được trong cùng phiên bằng một thao tác **có chủ ý** | P0 | demo | URD UN-011 |
| FR-order-execution-033 | Mở khoá không đặt lại hạn mức đã tiêu | Ra khỏi trạng thái khoá **không** xoá các ràng buộc đã tự đặt: lỗ đã lỗ, thời gian đã trôi | P0 | test | URD UN-011 |
| FR-order-execution-034 | Trạng thái khoá nói rõ cái gì còn dùng được | Mọi trạng thái khoá hiện rõ **vì sao** đang khoá và **cái gì vẫn dùng được** — tối thiểu là đóng vị thế và thoát khẩn cấp | P0 | demo | URD UN-011 · Journey 4 |
| FR-order-execution-035 | Nêu mọi lý do khoá đang có hiệu lực | Khi nhiều cơ chế cùng chạm việc mở lệnh, màn hình nêu **mọi** lý do đang có hiệu lực, không giấu bớt cái nào; và phân biệt rõ **hạn mức** (luật do chính người chơi đặt) với **ma sát** (một nhận định về trạng thái, thuộc `tilt-meter`) | P0 | demo | `tilt-meter` Mục 6 |

### 3.6 Quản lý vị thế

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-order-execution-036 | Danh sách vị thế đang mở | Hiển thị danh sách các vị thế đang mở; **vị thế đang được chọn** hiện rõ ràng | P0 | demo | URD UN-013 |
| FR-order-execution-037 | Nêu rõ đích tác động trước xác nhận | Mọi thao tác đóng hoặc sửa bảo vệ đều nêu rõ nó áp cho **vị thế nào** trước khi người chơi xác nhận | P0 | demo | URD UN-013 |
| FR-order-execution-038 | Đóng một vị thế đã chọn | Đóng hoàn toàn đúng vị thế đang chọn; các vị thế còn lại nguyên vẹn. Kết quả hiện theo đơn vị R | P0 | demo | URD Journey 5 |
| FR-order-execution-039 | Thông báo vị thế kết thúc ngoài ý muốn | Vị thế chạm cắt lỗ, chạm chốt lời, hoặc bị sàn đóng → thông báo **ngay** khi vị thế biến mất, kèm **lý do** và **kết quả**. Người chơi không phải tự phát hiện | P0 | test | URD UN-012 |
| FR-order-execution-040 | Thao tác lên vị thế không còn tồn tại | Xác nhận đóng hoặc sửa cho một vị thế **đã không còn** → nói rõ **"vị thế không còn"** và vì sao, thay vì im lặng hoặc báo lỗi mơ hồ | P0 | test | URD UN-012 |
| FR-order-execution-041 | Khái niệm "vị thế đang chọn" dùng chung | Khái niệm này là **hợp đồng liên feature**: `voice-journal` gắn memo vào vị thế đang chọn, `playbook-grading` và `trade-replay` tham chiếu tới nó. Feature này là nơi **duy nhất** định nghĩa và thay đổi nó | P0 | kiểm tra | `voice-journal` UN-004 |

### 3.7 Sửa mức bảo vệ (SL/TP)

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-order-execution-042 | Sửa chỉ tạo bản xem trước | Thao tác chỉnh SL/TP chỉ **dàn sẵn một bản xem trước**; nó **chưa được gửi đi** | P1 | test | URD UN-007 |
| FR-order-execution-043 | Bản xem trước hiện rủi ro tương ứng | Trong lúc chỉnh, màn hình cho thấy rủi ro và mục tiêu tương ứng thay đổi theo | P1 | demo | URD Journey 6 |
| FR-order-execution-044 | Áp bản xem trước cần xác nhận hai tay | Bản xem trước chỉ tới sàn sau một lần xác nhận `LT+RT` riêng, thực hiện ở màn chính | P1 | test | URD UN-007 · Definitions |
| FR-order-execution-045 | Validate mức bảo vệ tại bản xem trước | Chặn **tại bản xem trước** và nói rõ vì sao khi mức bảo vệ đặt về phía sai hoặc quá sát giá hiện tại — trước khi tới bước xác nhận | P1 | test | URD Mục 6 |

### 3.8 Hiển thị và bộ đếm

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-order-execution-046 | Lãi lỗ theo đơn vị rủi ro làm mặc định | Trạng thái vị thế và kết quả đóng lệnh hiển thị theo **đơn vị rủi ro (R)** làm mặc định | P0 | demo | URD UN-005 |
| FR-order-execution-047 | Tiền nằm sau một thao tác có chủ ý | Con số tiền chỉ hiện sau một thao tác bật có chủ ý; nó **không** xuất hiện ở trạng thái mặc định của bất kỳ màn nào thuộc feature này | P0 | kiểm tra | URD UN-005 · README |
| FR-order-execution-048 | Bộ đếm tự huỷ theo phiên | Bộ đếm số lần tự huỷ chủ động hiển thị nổi bật trên màn chính — là con số lớn nhất sau giá — tăng dần trong phiên, và **đặt lại ở phiên kế tiếp** | P0 | demo | URD UN-006 (OQ-4 resolved) · Definitions |
| FR-order-execution-049 | Ghi kèm cờ "điều kiện đứng ngoài" | Mỗi lần tự huỷ được ghi kèm **lúc đó có điều kiện đứng ngoài hay không**, để `process-score` quy điểm trên tập con mà không cần bộ đếm thứ hai. Bộ đếm hiển thị vẫn giữ **luật rộng**: đếm mọi lần tự huỷ chủ động | P0 | kiểm tra | URD UN-006 · `process-score` UN-008 (OQ-3 resolved) |
| FR-order-execution-050 | Đánh dấu dữ liệu giá cũ và chặn mở lệnh | Giá ngừng cập nhật dù kết nối vẫn còn → đánh dấu rõ dữ liệu giá là **cũ** và **chặn mở lệnh mới** cho tới khi giá sống lại | P0 | test | URD Mục 6 |
| FR-order-execution-051 | Chưa có dữ liệu giá lúc vừa mở phiên | Nói rõ đang **chờ dữ liệu**; mở lệnh bị chặn cho tới khi có giá. **Không** hiển thị giá bịa | P0 | test | URD Mục 6 |

### 3.9 Menu an toàn và mất kết nối

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-order-execution-052 | Mở menu an toàn huỷ ARM và khoá mở lệnh | Mở `GameOverlay` bằng `Menu` → huỷ trạng thái vũ trang và khoá việc mở lệnh mới cho tới khi đóng lại. Người chơi thấy rõ điều đó ngay lúc mở | P0 | test | URD UN-009 · Operating environment (ràng buộc 4) |
| FR-order-execution-053 | Điều hướng trong menu không phát ra lệnh | Không thao tác điều hướng hay áp preference nào trong menu phát ra được lệnh mở hoặc lệnh sửa. Hợp đồng điều hướng chung: D-pad chọn đích, `LB/RB` đổi tab, `A` vào/áp dụng, `B` quay lại, `Menu` thoát | P0 | test | URD UN-009 · Definitions |
| FR-order-execution-054 | Mất tay cầm | Rút dongle hoặc hết pin → huỷ trạng thái vũ trang **ngay, không chờ**; báo mất tay cầm; đường thoát bằng chuột/phím hiện rõ | P0 | test | URD Mục 6 |
| FR-order-execution-055 | Mất focus cửa sổ | Tab mất focus → huỷ trạng thái vũ trang ngay; khoá mở lệnh mới; quay lại thấy rõ mình bị khoá và vì sao | P0 | test | URD Mục 6 · Operating environment |
| FR-order-execution-056 | Kết nối im lặng quá ngưỡng | Im lặng quá ngưỡng khi đang có vị thế → tự khoá mở lệnh mới; đóng vị thế và thoát khẩn cấp vẫn được phép | P0 | test | URD Mục 6 |
| FR-order-execution-057 | Sàn bảo trì hoặc không phản hồi | Báo trạng thái bảo trì và khoá mở lệnh; **không** hiển thị giá bịa | P0 | test | URD Mục 6 |
| FR-order-execution-058 | Chọn cặp, khối lượng, khung thời gian bằng tay cầm | Người chơi đổi được cặp giao dịch, khối lượng và khung thời gian biểu đồ hoàn toàn bằng tay cầm, không phải chuyển sang chuột | P1 | demo | URD UN-008 (dựa A-06) |

### 3.10 Vòng đệm giá và đóng băng bối cảnh

> **Chuyển từ `trade-replay` sang 2026-08-29.** Lý do: `phase-02` vốn đã đặt vòng đệm ở đây; một vòng đệm
> chạy liên tục trên luồng giá **là** đang ở trên order socket, mà `system-overview.md` cấm journal path đi
> trên đó; luồng giá đã nằm sẵn trong tiến trình này nên không cần người đăng ký thứ hai; và **tape tích luỹ
> từ phiên đầu tiên** thay vì chỉ tồn tại từ ngày `trade-replay` ship (thứ bảy trong chín feature).
> Feature này **sinh ra** tape; `trade-replay` **đọc** nó.

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-order-execution-059 | Vòng đệm giá chạy liên tục trong phiên | Giữ dữ liệu giá gần đây trong bộ nhớ suốt phiên, đủ để cắt ra cửa sổ quanh một lệnh khi cần | P0 | test | `phase-02` · `trade-replay` UN-014 |
| FR-order-execution-060 | Đóng băng bối cảnh **tự động khi lệnh đóng** | Cắt và lưu cửa sổ quanh mỗi lệnh. Người chơi **không phải bật, không phải nhớ, không phải bấm gì** | P0 | test | `trade-replay` UN-014 |
| FR-order-execution-061 | Cửa sổ mặc định và mốc thu | **5 phút trước lúc mở, 5 phút sau lúc đóng**; việc đóng băng chạy tại `closed_at + post_roll`. Cả hai là **cấu hình** | P0 | kiểm tra | `trade-replay` UN-001 — xem OQ-9 |
| FR-order-execution-062 | Buổi không có lệnh nào thì **không lưu gì cả** | Không có kho dữ liệu nào phình ra sau một tối đứng ngoài. Và **không lưu bối cảnh cho một lần đứng ngoài** không dẫn tới lệnh — lần tự huỷ chỉ hiện lại khi nó rơi vào cửa sổ quanh một lệnh có thật | P0 | test | `trade-replay` UN-014 · Mục 3 |
| FR-order-execution-063 | Trạng thái thu và hạn giữ tape đọc được từ ngoài | Feature khác phân biệt được **đang thu nốt** · **đủ** · **cụt đuôi** · **quá hạn giữ**; và hạn giữ tape là **cấu hình của tape**, không phải của nhật ký | P0 | kiểm tra | `trade-replay` FR-025..029 — xem OQ-10 |

## 4. Non-Functional Requirements (NFR)

| ID | Category | Requirement | Priority | Acceptance |
|----|----------|-------------|----------|------------|
| NFR-order-execution-001 | performance | Từ lúc đọc tay cầm tới lúc dựng xong intent: **< 16 ms** | P0 | Đo trên máy người chơi, đọc phân vị 95 qua một phiên thật |
| NFR-order-execution-002 | performance | Gateway kiểm hạn mức rủi ro: **< 5 ms** | P0 | Đo tại gateway, phân vị 95 |
| NFR-order-execution-003 | performance | Chặng nhà → VPS **15–80 ms là điều kiện sống chung, không phải lỗi**. Không NFR nào được viết dựa trên giả định gateway đặt gần sàn | P0 | phân tích — soát lại mọi NFR khác không mâu thuẫn dòng này |
| NFR-order-execution-004 | performance | Phản hồi rung và xác nhận khớp lệnh đến **trước** và **độc lập** với mọi nội dung của `ai-desk`, `playbook-grading`, `voice-journal` | P0 | Quan sát thứ tự (không bấm giờ): rung luôn xuất hiện trước bất kỳ chữ nào của feature khác; chạy hai lần — một lần các feature kia chạy, một lần offline — thời điểm rung như nhau |
| NFR-order-execution-005 | reliability | Đường thoát hoàn tất **trong vòng 10 giây** kể từ lúc người chơi quyết định thoát, trong mọi tình huống sự cố đã liệt kê | P0 | Diễn tập hằng tháng: rút dongle / ẩn tab / ngắt mạng khi đang có vị thế, bấm thoát và bấm giờ |
| NFR-order-execution-006 | reliability | Một lần xác nhận hai tay ↔ đúng một vị thế trên sàn. Quan hệ này là **một-đối-một tuyệt đối**, không có ngoại lệ | P0 | Đối chiếu hằng tháng số lệnh cTrader demo với bản ghi xác nhận; một lệnh lệch là sự cố nghiêm trọng |
| NFR-order-execution-007 | reliability | Việc gửi intent là **idempotent theo `cid`**: gửi lại cùng một `cid` không bao giờ tạo vị thế thứ hai | P0 | test — bấm xác nhận hai lần liên tiếp, kiểm cTrader demo chỉ có một vị thế |
| NFR-order-execution-008 | security | Chỉ tài khoản **demo**. Cấu hình trỏ tới tài khoản thật → sản phẩm **không khởi động** và nói rõ vì sao | P0 | test — dựng cấu hình sai, kiểm sản phẩm từ chối khởi động |
| NFR-order-execution-009 | security | **Không tồn tại đường nào** để `ai-desk`, tín hiệu ngoài, hay giọng nói phát ra một lệnh. Cấu hình cấp quyền đặt lệnh cho AI hoặc gán cử chỉ nói vào nút thuộc đường đặt lệnh → sản phẩm **không khởi động** | P0 | test | `ai-desk` UN-003, UN-012 · `voice-journal` UN-014 |
| NFR-order-execution-010 | availability | Mọi feature bên lề (AI desk, chấm luật, nhật ký, chấm điểm, tua lại) **chết hoàn toàn** vẫn không làm giảm khả năng mở, đóng, và thoát vị thế | P0 | Diễn tập hằng tháng: gỡ khoá truy cập AI rồi chạy trọn chuỗi mở phiên → vào lệnh → đóng lệnh |
| NFR-order-execution-011 | usability | Người chơi thực hiện được trọn bộ thao tác một phiên trên tay cầm; **danh sách này là đóng**: chọn cặp, khối lượng, khung thời gian, vũ trang, bắn, huỷ, chọn vị thế, đóng vị thế, thoát khẩn cấp, khoá/mở khoá phiên, mở menu, mở bàn làm việc AI | P1 | demo — chạy một phiên đầy đủ không chạm chuột |
| NFR-order-execution-012 | usability | Giao diện sản phẩm bằng **tiếng Anh**; tài liệu nghiệp vụ bằng tiếng Việt | P0 | kiểm tra |
| NFR-order-execution-013 | compatibility | Chỉ **Chrome desktop**. Rung tay cầm có thể không có trên trình duyệt khác — khi đó **phản hồi bằng hình ảnh là chính thức** | P0 | kiểm tra |
| NFR-order-execution-014 | compatibility | Tay cầm nối qua **dongle 2.4G** là đường chính, **dây USB** là dự phòng. **Bluetooth không dùng** (Ultimate 2 cần macOS 26+) | P0 | kiểm tra |
| NFR-order-execution-015 | auditability | Mọi lần xác nhận, mọi lần tự huỷ (kèm cờ điều kiện đứng ngoài), mọi lần bỏ qua trạng thái "chưa rõ", và mọi lần đổi trạng thái khoá được ghi lại kèm dấu thời gian | P0 | kiểm tra — đủ để tính M1, M2, M4, M5 mà không cần trí nhớ |
| NFR-order-execution-016 | compliance | Mọi bề mặt giữ dòng chữ **demo / giải trí / không phải lời khuyên đầu tư** | P0 | kiểm tra | Project profile — Compliance |

## 5. Business Rules

| ID | Rule | Trigger | Implements FR | Source |
|----|------|---------|---------------|--------|
| BR-order-execution-001 | Gateway là thành phần **duy nhất** duyệt một lệnh demo; client chỉ chuẩn bị intent | Mọi lần bắn | FR-014, FR-021 | `system-overview.md` |
| BR-order-execution-002 | Sửa hạn mức theo hướng **siết** áp ngay và chỉ chi phối hành động mới; theo hướng **nới** áp từ phiên sau. Mỗi ô xét độc lập | Lưu hạn mức giữa phiên | FR-005, FR-006 | URD OQ-2 resolved |
| BR-order-execution-003 | Với ngưỡng cảnh báo tin, **ngưỡng dài hơn = siết** (báo sớm hơn), ngắn hơn = nới | Lưu ngưỡng cảnh báo tin | FR-005 | `ai-desk` OQ-2 resolved |
| BR-order-execution-004 | Bộ đếm tự huỷ chỉ đếm **quyết định của người chơi**. Huỷ do mất tay cầm, mất focus, mở menu, hoặc do `tilt-meter` bắt đầu khoá **không** được đếm | Mọi lần trạng thái vũ trang biến mất | FR-017, FR-018 | URD UN-006 · `tilt-meter` Mục 6 |
| BR-order-execution-005 | Nhả sớm nút xác nhận khi đang bị siết thao tác (mức nóng của `tilt-meter`) **không** tính là một lần tự huỷ — nhả tay giữa chừng không phải một quyết định không-vào | Nhả `RT` trước khi đủ thời gian giữ | FR-018 | `tilt-meter` A-13 (🔶) |
| BR-order-execution-006 | Mở khoá phiên **không** đặt lại hạn mức đã tiêu: lỗ đã lỗ, thời gian đã trôi | Mở khoá trong cùng phiên | FR-033 | URD UN-011 |
| BR-order-execution-007 | Hạn mức gắn với **phiên** và đặt lại ở phiên kế tiếp. Trần lỗ theo **ngày** chưa tồn tại — xem OQ-1 | Mở phiên mới | FR-007 | URD OQ-1 resolved · OQ-5 open |
| BR-order-execution-008 | Luật **playbook không bao giờ chặn được một lệnh**; chỉ hạn mức rủi ro mới chặn được. Không có cách nào khai một luật playbook thành luật chặn | Mọi lần bắn có playbook đang dùng | FR-009 | `playbook-grading` UN-002 |
| BR-order-execution-009 | Ma sát của `tilt-meter` chỉ áp cho **mở lệnh mới**. Đóng vị thế, thoát khẩn cấp, nút thoát trên màn hình và tự khoá phiên **không bao giờ** bị chạm | Chỉ số tâm lý ở mức nóng hoặc quá nóng | FR-029 | `tilt-meter` UN-001 |
| BR-order-execution-010 | Hết khung giờ khi còn vị thế mở → **chỉ-được-đóng**; hệ thống không tự đóng thay người chơi. Phiên chỉ kết thúc khi không còn vị thế nào | Đồng hồ chạm mốc kết thúc khung giờ | FR-008 | URD Mục 6 |
| BR-order-execution-011 | Siết hạn mức xuống dưới trạng thái đang có **không** ép đóng vị thế; chỉ chi phối hành động mới | Lưu hạn mức thấp hơn trạng thái hiện tại | FR-006 | URD Mục 6 |
| BR-order-execution-012 | Trạng thái "chưa rõ" khoá **mở lệnh mới**, không bao giờ khoá đóng lệnh hay thoát khẩn cấp | Không nhận được phản hồi trong thời gian hợp lý | FR-023, FR-029 | URD UN-002 |
| BR-order-execution-013 | **Feature này sinh ra tape; `trade-replay` đọc nó.** Vòng đệm chạy trên luồng giá của đường đặt lệnh — journal path không được đăng ký luồng đó | Suốt phiên | FR-059..FR-063 | `system-overview.md` (chốt 2026-08-29) |
| BR-order-execution-014 | Buổi không lệnh nào **không lưu tape**; lần đứng ngoài ngoài cửa sổ mọi lệnh cũng không lưu | Kết thúc phiên · lần tự huỷ | FR-062 | `trade-replay` Mục 3 |

## 6. Error Matrix

| Error ID | Title | Trigger | Severity | Related FR | Screen state | Recovery |
|----------|-------|---------|----------|------------|--------------|----------|
| E-order-execution-001 | Không mở được phiên — tài khoản chưa sẵn sàng | Chưa kết nối được sàn, phiên đăng nhập hết hạn, hoặc tài khoản không phải demo | critical | FR-001 | Màn mở phiên, nêu lý do cụ thể | Nêu rõ việc cần làm tiếp; **không** vào trạng thái nửa vời trông như đã sẵn sàng |
| E-order-execution-002 | Chưa có dữ liệu giá | Vừa mở phiên, chưa nhận được giá | major | FR-051 | HUD hiện "đang chờ dữ liệu", mở lệnh bị chặn | Tự gỡ khi có giá; không hiển thị giá bịa |
| E-order-execution-003 | Dữ liệu giá đã cũ | Giá ngừng cập nhật dù kết nối vẫn còn | **critical** | FR-050 | Đánh dấu rõ giá là cũ; mở lệnh bị chặn | Tự gỡ khi giá sống lại. Nguy hiểm hơn mất kết nối vì màn hình trông vẫn bình thường |
| E-order-execution-004 | Kết quả lệnh chưa rõ | Đã gửi, không có phản hồi trong thời gian hợp lý | **critical** | FR-023, FR-024, FR-025 | Nói rõ "chưa rõ kết quả"; mở lệnh mới bị khoá; đóng và thoát vẫn được | Tự đối chiếu với sàn khi kết nối ổn định; hoặc người chơi chủ động bỏ qua sau cảnh báo rủi ro hai vị thế |
| E-order-execution-005 | Lệnh bị từ chối | Gateway hoặc sàn từ chối | major | FR-021 | Nêu rõ lý do từ chối | Người chơi sửa điều kiện rồi vũ trang lại |
| E-order-execution-006 | Mất tay cầm | Rút dongle hoặc hết pin | **critical** | FR-054 | Huỷ ARM ngay; báo mất tay cầm; đường thoát chuột/phím hiện rõ | Cắm lại dongle hoặc dùng dây USB; bộ đếm tự huỷ **không** tăng |
| E-order-execution-007 | Mất focus cửa sổ | Tab bị ẩn hoặc mất focus | major | FR-055 | Huỷ ARM; khoá mở lệnh mới; nêu rõ vì sao | Quay lại focus cửa sổ; bộ đếm tự huỷ **không** tăng |
| E-order-execution-008 | Kết nối im lặng quá ngưỡng | Không có tin hiệu từ gateway quá ngưỡng khi đang có vị thế | **critical** | FR-056 | Khoá mở lệnh mới; đóng và thoát vẫn được | Tự gỡ khi kết nối ổn định lại |
| E-order-execution-009 | Sàn bảo trì hoặc không phản hồi | Sàn báo bảo trì, hoặc không trả lời | major | FR-057 | Báo trạng thái bảo trì; khoá mở lệnh; **không** hiển thị giá bịa | Chờ sàn trở lại |
| E-order-execution-010 | Chạm mức lỗ tối đa của phiên | Tổng lỗ phiên chạm hạn mức đã khai | major | FR-009 | Từ chối mở lệnh mới, nêu rõ đã chạm hạn mức nào | Đóng vị thế vẫn được phép; hạn mức đặt lại ở phiên sau |
| E-order-execution-011 | Ngoài khung giờ phiên | Đồng hồ ngoài khung giờ đã tự đặt | major | FR-009 | Từ chối mở lệnh mới kèm lý do | Đóng vị thế vẫn được phép |
| E-order-execution-012 | Hết khung giờ khi còn vị thế mở | Đồng hồ chạm mốc kết thúc, vẫn còn vị thế | major | FR-008 | Chuyển chỉ-được-đóng; cảnh báo rõ còn vị thế mở | **Không** tự đóng thay người chơi; phiên kết thúc khi không còn vị thế nào |
| E-order-execution-013 | Vượt số vị thế tối đa | Đã đạt số vị thế mở tối đa đã khai | minor | FR-009 | Từ chối vũ trang, nêu rõ hạn mức | Đóng bớt vị thế hoặc nới hạn mức từ phiên sau |
| E-order-execution-014 | Khối lượng không hợp lệ | Dưới mức tối thiểu, sai bước nhảy của sàn, hoặc vượt hạn mức tự đặt | minor | FR-010 | Chặn ngay **trước khi ARM**, nêu rõ giới hạn hợp lệ | Sửa khối lượng rồi vũ trang lại |
| E-order-execution-015 | Mức bảo vệ không hợp lệ | SL/TP đặt về phía sai hoặc quá sát giá hiện tại | minor | FR-045 | Chặn **tại bản xem trước**, nêu rõ vì sao | Sửa mức rồi áp lại; chưa tới bước xác nhận nên chưa có gì gửi đi |
| E-order-execution-016 | Khung giờ phiên nhập ngược | Giờ kết thúc trước giờ bắt đầu | minor | FR-004 | Chặn khi lưu, nêu rõ chỗ sai | Sửa lại khung giờ |
| E-order-execution-017 | Ngưỡng cảnh báo tin không hợp lệ | Bằng 0, âm, hoặc dài hơn cả phiên | minor | FR-004 | Chặn khi lưu, nêu rõ khoảng hợp lệ | Sửa lại; chưa khai thì dùng mặc định 15 phút |
| E-order-execution-018 | Vị thế không còn tồn tại | Xác nhận đóng hoặc sửa cho một vị thế vừa biến mất | major | FR-040 | Nói rõ **"vị thế không còn"** và vì sao | Không phải lỗi hệ thống; danh sách vị thế tự cập nhật |
| E-order-execution-019 | Không có gì để đóng | Bấm đóng hoặc thoát khẩn cấp khi không có vị thế nào | minor | FR-030 | Xác nhận nhẹ nhàng "không có gì để đóng" | **Không** báo lỗi, **không** đổi trạng thái khoá ngoài dự kiến |
| E-order-execution-020 | Siết hạn mức xuống dưới trạng thái đang có | Hạ khối lượng hoặc số vị thế tối đa thấp hơn cái đang mở | minor | FR-006 | Lưu thành công, kèm câu nói rõ vị thế đang có **không** bị ép đóng | Hạn mức mới chỉ chi phối hành động mới |
| E-order-execution-021 | Vị thế kết thúc ngoài ý muốn | Chạm SL, chạm TP, hoặc bị sàn đóng | major | FR-039 | Thông báo ngay kèm **lý do** và **kết quả** | Không phải lỗi; là sự kiện cần biết ngay |
| E-order-execution-022 | Mở menu khi đang vũ trang | Bấm `Menu` trong lúc đang ARM | minor | FR-052 | Trạng thái vũ trang bị huỷ; người chơi thấy rõ | Bộ đếm tự huỷ **không** tăng |

## 7. Success Criteria

| ID | Outcome nghiệp vụ | Đo bằng | Mốc đạt |
|----|-------------------|---------|---------|
| SC-order-execution-01 | Không lệnh nào vào sàn mà người chơi không chủ động quyết định | Đối chiếu số lệnh cTrader demo với bản ghi xác nhận hai tay (FR-020) | 0 lệnh ngoài ý muốn mỗi tháng |
| SC-order-execution-02 | Sự tự kiềm chế tăng theo thời gian, không phải nhờ vũ trang bừa | Tỷ lệ = số lần huỷ chủ động ÷ số lần vũ trang, đọc cuối mỗi phiên, kèm tổng số lần vũ trang | Cao hơn baseline sau 3 tháng **và** tổng số lần vũ trang mỗi phiên không tăng bất thường |
| SC-order-execution-03 | Luôn thoát được kể cả khi thiết bị hoặc kết nối hỏng | Diễn tập hằng tháng: rút dongle / ẩn tab / ngắt mạng khi đang có vị thế, bấm thoát và bấm giờ | 100% lần thử thành công, trong vòng 10 giây |
| SC-order-execution-04 | Không bao giờ hoang mang về trạng thái lệnh của mình | Người chơi ghi nhận mỗi lần đi kiểm tra chéo **ngoài kế hoạch** | 0 lần mỗi tháng (diễn tập SC-03 và checkpoint URD không tính) |
| SC-order-execution-05 | Hạn mức tự đặt thực sự được thi hành | Đối chiếu dấu thời gian từng lệnh trên cTrader demo với khung giờ và hạn mức đã khai | 0 lệnh mở ngoài khung giờ hoặc sau khi chạm lỗ tối đa |
| SC-order-execution-06 | Quy trình đứng trước tiền ở mọi màn của feature | Rà từng màn mỗi lần đổi giao diện | 100% màn mặc định không hiển thị con số tiền nào trước một thao tác bật có chủ ý |

> **SC-01, SC-04 và `ai-desk` USC-002 dùng chung một lần kiểm toán vị thế** — một lần đối chiếu, ba câu
> hỏi khác nhau — để ba thước đo không ra kết quả lệch nhau.
>
> **Đường kiểm chứng độc lập đã chốt: điện thoại chạy cTrader mobile** (OQ-3, 2026-08-29) — nên SC-01,
> SC-03, SC-04 đo được ngay từ phiên đầu. Nếu phải lùi về profile trình duyệt thứ hai thì **đánh dấu số đo
> là "đo yếu"**, không báo cáo như số thật.

## 8. Data Entities (tóm tắt — chi tiết ở `order-execution-erd.md`)

| Entity | Ý nghĩa nghiệp vụ | Thông tin nghiệp vụ cần lưu |
|--------|-------------------|------------------------------|
| **Phiên giao dịch** | Một buổi tối giao dịch, từ lúc mở tới lúc không còn vị thế nào | Thời điểm mở · thời điểm đóng · lý do đóng (tự đóng / hết khung giờ) · trạng thái khoá hiện tại · số phiên thứ mấy trong ngày |
| **Hạn mức phiên** | Bộ ràng buộc người chơi tự đặt cho phiên này | Khung giờ · khối lượng tối đa · số vị thế tối đa · mức lỗ tối đa · ngưỡng cảnh báo tin · loại (thi hành / chỉ cảnh báo) · lịch sử sửa kèm hướng siết-hay-nới |
| **Lần vũ trang** | Một lần người chơi chọn hướng nhưng chưa bắn | Thời điểm · hướng · cặp · khối lượng · kết cục (bắn / huỷ chủ động / huỷ bị động) · lý do huỷ bị động · **cờ điều kiện đứng ngoài** |
| **Ý định (intent)** | Gói người chơi gửi lên gateway — **không phải một lệnh** | Trạng thái clutch · thời điểm vũ trang · mức bảo vệ tương đối dự kiến |
| **Lệnh** | Một lần xác nhận hai tay đã được gửi đi | `cid` · thời điểm xác nhận · trạng thái kết quả (khớp / từ chối / chưa rõ) · lý do từ chối · **đã bị bỏ qua khi chưa rõ hay chưa** |
| **Vị thế** | Một vị thế demo đang tồn tại trên sàn | Cặp · hướng · khối lượng · giá vào · mức bảo vệ hiện tại · lãi lỗ theo R · thời điểm mở · thời điểm và **lý do đóng** |
| **Bản xem trước sửa bảo vệ** | Thay đổi SL/TP đã dàn sẵn nhưng **chưa gửi** | Vị thế đích · mức SL/TP mới · rủi ro và mục tiêu tương ứng · thời điểm dàn |
| **Bối cảnh đã đóng băng (tape)** | Cửa sổ dữ liệu giá quanh một lệnh, cắt ra khi lệnh đóng | Thuộc lệnh nào (`cid`) · mốc đầu và mốc cuối cửa sổ · dữ liệu giá trong cửa sổ · **trạng thái: đang thu nốt / đủ / cụt đuôi / quá hạn giữ** · thời điểm đóng băng. **`trade-replay` chỉ đọc** |
| **Sự kiện khoá** | Mỗi lần trạng thái khoá đổi | Thời điểm · lý do (thoát khẩn cấp / tự khoá / hết giờ / mất kết nối / chưa rõ kết quả) · cái gì còn dùng được · thời điểm mở khoá |

> **Bộ đếm tự huỷ không phải một entity riêng** — nó là số lần đếm được từ *Lần vũ trang* có kết cục "huỷ
> chủ động" trong phiên hiện tại. Một nguồn, hai cách đọc (FR-049): màn chính đọc luật rộng, `process-score`
> đọc tập con có cờ điều kiện đứng ngoài.

## 9. Flows (tóm tắt — chi tiết ở `order-execution-flows.md`)

| Flow | Tóm tắt | Nguồn |
|------|---------|-------|
| Mở phiên và vào lệnh đầu tiên | Mở phiên → khai hạn mức → chọn cặp/khối lượng → giữ clutch → vũ trang → đọc màn xác nhận → `LT+RT` → rung + xác nhận khớp | URD Journey 1 |
| Thoát khẩn cấp khi mọi thứ hỏng | Nhận ra cần thoát → `Y` trên tay cầm **hoặc** nút thoát trên màn hình → đóng toàn bộ → khoá phiên → xác nhận không còn gì mở | URD Journey 2 |
| Từ chối một setup | Đang vũ trang → nhả clutch hoặc bấm huỷ → trạng thái vũ trang biến mất, không gửi gì → bộ đếm tăng một | URD Journey 3 |
| Mất kết nối khi đang có vị thế | Sự cố → màn khoá nêu rõ cái gì còn dùng được → mở lệnh bị chặn, đóng và thoát vẫn được → nối lại → đối chiếu trạng thái thật với sàn | URD Journey 4 |
| Đóng vị thế theo kế hoạch | Quyết định thoát → chọn đúng vị thế → xác nhận đóng → vị thế biến mất, kết quả hiện theo R | URD Journey 5 |
| Sửa mức bảo vệ | Mở menu (huỷ ARM, khoá mở lệnh) → chọn vị thế → chỉnh SL/TP → áp (chỉ dàn bản xem trước) → về màn chính → `LT+RT` | URD Journey 6 |

## 10. Screens (tóm tắt — chi tiết ở `ascii-wireframe/`)

| Màn hình | Vai trò | Ghi chú ranh giới |
|----------|---------|-------------------|
| **HUD chính** | Giá · biểu đồ · danh sách vị thế · bộ đếm tự huỷ (con số lớn nhất sau giá) · trạng thái khoá · độ tươi dữ liệu · nút thoát dùng được bằng chuột | Không con số tiền nào trước một thao tác bật (FR-047) |
| **Màn xác nhận** | Tóm tắt lệnh sắp gửi: cặp, hướng, khối lượng, mức bảo vệ, rủi ro R | Feature này **sở hữu màn**; `playbook-grading` **đóng góp nội dung điểm** lên nó và không thêm bước nào vào chuỗi xác nhận |
| **Màn khai hạn mức** | Bốn hạn mức thi hành + ngưỡng chỉ cảnh báo | Phân biệt rõ hai loại; validate khi lưu (FR-004) |
| **GameOverlay (menu an toàn)** | Đích điều hướng chung: sửa bảo vệ, playbook, deck, nhật ký, replay, báo cáo, cài đặt | Mở → huỷ ARM + khoá mở lệnh (FR-052); điều hướng không phát ra lệnh (FR-053) |
| **Màn khoá** | Nêu rõ vì sao khoá và **cái gì còn dùng được** | Luôn nêu **mọi** lý do đang có hiệu lực (FR-035) |
| **Bản xem trước sửa bảo vệ** | Mức SL/TP mới + rủi ro/mục tiêu tương ứng | Trạng thái "đang chờ xác nhận" phải đọc khác hẳn "đã áp" (FR-042) |

> Ba màn hình đầu tiên là bề mặt mà `tilt-meter`, `playbook-grading`, `voice-journal`, `daily-journal` và
> `process-score` cùng gắn nội dung lên. Chi tiết chia flow và danh sách màn sẽ do `/user-flow` chốt trước
> khi vẽ wireframe.

## 11. Constraints, Dependencies & Assumptions

**Constraints (ràng buộc áp đặt — có source/owner):**

| Ràng buộc | Source / Owner |
|-----------|----------------|
| **Gateway là thành phần duy nhất duyệt một lệnh demo**; Spotware là matching engine thật | `docs/_shared/system-overview.md` |
| Giao thức client ↔ gateway là **WSS**; adapter sàn duy nhất là **cTrader Open API** | `docs/_shared/operating-environment.md` |
| Máy chủ: **Docker trên Ubuntu VPS**. Docker/Ubuntu mua "chạy liên tục không cần Windows", **không** mua tốc độ khớp lệnh | `docs/_shared/operating-environment.md` |
| Chặng nhà → VPS **15–80 ms** chiếm phần lớn độ trễ và không giảm được | `docs/_shared/system-overview.md` |
| Cửa sổ Chrome phải **đang focus** thì mới phát lệnh được | `docs/_shared/operating-environment.md` |
| Tay cầm qua **dongle 2.4G**; dây USB dự phòng; **Bluetooth không dùng được** | `docs/_shared/operating-environment.md` |
| Chỉ tài khoản **demo**, không có tiền thật trong bất kỳ đường nào | `docs/_shared/project-profile.md` — Compliance |
| **AI không bao giờ được chặn một lệnh** — mọi tính năng AI phải chịu được việc bị bỏ qua | `docs/_shared/operating-environment.md` |
| Mở GameOverlay **huỷ ARM và khoá mở lệnh mới** | `docs/_shared/operating-environment.md` |
| Luật playbook **không bao giờ chặn được một lệnh** | `playbook-grading` UN-002 |
| Ma sát `tilt-meter` **chỉ áp cho việc mở lệnh** | `tilt-meter` UN-001 |

**Dependencies (deliverable do bên khác sở hữu):**

| Phụ thuộc | Owner | Blocks nếu chưa sẵn |
|-----------|-------|---------------------|
| Tài khoản demo cTrader hoạt động, phiên đăng nhập còn hạn | Người chơi / Spotware | Toàn bộ feature |
| Tay cầm 8BitDo Ultimate 2 + dongle 2.4G | Người chơi | FR-011..FR-019, FR-058; **không** blocks FR-028 |
| Nội dung điểm luật trên màn xác nhận | `playbook-grading` | FR-013 — xem OQ-4 về hành vi thay thế |
| Định nghĩa "điều kiện đứng ngoài" để gắn cờ cho mỗi lần huỷ | `process-score` (OQ-10 của nó) | FR-049 — cờ ghi được nhưng chưa biết ghi theo danh sách nào |
| Ngưỡng cảnh báo trước sự kiện tin và nguồn lịch sự kiện | `ai-desk` | FR-003 — mặc định 15 phút dùng được trong lúc chờ |
| **Điện thoại chạy cTrader mobile** để kiểm chứng độc lập (chốt 2026-08-29) | Người chơi | Khả năng đo SC-01, SC-03, SC-04 |

**Assumptions (tin là đúng — nêu hệ quả nếu sai):**

| Giả định | Invalidate {X} nếu sai |
|----------|------------------------|
| "Luôn thoát được" nghĩa là đóng được vị thế **không cần tay cầm** (URD A-02) | FR-028 và NFR-005 không thoả UN-003 — nghĩa vụ an toàn cao nhất của feature |
| Một phiên = một buổi tối, hạn mức lỗ gắn với **phiên**, không cộng dồn theo ngày lịch (URD A-04) | BR-007 sai; mở phiên mới trở thành đường lách hạn mức lỗ — xem OQ-1 |
| Danh sách cặp sửa được trong Settings (URD A-01) | FR-058 hẹp lại; phạm vi CAP-12 của PRD phải viết lại |
| "Không rời tay khỏi tay cầm" là nhu cầu thật (URD A-06) | FR-058 và NFR-011 mất cơ sở, nên hạ xuống P2 |
| Người chơi mở được cTrader demo trên **điện thoại** để kiểm chứng (URD A-07 — **đã xác nhận 2026-08-29**) | Toàn bộ Mục 7 mất khả năng kiểm chứng. Điện thoại không dùng được thì lùi về profile trình duyệt thứ hai và **đánh dấu số đo là "đo yếu"** |
| Nhả sớm nút xác nhận không phải một lần tự huỷ (`tilt-meter` A-13) | BR-005 sai; mỗi lần trượt tay ở mức nóng lại được khen là kỷ luật, bộ đếm mất ý nghĩa |
| Người chơi chơi một mình, không có ai xem cùng (URD A-03) | Mục 2 thiếu một actor |

## 12. Open Questions

> **Số OQ đánh riêng cho từng tài liệu.** `OQ-3` của SRS này không nhất thiết là `OQ-3` của PRD
> cùng feature. Neo ổn định để đối chiếu là **số OQ của URD** ghi trong ngoặc *(kế thừa URD OQ-x)*.

* [ ] **OQ-1** *(kế thừa URD OQ-5)*: Một ngày chạy được tối đa mấy phiên, và có trần lỗ theo **ngày** đứng
  trên trần lỗ theo **phiên** không?
  🔶 **Tạm quyết:** không có trần ngày; hạn mức chỉ gắn với phiên (BR-007), và màn mở phiên hiển thị rõ
  **đây là phiên thứ mấy trong ngày** cùng tổng lỗ các phiên đã chạy, để việc lách trở nên nhìn thấy được.
  *Nếu sai:* thêm một hạn mức thi hành cấp ngày vào FR-002 và một luật ưu tiên vào BR-007; CAP-13 của PRD
  chuyển từ P2 lên P0.

* [ ] **OQ-2** *(kế thừa URD OQ-6)*: Mở khoá phiên sau thoát khẩn cấp cần thao tác nặng tới đâu?
  🔶 **Tạm quyết:** một thao tác **có chủ ý hơn một cú tap** — cùng mức cửa với việc xác nhận hai tay
  (FR-032). Một tap thì trạng thái khoá gần như không có sức răn đe.
  *Nếu sai (người chơi thấy quá nặng):* hạ về một cú tap và chấp nhận trạng thái khoá chỉ mang tính thông
  báo; khi đó Risk "khoá mất sức răn đe" ở PRD Mục 10 thành hiện thực.

* [x] **OQ-3** *(kế thừa URD OQ-7, chung với `ai-desk` và `mentor-signals`)*: Người chơi kiểm chứng độc
  lập bằng thiết bị nào?
  **Resolved 2026-08-29: điện thoại chạy cTrader mobile.** Cùng tài khoản demo, khác thiết bị và khác đường
  mạng — nên **độc lập thật**, bắt được đúng loại lỗi SC-01 sinh ra để bắt (*sản phẩm nhất quán với chính nó
  nhưng không khớp với sàn*) — và **không đụng ràng buộc giữ Chrome focus**.
  *Dự phòng nếu không có điện thoại:* profile trình duyệt thứ hai trên cùng máy đếm được vị thế nhưng yếu hơn
  (chung máy; diễn tập mất-focus phải alt-tab, đúng cái ràng buộc cấm) → **đánh dấu số đo là "đo yếu"**,
  không báo cáo như số thật.
  **SC-01, SC-03, SC-04 vì vậy đo được ngay từ phiên đầu.**

* [ ] **OQ-4**: `playbook-grading` chưa tồn tại thì màn xác nhận (FR-013) xử sự thế nào? URD của nó nói
  màn xác nhận **không mở ra khi chưa có điểm**.
  🔶 **Tạm quyết:** luật đó chỉ áp **khi `playbook-grading` đã tồn tại**. Chưa có nguồn điểm thì màn xác
  nhận mở bình thường và đọc là "chưa có playbook".
  *Nếu sai:* FR-013 phải chờ `playbook-grading` xong mới dùng được, và thứ tự phát hành hai feature đảo lại.

* [ ] **OQ-5**: Ngưỡng "thời gian hợp lý" của FR-023 (bao lâu không phản hồi thì chuyển sang "chưa rõ") và
  ngưỡng im lặng của FR-056 là bao nhiêu?
  🔶 **Tạm quyết:** hai ngưỡng **khác nhau và đều là cấu hình**; ngưỡng im lặng ngắn hơn ngưỡng "chưa rõ",
  vì mất tín hiệu nền phải phát hiện sớm hơn một lệnh chưa có kết quả.
  *Nếu sai:* đặt quá ngắn thì "chưa rõ" xuất hiện liên tục do độ trễ nhà→VPS và việc bỏ qua (FR-025) thành
  thói quen — đúng Risk đã ghi ở PRD Mục 10.

* [ ] **OQ-6** *(chung với `tilt-meter` OQ-4)*: Ma sát của `tilt-meter` có áp cho thao tác **sửa mức bảo vệ**
  không? FR-029 hiện chỉ bảo vệ đóng lệnh và thoát khẩn cấp.
  🔶 **Tạm quyết:** **không siết** thao tác sửa bảo vệ — giữ nguyên tắc chỉ cản việc mở lệnh mới.
  *Nếu sai:* BR-009 và FR-042..045 phải tách **nới cắt lỗ ra xa** (hành vi tilt cần cản) khỏi **siết bảo vệ
  vào gần** (hành vi phòng vệ, không bao giờ được cản). Đây là khoảng trống duy nhất của ranh giới an toàn.

* [ ] **OQ-7** *(chung với `trade-replay` OQ-8)*: Thông báo vị thế kết thúc (FR-039) có mang đường dẫn thẳng
  sang màn tua lại không? Nội dung thông báo thuộc feature này, đường dẫn sang thuộc `trade-replay`.
  🔶 **Tạm quyết:** feature này **nhận** phần dẫn đường và để chỗ cho nó trong FR-039.
  *Nếu sai:* `trade-replay` mất đường vào nóng nhất, đúng đường USC-002 của nó đặt cược.

* [ ] **OQ-9** *(nhận từ `trade-replay` khi chuyển quyền sở hữu tape, 2026-08-29)*: Cửa sổ **5 phút trước /
  5 phút sau** (FR-061) có đủ không? Ngắn quá thì không thấy bối cảnh dẫn tới setup; dài quá thì tốn chỗ mà
  không ai xem tới. Và: có cần thu **cả buổi tối như một dòng liên tục** không — nếu cần thì cách lưu đổi
  hoàn toàn. Cả hai nay là **tham số của feature này**.

* [ ] **OQ-10** *(nhận từ `trade-replay`, 2026-08-29)*: **Hạn giữ tape** là bao lâu (FR-063)? Đây là cấu
  hình **của tape**, tách hẳn khỏi nhật ký — nhật ký đã chốt **giữ vô hạn** và mục *hạn giữ nhật ký* đã bị
  bỏ. Tape là thứ duy nhất phình thật, nên nó là chỗ đúng để đặt một hạn giữ nếu cần.

* [ ] **OQ-8**: Danh sách cặp giao dịch cố định hay sửa được trong Settings (URD A-01)? Ảnh hưởng FR-058 và
  ranh giới với `reports-export` (màn cài đặt).

---

> **Nguồn:** `order-execution-urd.md` (13 nhu cầu, 6 journey, 24 tình huống ngoại lệ, 5 thước đo, 7 giả
> định) · `order-execution-prd.md` (13 capability) · bốn tài liệu nền `docs/_shared/` · ranh giới nhận từ
> `ai-desk`, `playbook-grading`, `tilt-meter`, `voice-journal`, `process-score`, `trade-replay`.
>
> **🔶 Bảy quyết định thay user** nằm ở Mục 12 (OQ-1..OQ-7), mỗi cái kèm hệ quả nếu sai. Không quyết định
> nào trong số đó được trình bày như một fact ở các mục trên — chúng đều có dòng trỏ về OQ tương ứng.
>
> **Tầng 2–4 chưa sinh:** `order-execution-flows.md`, `order-execution-states.md`, `order-execution-erd.md`,
> use case, user story, AC. Mục 8, 9, 10 ở trên là tóm tắt neo sẵn cho chúng.
