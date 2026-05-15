package config

import (
	"fmt"
	"os"
	"time"
)

type Config struct {
	DatabaseURL string
	JWTSecret   string
	JWTTTL      time.Duration
	Port        string
	CORSOrigin  string
}

func Load() (*Config, error) {
	dbURL := os.Getenv("DATABASE_URL")
	if dbURL == "" {
		dbURL = "postgres://postgres:pg123@localhost:5432/smart_expense?sslmode=disable"
	}

	jwtSecret := os.Getenv("JWT_SECRET")
	if jwtSecret == "" {
		jwtSecret = "dev-secret-change-in-production-min-32-chars"
	}
	if len(jwtSecret) < 32 {
		return nil, fmt.Errorf("JWT_SECRET must be at least 32 characters")
	}

	jwtTTL := 24 * time.Hour
	if v := os.Getenv("JWT_TTL"); v != "" {
		d, err := time.ParseDuration(v)
		if err != nil {
			return nil, fmt.Errorf("invalid JWT_TTL: %w", err)
		}
		jwtTTL = d
	}

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	corsOrigin := os.Getenv("CORS_ORIGIN")
	if corsOrigin == "" {
		corsOrigin = "http://localhost:5173"
	}

	return &Config{
		DatabaseURL: dbURL,
		JWTSecret:   jwtSecret,
		JWTTTL:      jwtTTL,
		Port:        port,
		CORSOrigin:  corsOrigin,
	}, nil
}
