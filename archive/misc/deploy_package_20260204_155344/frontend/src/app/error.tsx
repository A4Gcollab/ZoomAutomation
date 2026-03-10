'use client';

import { useEffect } from 'react';
import { logger } from '@/lib/logger';

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        logger.error('Next.js Error Page:', error);
    }, [error]);

    return (
        <div className="flex min-h-screen items-center justify-center bg-background p-4">
            <div className="max-w-md rounded-lg border border-destructive bg-card p-6 text-center shadow-lg">
                <h2 className="mb-2 text-2xl font-bold text-destructive">Application Error</h2>
                <p className="mb-4 text-muted-foreground">
                    An unexpected error occurred. Our team has been notified.
                </p>
                <div className="flex gap-2 justify-center">
                    <button
                        onClick={() => reset()}
                        className="rounded-md bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90"
                    >
                        Try Again
                    </button>
                    <button
                        onClick={() => window.location.href = '/'}
                        className="rounded-md border border-input bg-background px-4 py-2 hover:bg-accent"
                    >
                        Go Home
                    </button>
                </div>
            </div>
        </div>
    );
}
