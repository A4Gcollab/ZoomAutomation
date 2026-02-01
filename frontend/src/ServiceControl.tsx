// Service Management Component for Frontend
import { useState, useEffect } from 'react';
import { UserAPI } from './api';

interface ServiceHealth {
    status: string;
    running: boolean;
    last_heartbeat: string | null;
    uptime: number;
    last_cycle: string | null;
    error_count: number;
}

export function ServiceControl() {
    const [health, setHealth] = useState<ServiceHealth | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const fetchHealth = async () => {
        try {
            const data = await UserAPI.getServiceHealth();
            setHealth(data);
            setError(null);
        } catch (err: any) {
            setError(err.message || 'Failed to fetch service health');
        }
    };

    useEffect(() => {
        fetchHealth();
        const interval = setInterval(fetchHealth, 5000); // Poll every 5 seconds
        return () => clearInterval(interval);
    }, []);

    const handleStart = async () => {
        setLoading(true);
        try {
            await UserAPI.startService();
            await fetchHealth();
        } catch (err: any) {
            setError(err.message || 'Failed to start service');
        } finally {
            setLoading(false);
        }
    };

    const handleStop = async () => {
        setLoading(true);
        try {
            await UserAPI.stopService();
            await fetchHealth();
        } catch (err: any) {
            setError(err.message || 'Failed to stop service');
        } finally {
            setLoading(false);
        }
    };

    const handleRestart = async () => {
        setLoading(true);
        try {
            await UserAPI.restartService();
            await fetchHealth();
        } catch (err: any) {
            setError(err.message || 'Failed to restart service');
        } finally {
            setLoading(false);
        }
    };

    const formatUptime = (seconds: number) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        return `${hours}h ${minutes}m`;
    };

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'running': return 'bg-green-500';
            case 'stopped': return 'bg-gray-500';
            case 'error': return 'bg-red-500';
            default: return 'bg-yellow-500';
        }
    };

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-bold mb-4">Background Service</h2>

            {error && (
                <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
                    {error}
                </div>
            )}

            {health && (
                <div className="space-y-4">
                    {/* Status Indicator */}
                    <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${getStatusColor(health.status)}`}></div>
                        <span className="font-medium capitalize">{health.status}</span>
                        {health.running && health.uptime > 0 && (
                            <span className="text-sm text-gray-500">
                                Uptime: {formatUptime(health.uptime)}
                            </span>
                        )}
                    </div>

                    {/* Metrics */}
                    {health.running && (
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <div className="text-gray-500">Last Heartbeat</div>
                                <div className="font-medium">
                                    {health.last_heartbeat
                                        ? new Date(health.last_heartbeat).toLocaleTimeString()
                                        : 'N/A'}
                                </div>
                            </div>
                            <div>
                                <div className="text-gray-500">Error Count</div>
                                <div className="font-medium">{health.error_count}</div>
                            </div>
                        </div>
                    )}

                    {/* Control Buttons */}
                    <div className="flex gap-2 pt-4 border-t">
                        {!health.running ? (
                            <button
                                onClick={handleStart}
                                disabled={loading}
                                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 disabled:opacity-50"
                            >
                                {loading ? 'Starting...' : 'Start Service'}
                            </button>
                        ) : (
                            <>
                                <button
                                    onClick={handleStop}
                                    disabled={loading}
                                    className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
                                >
                                    {loading ? 'Stopping...' : 'Stop'}
                                </button>
                                <button
                                    onClick={handleRestart}
                                    disabled={loading}
                                    className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                                >
                                    {loading ? 'Restarting...' : 'Restart'}
                                </button>
                            </>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
