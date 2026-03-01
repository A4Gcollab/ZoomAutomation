'use client';

import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
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

const setUserProfile = async (firestore: any, user: User, additionalData: any = {}) => {
    if (!user) return;
    const userRef = doc(firestore, `users/${user.uid}`);
    const snapshot = await getDoc(userRef);

    if (!snapshot.exists()) {
        const { displayName, email, photoURL } = user;
        const createdAt = new Date();
        try {
            await setDoc(userRef, {
                uid: user.uid,
                displayName,
                email,
                photoURL,
                createdAt,
                ...additionalData,
            });
        } catch (error) {
            console.error("Error creating user document", error);
        }
    }
};

export function UserProvider({ children }: { children: ReactNode }) {
    const auth = useAuth();
    const firestore = useFirestore();
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Use onIdTokenChanged to handle token refreshes automatically
        const unsubscribe = auth.onIdTokenChanged(async (user) => {
            if (user) {
                try {
                    const token = await user.getIdToken();
                    console.log("Auth: Got fresh ID token", token.substring(0, 10) + "...");
                    localStorage.setItem('auth_token', token);
                    console.log("Auth: Saved token into localStorage");

                    // Only update profile/state if this is a sign-in or initial load (not just token refresh)
                    // We can check if we already have the user in state to avoid re-fetching profile too often
                    // But for simplicity, we'll ensure profile exists
                    await setUserProfile(firestore, user);
                    setUser(user);

                    // Note: Redirects are handled in the component (page.tsx)
                } catch (error) {
                    console.error("Error getting token:", error);
                }
            } else {
                localStorage.removeItem('auth_token');
                setUser(null);
            }
            setLoading(false);
        });

        // Handle redirect result if needed (though we use popup now)
        getRedirectResult(auth).then(async (result) => {
            if (result && result.user) {
                // Token update handled by onIdTokenChanged above
                router.push('/');
            }
        }).catch(console.error);

        return () => unsubscribe();
    }, [auth, firestore, router]);

    const signInWithGoogle = async () => {
        const provider = new GoogleAuthProvider();
        try {
            // Use redirect instead of popup to avoid Windows intercepting the OAuth flow
            await signInWithRedirect(auth, provider);
            // After redirect, the result is handled by getRedirectResult in useEffect above
        } catch (error) {
            console.error('Google sign-in error:', error);
            throw error;
        }
    };

    const signInWithEmail = async (email: string, password: string) => {
        return signInWithEmailAndPassword(auth, email, password);
    }

    const signUpWithEmail = async (email: string, password: string, displayName: string) => {
        const userCredential = await createUserWithEmailAndPassword(auth, email, password);
        await updateProfile(userCredential.user, { displayName });
        await setUserProfile(firestore, userCredential.user, { displayName });
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
