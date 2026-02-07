'use client';

import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import {
    onAuthStateChanged,
    GoogleAuthProvider,
    signInWithPopup,
    signOut as firebaseSignOut,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    updateProfile,
    type User,
    type Auth
} from 'firebase/auth';
import { doc, setDoc, getDoc, type Firestore } from 'firebase/firestore';
import { useRouter } from 'next/navigation';

type UserContextType = {
    user: User | null;
    loading: boolean;
    signInWithGoogle: () => Promise<void>;
    signInWithEmail: (email: string, password: string) => Promise<any>;
    signUpWithEmail: (email: string, password: string, displayName: string) => Promise<any>;
    signOut: () => Promise<void>;
};

const UserContext = createContext<UserContextType>({
    user: null,
    loading: true,
    signInWithGoogle: async () => {},
    signInWithEmail: async () => {},
    signUpWithEmail: async () => {},
    signOut: async () => {},
});

// Get Firebase instances directly (lazy initialization)
function getFirebaseAuth(): Auth | null {
    if (typeof window === 'undefined') return null;
    try {
        const { getAuth, getApp } = require('firebase/auth');
        const { getApps } = require('firebase/app');
        if (getApps().length === 0) return null;
        return getAuth(getApp());
    } catch {
        return null;
    }
}

function getFirebaseFirestore(): Firestore | null {
    if (typeof window === 'undefined') return null;
    try {
        const { getFirestore, getApp } = require('firebase/firestore');
        const { getApps } = require('firebase/app');
        if (getApps().length === 0) return null;
        return getFirestore(getApp());
    } catch {
        return null;
    }
}

export function UserProvider({ children }: { children: ReactNode }) {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [authReady, setAuthReady] = useState(false);

    useEffect(() => {
        // Wait for Firebase to be initialized
        const checkAuth = () => {
            const auth = getFirebaseAuth();
            if (auth) {
                setAuthReady(true);
                const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
                    if (firebaseUser) {
                        try {
                            const token = await firebaseUser.getIdToken();
                            localStorage.setItem('auth_token', token);
                            setUser(firebaseUser);

                            // Profile creation in background
                            const firestore = getFirebaseFirestore();
                            if (firestore) {
                                const userRef = doc(firestore, `users/${firebaseUser.uid}`);
                                getDoc(userRef).then(snapshot => {
                                    if (!snapshot.exists()) {
                                        setDoc(userRef, {
                                            uid: firebaseUser.uid,
                                            displayName: firebaseUser.displayName,
                                            email: firebaseUser.email,
                                            photoURL: firebaseUser.photoURL,
                                            createdAt: new Date(),
                                        }).catch(() => {});
                                    }
                                }).catch(() => {});
                            }
                        } catch {
                            localStorage.removeItem('auth_token');
                            setUser(null);
                        }
                    } else {
                        localStorage.removeItem('auth_token');
                        setUser(null);
                    }
                    setLoading(false);
                });
                return unsubscribe;
            } else {
                // Firebase not ready yet, check again
                const timer = setTimeout(checkAuth, 100);
                return () => clearTimeout(timer);
            }
        };

        const cleanup = checkAuth();
        return () => {
            if (typeof cleanup === 'function') {
                cleanup();
            }
        };
    }, []);

    const signInWithGoogle = useCallback(async () => {
        const auth = getFirebaseAuth();
        if (!auth) throw new Error('Auth not initialized');

        const provider = new GoogleAuthProvider();
        const result = await signInWithPopup(auth, provider);
        if (result.user) {
            const token = await result.user.getIdToken();
            localStorage.setItem('auth_token', token);
            setUser(result.user);
            router.push('/');
        }
    }, [router]);

    const signInWithEmail = useCallback(async (email: string, password: string) => {
        const auth = getFirebaseAuth();
        if (!auth) throw new Error('Auth not initialized');

        const result = await signInWithEmailAndPassword(auth, email, password);
        if (result.user) {
            const token = await result.user.getIdToken();
            localStorage.setItem('auth_token', token);
            setUser(result.user);
        }
        return result;
    }, []);

    const signUpWithEmail = useCallback(async (email: string, password: string, displayName: string) => {
        const auth = getFirebaseAuth();
        if (!auth) throw new Error('Auth not initialized');

        const result = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(result.user, { displayName });
        if (result.user) {
            const token = await result.user.getIdToken();
            localStorage.setItem('auth_token', token);
            setUser(result.user);
        }
        return result;
    }, []);

    const signOut = useCallback(async () => {
        const auth = getFirebaseAuth();
        localStorage.removeItem('auth_token');
        setUser(null);
        if (auth) {
            await firebaseSignOut(auth);
        }
        router.push('/login');
    }, [router]);

    return (
        <UserContext.Provider value={{ user, loading, signInWithGoogle, signInWithEmail, signUpWithEmail, signOut }}>
            {children}
        </UserContext.Provider>
    );
}

export const useUser = (): UserContextType => {
    return useContext(UserContext);
};
