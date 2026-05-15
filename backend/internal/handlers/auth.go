package handlers

import (
	"encoding/json"
	"errors"
	"net/http"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/smart-expense/backend/internal/auth"
	"github.com/smart-expense/backend/internal/models"
)

type AuthHandler struct {
	pool       *pgxpool.Pool
	jwtService *auth.JWTService
}

func NewAuthHandler(pool *pgxpool.Pool, jwtService *auth.JWTService) *AuthHandler {
	return &AuthHandler{pool: pool, jwtService: jwtService}
}

func (h *AuthHandler) Login(w http.ResponseWriter, r *http.Request) {
	var req models.LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, `{"error":"invalid request body"}`, http.StatusBadRequest)
		return
	}
	if req.Token == "" {
		http.Error(w, `{"error":"token is required"}`, http.StatusBadRequest)
		return
	}

	tx, err := h.pool.Begin(r.Context())
	if err != nil {
		http.Error(w, `{"error":"failed to start transaction"}`, http.StatusInternalServerError)
		return
	}
	defer tx.Rollback(r.Context())

	var telegramID int64
	err = tx.QueryRow(r.Context(),
		`SELECT telegram_id FROM tokens WHERE token = $1 FOR UPDATE`, req.Token,
	).Scan(&telegramID)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			http.Error(w, `{"error":"invalid token"}`, http.StatusUnauthorized)
			return
		}
		http.Error(w, `{"error":"failed to validate token"}`, http.StatusInternalServerError)
		return
	}

	accessToken, expiresIn, err := h.jwtService.Sign(telegramID)
	if err != nil {
		http.Error(w, `{"error":"failed to issue token"}`, http.StatusInternalServerError)
		return
	}

	_, err = tx.Exec(r.Context(), `DELETE FROM tokens WHERE token = $1`, req.Token)
	if err != nil {
		http.Error(w, `{"error":"failed to consume token"}`, http.StatusInternalServerError)
		return
	}

	if err := tx.Commit(r.Context()); err != nil {
		http.Error(w, `{"error":"failed to commit transaction"}`, http.StatusInternalServerError)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(models.LoginResponse{
		AccessToken: accessToken,
		TokenType:   "bearer",
		ExpiresIn:   expiresIn,
	})
}
