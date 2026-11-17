# TCV Live Crypto Price Ticker

Thanh giá chạy phải sang trái được đặt ngay dưới banner trên trang chủ (`index.html`), phía trên Tổng quan thị trường.

- Dữ liệu: Binance Spot public API, không yêu cầu API key.
- Chọn 40 cặp USDT có khối lượng quy đổi USDT (quoteVolume) cao nhất trong 24 giờ, lọc stablecoin và leveraged token phổ biến; cập nhật thứ hạng mỗi 5 phút.
- Giá và phần trăm 24 giờ: kết nối Binance WebSocket `!miniTicker@arr` (tính % từ giá đóng và giá mở 24h), không cần API key.
- Chạy liên tục từ phải qua trái; dừng khi rê chuột/điều hướng bằng bàn phím; tôn trọng `prefers-reduced-motion`.
- Khi không thể kết nối, hiển thị trạng thái dữ liệu chứ không tự bịa giá.
- Có thể có hạn chế truy cập API/WebSocket theo mạng hoặc khu vực. Cần mở bằng HTTP(S), không phải `file://`.

Kiểm tra cục bộ: giải nén và mở PowerShell trong thư mục gốc, chạy `py -m http.server 8000`, sau đó vào `http://localhost:8000/`.

Lưu ý: ticker này sử dụng **Binance Spot**, còn TCV AI Signal / Market Radar tiếp tục dùng dữ liệu Futures riêng như trước.
