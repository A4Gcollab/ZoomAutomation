'use client';

import { getApp, getApps, initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

import { firebaseConfig } from './config';

function initializeFirebase() {
  if (getApps().length) {
    return {
      app: getApp(),
      auth: getAuth(),
      firestore: getFirestore(),
    };
  }

  const app = initializeApp(firebaseConfig);
  const auth = getAuth(app);
  const firestore = getFirestore(app);

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
