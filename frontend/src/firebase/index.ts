'use client';

import { getApp, getApps, initializeApp } from 'firebase/app';
import { getAuth, browserLocalPersistence, setPersistence } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

import { firebaseConfig } from './config';

let authInitPromise: Promise<void> | null = null;

function initializeFirebase() {
  if (getApps().length) {
    const app = getApp();
    const auth = getAuth(app);
    const firestore = getFirestore(app);
    return { app, auth, firestore };
  }

  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  const firestore = getFirestore(app);

  // Set persistence to local (survives browser restart)
  if (!authInitPromise) {
    authInitPromise = setPersistence(auth, browserLocalPersistence).catch(console.error);
  }

  return { app, auth, firestore };
}

export { useUser } from './auth/use-user';
export {
  FirebaseProvider,
  useFirebaseApp,
  useFirestore,
  useAuth,
} from './provider';

export { initializeFirebase };
