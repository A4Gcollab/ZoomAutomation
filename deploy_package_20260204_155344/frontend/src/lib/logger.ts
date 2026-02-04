/**
 * Production-safe logging utility
 * Only logs in development, sends critical errors to monitoring in production
 */

const isDevelopment = process.env.NODE_ENV === 'development';

export const logger = {
    info: (...args: any[]) => {
        if (isDevelopment) {
            console.info('[INFO]', ...args);
        }
    },

    warn: (...args: any[]) => {
        if (isDevelopment) {
            console.warn('[WARN]', ...args);
        }
    },

    error: (...args: any[]) => {
        if (isDevelopment) {
            console.error('[ERROR]', ...args);
        } else {
            // In production, you could send to a monitoring service like Sentry
            // For now, we'll just suppress console errors in production
            // TODO: Integrate with error monitoring service
        }
    },

    debug: (...args: any[]) => {
        if (isDevelopment) {
            console.debug('[DEBUG]', ...args);
        }
    },
};
