# System Procedures for Working with Cline

This document contains detailed system rules and standard operating procedures for Cline AI Assistant working on the Jabaliweb project.

## Table of Contents
- [Component Development Standards](#component-development-standards)
- [Journal System Procedures](#journal-system-procedures)
- [Documentation Requirements](#documentation-requirements)
- [Code Quality Guidelines](#code-quality-guidelines)
- [File Access Procedures](#file-access-procedures)
- [Task Management](#task-management)

---

## Component Development Standards

### Size Requirements

**Absolute Rules:**
- Components MUST be less than 500 lines of code (LOC) ideally
- Components over 2,000 LOC are **completely unacceptable**
- When reviewing/creating components, always check line count
- If a component exceeds limits, it MUST be broken down

### Modularization Strategy

**When to Break Down Components:**
1. Component exceeds 500 LOC
2. Component has multiple distinct responsibilities
3. Logic can be reused elsewhere
4. Testing becomes difficult

**How to Modularize:**

```typescript
// Pattern 1: Extract Sub-Components
function LargeComponent() {
  return (
    <Container>
      <HeaderSection />
      <MainContent />
      <FooterSection />
    </Container>
  );
}

// Pattern 2: Extract Custom Hooks
function useComponentLogic() {
  const [state, setState] = useState();
  // Complex logic here
  return { state, actions };
}

function Component() {
  const { state, actions } = useComponentLogic();
  return <div>...</div>;
}

// Pattern 3: Extract Utility Functions
// Move to utils/ directory
export function complexCalculation(data: Data): Result {
  // Extract complex logic
}
```

### Component Structure

```typescript
// 1. Imports (grouped logically)
import React, { useState, useEffect } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { Button, Box } from '@mui/material';

// 2. Type Definitions
interface ComponentProps {
  id: string;
  onAction: (id: string) => void;
}

// 3. Component Implementation
export function Component({ id, onAction }: ComponentProps) {
  // State
  const [local, setLocal] = useState();
  
  // Redux/Context
  const data = useSelector(selectData);
  const dispatch = useDispatch();
  
  // Effects
  useEffect(() => {
    // Side effects
  }, []);
  
  // Handlers
  const handleClick = () => {
    onAction(id);
  };
  
  // Render
  return (
    <Box>
      <Button onClick={handleClick}>Action</Button>
    </Box>
  );
}
```

---

## Journal System Procedures

### When to Create a Journal

**Required for:**
- Features spanning multiple development sessions
- Complex features with 3+ phases
- Features requiring coordination with backend changes
- Features that may need context transfer to new tasks

**Not Required for:**
- Simple bug fixes
- Single-file updates
- Minor UI tweaks

### Journal Creation Process

**Step 1: Create Journal File**
```bash
# Location: docs/journals/[feature-name].md
# Use lowercase with hyphens
# Example: docs/journals/invite-flow.md
```

**Step 2: Use Template**
Copy structure from `clineflow/JOURNAL_TEMPLATE.md`

**Step 3: Initialize Sections**
- Write overview
- Create phase breakdown with checkboxes
- Add initial journal entry
- Set up quick reference

**Step 4: Update Regularly**
- Add entry after each significant change
- Update phase checkboxes as tasks complete
- Document all decisions and why they were made
- Track blockers and issues

### Journal Entry Format

```markdown
### YYYY-MM-DD HH:MM - [Entry Title]

**Achievement/Change:**
Brief description of what was accomplished or changed.

**Implementation Details:**
- Created `path/to/file.ts` - Purpose
- Modified `another/file.ts` - What changed
- Key code snippet or approach used

**Why This Approach:**
Explanation of technical decisions made.

**Testing/Verification:**
How to verify the changes work.

**Next Steps:**
- [ ] Specific next action
- [ ] Another action

**Status:** [In Progress / Blocked / Complete]

---
```

### Using Journals for Task Continuation

When approaching context window limits:

1. **Summarize in Journal:**
   - Document all completed work
   - List remaining tasks
   - Note key technical decisions
   - Include file locations and snippets

2. **Create New Task:**
   ```markdown
   # Context from Previous Task
   
   As documented in docs/journals/[feature].md:
   
   ## Completed
   - Phase 1: [Brief summary]
   - Phase 2: [Brief summary]
   
   ## Current State
   [Direct quotes from journal about where work left off]
   
   ## Next Steps
   Starting Phase 3: [Description]
   See journal for complete technical details.
   ```

3. **Reference Verbatim:**
   Include exact quotes from previous conversation to preserve context

---

## Documentation Requirements

### Documentation Hierarchy

**Level 1: Feature Specifications**
- Location: `docs/[FEATURE].md`
- Purpose: Complete feature design and requirements
- Audience: Developers, product managers, Cline
- Contents: Overview, requirements, implementation plan, API contracts, UX flows

**Level 2: Implementation Status/Journals**
- Location: `docs/[FEATURE]_STATUS.md` or `docs/journals/[feature].md`
- Purpose: Track implementation progress and decisions
- Audience: Developers, Cline (for task continuation)
- Contents: Phase tracking, journal entries, known issues, quick reference

**Level 3: Issue Documents**
- Location: `docs/[FEATURE]_[ISSUE].md`
- Purpose: Deep-dive investigations of specific problems
- Audience: Developers debugging similar issues
- Contents: Problem description, investigation, root cause, solution

### Documentation Style Guide

**Use Emojis for Scanning:**
- ✅ Complete
- ❌ Failed/Blocked
- 🔧 In Progress
- ⚠️ Warning/Caution
- 📝 Note/Documentation
- 🎯 Goal/Target
- 💡 Tip/Best Practice

**Code Snippets:**
```typescript
// Always use syntax highlighting
// Include file paths in comments
// Keep snippets focused and relevant

// Example from src/app/components/Example.tsx
function Example() {
  return <div>Clear, focused example</div>;
}
```

**Structure:**
- Use clear headings (##, ###)
- Break up long sections
- Include table of contents for long docs
- Add "Last Updated" dates

---

## Code Quality Guidelines

### No Unnecessary Code

**Rule:** Every line must serve a purpose for THIS component.

**Check Before Committing:**
- Remove unused imports
- Remove commented-out code
- Remove unused variables
- Remove dead code paths
- Remove debug console.logs

**Example Review:**
```typescript
// ❌ REMOVE
import { unusedUtil } from './utils'; // Not used
const DEBUG = false; // Dead code
if (DEBUG) { console.log('debug'); } // Dead code

// ✅ KEEP
import { neededUtil } from './utils'; // Actually used
const result = neededUtil(data); // Used below
```

### Component-Specific Implementation

**Rule:** Implement only what's needed NOW, not what MIGHT be needed.

**Don't Add:**
- "Future-proof" features not in current requirements
- Optional parameters that have no current use case
- Commented-out "alternative implementations"
- Overly generic abstractions

**Example:**
```typescript
// ❌ BAD: Over-engineered
interface UserCardProps {
  user: User;
  variant?: 'compact' | 'full' | 'minimal'; // Not needed yet
  showAvatar?: boolean; // Not needed yet
  onEdit?: () => void; // Not in requirements
  theme?: 'light' | 'dark'; // Not needed yet
}

// ✅ GOOD: Implements current requirements only
interface UserCardProps {
  user: User;
}
```

### Type Safety

**Requirements:**
- Use TypeScript properly
- Define interfaces for all props
- Avoid `any` type
- Use proper type imports

**Example:**
```typescript
// ✅ GOOD
interface MessageBubbleProps {
  message: Message;
  isCurrentUser: boolean;
  onDelete?: (id: string) => void;
}

export function MessageBubble({ 
  message, 
  isCurrentUser,
  onDelete 
}: MessageBubbleProps) {
  // Implementation
}
```

---

## File Access Procedures

### Accessing clineflow/ Files

**Problem:** Files in `clineflow/` are gitignored and invisible to Cline's @ mention system.

**Solution:** Use direct file path references.

**Procedure:**

1. **User wants to reference backend code:**
   ```markdown
   User: "Check how participants are added in the backend"
   
   Cline: "I'll read clineflow/companions-api/src/jabali/routers/participants.py"
   ```

2. **Reading clineflow files:**
   ```xml
   <read_file>
   <path>clineflow/companions-api/README.md</path>
   </read_file>
   ```

3. **Never use @ mentions:**
   ```markdown
   ❌ @clineflow/companions-api/README.md
   ✅ clineflow/companions-api/README.md
   ```

### Finding Available Reference Files

**Always check `clineflow/index.json` first:**
- Contains list of all cloned repositories
- Shows available file paths
- Provides descriptions of what each repo contains

**Example workflow:**
1. User asks about backend implementation
2. Check clineflow/index.json for relevant repo
3. Read specific files from that repo using direct paths
4. Provide answer with code examples

---

## Task Management

### Before Starting Any Task

**Checklist:**
1. **Read essential context files:**
   - clineflow/index.json (if working with CharismLite features)
   - docs/ARCHITECTURE.md (for system architecture)
   - Related feature docs in docs/

2. **Assess task size:**
   - Small (< 2 hours): Proceed directly
   - Medium (2-8 hours): Consider creating journal
   - Large (> 8 hours): Create journal before starting

3. **Check for existing documentation:**
   - Look for related docs in docs/
   - Check for similar implemented features
   - Review existing journals

### During Task Execution

**Progress Tracking:**
1. Update journal after major changes
2. Mark checkboxes as tasks complete
3. Document technical decisions
4. Note any blockers or issues

**Code Quality:**
1. Keep components under 500 LOC
2. Remove unnecessary code
3. Follow TypeScript best practices
4. Write clear comments for complex logic

**Communication:**
1. Be direct and technical
2. Provide clear explanations
3. Include code examples
4. Focus on task completion

### Completing Tasks

**Before Using attempt_completion:**
1. **Verify all tool uses succeeded:**
   - Check user's responses for errors
   - Confirm files were created/modified successfully
   - Verify commands executed without errors

2. **Update documentation:**
   - Update journal with final entry
   - Mark all checkboxes complete
   - Add "Completion" journal entry

3. **Provide clear result:**
   - Summarize what was accomplished
   - List files created/modified
   - Provide testing instructions if applicable

**Example Completion:**
```xml
<attempt_completion>
<result>
Successfully consolidated llm-refs documentation:

Files Created:
- .clinerules - Brief rules pointing to llm-refs/
- llm-refs/WORKING_WITH_CLINE.md - Complete guide
- llm-refs/PROCEDURES.md - Detailed system procedures
- llm-refs/JOURNAL_TEMPLATE.md - Template for task journals

Files Updated:
- llm-refs/index.json - Consolidated with extensive comments
- llm-refs/README.md - Added Cline limitations section
- llm-refs/clone-refs.sh - Added force flag for fresh clones

Files Deleted:
- llm-refs-index.json - Removed duplicate

All files follow established patterns from INVITE_FLOW documentation.
Ready for use in future development sessions.
</result>
</attempt_completion>
```

---

## Standard Operating Procedures

### SOP-001: Starting a New Feature

1. Read docs/ARCHITECTURE.md for context
2. Check if similar features exist
3. Create feature spec doc: `docs/[FEATURE].md`
4. Create implementation journal: `docs/journals/[feature].md`
5. Outline phases in journal
6. Begin implementation, updating journal regularly

### SOP-002: Modifying Existing Components

1. Read current component file
2. Check line count
3. If > 500 LOC, plan modularization
4. Make changes using replace_in_file for targeted edits
5. Verify changes with user before proceeding
6. Update related documentation if needed

### SOP-003: Debugging Issues

1. Check if issue is documented in docs/[FEATURE]_ISSUE.md
2. Review journal entries for similar problems
3. Check git history for related changes
4. If using backend API, check clineflow/companions-api/ reference
5. Document investigation in journal or issue doc
6. Implement fix
7. Document solution

### SOP-004: Approaching Context Limits

1. Check current context usage (shown in environment_details)
2. If > 70%, prepare for task continuation:
   - Update journal with current state
   - Document remaining work clearly
   - Note key technical decisions
   - Include verbatim quotes from conversation
3. Use new_task tool with comprehensive context
4. New task references journal for complete picture

### SOP-005: Intelligent Commit Workflow

**Trigger:** User says "commit changes", "commit", or "please commit"

**Purpose:** Automatically create git commit with context-aware journal entry

**Procedure:**

1. **Identify Active Journal**
   ```
   - Check docs/journals/ for most recently modified .md file
   - OR use journal mentioned in current task context
   - IF no journal exists: Inform user and request journal creation first
   ```

2. **Generate Journal Entry**
   Using full conversation context, create entry:
   ```markdown
   ### YYYY-MM-DD HH:MM - [Entry Title from Context]
   
   **Achievement:**
   [Clear description of what was accomplished, derived from conversation]
   
   **Implementation Details:**
   - Created/Modified `file.ts` - Purpose and significance
   - Key changes with brief explanation
   - Important code decisions made
   
   **Technical Decisions:**
   [Why this approach was chosen over alternatives]
   
   **Files Changed:**
   - `path/to/file1.ts` - [+50 -20 lines] Description
   - `path/to/file2.tsx` - [+30 lines] Description
   
   **Next Steps:**
   - [ ] Remaining task items
   - [ ] Follow-up work needed
   
   **Status:** [In Progress / Complete / Blocked]
   
   ---
   ```

3. **Append to Journal**
   ```bash
   # Read current journal content
   # Append new entry at end of Journal Entries section
   # Save file
   ```

4. **Stage Everything**
   ```bash
   git add .
   git add docs/journals/[journal-name].md
   ```

5. **Generate Commit Message**
   Format:
   ```
   type(scope): brief description
   
   - Key change 1 with context
   - Key change 2 with context
   - Key change 3 with context
   ```
   
   Types: feat, fix, refactor, docs, style, test, chore
   
   Example:
   ```
   refactor(clineflow): implement symlink system for references
   
   - Convert cloned repos to symlinks saving 758MB
   - Remove .gitignore rule blocking VSCode indexing
   - Enable autocomplete for reference files
   ```

6. **Execute Commit**
   ```bash
   git commit -m "[generated message]"
   ```

7. **Confirm to User**
   ```
   ✅ Committed changes with journal entry to docs/journals/[name].md
   
   Commit: [first 7 chars of hash]
   Files: [count] changed, [insertions] insertions(+), [deletions] deletions(-)
   ```

**Important Notes:**
- Journal entry MUST be meaningful, not just file lists
- Use conversation context to explain WHY changes were made
- Commit message MUST be descriptive with clear bullet points
- Always wait for git command confirmation before reporting success

### SOP-006: Task Journal Management

**Purpose:** Ensure every task has proper documentation through journals

**When to Create Journal:**

**MANDATORY for ALL tasks** - No exceptions

**Procedure:**

1. **Assess Task Type**
   ```
   - New Task: Create new journal
   - Continuation: Update existing journal with new task section
   ```

2. **New Journal Creation**
   ```bash
   # Location: docs/journals/[task-name].md
   # Use lowercase-with-hyphens naming
   # Examples:
   - intelligent-commit-system.md
   - user-authentication-flow.md
   - api-endpoint-refactor.md
   ```

3. **Use Template**
   ```
   - Copy structure from clineflow/JOURNAL_TEMPLATE.md
   - Fill in task-specific details
   - Create phase breakdown with checkboxes
   - Add initial journal entry
   ```

4. **Multi-Task Journal Pattern**
   When continuing work from previous task:
   
   ```markdown
   # [Feature Name] - Implementation Journal Index
   
   ## Task History
   - **Task 1** (2025-11-08): Initial implementation - [Details](#task-1)
   - **Task 2** (2025-11-08): Bug fixes - [Details](#task-2)
   - **Task 3** (2025-11-09): Polish - [Details](#task-3)
   
   ## Current Status
   [Summary from most recent task]
   
   ---
   
   ## Task 1 - Initial Implementation
   [Complete task 1 journal entries]
   
   ---
   
   ## Task 2 - Bug Fixes  
   [Complete task 2 journal entries]
   
   ---
   
   ## Task 3 - Polish
   [Complete task 3 journal entries]
   ```

5. **Update Journal Regularly**
   ```
   - After significant progress
   - Before/after each commit (via SOP-005)
   - When encountering issues
   - When making technical decisions
   - At task completion
   ```

6. **Journal Entry Best Practices**
   ```
   - Be specific and technical
   - Explain WHY, not just WHAT
   - Include code snippets for clarity
   - Document alternatives considered
   - Track blockers and their resolutions
   - Update checkboxes as work progresses
   ```

**Benefits:**
- Preserves context for task continuation
- Documents technical decisions
- Enables knowledge transfer
- Supports debugging and troubleshooting
- Creates project history

---

**Last Updated:** November 8, 2025
