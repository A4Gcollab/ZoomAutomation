'use client';

import { useState, useEffect, useRef } from 'react';
import { useUser } from '@/firebase/auth/use-user';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Icons } from '@/components/icons';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { useToast } from '@/hooks/use-toast';

export default function LoginPage() {
  const { user, loading, initialized, signInWithGoogle, signInWithEmail, signUpWithEmail } = useUser();
  const router = useRouter();
  const { toast } = useToast();
  const hasRedirected = useRef(false);

  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');
  const [signupName, setSignupName] = useState('');
  const [signupEmail, setSignupEmail] = useState('');
  const [signupPassword, setSignupPassword] = useState('');
  const [localLoading, setLocalLoading] = useState(false);

  // If user is already logged in, redirect to dashboard (only once)
  useEffect(() => {
    if (initialized && !loading && user && !hasRedirected.current) {
      hasRedirected.current = true;
      router.replace('/');
    }
  }, [user, loading, initialized, router]);

  const handleGoogleSignIn = async () => {
    setLocalLoading(true);
    try {
      await signInWithGoogle();
    } catch (error: any) {
      toast({ variant: 'destructive', title: 'Sign-in failed', description: error.message });
      setLocalLoading(false);
    }
  };

  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalLoading(true);
    try {
      await signInWithEmail(loginEmail, loginPassword);
      router.push('/');
    } catch (error: any) {
      toast({ variant: 'destructive', title: 'Sign-in failed', description: error.message || 'Please check your email and password.' });
      setLocalLoading(false);
    }
  };

  const handleEmailSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLocalLoading(true);
    try {
      await signUpWithEmail(signupEmail, signupPassword, signupName);
      router.push('/');
    } catch (error: any) {
      toast({ variant: 'destructive', title: 'Sign-up failed', description: error.message });
      setLocalLoading(false);
    }
  };

  // Show loading while auth is initializing or user is logged in (redirecting)
  if (!initialized || loading || user) {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center bg-background">
        <Icons.spinner className="h-8 w-8 animate-spin text-primary" />
        <p className="mt-4 text-sm text-muted-foreground">
          {user ? 'Redirecting to dashboard...' : 'Loading...'}
        </p>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background">
      <div className="w-full max-w-md p-4">
        <div className="flex flex-col items-center justify-center space-y-2 mb-6">
          <Icons.logo className="h-12 w-12 text-primary" />
          <h1 className="text-2xl font-semibold tracking-tight">
            Welcome to Zoom Auto
          </h1>
          <p className="text-sm text-muted-foreground">
            Sign in or create an account to continue
          </p>
        </div>
        <Tabs defaultValue="signin" className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="signin">Sign In</TabsTrigger>
            <TabsTrigger value="signup">Sign Up</TabsTrigger>
          </TabsList>
          <TabsContent value="signin">
            <Card>
              <CardHeader>
                <CardTitle>Sign In</CardTitle>
                <CardDescription>Enter your credentials to access your account.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <form onSubmit={handleEmailLogin} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="login-email">Email</Label>
                    <Input id="login-email" type="email" placeholder="m@example.com" required value={loginEmail} onChange={e => setLoginEmail(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="login-password">Password</Label>
                    <Input id="login-password" type="password" required value={loginPassword} onChange={e => setLoginPassword(e.target.value)} />
                  </div>
                  <Button type="submit" className="w-full" disabled={localLoading}>
                    {localLoading && <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />}
                    Sign In
                  </Button>
                </form>
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <span className="w-full border-t" />
                  </div>
                  <div className="relative flex justify-center text-xs uppercase">
                    <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
                  </div>
                </div>
                <Button variant="outline" className="w-full" onClick={handleGoogleSignIn} disabled={localLoading}>
                  <Icons.google className="mr-2 h-4 w-4" />
                  Google
                </Button>
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="signup">
            <Card>
              <CardHeader>
                <CardTitle>Sign Up</CardTitle>
                <CardDescription>Create a new account to get started.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <form onSubmit={handleEmailSignUp} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="signup-name">Name</Label>
                    <Input id="signup-name" type="text" placeholder="John Doe" required value={signupName} onChange={e => setSignupName(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-email">Email</Label>
                    <Input id="signup-email" type="email" placeholder="m@example.com" required value={signupEmail} onChange={e => setSignupEmail(e.target.value)} />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="signup-password">Password</Label>
                    <Input id="signup-password" type="password" required minLength={6} value={signupPassword} onChange={e => setSignupPassword(e.target.value)} />
                  </div>
                  <Button type="submit" className="w-full" disabled={localLoading}>
                    {localLoading && <Icons.spinner className="mr-2 h-4 w-4 animate-spin" />}
                    Create Account
                  </Button>
                </form>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
