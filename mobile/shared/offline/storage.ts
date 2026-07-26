// Storage abstraction (Stage 19).
//
// A tiny key/value interface so the SDK is agnostic to the platform's storage.
// In apps this is backed by encrypted device storage (e.g. iOS Keychain /
// Android Keystore for secrets, MMKV/AsyncStorage for cache); tests use memory.
// No business logic lives here.

export interface StorageAdapter {
  get(key: string): string | null;
  set(key: string, value: string): void;
  remove(key: string): void;
}

export class MemoryStorage implements StorageAdapter {
  private data = new Map<string, string>();

  get(key: string): string | null {
    return this.data.has(key) ? (this.data.get(key) as string) : null;
  }

  set(key: string, value: string): void {
    this.data.set(key, value);
  }

  remove(key: string): void {
    this.data.delete(key);
  }
}
