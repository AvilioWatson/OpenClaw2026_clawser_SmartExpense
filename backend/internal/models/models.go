package models

import "time"

type LoginRequest struct {
	Token string `json:"token"`
}

type LoginResponse struct {
	AccessToken string `json:"access_token"`
	TokenType   string `json:"token_type"`
	ExpiresIn   int64  `json:"expires_in"`
}

type Category struct {
	ID           string  `json:"id"`
	Name         string  `json:"name"`
	Type         string  `json:"type"`
	Icon         *string `json:"icon"`
	Color        *string `json:"color"`
	Description  *string `json:"description"`
	DisplayOrder int     `json:"display_order"`
}

type TransactionListResponse struct {
	Items  []Transaction `json:"items"`
	Total  int           `json:"total"`
	Limit  int           `json:"limit"`
	Offset int           `json:"offset"`
}

type TransactionSummary struct {
	TotalIncome  float64 `json:"total_income"`
	TotalExpense float64 `json:"total_expense"`
	Net          float64 `json:"net"`
	Count        int     `json:"count"`
}

type CategoryBreakdown struct {
	CategoryName  string  `json:"category_name"`
	CategoryIcon  *string `json:"category_icon"`
	CategoryColor *string `json:"category_color"`
	Type          string  `json:"type"`
	Total         float64 `json:"total"`
}

type Transaction struct {
	ID              string     `json:"id"`
	Amount          float64    `json:"amount"`
	Type            string     `json:"type"`
	Description     *string    `json:"description"`
	TransactionDate string     `json:"transaction_date"`
	PaymentMethod   *string    `json:"payment_method"`
	Merchant        *string    `json:"merchant"`
	Notes           *string    `json:"notes"`
	Tags            []string   `json:"tags"`
	LLMComment      *string    `json:"llm_comment"`
	LLMCommentAt    *time.Time `json:"llm_comment_at"`
	CreatedAt       time.Time  `json:"created_at"`
	CategoryName    string     `json:"category_name"`
	CategoryIcon    *string    `json:"category_icon"`
	CategoryColor   *string    `json:"category_color"`
}
