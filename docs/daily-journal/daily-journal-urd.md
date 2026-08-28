---
type: urd
feature: daily-journal
status: draft
updated: 2026-08-28
links: ["[[docs/_shared/project-profile.md]]", "[[docs/_shared/system-overview.md]]", "[[docs/_shared/definitions.md]]", "[[docs/_shared/operating-environment.md]]", "[[docs/order-execution/order-execution-urd.md]]", "[[docs/playbook-grading/playbook-grading-urd.md]]", "[[docs/ai-desk/ai-desk-urd.md]]", "[[docs/process-score/process-score-urd.md]]", "[[docs/trade-replay/trade-replay-urd.md]]", "[[docs/voice-journal/voice-journal-urd.md]]", "[[docs/tilt-meter/tilt-meter-urd.md]]"]
---

# daily-journal — User Requirements Document

## 1. Purpose

Ghi lại nhu cầu của người chơi ở **hai đầu của một buổi tối**: bước vào đã có chuẩn bị, và bước ra
với một bản ghi trung thực đủ để sáng hôm sau đọc lại hiểu được mình đã làm gì và vì sao.

Feature này là **đường chậm nhất** trong ba đường của hệ thống. Nó không đứng trên đường đặt lệnh,
không tính điểm, không khuyên gì. Giá trị của nó nằm ở chỗ khác: nó là nơi **duy nhất** giữ lại
những thứ không tự sinh ra từ sàn — luận điểm trước phiên, trạng thái người chơi lúc ngồi xuống,
và bối cảnh của một quyết định vốn chỉ tồn tại trong đầu vài phút rồi biến mất.

Vì vậy nhu cầu trung tâm ở đây không phải "xem lại thành tích" mà là **"chuẩn bị được, ghi lại được,
và tìm lại được — mà không có gì tôi viết ra sửa được sự thật từ sàn, cũng không có thao tác nào
trong nhật ký phát ra được một lệnh"**.

### User Problem & Current Experience

| User | Current Situation | Problem | User Consequence | Evidence |
|---|---|---|---|---|
| Người chơi | Ngồi xuống là mở biểu đồ và giao dịch ngay, không có nghi thức nào ở giữa | Không có khoảnh khắc nào để tự hỏi tối nay mình đang ở trạng thái nào và định làm gì | Đêm mệt và đêm tỉnh táo được đối xử y hệt nhau; không phân biệt được đêm nên đứng ngoài | Observed: `phase-12` (readiness checklist, daily analysis), `phase-06` (check-in 1–5) |
| Người chơi | Lý do vào lệnh chỉ nằm trong đầu lúc bấm, hôm sau đã mờ | Không tái dựng được bối cảnh của quyết định | Nhìn lại chỉ còn con số, không còn suy nghĩ — nên không rút ra được gì ngoài cảm giác tiếc | Observed: `README.md` (journal loop), `phase-12` (daily analysis, trade detail) |
| Người chơi | Công cụ nhật ký hiện có (Edgewonk, TradeZella) mở đầu bằng lãi lỗ | Tiền là thứ đập vào mắt trước tiên, ngay lúc định ngồi xuống soi quy trình | Buổi review bị kéo về kết quả trong ba giây đầu; quy trình thành phần phụ | Observed: `phase-12` ("Dollar P/L remains behind Outcome"), `docs/_shared/project-profile.md` (benchmark) |
| Người chơi | Bốn phiên thị trường ở bốn múi giờ, tự quy đổi trong đầu | Nhầm giờ, nặng nhất là quanh mốc đổi giờ mùa của London và New York | Ngồi vào bàn sai lúc, kỳ vọng thanh khoản sai — rồi đổ lỗi cho tape | Observed: `phase-12` (IANA zones, DST fixtures) |
| Người chơi | Tính cỡ lệnh nhẩm trong đầu hoặc bằng máy tính ngoài | Bước làm tròn khối lượng của sàn không nằm trong phép nhẩm | Rủi ro thật lệch khỏi rủi ro đã định, và chỉ phát hiện sau khi lệnh đã đóng | Observed: `phase-12` (position-size calculator dùng lại hàm quy đổi và làm tròn của `phase-02`) |
| Người chơi | Sau khi đóng phiên thì đóng luôn trình duyệt | Không có điểm về; buổi tối kết thúc bằng việc tắt máy | Vòng học khép lại nửa chừng — có dữ liệu nhưng không bao giờ được đọc | Assumption — xem A-04 Mục 8 |

## 2. User Types

| Tier | User Type | Context | Primary Goal | Pain Points |
|---|---|---|---|---|
| primary | **Người chơi** | Trước phiên: ngồi trước desktop, tay chưa cầm tay cầm, còn dùng bàn phím bình thường. Sau phiên: vẫn màn hình đó, phiên đã đóng, đầu còn nóng | Bước vào buổi tối đã biết mình định làm gì, và bước ra với một bản ghi mà sáng mai đọc lại vẫn hiểu | Không có nghi thức mở đầu; quên mất lý do; bị tiền kéo sự chú ý; không tìm lại được một nhóm lệnh cũ |

> **Không có secondary user.** Công cụ cá nhân một người dùng. **AI desk** là actor hệ thống và chỉ
> được **đọc số liệu tổng hợp** của nhật ký — nó không bao giờ viết, sửa hay xoá một dòng nhật ký nào
> (nguồn: `phase-12`, "read-only journal aggregates; no write tool"). Sàn cTrader/Spotware là nguồn
> sự thật cho dữ kiện khớp lệnh, cũng là actor hệ thống. Xem `docs/_shared/project-profile.md`.

## 3. Scope Boundaries

### In Scope

* Người chơi có **một điểm vào trước phiên và một điểm về sau khi đóng phiên** — cùng một màn hình "hôm nay", để buổi tối có mở đầu và có kết thúc thay vì bắt đầu giữa chừng rồi tắt máy.
* Người chơi thấy **bốn đồng hồ phiên thị trường** (Sydney, Tokyo, London, New York) chạy theo giờ thật của từng nơi, **đúng cả trong tuần đổi giờ mùa** — không phải cộng trừ trong đầu.
* Người chơi tự soát **năm mục sẵn sàng** (ngủ/năng lượng, bình tĩnh, tập trung, chấp nhận hạn mức tối nay, đã xem kế hoạch và tin) — mỗi mục có/không kèm ghi chú tuỳ ý. **Kết quả chỉ để tự biết, không bao giờ chặn mở khoá hay chặn một lệnh.**
* Người chơi **tự chấm 1–5** ở đầu phiên và cuối phiên bằng tay cầm, bỏ qua được, và bỏ qua không bị coi là điểm kém.
* Người chơi **viết ra kế hoạch của tối nay**: luận điểm, cặp theo dõi, vùng giá quan trọng, điều gì làm luận điểm sai, sự kiện rủi ro, nhãn phân loại và ghi chú. Nội dung này **do người chơi viết** — hệ thống được phép gợi ý ở nơi khác, nhưng **không bao giờ tự sửa hay tự đè lên chữ của người chơi**.
* Kế hoạch của tối nay được **chụp lại tại thời điểm lệnh đầu tiên** và bản chụp đó không sửa được nữa. Sau lệnh đầu tiên người chơi vẫn viết thêm được, nhưng phần viết thêm hiện ra **là** viết thêm — để mai đọc lại phân biệt được điều mình đã tin **trước** khi vào lệnh với điều mình nghĩ **sau** khi đã biết kết quả.
* Người chơi **mở được kế hoạch phiên mà AI desk đã lưu, ngay cạnh kế hoạch mình tự viết** — hai bên nằm riêng và luôn phân biệt được ai viết gì.
* Người chơi **đính ảnh biểu đồ đã tự chụp sẵn** vào kế hoạch của ngày hoặc vào một lệnh cụ thể.
* Người chơi **tính được cỡ lệnh** từ vốn, mức rủi ro (bằng tiền hoặc phần trăm), cặp, giá vào và giá dừng lỗ — và thấy cả **số yêu cầu lẫn số đã làm tròn theo bước của sàn**, kèm rủi ro thật bằng tiền và hạn mức đang áp. **Áp giá trị chỉ dàn sẵn bản xem trước trên màn chính; vẫn phải `LT+RT` mới có lệnh.** *(Chốt 2026-08-28: máy tính cỡ lệnh thuộc feature này; `order-execution` giữ phần chọn khối lượng thật và mọi ràng buộc hạn mức.)*
* Người chơi **mở lại một ngày** và thấy đủ: mấy phiên, mấy lệnh, mức sẵn sàng, điểm quy trình đã chốt, tự chấm, kế hoạch đã viết, các lỗi đã gắn, và các lệnh của ngày đó.
* **Một "ngày" trong nhật ký là một buổi tối giao dịch, không phải một ngày lịch máy móc.** Phiên bắt đầu tối hôm trước và đóng sau nửa đêm vẫn thuộc **buổi tối đã bắt đầu nó** — đóng phiên lúc 2 giờ sáng rồi mở "hôm nay" vẫn thấy đúng buổi tối vừa xong, không phải một ngày trống. Ngày tính theo giờ địa phương của người chơi. *(Xem OQ-6.)*
* Người chơi nhìn **một tháng trong một hình** — bản đồ nhiệt **mỗi ô là một buổi tối**, **mặc định tô theo quy trình**, không tô theo tiền. Ngày có nhiều phiên thì ô gộp lại; mở ngày ra mới tách từng phiên. *(Chốt 2026-08-28 — giữ hình lịch quen thuộc để đọc cả tháng trong một cái liếc.)*
* Người chơi mở nhật ký mà **không bị con số tiền đập vào mắt trước**: lãi lỗ bằng tiền chỉ hiện sau một lần bấm có chủ ý.
* Người chơi thấy **mười lệnh gần nhất** và **tìm lại một nhóm lệnh cũ** bằng bộ lọc nhiều chiều: kỳ (tuần, tháng, hoặc khoảng tự chọn), playbook, cặp, khung thời gian, mua/bán, phiên thị trường, phân loại kế hoạch, loại lỗi, thắng/thua/hoà. Bốn chiều **kỳ, cặp, phiên thị trường, kết quả** là thứ dùng gần như mỗi tuần; các chiều còn lại dùng thưa hơn — chênh lệch này để `/srs` quyết thứ tự làm, không phải để cắt bớt nhu cầu.
* Người chơi **mở một lệnh và thấy đủ bối cảnh ở một chỗ**: kế hoạch bất biến lúc vào, dữ kiện khớp và đóng từ sàn, các lần sửa SL/TP, kết quả chấm luật, memo, ảnh đính, lỗi đã gắn, và đường dẫn sang bản tua lại.
* Người chơi **viết ra triết lý giao dịch và các nguyên tắc cốt lõi của chính mình**, đọc lại và sửa được. *(Chốt 2026-08-28 — xem D-01 Mục 8.)*
* Người chơi biết chắc **những gì mình viết không bao giờ sửa được sự thật từ sàn** — giá khớp, thời điểm, lãi lỗ do sàn tính vẫn nguyên vẹn dù nhật ký ghi gì.
* Người chơi biết chắc **không thao tác nhật ký nào phát ra được một lệnh**, và nhật ký không bao giờ làm chậm đường đặt lệnh.
* Ngoài phiên người chơi **dùng bàn phím và chuột bình thường**; những thao tác nhật ký cần làm **trong phiên** thì phải làm được bằng tay cầm và phải ngắn. *(Chốt 2026-08-28.)*

### Out of Scope

* **Học từ chất lượng thực thi** — đối chiếu kế hoạch với thứ đã thực sự làm, phân nhóm lệnh có-kế-hoạch / bốc-đồng, điểm trước-trong-sau một lệnh, thư viện các loại lỗi và xu hướng lỗi thuộc feature **`execution-learning`** *(tách khỏi feature này 2026-08-28 theo quyết định của người chơi; chưa có URD)*. Nhật ký **hiển thị** lỗi đã được gắn và **lọc** theo nó, nhưng không định nghĩa, không tự suy ra, không chấm.
* **Tính điểm quy trình** (năm trục, radar) thuộc feature `process-score`. Nhật ký chỉ **đọc điểm đã chốt** và dùng nó để tô bản đồ nhiệt.
* **Các chỉ số so sánh nhiều phiên với nhau** — độ ổn định quy trình, hệ số lợi nhuận, tỉ lệ thắng, sụt giảm tối đa, R trung bình, tháng này so tháng trước thuộc feature `process-score`. *(Chốt 2026-08-28: ba nguồn `phase-06`, `phase-11`, `phase-12` đặt chúng ở ba chỗ khác nhau; chọn nguyên tắc **một nơi tính, một nơi đọc** — nhật ký duyệt bản ghi từng ngày và từng lệnh, mọi con số tổng hợp qua nhiều phiên thuộc deck điểm quy trình.)*
* **Hạn mức rủi ro, khoá và mở khoá phiên** thuộc feature `order-execution`. Nhật ký chỉ nhận việc **người chơi xác nhận đã chấp nhận hạn mức tối nay** như một mục trong danh sách sẵn sàng.
* **Bộ đếm số lần tự huỷ trên màn chính** thuộc `order-execution`. **Nơi cộng dồn con số đó qua nhiều phiên** thuộc `process-score` (cùng quyết định 2026-08-28 ở trên).
* **Ghi âm lý do vào lệnh và chuyển lời nói thành văn bản** thuộc feature `voice-journal`. Nhật ký chỉ **hiển thị** memo đã có.
* **Tua lại lệnh qua tape** thuộc feature `trade-replay`. Nhật ký chỉ giữ **đường dẫn sang đó**.
* **Chấm luật playbook và soạn playbook** thuộc feature `playbook-grading`.
* **Đo trạng thái tâm lý và ma sát thích ứng** thuộc feature `tilt-meter`.
* **Tư vấn, tín hiệu, phân tích, kế hoạch do AI soạn** thuộc feature `ai-desk`. Nhật ký được **liên kết tới** kế hoạch phiên mà AI desk đã lưu, nhưng chữ của AI và chữ của người chơi không bao giờ trộn vào nhau.
* **Báo cáo in được, xuất CSV/JSON, sao lưu, khôi phục, xoá toàn bộ, màn cài đặt** thuộc feature `reports-export`.
* Nhiều tài khoản, nhập lịch sử từ MT5 hay sàn khác, bản dùng trên điện thoại, giao diện sáng.
* Lấy ảnh biểu đồ tự động từ TradingView hay bất kỳ nguồn giá không chính thức nào.

## 4. User Needs

| ID | User | Context / Trigger | User Need | Expected Outcome | Importance | Evidence |
|---|---|---|---|---|---|---|
| UN-001 | Người chơi | Ngồi xuống trước khi mở khoá phiên | Có một nghi thức ngắn buộc mình dừng lại và tự trả lời tối nay đang ở trạng thái nào | Có một bản ghi chuẩn bị gắn với buổi tối này, làm xong trong vài phút, không phải một biểu mẫu dài | High | Observed: `phase-12` (five-item readiness checklist) |
| UN-002 | Người chơi | Đã soát xong hoặc cố tình bỏ trống danh sách sẵn sàng | Mức sẵn sàng thấp **không bao giờ** khoá mình lại — mình vẫn là người quyết định | Bỏ trống hết vẫn mở khoá phiên và vào lệnh được; không có cảnh báo nào biến thành rào chặn | Critical | Observed: `phase-12` ("Readiness is advisory and never blocks unlock or trading") |
| UN-003 | Người chơi | Bất kỳ lúc nào trong lúc chuẩn bị | Biết ngay đang ở phiên thị trường nào và còn bao lâu, không phải quy đổi múi giờ trong đầu | Bốn đồng hồ đọc đúng giờ địa phương thật, kể cả tuần đổi giờ mùa; mỗi thành phố đổi theo lịch của chính nó, và chỉ Tokyo là không bao giờ đổi | High | Observed: `phase-12` (IANA zones, DST) |
| UN-004 | Người chơi | Trước khi vào lệnh đầu tiên | Viết ra tối nay mình tin điều gì, nhìn cặp nào, vùng giá nào quan trọng, và điều gì chứng minh mình sai | Tối nay có một thứ để đối chiếu thay vì trí nhớ; mai đọc lại vẫn hiểu | Critical | Observed: `phase-12` (durable daily analysis entry) |
| UN-005 | Người chơi | Đang viết kế hoạch, cần minh hoạ | Đính được ảnh biểu đồ mình đã chụp vào kế hoạch hoặc vào một lệnh | Ảnh nằm cạnh chữ, mở lại vẫn còn, không phải lục thư mục ảnh trong máy | Medium | Observed: `phase-12` (attach local PNG/JPEG/WebP) |
| UN-006 | Người chơi | Đã có ý tưởng vào lệnh, cần biết vào bao nhiêu | Biết cỡ lệnh đúng với mức rủi ro mình định, **sau khi** sàn làm tròn, chứ không phải trước | Thấy cả số yêu cầu và số sàn nhận, rủi ro thật bằng tiền, hạn mức đang áp, và **số vốn dùng để tính lấy từ đâu, vào lúc nào** | High | Observed: `phase-12` (position-size calculator + phase 2 conversion) |
| UN-007 | Người chơi | Vừa tính xong cỡ lệnh | Áp con số đó vào màn chính mà **không sợ thao tác này tự gửi lệnh đi** | Áp xong chỉ có bản xem trước thay đổi; vẫn cần `LT+RT` | Critical | Observed: `phase-12` ("Applying the value only changes the HUD preview; LT+RT is still required") |
| UN-008 | Người chơi | Đầu phiên và cuối phiên | Tự chấm trạng thái mình bằng một thang ngắn, bằng tay cầm, bỏ qua được | Hai lần bấm là xong; bỏ qua không bị hiểu là điểm kém | Medium | Observed: `phase-06` (`checkin_pre`, `checkin_post` 1–5, skippable) |
| UN-009 | Người chơi | Vừa đóng phiên, đầu còn nóng | Có một chỗ để về đọc lại buổi tối vừa xong thay vì tắt máy | Sau khi đóng phiên, màn hình "hôm nay" là nơi đáp xuống, đã có sẵn dữ liệu của buổi tối | High | Observed: `phase-12` ("landing page after close") |
| UN-010 | Người chơi | Mở nhật ký bất kỳ lúc nào | Không bị con số tiền chiếm lấy sự chú ý ngay giây đầu tiên | Màn mặc định nói về quy trình; tiền nằm sau một lần bấm có chủ ý | Critical | Observed: `phase-12` ("Dollar P/L remains behind Outcome"), `phase-06` (outcome tab sau một click) |
| UN-011 | Người chơi | Cuối tuần hoặc cuối tháng, muốn biết mình có khá lên không | Nhìn một khoảng thời gian trong một hình và nhận ra đêm nào giữ được quy trình | Bản đồ nhiệt đọc được trong vài giây, tô theo quy trình; ngày trống không bị đọc nhầm thành đêm tệ | High | Observed: `phase-12` (process-first day heatmap) |
| UN-012 | Người chơi | Có một câu hỏi cụ thể ("mấy lệnh vàng phiên London theo playbook này ra sao") | Lọc lại lịch sử theo nhiều chiều cùng lúc | Ra đúng nhóm lệnh cần, không lẫn lệnh ngoài điều kiện đã chọn | High | Observed: `phase-12` (`/journal/history` filters) |
| UN-013 | Người chơi | Nhớ mang máng một lệnh cũ | Mở nó ra và thấy đủ bối cảnh ở một chỗ, không phải nhảy qua bốn màn | Một màn có kế hoạch lúc vào, dữ kiện từ sàn, các lần sửa bảo vệ, điểm luật, memo, ảnh, lỗi, link tua lại | High | Observed: `phase-12` (`/journal/trade/:cid`) |
| UN-014 | Người chơi | Bất kỳ lúc nào đọc lại nhật ký | Chắc chắn chữ mình viết không sửa được dữ kiện từ sàn | Nhận xét thêm vào được, nhưng giá khớp, thời điểm và lãi lỗ do sàn tính không bao giờ đổi theo | Critical | Observed: `phase-12` ("A review can annotate a trade; it cannot rewrite fills...") |
| UN-015 | Người chơi | Đang có vị thế, mở nhật ký giữa phiên | Biết chắc mở nhật ký không phát ra lệnh và không làm chậm đường đặt lệnh | Nhật ký chạy trên đường riêng, chậm nhất, tách khỏi đường đặt lệnh; mở nó thì ARM bị huỷ và không mở được lệnh mới | Critical | Observed: `docs/_shared/system-overview.md` (journal path), `docs/_shared/operating-environment.md` (ràng buộc 4) |
| UN-017 | Người chơi | Đang đọc lại một buổi tối đã qua | Phân biệt được điều mình tin **trước** khi vào lệnh với điều mình viết **sau** khi đã biết kết quả | Bản kế hoạch chốt tại lệnh đầu tiên còn nguyên; phần viết thêm sau đó nằm riêng và ghi rõ thời điểm | Critical | Observed: `docs/_shared/definitions.md` (Plan snapshot), `phase-11` ("plan acknowledged before first fire") |
| UN-018 | Người chơi | Vừa mở nhật ký, chưa có câu hỏi cụ thể nào | Thấy ngay mấy lệnh gần nhất mà không phải đặt bộ lọc | Mười lệnh gần nhất hiện sẵn, mỗi lệnh đủ để nhận ra nó và mở thẳng vào chi tiết | Medium | Observed: `phase-12` (latest ten trades) |
| UN-019 | Người chơi | Đang viết kế hoạch tối nay, AI desk đã lưu một kế hoạch phiên | Đọc kế hoạch AI đề xuất cạnh kế hoạch mình tự viết mà không lẫn chữ của ai vào chữ của ai | Hai bản nằm riêng, luôn phân biệt được nguồn; chữ người chơi không bị AI sửa | Medium | Observed: `phase-12` ("Link the stored phase 4 session plan") |
| UN-016 | Người chơi | Lúc bình tĩnh, ngoài phiên | Viết ra mình chơi theo triết lý gì và những nguyên tắc nào không được phá | Có một chỗ cố định để đọc lại trước những đêm khó, sửa được khi suy nghĩ thay đổi | Medium | Confirmed (người chơi chốt 2026-08-28) · Observed: `phase-12` (`/system` philosophy and core principles) |

## 5. Prioritized User Journeys

### Journey 1: Mở đầu một buổi tối

* __User:__ Người chơi
* __Importance:__ Critical
* __Trigger:__ Ngồi xuống trước màn hình, chưa mở khoá phiên
* __Expected outcome:__ Buổi tối bắt đầu bằng một lần dừng lại có ý thức, và có một bản ghi chuẩn bị gắn với ngày hôm nay
* __Related needs:__ UN-001, UN-002, UN-003, UN-004, UN-005, UN-008, UN-017, UN-019

1) Mở màn hình "hôm nay" của nhật ký; bốn đồng hồ phiên thị trường đang chạy.
2) Soát năm mục sẵn sàng, ghi chú ngắn ở mục nào thấy cần.
3) Tự chấm trạng thái đầu phiên.
4) Viết luận điểm tối nay: cặp theo dõi, vùng giá quan trọng, điều gì làm luận điểm sai, sự kiện rủi ro. Đính ảnh biểu đồ đã chụp sẵn nếu muốn; mở kế hoạch AI desk đã lưu để đọc cạnh bản của mình.
5) Sang màn chính và mở khoá phiên.

__Independent verification:__ Sau khi phiên đóng, mở lại đúng ngày đó thấy nguyên bản chuẩn bị đã
viết — và đối chiếu được: mở khoá phiên **thành công** ngay cả khi cả năm mục sẵn sàng đều bỏ trống.

### Journey 2: Tính cỡ lệnh rồi vẫn phải xác nhận bằng hai tay

* __User:__ Người chơi
* __Importance:__ Critical
* __Trigger:__ Đã thấy một setup, cần biết vào bao nhiêu cho đúng rủi ro đã định
* __Expected outcome:__ Con số đúng được dàn sẵn, và không có gì rời khỏi máy cho tới lần xác nhận cuối
* __Related needs:__ UN-006, UN-007, UN-015

1) Nhập vốn, mức rủi ro, cặp, giá vào, giá dừng lỗ.
2) Đọc số yêu cầu, số sàn nhận sau khi làm tròn, rủi ro thật bằng tiền, và hạn mức đang áp.
3) Áp giá trị sang màn chính.
4) Quay lại tay cầm, vũ trang, rồi bắn bằng `LT+RT`.

__Independent verification:__ Giữa bước 3 và bước 4, kiểm tra bên sàn không thấy bất kỳ lệnh hay
thay đổi nào — chỉ có bản xem trước trên màn chính đổi. Rủi ro thật của lệnh đã khớp trùng với con số
hiển thị ở bước 2, trong phạm vi bước làm tròn của sàn.

### Journey 3: Đóng phiên và đọc lại buổi tối

* __User:__ Người chơi
* __Importance:__ High
* __Trigger:__ Vừa đóng phiên, đầu còn nóng
* __Expected outcome:__ Buổi tối khép lại bằng một lần đọc, không phải bằng việc tắt máy
* __Related needs:__ UN-008, UN-009, UN-010, UN-014

1) Đóng phiên; màn hình đáp xuống là "hôm nay" của nhật ký.
2) Tự chấm trạng thái cuối phiên.
3) Đọc lại buổi tối: mấy lệnh, mức sẵn sàng đã ghi lúc đầu, điểm quy trình đã chốt, kế hoạch đã viết.
4) Muốn xem tiền thì bấm thêm một lần có chủ ý.

__Independent verification:__ Đóng phiên rồi không thao tác gì thêm — màn hình phải tự đáp xuống
"hôm nay" với dữ liệu buổi tối vừa xong đã có sẵn, không phải tự tìm đường vào. Và từ bước 1 tới
bước 3, không có con số lãi lỗ bằng tiền nào xuất hiện cho tới khi người chơi tự bấm sang phần kết quả.

### Journey 4: Nhìn lại một tháng

* __User:__ Người chơi
* __Importance:__ High
* __Trigger:__ Cuối tuần hoặc cuối tháng, muốn biết mình có khá lên không
* __Expected outcome:__ Nhận ra dạng hình của tháng — đêm nào giữ được quy trình, đêm nào không — rồi mở đúng đêm đáng xem
* __Related needs:__ UN-011, UN-010

1) Mở nhật ký, chọn kỳ theo tháng.
2) Đọc bản đồ nhiệt tô theo quy trình.
3) Chọn một ngày đáng chú ý.
4) Ngày đó mở ra: số phiên, số lệnh, mức sẵn sàng, điểm quy trình, tự chấm, kế hoạch, lỗi đã gắn, các lệnh.

__Independent verification:__ Chọn một ngày bất kỳ trên bản đồ nhiệt và mở nó, nội dung hiện ra
thuộc đúng ngày đã chọn; một ngày **không giao dịch** vẫn mở được và đọc ra là không giao dịch,
không phải một đêm điểm thấp.

### Journey 5: Truy một câu hỏi qua lịch sử

* __User:__ Người chơi
* __Importance:__ High
* __Trigger:__ Nghi ngờ một cách chơi cụ thể chỉ hiệu quả ở một phiên thị trường nhất định
* __Expected outcome:__ Có đúng nhóm lệnh cần nhìn, không phải cuộn qua tất cả
* __Related needs:__ UN-012, UN-013

1) Mở lịch sử.
2) Đặt các điều kiện cùng lúc: kỳ, playbook, cặp, phiên thị trường, kết quả.
3) Đọc danh sách trả về.
4) Mở một lệnh trong đó để xem chi tiết.

__Independent verification:__ Mọi lệnh trong kết quả đều thoả **tất cả** điều kiện đã đặt; đổi một
điều kiện thì danh sách đổi theo đúng hướng dự đoán.

### Journey 6: Mở lại một lệnh cũ để hiểu vì sao

* __User:__ Người chơi
* __Importance:__ High
* __Trigger:__ Một lệnh cũ vẫn còn gợn trong đầu
* __Expected outcome:__ Dựng lại được bối cảnh của quyết định, không phải đoán
* __Related needs:__ UN-013, UN-005, UN-014, UN-017, UN-018

1) Mở lệnh đó từ danh sách gần nhất hoặc từ lịch sử.
2) Đọc kế hoạch lúc vào và dữ kiện từ sàn cạnh nhau.
3) Xem các lần sửa mức bảo vệ, kết quả chấm luật, memo, ảnh đính.
4) Sang bản tua lại nếu muốn nhìn tape.

__Independent verification:__ Không rời màn này vẫn trả lời được: lúc đó định làm gì, đã làm gì,
và sàn ghi nhận gì. Nếu lệnh không có tape, màn vẫn mở được và nói rõ phần tua lại không có.

### Journey 7: Ghi lại triết lý và nguyên tắc

* __User:__ Người chơi
* __Importance:__ Medium
* __Trigger:__ Một buổi bình tĩnh ngoài phiên, sau khi nhận ra một bài học lặp lại
* __Expected outcome:__ Điều vừa nhận ra được viết xuống ở chỗ cố định, đọc lại được trước những đêm khó
* __Related needs:__ UN-016

1) Mở phần triết lý và nguyên tắc.
2) Viết hoặc sửa một nguyên tắc.
3) Lưu lại.

__Independent verification:__ Viết một nguyên tắc, chạy trọn một phiên có AI desk hoạt động và có
ghi memo, rồi mở lại — chữ phải nguyên văn từng ký tự. Kiểm chiều ngược: yêu cầu AI desk sửa một
nguyên tắc, nó phải không làm được.

## 6. User Exceptions & Edge Conditions

| Situation | User Impact | Expected User-facing Outcome | Related Journey / Need |
|---|---|---|---|
| Một tối người chơi **chủ động đứng ngoài** | Dễ bị đọc nhầm thành "đêm tệ", đúng thứ sản phẩm này tồn tại để chống lại | Đọc ra là một **quyết định** — trạng thái hợp lệ, không phải điểm 0, không phải thiếu dữ liệu; phân biệt được với ngày thị trường đóng | J4 · UN-011 · OQ-1 |
| Ngày **thị trường đóng** (cuối tuần, ngày lễ) | Gộp chung với đêm chủ động đứng ngoài thì làm mờ đúng thứ đáng được ghi nhận | Hiện là thị trường đóng, không phải một lựa chọn của người chơi, và không nằm trong mẫu số của bất kỳ tỉ lệ nào | J4 · UN-011 · OQ-1 |
| Bỏ trống toàn bộ mục sẵn sàng và tự chấm | Sợ bị công cụ phạt vì lười khai | Vào phiên bình thường; những chỗ cần dữ liệu đó ghi rõ **không có dữ liệu**, không quy về 0 | J1 · UN-002 |
| Chưa đủ số phiên để nói được điều gì có nghĩa | Đọc một con số ngẫu nhiên rồi tin nó | Nói thẳng **chưa đủ dữ liệu** kèm số phiên hiện có, thay vì in một con số tự tin | J4 · UN-011 |
| Buổi tối còn lệnh mở lúc đóng phiên | Tưởng phải chờ mới có điểm, hoặc tưởng con số đang thấy là tạm | Buổi đã đóng phiên **luôn** có điểm quy trình ngay; chỉ phần kết quả bằng tiền còn cập nhật sau. **Không** có trạng thái "đang chờ chốt" và không có số tạm (chốt 2026-08-28 tại `process-score` OQ-1) | J3 · UN-009 |
| Một lệnh không có bản tua lại (tape thiếu) | Bấm vào rồi gặp màn hỏng | Chi tiết lệnh vẫn mở đủ mọi phần khác, phần tua lại nói rõ không có | J6 · UN-013 |
| Ảnh đính quá lớn hoặc sai định dạng | Đính xong tưởng đã lưu, hôm sau mất | Báo ngay giới hạn cụ thể và từ chối rõ ràng — không âm thầm bỏ qua | UN-005 |
| Ảnh tích tụ làm đầy chỗ lưu | Một ngày nào đó không lưu được nữa mà không hiểu vì sao | Cho biết đang dùng bao nhiêu chỗ **trước khi** hết, không phải lúc đã hỏng | UN-005 |
| Mất kết nối hoặc đóng nhầm tab khi đang viết kế hoạch | Mất đoạn vừa gõ, mất luôn hứng viết | Chữ đã gõ không mất; quay lại viết tiếp từ chỗ dừng | J1 · UN-004 |
| Đêm rơi đúng mốc đổi giờ mùa | Ngồi vào bàn lệch một tiếng | Mỗi thành phố đổi theo lịch của **chính nó** — London, New York và Sydney đều có mốc đổi riêng và không cùng ngày; chỉ Tokyo là không bao giờ đổi. Trong cửa sổ 2–3 tuần mà châu Âu đã đổi còn Mỹ thì chưa, khoảng cách London–New York khác thường lệ và bốn đồng hồ vẫn phải đọc đúng | J1 · UN-003 |
| Sự kiện từ sàn về muộn sau khi đã đóng phiên | Bản ghi của ngày sai vĩnh viễn | Ngày tự cập nhật khi dữ kiện về; người chơi không phải sửa tay và không được phép sửa dữ kiện đó | UN-014 |
| Mở nhật ký giữa phiên khi đang có vị thế | Tưởng đang vũ trang, hoá ra đã bị huỷ; hoặc tệ hơn, tưởng mình bị kẹt không thoát được | Mở nhật ký huỷ ARM và khoá **mở lệnh mới**, nói rõ ngay lúc mở. **Đóng vị thế và thoát khẩn cấp vẫn luôn được phép** (`order-execution` UN-010). Đóng nhật ký lại thì mọi thứ trở về bình thường, không có gì bị khoá kéo dài | J6 · UN-015 |
| Ngày cũ có trước khi một tính năng tồn tại (chưa có playbook, chưa có memo) | Thấy ô trống rồi tưởng mình đã bỏ bê | Cột đó ghi **không có dữ liệu**, không suy đoán ngược và không tính như một thiếu sót của người chơi | J4 · J5 |
| Một buổi tối có hai phiên trở lên | Ô nhiệt phải tô bằng một con số, trong khi điểm quy trình chấm theo phiên | Ô nói rõ buổi đó có mấy phiên và chỉ hiển thị con số **do `process-score` cung cấp cho cả buổi**; nhật ký không tự gộp điểm nhiều phiên. Chưa có con số cấp buổi thì ô hiện từng phiên thay vì bịa một điểm trung bình | J4 · UN-011 · OQ-7 |
| Phiên bắt đầu tối hôm trước, đóng sau nửa đêm | Buổi tối bị cắt làm đôi; mở "hôm nay" ra thấy trống trong khi vừa giao dịch xong | Cả phiên thuộc buổi tối đã bắt đầu nó; "hôm nay" sau khi đóng phiên luôn là buổi tối vừa xong | J3 · J4 · UN-009 |
| Sửa kế hoạch sau khi đã biết kết quả | Sáng mai đọc lại tin nhầm là mình đã nghĩ thế từ đầu | Bản chụp trước lệnh đầu tiên không đổi; phần viết thêm hiển thị tách bạch kèm thời điểm | J1 · J6 · UN-017 |
| Giá dừng lỗ trùng hoặc sai phía so với giá vào | Con số cỡ lệnh vô nghĩa nhưng trông vẫn như một con số | Không hiện cỡ lệnh; nói rõ vì sao và không cho áp sang màn chính | J2 · UN-006 |
| Không quy đổi được sang tiền tài khoản (mất kết nối, thị trường đóng, cặp không định giá bằng USD) | Nhận một con số rủi ro sai mà tin là đúng | Nói thẳng **chưa tính được** kèm lý do — không bao giờ hiện một con số ước lượng | J2 · UN-006 |
| Số vốn đang dùng để tính đã cũ so với tài khoản thật | Rủi ro thật lệch khỏi rủi ro đã định, đúng thứ máy tính này sinh ra để chống | Hiện rõ số vốn đang dùng và lấy lúc nào; lệch nhiều thì nói ra trước khi cho áp | J2 · UN-006 |
| Áp cỡ lệnh xong nhưng chưa bắn, giá đã chạy xa | Bắn một con số tính cho mức giá cũ | Bản xem trước nói rõ nó tính ở mức giá nào, lúc nào; giá chạy quá xa thì nói ra trước khi người chơi bắn | J2 · UN-006, UN-007 |
| Mở nhật ký ở hai tab và sửa cùng một buổi tối | Bản viết sau đè mất bản viết trước mà không ai báo | Không âm thầm mất chữ — bản đang mở biết là đã cũ và nói ra trước khi ghi đè | J1 · UN-004 |
| Người chơi muốn sửa một dữ kiện từ sàn (giá, thời điểm, lãi lỗ) | Kỳ vọng sai về quyền của mình trên bản ghi | Không sửa được, và nói rõ vì sao: nhận xét thêm vào được, dữ kiện thì không | UN-014 |

## 7. User-side Constraints

* **Chrome desktop, giao diện tối, một tài khoản demo duy nhất.** Không có bản dùng trên điện thoại và không có giao diện sáng; nhật ký hiển thị tài khoản đang xem như một **nhãn chỉ đọc**, không phải một bộ chọn.
* **Ngoài phiên: bàn phím và chuột dùng bình thường.** Viết kế hoạch, ghi chú, đính ảnh, lọc lịch sử đều là việc làm khi không đang giao dịch, nên không phải nhét vào tay cầm. *(Chốt 2026-08-28.)*
* **Trong phiên: chỉ tay cầm.** Hiện chưa có thao tác nhật ký nào bắt buộc phải làm giữa phiên — tự chấm diễn ra trước khi mở khoá và sau khi đóng phiên. Nếu về sau có thao tác giữa phiên thì nó phải làm được bằng tay cầm và phải ngắn (xem OQ-2).
* **Nhật ký là nguồn bằng chứng cho `process-score`, không chỉ là nơi đọc điểm.** Mục sẵn sàng, tự chấm đầu và cuối buổi, và việc xác nhận kế hoạch trước lệnh đầu tiên đều do feature này thu và giữ; `process-score` đọc chúng và không được mở một luồng thu thứ hai.
* **Mở nhật ký từ menu an toàn giữa phiên sẽ huỷ ARM và khoá mở lệnh mới** (`docs/_shared/operating-environment.md`, ràng buộc 4). Người chơi phải lường trước điều này mỗi lần mở.
* **Ảnh biểu đồ phải tự chụp và lưu sẵn trong máy.** Không có đường nào lấy ảnh tự động từ TradingView hay nguồn giá không chính thức.
* **Một người dùng.** Không chia sẻ, không nhiều tài khoản, không nhập lịch sử từ sàn khác.
* **Nhật ký không bao giờ tự xoá thứ gì.** Chữ, ảnh và bản ghi giữ vô hạn; đổi lại, người chơi phải được cảnh báo dung lượng **trước khi** hết chỗ. Xoá **toàn bộ** là hành động chủ động của người chơi và thuộc `reports-export`; gỡ **một** ảnh hoặc một ghi chú vừa đính thì làm ngay tại chỗ đính — xem OQ-10. *(Chốt 2026-08-28.)*
* **Nội dung nhật ký là dữ liệu cá nhân** — chữ viết, ảnh, và memo giọng nói. Người chơi cần biết nó nằm ở đâu và xoá bằng cách nào; phần xoá và sao lưu thuộc `reports-export` (`docs/_shared/project-profile.md`, mục Compliance).
* **Giao diện tiếng Anh**, tài liệu nghiệp vụ tiếng Việt.

## 8. Assumptions & Validation

> **Quyết định đã chốt 2026-08-28** — không còn là giả định chờ kiểm chứng:
>
> * **D-01:** Triết lý và nguyên tắc cốt lõi thuộc feature này (`phase-12` sở hữu, `phase-13` chỉ trỏ tới). Câu tương ứng trong `trade-replay-urd.md` đã sửa cho khớp.
> * **D-02:** Nhật ký chỉ **đọc** điểm quy trình và mọi con số tổng hợp đã tính sẵn, **không tự tính con số nào — kể cả việc gộp điểm nhiều phiên trong một buổi tối**. Cần một con số cấp buổi thì `process-score` phải cung cấp sẵn. Chiều ngược lại thì có: nhật ký **cung cấp bằng chứng** chuẩn bị và nhìn lại cho điểm quy trình (Mục 7).

| ID | Assumption | Impact if Wrong | Validation Status | Next Action |
|---|---|---|---|---|
| A-03 | Một ngày không giao dịch là **dữ liệu hợp lệ**, không phải dữ liệu thiếu | Bản đồ nhiệt và mọi số trung bình sẽ hiểu sai những đêm đứng ngoài — phá đúng nguyên tắc lớn nhất của sản phẩm | Suy từ `phase-11` ("a correctly-declined evening scores at least as well as a well-traded one") | Kiểm khi thiết kế bản đồ nhiệt, xem OQ-1 |
| A-04 | Người chơi review ngay trong buổi tối đó, không phải vài ngày sau | Nếu review muộn thì "hôm nay" không còn là điểm về, và toàn bộ mô hình màn hình chính phải xoay trục quanh việc chọn ngày cũ | Chưa xác nhận với người chơi | **Hỏi TRƯỚC khi `/srs` khoá luồng màn hình** — đây là quyết định tổ chức thông tin, để trôi sang giai đoạn spec là muộn |
| A-05 | Khoảng 20 phiên mỗi tháng — lượng dữ liệu một năm vẫn nhỏ | Nếu nhiều hơn nhiều lần, việc lọc và xem lại cần cách tổ chức khác | Suy từ `phase-06` ("~20 sessions/month") | Xem lại sau ba tháng dùng thật |
| A-06 | Người chơi muốn đọc lại kế hoạch của ngày cạnh từng lệnh, chứ không chỉ ở cấp ngày | Nếu sai, phần liên kết lệnh với luận điểm là công thừa | Chưa xác nhận | Hỏi cùng OQ-3 |

## 9. User Success Criteria

| ID | User Outcome | Baseline | Target | Measurement | Review Period |
|---|---|---|---|---|---|
| USC-001 | Buổi tối bắt đầu có chuẩn bị thay vì bắt đầu giữa chừng | Chưa có — xác lập từ 10 buổi tối đầu | ≥ 80% số phiên trong tháng có ít nhất một phần chuẩn bị được ghi (mục sẵn sàng hoặc kế hoạch của ngày) | Đếm số phiên có bản ghi chuẩn bị gắn với nó, trên tổng số phiên | Hằng tháng |
| USC-002 | Một quyết định cũ dựng lại được, không phải đoán | Chưa có — xác lập từ 10 buổi tối đầu | ≥ 90% số lệnh trong tháng mở ra thấy đủ kế hoạch lúc vào, dữ kiện từ sàn và ít nhất một dấu vết lý do (memo, ghi chú, hoặc kết quả chấm luật) | Đếm số lệnh đủ ba phần trên tổng số lệnh của tháng. Nguồn dấu vết nào đang bị tắt hoặc chưa tồn tại thì loại khỏi mẫu số và ghi rõ đang đo trên mấy nguồn — không tính là thiếu sót của người chơi (cùng nguyên tắc `process-score` UN-015) | Hằng tháng |
| USC-003 | Quy trình đứng trước tiền ở mọi lối vào nhật ký | Chưa có | 100% màn mặc định không hiển thị con số tiền nào trước một lần bấm có chủ ý | Rà lại từng lối vào nhật ký sau mỗi lần đổi giao diện | Mỗi lần đổi giao diện nhật ký |
| USC-004 | Nhật ký không bao giờ chạm được vào đường đặt lệnh | Chưa có | 0 trường hợp một thao tác nhật ký phát ra lệnh hoặc sửa lệnh; và khi nhật ký đang mở, độ trễ từ lúc bấm tới lúc sàn xác nhận vẫn nằm trong ngân sách ở `docs/_shared/system-overview.md` | Đo độ trễ đặt lệnh trong hai điều kiện — nhật ký đóng và nhật ký đang mở — mỗi lần thêm màn nhật ký mới; ghi nhận sự cố phát lệnh khi xảy ra | Hằng tháng và mỗi lần thêm màn mới |
| USC-005 | Trả lời được câu "tháng qua đêm nào tôi giữ được quy trình" mà không phải lục | Chưa có — xác lập từ 10 buổi tối đầu | Chỉ ra được đêm đó **ngay từ bản đồ nhiệt**, không phải mở từng ngày để dò | Người chơi tự trả lời có/không một lần mỗi tháng khi nhìn lại tháng vừa xong | Hằng tháng |
| USC-006 | Giờ phiên thị trường không bao giờ lệch | Chưa có | 0 lần đọc sai giờ ở bất kỳ mốc đổi giờ nào của London, New York hoặc Sydney, kể cả trong cửa sổ châu Âu đã đổi mà Mỹ thì chưa | Đối chiếu bốn đồng hồ với giờ thật ngay sau mỗi mốc đổi giờ | Sau mỗi mốc đổi giờ — khoảng 6 lần một năm (châu Âu ×2, Mỹ ×2, Úc ×2) |

## 10. Open Questions

* [ ] OQ-1: Một ngày không giao dịch hiện màu gì trên bản đồ nhiệt để không bao giờ bị đọc nhầm thành đêm tệ — cùng thang màu quy trình, một màu trung tính riêng, hay một ký hiệu riêng?
* [ ] OQ-2: Giữa phiên có cần ghi chú nhanh bằng tay cầm không, ngoài tự chấm 1–5 và memo giọng nói? Nếu có thì hình thức nào chịu được ràng buộc "ngắn và bằng tay cầm"?
* [ ] OQ-3: Việc gắn một lệnh với luận điểm của ngày thuộc feature nào? Kế hoạch của ngày do `daily-journal` sở hữu, nhưng việc đối chiếu kế hoạch với thứ đã làm thuộc `execution-learning`. **Nên chốt trước `/srs` của `daily-journal`** — để muộn thì hai feature dễ dựng trùng cùng một đường liên kết lệnh với luận điểm.
* [ ] OQ-4: Feature `execution-learning` vừa tách 2026-08-28 — giữ tên slug này không, và URD của nó viết trước hay sau `/srs` của `daily-journal`?
* [ ] OQ-5: Memo giọng nói tìm kiếm được theo chữ hay chỉ mở được qua lệnh gắn với nó? `voice-journal` OQ-6 hỏi đúng câu này và trỏ ngược về đây — hai feature phải chốt cùng lúc. Câu tương tự cho **kế hoạch của ngày, ghi chú và nguyên tắc**: có tìm theo chữ không? Nếu không thì với dữ liệu giữ vô hạn, thứ đã viết ra chỉ tìm lại được qua ngày hoặc qua lệnh.
* [ ] OQ-6: Quy tắc "buổi tối vắt qua nửa đêm thuộc ngày bắt đầu" có đúng với cả phiên Sydney/Tokyo không, hay mốc gom phải theo khung giờ phiên mà người chơi tự đặt ở `order-execution`?
* [ ] OQ-7: `process-score` có cung cấp điểm ở mức **buổi tối** không, hay chỉ mức phiên? Nếu chỉ mức phiên thì quy tắc gộp nhiều phiên thành một ô thuộc feature nào — chốt cùng `process-score`.
* [ ] OQ-8: Những lần tự huỷ **không dẫn tới lệnh nào** hiện ở đâu? `trade-replay` OQ-7 đang hỏi ngược về đây. Ứng viên tự nhiên là chi tiết một buổi tối trong nhật ký, nhưng con số cộng dồn đã chốt thuộc `process-score` — cần chốt một lần cho cả ba tài liệu.
* [x] OQ-9 đã chốt 2026-08-28: URD `reports-export` **viết trước** — xem `docs/reports-export/reports-export-urd.md`. Nó nhận cảnh báo dung lượng (UN-017), sao lưu (UN-008) và xoá sạch (UN-014..016). Sản phẩm **chỉ cảnh báo dung lượng, không nhắc sao lưu định kỳ**, nên chỗ dựa duy nhất của ràng buộc "giữ vô hạn" là cảnh báo đó.
* [ ] OQ-11: **Mâu thuẫn xuyên tài liệu** phát hiện khi viết `reports-export`: màn cài đặt có mục *hạn giữ nhật ký* (`phase-13`), trong khi Mục 7 ở đây đã chốt nhật ký **giữ vô hạn, không bao giờ tự xoá thứ gì**. Hai điều không thể cùng đúng — cùng OQ-2 của `reports-export`.
* [ ] OQ-10: Gỡ **một** ảnh hoặc một ghi chú vừa đính: gỡ hẳn, hay đánh dấu đã gỡ mà vẫn giữ vết?
