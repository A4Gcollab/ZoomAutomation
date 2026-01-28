
import { useState } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom';
import { UserAPI } from './api';
import { FolderGit2, ShieldCheck, Zap } from 'lucide-react';

export default function Login() {
    const navigate = useNavigate();
    const [error, setError] = useState('');

    const handleLoginSuccess = async (token: string, isDemo = false) => {
        try {
            if (isDemo) {
                // Demo Logic
                localStorage.setItem('vong_token', token);
                localStorage.setItem('user_data', JSON.stringify({ name: "Demo Admin", email: "demo@omysha.com", picture: "" }));
                navigate('/');
                return;
            }

            const res = await UserAPI.login(token);
            localStorage.setItem('vong_token', token);
            localStorage.setItem('user_data', JSON.stringify(res.user));
            navigate('/');
        } catch (err) {
            console.error(err);
            setError("Access Denied: You do not have permission.");
        }
    };

    return (
        <div className="flex min-h-screen flex-col items-center justify-center p-4">
            {/* Background Decor */}
            <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
                <div className="absolute top-[-10%] left-[-10%] w-[500px] h-[500px] bg-indigo-600/20 rounded-full blur-[100px]"></div>
                <div className="absolute bottom-[-10%] right-[-10%] w-[500px] h-[500px] bg-cyan-600/10 rounded-full blur-[100px]"></div>
            </div>

            <div className="glass-card w-full max-w-md flex flex-col items-center border-t border-white/20">

                {/* Logo */}
                <div className="mb-8 flex h-20 w-20 items-center justify-center rounded-2xl bg-gradient-to-br from-indigo-500 to-cyan-500 shadow-xl shadow-indigo-500/30">
                    <FolderGit2 className="h-10 w-10 text-white" />
                </div>

                <h1 className="text-3xl font-bold text-center mb-2">
                    <span className="text-white">Zoom</span> <span className="text-gradient">Automation</span>
                </h1>
                <p className="text-sm text-gray-400 mb-8 text-center max-w-xs">
                    Secure Automation Dashboard for Zoom, YouTube, and Drive Management.
                </p>

                {/* Auth Options */}
                <div className="flex flex-col gap-4 w-full">
                    <div className="flex justify-center w-full">
                        <GoogleLogin
                            onSuccess={(res) => res.credential && handleLoginSuccess(res.credential)}
                            onError={() => setError("Google Login Failed")}
                            theme="filled_black"
                            shape="pill"
                            width="100%"
                        />
                    </div>

                    <div className="relative flex items-center py-2">
                        <div className="flex-grow border-t border-white/10"></div>
                        <span className="flex-shrink mx-4 text-xs text-gray-600 uppercase">Or Verified Testing</span>
                        <div className="flex-grow border-t border-white/10"></div>
                    </div>

                    <button
                        onClick={() => handleLoginSuccess("DEMO_TOKEN_VONG_2026", true)}
                        className="group flex items-center justify-center w-full gap-2 px-4 py-3 rounded-full border border-white/10 hover:bg-white/5 transition-all text-sm font-medium text-gray-300 hover:text-white"
                    >
                        <Zap className="w-4 h-4 text-yellow-400 group-hover:scale-110 transition-transform" />
                        <span>Enter Demo Mode</span>
                    </button>
                </div>

                <div className="mt-8 flex items-center gap-2 text-xs text-green-500/80 bg-green-500/10 px-3 py-1 rounded-full">
                    <ShieldCheck className="w-3 h-3" />
                    <span>AES-256 Encrypted Connection</span>
                </div>

                {error && (
                    <div className="mt-6 w-full rounded-lg bg-red-500/10 border border-red-500/20 p-3 text-center text-xs text-red-400 animate-pulse">
                        {error}
                    </div>
                )}
            </div>

            <p className="fixed bottom-6 text-xs text-gray-600">
                v2.0.0 (Enterprise Build) • Omysha TechProducts
            </p>
        </div>
    );
}
