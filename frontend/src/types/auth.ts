export interface User {
  id: string;
  full_name: string;
  email: string;
  created_at: string;
  updated_at: string;
}

export interface RegisterData {
  full_name: string;
  email: string;
  password: string;
  confirm_password: string;
}

export interface LoginData {
  email: string;
  password: string;
}
