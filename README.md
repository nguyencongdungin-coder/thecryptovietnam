# THE CRYPTO VIETNAM — Website tĩnh

## Đăng lên GitHub Pages
1. Giải nén ZIP, tải **các tệp bên trong** lên thư mục gốc của nhánh `main` trong repository `thecryptovietnam` (không tải cả thư mục cha).
2. GitHub → Settings → Pages → Deploy from a branch → `main` / `(root)`.
3. Nếu đã cấu hình tên miền riêng, giữ `thecryptovietnam.com` trong Settings → Pages → Custom domain. Tệp `CNAME` đã được chuẩn bị sẵn.
4. Kiểm tra website trên máy tính và điện thoại; kiểm tra HTTPS và liên kết Facebook/X/Telegram.
5. Nếu còn workflow tự động RSS cũ trong `.github/workflows/`, hãy tắt/xóa workflow đó khi không sử dụng nữa.

## Dữ liệu
- Bảng giá và chỉ số dùng API công khai CoinGecko, làm mới khoảng 5 phút/lần khi trang đang mở.
- API công khai có giới hạn truy cập và có thể bị từ chối (429), CORS hoặc lỗi mạng. Khi lỗi, website hiển thị dữ liệu lưu gần nhất có chú thích hoặc thông báo không khả dụng; **không tạo giá giả**.
- Nếu website có nhiều khách truy cập, nên chuyển sang dữ liệu chung được cập nhật theo lịch bằng GitHub Actions và/hoặc gói API phù hợp.
- Hình hero được cắt từ bản mockup đã thống nhất; logo dùng nguyên tệp người dùng cung cấp.
- Các chủ đề bên phải là **đề tài gợi ý**, không phải bài viết hoặc số liệu thảo luận thật.

## Tùy chỉnh
- `index.html`: văn bản, menu, liên kết cộng đồng.
- `style.css`: giao diện và thiết bị di động.
- `app.js`: dữ liệu thị trường.
- `hero-art.webp`: ảnh minh họa.

Trang này không giới thiệu SBITCOIN hoặc các dịch vụ chưa triển khai.


Cập nhật: ảnh hero mới không có người đàn ông, chỉ có Bitcoin và Trái Đất kỹ thuật số; đã bỏ khẩu hiệu bên phải. Các thành phần còn lại giữ nguyên.


## Cập nhật thị trường và phân tích
- Trang chủ: bảng dữ liệu CoinGecko, yêu cầu làm mới khoảng mỗi 5 phút khi mở website (giới hạn bởi API và trình duyệt).
- `thi-truong.html`: widget TradingView tổng quan và biểu đồ vốn hóa/BTC dominance.
- `phan-tich.html`: biểu đồ kỹ thuật TradingView, đổi mã và khung thời gian.
- TradingView là widget nhúng từ bên thứ ba, không phải API dữ liệu trích xuất. Một số tiện ích cần internet, có thể bị chặn bởi trình duyệt hoặc thay đổi theo chính sách nhà cung cấp.
- Các biểu đồ TradingView và bảng CoinGecko có thể khác nhau về sàn, cặp giao dịch và phương pháp tính.
- Chưa xác minh trực quan trên trình duyệt thật; cần kiểm tra trước khi xuất bản.

- `kien-thuc.html`: trang kiến thức quản trị rủi ro, liên kết từ chủ đề trang chủ.
- Ba chủ đề trang chủ lần lượt mở trang phân tích Bitcoin, thị trường altcoin và kiến thức quản trị rủi ro. Chỉ nút khám phá nhóm cộng đồng dẫn sang Facebook.


## Binance WebSocket – bảng Top 5 trực tiếp
- `live-prices.js` dùng luồng `@ticker` của Binance Spot cho BTCUSDT, ETHUSDT, SOLUSDT, XRPUSDT, BNBUSDT.
- Giá là giá cặp USDT (không phải USD tổng hợp); phần trăm 24 giờ là cửa sổ trượt.
- Khi mất kết nối sẽ thử lại và hiển thị trạng thái, giữ giá cuối nhưng không tuyên bố là giá trực tiếp.
- CoinGecko tiếp tục cung cấp các chỉ số tổng quan, làm mới khoảng 5 phút/lần.
- Cần kiểm tra thực tế trên HTTPS/GitHub Pages và mạng truy cập của người dùng; mạng chặn Binance sẽ không có dữ liệu trực tiếp.


## Khắc phục bảng Tổng quan thị trường
- Thử CoinGecko `/api/v3/global` trước; nếu lỗi, tự chuyển sang CoinPaprika `/v1/global`.
- BTC dominance từ CoinPaprika; ETH dominance được tính từ vốn hóa ETH / vốn hóa toàn thị trường khi ticker ETH có sẵn; nếu thiếu hiển thị `—` thay vì đoán.
- Chỉ hiển thị thay đổi vốn hóa 24h khi nhà cung cấp có trường dữ liệu đó.
- Có thời gian cập nhật và nhãn dữ liệu cũ; khi cả hai API lỗi sẽ thông báo rõ.
- Nguồn bên thứ ba có thể bị giới hạn truy cập hoặc lỗi mạng; không bảo đảm hoạt động mọi thời điểm.


## Top 5 tự động theo vốn hóa
- Top 5 không cố định: lấy 50 đồng vốn hóa lớn nhất từ CoinGecko, loại các stablecoin phổ biến rồi chọn 5 đồng đầu tiên. Kiểm tra lại mỗi 30 phút.
- Bảng sử dụng Binance Spot WebSocket cho giá cặp USDT nếu có luồng dữ liệu; nếu không, hiển thị giá USD CoinGecko lần cập nhật gần nhất (không giả làm giá live).
- Nếu CoinGecko lỗi, dùng bảng xếp hạng lưu trong trình duyệt và thông báo rõ; người dùng mới không có dữ liệu lưu sẽ thấy thông báo lỗi thay vì danh sách giả.
- Danh sách loại trừ stablecoin dựa trên các ID/ký hiệu đã biết, cần bảo trì khi stablecoin mới xuất hiện.
- Kiểm tra hoạt động khi có internet qua HTTPS/GitHub Pages; một số trình duyệt hoặc mạng có thể chặn Binance.


## TCV AI Signal — tích hợp `/ai-signal/` (miễn phí)
- Menu AI Signal có trên toàn bộ trang hiện hữu. Website giữ nguyên `CNAME`, logo, giao diện và các trang cũ.
- Trang AI Signal: `ai-signal/index.html`; dữ liệu `ai-signal/data/latest.json` và `backtests.json`. Không có dữ liệu mô phỏng.
- `scan.py` + `engine.py`: quét Binance USD-M Futures, Top 20 USDT perpetual theo `quoteVolume` 24h; nến đóng 15m/1h/4h.
- GitHub Actions `.github/workflows/signal.yml`: quét theo lịch 15 phút (best effort), thử Telegram khi có secrets, commit JSON, rồi deploy **toàn bộ website** lên GitHub Pages.

### Cách xuất bản trên GitHub Pages
1. Sao lưu repository website hiện tại. Giải nén ZIP tích hợp và đưa **tất cả tệp và thư mục**, gồm `.github/workflows/signal.yml`, vào root repository đang lưu website, bằng Git push hoặc giao diện GitHub. Không thay CNAME đã có.
2. Vào **Settings → Pages → Build and deployment → Source: GitHub Actions** (thay cho Deploy from branch nếu đang chọn).
3. Vào **Settings → Actions → General → Workflow permissions** chọn **Read and write permissions**; xác nhận repository và Pages Actions được cho phép.
4. Vào **Actions → TCV AI Signal — Free Futures Scanner and Site → Run workflow**. Xem logs: nếu Binance bị giới hạn tại máy chủ GitHub thì job sẽ báo lỗi, dữ liệu cũ vẫn giữ nguyên, không phát tín hiệu giả.
5. Khi job thành công, mở `https://thecryptovietnam.com/ai-signal/` nếu custom domain GitHub Pages được trỏ đúng, hoặc URL GitHub Pages của repository; kiểm tra biểu tượng dữ liệu/giờ quét.
6. Tuỳ chọn Telegram: tạo bot qua @BotFather, nhập **Settings → Secrets and variables → Actions → New repository secret** hai khóa `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`. Không đưa bí mật vào mã nguồn.

### Lưu ý vận hành
- Có thể lưu website trên Cloudflare Pages/Netlify, nhưng workflow này deploy chính thức qua GitHub Pages. Để đồng bộ dữ liệu trên Cloudflare/Netlify cần bảo đảm mỗi lần JSON thay đổi thì nhà cung cấp nhận được bản build mới. GitHub Pages là đường triển khai tham chiếu được thiết lập sẵn.
- Repo công khai có thể chứa `sent.json` (chỉ là khóa chống trùng, không có token/chat ID). Khi bật Telegram, nên thử nghiệm trong nhóm riêng và theo dõi giới hạn gửi.
- 15 phút là lịch yêu cầu, không phải SLA. Nếu không có lần quét mới trong 40 phút, giao diện báo dữ liệu cũ. Không dùng làm hệ thống giao dịch tự động.
- Backtest chỉ dùng dữ liệu giới hạn từ Binance, chưa tính funding, thanh lý và không chứng minh khả năng có lãi.
- Dữ liệu và kết quả chưa được kiểm tra trực tiếp trên Binance từ môi trường phát triển; kiểm chứng bắt đầu sau khi kích hoạt workflow.


## Trang chủ: bảng TCV AI Signal thu nhỏ
- Ô “CHỦ ĐỀ ĐÁNG QUAN TÂM” đã thay bằng TCV AI Signal; menu và trang `/ai-signal/` giữ nguyên.
- `tcv-mini-signal.js` tải chung `ai-signal/data/latest.json` với trang đầy đủ (không tạo tín hiệu mẫu). Hiển thị tối đa 3 tín hiệu LONG/SHORT theo nến đóng mới nhất; thiếu dữ liệu hoặc quá 40 phút sẽ chỉ thông báo trạng thái.
- Nếu chưa chạy GitHub Actions, trên trang chủ sẽ hiện “CHƯA CÓ DỮ LIỆU”, đúng với thực tế.
- Khi mở từ ổ đĩa bằng `file://`, browser có thể chặn fetch JSON. Hãy thử trong máy chủ HTTP (`py -m http.server 8000`) và mở `http://localhost:8000/`.
- Để xuất bản, đưa nội dung gói ZIP vào repository GitHub Pages hiện tại, giữ nguyên thư mục `.github`. Chưa thực hiện deploy hoặc xác nhận API Binance từ môi trường phát triển.
