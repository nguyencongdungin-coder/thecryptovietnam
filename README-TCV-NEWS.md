# THE CRYPTO VIETNAM – Tin tức đáng chú ý

Trang chủ hiển thị 3 tiêu đề RSS gần nhất, trang `tin-tuc.html` hiển thị tối đa 18 tiêu đề. Tin dẫn thẳng đến bài gốc của nhà xuất bản; không sao chép nội dung bài và không tự dịch/diễn giải thiếu kiểm chứng.

## Triển khai

- Giải nén gói PATCH và tải các file lên đúng vị trí trong GitHub repository. `index.html`, `dashboard.css`, `tin-tuc.html`, `news/news.js`, `news/data/latest.json`, `news/fetch_news.py`, `tests/test_news.py`, `README-TCV-NEWS.md`.
- Mở `.github/workflows/signal.yml` và thay nội dung bằng workflow mới trong PATCH, để tự đồng bộ RSS cùng chu kỳ quét OKX hiện có.
- Workflow đã sử dụng `GitHub Actions` deploy Pages, không chuyển về `Deploy from a branch`.
- Run workflow thủ công một lần; trong log kiểm tra bước `Collect RSS news headlines`, `Commit updated data`, `Deploy THE CRYPTO VIETNAM`.
- GitHub runner có thể bị RSS chặn, và GitHub scheduled jobs có thể chạy trễ. Khi không có tin mới, hệ thống giữ dữ liệu cũ, không tạo tin giả.

## Nguồn và biên tập

RSS được khai báo trong `news/fetch_news.py`: CoinDesk, Decrypt, Cointelegraph. Cần kiểm tra điều khoản RSS của các nhà xuất bản nếu sử dụng thương mại. Hiển thị tiêu đề tiếng Anh gốc, nguồn, thời gian xuất bản GMT+7 và liên kết gốc. **Chưa có bản tóm tắt/dịch tự động tiếng Việt**; việc này nên triển khai sau, có quy trình duyệt để tránh sai tin.

Không cần OPENAI_API_KEY hay dịch vụ tính phí. Mục tin cập nhật khi workflow OKX chạy theo lịch. Không cần thêm workflow news riêng tránh xung đột triển khai GitHub Pages.
