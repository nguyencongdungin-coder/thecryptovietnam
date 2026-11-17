# THE CRYPTO VIETNAM — Dashboard mới

Giao diện trang chủ được nâng cấp theo bản mockup người dùng đã duyệt.

## Bố cục
1. TCV Market Pulse (Top 100 Spot) + chỉ số Fear & Greed (Alternative.me) + mô tả độ rộng thị trường.
2. Thanh giá TradingView hiện có (giữ nguyên nhãn nguồn/thuộc tính của tiện ích).
3. Số liệu tổng quan CoinGecko/CoinPaprika.
4. Top 5 vốn hóa động, TCV Market Movers theo dữ liệu Spot 24h, TCV AI Signal.
5. Tin tức (liên kết đến nguồn Reuters, không đặt bài giả), Market Alerts (ngưỡng biến động 24h có thể giải thích), Watchlist (lưu localStorage).
6. Khám phá, TCV Market Radar và cộng đồng hiện có.

## Lưu ý dữ liệu
- Không có số giá hoặc tín hiệu giao dịch giả định; nếu chưa kết nối, giao diện ghi rõ chưa có dữ liệu.
- Market Movers lọc 100 cặp giao dịch Spot USDT có thanh khoản cao. Hàng thứ ba hiển thị **khối lượng giao dịch 24 giờ lớn**, KHÔNG phải tỷ lệ tăng vọt bất thường (cần dữ liệu lịch sử để kết luận bất thường).
- TCV Market Alerts là diễn biến 24h được tính khi tải trang, KHÔNG phải cảnh báo giá tức thì hoặc dịch vụ gửi thông báo nền.
- Chỉ số Fear & Greed dùng dữ liệu từ Alternative.me, có thể không tải được do CORS/giới hạn mạng.
- TCV AI Signal và Radar vẫn dựa trên dữ liệu quét thực tế của dự án hiện tại, không tạo tín hiệu giả.
- Watchlist lưu dữ liệu trên thiết bị người dùng qua localStorage, không đồng bộ tài khoản.
- Trang tĩnh miễn phí, thích hợp với GitHub Pages.

## Kiểm tra
Có thể giải nén và mở index.html để xem giao diện; để các request dữ liệu hoạt động ổn định hơn, chạy qua web server hoặc đăng lên GitHub Pages. Giữ nguyên cấu trúc thư mục khi đăng.
