import { useState, useEffect } from 'react';

function Account() {
    const [user, setUser] = useState(null);
    useEffect(() => {
        // Load user info
    }, []);
    return (
        <div>Account Component</div>
    );
}
export default Account;