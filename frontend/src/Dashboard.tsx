import { useEffect, useState } from 'react';
import { UserAPI } from './api';
import { useNavigate } from 'react-router-dom';
import { LogOut, Activity, CheckCircle, Clock, AlertCircle, RefreshCw, Play, Square, RotateCw, ExternalLink } from 'lucide-react';
import { notify } from './notifications';

interface Stats {
    completed: number;
    pending: number;
}

interface Recording {
    zoom_id: string;
    topic: string;
    start_time: string;
    status: string;
    team?: string;
    playlist?: string;
    youtube_url?: string;
    drive_url?: string;
    account_name?: string;
}

interface LogEntry {
    timestamp: string;
    level: string;
    logger: string;
    message: string;
}

interface ServiceHealth {
    status: string;
    running: boolean;
    uptime?: number;
    last_heartbeat?: string;
}

export default function Dashboard() {
    const navigate = useNavigate();
    const [stats, setStats] = useState<Stats>({ completed: 0, pending: 0 });
    const [queue, setQueue] = useState<Recording[]>([]);
    const [history, setHistory] = useState<Recording[]>([]);
    const [logs, setLogs] = useState<LogEntry[]>([]);
    const [errors, setErrors] = useState<LogEntry[]>([]);
    const [serviceHealth, setServiceHealth] = useState<ServiceHealth | null>(null);
    const [activeTab, setActiveTab] = useState<'queue' | 'history' | 'logs' | 'errors'>('queue');
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [user, setUser] = useState<any>(null);

    useEffect(() => {
        const userData = localStorage.getItem('user_data');
        if (userData) {
            setUser(JSON.parse(userData));
        }
        refreshData();
        const interval = setInterval(refreshData, 10000); // Refresh every 10s
        return () => clearInterval(interval);
    }, []);

    const refreshData = async () => {
        setIsRefreshing(true);
        try {
            const [statsData, queueData, historyData, logsData, errorsData, healthData] = await Promise.all([
                UserAPI.getStats(),
                UserAPI.getQueue(),
                UserAPI.getHistory(),
                UserAPI.getLogs(),
                UserAPI.getErrors(),
                UserAPI.getServiceHealth(),
            ]);

            setStats(statsData);
            setQueue(queueData);
            setHistory(historyData);
            setLogs(logsData.logs || []);
            setErrors(errorsData.logs || []);
            setServiceHealth(healthData);
        } catch (error: any) {
            if (error.response?.status === 401) {
                notify.error('Session expired. Please log in again.');
                localStorage.removeItem('vong_token');
                localStorage.removeItem('user_data');
                navigate('/');
                return;
            }
            notify.error('Failed to refresh data');
            console.error('Refresh error:', error);
        } finally {
            setIsRefreshing(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('vong_token');
        localStorage.removeItem('user_data');
        navigate('/');
    };

    const handleApprove = async (id: string, team: string, playlist: string) => {
        try {
            await UserAPI.approve(id, { team, playlist });
            notify.success('Recording approved!');
            refreshData();
        } catch (error) {
            notify.error('Failed to approve recording');
        }
    };

    const handleServiceAction = async (action: 'start' | 'stop' | 'restart') => {
        try {
            if (action === 'start') await UserAPI.startService();
            else if (action === 'stop') await UserAPI.stopService();
            else await UserAPI.restartService();

            notify.success(`Service ${action} initiated`);
            setTimeout(refreshData, 1000);
        } catch (error) {
            notify.error(`Failed to ${action} service`);
        }
    };

    const isAdmin = user?.role === 'admin';
    const errorCount = errors.length;

    return (
        <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
            {/* Header */}
            <header style={{
                background: 'var(--bg-surface)',
                borderBottom: '1px solid var(--border-subtle)',
                padding: '1rem 2rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <Activity size={28} color="var(--primary)" />
                    <h1 style={{ fontSize: '1.5rem', fontWeight: 700, letterSpacing: '-0.02em' }}>
                        YTZ AUTOMATION
                    </h1>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                    <button
                        onClick={refreshData}
                        className="btn-ghost"
                        disabled={isRefreshing}
                        style={{ padding: '0.5rem' }}
                    >
                        <RefreshCw size={18} className={isRefreshing ? 'animate-spin' : ''} />
                    </button>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <div style={{
                            width: 32,
                            height: 32,
                            borderRadius: '50%',
                            background: 'var(--bg-elevated)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 600,
                            fontSize: '0.875rem',
                        }}>
                            {user?.email?.[0]?.toUpperCase() || 'U'}
                        </div>
                        <div>
                            <div style={{ fontSize: '0.875rem', fontWeight: 500 }}>{user?.email}</div>
                            <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                {isAdmin ? 'Administrator' : 'User'}
                            </div>
                        </div>
                    </div>

                    <button onClick={handleLogout} className="btn-ghost" style={{ padding: '0.5rem' }}>
                        <LogOut size={18} />
                    </button>
                </div>
            </header>

            <div style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto' }}>
                {/* Service Control Panel */}
                <div className="industrial-card-elevated" style={{ marginBottom: '2rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <span
                                    className={`status-dot ${serviceHealth?.running ? 'status-dot-success' : 'status-dot-error'}`}
                                />
                                <div>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                        Background Service
                                    </div>
                                    <div style={{ fontSize: '1.25rem', fontWeight: 600 }}>
                                        {serviceHealth?.running ? 'RUNNING' : 'STOPPED'}
                                    </div>
                                </div>
                            </div>

                            {serviceHealth?.uptime !== undefined && (
                                <div style={{ paddingLeft: '1.5rem', borderLeft: '1px solid var(--border-subtle)' }}>
                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase' }}>
                                        Uptime
                                    </div>
                                    <div style={{ fontSize: '1rem', fontWeight: 500, fontFamily: 'JetBrains Mono' }}>
                                        {Math.floor(serviceHealth.uptime / 60)}m {serviceHealth.uptime % 60}s
                                    </div>
                                </div>
                            )}
                        </div>

                        <div style={{ display: 'flex', gap: '0.75rem' }}>
                            {!serviceHealth?.running && (
                                <button onClick={() => handleServiceAction('start')} className="btn-success">
                                    <Play size={16} />
                                    Start
                                </button>
                            )}
                            {serviceHealth?.running && (
                                <>
                                    <button onClick={() => handleServiceAction('stop')} className="btn-error">
                                        <Square size={16} />
                                        Stop
                                    </button>
                                    <button onClick={() => handleServiceAction('restart')} className="btn-primary">
                                        <RotateCw size={16} />
                                        Restart
                                    </button>
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {/* Stats Cards */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
                    <div className="industrial-card">
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                Pending
                            </span>
                            <Clock size={18} color="var(--warning)" />
                        </div>
                        <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'JetBrains Mono' }}>
                            {stats.pending}
                        </div>
                    </div>

                    <div className="industrial-card">
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                Completed
                            </span>
                            <CheckCircle size={18} color="var(--success)" />
                        </div>
                        <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'JetBrains Mono' }}>
                            {stats.completed}
                        </div>
                    </div>

                    <div className="industrial-card">
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                Errors
                            </span>
                            <AlertCircle size={18} color="var(--error)" />
                        </div>
                        <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'JetBrains Mono', color: errorCount > 0 ? 'var(--error)' : 'inherit' }}>
                            {errorCount}
                        </div>
                    </div>

                    <div className="industrial-card">
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                Total
                            </span>
                            <Activity size={18} color="var(--primary)" />
                        </div>
                        <div style={{ fontSize: '2rem', fontWeight: 700, fontFamily: 'JetBrains Mono' }}>
                            {stats.pending + stats.completed}
                        </div>
                    </div>
                </div>

                {/* Tabs */}
                <div style={{ borderBottom: '1px solid var(--border-subtle)', marginBottom: '1.5rem' }}>
                    <div style={{ display: 'flex', gap: '2rem' }}>
                        {(['queue', 'history', 'logs', 'errors'] as const).map(tab => (
                            <button
                                key={tab}
                                onClick={() => setActiveTab(tab)}
                                style={{
                                    padding: '0.75rem 0',
                                    fontSize: '0.875rem',
                                    fontWeight: 600,
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.05em',
                                    background: 'none',
                                    border: 'none',
                                    borderBottom: activeTab === tab ? '2px solid var(--primary)' : '2px solid transparent',
                                    color: activeTab === tab ? 'var(--primary)' : 'var(--text-secondary)',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                }}
                            >
                                {tab}
                                {tab === 'errors' && errorCount > 0 && (
                                    <span style={{
                                        marginLeft: '0.5rem',
                                        padding: '0.125rem 0.5rem',
                                        background: 'var(--error)',
                                        borderRadius: '9999px',
                                        fontSize: '0.75rem',
                                        fontWeight: 700,
                                    }}>
                                        {errorCount}
                                    </span>
                                )}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Tab Content */}
                {activeTab === 'queue' && (
                    <QueueTab queue={queue} onApprove={handleApprove} />
                )}

                {activeTab === 'history' && (
                    <HistoryTab history={history} />
                )}

                {activeTab === 'logs' && (
                    <LogsTab logs={logs} />
                )}

                {activeTab === 'errors' && (
                    <ErrorsTab errors={errors} />
                )}
            </div>
        </div>
    );
}

// Queue Tab Component
function QueueTab({ queue, onApprove }: { queue: Recording[], onApprove: (id: string, team: string, playlist: string) => void }) {
    const [editingId, setEditingId] = useState<string | null>(null);
    const [editTeam, setEditTeam] = useState('');
    const [editPlaylist, setEditPlaylist] = useState('');

    if (queue.length === 0) {
        return (
            <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
                <Clock size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
                <div style={{ fontSize: '1.125rem', fontWeight: 500 }}>No pending recordings</div>
                <div style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>All recordings have been processed</div>
            </div>
        );
    }

    return (
        <div className="table-container">
            <table className="table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Topic</th>
                        <th>Zoom ID</th>
                        <th>Team</th>
                        <th>Playlist</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    {queue.map(rec => (
                        <tr key={rec.zoom_id}>
                            <td className="text-mono">{rec.start_time.split('T')[0]}</td>
                            <td>{rec.topic}</td>
                            <td className="text-mono" style={{ color: 'var(--text-secondary)' }}>{rec.zoom_id}</td>
                            <td>
                                {editingId === rec.zoom_id ? (
                                    <input
                                        className="input"
                                        value={editTeam}
                                        onChange={(e) => setEditTeam(e.target.value)}
                                        placeholder="Team name"
                                        style={{ minWidth: '150px' }}
                                    />
                                ) : (
                                    <span>{rec.team || '-'}</span>
                                )}
                            </td>
                            <td>
                                {editingId === rec.zoom_id ? (
                                    <input
                                        className="input"
                                        value={editPlaylist}
                                        onChange={(e) => setEditPlaylist(e.target.value)}
                                        placeholder="Playlist name"
                                        style={{ minWidth: '150px' }}
                                    />
                                ) : (
                                    <span>{rec.playlist || '-'}</span>
                                )}
                            </td>
                            <td>
                                {editingId === rec.zoom_id ? (
                                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                                        <button
                                            className="btn-success"
                                            style={{ padding: '0.375rem 0.75rem', fontSize: '0.75rem' }}
                                            onClick={() => {
                                                onApprove(rec.zoom_id, editTeam, editPlaylist);
                                                setEditingId(null);
                                            }}
                                        >
                                            Approve
                                        </button>
                                        <button
                                            className="btn-ghost"
                                            style={{ padding: '0.375rem 0.75rem', fontSize: '0.75rem' }}
                                            onClick={() => setEditingId(null)}
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                ) : (
                                    <button
                                        className="btn-primary"
                                        style={{ padding: '0.375rem 0.75rem', fontSize: '0.75rem' }}
                                        onClick={() => {
                                            setEditingId(rec.zoom_id);
                                            setEditTeam(rec.team || '');
                                            setEditPlaylist(rec.playlist || '');
                                        }}
                                    >
                                        Edit & Approve
                                    </button>
                                )}
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// History Tab Component
function HistoryTab({ history }: { history: Recording[] }) {
    if (history.length === 0) {
        return (
            <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
                <CheckCircle size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
                <div style={{ fontSize: '1.125rem', fontWeight: 500 }}>No completed recordings</div>
            </div>
        );
    }

    return (
        <div className="table-container">
            <table className="table">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Topic</th>
                        <th>Status</th>
                        <th>Team</th>
                        <th>Links</th>
                    </tr>
                </thead>
                <tbody>
                    {history.map(rec => (
                        <tr key={rec.zoom_id}>
                            <td className="text-mono">{rec.start_time.split('T')[0]}</td>
                            <td>{rec.topic}</td>
                            <td>
                                <span className={`badge badge-${rec.status.toLowerCase()}`}>
                                    {rec.status}
                                </span>
                            </td>
                            <td>{rec.team || '-'}</td>
                            <td>
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                    {rec.youtube_url && (
                                        <a
                                            href={rec.youtube_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="btn-ghost"
                                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                                        >
                                            <ExternalLink size={14} />
                                            YouTube
                                        </a>
                                    )}
                                    {rec.drive_url && (
                                        <a
                                            href={rec.drive_url}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="btn-ghost"
                                            style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                                        >
                                            <ExternalLink size={14} />
                                            Drive
                                        </a>
                                    )}
                                </div>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

// Logs Tab Component
function LogsTab({ logs }: { logs: LogEntry[] }) {
    if (logs.length === 0) {
        return (
            <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
                <Activity size={48} style={{ margin: '0 auto 1rem', opacity: 0.5 }} />
                <div style={{ fontSize: '1.125rem', fontWeight: 500 }}>No logs available</div>
            </div>
        );
    }

    return (
        <div className="industrial-card" style={{ padding: 0 }}>
            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {logs.map((log, i) => (
                    <div
                        key={i}
                        style={{
                            padding: '0.75rem 1rem',
                            borderBottom: i < logs.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                            fontFamily: 'JetBrains Mono',
                            fontSize: '0.8125rem',
                            display: 'grid',
                            gridTemplateColumns: '140px 80px 100px 1fr',
                            gap: '1rem',
                            alignItems: 'start',
                        }}
                    >
                        <span style={{ color: 'var(--text-tertiary)' }}>{log.timestamp}</span>
                        <span className={`badge badge-${log.level.toLowerCase()}`} style={{ fontSize: '0.625rem', padding: '0.125rem 0.5rem' }}>
                            {log.level}
                        </span>
                        <span style={{ color: 'var(--text-secondary)' }}>{log.logger}</span>
                        <span style={{ color: 'var(--text-primary)', wordBreak: 'break-word' }}>{log.message}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

// Errors Tab Component
function ErrorsTab({ errors }: { errors: LogEntry[] }) {
    if (errors.length === 0) {
        return (
            <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)' }}>
                <CheckCircle size={48} style={{ margin: '0 auto 1rem', opacity: 0.5, color: 'var(--success)' }} />
                <div style={{ fontSize: '1.125rem', fontWeight: 500 }}>No errors found</div>
                <div style={{ fontSize: '0.875rem', marginTop: '0.5rem' }}>System is running smoothly</div>
            </div>
        );
    }

    return (
        <div className="industrial-card" style={{ padding: 0 }}>
            <div style={{ maxHeight: '600px', overflowY: 'auto' }}>
                {errors.map((error, i) => (
                    <div
                        key={i}
                        style={{
                            padding: '1rem',
                            borderBottom: i < errors.length - 1 ? '1px solid var(--border-subtle)' : 'none',
                            background: i % 2 === 0 ? 'var(--bg-surface)' : 'var(--bg-elevated)',
                        }}
                    >
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                            <AlertCircle size={16} color="var(--error)" />
                            <span style={{ fontFamily: 'JetBrains Mono', fontSize: '0.75rem', color: 'var(--text-tertiary)' }}>
                                {error.timestamp}
                            </span>
                            <span className="badge badge-error" style={{ fontSize: '0.625rem', padding: '0.125rem 0.5rem' }}>
                                {error.level}
                            </span>
                            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                {error.logger}
                            </span>
                        </div>
                        <div style={{
                            fontFamily: 'JetBrains Mono',
                            fontSize: '0.8125rem',
                            color: 'var(--error)',
                            whiteSpace: 'pre-wrap',
                            wordBreak: 'break-word',
                        }}>
                            {error.message}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
