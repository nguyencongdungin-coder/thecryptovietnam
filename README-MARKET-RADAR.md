# TCV Market Radar — Bản tích hợp vào THE CRYPTO VIETNAM

## Đã làm
- Chèn khối **TCV MARKET RADAR** ngay bên dưới phần **KHÁM PHÁ THE CRYPTO VIETNAM** trên trang chủ, phía trên phần KẾT NỐI CÙNG CỘNG ĐỒNG.
- Trang chủ hiển thị **12/20 coin** theo thanh khoản 24h, tự động đọc dữ liệu đã xác minh từ `market-radar/data/latest.json`.
- Trang `/market-radar/` hiển thị Top 20 Futures, lọc theo tăng/giảm giá 24h hoặc khối lượng nến 15 phút bất thường; hỗ trợ đổi kiểu sắp xếp.
- Tệp `scan.py` hiện viết dữ liệu Radar từ **cùng lần quét dữ liệu thật** của TCV AI Signal. Không tạo giá hoặc tín hiệu giả. Workflow tự commit thêm Radar JSON.
- Nút Radar trên trang chủ và trang riêng kết nối với TCV AI Signal, giữ nguyên menu và nút **Tham gia**.

## Cách dùng miễn phí
1. Giải nén, tải **toàn bộ nội dung bên trong** lên repository website GitHub Pages. Sao lưu website trước khi thay file.
2. Vào Actions > `TCV AI Signal — Free Futures Scanner and Site` > Run workflow.
3. Chờ workflow chạy thành công. Kiểm tra tệp `market-radar/data/latest.json` có `generated_at` và `coins` thật.
4. Vào website trang chủ, hoặc `/market-radar/`. Nếu dữ liệu quá **40 phút** hoặc chưa có, Radar sẽ không hiển thị các phần trăm cũ.
5. Nếu sử dụng Cloudflare Pages/Netlify thay vì GitHub Pages, cần cấu hình thêm cách đồng bộ dữ liệu mới từ GitHub Actions sang host đó; chỉ tải file tĩnh một lần thì dữ liệu không tự cập nhật. GitHub Pages được cấu hình sẵn trong workflow.

## Phương pháp
- Chọn Top 20 hợp đồng Futures vĩnh cửu USDT theo `quoteVolume` 24h của Binance USD-M Futures.
- Màu phản ánh `priceChangePercent` 24h của Binance; không phải dự đoán.
- Volume bất thường: `volume_ratio` từ 15m đã đóng >= 2 so với trung bình 20 nến đóng trước.
- Điểm bất thường quy tắc = min(100, round(min(|biến động 24h|,20)*3 + min(max(volume_ratio-1,0),4)*10)); **không phải xác suất thành công**.
- Quét GitHub Actions định kỳ dự kiến 15 phút; lịch có thể trễ; miễn phí nếu nằm trong hạn mức nền tảng.

## Trạng thái kiểm chứng
- Mã Python và JavaScript đã qua kiểm tra cú pháp; unit tests đã chạy.
- Chưa chạy end-to-end với Binance do môi trường hiện tại không có kết nối internet tới API Futures; chưa thể khẳng định dữ liệu LIVE hoặc Telegram chạy thành công.
- Đây là bộ lọc thông tin nghiên cứu, không đặt lệnh và không phải lời khuyên đầu tư.
