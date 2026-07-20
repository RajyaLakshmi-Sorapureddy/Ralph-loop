export type UserRole = 'requester' | 'finance';

export interface User {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export type RequestStatus = 'pending' | 'approved' | 'rejected' | 'more_info_needed';

export interface ReimbursementRequest {
  id: number;
  requester_id: number;
  amount: string;
  currency: string;
  category: string;
  expense_date: string;
  description: string;
  status: RequestStatus;
  created_at: string;
  updated_at: string;
}

export interface RequestDocument {
  id: number;
  request_id: number;
  file_name: string;
  file_size: number;
  uploaded_at: string;
}
