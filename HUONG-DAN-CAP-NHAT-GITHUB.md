# THE CRYPTO VIETNAM - Chuyển bộ quét Futures từ Binance sang Bybit V5

## Mục tiêu
Chỉ thay nguồn dữ liệu AI Signal + Market Radar (tránh HTTP 451 ở Binance Futures). Các bảng Spot, Market Pulse, TradingView và website vẫn giữ nguồn hiện tại.

## Tệp thay đổi
- scan.py: bộ chuyển đổi REST Bybit V5 với dữ liệu USDT Linear Perpetual, nến đã đóng, dữ liệu có kiểm tra
- .github/workflows/signal.yml: lịch quét + triển khai Pages (cập nhật và thay thế workflow đã tạo trên GitHub)
- tests/test_bybit_adapter.py: kiểm thử bộ chuyển dữ liệu API bằng mô phỏng cấu trúc JSON (KHÔNG phải kết quả truy cập Bybit thực)
- ai-signal/index.html, tcv-mini-signal.js, market-radar/index.html, market-radar/radar.js, index.html: thay các mô tả nguồn quét Futures cho đúng, không đổi nguồn bảng Spot

## Cách cập nhật
1. Trên GitHub repository THE CRYPTO VIETNAM, sao lưu nhánh hiện tại hoặc ghi nhớ commit gần nhất.
2. Có thể tải cả nội dung của ZIP WEBSITE-DA-CHUYEN-SANG-BYBIT lên repo (giải nén, giữ thư mục); hoặc chỉ tải các tệp trong ZIP PATCH.
3. Kiểm tra .github/workflows/signal.yml xuất hiện và đã thay phiên bản cũ.
4. Settings > Pages > Build and deployment > Source = GitHub Actions.
5. Settings > Actions > General > Workflow permissions > Read and write permissions nếu tổ chức cho phép.
6. Actions > TCV AI Signal - Futures Scanner and Site > Run workflow.
7. Mở job và xem bước Run tests, Scan Bybit public USDT perpetual market data, Commit updated data, Deploy THE CRYPTO VIETNAM.
8. Nếu HTTP 403/451 hoặc retCode khác 0, không dùng VPN/proxy để vượt hạn chế; kiểm tra điều kiện sử dụng hoặc đổi sang nguồn dữ liệu được phép.

Lưu ý: Chưa xác nhận API Bybit truy cập được từ GitHub Actions. Gói đã qua unittest offline; cần kiểm thử online. Không phải lời khuyên giao dịch.
