# THE CRYPTO VIETNAM — Chuyển bộ quét Futures sang OKX

1. Giải nén gói patch, sao chép đúng cấu trúc vào nhánh `main` của repository hiện có, thay thế tệp trùng tên.
2. ĐẶC BIỆT cập nhật `.github/workflows/signal.yml` riêng bằng GitHub editor nếu trình tải lên bỏ qua thư mục ẩn `.github`.
3. **Giữ nguyên** `engine.py`, `requirements.txt`, `CNAME`, trang web và dữ liệu JSON có sẵn. Không xóa `ai-signal/data/` hoặc `market-radar/data/`.
4. Trong GitHub, Actions → TCV AI Signal - Futures Scanner and Site → Run workflow.
5. Kiểm tra thứ tự: Run tests → Scan OKX public USDT perpetual SWAP market data → Commit updated data → Deploy. Sau đó mở website kiểm tra nguồn OKX, thời điểm cập nhật và danh sách Top 20.
6. Nếu workflow thất bại, không lặp lại liên tục. Chụp log bước đầu tiên bị lỗi. Không dùng giá, tín hiệu giả.

**Lưu ý:** Bước thử OKX trước đây chỉ xác minh một hợp đồng BTC 3 khung nến. Quét đầy đủ 20 hợp đồng x 3 khung cần kiểm thử trên GitHub Actions. Bản này dự kiến lấy tối đa 300 nến 1H cho backtest ngắn, không tuyên bố đủ 1000 nến. Khối lượng xếp hạng Top 20 là **ước tính USDT** tính từ `volCcy24h` (đồng cơ sở) × `last`, không phải doanh số thực hiện chính xác. Hệ thống hiện thực hóa phân tích dựa trên quy tắc, không phải AI học máy.
