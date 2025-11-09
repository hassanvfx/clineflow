# Working with Cline AI Assistant

This guide explains how to work effectively with Cline AI Assistant on the Jabaliweb project.

## Table of Contents
- [File Visibility Issues](#file-visibility-issues)
- [Component Size Guidelines](#component-size-guidelines)
- [Journal System](#journal-system)
- [Intelligent Commit Workflow](#intelligent-commit-workflow)
- [Documentation Patterns](#documentation-patterns)
- [Code Quality Standards](#code-quality-standards)
- [Reference Repository Access](#reference-repository-access)

---

## File Visibility Issues

### The Problem
Files in `clineflow/` are gitignored to prevent nested git repositories. This means Cline **cannot see these files** through:
- @ mentions in chat
- File explorer
- Automatic file discovery

### The Solution
**Use direct file paths** when asking Cline to read these files:

```markdown
# ❌ This won't work:
@clineflow/companions-api/README.md

# ✅ This works:
Can you read clineflow/companions-api/README.md?
```

### Quick Reference Index
Use `clineflow/index.json` to see all available backend reference files and their paths.

---

## Component Size Guidelines

### The Rule
- **Ideal:** Components should be less than 500 lines of code (LOC)
- **Maximum:** 2,000 LOC is completely unacceptable
- **Action:** Break down components that exceed limits

### Why This Matters
1. **Maintainability:** Smaller components are easier to understand and modify
2. **Reusability:** Well-factored components can be reused across the app
3. **Testing:** Smaller components are easier to test
4. **Performance:** Easier to optimize and debug

### How to Modularize
```typescript
// ❌ BAD: 2,000 line monolithic component
function MassiveComponent() {
  // Everything in one place
}

// ✅ GOOD: Broken into focused pieces
function ParentComponent() {
  return (
    <>
      <HeaderSection />
      <ContentSection />
      <FooterSection />
    </>
  );
}
```

### Examples
See these well-modularized components:
- `src/app/charsimlite/components/ParticipantCountBadge.tsx` (~100 LOC)
- `src/app/charsimlite/components/SystemMessageBubble.tsx` (~80 LOC)

---

## Journal System

### When to Create Journals
Create a task journal in `docs/journals/[task-name].md` for:
- Features that will take multiple sessions
- Complex implementations with many moving parts
- Features with multiple phases
- Work that requires tracking decisions and progress

### Journal Template
Use `clineflow/JOURNAL_TEMPLATE.md` as your starting point.

### Structure (Based on INVITE_FLOW_STATUS.md)

```markdown
# [Feature Name] Implementation Journal

## Overview
Brief description of the feature and its goals.

## Status Overview

### Phase 1: [Name] - [Status: ✅/🔧/❌]
- [x] Completed task
- [ ] Pending task
- [ ] Another pending task

### Phase 2: [Name] - [Status]
...

## Journal Entries

### YYYY-MM-DD HH:MM - Entry Title
**What Changed:**
- Detail 1
- Detail 2

**Why:**
Explanation of decisions made.

**Next Steps:**
- Action item 1
- Action item 2

---

### YYYY-MM-DD HH:MM - Another Entry
...

## Known Issues

### Issue Name
**Problem:** Description of the problem
**Root Cause:** What's causing it
**Status:** Being investigated / Blocked / Fixed
**Workaround:** Temporary solution if any

## Quick Reference

### Key Files
- `path/to/file.ts` - Purpose
- `path/to/another.ts` - Purpose

### Important Commands
```bash
npm run dev
```

### Backend API
- Endpoint details
- Data schemas
```

### Best Practices

1. **Update Frequently:** Add entries as you make progress
2. **Be Specific:** Include file names, line numbers, and code snippets
3. **Document Decisions:** Explain WHY you chose an approach
4. **Track Blockers:** Note what's blocking progress
5. **Use for Context:** When creating a new task, reference the journal

### Using Journals with New Tasks

When a task gets too large, create a new task with context from the journal:

```markdown
# Current Work
As documented in docs/journals/invite-flow.md, we completed Phase 1
(invite link generation and join flow) and Phase 2 (UI enhancements).

# Next Task
We're now starting Phase 3: Guest Discovery & Login Conversion.
See journal for complete history.
```

---

## Intelligent Commit Workflow

### The Magic Command

When you're ready to commit your changes, simply say:
- `"commit changes"`
- `"commit"`
- `"please commit"`

**That's it!** I'll handle everything automatically.

### What Happens Automatically

1. **📝 Generate Journal Entry**
   - I use our full conversation context
   - Create a meaningful entry explaining what was done and why
   - Include technical decisions and file changes

2. **📁 Update Journal**
   - Append the entry to your active journal in `docs/journals/`
   - Maintain proper formatting and structure

3. **🎯 Stage Everything**
   - Stage all your code changes
   - Stage the updated journal file

4. **💬 Create Commit Message**
   - Generate descriptive commit message with proper format
   - Include clear bullet points of key changes

5. **✅ Execute Commit**
   - Run `git commit` with the generated message
   - Confirm completion with commit details

### Example Workflow

```markdown
You: "I've finished implementing the user auth flow"
[... work on code ...]
You: "commit changes"

Me: ✅ Committed changes with journal entry to docs/journals/user-auth.md

### 2025-11-08 15:30 - Implemented User Authentication Flow

**Achievement:**
Successfully implemented complete user authentication system with login,
registration, and session management.

**Implementation Details:**
- Created `src/app/auth/LoginForm.tsx` - Login component with validation
- Created `src/app/auth/AuthProvider.tsx` - Context provider for auth state
- Modified `src/app/App.tsx` - Added auth routing logic
- Created `src/app/services/authAPI.ts` - API integration layer

**Technical Decisions:**
Chose JWT tokens over session cookies for better scalability with mobile app.
Implemented refresh token rotation for enhanced security.

**Files Changed:**
- `src/app/auth/LoginForm.tsx` - [+150 lines]
- `src/app/auth/AuthProvider.tsx` - [+80 lines]
- `src/app/App.tsx` - [+30 -10 lines]
- `src/app/services/authAPI.ts` - [+120 lines]

**Next Steps:**
- [ ] Add password reset functionality
- [ ] Implement email verification
- [ ] Add social login options

**Status:** Complete

---

Commit: abc1234
feat(auth): implement user authentication flow

- Create login/registration forms with validation
- Add JWT token management with refresh rotation
- Integrate auth context provider
- Connect to backend auth API endpoints
```

### Benefits

🎯 **Context-Aware**: Journal entries are meaningful, not just file lists

🎯 **Time-Saving**: No manual journal updates or commit message writing

🎯 **Consistent**: All commits have proper documentation automatically

🎯 **Historical Record**: Every commit has a corresponding journal entry

### Multi-Task Journal Pattern

When continuing work across multiple tasks, I automatically maintain the journal structure:

```markdown
# Feature - Implementation Journal Index

## Task History
- **Task 1** (2025-11-08): Initial implementation - [Details](#task-1)
- **Task 2** (2025-11-08): Bug fixes - [Details](#task-2) ← Added automatically

## Current Status
[Updated from latest task]

---

## Task 1 - Initial Implementation
[Original journal entries]

---

## Task 2 - Bug Fixes ← New section added automatically
### 2025-11-08 16:00 - Fixed Authentication Bugs
[Detailed entry...]
```

### Requirements

**You MUST have an active journal** before using intelligent commit:
- For new tasks: Create `docs/journals/[task-name].md` first
- For continuations: Use existing journal

If no journal exists, I'll prompt you to create one.

### Technical Details

See `clineflow/PROCEDURES.md` SOP-005 for complete implementation details.

---

## Documentation Patterns

### Follow Existing Examples

Study these well-documented features:
- `docs/INVITE_FLOW.md` - Detailed feature specification
- `docs/INVITE_FLOW_STATUS.md` - Implementation journal
- `docs/INVITE_FLOW_USERNAME_ISSUE.md` - Issue tracking

### Documentation Structure

**For New Features:**
1. **Specification Document** (`docs/[FEATURE].md`)
   - Overview
   - Requirements
   - Implementation plan
   - API contracts
   - UX flows

2. **Status Document** (`docs/[FEATURE]_STATUS.md`)
   - Implementation progress
   - Journal entries
   - Known issues
   - Quick reference

3. **Issue Documents** (`docs/[FEATURE]_[ISSUE].md`)
   - For specific problems requiring investigation

### Documentation Style

- Use emojis for visual scanning (✅ ❌ 🔧 ⚠️ 📝)
- Include code snippets with syntax highlighting
- Add visual diagrams for complex flows
- Keep "Quick Reference" sections for common tasks
- Update status regularly

---

## Code Quality Standards

### No Unnecessary Code
Every line of code should serve a specific purpose related to the component's function.

```typescript
// ❌ BAD: Unused imports and dead code
import { useState, useEffect, useMemo } from 'react';
import { someUnusedUtil } from './utils';

function MyComponent() {
  const [unusedState, setUnusedState] = useState(false);
  
  // Dead code that never executes
  if (false) {
    console.log('This never runs');
  }
  
  return <div>Hello</div>;
}

// ✅ GOOD: Clean, purposeful code
import { useState } from 'react';

function MyComponent() {
  const [count, setCount] = useState(0);
  
  return (
    <div>
      <p>Count: {count}</p>
      <button onClick={() => setCount(count + 1)}>
        Increment
      </button>
    </div>
  );
}
```

### Component-Specific Code Only
Don't add features "just in case" - only implement what's needed now.

```typescript
// ❌ BAD: Over-engineered with unused features
interface UserCardProps {
  user: User;
  onEdit?: () => void;        // Not used
  onDelete?: () => void;      // Not used
  showActions?: boolean;      // Not used
  variant?: 'compact' | 'full'; // Not needed
}

// ✅ GOOD: Implements only what's needed
interface UserCardProps {
  user: User;
}
```

### TypeScript Best Practices
- Use proper types, avoid `any`
- Define interfaces for component props
- Use type inference where appropriate

---

## Reference Repository Access

### Available References
See `clineflow/index.json` for the complete list of cloned reference repositories.

### Companions API (Backend Reference)
The main backend reference is cloned at `clineflow/companions-api/`.

**Key Files:**
```
clineflow/companions-api/
├── README.md                  # API overview
├── src/jabali/
│   ├── routers/
│   │   ├── threads.py        # Thread endpoints
│   │   └── participants.py   # Participant endpoints
│   └── schemas/
│       ├── threads.py        # Thread data models
│       └── participants.py   # Participant data models
```

### How to Ask Cline to Read Backend Files

```markdown
# Example request:
Can you read clineflow/companions-api/src/jabali/routers/participants.py
to see how the participant endpoints are implemented?
```

### Cloning Fresh References

```bash
cd clineflow
./clone-refs.sh
```

This script:
- Clones all repositories listed in `index.json`
- Uses shallow clones (`--depth 1`) to save space
- Skips already-cloned repos
- Always removes and re-clones for fresh copy

---

## Working with Large Tasks

### Task Size Management

When a task becomes too large (Context window approaching limits):

1. **Create a Journal:** Document progress in `docs/journals/[task].md`
2. **Summarize State:** Write a comprehensive summary of:
   - What's been completed
   - What's remaining
   - Key technical decisions
   - Important file locations
3. **Create New Task:** Use the journal as context for continuation
4. **Include Verbatim Quotes:** Copy exact text from conversations to preserve context

### Example Workflow

```markdown
# Task 1: Initial Implementation
1. Created docs/journals/invite-flow.md
2. Implemented Phase 1 (core functionality)
3. Documented progress in journal
4. Context window at 80%

# Task 2: Continuation
1. Loaded context from docs/journals/invite-flow.md
2. Implemented Phase 2 (UI enhancements)
3. Updated journal with new progress
4. Ready for Phase 3
```

---

## Cline-Specific Tips

### Plan Mode vs Act Mode
- **Plan Mode:** Used for discussion, planning, and gathering requirements
- **Act Mode:** Used for actual code changes and file operations

### Tool Usage
- Read files before modifying them
- Use `replace_in_file` for targeted edits
- Use `write_to_file` for new files or complete rewrites
- Wait for confirmation after each tool use

### Communication Style
- Be direct and technical
- Don't start with "Great" or "Certainly"
- Provide clear explanations with code examples
- Focus on accomplishing the task efficiently

---

## Getting Help

### For Feature Questions
1. Check existing documentation in `docs/`
2. Review similar implemented features
3. Check backend API reference in `clineflow/companions-api/`

### For Technical Issues
1. Check if issue is documented in `docs/[FEATURE]_ISSUE.md` files
2. Review journal entries for similar problems
3. Check git history for related changes

### For Cline Behavior
- This document explains Cline's limitations
- Use `.clinerules` for quick reference
- See `clineflow/PROCEDURES.md` for detailed procedures

---

**Last Updated:** November 8, 2025
