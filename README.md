# CompanyEnrichmentCLI-Codespace
Basic Company Enrichment CLI - GTM 1 - Github Codespaces

# Task
Company Enrichment CLI that
-takes company domain calls external API
-parses JSON
-normalizes data with Pydantic
-calculates ICP score 
-saves results
-handles errors/retries
-includes tests

# Data Flow
domain -> CLI -> API client -> raw JSON -> Pydantic model -> ICP scorer -> save result

# Development Order
1. CLI accepts domain (Complete)
2. HTTP request works (Complete)
3. Inspect API JSON   (Complete)
4. Pydantic Company model [In Progress]
5. Convert API response → Company
6. ICP score modeling function
7. Save JSON/SQLite/Postgres
8. Handle API/network errors
9. Add retries/backoff
10. Unit tests
11. Mock API tests
12. Clean architecture/refactor