name: "run-migration-{migration_name}"
label: "DB: Run Migration - {migration_description}"
type: "shell"
command: "python"
args:
  - "tools/run-migration.py"
  - "--file"
  - "{migration_path}"
  - "--db"
  - "{database_key}"
group: "build"
options:
  cwd: "${workspaceFolder}"
detail: "Execute database migration: {migration_description}"
presentation:
  echo: true
  reveal: "always"
  focus: false
  panel: "shared"
problemMatcher: []
tags:
  - "database"
  - "migration"
  - "schema"
dependencies: []
