---
type: brainstorm
feature: mentor-signals
status: draft
updated: 2026-08-29
links:
  - docs/ai-desk/srs/ai-desk-spec.md
  - docs/_shared/system-overview.md
  - docs/playbook-grading/srs/playbook-grading-spec.md
---

# Tham chiếu tín hiệu từ thầy

## 1. Tổng quan

Người chơi có **hai người thầy** mà mình rất tôn trọng. Mỗi thầy đã có hệ thống phân tích riêng và
đã bắn được tín hiệu ra ngoài. Tính năng này đưa tín hiệu của hai thầy **vào trong game để đọc** —
đúng lúc cần, đủ chi tiết để quyết định tốt hơn — và **dừng lại ở đó**.

Game **không** đặt lệnh theo thầy, **không** chấm điểm người chơi theo thầy, và **không** xếp hạng
thầy nào đúng hơn. Nó chỉ trả lời một câu hỏi: *"lúc này thầy đang nhìn thị trường thế nào?"*

## 2. Vấn đề & bối cảnh

Hiện tại tín hiệu của thầy nằm ngoài game. Người chơi phải mở ứng dụng khác ở màn hình bên cạnh,
tự nhớ, và khi tối review lại thì tín hiệu đã trôi mất — không còn đối chiếu được *"lúc tôi vào lệnh
đó, thầy đang nói gì"*.

Ba cái mất: **mất thông tin lúc cần** (đang nhìn chart mà tín hiệu ở cửa sổ khác), **mất sự chú ý**
(chuyển cửa sổ giữa phiên là lúc dễ hỏng nhất), và **mất bài học sau phiên** (không có bản ghi để so).

## 3. Người dùng & quyền truy cập

| Ai | Vai trò | Ghi chú |
|---|---|---|
| **Người chơi** | Người duy nhất đọc tín hiệu | Sản phẩm cá nhân, một người dùng |
| **Thầy A**, **Thầy B** | Nguồn tín hiệu, ngoài hệ thống | Không có tài khoản trong game, không đăng nhập, không thấy gì của người chơi. Quan hệ **một chiều vào** |

Mỗi thầy bắn tín hiệu qua **webhook có mã thầy nằm trong đường dẫn**. Sai mã thì tín hiệu bị bỏ
ngay ở cửa vào. Người chơi **bật hoặc tắt từng thầy độc lập** trong Cài đặt; thầy đang tắt thì
không nhận, không hiện, không lưu.

## 4. Năng lực

### P0 — không có thì tính năng vô nghĩa

- Nhận tín hiệu qua webhook và **biết chắc là của thầy nào**
- Chỉ giữ tín hiệu cho **bốn cặp game thật sự giao dịch**; cặp khác bỏ ngay
- Lưu và hiện: hướng mua/bán · giá vào · SL · TP nếu có · vùng chốt nếu có · **ảnh setup**
- **Tab Thầy** trong bàn làm việc — nơi đọc đầy đủ, có ảnh
- **Dải bối cảnh** hiện tín hiệu lúc đang xem, và **tắt dòng thầy ngay khi giữ cò**
- Tín hiệu thầy **không bao giờ là đầu vào của chấm điểm**
- Bật / tắt riêng từng thầy

### P1 — làm tính năng đáng giá

- **Đối chiếu sau phiên** ở chi tiết lệnh: lúc vào lệnh thầy đang có tín hiệu gì
- Đánh dấu **"đã cũ"** cho tín hiệu quá hạn
- Giới hạn số tín hiệu mỗi giờ để hệ thống bên thầy lỗi cũng không làm ngập game

### P2 — có thì tốt

- Phóng to ảnh setup bằng cần analog trong tab Thầy
- Thống kê *"bao nhiêu lần tôi vào ngược thầy, và kết quả ra sao"*

## 5. Luồng chính

1. Thầy A bắn tín hiệu qua webhook, đường dẫn mang mã riêng của Thầy A.
2. Game đọc mã, **xác định đúng thầy nào**. Sai mã thì bỏ, chỉ ghi vào nhật ký kỹ thuật — không
   làm phiền người chơi giữa phiên.
3. Game xem cặp. Ngoài XAUUSD / EURUSD / GBPUSD / USDJPY thì **bỏ luôn**.
4. Game xem thầy đó có đang bật không, và giờ này đã nhận quá nhiều chưa.
5. Game lưu tín hiệu và ảnh setup.
6. Tín hiệu hiện **hai chỗ**: dải bối cảnh (nếu đúng cặp người chơi đang xem) và tab Thầy.
7. Người chơi đọc. Muốn kỹ thì bấm `Menu` sang tab Thầy — mở Menu vốn đã huỷ ARM và khoá mở lệnh,
   nên đọc ảnh setup ở đó là **đọc trong trạng thái không thể lỡ tay bắn**.
8. Người chơi tự quyết. Giữ `LT` để ARM: **dòng thầy tắt**, chỉ còn con số đã đọc lúc mấy giờ.
   Overlay xác nhận vẫn chỉ nói **playbook của người chơi** và số luật sắp được chấm.
9. `LT+RT` thì lệnh đi — hoặc không đi. Cả hai đều **không liên quan tới tín hiệu thầy**.
10. Quá hai tiếng, tín hiệu xám đi và ghi **"đã cũ"**.
11. Sau phiên, chi tiết lệnh hiện *"lúc anh vào, thầy đang có gì"* — **chỉ để đối chiếu**.

```
   Thầy A                                   Thầy B
(hệ thống riêng)                        (hệ thống riêng)
     └────────── webhook · URL có mã thầy ──────────┘
                          │
                  ┌───────▼────────┐   sai
                  │ Mã thầy đúng?  ├────────► BỎ, chỉ ghi nhật ký kỹ thuật
                  └───────┬────────┘
                       đúng│
                  ┌───────▼────────────┐  không
                  │ Cặp game có chơi?  ├────────► BỎ LUÔN — đỡ nhiễu
                  └───────┬────────────┘
                        có│
                  ┌───────▼────────────┐  tắt / quá
                  │ Thầy đang bật?     ├────────► BỎ + ghi 1 dòng
                  │ Chưa quá 30/giờ?   │          cảnh báo ở tab Thầy
                  └───────┬────────────┘
                        ok│
                  ┌───────▼──────────────────────────┐
                  │ LƯU: hướng · entry · SL ·        │
                  │ TP? · vùng chốt? · ảnh ≤2MB      │
                  └───────┬──────────────────────────┘
            ┌─────────────┴─────────────┐
            ▼                           ▼
 ┌────────────────────┐      ┌─────────────────────────┐
 │ DẢI BỐI CẢNH       │      │ TAB THẦY  (mở bằng Menu)│
 │ THẦY A: MUA 2412.5 │      │ đủ chữ + ẢNH SETUP      │
 │ SL 2409.0          │      │ Menu đã huỷ ARM và      │
 │ (chỉ cặp đang xem) │      │ khoá mở lệnh sẵn        │
 └─────────┬──────────┘      └────────────┬────────────┘
           └──────────────┬───────────────┘
                          ▼
              ┌───────────────────────┐
              │  NGƯỜI CHƠI TỰ QUYẾT  │
              └───────────┬───────────┘
                    giữ LT (ARM)
                          ▼
              ┌─────────────────────────────────┐
              │ DÒNG THẦY TẮT                   │
              │ chỉ còn: THẦY ·2 (đã đọc 20:14) │
              │ overlay vẫn là: playbook CỦA    │
              │ NGƯỜI CHƠI + số luật sắp chấm   │
              └───────────┬─────────────────────┘
                    LT+RT → lệnh đi
                          ▼
              ┌─────────────────────────────────┐
              │ KHÔNG vào chấm điểm.            │
              │ Chỉ ghi kèm để SAU PHIÊN        │
              │ đối chiếu ở chi tiết lệnh       │
              └─────────────────────────────────┘
```

## 6. Hành vi hệ thống — đào sâu

### 6.1 Điểm rẽ nhánh

| # | Khi nào | Có | Không |
|---|---|---|---|
| DP-1 | Mã thầy trong đường dẫn có khớp Thầy A hoặc Thầy B? | Đi tiếp, gắn tên thầy | Bỏ, ghi nhật ký kỹ thuật, không báo người chơi |
| DP-2 | Cặp nằm trong bốn cặp game giao dịch? | Đi tiếp | **Bỏ luôn** — chấp nhận mất thông tin để đổi lấy đỡ nhiễu |
| DP-3 | Thầy đó đang bật? | Đi tiếp | Bỏ, không lưu |
| DP-4 | Giờ này thầy đó đã bắn dưới 30 tín hiệu? | Lưu | Bỏ phần dư, ghi một dòng cảnh báo ở tab Thầy |
| DP-5 | Có ảnh setup và ảnh dưới 2 MB? | Lưu cả ảnh | Giữ phần chữ, ghi *"ảnh quá lớn, đã bỏ"* |
| DP-6 | Tín hiệu thuộc cặp người chơi đang xem? | Hiện trên dải bối cảnh | Chỉ nằm trong tab Thầy |
| DP-7 | Người chơi đang giữ cò (ARM)? | **Tắt dòng thầy**, chỉ còn con số | Hiện đủ hướng, giá vào, SL |

### 6.2 Hai thầy nói gì thì hiện thế nào

| Thầy A | Thầy B | Dải bối cảnh hiện |
|---|---|---|
| MUA | BÁN | **Hiện cả hai, ngược nhau** — không cảnh báo, không gộp, không nói ai đúng |
| MUA | MUA | Hiện cả hai **riêng biệt** — không gộp thành một dòng |
| MUA | *(chưa có)* | Chỉ Thầy A |
| *(đang tắt)* | BÁN | Chỉ Thầy B |
| *(bắn cặp ngoài)* | BÁN | Chỉ Thầy B — tín hiệu cặp ngoài đã bị bỏ từ cửa vào |

Ngược nhau là **chuyện bình thường**, không phải lỗi. Game không có ý kiến gì về việc đó.

### 6.3 Vòng đời một tín hiệu

| Từ | Sang | Trigger | Quay lại? |
|---|---|---|---|
| *(chưa có)* | **mới** | Nhận webhook hợp lệ | — |
| mới | **đã cũ** | Quá 2 giờ kể từ lúc nhận | Không |
| mới | **đã bị thay** | Thầy gửi bản cập nhật (khác con số) | Không — bản cũ vẫn đọc được *(thêm 2026-08-29 qua `/urd`, OQ-10)* |
| mới hoặc đã bị thay | **đã huỷ** | Thầy gửi tin huỷ/thoát | Không — vẫn đọc được kèm giờ huỷ *(thêm 2026-08-29 qua `/urd`, OQ-10)* |
| mới hoặc đã cũ | **ảnh hết hạn** | Quá 90 ngày | Không — phần chữ vẫn còn |
| *(bất kỳ)* | **bị bỏ** | Sai mã · cặp ngoài · thầy tắt · vượt 30/giờ | Không — không được lưu ngay từ đầu |

Tín hiệu **đã cũ** vẫn đọc được, chỉ xám đi và ghi rõ giờ nhận. Không tự xoá khỏi màn hình.

### 6.4 Đứt gánh giữa đường

| Tình huống | Hành vi |
|---|---|
| **Gateway trên VPS ngừng lúc thầy bắn** | Tín hiệu mất luôn, thầy không gửi lại. Tab Thầy **không giả vờ là đã đủ**. Lưu ý: **đóng Chrome thì không mất gì** — gateway chạy suốt và vẫn nhận, mở game lên là thấy |
| **Đang ARM thì tín hiệu mới về** | Con số đếm tăng ngầm, **không bật dòng thầy lên**. Không cắt ngang lúc đang cầm cò |
| Mất mạng lúc đang tải ảnh | Giữ phần chữ, ghi *"ảnh chưa tải được"* |
| Ảnh vượt 2 MB | Bỏ ảnh, **giữ chữ**, ghi *"ảnh quá lớn, đã bỏ"* |
| Thầy bắn lại y hệt | Gộp, không nhân đôi |
| Đang mở tab Thầy thì tín hiệu mới về | Chèn lên đầu, **không tự cuộn** — tránh người chơi đọc nhầm dòng |
| Thầy gửi thiếu SL | **Vẫn hiện**, ghi rõ *"thầy không gửi SL"*. Không bịa, không loại |
| Thầy gửi thiếu **trường bắt buộc** (hướng, giá vào) | Không dùng được, nhưng vẫn hiện một dòng *"nhận được một tín hiệu không đọc được từ Thầy A"*. Đây là cách phân biệt **thầy im** với **hệ thống hỏng** *(sửa 2026-08-29 qua `/urd`, OQ-13)* |

### 6.5 Các tình huống biên khác

- Hai thầy bắn cùng lúc cùng cặp: cả hai vào, xếp theo **giờ nhận**, không ưu tiên ai.
- Thầy bắn tín hiệu cho thời điểm trong quá khứ: vẫn nhận, tính tuổi theo **giờ ghi trong tín hiệu**,
  không theo giờ game nhận được.
- Người chơi tắt một thầy giữa phiên: tín hiệu cũ của thầy đó **vẫn nằm trong nhật ký** để sau phiên
  đối chiếu, chỉ ngừng hiện trên dải bối cảnh.
- Đổi mã thầy trong Cài đặt: tín hiệu cũ giữ nguyên, tín hiệu gửi bằng mã cũ bị bỏ từ đó trở đi.

## 7. Kiểm tra, giới hạn & câu chữ

### 7.1 Bắt buộc / tuỳ chọn trong một tín hiệu

| Trường | Bắt buộc | Ghi chú |
|---|---|---|
| Tên thầy | Bắt buộc | Suy ra từ mã trong đường dẫn, không lấy từ nội dung tín hiệu |
| Cặp | Bắt buộc | Ngoài bốn cặp thì bỏ |
| Hướng mua/bán | Bắt buộc | Thiếu thì không dùng được, nhưng **vẫn hiện một dòng** *"nhận được một tín hiệu không đọc được từ Thầy A"* — không bỏ câm *(sửa 2026-08-29 qua `/urd`, OQ-13)* |
| Giá vào | Bắt buộc | |
| SL | Thường có | Thiếu thì vẫn hiện, ghi rõ là thiếu |
| TP | Tuỳ chọn | Thiếu thì ghi *"thầy không đặt TP"* |
| Vùng chốt | Tuỳ chọn | |
| Ảnh setup | Thường có | Tối đa 2 MB |

### 7.2 Giới hạn đã chốt

| Hạng mục | Giá trị |
|---|---|
| Số thầy | **2** — Thầy A, Thầy B |
| Trần tín hiệu | **30 mỗi giờ mỗi thầy** |
| Ảnh setup | **Tối đa 2 MB**, giữ **90 ngày** |
| Tín hiệu thành "đã cũ" | Sau **2 giờ** |
| Phần chữ của tín hiệu | Giữ **lâu hơn ảnh**, không xoá theo mốc 90 ngày |
| Cặp nhận | **XAUUSD · EURUSD · GBPUSD · USDJPY**; ngoài ra bỏ |

### 7.3 Câu chữ mẫu

**Báo lỗi**

| Tình huống | Câu chữ |
|---|---|
| Thầy bắn quá nhanh | `Thầy A gửi quá nhanh — đã bỏ {N} tín hiệu trong giờ này.` |
| Ảnh quá lớn | `Ảnh quá 2 MB — đã bỏ ảnh, giữ nội dung tín hiệu.` |
| Ảnh tải dở | `Chưa tải được ảnh setup.` |
| Sai mã thầy | *(không hiện cho người chơi — chỉ vào nhật ký kỹ thuật)* |

**Nội dung tín hiệu**

| Tình huống | Câu chữ |
|---|---|
| Đủ trường | `Thầy A: MUA 2412.5 · SL 2409.0 · TP 2421.0` |
| Không có TP | `Thầy A: MUA 2412.5 · SL 2409.0 · thầy không đặt TP` |
| Không có SL | `Thầy B: BÁN 2413.0 · thầy không gửi SL` |
| Quá hạn | `Đã cũ — nhận lúc 20:14, hơn 2 tiếng trước.` |
| Ảnh hết hạn lưu | `Ảnh đã hết hạn lưu (quá 90 ngày).` |
| Thầy đang tắt | `Thầy A đang tắt — không nhận tín hiệu.` |

**Lúc đang giữ cò**

| Tình huống | Câu chữ |
|---|---|
| Có tín hiệu, đã đọc | `THẦY ·2 (đã đọc lúc 20:14)` |
| Có tín hiệu, chưa mở tab lần nào | `THẦY ·2 (chưa đọc)` |

**Sau phiên**

| Tình huống | Câu chữ |
|---|---|
| Thầy ngược lệnh của người chơi | `Lúc anh vào lệnh: Thầy A MUA (ngược lệnh của anh) · Thầy B chưa có tín hiệu.` |
| Thầy cùng chiều | `Lúc anh vào lệnh: Thầy A MUA (cùng chiều) · Thầy B MUA (cùng chiều).` |
| Không thầy nào có tín hiệu | `Lúc anh vào lệnh: không thầy nào có tín hiệu cho cặp này.` |

## 8. Giả định

- Hệ thống bên hai thầy **đã chạy** và bắn được webhook ra ngoài — game không xây phần đó.
- Thầy **không** cần biết game tồn tại, không nhận lại gì từ game.
- Người chơi tin hai thầy này ở mức **muốn tham khảo**, không ở mức muốn sao chép lệnh.
- Tín hiệu là **thông tin cá nhân người chơi tự nhận**, không phân phối lại cho ai.

## 9. Rủi ro

| # | Rủi ro | Khả năng | Hậu quả nghiệp vụ | Cách phòng |
|---|---|---|---|---|
| R-1 | **Uy quyền của thầy thay chỗ quyền tự quyết** — người chơi vào lệnh vì thầy gật đầu chứ không vì playbook của mình | Thường | Điểm quy trình vẫn đẹp nhưng chất lượng quyết định tụt âm thầm; mục tiêu "tự tin" bị thay bằng "dựa dẫm" | Bốn lớp chặn đã chốt: tắt dòng thầy lúc ARM · không có mặt ở overlay xác nhận · không bao giờ vào chấm điểm · đối chiếu sau phiên để nhìn thẳng vào chuyện này |
| R-2 | Mã thầy lộ vì nằm trong đường dẫn | Hiếm | Người khác bắn tín hiệu giả vào tab Thầy. **Không đặt được lệnh nào** — ranh giới không-đặt-lệnh chặn từ gốc | Đổi mã được trong Cài đặt. Rủi ro chấp nhận được với công cụ cá nhân, tài khoản demo |
| R-3 | Hệ thống bên thầy đổi định dạng tín hiệu | Thỉnh thoảng | Tín hiệu vào thiếu trường, hoặc không vào nữa mà người chơi không biết | Thiếu trường thì **vẫn hiện và nói rõ thiếu gì**; không im lặng bỏ. Tab Thầy nói rõ danh sách có thể thiếu khi game từng tắt |
| R-4 | Ảnh setup phình dung lượng | Thỉnh thoảng | 2 MB × 30/giờ × 2 thầy là con số lớn nếu để lâu | Trần 2 MB, giữ 90 ngày, đếm được trong phần quản lý dữ liệu |
| R-5 | Bỏ cặp ngoài bốn symbol làm mất thông tin | Chắc chắn xảy ra | Thầy bắn cặp khác thì người chơi không biết là đã có | **Chấp nhận có ý thức** — đổi lấy dải bối cảnh sạch. Ghi lại đây để sau này muốn đảo ngược thì biết đã đánh đổi cái gì |

## 10. Chỉ số thành công

- Người chơi **mở tab Thầy trước khi ARM**, chứ không phải sau khi đã vào lệnh — cho thấy nó đang
  là tham khảo, không phải lời biện minh.
- **Điểm quy trình không tụt xu hướng** trong tháng đầu bật tính năng. Nếu tụt, đó là dấu hiệu R-1
  đang xảy ra và phải xử lý chứ không bảo vệ tính năng.
- **Đường đặt lệnh không hề bị chạm**: không lệnh nào chậm hơn, lỡ, hay bị chặn vì tín hiệu thầy về.
- Sau phiên, người chơi **đọc phần đối chiếu** — nếu không ai mở, phần đó không đáng giữ.

## 11. Ngoài phạm vi

- Tự động đặt lệnh theo thầy, dưới bất kỳ hình thức nào.
- Chấm điểm người chơi theo mức trùng khớp với thầy.
- Xếp hạng thầy, tính tỷ lệ thắng của thầy, hay nói thầy nào đáng tin hơn.
- Nhắn ngược lại cho thầy, hay để thầy thấy bất cứ gì của người chơi.
- Nguồn tín hiệu trả phí, dịch vụ sao chép lệnh, luồng mạng xã hội không chọn lọc.
- Nhận tín hiệu cho cặp game không giao dịch.

## 12. Câu hỏi mở

- ~~**OQ-1**~~ **Resolved 2026-08-29 qua `/urd` — tính năng riêng**, ở `docs/mentor-signals/`, dùng
  lại lane tín hiệu ngoài của `ai-desk` nhưng có danh tính thầy và lịch sử riêng.
- **OQ-2**: `ai-desk` đang ghi *"ngoài phạm vi: nguồn tín hiệu trả phí, dịch vụ sao chép lệnh"* —
  câu đó có cần sửa lại cho rõ **thầy do người chơi tự chọn thì khác** không?
- **OQ-3**: Tab Thầy là **tab thứ sáu** của bàn làm việc. Lướt bằng `LB/RB` có bắt đầu nhiều quá không?
- **OQ-4**: Đối chiếu sau phiên hiện ở **chi tiết lệnh**, ở **replay**, hay cả hai?
- **OQ-5**: **Vùng chốt** khi thầy có gửi thì trình bày thế nào — một dải giá, hay nhiều mức rời?
