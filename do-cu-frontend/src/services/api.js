// File: src/services/api.js
import axios from 'axios';
import { getSession, clearSession } from './session';

const apiBaseUrl = import.meta.env?.VITE_API_URL || '';

const api = axios.create({
    baseURL: apiBaseUrl,
    timeout: 45000,
});

export const serverOrigin = apiBaseUrl || '';

api.interceptors.request.use(
    (config) => {
        const token = getSession().token;
        if (token && !/^\/auth\/(login|register|verify-otp)$/.test(config.url)) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

api.interceptors.response.use(response => response, error => {
    const authorization = error.config?.headers?.Authorization;
    if (error.response?.status === 401 && authorization && authorization === `Bearer ${getSession().token}`) clearSession();
    return Promise.reject(error);
});

export default api;
