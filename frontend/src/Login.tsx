import { GoogleLogin, type CredentialResponse } from '@react-oauth/google';
import { UserAPI } from './api';
import { useNavigate } from 'react-router-dom';
import { Activity, Zap, Shield, Clock } from 'lucide-react';

export default function Login() {
    const navigate = useNavigate();

    const handleSuccess = async (credentialResponse: CredentialResponse) => {
        try {
            const token = credentialResponse.credential;
            if (!token) {
                alert('No credential received');
                return;
            }

            const data = await UserAPI.login(token);
            // Store the token (use returned one or original)
            localStorage.setItem('vong_token', data.token || token);
            localStorage.setItem('user_data', JSON.stringify(data.user));
            navigate('/dashboard');
        } catch (error: any) {
            alert(error.response?.data?.detail || 'Login failed');
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-indigo-900 to-slate-900 flex items-center justify-center p-4">
            {/* Background Pattern */}
            <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyI+PGRlZnM+PHBhdHRlcm4gaWQ9ImdyaWQiIHdpZHRoPSI2MCIgaGVpZ2h0PSI2MCIgcGF0dGVyblVuaXRzPSJ1c2VyU3BhY2VPblVzZSI+PHBhdGggZD0iTSAxMCAwIEwgMCAwIDAgMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0icmdiYSgyNTUsMjU1LDI1NSwwLjAzKSIgc3Ryb2tlLXdpZHRoPSIxIi8+PC9wYXR0ZXJuPjwvZGVmcz48cmVjdCB3aWR0aD0iMTAwJSIgaGVpZ2h0PSIxMDAlIiBmaWxsPSJ1cmwoI2dyaWQpIi8+PC9zdmc+')] opacity-40"></div>

            <div className="relative w-full max-w-md">
                {/* Main Card */}
                <div className="bg-white/10 backdrop-blur-xl rounded-2xl shadow-2xl border border-white/20 overflow-hidden">
                    {/* Header */}
                    <div className="bg-gradient-to-r from-indigo-600 to-purple-600 p-8 text-center">
                        <div className="inline-flex items-center justify-center w-16 h-16 bg-white/20 rounded-2xl mb-4 backdrop-blur-sm">
                            <Activity className="w-8 h-8 text-white" />
                        </div>
                        <h1 className="text-3xl font-bold text-white mb-2">YTZ Automation</h1>
                        <p className="text-indigo-100 text-sm">Streamline your workflow automation</p>
                    </div>

                    {/* Content */}
                    <div className="p-8">
                        {/* Features */}
                        <div className="space-y-3 mb-8">
                            <div className="flex items-center gap-3 text-white/90">
                                <div className="w-8 h-8 rounded-lg bg-indigo-500/20 flex items-center justify-center">
                                    <Zap className="w-4 h-4 text-indigo-400" />
                                </div>
                                <span className="text-sm">Automated recording processing</span>
                            </div>
                            <div className="flex items-center gap-3 text-white/90">
                                <div className="w-8 h-8 rounded-lg bg-purple-500/20 flex items-center justify-center">
                                    <Shield className="w-4 h-4 text-purple-400" />
                                </div>
                                <span className="text-sm">Secure Google authentication</span>
                            </div>
                            <div className="flex items-center gap-3 text-white/90">
                                <div className="w-8 h-8 rounded-lg bg-blue-500/20 flex items-center justify-center">
                                    <Clock className="w-4 h-4 text-blue-400" />
                                </div>
                                <span className="text-sm">Real-time status monitoring</span>
                            </div>
                        </div>

                        {/* Login Button */}
                        <div className="bg-white rounded-xl p-6 shadow-lg">
                            <p className="text-center text-sm text-gray-600 mb-4 font-medium">
                                Sign in to continue
                            </p>
                            <div className="flex flex-col gap-3 justify-center">
                                <GoogleLogin
                                    onSuccess={handleSuccess}
                                    onError={() => alert('Login Failed')}
                                    useOneTap={false}
                                    theme="filled_blue"
                                    size="large"
                                    text="signin_with"
                                    shape="rectangular"
                                />
                            </div>
                        </div>

                        {/* Footer Note */}
                        <p className="text-center text-xs text-white/60 mt-6">
                            Authorized users only • Secure access
                        </p>
                    </div>
                </div>

                {/* Bottom Glow Effect */}
                <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 w-3/4 h-8 bg-indigo-500/30 blur-2xl rounded-full"></div>
            </div>
        </div>
    );
}
