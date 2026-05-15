package handlers

import (
	"encoding/json"
	"net/http"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/smart-expense/backend/internal/models"
)

type CategoriesHandler struct {
	pool *pgxpool.Pool
}

func NewCategoriesHandler(pool *pgxpool.Pool) *CategoriesHandler {
	return &CategoriesHandler{pool: pool}
}

func (h *CategoriesHandler) List(w http.ResponseWriter, r *http.Request) {
	rows, err := h.pool.Query(r.Context(), `
		SELECT id, name, type, icon, color, description, display_order
		FROM categories
		WHERE is_active = true
		ORDER BY display_order, name
	`)
	if err != nil {
		http.Error(w, `{"error":"failed to fetch categories"}`, http.StatusInternalServerError)
		return
	}
	defer rows.Close()

	var categories []models.Category
	for rows.Next() {
		var c models.Category
		if err := rows.Scan(&c.ID, &c.Name, &c.Type, &c.Icon, &c.Color, &c.Description, &c.DisplayOrder); err != nil {
			http.Error(w, `{"error":"failed to scan category"}`, http.StatusInternalServerError)
			return
		}
		categories = append(categories, c)
	}
	if categories == nil {
		categories = []models.Category{}
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(categories)
}
