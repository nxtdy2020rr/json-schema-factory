import unittest
from src.inferer import infer_schema_from_value, merge_schemas

class TestSchemaInfer(unittest.TestCase):
    def test_infer_scalars(self):
        # Null
        self.assertEqual(infer_schema_from_value(None), {"type": "null"})
        # Boolean
        self.assertEqual(infer_schema_from_value(True), {"type": "boolean"})
        # Integer
        self.assertEqual(infer_schema_from_value(42), {"type": "integer"})
        # Float / Number
        self.assertEqual(infer_schema_from_value(3.14), {"type": "number"})
        
        # String - generic
        self.assertEqual(infer_schema_from_value("hello"), {"type": "string"})
        # String - DateTime format
        self.assertEqual(
            infer_schema_from_value("2026-08-22T12:00:00Z"),
            {"type": "string", "format": "date-time"}
        )
        # String - UUID format
        self.assertEqual(
            infer_schema_from_value("123e4567-e89b-12d3-a456-426614174000"),
            {"type": "string", "format": "uuid"}
        )
        # String - Email format
        self.assertEqual(
            infer_schema_from_value("test@example.com"),
            {"type": "string", "format": "email"}
        )

    def test_infer_array(self):
        # Empty array
        self.assertEqual(infer_schema_from_value([]), {"type": "array"})
        
        # Homogeneous array
        self.assertEqual(
            infer_schema_from_value([1, 2, 3]),
            {"type": "array", "items": {"type": "integer"}}
        )

        # Heterogeneous array
        self.assertEqual(
            infer_schema_from_value([1, "two"]),
            {"type": "array", "items": {"type": ["integer", "string"]}}
        )

    def test_infer_object(self):
        val = {
            "name": "Alice",
            "age": 30,
            "email": "alice@example.com"
        }
        schema = infer_schema_from_value(val)
        
        self.assertEqual(schema["type"], "object")
        self.assertEqual(schema["properties"]["name"], {"type": "string"})
        self.assertEqual(schema["properties"]["age"], {"type": "integer"})
        self.assertEqual(schema["properties"]["email"], {"type": "string", "format": "email"})
        self.assertEqual(sorted(schema["required"]), ["age", "email", "name"])

    def test_merge_objects(self):
        s1 = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"}
            },
            "required": ["id", "name"]
        }
        s2 = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "email": {"type": "string", "format": "email"}
            },
            "required": ["id", "email"]
        }
        
        merged = merge_schemas(s1, s2)
        
        self.assertEqual(merged["type"], "object")
        self.assertEqual(merged["properties"]["id"], {"type": "integer"})
        self.assertEqual(merged["properties"]["name"], {"type": "string"})
        self.assertEqual(merged["properties"]["email"], {"type": "string", "format": "email"})
        # Required list should be intersection: only "id" is common required
        self.assertEqual(merged["required"], ["id"])

if __name__ == "__main__":
    unittest.main()
