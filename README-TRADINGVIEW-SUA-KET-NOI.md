# TCV TradingView Ticker — sửa trạng thái kết nối

- Đổi nguồn web-component sang URL trong tài liệu chính thức: `https://widgets.tradingview-widget.com/w/en/tv-ticker-tape.js`.
- Nếu script không tải, thông báo lỗi thay vì đợi vô hạn.
- Có thêm `tcv-tradingview-status.js`. Nếu chỉ cập nhật riêng, phải thay `index.html`, `style.css` và **thêm** file JS này.
- Chạy bằng máy chủ local `py -m http.server 8000` và mở `http://localhost:8000/` thay vì file://.
- Nếu vẫn lỗi, thử tắt adblock cho trang, kiểm tra trình duyệt/mạng truy cập được domain widgets.tradingview-widget.com.
- Không thay đổi các công cụ khác; không dùng dữ liệu giá giả.
- Chưa thể xác nhận tải được widget trên mạng của bạn.
