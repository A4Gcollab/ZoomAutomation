// Error Notification Service
import { toast, type ToastOptions } from 'react-toastify';

const defaultOptions: ToastOptions = {
    position: 'top-right',
    autoClose: 5000,
    hideProgressBar: false,
    closeOnClick: true,
    pauseOnHover: true,
    draggable: true,
};

export const notify = {
    success: (message: string) => {
        toast.success(message, defaultOptions);
    },

    error: (message: string) => {
        toast.error(message, {
            ...defaultOptions,
            autoClose: 7000, // Errors stay longer
        });
    },

    warning: (message: string) => {
        toast.warning(message, defaultOptions);
    },

    info: (message: string) => {
        toast.info(message, defaultOptions);
    },

    // Special notifications
    authError: () => {
        toast.error('🔒 Authentication failed. Please sign in again.', {
            ...defaultOptions,
            autoClose: false, // Don't auto-close auth errors
        });
    },

    apiError: (operation: string, error?: string) => {
        toast.error(`❌ ${operation} failed${error ? `: ${error}` : ''}`, {
            ...defaultOptions,
            autoClose: 7000,
        });
    },

    uploadSuccess: (title: string) => {
        toast.success(`✅ "${title}" uploaded successfully!`, defaultOptions);
    },

    processingStart: (title: string) => {
        toast.info(`⚙️ Processing "${title}"...`, {
            ...defaultOptions,
            autoClose: 3000,
        });
    },
};
