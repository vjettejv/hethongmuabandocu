import test from 'node:test';
import assert from 'node:assert/strict';
import { listData, errorMessage, mergeMessage, imageSource, safeReturnPath, formatPrice } from '../src/services/contracts.js';
import { getSession, saveSession, clearSession } from '../src/services/session.js';

test('Post/Favorite raw arrays and Message/Admin data envelopes remain supported', () => {
    const rows = [{ id: 12 }];
    assert.equal(listData({ data: rows }), rows);
    assert.equal(listData({ data: { data: rows } }), rows);
    assert.throws(() => listData({ data: { error: 'Invalid response' } }));
});
test('failed requests give readable errors without exposing server bodies', () => {
    assert.match(errorMessage({ response: { status: 401 } }), /đăng nhập/);
    assert.match(errorMessage({ response: { status: 500, data: { error: 'private database string' } } }), /Máy chủ/);
    assert.equal(errorMessage({ response: { status: 400, data: { message: 'Email đã được sử dụng' } } }), 'Email đã được sử dụng');
    assert.match(errorMessage({}), /Vui lòng thử lại/);
});
test('HTTP send and realtime echo/reconnect history do not duplicate messages', () => {
    const rows = [{ id: 7, content: 'owned synthetic message' }];
    assert.equal(mergeMessage(rows, { id: '7' }), rows);
    assert.equal(mergeMessage(rows, { id: 8 }).length, 2);
});
test('upload origins preserve same-origin and existing HTTP images', () => {
    assert.equal(imageSource('/uploads/photo.png', 'http://localhost:3000'), 'http://localhost:3000/uploads/photo.png');
    assert.equal(imageSource('https://example.invalid/photo.png'), 'https://example.invalid/photo.png');
    assert.equal(imageSource('javascript:bad'), '');
    assert.equal(imageSource(undefined), '');
});
test('VND rendering retains API decimal cents without adding decimals to whole prices', () => {
    assert.equal(formatPrice(12345.67).replace(/\s/g, ''), '12.345,67₫');
    assert.equal(formatPrice(40000).replace(/\s/g, ''), '40.000₫');
    assert.equal(formatPrice(null), 'Liên hệ');
});
test('login return paths retain protected query destinations and reject external/loop paths', () => {
    assert.equal(safeReturnPath('/chat?to=12'), '/chat?to=12');
    for (const path of ['https://example.invalid', '//example.invalid', '/\\example.invalid', '/login', '/register?next=bad', undefined]) {
        assert.equal(safeReturnPath(path), '/');
    }
});

const memory = new Map();
globalThis.localStorage = { getItem: key => memory.get(key) ?? null, setItem: (key, value) => memory.set(key, value), removeItem: key => memory.delete(key) };
let events = 0;
globalThis.window = { dispatchEvent: () => { events++; } };
const token = claims => `header.${Buffer.from(JSON.stringify(claims)).toString('base64url')}.signature`;
const valid = { id: 4000, roleId: 1, exp: Math.floor(Date.now()/1000) + 300 };

test('successful login persists complete identity and notifies same-tab consumers', () => {
    memory.clear(); events = 0;
    const value = token(valid);
    saveSession({ token: value, user: { id: 4000, roleId: 1, username: 'synthetic' } });
    assert.equal(getSession().userId, 4000);
    assert.equal(getSession().isAuthenticated, true);
    assert.equal(memory.get('userRoleId'), '1');
    assert.equal(events, 1);
});
test('old token-only sessions recover identity from claims and ignore stale metadata', () => {
    memory.clear(); memory.set('token', token(valid)); memory.set('userId', '12'); memory.set('userRoleId', '2');
    assert.equal(getSession().userId, 4000);
    assert.equal(getSession().isAdmin, false);
});
test('expired and malformed tokens cannot enter protected pages', () => {
    for (const value of ['bad-token', token({ ...valid, exp: 1 }), token({ ...valid, id: null })]) {
        memory.set('token', value); assert.equal(getSession().isAuthenticated, false);
    }
});
test('mismatched login identity is rejected without persisting token', () => {
    memory.clear();
    assert.throws(() => saveSession({ token: token(valid), user: { id: 12, roleId: 1 } }));
    assert.equal(memory.has('token'), false);
});
test('admin role derives from claims; logout preserves unrelated site settings', () => {
    memory.clear(); memory.set('theme', 'owned setting');
    saveSession({ token: token({ ...valid, roleId: 2 }), user: { id: 4000, roleId: 2 } });
    assert.equal(getSession().isAdmin, true);
    clearSession();
    assert.equal(getSession().isAuthenticated, false);
    assert.equal(memory.get('theme'), 'owned setting');
    assert.equal(memory.has('token'), false);
});
