export interface User {
  name: string;
  email: string;
}

const USER_KEY = "autonegotiator_user";

export function saveUser(name: string, email: string): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(USER_KEY, JSON.stringify({ name, email }));
}

export function getUser(): User | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export function isLoggedIn(): boolean {
  return !!getUser();
}

export function logout(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(USER_KEY);
}
