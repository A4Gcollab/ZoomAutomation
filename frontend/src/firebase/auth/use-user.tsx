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
    type User
} from 'firebase/auth';
import { useAuth, useFirestore } from '@/firebase/provider';
import { doc, setDoc, getDoc } from 'firebase/firestore';
import { useRouter } from 'next/navigation';

type UserContextType = {
    user: User | null;
    loading: boolean;
    signInWithGoogle: () => Promise<void>;
    signInWithEmail: (email: string, password: string) => Promise<any>;
    signUpWithEmail: (email: string, password: string, displayName: string) => Promise<any>;
    signOut: () => Promise<void>;
};

const UserContext = createContext<UserContextType | undefined>(undefined);

// Global flag to track if auth listener is set up
let authListenerActive = false;

export function UserProvider({ children }: { children: ReactNode }) {
    const auth = useAuth();
    const firestore = useFirestore();
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Prevent duplicate listeners
        if (authListenerActive) {
            return;
        }
        authListenerActive = true;

        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
            if (firebaseUser) {
                try {
                    const token = await firebaseUser.getIdToken();
                    localStorage.setItem('auth_token', token);
                    setUser(firebaseUser);

                    // Profile creation in background
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

        return () => {
            unsubscribe();
            authListenerActive = false;
        };
    }, [auth, firestore]);

    const signInWithGoogle = useCallback(async () => {
        const provider = new GoogleAuthProvider();
        const result = await signInWithPopup(auth, provider);
        if (result.user) {
            const token = await result.user.getIdToken();
            localStorage.setItem('auth_token', token);
            setUser(result.user);
            router.push('/');
        }
    }, [auth, router]);

    const signInWithEmail = useCallback(async (email: string, password: string) => {
        const result = await signInWithEmailAndPassword(auth, email, password);
        if (result.user) {
            const token = await result.user.getIdToken();
            localStorage.setItem('auth_token', token);
            setUser(result.user);
        }
        return result;
    }, [auth]);

    const signUpWithEmail = useCallback(async (email: string, password: string, displayName: string) => {
        const result = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(result.user, { displayName });
        if (result.user) {
            const token = await result.user.getIdToken();
            localStorage.setItem('auth_token', token);
            setUser(result.user);
        }
        return result;
    }, [auth]);

    const signOut = useCallback(async () => {
        localStorage.removeItem('auth_token');
        setUser(null);
        await firebaseSignOut(auth);
        router.push('/login');
    }, [auth, router]);

    return (
        <UserContext.Provider value={{ user, loading, signInWithGoogle, signInWithEmail, signUpWithEmail, signOut }}>
            {children}
        </UserContext.Provider>
    );
}

export const useUser = (): UserContextType => {
    const context = useContext(UserContext);
    if (context === undefined) {
        throw new Error('useUser must be used within a UserProvider');
    }
    return context;
};
