'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { FirebaseApp, getApps, initializeApp, getApp } from 'firebase/app';
import { Auth, getAuth, browserLocalPersistence, setPersistence } from 'firebase/auth';
import { Firestore, getFirestore } from 'firebase/firestore';
import { firebaseConfig } from './config';

type FirebaseContextValue = {
  app: FirebaseApp;
  auth: Auth;
  firestore: Firestore;
};

const FirebaseContext = createContext<FirebaseContextValue | null>(null);

type FirebaseProviderProps = {
  children: React.ReactNode;
};

// Initialize Firebase once at module level (only on client)
let cachedFirebase: FirebaseContextValue | null = null;

function getFirebaseInstance(): FirebaseContextValue | null {
  if (typeof window === 'undefined') {
    return null;
  }

  if (cachedFirebase) {
    return cachedFirebase;
  }

  let app: FirebaseApp;
  if (getApps().length === 0) {
    app = initializeApp(firebaseConfig);
  } else {
    app = getApp();
  }

  const auth = getAuth(app);
  const firestore = getFirestore(app);

  // Set persistence
  setPersistence(auth, browserLocalPersistence).catch(console.error);

  cachedFirebase = { app, auth, firestore };
  return cachedFirebase;
}

export function FirebaseProvider({ children }: FirebaseProviderProps) {
  const [firebase, setFirebase] = useState<FirebaseContextValue | null>(null);

  useEffect(() => {
    const instance = getFirebaseInstance();
    if (instance) {
      setFirebase(instance);
    }
  }, []);

  // During SSR or before hydration, render children without context
  if (!firebase) {
    return <>{children}</>;
  }

  return (
    <FirebaseContext.Provider value={firebase}>
      {children}
    </FirebaseContext.Provider>
  );
}

export function useFirebaseApp() {
  const context = useContext(FirebaseContext);
  if (!context) {
    throw new Error('useFirebaseApp must be used within a FirebaseProvider');
  }
  return context.app;
}

export function useAuth() {
  const context = useContext(FirebaseContext);
  if (!context) {
    throw new Error('useAuth must be used within a FirebaseProvider');
  }
  return context.auth;
}

export function useFirestore() {
  const context = useContext(FirebaseContext);
  if (!context) {
    throw new Error('useFirestore must be used within a FirebaseProvider');
  }
  return context.firestore;
}
