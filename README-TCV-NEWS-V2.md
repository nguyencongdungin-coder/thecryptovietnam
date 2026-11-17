# THE CRYPTO VIETNAM — TCV News V2 (miễn phí)

## Những gì đã triển khai

- RSS gốc CoinDesk / Decrypt / Cointelegraph được giữ nguyên.
- Lọc tin theo chủ đề crypto, tránh tin cổ phiếu công nghệ không liên quan, loại tiêu đề quảng cáo.
- Chấm điểm chủ đề + độ mới, ưu tiên pháp lý / ETF / bảo mật, cố gắng đa dạng nguồn trong 3 tin trên trang chủ.
- Gắn nhãn chủ đề bằng tiếng Việt. Không bịa hoặc dịch sai tiêu đề.
- Hỗ trợ HIỂN THỊ bản dịch và tóm tắt tiếng Việt **chỉ khi được người quản trị đánh dấu approved: true** trong `news/data/approved_vi.json`.
- Không thêm API, không phụ thuộc máy chủ mới, không sửa workflow OKX hiện có.

## Đưa lên GitHub (giữ nguyên website và OKX)

Tải nội dung bản ZIP patch lên thư mục gốc repository `thecryptovietnam`:

- `news/fetch_news.py`
- `news/news.js`
- `news/data/approved_vi.json`
- `tests/test_news_v2.py`
- `dashboard.css`
- `index.html`
- `tin-tuc.html`
- `README-TCV-NEWS-V2.md`

Không sửa `.github/workflows/signal.yml`, `scan.py`, các JSON tín hiệu và `CNAME`.
Sau khi Commit, vào **Actions → TCV AI Signal - Futures Scanner and Site → Run workflow**.
Xem bước `Collect RSS news headlines` và `Deploy THE CRYPTO VIETNAM`.

## Bản dịch được duyệt (tùy chọn, không tự tạo bản dịch)

Trong `news/data/approved_vi.json`, người quản trị có thể bổ sung:

```json
{
  "items": {
    "https://example.com/original-article": {
      "approved": true,
      "title_vi": "Tiêu đề tiếng Việt đã kiểm chứng",
      "summary_vi": "Tóm tắt tiếng Việt dựa trên nội dung bài gốc đã đọc."
    }
  }
}
```

**Chỉ dùng URL bài thật từ `news/data/latest.json`, KHÔNG dùng URL example.com trong dữ liệu thật.** Khi không có bản dịch đã duyệt, hiển thị tiêu đề gốc. Nguồn và liên kết gốc được giữ. Dữ liệu nguồn cần được xác minh trước khi duyệt bản dịch. Không chép nguyên toàn văn bài báo.

## Giới hạn

Bản v2 CHƯA tự dịch 100% tiêu đề hoặc viết tóm tắt tiếng Việt. Công cụ dịch offline Argos Translate có thể nghiên cứu ở giai đoạn sau nhưng chưa nên tự đăng kết quả dịch máy lên trang tài chính. Quy tắc lọc bằng từ khóa cũng có thể bỏ sót tin quan trọng; nên xem lại sau vài ngày hoạt động.
