import json
import re
import sys
import argparse
from pathlib import Path

# Regular expressions for identifying common string formats
DATETIME_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?$")
UUID_REGEX = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def infer_schema_from_value(val, make_required=True):
    """Recursively infers a JSON schema from a single Python value."""
    if val is None:
        return {"type": "null"}
    elif isinstance(val, bool):
        return {"type": "boolean"}
    elif isinstance(val, int):
        return {"type": "integer"}
    elif isinstance(val, float):
        return {"type": "number"}
    elif isinstance(val, str):
        schema = {"type": "string"}
        if DATETIME_REGEX.match(val):
            schema["format"] = "date-time"
        elif UUID_REGEX.match(val):
            schema["format"] = "uuid"
        elif EMAIL_REGEX.match(val):
            schema["format"] = "email"
        return schema
    elif isinstance(val, list):
        if not val:
            return {"type": "array"}
        # Infer schema for each item and merge them
        item_schemas = [infer_schema_from_value(item, make_required) for item in val]
        merged_items = item_schemas[0]
        for other in item_schemas[1:]:
            merged_items = merge_schemas(merged_items, other)
        return {"type": "array", "items": merged_items}
    elif isinstance(val, dict):
        properties = {}
        required = []
        for k, v in val.items():
            properties[k] = infer_schema_from_value(v, make_required)
            if make_required:
                required.append(k)
        
        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
        return schema
    return {}

def merge_schemas(s1, s2):
    """Merges two JSON schemas recursively."""
    if not s1:
        return s2
    if not s2:
        return s1

    # Extract types
    t1 = s1.get("type")
    t2 = s2.get("type")

    # If types differ, return multi-type list
    if t1 != t2:
        types = []
        for t in [t1, t2]:
            if isinstance(t, list):
                types.extend(t)
            elif t:
                types.append(t)
        # Remove duplicates
        types = sorted(list(set(types)))
        
        # If both are objects/arrays, merging is complex, fallback to multi-type or anyOf
        # For simplicity, we just output type list
        return {"type": types if len(types) > 1 else types[0]}

    # If types are the same
    merged = {"type": t1}

    # Merge formats if string
    if t1 == "string":
        f1 = s1.get("format")
        f2 = s2.get("format")
        if f1 == f2 and f1:
            merged["format"] = f1

    # Merge array items
    elif t1 == "array":
        i1 = s1.get("items")
        i2 = s2.get("items")
        if i1 and i2:
            merged["items"] = merge_schemas(i1, i2)
        elif i1:
            merged["items"] = i1
        elif i2:
            merged["items"] = i2

    # Merge object properties
    elif t1 == "object":
        p1 = s1.get("properties", {})
        p2 = s2.get("properties", {})
        
        merged_props = {}
        all_keys = set(p1.keys()).union(p2.keys())
        
        for k in all_keys:
            if k in p1 and k in p2:
                merged_props[k] = merge_schemas(p1[k], p2[k])
            elif k in p1:
                merged_props[k] = p1[k]
            else:
                merged_props[k] = p2[k]
                
        merged["properties"] = merged_props
        
        # Required is the intersection of required keys in both schemas
        r1 = set(s1.get("required", []))
        r2 = set(s2.get("required", []))
        common_required = sorted(list(r1.intersection(r2)))
        if common_required:
            merged["required"] = common_required

    return merged

def main():
    parser = argparse.ArgumentParser(description="Infer JSON Schema from example JSON files")
    parser.add_argument("files", nargs="+", help="Path to one or more example JSON files")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    parser.add_argument("--optional-all", action="store_true", help="Do not mark any keys as required")
    parser.add_argument("--title", default="Inferred Schema", help="Schema title attribute")

    args = parser.parse_args()

    unified_schema = {}

    for filepath_str in args.files:
        path = Path(filepath_str)
        if not path.exists():
            print(f"Error: File not found '{filepath_str}'", file=sys.stderr)
            sys.exit(1)

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading JSON from '{filepath_str}': {e}", file=sys.stderr)
            sys.exit(1)

        # Infer schema for this file
        schema = infer_schema_from_value(data, make_required=not args.optional_all)
        
        # Merge into unified schema
        if not unified_schema:
            unified_schema = schema
        else:
            unified_schema = merge_schemas(unified_schema, schema)

    # Wrap in root schema metadata
    root_schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": args.title,
        "type": unified_schema.get("type", "object")
    }
    
    # Copy properties, items, required, format
    for key in ["properties", "required", "items", "format"]:
        if key in unified_schema:
            root_schema[key] = unified_schema[key]

    output_str = json.dumps(root_schema, indent=2)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output_str)
            print(f"Schema written successfully to {args.output}")
        except Exception as e:
            print(f"Error writing output to '{args.output}': {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print(output_str)

if __name__ == "__main__":
    main()
