```markdown
# tinyvoice Development Patterns

> Auto-generated skill from repository analysis

## Overview
This skill teaches you the core development patterns and conventions used in the `tinyvoice` Python codebase. You'll learn about file naming, import/export styles, commit message habits, and how to work with and write tests, even though no specific testing framework is detected. This guide is ideal for contributors who want to maintain consistency and quality in the project.

## Coding Conventions

### File Naming
- Use **snake_case** for all Python files.
  - Example: `audio_processor.py`, `voice_utils.py`

### Imports
- Use **relative imports** within the package.
  - Example:
    ```python
    from .audio_processor import process_audio
    ```

### Exports
- Use **named exports** (explicitly listing what is exported from a module).
  - Example:
    ```python
    __all__ = ['process_audio', 'VoiceModel']
    ```

### Commit Messages
- Freeform style, no strict prefixing.
- Average length: ~38 characters.
- Example:
  ```
  Add support for new audio format
  ```

## Workflows

### Adding a New Feature
**Trigger:** When you want to introduce new functionality.
**Command:** `/add-feature`

1. Create a new Python file using snake_case.
2. Implement your feature using relative imports as needed.
3. Add named exports to the module.
4. Write or update tests for your feature (see Testing Patterns).
5. Commit your changes with a clear, concise message.

### Fixing a Bug
**Trigger:** When you need to resolve a defect or issue.
**Command:** `/fix-bug`

1. Identify the problematic code.
2. Make necessary changes, following coding conventions.
3. Update or add tests to cover the bug fix.
4. Commit with a descriptive message about the fix.

### Writing Tests
**Trigger:** When adding or updating functionality.
**Command:** `/write-test`

1. Create a test file matching the pattern `*.test.ts` (note: TypeScript test files detected, but main code is Python).
2. Write tests for your Python code, ensuring coverage of new or changed logic.
3. Run tests using your preferred method (framework not specified).

## Testing Patterns

- Test files follow the pattern: `*.test.ts`
- The specific testing framework is **unknown**.
- Tests are likely written in TypeScript, possibly for integration or API layers.
- Example test file name: `audio_processor.test.ts`
- To add a test, create a new `.test.ts` file and implement your test cases.

## Commands
| Command      | Purpose                                  |
|--------------|------------------------------------------|
| /add-feature | Start the workflow for adding a feature  |
| /fix-bug     | Begin the bug fix workflow               |
| /write-test  | Initiate writing or updating tests       |
```
