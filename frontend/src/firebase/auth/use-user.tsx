'use client';

import { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';
import {
    onAuthStateChanged,
    GoogleAuthProvider,
    signInWithRedirect,
    signInWithPopup,
    signOut as firebaseSignOut,
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    updateProfile,
    getRedirectResult,
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

// Maximum time to wait for auth state (prevents infinite loading)
const AUTH_TIMEOUT_MS = 5000;

const setUserProfile = async (firestore: any, user: User, additionalData: any = {}) => {
    if (!user) return;
    try {
        const userRef = doc(firestore, `users/${user.uid}`);
        const snapshot = await getDoc(userRef);

        if (!snapshot.exists()) {
            const { displayName, email, photoURL } = user;
            const createdAt = new Date();
            await setDoc(userRef, {
                uid: user.uid,
                displayName,
                email,
                photoURL,
                createdAt,
                ...additionalData,
            });
        }
    } catch (error) {
        console.error("Error creating user document (non-blocking):", error);
        // Don't throw - profile creation is non-blocking
    }
};

export function UserProvider({ children }: { children: ReactNode }) {
    const auth = useAuth();
    const firestore = useFirestore();
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);
    const authInitialized = useRef(false);
    const timeoutRef = useRef<NodeJS.Timeout | null>(null);

    useEffect(() => {
        // Set a timeout to ensure loading doesn't hang forever
        timeoutRef.current = setTimeout(() => {
            if (loading && !authInitialized.current) {
                console.warn("Auth: Timeout reached, forcing loading to false");
                setLoading(false);
            }
        }, AUTH_TIMEOUT_MS);

        // Use onIdTokenChanged to handle token refreshes automatically
        const unsubscribe = auth.onIdTokenChanged(async (user) => {
            authInitialized.current = true;

            // Clear the timeout since we got a response
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
                timeoutRef.current = null;
            }

            if (user) {
                try {
                    const token = await user.getIdToken();
                    console.log("Auth: Got fresh ID token", token.substring(0, 10) + "...");
                    localStorage.setItem('auth_token', token);
                    console.log("Auth: Saved token into localStorage");

                    // Set user immediately, profile creation happens in background
                    setUser(user);
                    setLoading(false);

                    // Profile creation is non-blocking
                    setUserProfile(firestore, user).catch(console.error);
                } catch (error) {
                    console.error("Error getting token:", error);
                    setUser(null);
                    setLoading(false);
                }
            } else {
                localStorage.removeItem('auth_token');
                setUser(null);
                setLoading(false);
            }
        });

        // Handle redirect result if needed (though we use popup now)
        getRedirectResult(auth).then(async (result) => {
            if (result && result.user) {
                // Token update handled by onIdTokenChanged above
                router.push('/');
            }
        }).catch(console.error);

        return () => {
            unsubscribe();
            if (timeoutRef.current) {
                clearTimeout(timeoutRef.current);
            }
        };
    }, [auth, firestore, router]);

    const signInWithGoogle = async () => {
        const provider = new GoogleAuthProvider();
        try {
            const result = await signInWithPopup(auth, provider);
            if (result.user) {
                // Get and store the token immediately before redirect
                const token = await result.user.getIdToken();
                localStorage.setItem('auth_token', token);
                console.log("Auth: Token saved after Google sign in");

                await setUserProfile(firestore, result.user);
                setUser(result.user);
                router.push('/');
            }
        } catch (error) {
            console.error('Google sign-in error:', error);
            throw error;
        }
    };

    const signInWithEmail = async (email: string, password: string) => {
        const userCredential = await signInWithEmailAndPassword(auth, email, password);
        // Get and store the token immediately after sign in
        if (userCredential.user) {
            const token = await userCredential.user.getIdToken();
            localStorage.setItem('auth_token', token);
            console.log("Auth: Token saved after email sign in");
            setUser(userCredential.user);
        }
        return userCredential;
    }

    const signUpWithEmail = async (email: string, password: string, displayName: string) => {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(userCredential.user, { displayName });
        await setUserProfile(firestore, userCredential.user, { displayName });
        // Get and store the token immediately after sign up
        if (userCredential.user) {
            const token = await userCredential.user.getIdToken();
            localStorage.setItem('auth_token', token);
            console.log("Auth: Token saved after email sign up");
            setUser(userCredential.user);
        }
        return userCredential;
    }

    const signOut = async () => {
        await firebaseSignOut(auth);
        router.push('/login');
    };

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
