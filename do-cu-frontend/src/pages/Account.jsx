import { useEffect, useState } from 'react';
import api from '../services/api';
import Swal from 'sweetalert2';
import { useNavigate } from 'react-router-dom';

export default function Account() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState({ fullName: '', phone: '', address: '' });

  useEffect(() => {
    let mounted = true;
    api
      .get('/users/me')
      .then((res) => {
        const me = res.data?.data || res.data;
        if (!mounted) return;
        setForm({
          fullName: me?.fullName || '',
          phone: me?.phone || '',
          address: me?.address || ''
        });
      })
      .catch((err) => {
        console.error('Lỗi tải tài khoản:', err);
        if (err?.response?.status === 401 || err?.response?.status === 403) {
          localStorage.clear();
          Swal.fire('Hết phiên', 'Vui lòng đăng nhập lại để quản lý tài khoản.', 'info').then(() => navigate('/login'));
          return;
        }
        Swal.fire('Lỗi', err.response?.data?.message || 'Không thể tải thông tin tài khoản', 'error');
      })
      .finally(() => mounted && setLoading(false));

    return () => {
      mounted = false;
    };
  }, []);

  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.put('/users/me', form);
      Swal.fire('Thành công', 'Đã cập nhật thông tin tài khoản', 'success');
    } catch (err) {
      if (err?.response?.status === 401 || err?.response?.status === 403) {
        localStorage.clear();
        Swal.fire('Hết phiên', 'Vui lòng đăng nhập lại để cập nhật tài khoản.', 'info').then(() => navigate('/login'));
        return;
      }
      Swal.fire('Lỗi', err.response?.data?.message || 'Không thể cập nhật tài khoản', 'error');
    }
  };

  return (
    <div className="container">
      <div className="card card-pad" style={{ maxWidth: 720, margin: '0 auto' }}>
        <div className="toolbar">
          <div className="toolbar-grow">
            <h2 className="toolbar-title" style={{ margin: 0 }}>
              Tài khoản
            </h2>
            <div className="hint">Cập nhật tên hiển thị, số điện thoại và địa chỉ để giao dịch thuận tiện hơn.</div>
          </div>
          <button className="btn btn-ghost" type="button" onClick={() => navigate('/')}>
            Về trang chủ
          </button>
        </div>

        {loading ? (
          <div className="hint" style={{ padding: 10 }}>
            Đang tải...
          </div>
        ) : (
          <form onSubmit={submit} style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 10 }}>
            <div className="field">
              <div className="label">Tên hiển thị</div>
              <input
                className="input"
                type="text"
                value={form.fullName}
                placeholder="VD: Phạm Văn Đạt"
                onChange={(e) => setForm((s) => ({ ...s, fullName: e.target.value }))}
              />
            </div>

            <div className="field">
              <div className="label">Số điện thoại</div>
              <input
                className="input"
                type="text"
                value={form.phone}
                placeholder="VD: 09xxxxxxxx"
                onChange={(e) => setForm((s) => ({ ...s, phone: e.target.value }))}
              />
            </div>

            <div className="field">
              <div className="label">Địa chỉ</div>
              <input
                className="input"
                type="text"
                value={form.address}
                placeholder="VD: Hà Nội, Cầu Giấy..."
                onChange={(e) => setForm((s) => ({ ...s, address: e.target.value }))}
              />
            </div>

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 6 }}>
              <button className="btn btn-ghost" type="button" onClick={() => navigate(-1)}>
                Quay lại
              </button>
              <button className="btn btn-primary" type="submit">
                Lưu thay đổi
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

