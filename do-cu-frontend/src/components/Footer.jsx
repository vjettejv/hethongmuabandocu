export default function Footer() {
  return (
    <footer className="footer">
      <div className="container footer-inner">
        <div className="footer-left">
          <div className="footer-title">Chợ Đồ Cũ</div>
          <div className="footer-text">Nền tảng rao vặt đồ cũ: đăng tin nhanh, duyệt minh bạch, chat thuận tiện.</div>
        </div>
        <div className="footer-right">
          <div className="footer-meta">© {new Date().getFullYear()} DoCu</div>
        </div>
      </div>
    </footer>
  );
}
