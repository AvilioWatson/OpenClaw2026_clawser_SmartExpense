package handlers

import (
	"github.com/jackc/pgx/v5"
	"github.com/smart-expense/backend/internal/models"
)

func scanTransactions(rows pgx.Rows) ([]models.Transaction, error) {
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
			return nil, err
		}
		if t.Tags == nil {
			t.Tags = []string{}
		}
		transactions = append(transactions, t)
	}
	if transactions == nil {
		transactions = []models.Transaction{}
	}
	return transactions, nil
}
