import { useEffect, useState } from 'react';
import { getSession, SESSION_EVENT } from '../services/session';

export default function useSession() {
    const [session, setSession] = useState(getSession);
    useEffect(() => {
        const update = () => setSession(getSession());
        window.addEventListener(SESSION_EVENT, update);
        window.addEventListener('storage', update);
        update();
        return () => {
            window.removeEventListener(SESSION_EVENT, update);
            window.removeEventListener('storage', update);
        };
    }, []);
    useEffect(() => {
        if (!session.expiresAt) return;
        const timer = setTimeout(() => setSession(getSession()), Math.min(session.expiresAt - Date.now() + 1, 2147483647));
        return () => clearTimeout(timer);
    }, [session.expiresAt]);
    return session;
}
