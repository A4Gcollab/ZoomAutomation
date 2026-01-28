
import { useEffect, useState, useRef } from 'react';
import { UserAPI } from './api';
import {
    CheckCircle, Clock, RefreshCcw, Layers, LogOut,
    Activity, ChevronDown, PenLine,
    LayoutGrid, List, Plus
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';

export default function Dashboard() {
    const navigate = useNavigate();
    const [stats, setStats] = useState({ completed: 0, pending: 0 });
    const [queue, setQueue] = useState<any[]>([]);
    const [history, setHistory] = useState<any[]>([]);
    const [logs, setLogs] = useState<any[]>([]);
    const [options, setOptions] = useState<{ teams: string[], playlists: string[] }>({ teams: [], playlists: [] });
    const [activeTab, setActiveTab] = useState<'queue' | 'history'>('queue');
    const logEndRef = useRef<HTMLDivElement>(null);
    const [user] = useState(() => JSON.parse(localStorage.getItem('user_data') || '{}'));

    // Edit State
    const [editingRow, setEditingRow] = useState<string | null>(null);
    const [editForm, setEditForm] = useState({ team: '', playlist: '' });
    const [inputMode, setInputMode] = useState({ team: false, playlist: false });
    const [loading, setLoading] = useState(false);

    const refreshData = async () => {
        try {
            const [s, q, h, l, o] = await Promise.all([
                UserAPI.getStats(),
                UserAPI.getQueue(),
                UserAPI.getHistory(),
                UserAPI.getLogs(),
                UserAPI.getOptions()
            ]);
            setStats(s);
            setQueue(q);
            setHistory(h);
            setLogs(l);
            setOptions(o);
        } catch (e) {
            console.error("Fetch Error");
        }
    };

    useEffect(() => {
        refreshData();
        const interval = setInterval(refreshData, 5000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        logEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    const handleApprove = async (id: string) => {
        if (!editForm.team || !editForm.playlist) {
            alert("Please set Team and Playlist first");
            return;
        }
        setLoading(true);
        try {
            await UserAPI.approve(id, editForm);
            setEditingRow(null);
            await refreshData();
            setInputMode({ team: false, playlist: false });
        } catch (e) {
            alert("Approval Failed");
        } finally {
            setLoading(false);
        }
    };

    const startEdit = (row: any) => {
        setEditingRow(row.zoom_id);
        const hasTeam = options.teams.includes(row.team);
        const hasPlaylist = options.playlists.includes(row.playlist);
        setInputMode({
            team: !!row.team && !hasTeam,
            playlist: !!row.playlist && !hasPlaylist
        });
        setEditForm({ team: row.team || '', playlist: row.playlist || '' });
    };

    return (
        <div className="min-h-screen bg-slate-50 text-slate-800 font-sans">
            {/* Minimal Header */}
            <header className="bg-white border-b border-slate-200 px-6 lg:px-12 py-5 flex items-center justify-between sticky top-0 z-50 shadow-sm/50 backdrop-blur-md bg-white/90">
                <div className="flex items-center gap-4">
                    <div className="h-10 w-10 bg-indigo-600 rounded-xl flex items-center justify-center text-white shadow-indigo-200 shadow-lg">
                        <LayoutGrid className="w-6 h-6" />
                    </div>
                    <div>
                        <h1 className="text-xl font-bold text-slate-900 leading-none">Zoom Automation</h1>
                        <div className="flex items-center gap-2 text-xs text-slate-500 mt-1">
                            <div className="h-2 w-2 rounded-full bg-emerald-500 shadow-emerald-200 shadow-md"></div>
                            <span className="font-medium">Connected as {user.name}</span>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <button onClick={() => UserAPI.sync()} className="btn-ghost flex items-center gap-2 text-sm font-medium">
                        <RefreshCcw className="w-4 h-4" />
                        Sync
                    </button>
                    <button onClick={() => { localStorage.clear(); navigate('/login'); }} className="btn-ghost text-red-500 hover:bg-red-50 hover:text-red-600">
                        <LogOut className="w-5 h-5" />
                    </button>
                </div>
            </header>

            <main className="w-full px-6 lg:px-12 py-8 space-y-8">
                {/* Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                    <div className="zen-card p-5 flex items-center gap-4 border-l-4 border-l-emerald-500">
                        <div className="h-12 w-12 rounded-full bg-emerald-50 flex items-center justify-center text-emerald-600">
                            <CheckCircle className="w-6 h-6" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-slate-900">{stats.completed}</p>
                            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Processed</p>
                        </div>
                    </div>
                    <div className="zen-card p-5 flex items-center gap-4 border-l-4 border-l-amber-500">
                        <div className="h-12 w-12 rounded-full bg-amber-50 flex items-center justify-center text-amber-600">
                            <Clock className="w-6 h-6" />
                        </div>
                        <div>
                            <p className="text-2xl font-bold text-slate-900">{stats.pending}</p>
                            <p className="text-xs font-medium text-slate-500 uppercase tracking-wider">Pending</p>
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-4 gap-8 items-start">
                    {/* Main List - Wider (3/4) */}
                    <div className="xl:col-span-3 zen-card overflow-hidden min-h-[600px] flex flex-col shadow-sm">
                        <div className="flex border-b border-slate-100 bg-slate-50/50">
                            <button
                                onClick={() => setActiveTab('queue')}
                                className={clsx("flex-1 py-4 text-sm font-semibold text-center hover:bg-slate-50 transition-colors border-b-2", activeTab === 'queue' ? "border-indigo-600 text-indigo-600" : "border-transparent text-slate-500")}
                            >
                                Approval Queue ({queue.length})
                            </button>
                            <button
                                onClick={() => setActiveTab('history')}
                                className={clsx("flex-1 py-4 text-sm font-semibold text-center hover:bg-slate-50 transition-colors border-b-2", activeTab === 'history' ? "border-emerald-500 text-emerald-600" : "border-transparent text-slate-500")}
                            >
                                History
                            </button>
                        </div>

                        <div className="flex-1 overflow-x-visible p-6">
                            {(activeTab === 'queue' ? queue : history).length === 0 ? (
                                <div className="flex flex-col items-center justify-center h-64 text-slate-400">
                                    <List className="w-12 h-12 mb-4 opacity-20" />
                                    <p>No items found.</p>
                                </div>
                            ) : (
                                <table className="w-full text-left text-sm">
                                    <thead className="text-xs text-slate-400 uppercase font-semibold">
                                        <tr>
                                            <th className="pb-4 pl-2">Meeting Details</th>
                                            <th className="pb-4">Configuration</th>
                                            <th className="pb-4 text-right pr-2">Action</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-100">
                                        {activeTab === 'queue' && queue.map((row) => (
                                            <tr key={row.zoom_id} className="group hover:bg-slate-50 transition-colors">
                                                <td className="py-4 pl-2 align-top">
                                                    <div className="font-semibold text-slate-800">{row.topic || "Untitled"}</div>
                                                    <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
                                                        <Clock className="w-3 h-3" />
                                                        {row.start_time?.substring(0, 16).replace('T', ' ')}
                                                    </div>
                                                </td>
                                                <td className="py-4 align-top w-[45%]">
                                                    {editingRow === row.zoom_id ? (
                                                        <div className="bg-white border border-indigo-200 shadow-lg rounded-xl p-4 space-y-4 relative z-10 animate-in fade-in zoom-in-95 duration-200">
                                                            {/* TEAM */}
                                                            <div className="space-y-1">
                                                                <label className="text-label flex justify-between">
                                                                    Team
                                                                    {inputMode.team && <button onClick={() => setInputMode(p => ({ ...p, team: false }))} className="text-indigo-600 hover:underline text-[10px]">Select List</button>}
                                                                </label>
                                                                {inputMode.team ? (
                                                                    <input autoFocus value={editForm.team} onChange={e => setEditForm({ ...editForm, team: e.target.value })} className="zen-input" placeholder="Enter Team Name..." />
                                                                ) : (
                                                                    <div className="relative">
                                                                        <select
                                                                            value={editForm.team} onChange={e => {
                                                                                if (e.target.value === '__NEW__') { setInputMode(p => ({ ...p, team: true })); setEditForm(p => ({ ...p, team: '' })); }
                                                                                else setEditForm(p => ({ ...p, team: e.target.value }));
                                                                            }}
                                                                            className="zen-input appearance-none cursor-pointer"
                                                                        >
                                                                            <option value="" disabled>Select Team...</option>
                                                                            {options.teams.map(t => <option key={t} value={t}>{t}</option>)}
                                                                            <option value="__NEW__" className="text-indigo-600 font-bold">+ Create New</option>
                                                                        </select>
                                                                        <ChevronDown className="absolute right-3 top-2.5 w-4 h-4 text-slate-400 pointer-events-none" />
                                                                    </div>
                                                                )}
                                                            </div>

                                                            {/* PLAYLIST */}
                                                            <div className="space-y-1">
                                                                <label className="text-label flex justify-between">
                                                                    Playlist
                                                                    {inputMode.playlist && <button onClick={() => setInputMode(p => ({ ...p, playlist: false }))} className="text-indigo-600 hover:underline text-[10px]">Select List</button>}
                                                                </label>
                                                                {inputMode.playlist ? (
                                                                    <input value={editForm.playlist} onChange={e => setEditForm({ ...editForm, playlist: e.target.value })} className="zen-input" placeholder="Enter Playlist..." />
                                                                ) : (
                                                                    <div className="relative">
                                                                        <select
                                                                            value={editForm.playlist} onChange={e => {
                                                                                if (e.target.value === '__NEW__') { setInputMode(p => ({ ...p, playlist: true })); setEditForm(p => ({ ...p, playlist: '' })); }
                                                                                else setEditForm(p => ({ ...p, playlist: e.target.value }));
                                                                            }}
                                                                            className="zen-input appearance-none cursor-pointer"
                                                                        >
                                                                            <option value="" disabled>Select Playlist...</option>
                                                                            {options.playlists.map(p => <option key={p} value={p}>{p}</option>)}
                                                                            <option value="__NEW__" className="text-indigo-600 font-bold">+ Create New</option>
                                                                        </select>
                                                                        <ChevronDown className="absolute right-3 top-2.5 w-4 h-4 text-slate-400 pointer-events-none" />
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    ) : (
                                                        <div onClick={() => startEdit(row)} className="group/edit cursor-pointer p-2 rounded-lg hover:bg-slate-100 -ml-2 transition-colors">
                                                            {row.team ? (
                                                                <div className="space-y-1">
                                                                    <div className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
                                                                        {row.team}
                                                                    </div>
                                                                    <div className="text-xs text-slate-500 flex items-center gap-1.5">
                                                                        <Layers className="w-3 h-3 text-slate-400" />
                                                                        {row.playlist}
                                                                    </div>
                                                                </div>
                                                            ) : (
                                                                <div className="flex items-center gap-2 text-xs text-indigo-600 font-medium">
                                                                    <Plus className="w-4 h-4 bg-indigo-50 rounded-full p-0.5" />
                                                                    Configure
                                                                </div>
                                                            )}
                                                        </div>
                                                    )}
                                                </td>
                                                <td className="py-4 pr-2 align-top text-right">
                                                    {editingRow === row.zoom_id ? (
                                                        <button onClick={() => handleApprove(row.zoom_id)} disabled={loading} className="btn-primary text-xs w-full mt-8">
                                                            {loading ? '...' : 'Save'}
                                                        </button>
                                                    ) : (
                                                        <button onClick={() => startEdit(row)} className="p-2 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors">
                                                            <PenLine className="w-4 h-4" />
                                                        </button>
                                                    )}
                                                </td>
                                            </tr>
                                        ))}

                                        {activeTab === 'history' && history.map(row => (
                                            <tr key={row.zoom_id} className="hover:bg-slate-50">
                                                <td className="py-4 pl-2">
                                                    <div className="font-medium text-slate-800">{row.topic}</div>
                                                    <div className="text-xs text-slate-500">{row.start_time?.substring(0, 10)}</div>
                                                </td>
                                                <td className="py-4">
                                                    <div className="flex items-center gap-2">
                                                        <span className={clsx("text-xs px-2 py-0.5 rounded font-bold", row.status === 'COMPLETED' ? "bg-emerald-100 text-emerald-700" : "bg-slate-100 text-slate-600")}>
                                                            {row.status}
                                                        </span>
                                                        <span className="text-xs text-slate-400">by {row.approved_by}</span>
                                                    </div>
                                                </td>
                                                <td className="py-4 text-right pr-2 text-xs text-slate-500">
                                                    <div>{row.team}</div>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>

                    {/* Logs - Narrower (1/4) */}
                    <div className="xl:col-span-1 zen-card h-[600px] flex flex-col overflow-hidden bg-slate-900 border-slate-900 text-slate-300 shadow-xl">
                        <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-950/50 backdrop-blur">
                            <h2 className="text-sm font-semibold text-white flex items-center gap-2">
                                <Activity className="w-4 h-4 text-emerald-500" /> System Logs
                            </h2>
                        </div>
                        <div className="flex-1 overflow-y-auto p-4 space-y-2 font-mono text-xs">
                            {logs.length === 0 && <div className="text-slate-600 text-center mt-10">Use the system...</div>}
                            {logs.map(log => (
                                <div key={log.id} className="break-words">
                                    <span className="text-slate-500 mr-2">[{log.timestamp?.substring(11, 19)}]</span>
                                    <span className={clsx("font-bold mr-2", log.level === 'ERROR' ? "text-red-400" : "text-blue-400")}>{log.level}</span>
                                    <span className="text-slate-300">{log.message}</span>
                                </div>
                            ))}
                            <div ref={logEndRef}></div>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    );
}
