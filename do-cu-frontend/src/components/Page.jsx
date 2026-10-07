export function ErrorNotice({ error }) {
    return error ? <p className="notice notice-error" role="alert">{error}</p> : null;
}

export default function Page({ title, children }) {
    return <div className="container"><h1 className="page-title">{title}</h1>{children}</div>;
}
