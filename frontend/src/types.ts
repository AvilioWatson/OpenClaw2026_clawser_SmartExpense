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
