# Copilot Development Rules

This document contains important rules and best practices for AI assistants working on this project.

## PowerShell Command Rules

### 1. Command Chaining in PowerShell
**WRONG:** Using `&&` (bash syntax)
```powershell
cd c:\Users\AUKALATC01\Dev\data_orchestration && python test_staging_insert.py
```

**RIGHT:** Using `;` (PowerShell syntax)
```powershell
cd c:\Users\AUKALATC01\Dev\data_orchestration; python test_staging_insert.py
```

**BETTER:** Since we're already in the correct working directory, just run:
```powershell
python test_staging_insert.py
```

### 2. Working Directory Awareness
- The run_in_terminal tool already sets the working directory to `c:\Users\AUKALATC01\Dev\data_orchestration`
- No need to change directories unless specifically required
- Check the context to see current working directory before adding `cd` commands

## File Organization Rules

### 3. Test File Placement
**WRONG:** Creating test files in the root folder
```
data_orchestration/
├── test_staging_insert.py     ❌ Don't do this
├── simple_db_test.py          ❌ Don't do this  
├── debug_script.py            ❌ Don't do this
└── ...
```

**RIGHT:** Creating test files in appropriate directories
```
data_orchestration/
├── tests/
│   ├── debug/
│   │   ├── test_staging_insert.py    ✅ Good
│   │   └── simple_db_test.py         ✅ Good
│   └── unit/
└── temp/
    └── debug_scripts/                ✅ Alternative for temporary files
```

### 4. Temporary File Management
- Use `tests/debug/` for debugging scripts that might be useful later
- Use `temp/` for truly temporary files that can be deleted
- Never clutter the root directory with test/debug files
- Clean up temporary files after use

## Development Best Practices

### 5. Error Handling
- Always check for existing functionality before creating new code
- Verify database connections and environment setup before testing
- Use proper error handling and informative error messages

### 6. Code Reuse
- Check existing modules for functionality before duplicating code
- Use existing database connection logic rather than creating new connections
- Import and reuse transformation functions rather than rewriting them

## Project-Specific Rules

### 7. Database Operations
- Always use the existing `order_queries.py` connection logic
- Check environment variables are properly configured before running DB tests
- Use the established pattern for error handling in database operations

### 8. Testing Strategy
- Create focused, single-purpose test scripts
- Test one component at a time
- Include proper cleanup and error handling
- Document what each test is checking

---

**Remember:** These rules exist to maintain code quality and project organization. Follow them consistently to avoid repeating common mistakes.
