'use client';

import { createContext, useContext, useState, useEffect, useCallback, useRef, ReactNode } from 'react';
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
    initialized: boolean;
    signInWithGoogle: () => Promise<void>;
    signInWithEmail: (email: string, password: string) => Promise<any>;
    signUpWithEmail: (email: string, password: string, displayName: string) => Promise<any>;
    signOut: () => Promise<void>;
};

const UserContext = createContext<UserContextType | undefined>(undefined);

export function UserProvider({ children }: { children: ReactNode }) {
    const auth = useAuth();
    const firestore = useFirestore();
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const [initialized, setInitialized] = useState(false);
    const listenerSet = useRef(false);

    // Create user profile in Firestore (non-blocking)
    const ensureProfile = useCallback(async (firebaseUser: User) => {
        try {
            const userRef = doc(firestore, `users/${firebaseUser.uid}`);
            const snapshot = await getDoc(userRef);
            if (!snapshot.exists()) {
                await setDoc(userRef, {
                    uid: firebaseUser.uid,
                    displayName: firebaseUser.displayName,
                    email: firebaseUser.email,
                    photoURL: firebaseUser.photoURL,
                    createdAt: new Date(),
                });
            }
        } catch (error) {
            // Profile creation is non-blocking, just log
        }
    }, [firestore]);

    useEffect(() => {
        // Prevent multiple listeners
        if (listenerSet.current) return;
        listenerSet.current = true;

        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
            if (firebaseUser) {
                try {
                    const token = await firebaseUser.getIdToken(true);
                    localStorage.setItem('auth_token', token);
                    setUser(firebaseUser);
                    ensureProfile(firebaseUser);
                } catch (error) {
                    localStorage.removeItem('auth_token');
                    setUser(null);
                }
            } else {
                localStorage.removeItem('auth_token');
                setUser(null);
            }

            setLoading(false);
            setInitialized(true);
        });

        return () => {
            unsubscribe();
            listenerSet.current = false;
        };
    }, [auth, ensureProfile]);

    const signInWithGoogle = useCallback(async () => {
        const provider = new GoogleAuthProvider();
        const result = await signInWithPopup(auth, provider);
        if (result.user) {
            const token = await result.user.getIdToken(true);
            localStorage.setItem('auth_token', token);
            setUser(result.user);
            router.push('/');
        }
    }, [auth, router]);

    const signInWithEmail = useCallback(async (email: string, password: string) => {
        const result = await signInWithEmailAndPassword(auth, email, password);
        if (result.user) {
            const token = await result.user.getIdToken(true);
            localStorage.setItem('auth_token', token);
            setUser(result.user);
        }
        return result;
    }, [auth]);

    const signUpWithEmail = useCallback(async (email: string, password: string, displayName: string) => {
        const result = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(result.user, { displayName });
        if (result.user) {
            const token = await result.user.getIdToken(true);
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
        <UserContext.Provider value={{ user, loading, initialized, signInWithGoogle, signInWithEmail, signUpWithEmail, signOut }}>
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
