export interface LoginResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export interface Category {
  id: string
  name: string
  type: string
  icon: string | null
  color: string | null
  description: string | null
  display_order: number
}

export interface Transaction {
  id: string
  amount: number
  type: string
  description: string | null
  transaction_date: string
  payment_method: string | null
  merchant: string | null
  notes: string | null
  tags: string[]
  llm_comment: string | null
  llm_comment_at: string | null
  created_at: string
  category_name: string
  category_icon: string | null
  category_color: string | null
}

export interface TransactionListResponse {
  items: Transaction[]
  total: number
  limit: number
  offset: number
}

export interface TransactionSummary {
  total_income: number
  total_expense: number
  net: number
  count: number
}

export interface CategoryBreakdown {
  category_name: string
  category_icon: string | null
  category_color: string | null
  type: string
  total: number
}

export interface TransactionFilters {
  year?: number
  month?: number
  from?: string
  to?: string
  type?: string
  category_id?: string
  q?: string
  sort?: string
  order?: string
  limit?: number
  offset?: number
}
