import { useState } from 'react';
import { UserAPI } from './api';
import { Activity, Zap, Shield, Clock, Loader2, ArrowRight } from 'lucide-react';

export default function Login() {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [useDemoMode, setUseDemoMode] = useState(false);

    // Demo mode login - bypass Google OAuth
    const handleDemoLogin = async () => {
        setIsLoading(true);
        setError(null);

        try {
            console.log('Using demo mode login...');
            const data = await UserAPI.login('DEMO_TOKEN_VONG_2026');
            console.log('Demo login successful:', data);

            localStorage.setItem('vong_token', data.token || 'DEMO_TOKEN_VONG_2026');
            localStorage.setItem('user_data', JSON.stringify(data.user));

            window.location.href = '/dashboard';
        } catch (error: any) {
            console.error('Demo login error:', error);
            setError('Demo login failed. Check if backend is running on port 8000.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: '2rem',
            fontFamily: 'Inter, sans-serif'
        }}>
            <div style={{ width: '100%', maxWidth: '440px' }}>
                {/* Main Card */}
                <div style={{
                    background: 'white',
                    borderRadius: '20px',
                    boxShadow: '0 25px 50px rgba(0,0,0,0.25)',
                    overflow: 'hidden'
                }}>
                    {/* Header */}
                    <div style={{
                        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                        padding: '3rem 2rem',
                        textAlign: 'center'
                    }}>
                        <div style={{
                            width: 80,
                            height: 80,
                            margin: '0 auto 1.5rem',
                            background: 'rgba(255,255,255,0.25)',
                            borderRadius: '20px',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            backdropFilter: 'blur(10px)',
                        }}>
                            <Activity size={40} color="white" strokeWidth={2.5} />
                        </div>
                        <h1 style={{
                            fontSize: '2.25rem',
                            fontWeight: 800,
                            color: 'white',
                            marginBottom: '0.5rem',
                            letterSpacing: '-0.02em'
                        }}>
                            YTZ Automation
                        </h1>
                        <p style={{
                            color: 'rgba(255,255,255,0.95)',
                            fontSize: '1rem',
                            fontWeight: 500
                        }}>
                            Recording Management System
                        </p>
                    </div>

                    {/* Content */}
                    <div style={{ padding: '2.5rem' }}>
                        {/* Features */}
                        <div style={{ marginBottom: '2rem' }}>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                                <div style={{
                                    width: 44,
                                    height: 44,
                                    borderRadius: '12px',
                                    background: 'linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    flexShrink: 0
                                }}>
                                    <Zap size={22} color="#667eea" strokeWidth={2.5} />
                                </div>
                                <span style={{ fontSize: '0.9375rem', color: '#475569', fontWeight: 500 }}>
                                    Automated processing
                                </span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                                <div style={{
                                    width: 44,
                                    height: 44,
                                    borderRadius: '12px',
                                    background: 'linear-gradient(135deg, #faf5ff 0%, #f3e8ff 100%)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    flexShrink: 0
                                }}>
                                    <Shield size={22} color="#764ba2" strokeWidth={2.5} />
                                </div>
                                <span style={{ fontSize: '0.9375rem', color: '#475569', fontWeight: 500 }}>
                                    Secure authentication
                                </span>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                <div style={{
                                    width: 44,
                                    height: 44,
                                    borderRadius: '12px',
                                    background: 'linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    flexShrink: 0
                                }}>
                                    <Clock size={22} color="#3b82f6" strokeWidth={2.5} />
                                </div>
                                <span style={{ fontSize: '0.9375rem', color: '#475569', fontWeight: 500 }}>
                                    Real-time monitoring
                                </span>
                            </div>
                        </div>

                        {/* Error Message */}
                        {error && (
                            <div style={{
                                padding: '1rem 1.25rem',
                                background: '#fef2f2',
                                border: '2px solid #fecaca',
                                borderRadius: '12px',
                                marginBottom: '1.5rem',
                                fontSize: '0.875rem',
                                color: '#991b1b',
                                fontWeight: 500,
                                lineHeight: 1.6
                            }}>
                                {error}
                            </div>
                        )}

                        {/* Demo Mode Login Button */}
                        <button
                            onClick={handleDemoLogin}
                            disabled={isLoading}
                            style={{
                                width: '100%',
                                padding: '1rem 1.5rem',
                                background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                                color: 'white',
                                border: 'none',
                                borderRadius: '12px',
                                fontSize: '1rem',
                                fontWeight: 700,
                                cursor: isLoading ? 'not-allowed' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '0.75rem',
                                boxShadow: '0 4px 12px rgba(102, 126, 234, 0.4)',
                                transition: 'all 0.2s',
                                opacity: isLoading ? 0.7 : 1,
                                transform: isLoading ? 'scale(0.98)' : 'scale(1)',
                            }}
                            onMouseEnter={(e) => {
                                if (!isLoading) {
                                    e.currentTarget.style.transform = 'translateY(-2px)';
                                    e.currentTarget.style.boxShadow = '0 6px 20px rgba(102, 126, 234, 0.5)';
                                }
                            }}
                            onMouseLeave={(e) => {
                                if (!isLoading) {
                                    e.currentTarget.style.transform = 'translateY(0)';
                                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(102, 126, 234, 0.4)';
                                }
                            }}
                        >
                            {isLoading ? (
                                <>
                                    <Loader2 size={20} className="animate-spin" />
                                    <span>Logging in...</span>
                                </>
                            ) : (
                                <>
                                    <span>Enter Dashboard</span>
                                    <ArrowRight size={20} strokeWidth={2.5} />
                                </>
                            )}
                        </button>

                        {/* Info Note */}
                        <div style={{
                            marginTop: '1.5rem',
                            padding: '1rem',
                            background: '#f8fafc',
                            borderRadius: '10px',
                            border: '1px solid #e2e8f0'
                        }}>
                            <p style={{
                                fontSize: '0.8125rem',
                                color: '#64748b',
                                lineHeight: 1.6,
                                margin: 0
                            }}>
                                <strong style={{ color: '#475569' }}>Demo Mode:</strong> Click the button above to access the dashboard without Google OAuth. Perfect for testing and development.
                            </p>
                        </div>

                        {/* Footer Note */}
                        <p style={{
                            textAlign: 'center',
                            fontSize: '0.75rem',
                            color: '#94a3b8',
                            marginTop: '2rem',
                            fontWeight: 500
                        }}>
                            Authorized users only • Secure access
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
