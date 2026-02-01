
import { useState, useEffect } from 'react';
import { UserAPI } from './api';
import { Activity, Loader } from 'lucide-react';

interface ServiceHealth {
    status: string;
    running: boolean;
    uptime?: number;
    error_count?: number;
}

export function ServiceStatus() {
    const [health, setHealth] = useState<ServiceHealth | null>(null);
    const [showControls, setShowControls] = useState(false);
    const [loading, setLoading] = useState(false);

    const fetchHealth = async () => {
        try {
            const data = await UserAPI.getServiceHealth();
            setHealth(data);
        } catch (err) {
            // Silent fail for non-admin users
        }
    };

    useEffect(() => {
        fetchHealth();
        const interval = setInterval(fetchHealth, 5000);
        return () => clearInterval(interval);
    }, []);

    const handleAction = async (action: 'start' | 'stop' | 'restart') => {
        setLoading(true);
        try {
            if (action === 'start') await UserAPI.startService();
            else if (action === 'stop') await UserAPI.stopService();
            else await UserAPI.restartService();
            await fetchHealth();
        } catch (err: any) {
            const msg = err.response?.data?.detail || err.message || `Failed to ${action} service`;
            alert(msg);
        } finally {
            setLoading(false);
            setShowControls(false);
        }
    };

    if (!health) {
        return (
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100">
                <div className="w-2 h-2 rounded-full bg-gray-300 animate-pulse"></div>
                <span className="text-xs text-slate-500">Connecting...</span>
            </div>
        );
    }

    const getStatusColor = () => {
        switch (health.status) {
            case 'running': return 'bg-green-500';
            case 'stopped': return 'bg-gray-400';
            case 'error': return 'bg-red-500';
            default: return 'bg-yellow-500';
        }
    };

    const formatUptime = (seconds: number) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        if (hours > 0) return `${hours}h ${minutes}m`;
        return `${minutes}m`;
    };

    return (
        <div className="relative flex items-center">
            {/* Status Indicator */}
            <button
                onClick={() => setShowControls(!showControls)}
                className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100 hover:bg-slate-200 transition-colors"
            >
                <div className={`w-2 h-2 rounded-full ${getStatusColor()} animate-pulse`}></div>
                <span className="text-xs font-medium text-slate-700 capitalize">{health.status}</span>
                {health.running && health.uptime && (
                    <span className="text-xs text-slate-500">• {formatUptime(health.uptime)}</span>
                )}
            </button>

            {/* Quick Start Button for All Users */}
            {!health.running && (
                <button
                    onClick={(e) => {
                        e.stopPropagation();
                        handleAction('start');
                    }}
                    disabled={loading}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-green-600 hover:bg-green-700 text-white text-xs font-medium transition-colors ml-2"
                >
                    {loading ? <Loader className="w-3 h-3 animate-spin" /> : 'Start Backend'}
                </button>
            )}

            {/* Dropdown Controls */}
            {showControls && (
                <>
                    <div
                        className="fixed inset-0 z-40"
                        onClick={() => setShowControls(false)}
                    ></div>
                    <div className="absolute right-0 mt-2 w-64 bg-white rounded-lg shadow-xl border border-slate-200 p-4 z-50">
                        <div className="flex items-center gap-2 mb-3 pb-3 border-b">
                            <Activity className="w-4 h-4 text-indigo-600" />
                            <span className="font-semibold text-sm">Service Control</span>
                        </div>

                        {/* Status Info */}
                        <div className="space-y-2 mb-4 text-xs">
                            <div className="flex justify-between">
                                <span className="text-slate-500">Status:</span>
                                <span className="font-medium capitalize">{health.status}</span>
                            </div>
                            {health.running && (
                                <>
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Uptime:</span>
                                        <span className="font-medium">{formatUptime(health.uptime || 0)}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span className="text-slate-500">Errors:</span>
                                        <span className="font-medium">{health.error_count || 0}</span>
                                    </div>
                                </>
                            )}
                        </div>

                        {/* Control Buttons */}
                        <div className="flex gap-2">
                            {!health.running ? (
                                <button
                                    onClick={() => handleAction('start')}
                                    disabled={loading}
                                    className="flex-1 px-3 py-2 bg-green-600 text-white text-xs font-medium rounded hover:bg-green-700 disabled:opacity-50 flex items-center justify-center gap-1"
                                >
                                    {loading ? <Loader className="w-3 h-3 animate-spin" /> : 'Start'}
                                </button>
                            ) : (
                                <>
                                    <button
                                        onClick={() => handleAction('stop')}
                                        disabled={loading}
                                        className="flex-1 px-3 py-2 bg-red-600 text-white text-xs font-medium rounded hover:bg-red-700 disabled:opacity-50"
                                    >
                                        Stop
                                    </button>
                                    <button
                                        onClick={() => handleAction('restart')}
                                        disabled={loading}
                                        className="flex-1 px-3 py-2 bg-blue-600 text-white text-xs font-medium rounded hover:bg-blue-700 disabled:opacity-50"
                                    >
                                        Restart
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
