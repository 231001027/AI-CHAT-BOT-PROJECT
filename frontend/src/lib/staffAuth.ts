export interface StaffAccount {
  id: string;
  name: string;
}

const PASSWORD = 'NIEPMD@123';

const STAFF: StaffAccount[] = [
  { id: 'nachi@niepmdshc', name: 'Dr. Nachiketa Rout' },
  { id: 'bala@niepmdshc', name: 'Mrs. Balambigai' },
  { id: 'gaya@niepmdshc', name: 'Mrs. Gayathri' },
  { id: 'moni@niepmdshc', name: 'Mr. Monish' },
  { id: 'joyp@niepmdshc', name: 'Mr. Joy Philip' },
  { id: 'juli@niepmdshc', name: 'Mrs. Julie Sandra Abel' },
  { id: 'inna@niepmdshc', name: 'Mr. Innamul Hassan' },
  { id: 'eric@niepmdshc', name: 'Mr. Eric Reynold R' },
];

const STORAGE_KEY = 'niepmd-staff-user';

export function authenticateStaff(userId: string, password: string): StaffAccount | null {
  const id = userId.trim().toLowerCase();
  if (password.trim().toLowerCase() !== PASSWORD.toLowerCase()) return null;
  return STAFF.find((account) => account.id === id) ?? null;
}

export function getSignedInStaff(): StaffAccount | null {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StaffAccount;
    return STAFF.find((account) => account.id === parsed.id) ?? null;
  } catch {
    return null;
  }
}

export function signInStaff(account: StaffAccount) {
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(account));
  window.dispatchEvent(new Event('niepmd-staff-auth'));
}

export function signOutStaff() {
  window.localStorage.removeItem(STORAGE_KEY);
  window.dispatchEvent(new Event('niepmd-staff-auth'));
}
