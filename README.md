# CompanyEnrichmentCLI-Codespace
Basic Company Enrichment CLI - GTM 1 - Github Codespaces

# Task
Company Enrichment CLI that<br>
-takes company domain calls external API<br>
-parses JSON<br>
-normalizes data with Pydantic<br>
-calculates ICP score<br>
-saves results<br>
-handles errors/retries<br>
-includes tests<br>

# Data Flow
domain -> CLI -> API client -> raw JSON -> Pydantic model -> ICP scorer -> save result

# Development Tasks
1. CLI accepts domain ✅<br>
2. HTTP request works ✅<br>
3. Inspect API JSON   ✅<br>
4. Pydantic Company model ✅<br>
5. Convert API response → Company ✅<br>
6. ICP score modeling function ✅<br>
7. Save data to JSON & CSV ✅<br>4
8. Handle API/network errors ✅<br>
9. Add retries/backoff ✅<br>
10. Unit tests ✅<br>
11. Mock API tests ✅<br>
12. Clean architecture/refactor <br>

