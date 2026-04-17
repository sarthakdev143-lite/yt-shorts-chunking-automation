# AGENT.md

## Overview

This repository is developed with the assistance of AI coding agents.
This document defines how the agent should behave, how code should be written, and the Git workflow that must be followed after completing tasks.

The agent must behave like a **responsible software engineer**, not a code generator.

---

# Agent Behavior Rules

## Understand Before Writing Code

Before writing or modifying code, the agent must:

1. Read relevant files
2. Understand project structure
3. Identify dependencies
4. Identify coding patterns
5. Plan changes
6. Then implement

The agent must **never blindly generate full files without context**.

---

# Coding Principles

## General Rules

* Keep code simple and readable
* Avoid overengineering
* Avoid duplicate logic
* Prefer small functions
* Use meaningful names
* Follow existing code style
* Do not create very large files
* Do not introduce unnecessary dependencies

---

# Naming Conventions

## Variables

camelCase

## Classes

PascalCase

## Constants

UPPER_SNAKE_CASE

## Files

kebab-case

---

# File Modification Rules

The agent should:

* Modify existing files instead of creating duplicates
* Not rename files unless necessary
* Not delete code unless sure it is unused
* Not commit secrets or API keys
* Not change environment configs unless required

---

# Security Rules

The agent must ensure:

* Passwords are hashed
* Tokens are secure
* No secrets in frontend
* Input validation exists
* Environment variables are used
* Encryption used where required

Never expose:

```
API_KEYS
JWT_SECRET
DATABASE_URL
PRIVATE_KEYS
```

---

# Performance Rules

The agent should:

* Avoid unnecessary API calls
* Optimize database queries
* Use pagination for large data
* Use caching where useful
* Lazy load heavy components
* Compress large assets

---

# Documentation Rules

When adding a new feature, the agent must:

1. Update README if needed
2. Add comments to complex logic
3. Document API endpoints
4. Document environment variables
5. Update architecture docs if structure changes

---

# Testing Rules

When adding logic:

* Test edge cases
* Test invalid input
* Test empty states
* Test error handling
* Add unit tests if test framework exists

---

# Git Workflow (VERY IMPORTANT)

## Branch Strategy

The agent must follow this branching model:

```
main        -> production code
dev         -> integration branch
feature/*   -> new features
fix/*       -> bug fixes
refactor/*  -> refactoring
```

---

## Workflow Steps For Every Task

When the agent completes a task, it must follow this workflow:

```
1. Pull latest dev branch
2. Create new branch
3. Make changes
4. Commit with proper message
5. Push branch
6. Create Pull Request to dev
```

---

## Branch Naming Rules

```
feature/login-system
feature/diary-encryption
fix/login-bug
fix/token-expiry
refactor/api-structure
refactor/database-layer
```

---

# Commit Message Format

## Format

```
type(scope): short description
```

## Examples

```
feat(auth): add jwt authentication
feat(diary): add entry encryption
fix(api): fix login response bug
refactor(db): move queries to repository layer
docs(readme): update installation steps
ui(home): improve landing page layout
```

---

## Allowed Commit Types

| Type        | Meaning                 |
| ----------- | ----------------------- |
| feat        | New feature             |
| fix         | Bug fix                 |
| refactor    | Code restructuring      |
| docs        | Documentation           |
| style       | Formatting              |
| ui          | UI changes              |
| test        | Tests                   |
| performance | Performance improvement |
| chore       | Maintenance             |

---

# Example Git Workflow (Step by Step)

```
git checkout dev
git pull origin dev

git checkout -b feature/diary-encryption

# make changes

git add .
git commit -m "feat(diary): add encryption for diary entries"

git push origin feature/diary-encryption
```

Then create Pull Request:

```
feature/diary-encryption -> dev
```

---

# When Agent Must Ask Before Acting

The agent must ask before continuing if:

* Database schema change required
* Authentication logic change required
* Large refactor required
* New major dependency required
* Deleting files
* Changing environment variables
* Changing project architecture

---

# What The Agent Must Never Do

The agent must never:

1. Delete database data
2. Expose secrets
3. Rewrite entire project without instruction
4. Change authentication logic without approval
5. Add unnecessary dependencies
6. Create massive files (>1000 lines)
7. Hardcode credentials
8. Push directly to main branch
9. Skip Git workflow
10. Commit broken code

---

# Ideal Workflow For Agent (Summary)

```
1. Understand task
2. Explore repository
3. Locate relevant files
4. Plan changes
5. Implement minimal changes
6. Test logic mentally
7. Update docs if needed
8. Create branch
9. Commit properly
10. Push and create PR
11. Write summary of changes
```

---

# Agent Response Format After Task

The agent should respond in this format after completing tasks:

```
## Summary
What was changed

## Files Modified
List of files

## Branch Name
feature/xyz

## Commit Message
feat(module): description

## Risks
Possible side effects

## Next Steps
What should be done next
```

---

# Final Rule

The agent is responsible for the **long-term health of the project**.

Priority order:

1. Maintainability
2. Security
3. Performance
4. Readability
5. Scalability
6. Then speed of development
