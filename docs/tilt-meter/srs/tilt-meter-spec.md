---
type: srs
feature: tilt-meter
status: draft
updated: 2026-08-29
links:
  - docs/tilt-meter/tilt-meter-urd.md
  - docs/tilt-meter/tilt-meter-prd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/srs/order-execution-spec.md
  - docs/playbook-grading/srs/playbook-grading-spec.md
  - docs/voice-journal/voice-journal-urd.md
  - docs/process-score/process-score-urd.md
---

# tilt-meter — Software Requirements Specification

## 1. Scope

Đặc tả một **chỉ số trạng thái đọc từ hành vi quan sát được trên tay cầm và dữ liệu đã có sẵn trong nhật ký**,
rơi vào một trong bốn mức với hệ quả tăng dần, cản người chơi **đúng một chỗ duy nhất: lúc mở lệnh mới** —
dưới hai ranh giới cứng sinh ra cùng lúc với nó.

**Trong phạm vi:** thu thập hành vi tay cầm và dữ kiện nhật ký · tính mức thường của chính người chơi trên
30 phiên gần nhất · phân bốn mức cộng một trạng thái trung tính · nêu tên hành vi đóng góp lớn nhất bằng một
câu · hệ quả từng mức (ấm: không tốn gì · nóng: siết thao tác bắn · quá nóng: khoá mở lệnh 5 phút) · đường ra
sớm bằng memo · khoảng khoá theo đồng hồ và hành vi khi mất kết nối · bật/tắt hoàn toàn · sinh dữ liệu cho
`trade-replay` và `process-score` · giữ hai con số của hai thước đo riêng.

**Ngoài phạm vi:** đo trạng thái giọng nói — **người chơi bỏ hẳn 2026-08-28**, mở lại phải qua CR · phân loại
cảm xúc, phát hiện từ ngữ tiêu cực, chấm điểm nội dung lời nói, hoặc bất kỳ mô hình ngôn ngữ nào trong phép
tính — **ngoài phạm vi vĩnh viễn** · hạn mức rủi ro và chốt an toàn khi vắng mặt (`order-execution`) · bộ đếm
tự huỷ (`order-execution`) · chấm luật playbook (`playbook-grading`) · bảng nhìn lại tilt theo phiên và điểm
quy trình (`process-score`) · ghi âm và chép lời (`voice-journal`) · tua lại tape (`trade-replay`) · nghi thức
trước phiên (`daily-journal`) · báo cáo và xuất dữ liệu (`reports-export`).

> **Hai ranh giới cứng, quan trọng ngang nhu cầu chính:**
> 1. **Không bao giờ chạm đường thoát.** Đóng vị thế, thoát khẩn cấp, nút thoát trên màn hình và tự khoá
>    phiên hoạt động y hệt như khi chỉ số ở mức thấp nhất. **Không tồn tại cấu hình nào bật được việc cản
>    đường thoát.**
> 2. **Không bao giờ là đầu vào của điểm.** Trạng thái tâm lý không xuất hiện trong bất kỳ phép tính điểm
>    nào, kể cả qua cửa sau.
>
> **Một cơ chế cản người ở sai chỗ thì nguy hiểm; một cơ chế mắng người thì bị tắt sau hai tuần.**

## 2. Actors & Stakeholders

| Actor | Loại | Mục tiêu | Trong scope? |
|-------|------|----------|--------------|
| **Người chơi** | người | Được cản lại đúng lúc mình đang trượt, không mất quyền thoát, không bị chấm điểm nhân cách | Có |
| **Bộ đo hành vi** | hệ thống | Thu hành vi tay cầm + dữ kiện nhật ký → chỉ số + mức + hành vi đóng góp lớn nhất | Có |
| **`order-execution`** | hệ thống | Sở hữu chuỗi vũ trang–bắn (nơi ma sát gắn vào) và đường thoát (nơi ma sát **không bao giờ** được gắn vào) | **Không** — ranh giới tích hợp |
| **`voice-journal`** | hệ thống | Cấp **sự kiện "đã ghi một memo"**; và cấp đường ghi memo bằng bàn phím dùng được lúc bị khoá | **Không** — chỉ cấp sự kiện, **không bao giờ cấp nội dung** |
| **`playbook-grading`** | hệ thống | Cấp số luật không đạt trong ba lần bắn gần nhất, làm một tín hiệu | **Không** — chỉ đọc |
| **`process-score`** | hệ thống | Đọc dữ liệu tilt để **kể lại buổi tối**, tuyệt đối không đưa vào phép gộp điểm | **Không** — chỉ đọc |
| **`trade-replay`** | hệ thống | Đặt mỗi lần đổi mức lên dải thời gian của một lệnh | **Không** — chỉ đọc |
| **AI desk** | hệ thống | — | **Không.** Không tham gia phép tính; chỉ đọc được mức và nguyên nhân chính ở **dạng tổng hợp**, không đọc từng mẫu |

## 3. Functional Requirements (FR)

### 3.1 Ranh giới an toàn

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-tilt-meter-001 | Không bao giờ chạm đường thoát | Đóng vị thế, thoát khẩn cấp, nút thoát trên màn hình và tự khoá phiên hoạt động **y hệt** như khi chỉ số ở mức thấp nhất — không chậm hơn, không thêm một bước nào, ở **mọi** mức | P0 | test | URD UN-001 |
| FR-tilt-meter-002 | Không có cấu hình nào bật được việc cản đường thoát | Cấu hình cho phép tilt chạm một thao tác thuộc đường thoát → **sản phẩm không khởi động** | P0 | test | URD UN-001 · README |
| FR-tilt-meter-003 | Ma sát chỉ áp cho việc **mở** lệnh mới | Không thao tác nào khác bị chạm. Cho tới khi OQ-1 chốt, thao tác **sửa mức bảo vệ không bị siết** | P0 | test | URD UN-001 · Mục 6 — xem OQ-1 |
| FR-tilt-meter-004 | Không bao giờ là đầu vào của điểm | Chỉ số và mọi thành phần của nó **không xuất hiện** trong bất kỳ phép tính điểm nào của `process-score` | P0 | test | URD UN-002 |
| FR-tilt-meter-005 | Không đi vào điểm qua cửa sau | Tập "điều kiện đứng ngoài" mà `process-score` dùng để cộng điểm cho một lần tự huỷ **không bao gồm mức tâm lý** | P0 | kiểm tra | `process-score` A-09 (chốt 2026-08-28) |
| FR-tilt-meter-006 | Không lưu như một đặc điểm của con người | Chỉ số là trạng thái của **phiên**. Không con số nào tích lại thành một nhãn dán lên người chơi. Số lệnh thua liên tiếp là **đầu vào**, **không bao giờ** hiện ra như một chuỗi thành tích ngược | P0 | test | URD UN-011 |

### 3.2 Thu thập và tính chỉ số

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-tilt-meter-007 | Thành phần hành vi tay cầm | Đo: số lần đóng-mở chốt an toàn trước một lần vũ trang · số lần đảo hướng mua-bán khi đang vũ trang · nhịp bấm nút · số bước đổi khối lượng · thời gian từ lúc vũ trang tới lúc bắn · thời gian ngồi im | P0 | test | URD Mục 3 |
| FR-tilt-meter-008 | Thành phần từ dữ liệu nhật ký sẵn có | Dùng thêm: thời gian kể từ lệnh thua gần nhất · số lệnh thua trong buổi · khối lượng lệnh sắp vào so với mức thường của phiên · nhịp mở lệnh · số luật playbook không đạt trong **ba lần bắn gần nhất**. **Không phát sinh việc ghi mới** | P0 | test | URD Mục 3 |
| FR-tilt-meter-009 | Không suy đoán cảm xúc từ nguồn nào khác | Mọi thành phần là một hành vi **đếm được** hoặc một dữ kiện **có sẵn**. Không phân loại cảm xúc, không phân tích từ ngữ, **không mô hình ngôn ngữ nào trong phép tính** | P0 | test | URD UN-006 |
| FR-tilt-meter-010 | Thành phần thiếu dữ liệu thì không áp | Buổi chưa có lệnh thua nào, phiên mới chỉ một hai lệnh, hoặc chưa khai playbook nào → thành phần tương ứng **không áp**. Chỉ số tính trên những gì thật sự đo được và **không vì thiếu một thành phần mà tự thấp đi hay cao lên** | P0 | test | URD Mục 6 |
| FR-tilt-meter-011 | Ngồi im không phải tín hiệu xấu | Chỉ nhịp bấm **cao hơn** mức thường mới đẩy chỉ số lên. Một buổi kiên nhẫn phải cho chỉ số thấp | P0 | test | URD Mục 6 |
| FR-tilt-meter-012 | Đổi cặp liên tục là tín hiệu nhưng không đủ một mình | Được ghi nhận như một tín hiệu, nhưng **một mình nó không đủ** đẩy lên mức nóng; câu nêu lý do phải nêu đúng nó | P0 | test | URD Mục 6 |
| FR-tilt-meter-013 | Chỉ số nguội dần khi không có dữ liệu mới | Mất tay cầm hoặc mất focus lâu → chỉ số **nguội dần theo thời gian** thay vì đứng yên; vắng đủ lâu thì bắt đầu lại từ trung tính và nói rõ vì sao | P0 | test | URD Mục 6 |

### 3.3 Mức thường của chính người chơi

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-tilt-meter-014 | Mốc so sánh lấy từ 30 phiên gần nhất của chính người chơi | Mọi mốc so sánh là mức thường của chính người chơi. **Không có chuẩn của đám đông nào được áp lên người chơi** | P0 | test | URD UN-005 |
| FR-tilt-meter-015 | Dưới 5 phiên: trung tính, không sinh ma sát | Lịch sử dưới 5 phiên → chỉ báo hiện **trung tính**, hệ thống nói rõ đang còn học, và **không sinh ma sát nào** | P0 | test | URD UN-009 (🔶 A-12) — xem OQ-5 |
| FR-tilt-meter-016 | Mức thường ổn định quanh 30 phiên | Giữa mốc 5 phiên và 30 phiên, cơ chế có chạy nhưng còn thô; người chơi biết điều đó | P0 | kiểm tra | URD Mục 7 |
| FR-tilt-meter-017 | Bật lại sau một thời gian dài tắt | Dùng lại 30 phiên gần nhất đang có; quá ít mẫu còn dùng được → quay về trạng thái trung tính như người mới, thay vì tính trên dữ liệu đã lỗi thời | P0 | test | URD Mục 6 |
| FR-tilt-meter-018 | Mức thường **có** tích luỹ, chỉ số thì không | Thứ không tích luỹ là **chỉ số** và mọi cách trình bày nó thành chuỗi hay cấp độ. Mức thường của chính người chơi **có** tích luỹ qua 30 phiên — nhưng nó là **thước để so**, không phải nhãn dán lên người chơi | P0 | kiểm tra | URD UN-011 |

### 3.4 Bốn mức và câu nêu lý do

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-tilt-meter-019 | Bốn mức | Chỉ số rơi vào đúng một trong bốn mức: **bình thường · ấm · nóng · quá nóng**. Chỉ mức thấp nhất im lặng hoàn toàn | P0 | demo | URD Mục 3 |
| FR-tilt-meter-020 | Trạng thái trung tính riêng biệt | Ngoài bốn mức còn một **trạng thái hiển thị riêng — trung tính** — nghĩa là chưa đủ dữ liệu để nói gì. Nó đọc **khác hẳn** mức bình thường và **không bao giờ sinh ma sát** | P0 | demo | URD Mục 3 |
| FR-tilt-meter-021 | Luôn nêu tên hành vi bằng một câu | Màn hình chính **luôn** nêu tên hành vi đang đẩy chỉ số lên nhiều nhất, bằng một câu người đọc hiểu được ("vừa vào lại 40 giây sau một lệnh thua"). **Không bao giờ chỉ hiện một con số trần** | P0 | demo | URD UN-004 |
| FR-tilt-meter-022 | Câu nêu lý do không nhắc thứ chưa có | Chưa có luật playbook nào thì câu nêu lý do **không bao giờ** nhắc tới luật | P0 | test | URD Mục 6 |
| FR-tilt-meter-023 | Ba ngưỡng chia bốn mức là cấu hình | Ba ngưỡng là giá trị cấu hình, xem lại sau một tháng dữ liệu thật | P0 | kiểm tra | URD A-03 — xem OQ-4 |

### 3.5 Hệ quả từng mức

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-tilt-meter-024 | Mức bình thường im lặng hoàn toàn | Không dòng cảnh báo, không ma sát, không đổi gì | P0 | test | URD Mục 3 |
| FR-tilt-meter-025 | Mức ấm không tốn của người chơi thứ gì | Chỉ thêm **một dòng chữ** và đổi màu chỉ báo. Thao tác bắn **không đổi một chút nào** — vẫn là bấm nhả, không thêm bước | P0 | test | URD UN-008 |
| FR-tilt-meter-026 | Mức nóng siết thao tác bắn | Người chơi phải **giữ** nút xác nhận một khoảng ngắn thay vì bấm nhả; trong lúc giữ còn kịp đổi ý | P0 | test | URD UN-003 |
| FR-tilt-meter-027 | Mức nóng bổ sung nội dung màn xác nhận | Màn xác nhận nêu thêm **lý do** và **mức rủi ro của chính lệnh này** | P0 | demo | URD Journey 2 |
| FR-tilt-meter-028 | Nhả sớm nút xác nhận | Không có lệnh nào phát sinh; trạng thái vũ trang **không mất**; màn hình nói rõ cần giữ đủ lâu. Nhả sớm **không** tính là một lần tự huỷ | P0 | test | URD Mục 6 (🔶 A-13) · `order-execution` BR-005 |
| FR-tilt-meter-029 | Mức quá nóng khoá mở lệnh 5 phút | Khoá việc **mở lệnh mới** trong 5 phút, kèm đồng hồ đếm ngược và lời mời ghi một memo | P0 | test | URD UN-003 |
| FR-tilt-meter-030 | Huỷ ARM khi khoá bắt đầu | Chạm mức quá nóng trong lúc đang vũ trang → trạng thái vũ trang bị huỷ **ngay khi khoá bắt đầu**, để đường ghi memo mở ra. Lần huỷ này **không** tính là một lần tự huỷ; người chơi thấy rõ vì sao vũ trang biến mất | P0 | test | URD Mục 6 · `order-execution` BR-004 |
| FR-tilt-meter-031 | Khoá lại được, nhưng không leo thang | Hết 5 phút mà chỉ số vẫn ở mức quá nóng → khoá lại được, và màn hình nói rõ **đây là lần khoá thứ mấy** trong buổi cùng hành vi nào đang giữ chỉ số ở đó. Khoảng khoá **không dài thêm** theo số lần — **không có leo thang hình phạt** | P0 | test | URD Mục 6 |
| FR-tilt-meter-032 | Mọi lệnh mở đều bị khoá như nhau | Kể cả lệnh mở **ngược chiều để giảm rủi ro** của vị thế đang có — hệ thống không đọc được ý định. Màn hình chỉ rõ đường giảm rủi ro **không bị chạm** vẫn còn nguyên: đóng bớt vị thế hoặc thoát khẩn cấp | P0 | test | URD Mục 6 |

### 3.6 Khoảng khoá và đường ra sớm

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-tilt-meter-033 | Ghi memo hạ chỉ số thật | Ghi một memo trong lúc bị khoá làm chỉ số **hạ xuống thật**. Xuống dưới mức quá nóng thì việc mở lệnh mở lại **trước khi hết 5 phút** | P0 | test | URD UN-007 |
| FR-tilt-meter-034 | Bấm "đã đọc" không đổi chỉ số | Bấm "đã đọc" chỉ **tắt dòng cảnh báo trên màn hình**. Chỉ số **không đổi**; đồng hồ đếm ngược và câu nêu lý do bị khoá **vẫn còn** cho tới khi hết khoá | P0 | test | URD UN-007 (OQ-2 resolved) |
| FR-tilt-meter-035 | Không đọc nội dung memo | Hệ thống **không đọc nội dung memo**. Memo có nội dung không liên quan vẫn hạ chỉ số — việc dừng lại để nói ra một điều gì đó đã là một khoảng nghỉ | P0 | test | URD Mục 6 (🔶 A-06) |
| FR-tilt-meter-036 | Đường ghi memo bằng bàn phím luôn mở lúc bị khoá | Đã tắt giọng nói, mic bị từ chối, hoặc máy không có mic → **đường memo bằng bàn phím luôn có mặt** và được nêu ngay trên màn khoá | P0 | test | URD Mục 6 (🔶 A-10) — xem OQ-2 |
| FR-tilt-meter-037 | Không có đường ra nào thì nói thẳng | Cả hai đường đều không dùng được → màn khoá **nói thẳng** lần này chỉ còn cách chờ hết giờ, thay vì mời một việc không làm được | P0 | test | URD Mục 3 — xem OQ-2 |
| FR-tilt-meter-038 | Khoảng khoá đi theo đồng hồ, không theo phiên | Đóng phiên rồi mở phiên mới, hoặc tự khoá rồi mở khoá lại, **không rút ngắn** khoảng khoá. Phần thời gian còn lại vẫn được thi hành ở phiên mới, kèm câu nói rõ vì sao | P0 | test | URD Mục 3 (🔶 A-05) — xem OQ-6 |
| FR-tilt-meter-039 | Chỉ số bắt đầu lại từ trung tính mỗi phiên | Khác với khoảng khoá: **chỉ số** vẫn bắt đầu lại từ trung tính ở mỗi phiên. Không có gì tích luỹ qua đêm | P0 | test | URD Mục 3 (🔶 A-05) |
| FR-tilt-meter-040 | Mất kết nối rồi vào lại giữa khoá | Khoảng khoá **tính lại từ mốc bắt đầu** và đếm tiếp phần còn lại | P0 | test | URD UN-013 |
| FR-tilt-meter-041 | **Đồng hồ không tin được thì cho phép giao dịch** | Nếu không tính đúng được khoảng khoá, hệ thống **mở ra** — cố ý **ngược** với chốt an toàn khi vắng mặt của `order-execution`, vì cái kia phòng việc không có người còn cái này chỉ là một nhận định. Người chơi thấy rõ điều đó vừa xảy ra | P0 | test | URD UN-013 |
| FR-tilt-meter-042 | Vũ trang rồi huỷ liên tục trong lúc bị khoá | Các lần huỷ đó vẫn đếm như mọi lần huỷ chủ động khác. Việc quy chúng ra điểm đã có trần ở `process-score`; feature này **không thêm luật riêng** | P0 | kiểm tra | URD Mục 6 · `process-score` UN-008 |

### 3.7 Bật và tắt

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-tilt-meter-043 | Tắt hoàn toàn, không để lại dấu vết | Tắt xong thì **không chỉ báo, không dòng cảnh báo, không ma sát, không khoá**; không phần nào sót lại "để tham khảo" | P0 | test | URD UN-010 |
| FR-tilt-meter-044 | Tắt có hiệu lực từ phiên sau | Việc tắt có hiệu lực **từ phiên sau**; một khoảng khoá đang chạy **vẫn chạy hết**. Đó là cái giá của việc không để nút tắt thành đường vượt khoảng chờ | P0 | test | URD UN-010 (🔶 A-08) |
| FR-tilt-meter-045 | Ghi lại mỗi lần bật/tắt kèm ngày | Mỗi lần người chơi bật hoặc tắt cơ chế được ghi lại kèm ngày — **không có nó thì thước đo "còn dùng hay đã bỏ" không có nguồn số** | P0 | kiểm tra | URD Mục 3 · SC-03 |
| FR-tilt-meter-046 | Tắt không ảnh hưởng phần còn lại của sản phẩm | Chấm luật, ghi âm, chấm điểm buổi chạy nguyên vẹn khi tilt bị tắt | P0 | test | URD Journey 6 |

### 3.8 Dữ liệu cho feature khác

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-tilt-meter-047 | Mức tilt tại thời điểm bắn gắn vào mỗi lệnh | Mỗi lệnh giữ lại **mức tilt tại thời điểm bắn**, để sau này đối chiếu quyết định với trạng thái lúc ra quyết định | P1 | kiểm tra | URD UN-012 |
| FR-tilt-meter-048 | Ghi lại mỗi lần đổi mức | Mỗi lần chỉ số đổi mức được ghi lại kèm **mốc thời gian** và **hành vi đã đẩy nó lên**, đủ để `trade-replay` đặt nó đúng chỗ trên dải thời gian | P1 | kiểm tra | URD UN-014 · `trade-replay` UN-011 |
| FR-tilt-meter-049 | Giữ hai con số theo phiên | Mỗi phiên giữ lại: **số lần mở lệnh trong vòng 60 giây sau một lần đóng lỗ**, và **số lệnh có khối lượng từ gấp đôi mức thường của phiên trở lên**. Cơ chế vốn đã tính cả hai để chấm điểm — đây là việc giữ chúng lại theo phiên | P1 | kiểm tra | URD Mục 3 (🔶 A-09) |
| FR-tilt-meter-050 | AI desk chỉ đọc được dạng tổng hợp | AI desk đọc được **mức** và **nguyên nhân chính** ở dạng tổng hợp; **không** đọc được từng mẫu hành vi | P1 | kiểm tra | URD Mục 2 · Mục 7 |
| FR-tilt-meter-051 | Chế độ diễn tập đặt thẳng mức | Người chơi đặt thẳng mức trạng thái để tự kiểm hai ranh giới FR-001 và FR-004, mà không phải dựng bằng hành vi thật cả buổi | P1 | demo | URD OQ-10 — xem OQ-3 |

### 3.9 Xung đột với cơ chế khác

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-tilt-meter-052 | Nêu mọi lý do, nhưng không nói chồng | Khi nhiều cơ chế cùng chạm việc mở lệnh, màn hình nêu **mọi** lý do đang có hiệu lực. Nhưng khi một cơ chế khác **đã xử lý xong** tình huống (vd mất tay cầm đã tự huỷ vũ trang), feature này **không nói thêm gì** — người chơi chỉ nghe một lời giải thích | P0 | demo | URD Mục 6 |
| FR-tilt-meter-053 | Phân biệt hạn mức với ma sát | Vừa bị hạn mức rủi ro chặn vừa đang trong khoảng khoá → nói rõ cả hai và phân biệt: hạn mức là **luật do chính mình đặt**, khoảng khoá là **một nhận định về trạng thái**. Hai thứ **không dùng chung một câu** | P0 | demo | URD Mục 6 |
| FR-tilt-meter-054 | Mất tay cầm hoặc mất focus ở mức nóng | Trạng thái vũ trang bị huỷ theo luật của `order-execution`; feature này **không thêm gì** và **không nói thêm gì** | P0 | test | URD Mục 6 |

## 4. Non-Functional Requirements (NFR)

| ID | Category | Requirement | Priority | Acceptance |
|----|----------|-------------|----------|------------|
| NFR-tilt-meter-001 | reliability | Đường thoát **không chậm hơn một phần nghìn giây** khi chỉ số ở mức cao nhất so với mức thấp nhất | P0 | Đo thời gian từ lúc bấm đóng tới lúc gửi đi, ở mức bình thường và ở mức quá nóng; chênh lệch không đo được |
| NFR-tilt-meter-002 | reliability | Feature này chết hoàn toàn **không** làm giảm khả năng mở, đóng, thoát vị thế | P0 | Diễn tập: tắt hẳn feature rồi chạy trọn chuỗi mở phiên → vào lệnh → đóng lệnh |
| NFR-tilt-meter-003 | reliability | Khoảng khoá **fail-open**: không tính đúng được thì cho phép giao dịch | P0 | test — ngắt mạng và làm hỏng đồng hồ giữa khoảng khoá; việc mở lệnh phải được phép và người chơi thấy rõ |
| NFR-tilt-meter-004 | security | Cấu hình cho phép tilt chạm một thao tác thuộc đường thoát → **sản phẩm không khởi động** | P0 | test — dựng cấu hình sai, kiểm sản phẩm từ chối khởi động và nêu rõ lý do |
| NFR-tilt-meter-005 | correctness | Phép tính chỉ số là **hàm thuần** trên các thành phần hành vi và dữ kiện nhật ký; **không mô hình ngôn ngữ nào tham gia** | P0 | phân tích — soát mọi đầu vào của phép tính |
| NFR-tilt-meter-006 | privacy | Dữ liệu hành vi **không rời khỏi máy chủ của chính người chơi**. AI desk chỉ đọc được ở dạng tổng hợp | P0 | kiểm tra | URD Mục 7 |
| NFR-tilt-meter-007 | data integrity | Chỉ số **không bao giờ được lưu như một đặc điểm của con người**; không tồn tại bản ghi nào cộng dồn chỉ số xuyên phiên | P0 | kiểm tra — soát sơ đồ dữ liệu tìm bất kỳ trường nào tích luỹ xuyên phiên |
| NFR-tilt-meter-008 | usability | Câu nêu lý do (FR-021) phải để người chơi **nhận ra một cảnh báo sai là sai** — dùng lời mô tả chính việc vừa làm, không dùng thuật ngữ nội bộ | P0 | Kiểm khi có sản phẩm: mỗi lần vào mức nóng, người chơi nói được câu đó đúng hay sai |
| NFR-tilt-meter-009 | usability | Khoảng khoá **không leo thang** theo số lần bị khoá trong buổi | P0 | test | URD Mục 6 |
| NFR-tilt-meter-010 | compliance | **Chỉ số này không phải chẩn đoán tâm lý và không phải lời khuyên đầu tư** — nó chỉ nói hành vi vừa rồi khác mức thường của chính người chơi | P0 | kiểm tra | Project profile |
| NFR-tilt-meter-011 | compatibility | Chỉ Chrome desktop; cửa sổ phải đang focus trong phiên (kế thừa `order-execution`) | P0 | kiểm tra |
| NFR-tilt-meter-012 | usability | Giao diện tiếng Anh; tài liệu nghiệp vụ tiếng Việt | P0 | kiểm tra |

## 5. Business Rules

| ID | Rule | Trigger | Implements FR | Source |
|----|------|---------|---------------|--------|
| BR-tilt-meter-001 | **Ma sát chỉ áp cho việc MỞ lệnh mới.** Đóng vị thế, thoát khẩn cấp, nút thoát màn hình và tự khoá phiên không bao giờ bị chạm, ở bất kỳ mức nào | Mọi mức | FR-001, FR-002, FR-003 | URD UN-001 |
| BR-tilt-meter-002 | **Tilt không bao giờ là đầu vào của điểm**, kể cả qua cửa sau — tập "điều kiện đứng ngoài" của `process-score` không bao gồm mức tâm lý | Mọi lần chấm điểm buổi | FR-004, FR-005 | URD UN-002 · `process-score` A-09 |
| BR-tilt-meter-003 | Mọi mốc so sánh là **mức thường của chính người chơi** trên 30 phiên gần nhất; không có chuẩn đám đông nào | Mọi lần tính chỉ số | FR-014 | URD UN-005 |
| BR-tilt-meter-004 | Dưới **5 phiên**: chỉ báo trung tính và **không sinh ma sát nào** | Lịch sử < 5 phiên | FR-015 | URD UN-009 (🔶) |
| BR-tilt-meter-005 | Chỉ **ghi memo** mới hạ chỉ số. Bấm "đã đọc" chỉ tắt dòng cảnh báo và không đổi chỉ số — nếu bấm một nút cũng hạ được thì cơ chế tự vô hiệu hoá | Trong khoảng khoá | FR-033, FR-034 | URD OQ-2 resolved |
| BR-tilt-meter-006 | Hệ thống **không đọc nội dung memo**. Hệ quả (memo rỗng vẫn hạ chỉ số) được chấp nhận có ý thức | Ghi memo lúc bị khoá | FR-035 | URD Mục 6 (🔶 A-06) |
| BR-tilt-meter-007 | **Khoảng khoá đi theo đồng hồ**, sống qua ranh giới phiên. **Chỉ số** thì bắt đầu lại từ trung tính mỗi phiên | Đóng/mở phiên trong lúc khoá chạy | FR-038, FR-039 | URD Mục 3 (🔶 A-05) |
| BR-tilt-meter-008 | Khoảng khoá **fail-open** khi đồng hồ không tin được — cố ý ngược với chốt an toàn khi vắng mặt | Mất kết nối / đồng hồ hỏng | FR-041 | URD UN-013 |
| BR-tilt-meter-009 | Tắt cơ chế có hiệu lực **từ phiên sau**; khoảng khoá đang chạy không bị xoá bởi thao tác tắt | Tắt giữa lúc đang bị khoá | FR-044 | URD UN-010 (🔶 A-08) |
| BR-tilt-meter-010 | Khoảng khoá **không leo thang** theo số lần bị khoá trong buổi | Khoá lần thứ hai trở đi | FR-031 · NFR-009 | URD Mục 6 |
| BR-tilt-meter-011 | Huỷ ARM do tilt bắt đầu khoá là **huỷ bị động** — bộ đếm tự huỷ không tăng | Chạm mức quá nóng khi đang ARM | FR-030 | `order-execution` BR-004 |
| BR-tilt-meter-012 | **Nhả sớm** nút xác nhận ở mức nóng không phải một lần tự huỷ — nhả tay giữa chừng không phải một quyết định | Nhả nút trước khi đủ thời gian giữ | FR-028 | URD (🔶 A-13) · `order-execution` BR-005 |
| BR-tilt-meter-013 | Thành phần thiếu dữ liệu **không áp**; chỉ số không vì thiếu mà tự thấp đi hay cao lên | Thành phần câm | FR-010 | URD Mục 6 |
| BR-tilt-meter-014 | Khi một cơ chế khác **đã xử lý xong** tình huống, feature này **không nói thêm gì** | Mất tay cầm / mất focus | FR-052, FR-054 | URD Mục 6 |

## 6. Error Matrix

| Error ID | Title | Trigger | Severity | Related FR | Screen state | Recovery |
|----------|-------|---------|----------|------------|--------------|----------|
| E-tilt-meter-001 | **Lệnh đóng bị chậm hoặc bị từ chối khi đang ở mức cao** | Ma sát rò rỉ sang đường thoát | **critical** | FR-001 | — | **Đây là lỗi phải sửa ngay, không phải một tình huống chấp nhận được.** Kịch bản nguy hiểm duy nhất của cả feature |
| E-tilt-meter-002 | Kẹt trong khoảng khoá vì đồng hồ không tin được | Mất kết nối, đồng hồ hỏng giữa khoá | **critical** | FR-041 | Cho phép giao dịch, và **nói rõ điều đó vừa xảy ra** | Fail-open có chủ ý, ngược với chốt an toàn khi vắng mặt |
| E-tilt-meter-003 | Đang vũ trang đúng lúc chạm mức quá nóng | Chỉ số vọt lên khi đang ARM | major | FR-030 | Trạng thái vũ trang bị huỷ ngay để đường ghi memo mở ra; nói rõ vì sao | Bộ đếm tự huỷ **không** tăng |
| E-tilt-meter-004 | **Không có đường ghi memo lúc bị khoá** | Đã tắt giọng nói, mic bị từ chối, hoặc không có mic | major | FR-036, FR-037 | Đường bàn phím luôn có mặt và nêu ngay trên màn khoá | Cả hai đường đóng → nói thẳng lần này chỉ còn cách chờ hết giờ. Xem OQ-2 |
| E-tilt-meter-005 | Cần thoát một vị thế đang lỗ nhanh khi đang bị khoá | Giá chạy ngược giữa khoảng khoá | **critical** | FR-001, FR-032 | Thoát bình thường, không chờ, không thêm bước | Màn khoá chỉ rõ đường giảm rủi ro **không bị chạm** vẫn còn nguyên |
| E-tilt-meter-006 | Muốn mở lệnh ngược chiều để giảm rủi ro khi đang bị khoá | Ý định phòng vệ nhưng vẫn là lệnh mở | minor | FR-032 | Vẫn bị khoá — hệ thống không đọc được ý định | Đóng bớt vị thế hoặc thoát khẩn cấp, hai đường không bị chạm |
| E-tilt-meter-007 | Hết 5 phút mà chỉ số vẫn ở mức quá nóng | Hành vi chưa đổi | minor | FR-031 | Khoá lại, nói rõ **lần khoá thứ mấy** và hành vi nào đang giữ chỉ số ở đó | Khoảng khoá **không dài thêm** — không leo thang hình phạt |
| E-tilt-meter-008 | Buổi chưa có lệnh thua nào | Thành phần "vào lại sau thua" câm | minor | FR-010 | Thành phần đó không áp | Chỉ số tính trên phần đo được; không tự thấp đi hay cao lên |
| E-tilt-meter-009 | Phiên mới chỉ có một hai lệnh | "Khối lượng gấp đôi mức thường của phiên" chưa có nghĩa | minor | FR-010 | Thành phần khối lượng hoãn lại cho tới khi đủ mẫu | Người chơi không bị chấm là tăng khối lượng chỉ vì lệnh thứ hai to hơn lệnh đầu |
| E-tilt-meter-010 | Chưa khai playbook nào | Thành phần "luật không đạt" câm | minor | FR-010, FR-022 | Thành phần đó không áp; **câu nêu lý do không nhắc tới luật** | — |
| E-tilt-meter-011 | Lịch sử dưới 5 phiên | Người chơi mới | minor | FR-015 | Chỉ báo **trung tính**, nói rõ đang còn học | **Không sinh ma sát nào.** Checkpoint này chỉ chạy được trong 5 phiên đầu — xem OQ-5 |
| E-tilt-meter-012 | Bật lại sau nhiều tuần tắt | Mức thường có thể đã cũ | minor | FR-017 | Dùng lại 30 phiên gần nhất; quá ít mẫu → quay về trung tính như người mới | Không tính trên dữ liệu đã lỗi thời |
| E-tilt-meter-013 | Mất tay cầm hoặc mất focus lâu rồi quay lại | Trạng thái đã cũ | major | FR-013 | Chỉ số **nguội dần theo thời gian**; vắng đủ lâu thì bắt đầu lại từ trung tính, nói rõ vì sao | Khoảng khoá đang chạy **không** bị ảnh hưởng. Đây đúng loại cảnh báo sai khiến người chơi tắt cơ chế |
| E-tilt-meter-014 | Ngồi im rất lâu rồi mới bắn | Nhịp bấm thấp bất thường | minor | FR-011 | Không phải tín hiệu xấu | Một buổi kiên nhẫn phải cho chỉ số thấp |
| E-tilt-meter-015 | Vừa bị hạn mức chặn vừa đang trong khoảng khoá | Hai cơ chế cùng lúc | minor | FR-053 | Nói rõ cả hai, **phân biệt rõ** hạn mức với ma sát | Hai thứ không dùng chung một câu |
| E-tilt-meter-016 | Mất tay cầm hoặc mất focus ở mức nóng | Hai cơ chế cùng chạm việc mở lệnh | minor | FR-054 | ARM huỷ theo luật `order-execution`; feature này **không thêm gì** | Người chơi chỉ thấy một lý do, không phải hai |
| E-tilt-meter-017 | Đóng-mở phiên trong lúc khoảng khoá đang chạy | Thử vượt khoá bằng cách mở phiên mới | minor | FR-038 | Phần thời gian còn lại vẫn được thi hành ở phiên mới, kèm câu nói rõ vì sao | Chỉ số thì vẫn bắt đầu lại từ trung tính — hai thứ khác nhau |
| E-tilt-meter-018 | Tắt cơ chế ngay giữa lúc đang bị khoá | Thử dùng nút tắt làm đường lách | minor | FR-044 | Việc tắt chỉ có hiệu lực **từ phiên sau**; khoảng khoá đang chạy không bị xoá | — |
| E-tilt-meter-019 | Ghi memo nội dung không liên quan lúc bị khoá | Memo rỗng hoặc lạc đề | minor | FR-035 | Chỉ số **vẫn hạ** | Hệ quả chấp nhận có ý thức của ranh giới không-đọc-nội-dung. Thành thói quen thì xem lại **liều lượng** (OQ-7), không xem lại ranh giới |
| E-tilt-meter-020 | Nhả sớm nút xác nhận ở mức nóng | Giữ chưa đủ lâu | minor | FR-028 | Không lệnh nào phát sinh; trạng thái vũ trang **không mất**; nói rõ cần giữ đủ lâu | **Không** tính là một lần tự huỷ |
| E-tilt-meter-021 | Đổi cặp liên tục trong vài phút | Tín hiệu thật nhưng dễ chấm quá tay | minor | FR-012 | Ghi nhận như một tín hiệu, **một mình không đủ** đẩy lên mức nóng | Câu nêu lý do phải nêu đúng nó, không nêu một hành vi khác |

## 7. Success Criteria

| ID | Outcome nghiệp vụ | Đo bằng | Mốc đạt |
|----|-------------------|---------|---------|
| SC-tilt-meter-01 | Ít vào lại ngay sau một lệnh thua hơn | Số lần mở lệnh trong vòng 60 giây sau một lần đóng lỗ, trung bình mỗi phiên. **Đọc kèm tổng số lệnh mỗi phiên** | Thấp hơn baseline (4 phiên đầu) sau 3 tháng |
| SC-tilt-meter-02 | Ít mở lệnh với khối lượng vọt bất thường hơn | Tỷ lệ lệnh có khối lượng ≥ gấp đôi mức thường của phiên. **Đọc kèm mức thường của phiên theo tháng** | Thấp hơn baseline (4 phiên đầu) sau 3 tháng |
| SC-tilt-meter-03 | Người chơi vẫn còn bật cơ chế sau 3 tháng | Ghi nhận mọi lần đổi trạng thái bật/tắt kèm ngày (FR-045) | Bật ở cuối tháng thứ ba, và không có giai đoạn tắt kéo dài quá một phiên |
| SC-tilt-meter-04 | *(ranh giới tuyệt đối)* Đường thoát không bao giờ bị chạm | Dựng trạng thái quá nóng, rồi ngay trong lúc đó thoát khẩn cấp — kiểm cTrader demo không còn vị thế nào. Kiểm chiều ngược ngay tại đó: một lệnh **mở** phải bị từ chối | 0 lần lệnh đóng bị chậm hoặc bị từ chối. **Một lần là một lỗi phải sửa ngay** |
| SC-tilt-meter-05 | *(ranh giới tuyệt đối)* Tilt không bao giờ vào điểm | Ép chỉ số lên mức quá nóng trong khi giữ nguyên mọi hành vi đặt lệnh; so điểm quy trình với lần chạy cùng hành vi mà tâm lý bình thường | Điểm **không đổi**. Đây là checkpoint **chung với `process-score`** — không feature nào sở hữu nó một mình |
| SC-tilt-meter-06 | Mức ấm thật sự không tốn gì | Ở mức ấm, đo lại chính thao tác bắn | Vẫn là bấm nhả, không thêm bước. Khác biệt duy nhất so với mức bình thường là màu chỉ báo và một dòng chữ |

> **SC-01 và SC-02 dùng baseline từ 4 phiên đầu, không phải 10** — vì cơ chế không sinh ma sát trong 5 phiên
> đầu (FR-015), lấy baseline từ 10 phiên sẽ trộn 6 phiên đã có ma sát vào mốc gốc.
>
> **SC-03 canh gác hai cái đầu.** Một cơ chế bị tắt thì SC-01 và SC-02 vẫn có thể đẹp lên vì lý do khác.
> **Ba thước đo phải đọc cùng nhau.**
>
> **SC-04 và SC-05 là ranh giới, không phải xu hướng.** Cả hai khó kiểm bằng hành vi thật (tốn cả buổi, phụ
> thuộc thị trường) — đó chính là lý do FR-051 (chế độ diễn tập) tồn tại. Xem OQ-3.
>
> **Giới hạn đã biết:** SC-01 và SC-02 đo *hành vi giảm đi*, không đo *quyết định tốt lên*. Vào lại ít hơn
> vì đã bình tĩnh, và vào lại ít hơn vì đã chán, cho ra **cùng một con số**.

## 8. Data Entities (tóm tắt — chi tiết ở `tilt-meter-erd.md`)

| Entity | Ý nghĩa nghiệp vụ | Thông tin nghiệp vụ cần lưu |
|--------|-------------------|------------------------------|
| **Mẫu hành vi** | Một hành vi quan sát được trên tay cầm | Thời điểm · loại hành vi · giá trị · phiên nào. **Không rời khỏi máy chủ người chơi**; AI desk không đọc được từng mẫu |
| **Mức thường của người chơi** | Mốc so sánh tính trên 30 phiên gần nhất | Loại thành phần · giá trị mức thường · số phiên đã dùng để tính · thời điểm cập nhật gần nhất |
| **Trạng thái chỉ số trong phiên** | Chỉ số hiện tại của phiên đang chạy | Phiên nào · mức hiện tại (bốn mức hoặc trung tính) · **hành vi đóng góp lớn nhất** · thành phần nào đang không áp · thời điểm cập nhật |
| **Sự kiện đổi mức** | Mỗi lần chỉ số chuyển vùng | Thời điểm · mức trước · mức sau · **hành vi đã đẩy nó lên** · phiên nào. Nguồn cho `trade-replay` |
| **Khoảng khoá** | Một lần khoá mở lệnh ở mức quá nóng | Thời điểm bắt đầu · độ dài · **lần khoá thứ mấy trong buổi** · lý do kết thúc (hết giờ / ghi memo / fail-open) · phiên bắt đầu và phiên kết thúc (có thể khác nhau) |
| **Mức tilt tại thời điểm bắn** | Trạng thái lúc người chơi bấm nút | Lệnh nào · mức · hành vi đóng góp lớn nhất lúc đó. **Đóng băng, không đổi về sau** |
| **Hai con số theo phiên** | Nguồn số cho SC-01 và SC-02 | Phiên nào · số lần mở lệnh trong 60 giây sau một lần đóng lỗ · số lệnh khối lượng ≥ gấp đôi mức thường của phiên |
| **Sự kiện bật/tắt** | Mỗi lần người chơi đổi trạng thái cơ chế | Ngày · bật hay tắt · lý do (tuỳ chọn, không bắt buộc). Nguồn số duy nhất cho SC-03 |

> **Không tồn tại entity nào cộng dồn chỉ số xuyên phiên** (NFR-007). *Mức thường của người chơi* có tích
> luỹ, nhưng nó là **thước để so**, không phải nhãn dán lên người chơi.

## 9. Flows (tóm tắt — chi tiết ở `tilt-meter-flows.md`)

| Flow | Tóm tắt | Nguồn |
|------|---------|-------|
| Thoát được kể cả ở mức tệ nhất | Đang bị khoá mở lệnh ở mức quá nóng → giá chạy ngược → bấm đóng hoặc thoát khẩn cấp → lệnh đóng đi thẳng, **không thêm bước, không chờ hết khoá** | URD Journey 1 |
| Chuỗi thua rồi vào lại to gấp đôi | Đóng lệnh thua thứ hai → trong một phút tăng khối lượng gấp đôi và vũ trang lại → chỉ báo sang mức nóng kèm câu nêu đúng hành vi → màn xác nhận thêm lý do + mức rủi ro → phải **giữ** nút để bắn | URD Journey 2 |
| Bị khoá, kể ra lý do để mở sớm | Chạm quá nóng → đồng hồ đếm ngược + lời mời ghi memo → thử vũ trang bị từ chối → ghi memo → chỉ số hạ; xuống dưới ngưỡng thì mở lại sớm. Bấm "đã đọc" thì chỉ số **không đổi** | URD Journey 3 |
| Được nhắc mà không mất gì | Chỉ báo sang mức ấm kèm một dòng nêu hành vi → người chơi đọc → vũ trang và bắn **giống hệt** mức bình thường | URD Journey 4 |
| Những phiên đầu, hệ thống chưa biết gì | Phiên 1–4 → chỉ báo trung tính, nói rõ chưa đủ dữ liệu → giao dịch bình thường, **không ma sát nào** dù thao tác nhanh hay chậm | URD Journey 5 |
| Không tin nữa và tắt hẳn | Tắt trong cài đặt (hiệu lực từ phiên sau) → phiên sau không chỉ báo, không cảnh báo, không ma sát → phần còn lại của sản phẩm chạy nguyên vẹn | URD Journey 6 |

## 10. Screens (tóm tắt — chi tiết ở `ascii-wireframe/`)

| Màn hình | Vai trò | Ghi chú ranh giới |
|----------|---------|-------------------|
| **Chỉ báo tilt trên HUD** | Mức hiện tại + **một câu nêu tên hành vi** | Trên HUD do `order-execution` sở hữu. **Không bao giờ chỉ một con số trần.** Biến mất hoàn toàn khi cơ chế bị tắt |
| **Khối bổ sung trên màn xác nhận** | Ở mức nóng: lý do + mức rủi ro của chính lệnh này | Đóng góp nội dung vào màn do `order-execution` sở hữu; **không** thêm bước vào chuỗi xác nhận (ma sát nằm ở cách bấm, không ở số bước) |
| **Màn khoá (mức quá nóng)** | Đồng hồ đếm ngược · câu nêu lý do · **lời mời ghi memo** · lần khoá thứ mấy | Phải nêu rõ đường ghi memo **nào đang dùng được**; cả hai đóng thì nói thẳng chỉ còn cách chờ. Luôn chỉ rõ đóng vị thế và thoát khẩn cấp **không bị chạm** |
| **Mục bật/tắt trong cài đặt** | Bật hoặc tắt hoàn toàn | Thuộc màn cài đặt do `reports-export` sở hữu. Tắt có hiệu lực **từ phiên sau** |
| **Chế độ diễn tập** | Đặt thẳng mức để tự kiểm hai ranh giới | Chỉ tồn tại nếu OQ-3 được chấp nhận |

## 11. Constraints, Dependencies & Assumptions

**Constraints (ràng buộc áp đặt — có source/owner):**

| Ràng buộc | Source / Owner |
|-----------|----------------|
| **Ma sát chỉ áp cho việc mở lệnh mới**; đường thoát không bao giờ bị chạm | URD UN-001 · README (boot-fail) |
| **Tilt không bao giờ là đầu vào của điểm** | URD UN-002 · `process-score` UN-014 |
| **Không mô hình ngôn ngữ nào trong phép tính**; không phân loại cảm xúc, không phát hiện từ ngữ | URD UN-006 — ngoài phạm vi **vĩnh viễn** |
| **Không đo trạng thái giọng nói** — người chơi bỏ hẳn 2026-08-28; mở lại phải qua một CR | URD Mục 3 |
| Hệ thống chỉ biết những gì xảy ra **trên tay cầm và trong nhật ký**. Một cuộc gọi khó chịu, một đêm mất ngủ nằm ngoài tầm quan sát và sẽ không bao giờ được đo | URD Mục 7 |
| Cần ít nhất **5 phiên** trước khi cơ chế bắt đầu chạy; khoảng **30 phiên** trước khi mức thường ổn định | URD Mục 7 |
| Dữ liệu hành vi **không rời khỏi máy chủ của chính người chơi** | URD Mục 7 |
| **Chỉ số này không phải chẩn đoán tâm lý** và không phải lời khuyên đầu tư | `docs/_shared/project-profile.md` |
| Chỉ Chrome desktop; giữ cửa sổ focus suốt phiên | `docs/_shared/operating-environment.md` |

**Dependencies (deliverable do bên khác sở hữu):**

| Phụ thuộc | Owner | Blocks nếu chưa sẵn |
|-----------|-------|---------------------|
| Chuỗi vũ trang–bắn để gắn ma sát vào | `order-execution` (FR-011..FR-017) | FR-026, FR-028, FR-029 |
| Đường thoát để **không** chạm vào | `order-execution` (FR-029) | Không có gì để kiểm chứng FR-001 |
| Luật huỷ ARM bị động và bộ đếm tự huỷ | `order-execution` (FR-018, BR-004) | FR-030, FR-042 |
| **Sự kiện "đã ghi một memo"** — không phải nội dung | `voice-journal` | FR-033 — **đường ra sớm biến mất nếu thiếu** |
| Đường ghi memo bằng **bàn phím**, dùng được lúc bị khoá | `voice-journal` (UN-011) | FR-036 — xem OQ-2 |
| Số luật không đạt trong ba lần bắn gần nhất | `playbook-grading` | FR-008 — thành phần đó không áp nếu thiếu (FR-010) |
| Màn cài đặt làm chỗ đặt nút bật/tắt | `reports-export` | FR-043 |
| Bề mặt hồi tưởng tilt của một buổi tối | `process-score` | Không blocks — dữ liệu vẫn sinh ra, chỉ chưa ai đọc thành xu hướng |
| Dải sự kiện trên dòng thời gian một lệnh | `trade-replay` | Không blocks — như trên |

**Assumptions (tin là đúng — nêu hệ quả nếu sai):**

| Giả định | Invalidate {X} nếu sai |
|----------|------------------------|
| Người chơi này **thực sự có** các hành vi tiền-tilt (URD A-11) | Cơ chế đo đúng nhưng đo một thứ không xảy ra — feature vô dụng, **không có hại** |
| 5 phút là đủ để nguội mà không bị cảm nhận thành hình phạt (URD A-01) | FR-029 sai liều; quá dài thì FR-043 (tắt) thành đường thoát thường xuyên và SC-03 trượt |
| Giữ nút một khoảng ngắn là mức ma sát cảm nhận được mà không gây bực (URD A-02) | FR-026 sai liều — số này cần người chơi **cảm nhận**, không quyết được trên giấy |
| Ba ngưỡng chia bốn mức hợp với chính người chơi này (URD A-03) | FR-023 phải hiệu chuẩn lại; hoặc luôn ở mức ấm, hoặc hay chạm mức nóng oan — xem OQ-4 |
| Bỏ thành phần giọng nói không làm chỉ số kém nhạy đi đáng kể (URD A-04) | FR-007/008 không đủ nhạy; cơ chế bỏ sót đúng những lúc cần nhất. Mở lại **phải qua một CR** |
| Chỉ số sống trong phiên, khoảng khoá đi theo đồng hồ (URD A-05 🔶) | BR-007 sai; đóng-mở phiên thành đường vượt khoá dễ hơn cả nút tắt — xem OQ-6 |
| Ghi memo luôn là hành động có ý thức; không xét nội dung (URD A-06 🔶) | BR-006 bị lợi dụng; memo rỗng thành thói quen — xem lại **liều lượng** (OQ-7), không xem lại ranh giới |
| Người chơi nhận ra cảnh báo sai **là sai** nhờ câu nêu lý do (URD A-07) | NFR-008 không đạt; cảnh báo sai thành phán xét không cãi được, người chơi tắt cơ chế và SC-03 trượt |
| Tắt chỉ có hiệu lực từ phiên sau (URD A-08 🔶) | BR-009 sai; FR-043 trở thành đường lách chính thức của FR-029 |
| Feature này tự giữ hai con số của SC-01/SC-02 (URD A-09 🔶) | FR-049 thiếu → **cả hai thước đo không đo được ở đâu cả** |
| Đường ghi memo luôn dùng được lúc bị khoá (URD A-10 🔶) | FR-036, FR-037 không thoả → khoá 5 phút thành hình phạt thuần — xem OQ-2 |
| Dưới 5 phiên nên im lặng hoàn toàn (URD A-12 🔶) | FR-015 sai; người chơi mất bảo vệ đúng tuần dễ tilt nhất — xem OQ-5 |
| Nhả sớm không phải một lần tự huỷ (URD A-13 🔶) | BR-012 sai; mỗi lần trượt tay ở mức nóng lại được khen là kỷ luật, bộ đếm mất ý nghĩa |

## 12. Open Questions

> **Số OQ đánh riêng cho từng tài liệu.** `OQ-3` của SRS này không nhất thiết là `OQ-3` của PRD
> cùng feature. Neo ổn định để đối chiếu là **số OQ của URD** ghi trong ngoặc *(kế thừa URD OQ-x)*.

* [ ] **OQ-1** *(kế thừa URD OQ-4 — URD đánh dấu "ưu tiên, chốt trước `/srs`")*: Ma sát có áp cho thao tác
  **sửa mức cắt lỗ / chốt lời** không?
  🔶 **Tạm quyết:** **không siết** (FR-003) — giữ nguyên tắc chỉ cản việc mở lệnh mới. Nhất quán với
  `order-execution` OQ-6.
  *Nếu sai:* FR-003 và BR-001 phải phân biệt **nới cắt lỗ ra xa** (hành vi tilt, cần cản) khỏi **siết bảo vệ
  vào gần** (hành vi phòng vệ, không bao giờ được cản) — phần khó nhất của cả feature.
  **Đây là khoảng trống duy nhất còn hở của ranh giới an toàn, và nó hở đúng cái cửa mà một người đang tilt
  hay dùng nhất để tự làm hại mình thêm.**

* [ ] **OQ-2** *(kế thừa URD OQ-9 — "ưu tiên, chốt trước `/srs`", chung với `voice-journal` OQ-8)*: Đường ra
  sớm khỏi khoảng khoá phải luôn dùng được. Ba tình huống làm nó biến mất: đang vũ trang · đã tắt hẳn giọng
  nói · không có mic.
  🔶 **Tạm quyết:** (a) đang vũ trang → FR-030 huỷ ARM ngay khi khoá bắt đầu, nên tình huống này tự giải;
  (b) hai tình huống còn lại → **đường ghi memo bằng bàn phím luôn mở** (FR-036); (c) cả hai đóng → nói thẳng
  chỉ còn cách chờ (FR-037).
  *Nếu sai:* khoá 5 phút thành hình phạt thuần đúng trong những tình huống người chơi ít quyền lực nhất.

* [ ] **OQ-3** *(kế thừa URD OQ-10)*: Có chấp nhận **chế độ diễn tập** (FR-051) cho phép đặt thẳng mức không?
  **Chặn FR-051, và làm SC-04/SC-05 khó kiểm.** Không có nó thì hai ranh giới quan trọng nhất chỉ kiểm được
  bằng cách dựng hành vi thật — tốn cả một buổi và phụ thuộc thị trường.

* [ ] **OQ-4** *(kế thừa URD OQ-5)*: Ba ngưỡng (FR-023) cố định hay người chơi tự chỉnh được sau khi có dữ
  liệu? Cho chỉnh thì nới ngưỡng thành **đường lách hợp pháp** của FR-026/FR-029; không cho chỉnh thì ngưỡng
  sai là hỏng cả cơ chế.

* [ ] **OQ-5** *(kế thừa URD OQ-11)*: Trong **5 phiên đầu** — im lặng hoàn toàn, hay vẫn chạy bằng các thành
  phần hành vi như nguồn thiết kế?
  🔶 **Tạm quyết:** im lặng hoàn toàn (FR-015), và baseline của SC-01/SC-02 lấy từ **4 phiên đầu** cho khớp.
  *Nếu sai:* người chơi mất bảo vệ đúng tuần làm quen và dễ tilt nhất.

* [ ] **OQ-6** *(kế thừa URD OQ-6)*: Hai phiên cách nhau vài giờ trong cùng một ngày thì **chỉ số** có mang
  sang không? (Khoảng **khoá** đã chốt là có — FR-038.)

* [ ] **OQ-7** *(kế thừa URD OQ-7)*: Ghi một memo hạ chỉ số **bao nhiêu**? Nếu một memo luôn đủ để ra khỏi
  mức quá nóng ngay lập tức thì nó thành **thao tác lách** chứ không còn là can thiệp — đặc biệt khi hệ thống
  không đọc nội dung (BR-006).

* [ ] **OQ-8** *(kế thừa URD OQ-8)*: Deck của `process-score` có hiện hai con số của FR-049 thành xu hướng
  nhiều tháng không, hay người chơi đọc thô từ dữ liệu phiên trong ba tháng đầu?

* [ ] **OQ-9** *(kế thừa URD OQ-12 — `ai-desk` đã trả lời)*: `ai-desk-prd.md` OQ-5 đã **tạm quyết không
  nhận** nghĩa vụ nói ở mức tilt nóng.
  🔶 **Tạm quyết:** feature này **tự viết wording** của mình, không phụ thuộc AI — nhất quán với ràng buộc
  "không mô hình ngôn ngữ nào trong phép tính", và tránh được việc AI phán xét trạng thái tâm lý.
  *Nếu sai:* mất một kênh giải thích có sắc thái hơn, đổi lại giữ được ranh giới sạch hơn.

---

> **Nguồn:** `tilt-meter-urd.md` (14 nhu cầu, 6 journey, 20 tình huống ngoại lệ, 3 thước đo, 13 giả định) ·
> `tilt-meter-prd.md` (15 capability) · bốn tài liệu nền `docs/_shared/` · ranh giới nhận từ
> `order-execution`, `voice-journal`, `playbook-grading`, `process-score`, `trade-replay`, `ai-desk`,
> `reports-export`.
>
> **🔶 Bốn quyết định thay user:** OQ-1, OQ-2, OQ-5, OQ-9 — mỗi cái kèm hệ quả nếu sai. **URD đánh dấu OQ-1
> và OQ-2 là "phải chốt trước `/srs`"**; em đã tạm quyết theo hướng an toàn nhất, nhưng cả hai chạm ranh giới
> an toàn nên vẫn cần người chơi xác nhận.
>
> **Tầng 2–4 chưa sinh:** `tilt-meter-flows.md`, `-states.md`, `-erd.md`, use case, user story, AC. Mục 8, 9,
> 10 neo sẵn cho chúng — riêng `-states.md` sẽ quan trọng vì feature này là một máy trạng thái năm vùng.
