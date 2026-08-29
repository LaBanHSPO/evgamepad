---
type: urd
feature: mentor-signals
status: draft
updated: 2026-08-29
links:
  - docs/mentor-signals/brainstorms/mentor-signal-reference.md
  - docs/ai-desk/ai-desk-urd.md
  - docs/ai-desk/srs/ai-desk-spec.md
  - docs/daily-journal/srs/daily-journal-spec.md
  - docs/playbook-grading/srs/playbook-grading-spec.md
  - docs/_shared/system-overview.md
---

# mentor-signals — User Requirements Document

## 1. Purpose

Người chơi có **hai người thầy** mà mình rất tôn trọng. Mỗi thầy đã có hệ thống phân tích riêng và
đã bắn được tín hiệu ra ngoài. Tài liệu này mô tả nhu cầu của người chơi quanh việc đưa tín hiệu
của hai thầy **vào trong game để đọc** — đúng lúc cần, đủ chi tiết để quyết định tốt hơn.

Giá trị người chơi nhắm tới là **thêm một góc nhìn**, không phải **thêm một người ra lệnh**. Vì vậy
nhu cầu quan trọng nhất trong tài liệu này không phải "thấy được tín hiệu thầy" mà là hai nhu cầu
đi kèm nó: **tín hiệu không bao giờ tự thành lệnh và không bao giờ vào chấm điểm** (`UN-002`, đo bằng
`USC-006`), và **lúc bấm cò thì không có ai gật đầu với mình** (`UN-004`). Bỏ hai cái đó đi thì tính
năng này biến thành một dịch vụ sao chép lệnh có thêm ảnh minh hoạ.

> **Về nhãn Evidence.** `brainstorms/mentor-signal-reference.md` là bản ghi một buổi phỏng vấn về
> thứ **định làm** — nó là lời người chơi tự thuật, không phải quan sát hành vi. Vì vậy dữ kiện rút
> từ đó mang nhãn `Confirmed (tự thuật)`, không phải `Observed`. Nhãn `Observed` chỉ dành cho thứ
> đọc được từ mã nguồn, kế hoạch kỹ thuật, hoặc hành vi đã ghi nhận.

### User Problem & Current Experience

| User | Current Situation | Problem | User Consequence | Evidence |
|---|---|---|---|---|
| Người chơi | Tín hiệu thầy nằm trong một ứng dụng khác, mở ở màn hình bên cạnh | Muốn xem thầy nói gì thì phải rời mắt khỏi game giữa phiên | Chuyển cửa sổ giữa phiên là lúc dễ hỏng nhất; cửa sổ game mất focus thì đường đặt lệnh khoá lại | Confirmed (tự thuật) 2026-08-29 · [[docs/mentor-signals/brainstorms/mentor-signal-reference.md\|brainstorm Mục 2]] |
| Người chơi | Đọc một lần rồi tự nhớ trong đầu | Nhớ sai, nhớ thiếu, hoặc quên hẳn giữa lúc tape chạy | Vào lệnh dựa trên một phiên bản đã méo của điều thầy nói, mà không biết là nó đã méo | Confirmed (tự thuật) 2026-08-29 · [[docs/mentor-signals/brainstorms/mentor-signal-reference.md\|brainstorm Mục 2]] |
| Người chơi | Sau phiên, tín hiệu đã trôi mất trong lịch sử ứng dụng khác | Không đối chiếu được *"lúc tôi vào lệnh đó, thầy đang nói gì"* | Mất phần đáng giá nhất của việc có thầy — bài học sau trận. Sự tôn trọng thầy chỉ còn tác dụng **trong** trận, là lúc nó nguy hiểm nhất | Confirmed (tự thuật) 2026-08-29 · [[docs/mentor-signals/brainstorms/mentor-signal-reference.md\|brainstorm Mục 2, Mục 10]] |

## 2. User Types

| Tier | User Type | Context | Primary Goal | Pain Points |
|---|---|---|---|---|
| primary | **Người chơi** | Một mình, buổi tối, Chrome desktop đang focus, tay cầm trong tay | Có thêm góc nhìn của hai người thầy mình tin, mà vẫn là người quyết định | Phải rời game để xem; nhớ sai; sau phiên không đối chiếu được |

> **Không có người dùng phụ.** Thầy A và Thầy B **không phải người dùng của hệ thống** — họ là
> **actor bên ngoài**: bắn tín hiệu vào và không nhận lại gì. Họ không có tài khoản, không đăng nhập,
> không thấy bất cứ thứ gì của người chơi, và không cần biết game này tồn tại. Quan hệ là **một chiều
> vào**, giống cách `ai-desk` đối xử với hệ thống phân tích ngoài.

## 3. Scope Boundaries

### In Scope

* Người chơi nhận được tín hiệu của **hai thầy** ngay trong game, và **biết chắc tín hiệu nào của thầy nào**.
* Người chơi đọc được **đầy đủ nội dung** tín hiệu — hướng, giá vào, SL, TP nếu có, vùng chốt nếu có — kèm **ảnh setup** của thầy.
* Người chơi thấy tín hiệu **đúng lúc đang cân nhắc**, và **không thấy nó lúc đang bấm cò**.
* Người chơi biết **bản mình đang đọc có phải bản mới nhất** của thầy không.
* Người chơi **bật hoặc tắt từng thầy** độc lập, bất cứ lúc nào.
* Người chơi biết **đường nhận tín hiệu của từng thầy còn sống hay đã chết**.
* Người chơi khai **ngôn ngữ của từng thầy**, và nhãn của game bám theo ngôn ngữ đó.
* Sau phiên, người chơi **đối chiếu** lệnh của mình với tín hiệu thầy tại thời điểm vào lệnh.
* Người chơi **xoá riêng** được toàn bộ dữ liệu thầy.

### Out of Scope

* Đặt lệnh theo thầy dưới bất kỳ hình thức nào, **kể cả điền sẵn con số của thầy vào phiếu lệnh** để người chơi tự xác nhận. Đường đặt lệnh thuộc `order-execution`.
* Chấm điểm người chơi theo mức trùng khớp với thầy → luật playbook thuộc `playbook-grading`, điểm quy trình thuộc `process-score`. **Hai tài liệu đó phải ghi ranh giới này vào phần Ngoài phạm vi của họ thì nó mới có hiệu lực** — xem `UN-002` và `OQ-9`.
* Xếp hạng thầy, tính tỷ lệ thắng của thầy, hay gợi ý thầy nào đáng tin hơn.
* Gửi ngược bất cứ thứ gì cho thầy, hay để thầy thấy hoạt động của người chơi.
* **Nguồn tín hiệu thương mại mua ngoài, không do người chơi chọn đích danh** — dịch vụ bán tín hiệu, luồng mạng xã hội không chọn lọc. Hai người thầy do người chơi tự chọn **không** thuộc nhóm này, kể cả nếu có thu phí — xem `OQ-4`.
* Tín hiệu cho cặp ngoài **XAUUSD · EURUSD · GBPUSD · USDJPY**.
* Khung **chi tiết một lệnh** thuộc `daily-journal` và **trục thời gian replay** thuộc `trade-replay`; `UN-009` chỉ **mượn** hai khung đó, giống cách `voice-journal` và `playbook-grading` đang mượn. Việc xuất và sao lưu thuộc `reports-export`.

## 4. User Needs

| ID | User | Context / Trigger | User Need | Expected Outcome | Importance | Evidence |
|---|---|---|---|---|---|---|
| UN-001 | Người chơi | Mọi lúc, với mọi tín hiệu hiện trên màn hình | Biết chắc tín hiệu này **đúng là của thầy mình**, không phải của ai khác gửi vào | Tên thầy do hệ thống xác định từ **đường vào riêng của từng thầy**, không lấy từ nội dung tín hiệu. Tín hiệu không xác định được nguồn thì **không hiện**, và người chơi không phải tự nghi ngờ từng dòng mình đọc | Critical | Confirmed (tự thuật) 2026-08-29 |
| UN-002 | Người chơi | Suốt phiên, và mỗi lần xem lại điểm của một lệnh | Biết chắc tín hiệu thầy **không bao giờ** tự trở thành lệnh, và **không bao giờ** tham gia vào bất kỳ điểm số nào | Không tồn tại đường nào để một tín hiệu thầy phát sinh lệnh, và bản ghi điểm của mọi lệnh **không chứa trường nào của thầy**. Kiểm được bằng `USC-006` thay vì phải tin. Ranh giới này chỉ có hiệu lực khi `playbook-grading` và `process-score` cùng ghi nhận nó — xem `OQ-9` | Critical | Confirmed (tự thuật) 2026-08-29 · Observed: `docs/_shared/system-overview.md` (cold path chỉ sinh ra đơn vị tín hiệu) |
| UN-003 | Người chơi | Đang nhìn biểu đồ, cân nhắc một cơ hội | Thấy thầy đang nói gì **mà không phải rời game** sang cửa sổ khác, và **không phải mở thêm gì cả** | Tín hiệu của cặp đang xem hiện ngay trên dải bối cảnh: tên thầy, hướng, giá vào, SL. Đây là **con đường chính**, không phải lối tắt — `USC-001` tính nó ngang với việc mở bàn làm việc | Critical | Confirmed (tự thuật) 2026-08-29 |
| UN-004 | Người chơi | **Mọi lần vũ trang**, kể cả vũ trang để đóng vị thế hay sửa bảo vệ | **Không có ai gật đầu với mình lúc đó** — chỉ còn mình và playbook của mình | Ngay khi giữ `LT`, dòng tín hiệu thầy **tắt**, chỉ còn con số và giờ đã đọc. Overlay xác nhận vẫn chỉ nói playbook của người chơi và số luật sắp được chấm. Thầy **không có mặt** ở mọi khoảnh khắc quyết định, không riêng lúc mở lệnh mới | Critical | Confirmed (tự thuật) 2026-08-29; mở rộng sang đóng/sửa bảo vệ và phiên khoá: Confirmed 2026-08-29 (OQ-12) |
| UN-005 | Người chơi | Muốn xem kỹ ý thầy trước khi quyết | Đọc được **ảnh setup** và toàn bộ chi tiết, **trong trạng thái không thể lỡ tay bắn** | Ảnh setup và nội dung đầy đủ nằm ở bàn làm việc. Mở bàn làm việc vốn đã huỷ trạng thái vũ trang và khoá mở lệnh mới, nên đọc kỹ là **an toàn theo cấu trúc**, không phải nhờ người chơi tự kiềm chế | High | Confirmed (tự thuật) 2026-08-29 · `ai-desk` UN-014 (cùng cái giá đã biết trước) |
| UN-006 | Người chơi | Mở lên và thấy một tín hiệu | Biết tín hiệu này **mới hay đã cũ**, để không hành động theo một ý kiến đã hết thời sự | Tuổi tín hiệu tính theo **giờ thầy ghi trong tín hiệu**; quá hai giờ thì **phân biệt rõ bằng mắt là đã cũ**, kèm cả giờ thầy ghi lẫn giờ hệ thống nhận, gọi tên khác nhau. Tín hiệu cũ **vẫn đọc được**, không tự biến mất | High | Confirmed (tự thuật) 2026-08-29 (ngưỡng 2 giờ) |
| UN-007 | Người chơi | Thầy gửi tín hiệu thiếu trường — không có TP, không có SL, hoặc thiếu cả trường bắt buộc | Biết là **thầy không gửi**, chứ không phải hệ thống bịa cho đủ hoặc lặng lẽ giấu đi | Trường tuỳ chọn thiếu thì nói thẳng: *"thầy không đặt TP"*. Thiếu **trường bắt buộc** (hướng, giá vào) thì tín hiệu không dùng được, nhưng vẫn hiện **một dòng** *"nhận được một tín hiệu không đọc được từ Thầy A"* — không bỏ câm. Người chơi luôn phân biệt được **thầy im lặng** với **hệ thống im lặng** | High | Confirmed (tự thuật) 2026-08-29; case trường bắt buộc: Confirmed 2026-08-29 (OQ-13) |
| UN-008 | Người chơi | **Gateway trên VPS** ngừng trong lúc thầy bắn — khởi động lại, cập nhật, mất mạng | Biết rằng danh sách mình đang nhìn **có thể đang thiếu**, thay vì tưởng là đã đủ | Tín hiệu đi tới **gateway chạy suốt ngày đêm trên VPS**, không phụ thuộc việc người chơi có mở Chrome hay không — thầy bắn lúc hai giờ chiều thì tối mở game vẫn còn nguyên. Chỉ khi gateway ngừng thì tín hiệu mới mất, và thầy **không gửi lại**; khi đó bàn làm việc nói rõ có khoảng thời gian không nhận được gì. **Phạm vi lời hứa này chỉ gồm bốn cặp game giao dịch, với thầy đang bật** — ngoài phạm vi đó việc mất tín hiệu là **im lặng có chủ ý**, xem A-03 | Medium | Observed: `plans/260824-1506-evening-forex-gold-gamepad/phase-04-ai-desk-sentinel-news-volman.md` (`POST /hooks/tv` xử lý tại `apps/gateway/`, dịch vụ luôn bật) |
| UN-009 | Người chơi | Sau phiên, đang review lệnh đã đóng | Đối chiếu lệnh của mình với **tín hiệu thầy tại đúng thời điểm vào lệnh** | Hai chỗ: khung chi tiết lệnh của `daily-journal` hiện thầy đang có tín hiệu gì lúc đó và cùng chiều hay ngược chiều; trục thời gian của `trade-replay` hiện **vạch giờ thầy bắn** cạnh giờ người chơi vào, để thấy ai trước ai sau. **Chỉ đối chiếu** — không tính điểm, không nhận xét ai đúng ai sai | High | Confirmed (tự thuật) 2026-08-29; chỗ đặt: Confirmed 2026-08-29 (OQ-4) |
| UN-010 | Người chơi | Không muốn nghe một thầy trong giai đoạn nào đó | **Tắt riêng một thầy** mà không phải xoá cấu hình hay dựng lại | Bật/tắt từng thầy độc lập trong cài đặt. Thầy đang tắt thì không nhận, không hiện, và **bàn làm việc nói rõ thầy đó đang tắt** — để im lặng của màn hình không bị đọc nhầm thành im lặng của thầy. Tín hiệu cũ vẫn còn trong nhật ký | Medium | Confirmed (tự thuật) 2026-08-29 |
| UN-011 | Người chơi | Hệ thống bên thầy lỗi và bắn dồn dập | Không bị ngập màn hình vì một sự cố bên ngoài | Quá **30 tín hiệu mỗi giờ mỗi thầy** thì phần dư bị bỏ, kèm **một dòng** cho biết đã bỏ bao nhiêu. Người chơi biết mình đang thiếu bao nhiêu, mà màn hình vẫn sạch | Medium | Confirmed (tự thuật) 2026-08-29 |
| UN-012 | Người chơi | Hai thầy cùng có tín hiệu cho một cặp, ngược chiều nhau | Thấy **cả hai**, không bị hệ thống chọn hộ hay cảnh báo hộ | Hai tín hiệu hiện riêng biệt, xếp theo giờ nhận. Không gộp, không xếp hạng, không đánh dấu mâu thuẫn. Ngược nhau là **chuyện bình thường của thị trường**, không phải lỗi cần hệ thống can thiệp | Medium | Confirmed (tự thuật) 2026-08-29 |
| UN-013 | Người chơi | Nghi đường vào của một thầy đã lộ | **Lấy lại quyền kiểm soát đường vào** của thầy đó mà không mất lịch sử | Đổi được đường vào trong cài đặt; tín hiệu đã nhận giữ nguyên, tín hiệu gửi bằng đường cũ bị bỏ từ đó. Để nhu cầu này kích hoạt được, người chơi phải **tra cứu chủ động sau phiên** được số lần có tín hiệu gửi sai đường trong ngày — xem `UN-014` | Medium | Confirmed (tự thuật) 2026-08-29 · brainstorm Mục 9 R-2. Mức đầu tư giả định là tối thiểu — xem A-07 |
| UN-014 | Người chơi | Vừa khai một thầy lần đầu; và bất cứ lúc nào màn hình im lặng lâu | Phân biệt được **"thầy đang im"** với **"đường nhận đã chết"** | Người chơi tra được **lần cuối mỗi thầy gửi được một tín hiệu hợp lệ là lúc nào**, số tín hiệu bị bỏ hôm nay và vì sao (sai đường vào, thiếu trường bắt buộc, ngoài bốn cặp, vượt trần). Khai thầy lần đầu thì đây cũng là cách xác nhận **đã nối được**. Đây là bản sao đúng chỗ của `ai-desk` UN-004 (*"coach offline"*) | High | **Suy luận** từ nguyên tắc của `UN-008` — xem A-11 |
| UN-015 | Người chơi | Thầy sửa tín hiệu (dời SL, đổi giá vào, thêm TP), hoặc **thầy huỷ / bảo thoát** | Biết bản mình đang đọc là **bản mới nhất** của thầy, và biết thầy đã rút lại chưa | Chỉ **giống nhau ở mọi con số** mới là trùng và được gộp. Khác bất kỳ con số nào là **bản cập nhật**: hiện nối tiếp bản cũ, bản cũ đánh dấu **đã bị thay**. Thầy huỷ thì tín hiệu chuyển sang **đã huỷ**, rút khỏi dải bối cảnh, vẫn đọc được kèm giờ huỷ. Không có đường nào để người chơi đọc một mức giá thầy đã đổi — hoặc một setup thầy đã bỏ — dưới nhãn thời gian còn "mới" | High | Huỷ: Confirmed 2026-08-29 (OQ-10). Định nghĩa "trùng": **suy luận** — xem A-12 |
| UN-016 | Người chơi | Muốn dừng hẳn, hoặc lo dữ liệu của thầy đi ra ngoài | **Xoá riêng** toàn bộ dữ liệu thầy, và biết bản xuất báo cáo có kèm nội dung thầy hay không | Xoá được dữ liệu thầy độc lập với phần còn lại của nhật ký. Nội dung và ảnh biểu đồ của thầy là **tư liệu cá nhân người chơi tự nhận, không phân phối lại** — hành vi khi xuất và sao lưu phải nói rõ, theo yêu cầu Compliance của hồ sơ dự án. Thuộc `reports-export` | Medium | **Suy luận** từ `docs/_shared/project-profile.md` mục Compliance + brainstorm Mục 8. Xem A-13 |

> **Trong nhóm Critical có hai tầng.** `UN-002` và `UN-004` là **nền tảng triết lý** — bỏ một trong
> hai thì tính năng này biến thành dịch vụ sao chép lệnh có thêm ảnh minh hoạ. `UN-001` và `UN-003`
> là **điều kiện hạ tầng** để hai cái kia có ý nghĩa: không xác định đúng thầy thì không có gì đáng
> tin để tham khảo, không thấy được tín hiệu thì không có gì để tham khảo cả. Khi phải cắt, cắt theo
> thứ tự ngược lại — hạ tầng có thể làm đơn giản đi, nền tảng thì không.

## 5. Prioritized User Journeys

> **Quy tắc xếp mức:** mức của journey phản ánh **kết quả journey đó mang lại**, không phải mức cao
> nhất trong danh sách nhu cầu liên quan.
>
> **Đường kiểm chứng độc lập là điện thoại chạy app cTrader** (`A-08`) — nằm ngoài máy Mac nên không
> phá ràng buộc giữ Chrome focus. Riêng Journey 2 cần quan sát đúng lúc giữ cò nên dùng **ghi hình
> màn hình bằng công cụ ngoài**.

### Journey 1: Đọc thầy trước khi quyết định

* **User:** Người chơi
* **Importance:** Critical
* **Trigger:** Đang nhìn một cặp, dải bối cảnh hiện tín hiệu thầy
* **Expected outcome:** Người chơi bước vào quyết định của mình với thông tin của thầy đã nằm sẵn trong đầu — **trước** khi tay chạm cò, không phải sau
* **Related needs:** UN-003, UN-005, UN-006, UN-007, UN-015

1) Dải bối cảnh hiện tên thầy, hướng, giá vào, SL cho cặp đang xem — đọc được **ngay tại chỗ**.
2) Muốn xem ảnh setup thì bấm `Menu` sang bàn làm việc — thao tác này đã huỷ vũ trang và khoá mở lệnh mới.
3) Thấy rõ trường nào thầy không gửi, tín hiệu còn mới hay đã cũ, và có phải bản mới nhất không.
4) Quay lại biểu đồ, tự quyết.

**Independent verification:** Mở app cTrader **trên điện thoại** và xác nhận không có lệnh nào được
tạo trong toàn bộ hành trình này, kể cả khi người chơi đọc rất lâu. Máy Mac không bị đụng tới.

### Journey 2: Giữ cò mà không bị thầy chen vào

* **User:** Người chơi
* **Importance:** Critical
* **Trigger:** Người chơi giữ `LT` để vũ trang — mở lệnh mới, đóng vị thế, hoặc sửa bảo vệ
* **Expected outcome:** Ở giây quyết định, màn hình chỉ còn **playbook của người chơi**. Thầy đã lùi lại thành một con số đã đọc lúc mấy giờ
* **Related needs:** UN-004, UN-002

1) Đang xem, dòng thầy hiện đủ hướng và giá.
2) Giữ `LT` — **dòng thầy tắt**, còn lại con số và giờ đã đọc.
3) Overlay xác nhận hiện playbook đang chọn và số luật sắp được chấm; **không có chữ nào của thầy**.
4) `LT+RT` thì lệnh đi, hoặc buông tay thì thôi. Cả hai đều không liên quan tới thầy.

**Independent verification:** **Ghi hình màn hình bằng công cụ ngoài** (không dùng bản replay của
chính sản phẩm — kiểm hệ thống bằng đầu ra của nó không phải kiểm chứng độc lập). Chạy hai lượt:
một lượt người chơi giữ `LT` bình thường, một lượt cho một tín hiệu mới về đúng lúc đang giữ. Xem
lại bản ghi và xác nhận **dải bối cảnh, tab Thầy và rung tay cầm** đều không đổi ngoài con số đếm.

### Journey 3: Đối chiếu sau phiên

* **User:** Người chơi
* **Importance:** High
* **Trigger:** Sau phiên, mở lại một lệnh đã đóng
* **Expected outcome:** Người chơi thấy được mình đã đi cùng hay đi ngược thầy, và **tự rút ra bài học** mà không bị chấm điểm vì chuyện đó
* **Related needs:** UN-009, UN-002

1) Mở chi tiết một lệnh đã đóng (khung của `daily-journal`).
2) Thấy tín hiệu của từng thầy tại thời điểm vào lệnh, kèm cùng chiều hay ngược chiều.
3) Thấy rõ thông tin này **không** tham gia vào bất kỳ điểm số nào của lệnh đó.

**Independent verification:** Kiểm **cấu trúc**, không kiểm cặp lệnh song sinh: mở bản ghi điểm của
một lệnh bất kỳ và xác nhận **danh sách dữ kiện tham gia chấm không chứa trường nào của thầy**. Phép
kiểm này lặp lại được trên mọi lệnh, không cần dựng hai lệnh giống hệt nhau — điều không tồn tại
trong thực tế.

### Journey 4: Hai thầy nói ngược nhau

* **User:** Người chơi
* **Importance:** Medium
* **Trigger:** Cả hai thầy cùng có tín hiệu cho cặp đang xem, ngược chiều
* **Expected outcome:** Người chơi thấy đủ hai góc nhìn và tự xử lý mâu thuẫn đó — đúng như ngoài đời
* **Related needs:** UN-012, UN-001

1) Dải bối cảnh hiện hai dòng riêng, mỗi dòng một thầy.
2) Không có cảnh báo mâu thuẫn, không gộp, không nói ai đúng.
3) Người chơi vào bàn làm việc đọc kỹ cả hai nếu muốn.

**Independent verification:** Bắn hai tín hiệu ngược chiều từ hai đường vào khác nhau; trong **60
giây** sau đó, xác nhận ba bề mặt **dải bối cảnh · rung tay cầm · overlay xác nhận** không phát sinh
thông báo nào ngoài hai dòng tín hiệu, và tab Thầy hiện đúng hai mục đúng tên thầy.

### Journey 5: Tắt một thầy, hoặc lấy lại đường vào

* **User:** Người chơi
* **Importance:** Medium
* **Trigger:** Người chơi muốn ngừng nghe một thầy, hoặc nghi đường vào đã lộ
* **Expected outcome:** Thay đổi có hiệu lực ngay, và **lịch sử không mất**
* **Related needs:** UN-010, UN-013, UN-014

1) Vào cài đặt, tắt Thầy A hoặc đổi đường vào của thầy đó.
2) Từ đó không nhận tín hiệu mới theo cấu hình cũ.
3) Tín hiệu đã nhận trước đó vẫn còn để đối chiếu sau phiên.

**Independent verification:** Sau khi tắt, bắn một tín hiệu bằng cấu hình cũ; trong **60 giây**, xác
nhận **dải bối cảnh và tab Thầy** không hiện gì mới, đồng thời `UN-014` ghi nhận có một tín hiệu bị
bỏ. Mở lại một lệnh cũ và xác nhận tín hiệu lịch sử của thầy đó vẫn còn nguyên.

## 6. User Exceptions & Edge Conditions

| Situation | User Impact | Expected User-facing Outcome | Related Journey / Need |
|---|---|---|---|
| **Gateway trên VPS** ngừng trong lúc thầy bắn | Tín hiệu mất luôn, thầy không gửi lại | Bàn làm việc nói rõ có khoảng thời gian không nhận được gì. **Không giả vờ danh sách là đầy đủ** | UN-008 |
| **Chrome đóng** trong lúc thầy bắn | Không mất gì cả | Gateway vẫn nhận và lưu. Mở game lên là thấy, kèm **giờ thầy ghi** thật, không phải giờ mở máy | UN-008 · UN-006 |
| Tín hiệu mới về đúng lúc **đang vũ trang** | Nguy cơ bị cắt ngang ở giây nhạy cảm nhất | Con số đếm tăng ngầm; **không có gì bật lên**, không có gì nhấp nháy | J2 · UN-004 |
| Đang **giữ một vị thế mở**, thầy bắn ngược chiều vị thế đó | Dễ tìm cớ để thoát sớm hoặc gồng thêm | Dòng thầy **vẫn hiện** khi chỉ đang quan sát — đó là thông tin. Nhưng vừa giữ `LT` để vũ trang lệnh đóng thì **tắt ngay**, đúng như lúc mở lệnh mới. Không có ngoại lệ cho hành động "an toàn" | UN-004 · A-09 |
| **Phiên đang khoá**, đã chạm hạn mức lỗ ngày, hoặc tilt đang thêm ma sát | Hệ thống chìa ra cơ hội đúng lúc vừa cấm hành động | Tín hiệu **chỉ được ghi nhận, không đòi hành động**: dòng thầy rút khỏi dải bối cảnh, chỉ còn con số; vẫn đọc được trong tab Thầy nếu người chơi chủ động mở. Theo đúng tiền lệ `ai-desk` Mục 6 | UN-004 · A-09 |
| Thầy gửi tín hiệu **thiếu trường bắt buộc** (không hướng, không giá vào) | Tưởng thầy im lặng trong khi hệ thống đang hỏng | Hiện **một dòng** *"nhận được một tín hiệu không đọc được từ Thầy A"*, và đếm vào `UN-014`. Đây là đường mất tín hiệu **dễ xảy ra nhất** (brainstorm R-3: hệ thống bên thầy đổi định dạng — *Thỉnh thoảng*) | UN-007 · UN-014 |
| Thầy gửi lại cùng cặp cùng hướng nhưng **khác con số** | Đọc một mức giá thầy đã đổi, dưới nhãn thời gian còn "mới" | Coi là **bản cập nhật**, hiện nối tiếp bản cũ; bản cũ đánh dấu **đã bị thay**. Chỉ giống nhau ở mọi con số mới là trùng và được gộp | UN-015 |
| **Thầy huỷ / bảo thoát** khỏi một tín hiệu đã gửi | Vào lệnh theo một setup chính thầy đã bỏ | Tín hiệu gốc chuyển sang **đã huỷ**: rút khỏi dải bối cảnh, vẫn đọc được trong tab Thầy kèm giờ huỷ. Đối chiếu sau phiên nói rõ thầy huỷ **trước hay sau** lúc người chơi vào lệnh | UN-015 · UN-009 |
| Thầy bắn cặp mà người chơi đang không nhìn | Có thông tin mà không biết | **Im lặng** — tín hiệu nằm trong bàn làm việc, thấy khi chủ động mở hoặc khi đổi sang cặp đó | UN-003 |
| Thầy bắn cặp **ngoài bốn cặp** game giao dịch | Mất thông tin, không dấu vết | Không hiện ở đâu cả. Người chơi **đã chấp nhận đánh đổi này** để giữ màn hình sạch — xem A-03, và `UN-014` vẫn đếm được số lần | Mục 3 Out of Scope |
| Ảnh setup vượt 2 MB, hoặc mất mạng lúc đang tải | Thiếu phần trực quan | **Giữ nguyên phần chữ**, nói rõ *"ảnh quá lớn, đã bỏ"* hoặc *"chưa tải được ảnh"*. Không mất cả tín hiệu vì một cái ảnh | UN-007 |
| Ảnh quá 90 ngày | Xem lại lệnh cũ thì không còn ảnh | Phần chữ vẫn còn, kèm *"ảnh đã hết hạn lưu"*. Người chơi biết là **đã từng có ảnh**, không tưởng thầy không gửi | UN-009 · UN-007 |
| Thầy bắn dồn dập vì hệ thống bên đó lỗi | Ngập màn hình | Bỏ phần vượt trần, kèm **một dòng** cho biết đã bỏ bao nhiêu trong giờ đó | UN-011 |
| Tín hiệu gửi tới **sai đường vào** | Có người lạ bắn vào | Không hiện gì cả, **không làm phiền người chơi giữa phiên**. Không đặt được lệnh nào. Nhưng **tra cứu được sau phiên** qua `UN-014` — nếu không thì `UN-013` không bao giờ có cớ kích hoạt | UN-001 · UN-013 · UN-014 |
| Đang mở bàn làm việc thì tín hiệu mới về | Đang đọc dở bị đẩy dòng, đọc nhầm | Mục mới chèn lên đầu nhưng **vị trí đang đọc không bị dịch chuyển** | UN-005 |
| Tín hiệu ghi **giờ ở tương lai** (đồng hồ bên thầy lệch) | Không bao giờ đạt mốc hai giờ, ở lại "mới" vĩnh viễn | Tính tuổi từ **giờ gateway nhận**, và nói rõ giờ thầy ghi bị lệch | UN-006 |
| Chỉ mới khai **một thầy**, hoặc chưa thầy nào | `UN-012` và Journey 4 bị đọc như bắt buộc phải có hai | Mọi màn hình hoạt động bình thường với một thầy. `UN-014` cho biết thầy còn lại chưa khai hay khai rồi mà chưa nhận được gì | UN-014 · UN-012 |
| Không thầy nào có tín hiệu cho cặp đang xem | Không rõ là "thầy im", "thầy đang tắt", hay "hệ thống hỏng" | Ba trạng thái này phải **nói khác nhau**. Dữ kiện để phân biệt nằm ở `UN-010` và `UN-014` | UN-007 · UN-010 · UN-014 |

## 7. User-side Constraints

* Người chơi phải **giữ cửa sổ Chrome focus suốt phiên** — đó chính là lý do tính năng này tồn tại, và cũng là ràng buộc khiến "mở app của thầy ở bên cạnh" không phải một giải pháp.
* Đọc kỹ tín hiệu **có giá phải trả và người chơi biết trước**: mở bàn làm việc huỷ trạng thái vũ trang và khoá mở lệnh mới cho tới khi đóng lại. Giống `ai-desk` UN-014.
* Tab Thầy đặt **ngay cạnh tab Tin** — hai nguồn thông tin từ bên ngoài nằm liền nhau để lướt `LB/RB` ít nhất. Vẫn cần thử bằng tay cầm thật ở vòng `/user-flow`.
* **Tối đa hai thầy**, gọi là Thầy A và Thầy B.
* Chỉ nhận tín hiệu cho **XAUUSD · EURUSD · GBPUSD · USDJPY**.
* **Nội dung tín hiệu giữ nguyên ngôn ngữ thầy gửi** — game không dịch, không viết lại, không chuẩn hoá cách diễn đạt của thầy. **Nhãn của game cũng bám theo ngôn ngữ đó**, khai một lần cho từng thầy. Hệ quả chấp nhận có ý thức: hai dòng cạnh nhau trên dải bối cảnh có thể khác ngôn ngữ nhãn.
* **Vùng chốt hiện theo đúng cách thầy gửi** — một dải thì là dải, ba mức rời thì là ba mức. Game không quy đổi về một dạng chung.
* **Ảnh setup chỉ giữ 90 ngày.** Phần chữ giữ lâu hơn. Người chơi cần biết trước để không trông chờ ảnh khi xem lại lệnh cũ.
* Quan hệ với thầy là **một chiều vào**: thầy không nhận lại gì, không thấy gì, và không cần biết game tồn tại.
* Nội dung và ảnh biểu đồ của thầy là **tư liệu cá nhân người chơi tự nhận, không phân phối lại cho ai**.
* Toàn bộ nội dung thầy gửi là tài liệu để đọc **trên tài khoản demo**, không phải lời khuyên đầu tư. Dòng miễn trừ của sản phẩm vẫn áp dụng và không tắt được.

## 8. Assumptions & Validation

| Assumption | Impact if Wrong | Validation Status | Next Action |
|---|---|---|---|
| **A-01** — Hệ thống bên hai thầy đã chạy và bắn được tín hiệu ra ngoài | Toàn bộ tính năng không có đầu vào; không journey nào chạy được | `Confirmed` — người chơi khẳng định 2026-08-29 | Nhận một tín hiệu thật từ mỗi thầy trước khi làm phần còn lại; `UN-014` chính là màn hình để xác nhận việc này |
| **A-02** — Nhãn game **bám theo ngôn ngữ của từng thầy**, không theo ngôn ngữ chung của sản phẩm | Khu vực tín hiệu thầy lệch khỏi phần còn lại của game | `Confirmed` — người chơi chốt 2026-08-29 (OQ-6). Ngoại lệ có chủ ý so với hồ sơ dự án | Không còn việc phải làm |
| **A-14** — Ngôn ngữ của mỗi thầy được **khai một lần trong cài đặt**, game không tự đoán từng tin | Một tín hiệu điển hình (*"BUY 2412.5 SL 2409.0"*) gần như toàn số, **không đủ chữ để đoán ngôn ngữ** — đoán sai thì nhãn lẫn lộn ngay giữa phiên | `Suy luận` — người chơi chốt "nhãn theo ngôn ngữ thầy" nhưng chưa nói khai hay đoán | Xác nhận ở vòng `/srs`; chỉ có 2 thầy nên khai tay là rẻ |
| **A-03** — Tín hiệu cho cặp ngoài bốn cặp bị bỏ **hẳn**, không hiện ở đâu | Người chơi không bao giờ biết thầy đã từng có ý kiến về cặp khác | `Suy luận` từ hai quyết định đã chốt: "bỏ luôn đỡ nhiễu" và "im lặng với cặp không đang xem" | `UN-014` vẫn đếm được số lần, nên thiệt hại có giới hạn. Xem lại sau một tháng dùng thật |
| **A-04** — Người chơi tin hai thầy ở mức **muốn tham khảo**, không ở mức muốn sao chép | Mọi cơ chế bảo vệ trong tài liệu này trở thành vật cản khó chịu thay vì lớp đỡ | `Confirmed` — người chơi khẳng định 2026-08-29 | `USC-003` là **cờ để xem lại**, không phải bằng chứng giả định sai — một tháng đồng ý với thầy một cách chính đáng là chuyện có thật |
| **A-05** — Mỗi tháng có **đủ số lệnh** trùng với lúc thầy có tín hiệu để `USC-001` và `USC-003` có ý nghĩa | Tỷ lệ nhảy lịch bịch trên mẫu quá nhỏ; đánh giá sai cả hai chiều | `Confirmed` — xử lý bằng ngưỡng thay vì bằng giả định: **cả hai tiêu chí đều có mẫu tối thiểu 10 lệnh**, dưới ngưỡng thì không kết luận (OQ-7) | Không còn việc phải làm |
| **A-06** — Mốc của `USC-002` là **trung bình tháng liền trước khi bật** | `USC-002` không có mốc, thành một con số không so được với gì | `Confirmed` — người chơi chốt 2026-08-29 (OQ-8). Tính năng nằm cuối lộ trình nên lúc bật đã có sẵn dữ liệu | Không còn việc phải làm |
| **A-07** — Giữ lịch sử khi đổi đường vào của thầy (`UN-013`) chỉ cần mức đầu tư **tối thiểu** | Đang đầu tư đáng kể cho một rủi ro mà brainstorm xếp là **Hiếm** (R-2) | `Suy luận` — chưa ước lượng công sức | Nếu `/srs` thấy tốn kém, hỏi lại người chơi có chấp nhận bản đơn giản không: đổi đường vào thì mất liên tục lịch sử |
| **A-08** — Đường kiểm chứng độc lập là **điện thoại chạy app cTrader**, nằm ngoài máy Mac nên không phá ràng buộc giữ Chrome focus. Journey 2 dùng **ghi hình màn hình bằng công cụ ngoài** | `USC-006` và Independent verification của Mục 5 mất khả năng kiểm chứng | `Confirmed` — người chơi chốt 2026-08-29 (OQ-11). Đã đóng chung `ai-desk` OQ-8 và `order-execution` OQ-7 | Không còn việc phải làm |
| **A-09** — Dòng thầy **vẫn hiện** khi chỉ đang giữ vị thế, **tắt** ở mọi lần vũ trang (kể cả vũ trang để đóng), và **rút khỏi dải bối cảnh** khi phiên đang khoá | Hệ bảo vệ có lỗ đúng ở hai chỗ dễ tổn thương nhất | `Confirmed` — người chơi chốt 2026-08-29 (OQ-12) | Không còn việc phải làm |
| **A-10** — Tín hiệu thiếu **trường bắt buộc** vẫn hiện một dòng báo, thay vì bỏ câm như brainstorm | Đường mất tín hiệu dễ xảy ra nhất vẫn im lặng; `UN-008` bị phá | `Confirmed` — người chơi chốt 2026-08-29 (OQ-13), **thay đổi có chủ ý so với brainstorm Mục 7.1** | Đã đồng bộ ngược vào brainstorm |
| **A-11** — Người chơi cần biết **đường nhận còn sống hay đã chết** (`UN-014`) | Thầy đổi định dạng thứ Hai, thứ Sáu người chơi vẫn tưởng thầy im lặng | `Suy luận` từ nguyên tắc `UN-008` và tiền lệ `ai-desk` UN-004 | Xác nhận với người chơi ở vòng `/srs` |
| **A-12** — Định nghĩa "trùng" là **giống nhau ở mọi con số** | Bản cập nhật của thầy bị nuốt, hoặc mọi cập nhật thành tín hiệu mới gây mâu thuẫn giả | `Confirmed` — người chơi chốt 2026-08-29 (OQ-15) | Không còn việc phải làm |
| **A-13** — Người chơi cần **xoá riêng** dữ liệu thầy và biết hành vi khi xuất/sao lưu | Ảnh biểu đồ của thầy đi vào bản xuất mà người chơi không biết; vi phạm yêu cầu Compliance của hồ sơ dự án | `Suy luận` từ `docs/_shared/project-profile.md` mục Compliance | Nối với `reports-export` ở vòng `/srs` |

## 9. User Success Criteria

> Ba tiêu chí đầu bù nhau và **phải đọc cùng nhau**. `USC-001` đo thói quen đọc, `USC-002` canh chất
> lượng quyết định, `USC-003` canh việc người chơi còn giữ được chính kiến. Chỉ nhìn `USC-001` thì
> một người bấm theo thầy mỗi lệnh vẫn đạt điểm tuyệt đối.
>
> Hệ quả bắt buộc: ở **bất cứ đâu** hai con số này được trình bày cho người chơi, `USC-001` và
> `USC-003` phải **hiện cùng nhau**. Tách rời chúng là làm hỏng chính cơ chế bảo vệ mà tài liệu này
> dựng lên.
>
> `USC-006` khác hẳn bốn cái còn lại: nó là một **ranh giới tuyệt đối được kiểm toán**, không phải
> một chỉ số cải thiện theo thời gian. Nó dùng **chung một lần kiểm toán vị thế** với `ai-desk`
> `USC-002` và `order-execution` `USC-001` để ba tài liệu không ra kết quả lệch nhau.

| ID | User Outcome | Baseline | Target | Measurement | Review Period |
|---|---|---|---|---|---|
| USC-001 | Người chơi đọc thầy **trước** khi quyết, không phải sau khi đã vào lệnh | **Chưa có** — tính năng chưa tồn tại | Trong các lệnh mà lúc đó thầy có tín hiệu, **từ 8/10 lệnh trở lên** người chơi đã thấy tín hiệu trước khi vũ trang. **Mẫu tối thiểu 10 lệnh**; dưới ngưỡng thì ghi *"chưa đủ dữ liệu"*, không kết luận | Sự kiện tính là *"tín hiệu của **đúng cặp sắp vào lệnh** đã hiển thị cho người chơi — **trên dải bối cảnh hoặc trong tab Thầy** — trong vòng **30 phút** trước lúc vũ trang"*. Tính cả hai con đường, để không phạt `UN-003` là con đường thiết kế chính | Hằng tháng |
| USC-002 | Chất lượng quyết định **không tụt** sau khi có thầy trong game | Điểm quy trình trung bình của **tháng liền trước khi bật** tính năng (OQ-8) | Điểm quy trình trung bình tháng này **không thấp hơn** mốc | So điểm quy trình trung bình theo tháng | Hằng tháng |
| USC-003 | Người chơi **vẫn giữ được chính kiến** — thầy là một góc nhìn, không phải mệnh lệnh | **Chưa có** | Tỷ lệ *lệnh vào ngược chiều thầy ÷ lệnh có tín hiệu thầy lúc vào* **lớn hơn 0**, với mẫu tối thiểu **10 lệnh có tín hiệu** trong tháng. Dưới mẫu đó thì chỉ số **không kết luận gì** | Người chơi **tự rà tay** trong nhật ký cuối tháng — **không phải một bộ đếm hiển thị trong sản phẩm**, vì Mục 3 đã loại thống kê trùng khớp. Đây là **dấu hiệu cần điều tra**, không phải tiêu chí đạt/không đạt | Hằng tháng |
| USC-004 | Đường đặt lệnh **không hề bị chạm** bởi tính năng này | Không áp dụng — đây là phép kiểm thứ tự, không phải chỉ số | Chuỗi vũ trang → bắn cho ra **rung tay cầm và xác nhận khớp lệnh y như nhau** ở cả hai lượt: một lượt chạy trong lúc thầy đang bắn dồn dập, một lượt chạy khi lane thầy đã tắt hẳn | Kiểm **thứ tự quan sát được, không bấm giờ** — theo đúng cách `ai-desk` Journey 5 đã giải bài toán này | Hằng tháng, và sau mỗi lần đổi phần nhận tín hiệu |
| USC-005 | Phần đối chiếu sau phiên **thật sự được đọc** | **Chưa có** | Phần đối chiếu được mở ở **ít nhất một nửa** số phiên có lệnh | Đếm **hành động chủ động** của người chơi: mở khối thầy trong chi tiết lệnh, hoặc bật lớp vạch thầy trên trục thời gian replay. **Không** tính việc mở khung chi tiết lệnh nói chung — đó là hệ quả, không phải sự quan tâm (OQ-4 resolved 2026-08-29) | Hằng tháng |
| USC-006 | *(ranh giới tuyệt đối)* Tín hiệu thầy **không bao giờ** đặt được lệnh và **không bao giờ** vào chấm điểm | **0** — không phải chỉ số cần cải thiện | **(a)** 0 vị thế trên cTrader demo không tương ứng với một lần xác nhận hai tay của người chơi. **(b)** 0 lần bản ghi điểm của một lệnh chứa trường nào của thầy | (a) dùng **chung lần kiểm toán vị thế** với `ai-desk` `USC-002` và `order-execution` `USC-001`. (b) rà bản ghi điểm của toàn bộ lệnh trong tháng. Mọi chênh lệch là **sự cố nghiêm trọng phải điều tra ngay** | Hằng tháng, và ngay khi nghi ngờ |

## 10. Open Questions

* [x] **OQ-1**: **Resolved 2026-08-29 — tính năng riêng.** `mentor-signals` đứng riêng ở `docs/mentor-signals/`, dùng lại lane tín hiệu ngoài của `ai-desk` nhưng có danh tính thầy, lịch sử và luật bật/tắt riêng. Lý do: `ai-desk` là bàn AI và luật máy; hai người thầy thật nằm trong đó làm mờ nghĩa của cả hai.
* [x] **OQ-2**: **Resolved 2026-08-29 — đã sửa ngay.** `ai-desk-urd.md` Mục 3 và `ai-desk-spec.md` Mục "Ngoài phạm vi" nay ghi *"nguồn thương mại mua ngoài, không do người chơi chọn đích danh"*, và nói rõ **không bao gồm** thầy do người chơi tự chọn — kể cả nếu thầy có thu phí. Hai tài liệu hết mâu thuẫn.
* [x] **OQ-3**: **Resolved 2026-08-29 — đặt tab Thầy ngay cạnh tab Tin.** Hai tab "thông tin đến từ bên ngoài" nằm liền nhau nên lướt ít hơn. Vẫn là sáu tab, chỉ đổi thứ tự. **Cần thử lại bằng tay cầm thật ở vòng `/user-flow`** — sáu tab lướt nhanh hay chậm là chuyện cảm giác, không suy ra được trên giấy.
* [x] **OQ-4**: **Resolved 2026-08-29 — cả hai.** Khối *"lúc anh vào, thầy đang có gì"* nằm ở khung chi tiết lệnh của `daily-journal`; đồng thời tín hiệu thầy hiện thành **vạch trên trục thời gian của `trade-replay`**, để thấy đúng giây thầy bắn so với giây người chơi vào. Hệ quả: `mentor-signals` mượn khung của **hai** feature, nên đợt đồng bộ ở `OQ-9` gồm **bốn** tài liệu chứ không phải ba.
* [x] **OQ-5**: **Resolved 2026-08-29 — theo đúng thầy gửi.** Thầy gửi một dải thì hiện dải, gửi ba mức rời thì hiện ba mức. Game **không quy đổi, không chuẩn hoá** — nhất quán với nguyên tắc giữ nguyên gốc: quy ba mức về một dải là làm mất ý *"chốt ba lần"* của thầy.
* [x] **OQ-6**: **Resolved 2026-08-29 — nhãn game bám theo ngôn ngữ của từng thầy.** Tín hiệu của Thầy A hiện với nhãn cùng ngôn ngữ thầy A nhắn, tương tự Thầy B. Hai dòng cạnh nhau có thể khác ngôn ngữ nhãn — đó là chấp nhận có ý thức, đổi lấy việc mỗi khối đọc liền mạch. **Ngôn ngữ khai một lần cho từng thầy trong cài đặt, game không tự đoán từng tin** — xem A-14. Đây là ngoại lệ có chủ ý so với hồ sơ dự án (*"giao diện sản phẩm: tiếng Anh"*), giới hạn trong khu vực tín hiệu thầy.
* [x] **OQ-7**: **Resolved 2026-08-29 — dưới 10 lệnh thì không kết luận.** Cùng mẫu tối thiểu với `USC-003` cho đồng bộ. Dưới ngưỡng thì ghi *"chưa đủ dữ liệu"*, không ghi đạt và cũng không ghi trượt.
* [x] **OQ-8**: **Resolved 2026-08-29 — trung bình tháng liền trước khi bật.** Tính năng này nằm cuối lộ trình nên lúc bật thì sản phẩm đã chạy một thời gian và điểm quy trình đã có sẵn.
* [x] **OQ-9**: **Resolved 2026-08-29 — cập nhật ở vòng `/srs`, gộp một lần.** Ba tài liệu `playbook-grading`, `process-score`, `daily-journal` hiện chưa biết `mentor-signals` tồn tại (đã kiểm bằng grep toàn `docs/`). Sau khi `/srs mentor-signals` sinh ra mã FR/NFR cụ thể, các tài liệu đó được sửa **một lần**: hai tài liệu chấm điểm thêm *"không nhận dữ kiện thầy"* vào phần Ngoài phạm vi, `daily-journal` thêm `mentor-signals` vào bảng ai được mượn khung chi tiết lệnh, và **`trade-replay` thêm lớp vạch tín hiệu thầy trên trục thời gian** (do OQ-4). Tổng **bốn** tài liệu. Sửa sớm hơn thì phải viết chung chung vì chưa có mã để trích, rồi sửa lại lần nữa. **Đây là việc bắt buộc của `/srs`, không phải tuỳ chọn** — chừng nào chưa làm, `UN-002` chưa có bên thi hành.
* [x] **OQ-10**: **Resolved 2026-08-29 — có nhận, thêm trạng thái "đã huỷ".** Thầy gửi tin huỷ/thoát thì tín hiệu gốc chuyển sang **đã huỷ**: rút khỏi dải bối cảnh, vẫn đọc được trong tab Thầy kèm giờ huỷ. Phần đối chiếu sau phiên nói rõ thầy huỷ **trước hay sau** lúc người chơi vào lệnh — đó mới là dữ kiện đáng học. Không nhận tin huỷ thì một setup chính thầy đã bỏ vẫn nằm trên màn hình thêm hai tiếng.
* [x] **OQ-11**: Đường kiểm chứng độc lập là thiết bị nào? — **Resolved 2026-08-29:** **điện thoại chạy cTrader mobile** — cùng tài khoản demo, khác thiết bị và khác đường mạng nên độc lập thật, và không đụng ràng buộc giữ Chrome focus. Giải một lần cho cả ba tài liệu cùng `ai-desk` OQ-8 và `order-execution` OQ-7. A-08 vì vậy đã được xác nhận.
* [x] **OQ-12**: **Resolved 2026-08-29.** (a) Đang giữ vị thế mở: dòng thầy **vẫn hiện khi chỉ quan sát**, và **tắt ngay khi vũ trang lệnh đóng** — cùng một luật cho mọi lần bấm cò, không có ngoại lệ nào cho hành động "an toàn". (b) Phiên đang khoá hoặc đã chạm hạn mức: dòng thầy **rút khỏi dải bối cảnh**, chỉ còn con số; nội dung vẫn đọc được trong tab Thầy nếu người chơi chủ động mở. Lý do: chìa một cơ hội ra đúng lúc vừa cấm hành động là cách nhanh nhất để biến hạn mức thành sự ấm ức.
* [x] **OQ-13**: **Resolved 2026-08-29 — hiện một dòng báo.** Tín hiệu thiếu trường bắt buộc (hướng, giá vào) không dùng được, nhưng vẫn hiện *"nhận được một tín hiệu không đọc được từ Thầy A"* kèm giờ. **Đây là thay đổi so với brainstorm Mục 7.1** ("không phải tín hiệu, bỏ"), người chơi chốt lại vì nguyên tắc `UN-008` mạnh hơn: bỏ câm là đường mất tín hiệu dễ xảy ra nhất (brainstorm R-3 xếp *Thỉnh thoảng*), và nó khiến "hệ thống hỏng" trông hệt như "thầy đang im".
* [x] **OQ-14**: **Resolved 2026-08-29 — 30 phút.** Đủ dài cho một lần canh setup M5, đủ ngắn để không tính nhầm cái liếc mắt từ đầu phiên.
* [x] **OQ-15**: **Resolved 2026-08-29 — giống nhau ở mọi con số.** Cùng thầy + cùng cặp + cùng hướng + giá vào, SL, TP, vùng chốt **đều y hệt** thì mới là trùng và được gộp. Lệch một con số là **bản cập nhật**. Chọn hướng chặt để không bao giờ nuốt mất việc thầy dời SL — đúng cái `UN-015` sinh ra để chặn.
