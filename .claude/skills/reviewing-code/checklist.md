# Code Review Checklist

## Security
- [ ] No hardcoded secrets, tokens, or passwords
- [ ] User input validated and sanitized
- [ ] SQL queries parameterized (no string concatenation)
- [ ] HTML output escaped (no XSS vectors)
- [ ] Auth checks present on protected endpoints
- [ ] No sensitive data in logs or error messages
- [ ] File uploads validated (type, size, name)

## Correctness
- [ ] Logic handles edge cases (empty, null, boundary values)
- [ ] Error cases handled explicitly (not swallowed or ignored)
- [ ] Async operations handle rejection/timeout
- [ ] Database transactions used for multi-step operations
- [ ] Race conditions considered for concurrent operations
- [ ] Cleanup happens on error paths (connections, files, locks)

## Testing
- [ ] New logic has corresponding tests
- [ ] Edge cases have tests
- [ ] Error paths have tests
- [ ] Tests are deterministic (no flaky dependencies)
- [ ] Test names describe behavior, not implementation
- [ ] Mocks are appropriate (external deps, not internal)

## Performance
- [ ] No N+1 query patterns
- [ ] Large lists use pagination
- [ ] Expensive operations cached appropriately
- [ ] No synchronous operations that should be async
- [ ] Query count verified with assertNumQueries

## Conventions
- [ ] File naming matches project pattern
- [ ] Code organization matches project structure
- [ ] Error handling follows project pattern (Response + status code)
- [ ] Tests follow project testing patterns (T-NNN IDs, factory fixtures)
- [ ] Imports grouped: stdlib → django → rest_framework → local

## Maintainability
- [ ] No dead code or commented-out code
- [ ] No TODOs without context or tracking
- [ ] Complex logic has explanatory comments
- [ ] Functions are focused (single responsibility)
- [ ] No magic numbers — use named constants
- [ ] Dependencies are justified (not added frivolously)
