# TCV — Chỉnh khoảng đệm trên bên trong TradingView Ticker

Lần này thay đổi **đúng phần trong thanh ticker**, không chỉ chỉnh khoảng trống phía trên banner.
- Khung hiển thị được cắt gọn chiều cao; đưa widget lên 6px bằng CSS transform và clip phần phía trên.
- Vẫn giữ hiệu ứng chuyển động, nguyên mã nhúng, liên kết bị chặn và các phần website khác.
- Do TradingView là widget bên ngoài, khoảng đệm cụ thể có thể thay đổi theo phiên bản nhúng và trình duyệt.

Cập nhật nhanh: sao lưu rồi thay `style.css`, tải lại bằng Ctrl+F5. Nếu không thấy thay đổi, xem tab Network/Styles để chắc chắn style.css mới được tải và không dùng cache.
