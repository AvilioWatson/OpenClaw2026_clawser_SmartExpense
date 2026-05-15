package handlers

import (
	"fmt"
	"net/http"
	"strconv"
	"strings"
	"time"
)

const (
	defaultLimit = 50
	maxLimit     = 200
)

type transactionFilters struct {
	from       *time.Time
	to         *time.Time
	txType     string
	categoryID string
	query      string
	sort       string
	order      string
	limit      int
	offset     int
}

func parseTransactionFilters(r *http.Request) (transactionFilters, error) {
	q := r.URL.Query()
	f := transactionFilters{
		sort:   "transaction_date",
		order:  "desc",
		limit:  defaultLimit,
		offset: 0,
	}

	if yearStr := q.Get("year"); yearStr != "" {
		year, err := strconv.Atoi(yearStr)
		if err != nil || year < 1970 || year > 2100 {
			return f, fmt.Errorf("invalid year")
		}
		month := 0
		if monthStr := q.Get("month"); monthStr != "" {
			month, err = strconv.Atoi(monthStr)
			if err != nil || month < 1 || month > 12 {
				return f, fmt.Errorf("invalid month")
			}
		}
		if month > 0 {
			start := time.Date(year, time.Month(month), 1, 0, 0, 0, 0, time.UTC)
			end := start.AddDate(0, 1, -1)
			f.from = &start
			f.to = &end
		} else {
			start := time.Date(year, 1, 1, 0, 0, 0, 0, time.UTC)
			end := time.Date(year, 12, 31, 0, 0, 0, 0, time.UTC)
			f.from = &start
			f.to = &end
		}
	} else {
		if fromStr := q.Get("from"); fromStr != "" {
			t, err := time.Parse("2006-01-02", fromStr)
			if err != nil {
				return f, fmt.Errorf("invalid from date")
			}
			f.from = &t
		}
		if toStr := q.Get("to"); toStr != "" {
			t, err := time.Parse("2006-01-02", toStr)
			if err != nil {
				return f, fmt.Errorf("invalid to date")
			}
			f.to = &t
		}
	}

	if f.from != nil && f.to != nil && f.from.After(*f.to) {
		return f, fmt.Errorf("from date must be before to date")
	}

	if t := q.Get("type"); t != "" {
		if t != "income" && t != "expense" {
			return f, fmt.Errorf("invalid type")
		}
		f.txType = t
	}

	f.categoryID = q.Get("category_id")
	f.query = strings.TrimSpace(q.Get("q"))

	if sort := q.Get("sort"); sort != "" {
		switch sort {
		case "transaction_date", "amount", "category_name", "created_at":
			f.sort = sort
		default:
			return f, fmt.Errorf("invalid sort")
		}
	}

	if order := q.Get("order"); order != "" {
		switch strings.ToLower(order) {
		case "asc", "desc":
			f.order = strings.ToLower(order)
		default:
			return f, fmt.Errorf("invalid order")
		}
	}

	if limitStr := q.Get("limit"); limitStr != "" {
		limit, err := strconv.Atoi(limitStr)
		if err != nil || limit < 1 {
			return f, fmt.Errorf("invalid limit")
		}
		if limit > maxLimit {
			limit = maxLimit
		}
		f.limit = limit
	}

	if offsetStr := q.Get("offset"); offsetStr != "" {
		offset, err := strconv.Atoi(offsetStr)
		if err != nil || offset < 0 {
			return f, fmt.Errorf("invalid offset")
		}
		f.offset = offset
	}

	return f, nil
}

func (f transactionFilters) buildWhere(telegramID int64) (string, []interface{}) {
	conds := []string{"t.telegram_id = $1"}
	args := []interface{}{telegramID}
	n := 2

	if f.from != nil {
		conds = append(conds, fmt.Sprintf("t.transaction_date >= $%d", n))
		args = append(args, f.from.Format("2006-01-02"))
		n++
	}
	if f.to != nil {
		conds = append(conds, fmt.Sprintf("t.transaction_date <= $%d", n))
		args = append(args, f.to.Format("2006-01-02"))
		n++
	}
	if f.txType != "" {
		conds = append(conds, fmt.Sprintf("t.type = $%d", n))
		args = append(args, f.txType)
		n++
	}
	if f.categoryID != "" {
		conds = append(conds, fmt.Sprintf("t.category_id = $%d::uuid", n))
		args = append(args, f.categoryID)
		n++
	}
	if f.query != "" {
		conds = append(conds, fmt.Sprintf("(t.merchant ILIKE $%d OR t.description ILIKE $%d)", n, n))
		args = append(args, "%"+f.query+"%")
	}

	return strings.Join(conds, " AND "), args
}

func (f transactionFilters) orderClause() string {
	col := "t.transaction_date"
	switch f.sort {
	case "amount":
		col = "t.amount"
	case "category_name":
		col = "c.name"
	case "created_at":
		col = "t.created_at"
	}
	order := "DESC"
	if f.order == "asc" {
		order = "ASC"
	}
	if f.sort == "transaction_date" {
		return fmt.Sprintf("ORDER BY %s %s, t.created_at DESC", col, order)
	}
	return fmt.Sprintf("ORDER BY %s %s", col, order)
}
