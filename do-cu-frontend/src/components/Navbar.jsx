import { Link, useNavigate } from 'react-router-dom';
import { useEffect, useState, useRef } from 'react';
import Swal from 'sweetalert2';
import api from '../services/api';

function LogoMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 40 40" role="img" aria-label="Chợ Đồ Cũ">
      <defs>
        <linearGradient id="docu_grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="rgb(238,77,45)" />
          <stop offset="1" stopColor="rgb(215,58,28)" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="40" height="40" rx="12" fill="url(#docu_grad)" />
      {/* Simple "tag + arrow" mark */}
      <path
        d="M23.3 10.5h-6.9c-1 0-1.9.4-2.6 1.1l-3.3 3.3c-1.5 1.5-1.5 3.8 0 5.3l6.8 6.8c1.5 1.5 3.8 1.5 5.3 0l6.8-6.8c.7-.7 1.1-1.6 1.1-2.6v-6.9c0-1.9-1.5-3.4-3.4-3.4Zm3.3 7.7c0 .4-.2.8-.5 1.1l-6.2 6.2c-.6.6-1.6.6-2.2 0l-6.2-6.2c-.6-.6-.6-1.6 0-2.2l3-3c.3-.3.7-.5 1.1-.5h6.3c.9 0 1.7.8 1.7 1.7v1.2Z"
        fill="rgba(255,255,255,0.92)"
      />
      <circle cx="24.9" cy="15.2" r="1.5" fill="rgba(15,23,42,0.22)" />
    </svg>
  );
}

export default function Navbar({ session, currentPath, onLogout }) {
  const navigate = useNavigate();

  const isActive = (prefix) => (prefix === '/' ? currentPath === '/' : currentPath.startsWith(prefix));

  const confirmLogout = async () => {
    const result = await Swal.fire({
      title: 'Đăng xuất?',
      text: 'Bạn sẽ cần đăng nhập lại để tiếp tục mua bán.',
      icon: 'question',
      showCancelButton: true,
      confirmButtonText: 'Đăng xuất',
      cancelButtonText: 'Ở lại',
      confirmButtonColor: '#ef4444',
    });
    if (result.isConfirmed) onLogout();
  };

  // Notification State
  const [notifications, setNotifications] = useState([]);
  const [showNotifDropdown, setShowNotifDropdown] = useState(false);
  const notifRef = useRef(null);

  useEffect(() => {
    if (!session.isAuthenticated) return;
    
    // Fetch initial notifications
    api.get('/messages/notifications')
      .then(res => {
        setNotifications(res.data?.data || []);
      })
      .catch(err => console.error('Error fetching notifications:', err));

    // Listen for new notifications
    const handleNewNotif = (e) => {
      setNotifications(prev => [e.detail, ...prev]);
    };
    window.addEventListener('new_notification', handleNewNotif);

    // Click outside to close
    const handleClickOutside = (e) => {
      if (notifRef.current && !notifRef.current.contains(e.target)) {
        setShowNotifDropdown(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);

    return () => {
      window.removeEventListener('new_notification', handleNewNotif);
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [session.isAuthenticated]);

  const unreadCount = notifications.filter(n => !n.isRead).length;

  const handleMarkAllRead = () => {
    if (unreadCount === 0) return;
    api.put('/messages/notifications/read-all')
      .then(() => {
        setNotifications(prev => prev.map(n => ({ ...n, isRead: true })));
      })
      .catch(err => console.error(err));
  };

  return (
    <header className="topbar">
      <div className="container topbar-inner">
        <Link className="brand" to="/" aria-label="Về trang chủ">
          <LogoMark />
          <div className="brand-text">
            <div className="brand-name">Chợ Đồ Cũ</div>
            <div className="brand-sub">Mua bán nhanh, giá tốt</div>
          </div>
        </Link>

        <nav className="nav">
          <div className="nav-links">
            <Link className={isActive('/') ? 'nav-link active' : 'nav-link'} to="/">
              Trang chủ
            </Link>

            {session.isAuthenticated ? (
              <>
              {!session.isAdmin && (
                <>
                  <Link className={isActive('/create-post') ? 'nav-link active' : 'nav-link'} to="/create-post">
                    Đăng tin
                  </Link>
                  <Link className={isActive('/my-posts') ? 'nav-link active' : 'nav-link'} to="/my-posts">
                    Tin của tôi
                  </Link>
                  <Link className={isActive('/my-favorites') ? 'nav-link active' : 'nav-link'} to="/my-favorites">
                    Tin yêu thích
                  </Link>
                </>
              )}
              <Link className={isActive('/chat') ? 'nav-link active' : 'nav-link'} to="/chat">
                Chat
              </Link>
              {session.isAdmin && (
                <Link className={isActive('/admin') ? 'nav-link active' : 'nav-link'} to="/admin">
                  Quản trị
                </Link>
              )}
              </>
            ) : null}
          </div>

          {session.isAuthenticated ? (
            <div className="nav-actions">
              
              {/* Notification Bell */}
              <div className="notif-wrapper" ref={notifRef} style={{ position: 'relative', marginRight: '1rem' }}>
                <button 
                  className="btn btn-ghost" 
                  style={{ padding: '0.5rem', position: 'relative' }}
                  onClick={() => {
                    setShowNotifDropdown(!showNotifDropdown);
                    if (!showNotifDropdown && unreadCount > 0) handleMarkAllRead();
                  }}
                  aria-label="Thông báo"
                >
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path>
                    <path d="M13.73 21a2 2 0 0 1-3.46 0"></path>
                  </svg>
                  {unreadCount > 0 && (
                    <span style={{
                      position: 'absolute', top: '2px', right: '2px', background: '#ef4444',
                      color: 'white', fontSize: '10px', fontWeight: 'bold', padding: '2px 6px',
                      borderRadius: '10px', minWidth: '18px', textAlign: 'center'
                    }}>
                      {unreadCount > 9 ? '9+' : unreadCount}
                    </span>
                  )}
                </button>

                {/* Dropdown Menu */}
                {showNotifDropdown && (
                  <div className="notif-dropdown" style={{
                    position: 'absolute', top: '100%', right: '-10px', width: '320px',
                    background: 'white', borderRadius: '12px', boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                    border: '1px solid #e2e8f0', zIndex: 100, overflow: 'hidden', marginTop: '10px'
                  }}>
                    <div style={{ padding: '12px 16px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 600 }}>Thông báo</h3>
                      {unreadCount > 0 && (
                        <button onClick={handleMarkAllRead} style={{ background: 'none', border: 'none', color: '#3b82f6', fontSize: '12px', cursor: 'pointer' }}>Đánh dấu đã đọc</button>
                      )}
                    </div>
                    <div style={{ maxHeight: '350px', overflowY: 'auto' }}>
                      {notifications.length === 0 ? (
                        <div style={{ padding: '24px', textAlign: 'center', color: '#64748b', fontSize: '14px' }}>Chưa có thông báo nào.</div>
                      ) : (
                        notifications.map((n, i) => (
                          <div key={n.id || i} style={{
                            padding: '12px 16px', borderBottom: '1px solid #f1f5f9',
                            background: n.isRead ? 'transparent' : '#f0f9ff',
                            transition: 'background 0.2s', cursor: 'default'
                          }}>
                            <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '4px', color: '#0f172a' }}>{n.title}</div>
                            <div style={{ fontSize: '13px', color: '#475569', lineHeight: 1.4 }}>{n.message}</div>
                            <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '6px' }}>
                              {new Date(n.createdAt).toLocaleDateString('vi-VN', { hour: '2-digit', minute: '2-digit' })}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>

              <button className="user-chip" type="button" onClick={() => navigate('/account')} title="Tài khoản">
                <span className="user-avatar" aria-hidden="true">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                    <path
                      d="M12 12c2.76 0 5-2.24 5-5S14.76 2 12 2 7 4.24 7 7s2.24 5 5 5Z"
                      fill="rgba(255,255,255,0.92)"
                    />
                    <path
                      d="M4 20.25c0-3.73 3.58-6.75 8-6.75s8 3.02 8 6.75V22H4v-1.75Z"
                      fill="rgba(255,255,255,0.86)"
                    />
                  </svg>
                </span>
                <span className="user-label">Tài khoản</span>
              </button>
              <button className="btn btn-ghost" type="button" onClick={confirmLogout}>
                Đăng xuất
              </button>
            </div>
          ) : (
            <div className="nav-actions">
              <Link className={isActive('/login') ? 'btn btn-ghost' : 'btn btn-ghost'} to="/login">
                Đăng nhập
              </Link>
              <Link className={isActive('/register') ? 'btn btn-primary' : 'btn btn-primary'} to="/register">
                Đăng ký
              </Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

