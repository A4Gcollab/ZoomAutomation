import { GoogleLogin, type CredentialResponse } from '@react-oauth/google';
import { UserAPI } from './api';
import { Activity, Zap, Shield, Clock, Loader2 } from 'lucide-react';
import { useState } from 'react';

export default function Login() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSuccess = async (credentialResponse: CredentialResponse) => {
        console.log('Google Login Success:', credentialResponse);
        setIsLoading(true);
        setError(null);

        try {
            const token = credentialResponse.credential;
            if (!token) {
                throw new Error('No credential received from Google');
            }

            console.log('Sending token to backend...');
            const data = await UserAPI.login(token);
            console.log('Backend response:', data);

            // Store the token and user data
            localStorage.setItem('vong_token', data.token || token);
            localStorage.setItem('user_data', JSON.stringify(data.user));

            console.log('Navigating to dashboard...');
            // Force navigation
            window.location.href = '/dashboard';
        } catch (error: any) {
            console.error('Login error:', error);
            const errorMsg = error.response?.data?.detail || error.message || 'Login failed. Please try again.';
            setError(errorMsg);
            alert(errorMsg);
        } finally {
            setIsLoading(false);
        }
    };

    const handleError = () => {
        console.error('Google Login Error');
        setError('Google login failed. Please try again.');
        alert('Google login failed. Please try again.');
    };

    return (
        <div style={{ minHeight: '100vh', background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
            <div style={{ width: '100%', maxWidth: '420px' }}>
                {/* Main Card */}
                <div style={{ background: 'white', borderRadius: '16px', boxShadow: '0 20px 60px rgba(0,0,0,0.3)', overflow: 'hidden' }}>
                    {/* Header */}
                    <div style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', padding: '2rem', textAlign: 'center' }}>
                        <div style={{
                            width: 64,
                            height: 64,
                            margin: '0 auto 1rem',
                            background: 'rgba(255,255,255,0.2)',
                            borderRadius: '16px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            backdropFilter: 'blur(10px)',
                        }}>
                            <Activity size={32} color="white" />
                        </div>
                        <h1 style={{ fontSize: '1.875rem', fontWeight: 700, color: 'white', marginBottom: '0.5rem' }}>
                            YTZ Automation
                        </h1>
                        <p style={{ color: 'rgba(255,255,255,0.9)', fontSize: '0.875rem' }}>
                            Recording Management System
                        </p>
                    </div>

                    {/* Content */}
                    <div style={{ padding: '2rem' }}>
                        {/* Features */}
                        <div style={{ marginBottom: '2rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                                <div style={{ width: 36, height: 36, borderRadius: '8px', background: '#eef2ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <Zap size={18} color="#667eea" />
                                </div>
                                <span style={{ fontSize: '0.875rem', color: '#64748b' }}>Automated processing</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' }}>
                                <div style={{ width: 36, height: 36, borderRadius: '8px', background: '#f3e8ff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <Shield size={18} color="#764ba2" />
                                </div>
                                <span style={{ fontSize: '0.875rem', color: '#64748b' }}>Secure authentication</span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                                <div style={{ width: 36, height: 36, borderRadius: '8px', background: '#dbeafe', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                                    <Clock size={18} color="#3b82f6" />
                                </div>
                                <span style={{ fontSize: '0.875rem', color: '#64748b' }}>Real-time monitoring</span>
                            </div>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div style={{
                                padding: '0.75rem 1rem',
                                background: '#fee2e2',
                                border: '1px solid #fca5a5',
                                borderRadius: '8px',
                                marginBottom: '1rem',
                                fontSize: '0.875rem',
                                color: '#991b1b',
                            }}>
                                {error}
                            </div>
                        )}

                        {/* Login Button */}
                        <div style={{ background: '#f8fafc', borderRadius: '12px', padding: '1.5rem', border: '1px solid #e2e8f0' }}>
                            <p style={{ textAlign: 'center', fontSize: '0.875rem', color: '#64748b', marginBottom: '1rem', fontWeight: 500 }}>
                                Sign in to continue
                            </p>

                            {isLoading ? (
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '1rem' }}>
                                    <Loader2 size={24} color="#667eea" className="animate-spin" />
                                    <span style={{ marginLeft: '0.75rem', color: '#64748b' }}>Logging in...</span>
                                </div>
                            ) : (
                                <div style={{ display: 'flex', justifyContent: 'center' }}>
                                    <GoogleLogin
                                        onSuccess={handleSuccess}
                                        onError={handleError}
                                        useOneTap={false}
                                        theme="outline"
                                        size="large"
                                        text="signin_with"
                                        shape="rectangular"
                                        width="280"
                                    />
                                </div>
                            )}
                        </div>

                        {/* Footer Note */}
                        <p style={{ textAlign: 'center', fontSize: '0.75rem', color: '#94a3b8', marginTop: '1.5rem' }}>
                            Authorized users only • Secure access
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
