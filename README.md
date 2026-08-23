# json-schema-factory - Shared Open Source Project - Open-Source Project

A Python CLI tool that parses one or more JSON example files and automatically generates a unified draft-2020-12 compliant JSON Schema.

## Project Features

- **No external dependencies**: Written using only standard library Python modules.
- **Smart string detection**: Identifies strings containing `date-time` (ISO-8601), `uuid`, and `email` formats, injecting the corresponding format validation rules.
- **Schema merging**: Merges multiple schemas recursively. If a field contains different types across instances, it automatically combines them into multi-type structures.
- **Required keys resolution**: Determines required keys by taking the intersection of fields across all examples (i.e. if a field is missing in one instance, it is treated as optional in the merged schema).

## Repository Layout

```text
json-schema-factory/
├── src/
│   └── inferer.py
├── tests/
│   └── test_inferer.py
└── README.md
```

## Build instructions

Ensure Python (version 3.7 or later) is installed. No pip dependencies are required.

## Running the Project

Generate schema and print to stdout:

```bash
python src/inferer.py example.json
```

Generate a unified schema from multiple examples and write to a file:

```bash
python src/inferer.py instance1.json instance2.json -o unified_schema.json
```

### Options

- `-o, --output <file>`: Write the resulting JSON schema to a file instead of stdout.
- `--optional-all`: Do not mark any properties as required (makes all fields optional).
- `--title <string>`: Custom schema title attribute (defaults to "Inferred Schema").

## Example

Given `user1.json`:
```json
{
  "id": 1,
  "name": "Alice",
  "email": "alice@example.com"
}
```

And `user2.json` (missing `email` but has `role`):
```json
{
  "id": 2,
  "name": "Bob",
  "role": "admin"
}
```

Running:
```bash
python src/inferer.py user1.json user2.json
```

Outputs:
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Inferred Schema",
  "type": "object",
  "properties": {
    "id": {
      "type": "integer"
    },
    "name": {
      "type": "string"
    },
    "email": {
      "type": "string",
      "format": "email"
    },
    "role": {
      "type": "string"
    }
  },
  "required": [
    "id",
    "name"
  ]
}
```
*(Notice that `email` and `role` are optional, whereas `id` and `name` are marked as required because they exist in both instances.)*

## Running Tests

Run the test suite using Python's built-in `unittest` framework:

```bash
python -m unittest tests/test_inferer.py
```

---
*Released under the MIT License by Sassywow.*

---
*Released under the MIT License by alibasit-lgtm4.*
