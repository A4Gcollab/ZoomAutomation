// API Client for Backend Communication
import { logger } from './logger';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

// Get auth token from localStorage
const getAuthToken = (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
};

// API Request Helper
async function apiRequest<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const token = getAuthToken();

    // Debug logging for token
    if (!token) {
        logger.warn('API Request: No auth token found in localStorage');
    } else {
        // Log first few chars for security safe debugging
        logger.debug(`API Request: Found token (${token.substring(0, 10)}...)`);
    }

    const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...(token && { 'X-Token': token }),
        ...options.headers,
    };

    // Log headers (excluding sensitive full token)
    logger.debug(`API Request ${endpoint} Headers:`, {
        ...headers,
        'X-Token': token ? '(present)' : '(missing)'
    });

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        // Token expired or invalid
        if (typeof window !== 'undefined') {
            localStorage.removeItem('auth_token');
            window.location.href = '/login';
        }
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        let errorData;
        try {
            errorData = await response.json();
        } catch (e) {
            errorData = { detail: 'Unknown error (failed to parse JSON)' };
        }

        logger.error('API Error Response:', response.status, errorData);

        let errorMessage = `HTTP ${response.status}`;
        if (errorData.detail) {
            if (typeof errorData.detail === 'string') {
                errorMessage = errorData.detail;
            } else {
                // Handle Pydantic validation errors (array of objects)
                errorMessage = JSON.stringify(errorData.detail);
            }
        }

        throw new Error(errorMessage);
    }

    return response.json();
}

// API Methods
export const api = {
    // Auth
    login: async (googleToken: string) => {
        return apiRequest<{ token: string; user: any }>('/auth/login', {
            method: 'POST',
            body: JSON.stringify({ token: googleToken }),
        });
    },

    // Health
    health: async () => {
        return apiRequest<{ status: string }>('/health');
    },

    healthDetailed: async () => {
        return apiRequest<any>('/health/detailed');
    },

    // Stats
    getStats: async () => {
        return apiRequest<{ completed: number; pending: number }>('/stats');
    },

    // Queue
    getQueue: async () => {
        return apiRequest<any[]>('/queue');
    },

    // History
    getHistory: async (limit: number = 50) => {
        return apiRequest<any[]>(`/history?limit=${limit}`);
    },

    // Options (Teams & Playlists)
    getOptions: async () => {
        return apiRequest<{ teams: string[]; playlists: string[] }>('/options');
    },

    // Approve Recording
    approveRecording: async (zoomId: string, team: string, playlist: string) => {
        return apiRequest<{ status: string }>(`/approve/${zoomId}`, {
            method: 'POST',
            body: JSON.stringify({ team, playlist }),
        });
    },

    // Logs
    getLogs: async (lines: number = 100, level: string = 'INFO') => {
        return apiRequest<{ logs: any[]; total: number }>(`/logs?lines=${lines}&level=${level}`);
    },

    // Errors
    getErrors: async (lines: number = 50) => {
        return apiRequest<{ logs: any[] }>(`/errors?lines=${lines}`);
    },

    // Service Control
    getServiceStatus: async () => {
        return apiRequest<{ status: string; running: boolean; uptime: number }>('/service/status');
    },

    startService: async () => {
        return apiRequest<{ success: boolean; message: string }>('/service/start', {
            method: 'POST',
        });
    },

    stopService: async () => {
        return apiRequest<{ success: boolean; message: string }>('/service/stop', {
            method: 'POST',
        });
    },

    restartService: async () => {
        return apiRequest<{ success: boolean; message: string }>('/service/restart', {
            method: 'POST',
        });
    },
};

// WebSocket Manager
export class WebSocketManager {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 5;
    private listeners: Map<string, Set<Function>> = new Map();
    private reconnectTimeout: NodeJS.Timeout | null = null;

    connect() {
        if (this.ws?.readyState === WebSocket.OPEN) return;

        this.ws = new WebSocket(WS_URL);

        this.ws.onopen = () => {
            logger.info('WebSocket connected');
            this.reconnectAttempts = 0;
            this.emit('connected', null);
        };

        this.ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.emit(data.type, data);
            } catch (error) {
                logger.error('WebSocket message parse error:', error);
            }
        };

        this.ws.onclose = () => {
            logger.info('WebSocket disconnected');
            this.emit('disconnected', null);
            this.reconnect();
        };

        this.ws.onerror = (error) => {
            logger.error('WebSocket error:', error);
            this.emit('error', error);
        };
    }

    private reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            logger.error('Max reconnection attempts reached');
            this.emit('max_reconnect_reached', null);
            return;
        }

        this.reconnectAttempts++;
        const delay = Math.min(2000 * this.reconnectAttempts, 32000);

        logger.info(`Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

        this.reconnectTimeout = setTimeout(() => {
            this.connect();
        }, delay);
    }

    on(event: string, callback: Function) {
        if (!this.listeners.has(event)) {
            this.listeners.set(event, new Set());
        }
        this.listeners.get(event)!.add(callback);
    }

    off(event: string, callback: Function) {
        const callbacks = this.listeners.get(event);
        if (callbacks) {
            callbacks.delete(callback);
        }
    }

    private emit(event: string, data: any) {
        const callbacks = this.listeners.get(event);
        if (callbacks) {
            callbacks.forEach((cb) => cb(data));
        }
    }

    disconnect() {
        if (this.reconnectTimeout) {
            clearTimeout(this.reconnectTimeout);
        }
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }

    send(data: any) {
        if (this.ws?.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }
}

export const wsManager = new WebSocketManager();
