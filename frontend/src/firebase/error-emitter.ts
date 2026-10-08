import { type FirestorePermissionError } from './errors';

type AppEvents = {
  'permission-error': (error: FirestorePermissionError) => void;
};

class TypedEventEmitter<T extends Record<string, any>> {
  private listeners: { [K in keyof T]?: Array<T[K]> } = {};

  emit<K extends keyof T>(event: K, ...args: Parameters<T[K]>) {
    const eventListeners = this.listeners[event];
    if (eventListeners) {
      eventListeners.forEach((listener) => {
        (listener as any)(...args);
      });
    }
  }

  on<K extends keyof T>(event: K, listener: T[K]) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event]!.push(listener);
  }

  off<K extends keyof T>(event: K, listener: T[K]) {
    const eventListeners = this.listeners[event];
    if (eventListeners) {
      this.listeners[event] = eventListeners.filter((l) => l !== listener) as any;
    }
  }
}

export const errorEmitter = new TypedEventEmitter<AppEvents>();
