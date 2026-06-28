import { Link } from 'react-router-dom';

function LogoMark() {
  return (
    <svg className="brand-mark" viewBox="0 0 40 40" role="img" aria-label="Chá»£ Äá»“ CÅ©">
      <defs>
        <linearGradient id="docu_grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0" stopColor="rgb(238,77,45)" />
          <stop offset="1" stopColor="rgb(215,58,28)" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width="40" height="40" rx="12" fill="url(#docu_grad)" />
      <path
        d="M23.3 10.5h-6.9c-1 0-1.9.4-2.6 1.1l-3.3 3.3c-1.5 1.5-1.5 3.8 0 5.3l6.8 6.8c1.5 1.5 3.8 1.5 5.3 0l6.8-6.8c.7-.7 1.1-1.6 1.1-2.6v-6.9c0-1.9-1.5-3.4-3.4-3.4Zm3.3 7.7c0 .4-.2.8-.5 1.1l-6.2 6.2c-.6.6-1.6.6-2.2 0l-6.2-6.2c-.6-.6-.6-1.6 0-2.2l3-3c.3-.3.7-.5 1.1-.5h6.3c.9 0 1.7.8 1.7 1.7v1.2Z"
        fill="rgba(255,255,255,0.92)"
      />
      <circle cx="24.9" cy="15.2" r="1.5" fill="rgba(15,23,42,0.22)" />
    </svg>
  );
}

export default function Navbar({ currentPath }) {
  const isActive = (prefix) => (prefix === '/' ? currentPath === '/' : currentPath.startsWith(prefix));

  return (
    <nav className="navbar">
      <Link to="/">
        <LogoMark />
      </Link>
    </nav>
  );
}