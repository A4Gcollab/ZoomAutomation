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

export function UserProvider({ children }: { children: ReactNode }) {
    const auth = useAuth();
    const firestore = useFirestore();
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    // Save token to localStorage
    const saveToken = useCallback(async (firebaseUser: User) => {
        try {
            const token = await firebaseUser.getIdToken(true);
            localStorage.setItem('auth_token', token);
            return token;
        } catch (error) {
            console.error("Failed to get token:", error);
            return null;
        }
    }, []);

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
            console.error("Profile creation error (non-blocking):", error);
        }
    }, [firestore]);

    useEffect(() => {
        console.log("Auth: Setting up listener");

        // Single source of truth: onAuthStateChanged
        const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
            console.log("Auth: State changed -", firebaseUser ? `user: ${firebaseUser.email}` : "no user");

            if (firebaseUser) {
                // User is signed in
                await saveToken(firebaseUser);
                setUser(firebaseUser);
                ensureProfile(firebaseUser); // Fire and forget
            } else {
                // User is signed out
                localStorage.removeItem('auth_token');
                setUser(null);
            }

            setLoading(false);
        });

        return () => unsubscribe();
    }, [auth, saveToken, ensureProfile]);

    // Token refresh handler
    useEffect(() => {
        if (!user) return;

        const unsubscribe = auth.onIdTokenChanged(async (firebaseUser) => {
            if (firebaseUser) {
                await saveToken(firebaseUser);
            }
        });

        return () => unsubscribe();
    }, [auth, user, saveToken]);

    const signInWithGoogle = useCallback(async () => {
        const provider = new GoogleAuthProvider();
        const result = await signInWithPopup(auth, provider);
        // onAuthStateChanged will handle the rest
        if (result.user) {
            await saveToken(result.user);
            router.push('/');
        }
    }, [auth, router, saveToken]);

    const signInWithEmail = useCallback(async (email: string, password: string) => {
        const result = await signInWithEmailAndPassword(auth, email, password);
        // onAuthStateChanged will handle the rest
        if (result.user) {
            await saveToken(result.user);
        }
        return result;
    }, [auth, saveToken]);

    const signUpWithEmail = useCallback(async (email: string, password: string, displayName: string) => {
        const result = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(result.user, { displayName });
        // onAuthStateChanged will handle the rest
        if (result.user) {
            await saveToken(result.user);
        }
        return result;
    }, [auth, saveToken]);

    const signOut = useCallback(async () => {
        localStorage.removeItem('auth_token');
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
