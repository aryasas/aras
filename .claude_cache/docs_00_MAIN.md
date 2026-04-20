<project_context>
# Aras: Flask Low-Code CRUD Builder
Auto-generates UI, DB, REST. Stack: Python 3.9+, Flask, MariaDB, Celery.
Run: `flask run` (port 8080)
</project_context>

<documentation_index>
- **Architecture & App Lifecycle:** Read `docs/ARCHITECTURE.md`
- **Commands & Troubleshooting:** Read `docs/QUICK_REF.md`
- **Database & Models:** Read `docs/DATABASE.md`
</documentation_index>

<agent_rules>
1. BE CONCISE: Zero conversational filler. Output minimal explanations.
2. LIMIT I/O: Only read the specific `docs/*.md` file relevant to the current task. Track read files. 
3. DO NOT rewrite entire files; output specific diffs or targeted function replacements.
4. Use absolute imports from `aras` or `arasCore`.
5. CRITICAL FILE READING OVERRIDE: You are strictly FORBIDDEN from using your native `Read`, `View`, or `cat` tools to read code files. 
   - To read ANY file, you MUST use the terminal to execute: `./smart_read.sh <filepath>`
   - This script handles deduplication and diffing automatically.
</agent_rules>