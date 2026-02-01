
import axios from 'axios';

// Detect if we are running locally or on VPS (same host)
// If frontend is served by Nginx on port 80/3000 and backend on 8000
const API_URL = import.meta.env.PROD
    ? '/api' // Nginx proxy behavior
    : 'http://localhost:8000'; // Local dev

export const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Interceptor to add Token
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('vong_token');
    if (token) {
        config.headers['x-token'] = token;
    }
    return config;
});

export const UserAPI = {
    login: async (googleToken: string) => {
        const res = await api.post('/auth/login', { token: googleToken });
        return res.data;
    },
    getStats: async () => (await api.get('/stats')).data,
    getQueue: async () => (await api.get('/queue')).data,
    getHistory: async () => (await api.get('/history')).data,
    getOptions: async () => (await api.get('/options')).data,
    getLogs: async () => (await api.get('/logs')).data,
    approve: async (id: string, data: { team: string, playlist: string }) =>
        (await api.post(`/approve/${id}`, data)).data,
    sync: async () => (await api.post('/sync')).data,
    getSheetsUrl: async () => (await api.get('/sheets-url')).data,

    // Service Management
    getServiceHealth: async () => (await api.get('/service/health')).data,
    startService: async () => (await api.post('/service/start')).data,
    stopService: async () => (await api.post('/service/stop')).data,
    restartService: async () => (await api.post('/service/restart')).data,
};
