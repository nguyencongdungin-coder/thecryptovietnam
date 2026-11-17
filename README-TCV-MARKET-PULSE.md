# TCV Market Pulse

Thay ô Tổng quan thị trường đầu tiên trong trang chủ bằng TCV Market Pulse. Bốn chỉ số còn lại giữ nguyên.

- Dùng dữ liệu thực từ Binance Spot API `/api/v3/ticker/24hr`.
- Chọn 100 cặp USDT có quote volume 24H lớn nhất (loại stablecoin, fiat và token đòn bẩy phổ biến).
- Giá biến động 24H > +0,1%: tăng; < -0,1%: giảm; còn lại: đi ngang.
- Cập nhật mỗi 5 phút khi tab hoạt động.
- Độ rộng thị trường Binance Spot không đại diện cho toàn bộ thị trường.
- Nếu mạng chặn Binance, sẽ báo lỗi (không chế dữ liệu).
- Khi cập nhật website chỉ cần thay `index.html`, `style.css` và thêm `tcv-market-pulse.js`.
- Các API có thể thay đổi và bị chặn theo khu vực; cần kiểm tra trên hosting thực tế.
