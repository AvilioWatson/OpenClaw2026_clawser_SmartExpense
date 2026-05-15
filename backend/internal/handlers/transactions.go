package handlers

import (
	"encoding/json"
	"net/http"
	"strconv"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/smart-expense/backend/internal/middleware"
	"github.com/smart-expense/backend/internal/models"
)

const transactionSelectCols = `
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
`

type TransactionsHandler struct {
	pool *pgxpool.Pool
}

func NewTransactionsHandler(pool *pgxpool.Pool) *TransactionsHandler {
	return &TransactionsHandler{pool: pool}
}

func (h *TransactionsHandler) writeFilterError(w http.ResponseWriter, err error) {
	http.Error(w, `{"error":"`+err.Error()+`"}`, http.StatusBadRequest)
}

func (h *TransactionsHandler) List(w http.ResponseWriter, r *http.Request) {
	telegramID, ok := middleware.TelegramIDFromContext(r.Context())
	if !ok {
		http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
		return
	}

	filters, err := parseTransactionFilters(r)
	if err != nil {
		h.writeFilterError(w, err)
		return
	}

	where, args := filters.buildWhere(telegramID)

	var total int
	countSQL := `SELECT COUNT(*) FROM transactions t JOIN categories c ON c.id = t.category_id WHERE ` + where
	if err := h.pool.QueryRow(r.Context(), countSQL, args...).Scan(&total); err != nil {
		http.Error(w, `{"error":"failed to count transactions"}`, http.StatusInternalServerError)
		return
	}

	listSQL := `SELECT ` + transactionSelectCols + `
		FROM transactions t
		JOIN categories c ON c.id = t.category_id
		WHERE ` + where + `
		` + filters.orderClause() + `
		LIMIT $` + strconv.Itoa(len(args)+1) + ` OFFSET $` + strconv.Itoa(len(args)+2)

	args = append(args, filters.limit, filters.offset)

	rows, err := h.pool.Query(r.Context(), listSQL, args...)
	if err != nil {
		http.Error(w, `{"error":"failed to fetch transactions"}`, http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	items, err := scanTransactions(rows)
	if err != nil {
		http.Error(w, `{"error":"failed to scan transaction"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(models.TransactionListResponse{
		Items:  items,
		Total:  total,
		Limit:  filters.limit,
		Offset: filters.offset,
	})
}

func (h *TransactionsHandler) Summary(w http.ResponseWriter, r *http.Request) {
	telegramID, ok := middleware.TelegramIDFromContext(r.Context())
	if !ok {
		http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
		return
	}

	filters, err := parseTransactionFilters(r)
	if err != nil {
		h.writeFilterError(w, err)
		return
	}

	where, args := filters.buildWhere(telegramID)

	var summary models.TransactionSummary
	err = h.pool.QueryRow(r.Context(), `
		SELECT
			COALESCE(SUM(CASE WHEN t.type = 'income' THEN t.amount ELSE 0 END), 0),
			COALESCE(SUM(CASE WHEN t.type = 'expense' THEN t.amount ELSE 0 END), 0),
			COUNT(*)
		FROM transactions t
		JOIN categories c ON c.id = t.category_id
		WHERE `+where, args...).Scan(&summary.TotalIncome, &summary.TotalExpense, &summary.Count)
	if err != nil {
		http.Error(w, `{"error":"failed to fetch summary"}`, http.StatusInternalServerError)
		return
	}
	summary.Net = summary.TotalIncome - summary.TotalExpense

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(summary)
}

func (h *TransactionsHandler) ByCategory(w http.ResponseWriter, r *http.Request) {
	telegramID, ok := middleware.TelegramIDFromContext(r.Context())
	if !ok {
		http.Error(w, `{"error":"unauthorized"}`, http.StatusUnauthorized)
		return
	}

	filters, err := parseTransactionFilters(r)
	if err != nil {
		h.writeFilterError(w, err)
		return
	}

	where, args := filters.buildWhere(telegramID)

	rows, err := h.pool.Query(r.Context(), `
		SELECT c.name, c.icon, c.color, t.type, COALESCE(SUM(t.amount), 0)
		FROM transactions t
		JOIN categories c ON c.id = t.category_id
		WHERE `+where+`
		GROUP BY c.id, c.name, c.icon, c.color, t.type
		ORDER BY SUM(t.amount) DESC
	`, args...)
	if err != nil {
		http.Error(w, `{"error":"failed to fetch breakdown"}`, http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var breakdown []models.CategoryBreakdown
	for rows.Next() {
		var b models.CategoryBreakdown
		if err := rows.Scan(&b.CategoryName, &b.CategoryIcon, &b.CategoryColor, &b.Type, &b.Total); err != nil {
			http.Error(w, `{"error":"failed to scan breakdown"}`, http.StatusInternalServerError)
			return
		}
		breakdown = append(breakdown, b)
	}
	if breakdown == nil {
		breakdown = []models.CategoryBreakdown{}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(breakdown)
}
