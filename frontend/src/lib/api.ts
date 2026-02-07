// API Client for Backend Communication - Hardened with retry logic
import { logger } from './logger';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

// Get auth token from localStorage
const getAuthToken = (): string | null => {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('auth_token');
};

// Retry helper with exponential backoff
async function withRetry<T>(
    fn: () => Promise<T>,
    retries: number = 2,
    initialDelay: number = 1000
): Promise<T> {
    let lastError: Error | null = null;
    for (let i = 0; i <= retries; i++) {
        try {
            return await fn();
        } catch (error: any) {
            lastError = error;
            // Don't retry auth errors or client errors (4xx)
            if (error.message?.includes('Unauthorized') || error.message?.includes('HTTP 4')) {
                throw error;
            }
            if (i < retries) {
                const delay = initialDelay * Math.pow(2, i);
                logger.warn(`API retry ${i + 1}/${retries} in ${delay}ms: ${error.message}`);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
    }
    throw lastError;
}

// API Request Helper with timeout
async function apiRequest<T>(
    endpoint: string,
    options: RequestInit = {},
    timeoutMs: number = 30000
): Promise<T> {
    const token = getAuthToken();

    const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...(token && { 'X-Token': token }),
        ...options.headers,
    };

    // Add timeout via AbortController
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, {
            ...options,
            headers,
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (response.status === 401) {
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
                errorData = { detail: 'Unknown error' };
            }

            let errorMessage = `HTTP ${response.status}`;
            if (errorData.detail) {
                errorMessage = typeof errorData.detail === 'string'
                    ? errorData.detail
                    : JSON.stringify(errorData.detail);
            }

            throw new Error(errorMessage);
        }

        return response.json();
    } catch (error: any) {
        clearTimeout(timeoutId);
        if (error.name === 'AbortError') {
            throw new Error(`Request timeout after ${timeoutMs}ms`);
        }
        throw error;
    }
}

// API Methods - all GET requests auto-retry on network errors
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
        return withRetry(() => apiRequest<{ status: string }>('/health'));
    },

    healthDetailed: async () => {
        return withRetry(() => apiRequest<any>('/health/detailed'));
    },

    // Stats
    getStats: async () => {
        return withRetry(() =>
            apiRequest<{ completed: number; pending: number; errors: number; processing: number; approved: number }>('/stats')
        );
    },

    // Queue
    getQueue: async () => {
        return withRetry(() => apiRequest<any[]>('/queue'));
    },

    // History
    getHistory: async (limit: number = 50) => {
        return withRetry(() => apiRequest<any[]>(`/history?limit=${limit}`));
    },

    // Options (Teams & Playlists)
    getOptions: async () => {
        return withRetry(() =>
            apiRequest<{ teams: string[]; playlists: string[] }>('/options')
        );
    },

    // Approve Recording - no retry (mutation)
    approveRecording: async (zoomId: string, team: string, playlist: string) => {
        return apiRequest<{ status: string }>(`/approve/${zoomId}`, {
            method: 'POST',
            body: JSON.stringify({ team, playlist }),
        });
    },

    // Logs
    getLogs: async (lines: number = 100, level: string = 'INFO') => {
        return withRetry(() =>
            apiRequest<{ logs: any[]; total: number }>(`/logs?lines=${lines}&level=${level}`)
        );
    },

    // Errors
    getErrors: async (lines: number = 50) => {
        return withRetry(() =>
            apiRequest<{ logs: any[] }>(`/errors?lines=${lines}`)
        );
    },

    // Service Control
    getServiceStatus: async () => {
        return withRetry(() =>
            apiRequest<{ status: string; running: boolean; uptime: number }>('/service/status')
        );
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
        }, 15000); // 15s timeout for restart
    },
};

// WebSocket Manager - more resilient with unlimited reconnects
export class WebSocketManager {
    private ws: WebSocket | null = null;
    private reconnectAttempts = 0;
    private maxReconnectAttempts = 999; // Essentially unlimited
    private listeners: Map<string, Set<Function>> = new Map();
    private reconnectTimeout: NodeJS.Timeout | null = null;

    connect() {
        if (this.ws?.readyState === WebSocket.OPEN) return;

        try {
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
                    // Silently ignore parse errors
                }
            };

            this.ws.onclose = () => {
                this.emit('disconnected', null);
                this.reconnect();
            };

            this.ws.onerror = () => {
                this.emit('error', null);
            };
        } catch (error) {
            // WebSocket constructor can throw
            this.reconnect();
        }
    }

    private reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            return;
        }

        this.reconnectAttempts++;
        // Cap at 60 seconds between reconnects
        const delay = Math.min(2000 * Math.pow(1.5, this.reconnectAttempts - 1), 60000);

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
            callbacks.forEach((cb) => {
                try {
                    cb(data);
                } catch (e) {
                    // Don't let listener errors crash the WS manager
                }
            });
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
