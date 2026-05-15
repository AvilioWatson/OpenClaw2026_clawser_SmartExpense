package middleware

import (
	"context"
	"net/http"
	"strings"

	"github.com/smart-expense/backend/internal/auth"
)

type contextKey string

const TelegramIDKey contextKey = "telegram_id"

func Auth(jwtService *auth.JWTService) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			header := r.Header.Get("Authorization")
			if header == "" {
				http.Error(w, `{"error":"missing authorization header"}`, http.StatusUnauthorized)
				return
			}
			parts := strings.SplitN(header, " ", 2)
			if len(parts) != 2 || !strings.EqualFold(parts[0], "bearer") {
				http.Error(w, `{"error":"invalid authorization header"}`, http.StatusUnauthorized)
				return
			}
			telegramID, err := jwtService.Validate(parts[1])
			if err != nil {
				http.Error(w, `{"error":"invalid or expired token"}`, http.StatusUnauthorized)
				return
			}
			ctx := context.WithValue(r.Context(), TelegramIDKey, telegramID)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

func TelegramIDFromContext(ctx context.Context) (int64, bool) {
	id, ok := ctx.Value(TelegramIDKey).(int64)
	return id, ok
}
