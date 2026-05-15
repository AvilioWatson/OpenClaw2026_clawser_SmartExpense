package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/smart-expense/backend/internal/middleware"
	"github.com/smart-expense/backend/internal/models"
)

type TransactionsHandler struct {
	pool *pgxpool.Pool
}

func NewTransactionsHandler(pool *pgxpool.Pool) *TransactionsHandler {
	return &TransactionsHandler{pool: pool}
}

func (h *TransactionsHandler) List(w http.ResponseWriter, r *http.Request) {
	telegramID, ok := middleware.TelegramIDFromContext(r.Context())
	if !ok {
		http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
		return
	}

	rows, err := h.pool.Query(r.Context(), `
		SELECT
			t.id::text,
			t.amount,
			t.type,
			t.description,
			t.transaction_date::text,
			t.payment_method,
			t.merchant,
			t.notes,
			t.tags,
			t.llm_comment,
			t.llm_comment_at,
			t.created_at,
			c.name,
			c.icon,
			c.color
		FROM transactions t
		JOIN categories c ON c.id = t.category_id
		WHERE t.telegram_id = $1
		ORDER BY t.transaction_date DESC, t.created_at DESC
	`, telegramID)
	if err != nil {
		http.Error(w, `{"error":"failed to fetch transactions"}`, http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var transactions []models.Transaction
	for rows.Next() {
		var t models.Transaction
		if err := rows.Scan(
			&t.ID,
			&t.Amount,
			&t.Type,
			&t.Description,
			&t.TransactionDate,
			&t.PaymentMethod,
			&t.Merchant,
			&t.Notes,
			&t.Tags,
			&t.LLMComment,
			&t.LLMCommentAt,
			&t.CreatedAt,
			&t.CategoryName,
			&t.CategoryIcon,
			&t.CategoryColor,
		); err != nil {
			http.Error(w, `{"error":"failed to scan transaction"}`, http.StatusInternalServerError)
			return
		}
		if t.Tags == nil {
			t.Tags = []string{}
		}
		transactions = append(transactions, t)
	}
	if transactions == nil {
		transactions = []models.Transaction{}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(transactions)
}
