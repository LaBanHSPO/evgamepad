---
type: srs
feature: process-score
status: draft
updated: 2026-08-29
links:
  - docs/process-score/process-score-urd.md
  - docs/process-score/process-score-prd.md
  - docs/_shared/project-profile.md
  - docs/_shared/system-overview.md
  - docs/_shared/definitions.md
  - docs/_shared/operating-environment.md
  - docs/order-execution/srs/order-execution-spec.md
  - docs/playbook-grading/srs/playbook-grading-spec.md
  - docs/ai-desk/srs/ai-desk-spec.md
  - docs/tilt-meter/srs/tilt-meter-spec.md
  - docs/voice-journal/srs/voice-journal-spec.md
  - docs/daily-journal/srs/daily-journal-spec.md
  - docs/trade-replay/srs/trade-replay-spec.md
---

# process-score — Software Requirements Specification

## 1. Scope

Đặc tả **một điểm quy trình cho mỗi buổi tối, dựng trên năm trục chỉ-về-quy-trình**, và **deck** — bề mặt
nhìn lại nơi con số đó sống.

**Trong phạm vi:** tính điểm từ năm trục (tuân thủ · chọn lọc · kỷ luật rủi ro · chuẩn bị · nhìn lại) · luật
trục-thiếu-bằng-chứng-rơi-ra-và-chuẩn-hoá-lại · chốt điểm ngay khi đóng phiên · lưu **đầu vào từng trục** để
truy ngược và tính lại · deck mở ở panel quy trình với tiền sau một cú bấm có chủ ý · radar năm trục · bảng
theo playbook · so sánh tháng · trạng thái mẫu-nhỏ · hồi tưởng tilt · ghi lại mỗi lần mở deck giữa phiên ·
cấp các trục cho copilot đọc.

**Ngoài phạm vi:** **sinh ra bất kỳ dữ liệu nào khác của riêng mình** — feature này đọc bằng chứng từ bảy
feature khác · chấm điểm từng lệnh theo luật playbook (`playbook-grading`) · sinh chỉ số chất lượng cơ hội
(`ai-desk`) · đo trạng thái tâm lý (`tilt-meter`) · hạn mức rủi ro và việc thi hành (`order-execution`) · bộ
đếm tự huỷ trên màn chính (`order-execution`) · thu điểm tự chấm và nghi thức chuẩn bị (`daily-journal`) ·
ghi âm (`voice-journal`) · tua lại tape (`trade-replay`) · báo cáo, xuất dữ liệu, sao lưu
(`reports-export`) · chia sẻ, xếp hạng, so sánh điểm với bất kỳ ai.

> **Tính chất trung tâm của tài liệu này — mọi thứ khác tồn tại để bảo vệ nó:**
> **Với cùng mức chuẩn bị và nhìn lại, một tối đứng ngoài đúng lúc không bao giờ chấm thấp hơn một tối giao
> dịch tốt.** Đây là một **bất đẳng thức giữa hai buổi cùng mức chuẩn bị và nhìn lại**, không phải lời hứa
> rằng mọi tối đứng ngoài đều chấm 100.
>
> **Hai ranh giới đi kèm:** (1) **Không có điểm sống để canh giữa phiên** — nếu có, chính điểm này sẽ thay
> chỗ lãi lỗ làm nỗi lo mới, đúng thứ cả sản phẩm sinh ra để chữa. (2) **Tilt không bao giờ là đầu vào của
> điểm**, kể cả qua cửa sau.
>
> **Feature này không sinh dữ liệu của riêng nó** — ngoại lệ duy nhất là bản ghi **số lần mở deck giữa
> phiên**, vì đó là số liệu đo chính rủi ro lớn nhất của nó.

## 2. Actors & Stakeholders

| Actor | Loại | Mục tiêu | Trong scope? |
|-------|------|----------|--------------|
| **Người chơi** | người | Biết mình có đang ra quyết định tốt hơn không, bằng một thước đo **thị trường không quyết hộ** | Có |
| **Bộ tính điểm** | hệ thống | Hàm thuần trên bản ghi → điểm + đầu vào từng trục | Có |
| **`playbook-grading`** | hệ thống | Cấp kết quả chấm luật mỗi lần bắn → **trục tuân thủ** | **Không** — chỉ đọc |
| **`order-execution`** | hệ thống | Cấp kết quả kiểm hạn mức mỗi lần bắn (**trục kỷ luật rủi ro**) và bộ đếm tự huỷ kèm cờ điều kiện đứng ngoài | **Không** — chỉ đọc |
| **`ai-desk`** | hệ thống | Cấp chỉ số chất lượng cơ hội **ghi lại suốt phiên** → **trục chọn lọc**; copilot đọc các trục để huấn luyện | **Không** — chỉ đọc, và **không tính con số nào hiện trên deck** |
| **`daily-journal`** | hệ thống | Cấp kế hoạch đã xác nhận, tự chấm đầu/cuối buổi → **trục chuẩn bị** và **trục nhìn lại**. **Là nguồn thu, deck không được mở luồng thu thứ hai** | **Không** — chỉ đọc |
| **`voice-journal`** | hệ thống | Cấp sự kiện memo → **trục chuẩn bị** và **trục nhìn lại** | **Không** — chỉ đọc |
| **`trade-replay`** | hệ thống | Cấp bản ghi "đã mở replay" → **trục nhìn lại** (deck đọc ở **mức phiên**) | **Không** — chỉ đọc |
| **`tilt-meter`** | hệ thống | Cấp dữ liệu hồi tưởng | **Không** — và **không bao giờ đi vào phép gộp điểm** |

## 3. Functional Requirements (FR)

### 3.1 Điểm và năm trục

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-process-score-001 | Một điểm quy trình cho mỗi buổi tối | Tổng hợp từ **năm trục chỉ-về-quy-trình**: tuân thủ · chọn lọc · kỷ luật rủi ro · chuẩn bị · nhìn lại | P0 | demo | URD UN-001 |
| FR-process-score-002 | Trọng số cộng lại **đúng 1.00** | Bộ trọng số không cộng đúng 1.00 → **hệ thống không chạy** và nói rõ vì sao. **Không âm thầm tự chuẩn hoá** — như vậy người chơi sẽ tin vào một thước đo khác với thứ mình nghĩ mình đã đặt | P0 | test | URD Mục 3, Journey 6 |
| FR-process-score-003 | Không con số kết quả nào là trục | Tỷ lệ thắng, profit factor, lãi lỗ và R **không phải là trục**. Mọi đầu vào đều thuộc phía quy trình | P0 | kiểm tra | URD UN-001 |
| FR-process-score-004 | Trục tuân thủ đọc **đúng bộ luật gateway đã thi hành** | Trục kỷ luật rủi ro chấm lại đúng bộ luật `order-execution` đã thi hành, **không dựng một định nghĩa thứ hai** | P0 | kiểm tra | URD Mục 3 · A-07 |
| FR-process-score-005 | Luật không kiểm được **không nằm trong mẫu số** trục tuân thủ | Đúng như `playbook-grading` đã định nghĩa. Deck **không dựng một định nghĩa tuân thủ thứ hai** | P0 | test | URD Mục 6 · `playbook-grading` FR-024 |

### 3.2 Tính chất trung tâm

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-process-score-006 | **Đứng ngoài đúng lúc không bao giờ chấm thấp hơn** | Với **cùng mức chuẩn bị và nhìn lại**, buổi đứng ngoài không bao giờ chấm thấp hơn buổi giao dịch tốt. Bộ số minh hoạ: tape chết không lệnh nào + chuẩn bị và nhìn lại đầy đủ chấm **100**; tối giao dịch tốt với một luật hụt và một lần bắn thiếu SL chấm **98** | P0 | test | URD UN-002 |
| FR-process-score-007 | Đứng ngoài **không phải tấm vé miễn phí** | Bỏ chuẩn bị thì tối đứng ngoài **cũng tụt điểm** — bất đẳng thức chỉ áp giữa hai buổi **cùng mức chuẩn bị và nhìn lại** | P0 | test | URD UN-002 |
| FR-process-score-008 | Đông cứng trong tape giàu cơ hội đọc khác tối đứng ngoài | Cơ hội tốt nhưng không vào lệnh nào, cùng mức chuẩn bị đầy đủ → chấm **70**, thấp hơn rõ rệt so với 100 của tape chết. **Trục chọn lọc là nơi nói ra điều đó** | P0 | test | URD Mục 6 |
| FR-process-score-009 | Giao dịch quá tay trong tape chết chấm thấp hơn nữa | Với bộ bằng chứng của nguồn (tuân thủ 80, kỷ luật rủi ro 70, nhìn lại 60) → chấm **65**. **Sự rụt rè là lỗi nhẹ hơn sự liều lĩnh, và điểm phải phản ánh đúng thứ tự đó** | P0 | test | URD Mục 6, UN-007 |

### 3.3 Trục thiếu bằng chứng

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-process-score-010 | Trục không có mẫu số **rơi khỏi công thức** | Trọng số còn lại được **chia lại**. Chấm 0 là **phạt việc đứng ngoài** (cấm); chấm 100 là **cho điểm miễn phí** (cũng sai) | P0 | test | URD UN-003 |
| FR-process-score-011 | Trục rơi ra hiện thành **vòng gạch đứt "không áp dụng"** | Trên radar, **không phải nan quạt bằng 0** — nhìn một cái là biết đây là "không có dữ liệu" chứ không phải "làm tệ" | P0 | demo | URD UN-003 |
| FR-process-score-012 | Tiểu mục thiếu bằng chứng rơi ra trước, cả trục rơi sau | **Tiểu mục** thiếu bằng chứng rơi ra và trục chuẩn hoá lại; **rơi hết tiểu mục thì cả trục rơi** thành "không áp dụng" | P0 | test | URD OQ-5 resolved |
| FR-process-score-013 | Chia lại trọng số **chỉ khi không có lệnh nào** | **Một lệnh đã đủ** cho trục tuân thủ và kỷ luật rủi ro có mẫu số thật — nên một buổi chỉ có đúng một lệnh rất tệ **bị chấm đúng như nó tệ** | P0 | test | URD Mục 6 |
| FR-process-score-014 | Buổi không lệnh nào: trục nhìn lại đổi bộ tiểu mục | Chuyển sang bộ tiểu mục **không phụ thuộc lệnh**: tự chấm cuối buổi · có memo · có mở lại một lệnh cũ | P0 | test | URD Mục 6 |
| FR-process-score-015 | Deck nói rõ **điểm đang dựa trên mấy trục** | Để người chơi **không đọc nhầm một con số mỏng thành một đánh giá đầy đủ** | P0 | demo | URD Mục 6 — xem OQ-1 |
| FR-process-score-016 | Không trừ điểm vì tính năng chủ động không dùng | Ghi âm bị tắt hoặc không khả dụng → tiểu mục dựa vào memo **rơi khỏi trục và trục chuẩn hoá lại**. **Nhưng nếu ghi âm sẵn sàng mà người chơi bỏ qua, đó vẫn là một thiếu sót thật và được tính là thiếu** | P1 | test | URD UN-015 |
| FR-process-score-017 | Phiên đầu tiên chưa có lệnh cũ nào để tua lại | Tiểu mục "đã mở replay" **rơi ra** và trục chuẩn hoá lại — buổi đầu tiên **không bị bắt làm một việc bất khả thi** | P1 | test | URD Mục 6 |

### 3.4 Thời điểm chốt và không cộng dồn

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-process-score-018 | Điểm **chốt ngay khi đóng phiên** | Không chờ lệnh giữ qua đêm ngã ngũ. Bốn trục quy trình đã có đủ bằng chứng **tại thời điểm bắn**; trục **nhìn lại** chốt tại thời điểm đóng phiên với bộ tiểu mục có mặt lúc đó | P0 | test | URD UN-004, OQ-1 resolved |
| FR-process-score-019 | **Không có điểm sống để nhìn giữa phiên** | Không tồn tại điểm tạm thời. **Không có gì để làm mới, không có gì để canh** | P0 | test | URD UN-004 |
| FR-process-score-020 | Điểm **không bao giờ xuất hiện trên màn hình chính** | Lúc đang giao dịch, điểm không hiện ở bất kỳ đâu trên HUD | P0 | test | URD UN-004 |
| FR-process-score-021 | Điểm chốt **lặng lẽ**; người chơi tự mở deck khi muốn | **Không có bảng điểm tự bật ra** lúc đóng phiên | P0 | demo | URD Mục 3 |
| FR-process-score-022 | Con số **kết quả** chờ lệnh ngã ngũ, nhưng **không đụng tới điểm** | Chỉ các con số kết quả ở tab tiền mới cập nhật sau, nên **xu hướng theo tháng không thủng lỗ** | P0 | test | URD Mục 6 |
| FR-process-score-023 | Phiên kết thúc bất thường vẫn được chốt điểm | Mất điện, đóng trình duyệt, mất kết nối → buổi tối **vẫn được chốt điểm từ những gì đã ghi được**, và **nói rõ phiên kết thúc bất thường** để người chơi không đọc nhầm một buổi ngắn thành một buổi kém | P0 | test | URD Mục 6 |
| FR-process-score-024 | **Không gì cộng dồn xuyên phiên** | Không chuỗi ngày, không cấp độ, không huy hiệu, không "đã bao nhiêu ngày kể từ". **Không tồn tại bản ghi cộng dồn nào** | P0 | test | URD UN-005 · README |
| FR-process-score-025 | Xu hướng theo tháng là **phân bố kèm số phiên** | Là thứ **đọc để hiểu**, không phải thứ để **giữ cho khỏi đứt**. Đọc lại nhiều phiên để so sánh **không phải là cộng dồn** — thứ bị cấm là một con số chạy dài không bao giờ đặt lại | P1 | demo | URD UN-005 |

### 3.5 Deck: panel quy trình và tab kết quả

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-process-score-026 | Deck mở ra ở **panel quy trình** | Mặc định là panel quy trình, không phải tab kết quả | P0 | demo | URD UN-006 |
| FR-process-score-027 | **Không đồng nào** trước một cú bấm có chủ ý | Con số tiền chỉ hiện sau khi người chơi tự bấm sang tab kết quả. **Không thông báo nào mang theo con số tiền** | P0 | kiểm tra | URD UN-006 |
| FR-process-score-028 | Nội dung panel quy trình | Xu hướng tuân thủ · số lần từ chối · chất lượng cơ hội của buổi tối · điểm tự chấm đầu/cuối buổi đối chiếu với tuân thủ · chênh lệch tháng này so tháng trước | P0 | demo | URD Mục 3 |
| FR-process-score-029 | Nội dung tab kết quả | Lãi theo % · Sharpe kèm cỡ mẫu · profit factor · R trung bình · tỷ lệ thắng · sụt vốn tối đa · bảng theo kiểu setup | P1 | demo | URD Mục 3 |
| FR-process-score-030 | Quay lại panel quy trình thì tiền **biến mất hoàn toàn** | Không sót con số tiền nào | P0 | test | URD Journey 3 |
| FR-process-score-031 | Deck **lấy con số của sàn làm chuẩn** cho tiền | **Không tự dựng lại từ các lần khớp**; lệch thì **nói rõ đang lệch và chỉ về sàn**, không âm thầm hiện con số của mình | P1 | test | URD Mục 6 |

### 3.6 Radar và trục chọn lọc

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-process-score-032 | Biểu đồ radar năm trục | Cho thấy **hình dạng** của buổi tối, không chỉ một con số | P1 | demo | URD UN-007 — xem OQ-5 |
| FR-process-score-033 | Chính **tên trục** nói ra sự khác nhau | Đông cứng (70) và liều lĩnh (65) phải đọc ra khác nhau **nhờ tên trục**, không chỉ nhờ con số | P1 | demo | URD UN-007 |
| FR-process-score-034 | Trần phần cộng điểm cho việc tự huỷ | Mỗi lần tự huỷ **trong lúc đang có điều kiện đứng ngoài** cộng thêm vào trục chọn lọc, nhưng phần cộng có **trần**, và **trục chọn lọc không vượt quá 100**. Huỷ hàng chục lần **cũng không mua thêm được điểm nào** | P1 | test | URD UN-008 |
| FR-process-score-035 | Chỉ quy điểm trên **tập con** có điều kiện đứng ngoài | Bộ đếm trên màn chính vẫn đếm **mọi** lần tự huỷ (luật `order-execution`). Trục này chỉ quy điểm trên tập con — **một bộ đếm gốc, hai cách đọc, không có bộ đếm thứ hai** | P1 | kiểm tra | URD OQ-3 resolved · `order-execution` FR-049 |
| FR-process-score-036 | Tập "điều kiện đứng ngoài" **không bao gồm mức tâm lý** | Nếu bao gồm, tilt đi vào trục chọn lọc **qua cửa sau** và lời hứa "tilt không bao giờ là đầu vào" sẽ sai | P1 | test | URD A-09 (chốt 2026-08-28) · `tilt-meter` FR-005 |
| FR-process-score-037 | AI desk im lặng cả buổi | Còn nhãn mức của phiên → chuyển sang cách đọc **ba mức thô** (chết / bình thường / giàu cơ hội) và **nói rõ đang dùng cách đọc thô**; công thức không đổi, chỉ độ phân giải giảm. **Không còn gì cả** → trục chọn lọc **rơi khỏi công thức** và deck nói rõ | P1 | test | URD Mục 6 — xem OQ-4 |
| FR-process-score-038 | Không bịa hằng số để có một con số trông đẹp | Chỉ số không quy về thang 0–1 một cách có cơ sở → dùng ba mức thô và **ghi rõ trong cấu hình** | P1 | kiểm tra | URD Mục 6 |

### 3.7 Truy ngược và trọng số

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-process-score-039 | Lưu **đầu vào của từng trục**, không chỉ điểm tổng | Đây là điều kiện để FR-040 và FR-041 khả thi — và **không backfill được về sau** | P0 | kiểm tra | URD UN-009 |
| FR-process-score-040 | Đổi trọng số thì lịch sử **tính lại** | Điểm của các buổi cũ được tính lại **từ chính các đầu vào đã lưu** | P0 | test | URD UN-009, Journey 6 |
| FR-process-score-041 | Mọi con số trên deck **đối chiếu được** | Truy ngược được về đầu vào của nó | P0 | kiểm tra | URD UN-009 |
| FR-process-score-042 | Mọi tháng luôn được chấm bằng **cùng một thước** | Nhờ FR-040, xu hướng theo tháng vẫn đọc được sau khi đổi trọng số | P0 | test | URD Journey 6 |
| FR-process-score-043 | Điểm là **hàm thuần trên bản ghi** | Cùng một dữ liệu **luôn** cho ra cùng một điểm. **Không mô hình ngôn ngữ nào tính một con số hiện trên deck**; copilot chỉ được **kể lại** những con số deck đã tính | P0 | test | URD UN-010 |

### 3.8 Bảng playbook, so sánh tháng, mẫu nhỏ

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-process-score-044 | Bảng thống kê theo playbook | Số lệnh · mức tuân thủ · kỳ vọng theo R · MFE/MAE trung bình · hiệu suất trung bình | P1 | demo | URD UN-012 |
| FR-process-score-045 | Con số quy trình mặc định, con số kết quả sau cú bấm | Số lệnh và mức tuân thủ hiện ở panel quy trình; kỳ vọng theo R và các con số kết quả nằm **sau cùng cú bấm có chủ ý** như mọi con số tiền khác | P1 | test | URD UN-012 |
| FR-process-score-046 | Playbook đã ngừng dùng vẫn tra ra được | Với **đầy đủ lịch sử** — deck **không bao giờ mất một tháng** vì một playbook bị bỏ | P1 | test | URD Mục 6 |
| FR-process-score-047 | Chênh lệch tháng này so tháng trước | Trên **mức tuân thủ · tỷ lệ từ chối · điểm tự chấm trung bình** | P1 | demo | URD UN-013 |
| FR-process-score-048 | Phân bố điểm theo tháng **kèm số phiên** | Không bao giờ là một chuỗi ngày | P1 | demo | URD UN-013, UN-005 |
| FR-process-score-049 | Mẫu ít thì **nói thẳng là mẫu ít** | Chỉ số cần mẫu lớn (Sharpe) hiện trạng thái **"chưa đủ phiên"** khi dưới ngưỡng, và **luôn in kèm cỡ mẫu** bên cạnh con số | P1 | test | URD UN-011 |
| FR-process-score-050 | Tháng không có lệnh nào | Profit factor, tỷ lệ thắng, R trung bình đọc là **"không áp dụng"** — **không hiện 0 và không hiện vô cực**. **Điểm quy trình của tháng đó vẫn đọc bình thường** — đó chính là điểm mấu chốt của feature | P1 | test | URD Mục 6 |
| FR-process-score-051 | Mở deck khi **chưa có phiên nào đã đóng** | Nói rõ **chưa có phiên nào** và chỉ đường tới việc chạy phiên đầu — **không hiện khung điểm rỗng, không hiện 0** | P1 | test | URD Mục 6 |
| FR-process-score-052 | Bỏ qua tự chấm nhiều phiên liền | Deck **lùi về hiển thị phần tuân thủ** và **không nhắc nhở** — việc tự chấm vốn là tuỳ chọn | P1 | test | URD Mục 6 |
| FR-process-score-053 | Cùng một số liệu chỉ có **một nơi tính** | Số liệu tháng xuất hiện ở cả deck lẫn bảng tổng của nhật ký → **chỉ deck tính**; nhật ký đọc lại **đúng con số đó**. **Không có định nghĩa thứ hai ở bất kỳ đâu** | P1 | kiểm tra | URD Mục 6 · `daily-journal` BR-006 |

### 3.9 Tilt và copilot

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-process-score-054 | Tilt hiện như **hồi tưởng của buổi tối** | Các dải trạng thái theo thời gian trong phiên · nguyên nhân chính · đối chiếu với **mức tuân thủ**, **không** đối chiếu với lãi lỗ | P1 | demo | URD UN-014 |
| FR-process-score-055 | **Tilt không bao giờ là đầu vào của điểm** | Nó **giải thích, không trừng phạt** | P0 | test | URD UN-014 · `tilt-meter` FR-004 |
| FR-process-score-056 | Tilt không có dữ liệu | Phần hồi tưởng nói rõ **không có dữ liệu**, **không hiện một dải phẳng trông như trạng thái tốt**. **Điểm không đổi**, vì tilt vốn không phải đầu vào | P1 | test | URD Mục 6 |
| FR-process-score-057 | Người chơi đã **tắt hẳn** tính năng đo tâm lý | Phần hồi tưởng **biến mất khỏi deck**, không để lại chỗ trống — khác hẳn trường hợp *mất dữ liệu* ở FR-056 | P1 | test | URD Mục 6 · `tilt-meter` FR-043 |
| FR-process-score-058 | Copilot huấn luyện được **một trục có tên** | Copilot đọc được các trục và huấn luyện đúng trục người chơi nêu tên | P2 | demo | URD UN-017 |
| FR-process-score-059 | Copilot vẫn **chỉ đọc** | Không đặt lệnh, không đóng lệnh, **không ghi được gì**, và **không tự tính ra con số nào** | P0 | test | URD UN-017 · `ai-desk` FR-001 |

### 3.10 Mở deck

| ID | Title | Description | Priority | Verify by | Source |
|----|-------|-------------|----------|-----------|--------|
| FR-process-score-060 | Deck **mở bằng tay cầm** từ menu an toàn | Theo hợp đồng điều hướng chung — mở được ngay khi rời tay cầm, **không phải đi tìm chuột** | P1 | demo | URD UN-016 |
| FR-process-score-061 | Đọc, lọc và đổi tab bằng **chuột và bàn phím** | Đây là màn hình **nhìn lại**, không phải màn hình thao tác nhanh | P1 | kiểm tra | URD UN-016 |
| FR-process-score-062 | Mở deck giữa phiên **không bị chặn** | Chặn thì phải đẻ thêm một trạng thái khoá, mà người chơi **có lý do chính đáng** để mở giữa phiên | P1 | test | URD OQ-2 resolved |
| FR-process-score-063 | **Buổi hôm nay chưa tồn tại trên deck** cho tới khi đóng phiên | Xem được phần lịch sử và xu hướng, nhưng **không có điểm cho buổi tối đang chạy** | P0 | test | URD Mục 6 |
| FR-process-score-064 | **Ghi lại mỗi lần mở deck giữa lúc phiên còn chạy** | Đây là số liệu SC-01 cần để canh chừng **rủi ro lớn nhất của feature**; không ghi thì thước đo đó không đo được. **Không backfill được về sau** | P0 | kiểm tra | URD Mục 3, OQ-4 resolved |
| FR-process-score-065 | Mở deck **huỷ ARM và khoá mở lệnh mới** | Vì deck mở từ menu an toàn (luật `order-execution`), và màn hình **nói rõ điều đó ngay lúc mở** | P1 | test | URD Mục 3 · `order-execution` FR-052 |
| FR-process-score-066 | Mọi panel giữ dòng chữ demo / giải trí / không phải lời khuyên | Không tắt được | P0 | kiểm tra | URD Mục 3 |

## 4. Non-Functional Requirements (NFR)

| ID | Category | Requirement | Priority | Acceptance |
|----|----------|-------------|----------|------------|
| NFR-process-score-001 | correctness | Điểm là **hàm thuần trên bản ghi**; cùng một dữ liệu luôn cho cùng một điểm | P0 | test — dựng lại cùng một buổi 10 lần, điểm trùng khít |
| NFR-process-score-002 | correctness | **Không mô hình ngôn ngữ nào** tính một con số hiện trên deck | P0 | phân tích — soát mọi đầu vào của phép tính |
| NFR-process-score-003 | correctness | Bất đẳng thức của FR-006 đúng với **mọi** cặp buổi cùng mức chuẩn bị và nhìn lại, không chỉ với bộ số minh hoạ | P0 | test — dựng nhiều cặp buổi, kiểm bất đẳng thức giữ nguyên |
| NFR-process-score-004 | data integrity | **Đầu vào từng trục được lưu từ phiên đầu tiên.** Không lưu thì **không backfill được** | P0 | kiểm tra — soát sơ đồ dữ liệu ngay trước phiên đầu |
| NFR-process-score-005 | data integrity | **Không tồn tại bản ghi nào cộng dồn xuyên phiên** trong toàn bộ sơ đồ dữ liệu | P0 | kiểm tra — soát tìm bất kỳ trường nào chạy dài không bao giờ đặt lại |
| NFR-process-score-006 | data integrity | Feature này **không sinh dữ liệu của riêng nó**, trừ bản ghi số lần mở deck giữa phiên (FR-064) | P0 | kiểm tra — soát mọi đường ghi |
| NFR-process-score-007 | reliability | Bộ trọng số không cộng đúng 1.00 → **hệ thống không chạy**, không âm thầm tự chuẩn hoá | P0 | test — dựng cấu hình sai, kiểm sản phẩm từ chối chạy và nêu rõ lý do |
| NFR-process-score-008 | reliability | Feature này chết hoàn toàn **không** làm giảm khả năng mở, đóng, thoát vị thế | P0 | Diễn tập: tắt hẳn deck rồi chạy trọn chuỗi mở phiên → vào lệnh → đóng lệnh |
| NFR-process-score-009 | reliability | Deck **không thi hành gì** — không chặn lệnh, không đổi hạn mức, không sửa điểm của một lệnh. Nó **chỉ đọc và trình bày** | P0 | kiểm tra | URD Mục 7 |
| NFR-process-score-010 | usability | **Không con số tiền nào** ở trạng thái mặc định của bất kỳ panel nào — kể cả trong radar, các bảng, và thông báo | P0 | kiểm tra — rà toàn deck mà không bấm gì |
| NFR-process-score-011 | usability | Deck mở bằng tay cầm; **không thiết kế mọi thao tác đọc bảng cho tay cầm** — đây là màn nhìn lại | P1 | demo |
| NFR-process-score-012 | compatibility | Chỉ Chrome desktop; deck nằm trong cùng ứng dụng web | P0 | kiểm tra |
| NFR-process-score-013 | compliance | **Điểm quy trình không phải lời khuyên đầu tư**; mọi panel giữ dòng chữ demo / giải trí / không phải lời khuyên | P0 | kiểm tra | Project profile |
| NFR-process-score-014 | usability | Giao diện tiếng Anh; tài liệu nghiệp vụ tiếng Việt | P0 | kiểm tra |

## 5. Business Rules

| ID | Rule | Trigger | Implements FR | Source |
|----|------|---------|---------------|--------|
| BR-process-score-001 | **Với cùng mức chuẩn bị và nhìn lại, tối đứng ngoài đúng lúc không bao giờ chấm thấp hơn tối giao dịch tốt.** Đây là bất đẳng thức giữa hai buổi cùng mức, **không phải lời hứa mọi tối đứng ngoài đều chấm 100** | Mọi lần chấm | FR-006, FR-007 · NFR-003 | URD UN-002 |
| BR-process-score-002 | Trục **thiếu bằng chứng rơi khỏi công thức** và trọng số còn lại chia lại. Chấm 0 là phạt việc đứng ngoài (**cấm**); chấm 100 là cho điểm miễn phí | Buổi không lệnh nào · nguồn bằng chứng chưa có | FR-010, FR-012 | URD UN-003 |
| BR-process-score-003 | Chia lại trọng số **chỉ xảy ra khi không có lệnh nào**. Một lệnh đã đủ mẫu số, nên buổi một-lệnh-rất-tệ **bị chấm đúng như nó tệ** | Buổi có ≥1 lệnh | FR-013 | URD Mục 6 |
| BR-process-score-004 | Điểm **chốt ngay khi đóng phiên**, không chờ lệnh giữ qua đêm. Chỉ con số **kết quả** mới chờ ngã ngũ, và việc đó **không đụng tới điểm** | Đóng phiên | FR-018, FR-022 | URD OQ-1 resolved |
| BR-process-score-005 | **Không có điểm sống**, và điểm **không bao giờ xuất hiện trên màn hình chính** | Trong lúc phiên chạy | FR-019, FR-020, FR-063 | URD UN-004 |
| BR-process-score-006 | **Không gì cộng dồn xuyên phiên.** Đọc lại nhiều phiên để so sánh **không phải cộng dồn**; thứ bị cấm là **một con số chạy dài không bao giờ đặt lại** | Luôn luôn | FR-024, FR-025 · NFR-005 | URD UN-005 · README |
| BR-process-score-007 | **Tiền sau một cú bấm có chủ ý** ở mọi panel; không thông báo nào mang theo con số tiền | Mở deck · đổi panel | FR-026, FR-027, FR-030 · NFR-010 | URD UN-006 |
| BR-process-score-008 | **Tilt không bao giờ là đầu vào của điểm** — kể cả qua cửa sau. Tập "điều kiện đứng ngoài" **không bao gồm mức tâm lý** | Mọi lần chấm · quy điểm cho lần tự huỷ | FR-036, FR-055 | URD A-09 (chốt) · `tilt-meter` BR-002 |
| BR-process-score-009 | Phần cộng cho việc tự huỷ có **trần**; trục chọn lọc **không vượt quá 100**. Chỉ những lần huỷ **trong lúc có điều kiện đứng ngoài** mới được tính | Mỗi lần tự huỷ | FR-034, FR-035 | URD UN-008 |
| BR-process-score-010 | **Một bộ đếm gốc, hai cách đọc.** Bộ đếm trên màn chính đếm mọi lần tự huỷ; deck quy điểm trên tập con. **Không có bộ đếm thứ hai** | Mỗi lần tự huỷ | FR-035 | URD OQ-3 resolved · `order-execution` BR-004 |
| BR-process-score-011 | Trọng số phải cộng **đúng 1.00**, nếu không **hệ thống không chạy**. **Không âm thầm tự chuẩn hoá** | Nạp cấu hình trọng số | FR-002 · NFR-007 | URD Journey 6 |
| BR-process-score-012 | Lưu **đầu vào từng trục**, không chỉ điểm tổng — để đổi trọng số thì lịch sử tính lại và mọi con số đối chiếu được | Chốt điểm mỗi buổi | FR-039, FR-040, FR-041 | URD UN-009 |
| BR-process-score-013 | **Một nơi tính, một nơi đọc.** Chỉ deck tính; nhật ký đọc lại đúng con số đó. **Không có định nghĩa thứ hai ở bất kỳ đâu** | Số liệu xuất hiện ở nhiều nơi | FR-053 | URD Mục 6 · `daily-journal` BR-006 |
| BR-process-score-014 | Trục tuân thủ và kỷ luật rủi ro đọc **đúng bộ luật `order-execution` và `playbook-grading` đã định nghĩa**; deck **không dựng định nghĩa thứ hai** | Mọi lần chấm | FR-004, FR-005 | URD A-07 |
| BR-process-score-015 | **Không trừ điểm vì một tính năng người chơi chủ động không dùng.** Nhưng tính năng **sẵn sàng mà bỏ qua** thì vẫn là thiếu sót thật | Ghi âm tắt · replay chưa có | FR-016, FR-017 | URD UN-015 |
| BR-process-score-016 | Deck **luôn lấy con số của sàn làm chuẩn** cho tiền; lệch thì nói rõ và chỉ về sàn | Hiện tab kết quả | FR-031 | URD Mục 6 |
| BR-process-score-017 | Deck **không thi hành gì** — không chặn lệnh, không đổi hạn mức, không sửa điểm của một lệnh | Luôn luôn | NFR-009 | URD Mục 7 |
| BR-process-score-018 | Câu trả lời checklist **muộn không làm tính lại điểm đã chốt**. Nó làm giàu bản ghi của **lệnh**, không đụng tới điểm của **buổi** | Trả lời checklist sau khi phiên đóng | — | URD A-10 (🔶) · `playbook-grading` BR-006 |

## 6. Error Matrix

| Error ID | Title | Trigger | Severity | Related FR | Screen state | Recovery |
|----------|-------|---------|----------|------------|--------------|----------|
| E-process-score-001 | **Bộ trọng số không cộng bằng 1.00** | Cấu hình sai | **critical** | FR-002 | **Hệ thống không chạy**, nói rõ vì sao | **Không âm thầm tự chuẩn hoá** — người chơi sẽ tin vào một thước đo khác với thứ mình nghĩ mình đã đặt |
| E-process-score-002 | Buổi **không lệnh nào cả buổi** | Tối đứng ngoài | major | FR-010, FR-011, FR-014 | Hai trục **rơi khỏi công thức**, trọng số chia lại; radar hiện **vòng gạch đứt "không áp dụng"** | Trục nhìn lại đổi sang bộ tiểu mục không phụ thuộc lệnh |
| E-process-score-003 | **Đông cứng trong tape giàu cơ hội** | Cơ hội tốt nhưng không vào lệnh nào | minor | FR-008 | Chấm **70** — thấp hơn rõ rệt so với 100 của tape chết | Trục chọn lọc là nơi nói ra điều đó. Rụt rè là lỗi nhẹ hơn liều lĩnh |
| E-process-score-004 | Chỉ có đúng **một lệnh, và lệnh đó rất tệ** | Buổi một lệnh | minor | FR-013 | Chia lại trọng số **không xảy ra**; buổi bị chấm **đúng như nó tệ** | Một lệnh đã đủ mẫu số thật |
| E-process-score-005 | **Huỷ hàng chục lần trong một buổi** | Farm điểm | minor | FR-034 | Phần cộng có **trần**; trục chọn lọc không vượt quá 100 | Chỉ những lần huỷ **trong lúc có điều kiện đứng ngoài** mới được tính |
| E-process-score-006 | **AI desk im lặng cả buổi** | Không có chỉ số chất lượng cơ hội | **critical** | FR-037 | Còn nhãn mức → **ba mức thô**, nói rõ đang dùng cách đọc thô. Không còn gì → trục chọn lọc **rơi ra**, deck nói rõ | **Trục làm nên toàn bộ tính chất "đứng ngoài chấm tốt"** mất đầu vào. Xem OQ-4 |
| E-process-score-007 | Chỉ số chất lượng cơ hội không quy về thang 0–1 có cơ sở | Thiếu định nghĩa | minor | FR-038 | Dùng ba mức thô và **ghi rõ trong cấu hình** | **Không bịa hằng số** để có một con số trông đẹp |
| E-process-score-008 | Tắt ghi âm, hoặc không có micro dùng được | Người chơi chủ động không dùng | minor | FR-016 | Tiểu mục dựa vào memo **rơi khỏi trục**, trục chuẩn hoá lại | **Nhưng ghi âm sẵn sàng mà bỏ qua thì vẫn tính là thiếu** |
| E-process-score-009 | Phiên đầu tiên, chưa có lệnh cũ nào để tua lại | Buổi đầu | minor | FR-017 | Tiểu mục "đã mở replay" **rơi ra**, trục chuẩn hoá lại | Buổi đầu tiên **không bị bắt làm một việc bất khả thi** |
| E-process-score-010 | **Các feature nguồn chưa có** | Chưa có playbook, memo, replay, bản chụp kế hoạch | major | FR-012, FR-015 | Áp đúng luật đã có: tiểu mục rơi → trục chuẩn hoá; rơi hết thì cả trục rơi. **Deck nói rõ điểm đang dựa trên mấy trục** | Không cần luật riêng. Xem OQ-1 |
| E-process-score-011 | **Mở deck giữa lúc phiên còn chạy** | Người chơi tự mở | minor | FR-062, FR-063, FR-064 | **Không bị chặn**; nhưng **buổi hôm nay chưa tồn tại trên deck**. Mỗi lần mở như vậy **được ghi lại** | Đây chính là rủi ro số một — nên không chặn mà **đếm** |
| E-process-score-012 | Mở deck khi **chưa có phiên nào đã đóng** | Ngày đầu tiên | minor | FR-051 | Nói rõ **chưa có phiên nào**, chỉ đường tới việc chạy phiên đầu | **Không hiện khung điểm rỗng, không hiện 0** |
| E-process-score-013 | Tháng chưa đủ số phiên cho chỉ số cần mẫu lớn | Hai tháng đầu | minor | FR-049 | Hiện **"chưa đủ phiên"** thay vì con số, và **luôn in kèm cỡ mẫu** | Một con số tự tin dựng trên mẫu quá nhỏ còn tệ hơn không có số |
| E-process-score-014 | **Một tháng không có lệnh nào** | Tháng đứng ngoài | minor | FR-050 | Profit factor, tỷ lệ thắng, R trung bình đọc là **"không áp dụng"** — không hiện 0, không hiện vô cực | **Điểm quy trình của tháng đó vẫn đọc bình thường** — đó chính là điểm mấu chốt của feature |
| E-process-score-015 | Bỏ qua tự chấm nhiều phiên liền | Người chơi không bấm | minor | FR-052 | Deck **lùi về hiển thị phần tuân thủ** và **không nhắc nhở** | Việc tự chấm vốn là tuỳ chọn, hai lần bấm, bỏ được |
| E-process-score-016 | Còn lệnh mở lúc đóng phiên | Vị thế qua đêm | minor | FR-018, FR-022 | Điểm vẫn **chốt ngay khi đóng phiên** | Chỉ con số kết quả ở tab tiền mới chờ ngã ngũ; **xu hướng theo tháng không thủng lỗ** |
| E-process-score-017 | **Phiên kết thúc bất thường** | Mất điện, đóng trình duyệt, mất kết nối | major | FR-023 | Vẫn chốt điểm **từ những gì đã ghi được**, và **nói rõ phiên kết thúc bất thường** | Để người chơi không đọc nhầm một buổi ngắn thành một buổi kém |
| E-process-score-018 | **Đổi trọng số giữa chừng** | Người chơi hiệu chuẩn lại | minor | FR-040, FR-042 | Điểm cũ **tính lại từ đầu vào đã lưu**; mọi tháng luôn được chấm bằng **cùng một thước** | Không có FR-039 thì việc này bất khả thi và **không backfill được** |
| E-process-score-019 | **Số liệu tiền trên deck lệch với tài khoản trên sàn** | Deck tự dựng lại từ các lần khớp | major | FR-031 | Deck **luôn lấy con số của sàn làm chuẩn**; lệch thì **nói rõ đang lệch và chỉ về sàn** | Không âm thầm hiện con số của mình — mất niềm tin vào cả tab kết quả |
| E-process-score-020 | Cùng một số liệu tháng xuất hiện ở **hai nơi** | Deck và bảng tổng của nhật ký | major | FR-053 | **Chỉ deck tính**; nhật ký đọc lại đúng con số đó | Không có định nghĩa thứ hai ở bất kỳ đâu |
| E-process-score-021 | **Tilt không có dữ liệu** | Mất tay cầm giữa phiên, hoặc chưa có tính năng đo tilt | minor | FR-056 | Phần hồi tưởng nói rõ **không có dữ liệu**, **không hiện một dải phẳng trông như trạng thái tốt** | **Điểm không đổi**, vì tilt vốn không phải đầu vào |
| E-process-score-022 | Người chơi đã **tắt hẳn** tính năng đo tâm lý | `tilt-meter` bị tắt | minor | FR-057 | Phần hồi tưởng **biến mất khỏi deck**, không để lại chỗ trống | **Khác hẳn** trường hợp mất dữ liệu ở E-021 |
| E-process-score-023 | Playbook đã ngừng dùng nằm trong bảng so sánh | Người chơi bỏ một sách | minor | FR-046 | Vẫn tra ra được với **đầy đủ lịch sử** | Deck **không bao giờ mất một tháng** vì một playbook bị bỏ |
| E-process-score-024 | Một luật playbook **không kiểm được** | Thiếu dữ liệu lúc chấm | minor | FR-005 | Luật đó **không nằm trong mẫu số** trục tuân thủ, đúng như `playbook-grading` định nghĩa | Deck **không dựng một định nghĩa tuân thủ thứ hai** |
| E-process-score-025 | **Trả lời checklist tự-đánh-giá sau khi phiên đã đóng** | Trả lời muộn | minor | — (BR-018) | Điểm đã chốt **không tính lại**; trục tuân thủ chỉ đọc phần hệ thống tự kiểm tại thời điểm bắn | Câu trả lời muộn làm giàu bản ghi của **lệnh**, không đụng điểm của **buổi**. Xem OQ-7 |

## 7. Success Criteria

| ID | Outcome nghiệp vụ | Đo bằng | Mốc đạt |
|----|-------------------|---------|---------|
| SC-process-score-01 | Điểm quy trình **không trở thành nỗi lo mới** thay chỗ lãi lỗ | Đếm số lần mở deck **trong lúc phiên còn chạy** (FR-064), đọc cuối tháng, **đặt cạnh số lệnh trung bình mỗi tối và chất lượng cơ hội trung bình**. Đọc kèm **tỷ lệ phiên có mở deck sau khi đóng phiên** | Số lần mở giữa phiên **không tăng theo tháng**, đồng thời số lệnh trung bình không tăng khi chất lượng cơ hội không đổi. **Ngưỡng tuyệt đối cố ý chưa đặt** — để phân bố 10 phiên đầu tự nói |
| SC-process-score-02 | Điểm trung bình **đi lên, không phải đi lên nhờ nới thước** | Đọc điểm trung bình theo tháng kèm **số phiên** và **phiên bản trọng số đang dùng**. Đổi trọng số giữa kỳ thì **so lại toàn bộ lịch sử bằng bộ mới trước khi kết luận** | Cao hơn mốc gốc sau 3 tháng, **và mọi tháng đem so đều đã tính lại bằng cùng một bộ trọng số** |
| SC-process-score-03 | Người chơi **tự tin và vui hơn** khi giao dịch | Điểm tự chấm **cuối buổi** trung bình theo tháng, kèm **tỷ lệ phiên có tự chấm** — tỷ lệ này tụt thì con số trung bình mất ý nghĩa | Cao hơn mốc gốc sau 3 tháng, **đọc cạnh điểm quy trình chứ không cạnh lãi lỗ** |
| SC-process-score-04 | *(tính chất tuyệt đối)* Đứng ngoài đúng lúc không bao giờ chấm thấp hơn | Dựng hai buổi **cùng mức chuẩn bị và nhìn lại**: A (tape chết, không lệnh) và B (tape bình thường, một luật hụt + một lần bắn thiếu SL). Rồi kiểm rộng với **mọi** cặp buổi cùng mức | A = **100**, B = **98**; và bất đẳng thức giữ với mọi cặp. **Một cặp vi phạm là hỏng lý do tồn tại của feature** |
| SC-process-score-05 | *(ranh giới)* Tilt không bao giờ vào điểm | **Ép chỉ số tâm lý lên mức quá nóng** trong khi giữ nguyên mọi hành vi đặt lệnh; so điểm với lần chạy cùng hành vi mà tâm lý bình thường | Điểm **không đổi**. **Checkpoint chung với `tilt-meter`** — không feature nào sở hữu nó một mình |
| SC-process-score-06 | *(ranh giới)* Không gì cộng dồn xuyên phiên | Rà toàn deck tìm chuỗi ngày, cấp độ, huy hiệu, "đã bao nhiêu ngày kể từ" | **Không tồn tại ở đâu cả** |

> **SC-01 và SC-02 kéo ngược nhau, và đó là chủ ý.** SC-02 muốn điểm đi lên; SC-01 canh chừng đúng cái giá
> phải trả nếu người chơi bắt đầu **đuổi theo con số đó**. **Phải đọc cùng nhau** — SC-02 đạt trong khi
> SC-01 xấu đi thì feature đang **thất bại** chứ không phải thành công.
>
> **SC-03 là thước đo cấp sản phẩm** mà feature này **đọc hộ**, không truy về một nhu cầu riêng của nó.
>
> **Giới hạn đã biết.** Cả ba thước đo xu hướng đọc từ chính dữ liệu do sản phẩm sinh ra, nên chúng đo *sự
> nhất quán của quy trình*, không đo *chất lượng của quy trình*. SC-02 chặn được việc **nới trọng số**,
> nhưng **không** chặn được việc **hạ chuẩn ở tầng dưới** — nới luật playbook làm trục tuân thủ đẹp lên. Vế
> phòng thủ nằm ở `playbook-grading` SC-02, và **hai thước đo cần đọc cùng nhau**.
>
> **Lá chắn của SC-02 chưa phủ hết.** Trục chọn lọc phụ thuộc **số lệnh kỳ vọng và độ rộng dải** — cấu hình
> riêng của feature, **không phải trọng số** — nên nới chúng vẫn là một đường làm đẹp điểm mà vế "cùng một
> bộ trọng số" **không chặn được**. Xem OQ-2.

## 8. Data Entities (tóm tắt — chi tiết ở `process-score-erd.md`)

| Entity | Ý nghĩa nghiệp vụ | Thông tin nghiệp vụ cần lưu |
|--------|-------------------|------------------------------|
| **Điểm của một buổi tối** | Kết quả chấm một phiên | Phiên nào · điểm tổng · **phiên bản trọng số đã dùng** · thời điểm chốt · **phiên có kết thúc bất thường không** · số trục thật sự tham gia |
| **Đầu vào của một trục** | Bằng chứng thô mà trục dựng trên | Thuộc điểm nào · trục nào · **các tiểu mục và giá trị từng cái** · tiểu mục nào **rơi ra và vì sao** · trục có rơi hết không · **nguồn feature nào cấp**. **Đây là thứ cho phép tính lại khi đổi trọng số — không lưu thì không backfill được** |
| **Bộ trọng số** | Cấu hình năm trục | Phiên bản · trọng số từng trục · **tổng phải đúng 1.00** · thời điểm áp dụng |
| **Cấu hình trục chọn lọc** | Số lệnh kỳ vọng và độ rộng dải | Giá trị · thời điểm hiệu chuẩn. **Không phải trọng số** — nên SC-02 không phủ, xem OQ-2 |
| **Lần mở deck giữa phiên** | Số liệu canh chừng rủi ro số một | Thời điểm · phiên nào (phiên đang chạy). **Ngoại lệ duy nhất của "không sinh dữ liệu riêng"** |

> **Không có entity nào lưu:** điểm chấm từng lệnh (`playbook-grading`) · chỉ số chất lượng cơ hội
> (`ai-desk`) · bộ đếm tự huỷ (`order-execution`) · điểm tự chấm và kế hoạch (`daily-journal`) · memo
> (`voice-journal`) · bản ghi xem lại (`trade-replay`) · dữ liệu tilt (`tilt-meter`). Đó là **ranh giới
> "không sinh dữ liệu của riêng nó"** (NFR-006), không phải một thiếu sót.
>
> **Không có entity nào cộng dồn xuyên phiên** (NFR-005).

## 9. Flows (tóm tắt — chi tiết ở `process-score-flows.md`)

| Flow | Tóm tắt | Nguồn |
|------|---------|-------|
| Đóng phiên rồi mở deck xem tối nay ra sao | Phiên đóng → điểm chốt **lặng lẽ**, không có gì bật ra → người chơi tự mở deck bằng tay cầm → deck mở ở **panel quy trình** → nhìn radar thấy trục nào kéo điểm xuống → **không con số tiền nào trong toàn màn** | URD Journey 1 |
| Tối tape chết, đứng ngoài cả buổi | Chất lượng cơ hội thấp, vũ trang vài lần rồi tự huỷ → đóng phiên không lệnh nào → deck: **100** → radar hiện hai trục là **vòng gạch đứt "không áp dụng"** → trục chọn lọc đạt tối đa | URD Journey 2 |
| Muốn xem tiền — phải tự bấm sang | Deck đang ở panel quy trình → bấm sang tab kết quả (**thao tác có chủ ý**) → thấy các con số kết quả → Sharpe kèm cỡ mẫu, chưa đủ phiên thì nói "chưa đủ phiên" → quay lại panel quy trình, tiền **biến mất hoàn toàn** | URD Journey 3 |
| Nhìn radar tìm trục yếu rồi hỏi copilot đúng trục đó | Nhìn radar thấy một trục lõm → hỏi copilot bằng **tên trục** → copilot trả lời dựa trên **chính các trục deck đã tính**, không bịa con số mới | URD Journey 4 |
| Cuối tháng nhìn lại — tháng này so tháng trước | Mở phần so sánh theo tháng → chênh lệch trên mức tuân thủ, tỷ lệ từ chối, điểm tự chấm → phân bố điểm **kèm số phiên** → **không chuỗi ngày, không cấp độ, không cộng dồn** | URD Journey 5 |
| Đổi trọng số rồi lịch sử tính lại | Đổi trọng số → bộ mới phải cộng đúng 1.00, nếu không **hệ thống không chạy** → điểm các buổi cũ **tính lại từ đầu vào đã lưu** → xu hướng theo tháng vẫn đọc được | URD Journey 6 |
| So sánh xem playbook nào thực sự chạy | Mở bảng theo playbook ở panel quy trình → số lệnh và mức tuân thủ → muốn xem kỳ vọng theo R thì bấm sang tab kết quả → playbook ngừng dùng vẫn tra ra được | URD Journey 7 |
| Xem lại trạng thái tâm lý của một buổi tối | Mở phần hồi tưởng tilt → các dải trạng thái theo thời gian + nguyên nhân chính → đối chiếu với **mức tuân thủ**, không với lãi lỗ | URD Journey 8 |

## 10. Screens (tóm tắt — chi tiết ở `ascii-wireframe/`)

| Màn hình | Vai trò | Ghi chú ranh giới |
|----------|---------|-------------------|
| **Deck — panel quy trình** (mặc định) | Điểm tối nay · radar năm trục · số lần từ chối · chất lượng cơ hội · tự chấm đối chiếu tuân thủ · chênh lệch tháng | **Không con số tiền nào**, kể cả trong radar, bảng, và thông báo. Mở bằng tay cầm từ menu an toàn |
| **Deck — tab kết quả** | Lãi % · Sharpe kèm cỡ mẫu · profit factor · R trung bình · tỷ lệ thắng · sụt vốn tối đa · bảng theo kiểu setup | Chỉ mở sau **một cú bấm có chủ ý**. Quay lại panel quy trình thì tiền **biến mất hoàn toàn** |
| **Radar năm trục** | Hình dạng của buổi tối | Trục rơi ra hiện **vòng gạch đứt "không áp dụng"**, **không phải nan quạt bằng 0**. Hình thức (radar hay bảng 5 dòng) chưa chốt — xem OQ-5 |
| **Bảng theo playbook** | Số lệnh · mức tuân thủ (quy trình) · kỳ vọng R · MFE/MAE (kết quả) | Con số quy trình mặc định; con số kết quả sau cùng cú bấm |
| **Hồi tưởng tilt** | Dải trạng thái trong phiên · nguyên nhân chính · đối chiếu **mức tuân thủ** | **Biến mất hoàn toàn** khi `tilt-meter` bị tắt; khác hẳn trạng thái "không có dữ liệu" |

## 11. Constraints, Dependencies & Assumptions

**Constraints (ràng buộc áp đặt — có source/owner):**

| Ràng buộc | Source / Owner |
|-----------|----------------|
| **Với cùng mức chuẩn bị và nhìn lại, tối đứng ngoài không bao giờ chấm thấp hơn** | URD UN-002 — lý do tồn tại của feature |
| **Điểm chỉ tồn tại sau khi đóng phiên** — không có cách nào xem điểm của buổi đang chạy. **Ràng buộc có chủ ý, không phải giới hạn kỹ thuật** | URD Mục 7 |
| **Feature này không sinh dữ liệu của riêng nó** (trừ bản ghi mở deck giữa phiên) | URD Mục 7 |
| **Tilt không bao giờ là đầu vào của điểm**, kể cả qua cửa sau | URD UN-014 · `tilt-meter` UN-002 |
| **Không gì cộng dồn xuyên phiên** — không chuỗi, không cấp độ, không huy hiệu | `README.md` · URD UN-005 |
| **Deck không thi hành gì** — không chặn lệnh, không đổi hạn mức, không sửa điểm của một lệnh | URD Mục 7 |
| **Không mô hình ngôn ngữ nào tính một con số hiện trên deck** | URD UN-010 |
| Deck **mở bằng tay cầm, đọc bằng chuột và bàn phím** | URD Mục 7 |
| Trọng số các trục, số lệnh kỳ vọng và độ rộng dải là **cấu hình**; tháng đầu là tạm — chưa hiệu chuẩn cho người chơi này | URD Mục 7 |
| Mở deck từ menu an toàn **huỷ ARM và khoá mở lệnh mới** | `docs/_shared/operating-environment.md` |
| Chỉ Chrome desktop; **điểm quy trình không phải lời khuyên đầu tư** | `docs/_shared/project-profile.md` |

**Dependencies (deliverable do bên khác sở hữu):**

> Bảng năm trục ↔ nguồn bằng chứng là căn cứ đọc mục này. **Mọi phụ thuộc dưới đây là phụ thuộc nội dung**,
> không phải hạ tầng.

| Phụ thuộc | Owner | Blocks nếu chưa sẵn |
|-----------|-------|---------------------|
| Kết quả chấm luật mỗi lần bắn → **trục tuân thủ** | `playbook-grading` (FR-018, FR-044) | Trục tuân thủ rơi ra (FR-010 xử lý được) |
| Kết quả kiểm hạn mức mỗi lần bắn → **trục kỷ luật rủi ro** | `order-execution` (FR-009) | Như trên |
| Chỉ số chất lượng cơ hội **ghi lại suốt phiên** → **trục chọn lọc** | `ai-desk` (FR-048, NFR-015) | **Trục làm nên tính chất trung tâm** mất đầu vào — xem OQ-4 |
| Bộ đếm tự huỷ **kèm cờ điều kiện đứng ngoài** | `order-execution` (FR-049) | FR-034, FR-035 |
| Kế hoạch đã xác nhận trước lệnh đầu · tự chấm đầu buổi → **trục chuẩn bị** | `daily-journal` (FR-009, FR-013) | **25% trọng số rơi ra ngày ra mắt** — xem OQ-1 |
| Tự chấm cuối buổi · memo · đã mở replay · checklist đã trả lời → **trục nhìn lại** | `daily-journal` · `voice-journal` · `trade-replay` · `playbook-grading` | Như trên |
| Bản ghi "lệnh nào đã xem lại, lúc nào" | `trade-replay` (FR-049) | Tiểu mục "đã mở replay" rơi ra |
| Dữ liệu hồi tưởng tilt | `tilt-meter` (FR-047, FR-048) | FR-054; **điểm không đổi** vì tilt không phải đầu vào |
| Menu an toàn làm chỗ mở deck | `order-execution` (FR-052) | FR-060, FR-065 |
| Copilot đọc được các trục | `ai-desk` | FR-058 |
| **Danh sách "điều kiện đứng ngoài"** | Người chơi | FR-034, FR-036 — xem OQ-3 |

**Assumptions (tin là đúng — nêu hệ quả nếu sai):**

| Giả định | Invalidate {X} nếu sai |
|----------|------------------------|
| Số lệnh kỳ vọng và độ rộng dải hợp với nhịp giao dịch thật (URD A-01) | Trục chọn lọc **luôn dính 100** hoặc **không bao giờ với tới** — trục quan trọng nhất mất tác dụng phân biệt. Xem OQ-2 |
| Chỉ số chất lượng cơ hội quy về được thang 0–1 có cơ sở (URD A-02) | FR-037 lùi về ba mức thô; độ phân giải giảm nhưng tính chất trung tâm vẫn giữ. Xem OQ-4 |
| Người chơi chấp nhận **một con số duy nhất** và nó **không thay chỗ lãi lỗ làm nỗi lo mới** (URD A-03) | **Toàn bộ cơ chế phản tác dụng** — feature sinh ra để chữa lo âu lại tạo ra nguồn lo âu mới. Đây là **rủi ro số một**; SC-01 đo nó |
| Điểm tự chấm do `daily-journal` thu; deck chỉ hiển thị (URD A-04) | Deck cần một **luồng nhập liệu** — mở rộng phạm vi đáng kể và vi phạm nguyên tắc "không luồng thu thứ hai" |
| Bốn trục quy trình có đủ bằng chứng **tại thời điểm bắn** (URD A-05) | Nếu một trục cần lệnh đóng mới chấm được, **điểm chốt bằng dữ liệu thiếu**. Xem OQ-7 |
| **Bảy nguồn bằng chứng đã có mặt** khi người chơi bắt đầu dùng deck (URD A-06) | **Ngày ra mắt deck chỉ có 3/5 trục** (25% trọng số rơi ra) — **trạng thái mặc định, không phải tình huống hiếm**. Xem OQ-1 |
| Trục tuân thủ đọc **đúng bộ luật gateway đã thi hành** (URD A-07) | Deck báo một lệnh phá luật mà gateway đã cho qua — **người chơi mất niềm tin vào cả hai** |
| Ngưỡng "bao nhiêu lần mở deck giữa phiên là đáng lo" **tự lộ ra từ 10 phiên đầu** (URD A-08) | SC-01 hoặc báo động giả liên tục, hoặc không bao giờ kêu. **Cách lấy số đã chốt; ngưỡng cố ý chưa đặt** |
| Tập "điều kiện đứng ngoài" **không bao gồm mức tâm lý** (URD A-09 — chốt) | **Cái giá đã chấp nhận:** tự huỷ *vì biết mình đang nóng* — hành vi kỷ luật nhất — không được cộng điểm chọn lọc, trừ khi cùng lúc có hoàn cảnh khác |
| Câu trả lời checklist muộn **không** làm tính lại điểm đã chốt (URD A-10 🔶) | Cùng một buổi tối cho **hai con số khác nhau** tuỳ lúc đọc. Xem OQ-8 |

## 12. Open Questions

> **Số OQ đánh riêng cho từng tài liệu.** `OQ-3` của SRS này không nhất thiết là `OQ-3` của PRD cùng feature.
> Neo ổn định để đối chiếu là **số OQ của URD** ghi trong ngoặc *(kế thừa URD OQ-x)*.

* [ ] **OQ-1** *(kế thừa URD A-06, chung với `daily-journal`)*: `daily-journal` ra **trước hay sau** feature
  này? Với thứ tự hiện tại, deck ra mắt với **3/5 trục** (chuẩn bị 0.15 + nhìn lại 0.10 = **25% trọng số rơi
  ra**) — **trạng thái mặc định, không phải tình huống hiếm**.
  🔶 **Tạm quyết:** chấp nhận ra mắt 3/5 trục, và FR-015 buộc deck **nói rõ điểm đang dựa trên mấy trục**.
  *Nếu sai:* nên đổi thứ tự để `daily-journal` ra trước — quyết định lịch, không phải quyết định thiết kế.

* [ ] **OQ-2** *(kế thừa URD OQ-7)*: Hiệu chuẩn lại **số lệnh kỳ vọng và độ rộng dải** — làm khi nào, dựa
  trên bao nhiêu phiên, và đổi giữa chừng thì các tháng cũ có được tính lại như khi đổi trọng số không?
  **Đây là lỗ hổng SC-02 không chặn được**: hai con số này là **cấu hình trục chọn lọc, không phải trọng
  số**, nên nới chúng là một đường làm đẹp điểm mà vế "cùng một bộ trọng số" không phủ tới.

* [ ] **OQ-3** *(kế thừa URD OQ-10)*: Danh sách đóng **"điều kiện đứng ngoài"** gồm đúng những hoàn cảnh nào
  — sắp có tin · chênh lệch giá vượt trần · ngoài khung giờ · không playbook nào đủ luật? **Mức tâm lý đã bị
  loại** (FR-036, chốt 2026-08-28). Câu còn lại là **bốn hoàn cảnh kia đã đủ chưa**. **Chặn FR-034.**
  Em **không tạm quyết** — đây là một danh sách nghiệp vụ đóng, chỉ người chơi mới chốt được.

* [ ] **OQ-4** *(kế thừa URD OQ-11, `ai-desk` đã trả lời)*: `ai-desk` có **ghi lại** chỉ số chất lượng cơ hội
  suốt phiên không? Trục chọn lọc cần **mức trung bình cả phiên**.
  🔶 **Tạm quyết:** `ai-desk` FR-048 và NFR-015 **đã nhận nghĩa vụ ghi lại**. Không có thì FR-037 lùi về **ba
  mức thô** và ghi rõ trong cấu hình.
  *Nếu sai:* **trục chọn lọc — trục làm nên toàn bộ tính chất trung tâm — rơi khỏi công thức.**

* [ ] **OQ-5** *(kế thừa URD OQ-12)*: Hình thức thể hiện năm trục — **biểu đồ radar** (theo nguồn) hay **một
  bảng năm dòng** có cùng thông tin? Với một người dùng, bảng rẻ hơn nhiều. **Chặn FR-032**; chốt lúc vẽ
  wireframe.

* [ ] **OQ-6** *(kế thừa URD OQ-9, chung với `daily-journal` OQ-3)*: Feature này có cung cấp điểm ở mức
  **buổi tối** không, hay chỉ mức **phiên**? Nguồn chỉ định nghĩa điểm theo phiên. Một buổi có hai phiên trở
  lên thì bản đồ nhiệt của `daily-journal` phải tô bằng một con số — **quy tắc gộp nhiều phiên thành một ô
  thuộc feature nào?** Em **không tạm quyết** — nó chạm ranh giới sở hữu giữa hai feature.

* [ ] **OQ-7** *(kế thừa URD A-05)*: Soát **từng tiểu mục của năm trục** — cái nào thật sự chấm được tại
  **thời điểm bắn**, cái nào cần lệnh đóng? Cách xử lý đã chốt (FR-018), nhưng **từng tiểu mục thì chưa
  soát**. Cái nào cần lệnh đóng phải **tách ra như một con số kết quả**, nếu không FR-018 chốt bằng dữ liệu
  thiếu.

* [ ] **OQ-8** *(kế thừa URD A-10, chung với `playbook-grading`)*: Câu trả lời checklist tự-đánh-giá **muộn**
  có làm tính lại điểm đã chốt không?
  🔶 **Tạm quyết:** **không** (BR-018). Câu trả lời muộn làm giàu bản ghi của **lệnh**, không đụng điểm của
  **buổi** — nhất quán với `playbook-grading` FR-043.
  *Nếu sai:* cùng một buổi tối cho hai con số khác nhau tuỳ lúc đọc — phá đúng tính chất FR-018 vừa chốt.

* [ ] **OQ-9** *(chung với `daily-journal` và `trade-replay`)*: Những lần **tự huỷ không dẫn tới lệnh nào**
  hiện ở đâu? Ứng viên: chi tiết một buổi tối ở `daily-journal`, hoặc dải sự kiện ở `trade-replay`, hoặc
  deck. Con số cộng dồn đã chốt thuộc feature này. **Cần chốt một lần cho cả ba tài liệu.**

---

> **Nguồn:** `process-score-urd.md` (17 nhu cầu, 8 journey, 21 tình huống ngoại lệ, 3 thước đo, 10 giả
> định) · `process-score-prd.md` (17 capability) · bốn tài liệu nền `docs/_shared/` · bằng chứng đọc từ
> **bảy** feature nguồn, cộng `tilt-meter` như nguồn thứ tám **chỉ để kể lại, không vào phép gộp**.
>
> **🔶 Ba quyết định thay user:** OQ-1 (chấp nhận ra mắt 3/5 trục), OQ-4 (lùi ba mức thô nếu thiếu), OQ-8
> (câu trả lời muộn không tính lại điểm buổi). **OQ-3 và OQ-6 em cố ý không quyết** — cái đầu là một danh
> sách nghiệp vụ đóng, cái sau chạm ranh giới sở hữu với `daily-journal`.
>
> **Tầng 2–4 chưa sinh:** `process-score-flows.md`, `-states.md`, `-erd.md`, use case, user story, AC.
