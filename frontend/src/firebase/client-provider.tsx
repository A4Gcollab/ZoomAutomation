'use client';

import React from 'react';
import { FirebaseProvider } from './provider';
import { FirebaseErrorListener } from '@/components/FirebaseErrorListener';
import { UserProvider } from './auth/use-user';

export function FirebaseClientProvider({ children }: { children: React.ReactNode }) {
  return (
    <FirebaseProvider>
      <UserProvider>
        {children}
        <FirebaseErrorListener />
      </UserProvider>
    </FirebaseProvider>
  );
}
