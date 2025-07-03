# JSON Validator Tool

The JSON Validator Tool provides comprehensive JSON data validation, formatting, and transformation capabilities. It supports schema validation, data type checking, and custom validation rules.

## Overview

The JSON Validator Tool offers:
- JSON schema validation
- Data type validation and conversion
- Format validation (email, URL, date, etc.)
- Custom validation rules
- JSON formatting and beautification
- Error reporting and suggestions
- Data transformation and normalization

## Configuration

### Basic Configuration
```json
{
  "name": "validate_json",
  "tool": "json_validator",
  "config": {
    "data": {
      "name": "John Doe",
      "email": "john@example.com",
      "age": 30
    },
    "schema": {
      "type": "object",
      "properties": {
        "name": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "age": {"type": "integer", "minimum": 0}
      },
      "required": ["name", "email"]
    }
  }
}
```

### Advanced Configuration
```json
{
  "name": "complex_validation",
  "tool": "json_validator",
  "config": {
    "data": {
      "user": {
        "id": 123,
        "profile": {
          "name": "John Doe",
          "email": "john@example.com",
          "preferences": ["dark_mode", "notifications"]
        }
      }
    },
    "schema": {
      "type": "object",
      "properties": {
        "user": {
          "type": "object",
          "properties": {
            "id": {"type": "integer"},
            "profile": {
              "type": "object",
              "properties": {
                "name": {"type": "string", "minLength": 2},
                "email": {"type": "string", "format": "email"},
                "preferences": {
                  "type": "array",
                  "items": {"type": "string"},
                  "uniqueItems": true
                }
              },
              "required": ["name", "email"]
            }
          },
          "required": ["id", "profile"]
        }
      }
    },
    "options": {
      "strict": true,
      "format_validation": true,
      "custom_validators": {
        "email_domain": "example.com"
      }
    }
  }
}
```

## Parameters

### Required Parameters
- **data**: JSON data to validate
- **schema**: JSON schema for validation (optional if using built-in validators)

### Optional Parameters
- **options**: Validation options and settings
- **custom_validators**: Custom validation functions
- **transformations**: Data transformation rules
- **output_format**: Output format (json, yaml, xml)

## Validation Types

### 1. Schema Validation
Validate data against JSON Schema:

```json
{
  "config": {
    "data": {
      "title": "Sample Post",
      "content": "This is the content",
      "tags": ["tech", "programming"]
    },
    "schema": {
      "type": "object",
      "properties": {
        "title": {
          "type": "string",
          "minLength": 1,
          "maxLength": 100
        },
        "content": {
          "type": "string",
          "minLength": 10
        },
        "tags": {
          "type": "array",
          "items": {"type": "string"},
          "maxItems": 5
        }
      },
      "required": ["title", "content"]
    }
  }
}
```

### 2. Type Validation
Validate data types and convert if needed:

```json
{
  "config": {
    "data": {
      "count": "42",
      "price": "19.99",
      "active": "true"
    },
    "type_conversions": {
      "count": "integer",
      "price": "float",
      "active": "boolean"
    }
  }
}
```

### 3. Format Validation
Validate specific data formats:

```json
{
  "config": {
    "data": {
      "email": "user@example.com",
      "url": "https://example.com",
      "date": "2024-01-15"
    },
    "format_validation": {
      "email": "email",
      "url": "uri",
      "date": "date"
    }
  }
}
```

### 4. Custom Validation
Apply custom validation rules:

```json
{
  "config": {
    "data": {
      "username": "john_doe",
      "password": "secure123"
    },
    "custom_rules": {
      "username": {
        "pattern": "^[a-zA-Z0-9_]{3,20}$",
        "message": "Username must be 3-20 characters, alphanumeric and underscore only"
      },
      "password": {
        "min_length": 8,
        "require_uppercase": true,
        "require_lowercase": true,
        "require_digit": true
      }
    }
  }
}
```

## Examples

### API Response Validation
```json
{
  "name": "validate_api_response",
  "tool": "json_validator",
  "config": {
    "data": {
      "status": "success",
      "data": {
        "users": [
          {"id": 1, "name": "John", "email": "john@example.com"},
          {"id": 2, "name": "Jane", "email": "jane@example.com"}
        ]
      }
    },
    "schema": {
      "type": "object",
      "properties": {
        "status": {"type": "string", "enum": ["success", "error"]},
        "data": {
          "type": "object",
          "properties": {
            "users": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "id": {"type": "integer"},
                  "name": {"type": "string"},
                  "email": {"type": "string", "format": "email"}
                },
                "required": ["id", "name", "email"]
              }
            }
          }
        }
      },
      "required": ["status", "data"]
    }
  }
}
```

### Form Data Validation
```json
{
  "name": "validate_form",
  "tool": "json_validator",
  "config": {
    "data": {
      "firstName": "John",
      "lastName": "Doe",
      "email": "john.doe@example.com",
      "phone": "+1-555-123-4567",
      "age": "25"
    },
    "schema": {
      "type": "object",
      "properties": {
        "firstName": {"type": "string", "minLength": 2},
        "lastName": {"type": "string", "minLength": 2},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string", "pattern": "^\\+?[1-9]\\d{1,14}$"},
        "age": {"type": "integer", "minimum": 18, "maximum": 120}
      },
      "required": ["firstName", "lastName", "email"]
    },
    "transformations": {
      "age": "integer"
    }
  }
}
```

### Configuration Validation
```json
{
  "name": "validate_config",
  "tool": "json_validator",
  "config": {
    "data": {
      "database": {
        "host": "localhost",
        "port": 5432,
        "name": "myapp",
        "ssl": true
      },
      "api": {
        "base_url": "https://api.example.com",
        "timeout": 30,
        "retries": 3
      }
    },
    "schema": {
      "type": "object",
      "properties": {
        "database": {
          "type": "object",
          "properties": {
            "host": {"type": "string"},
            "port": {"type": "integer", "minimum": 1, "maximum": 65535},
            "name": {"type": "string", "pattern": "^[a-zA-Z0-9_]+$"},
            "ssl": {"type": "boolean"}
          },
          "required": ["host", "port", "name"]
        },
        "api": {
          "type": "object",
          "properties": {
            "base_url": {"type": "string", "format": "uri"},
            "timeout": {"type": "integer", "minimum": 1},
            "retries": {"type": "integer", "minimum": 0, "maximum": 10}
          },
          "required": ["base_url", "timeout"]
        }
      }
    }
  }
}
```

## Response Format

### Successful Validation
```json
{
  "success": true,
  "valid": true,
  "data": {
    "name": "John Doe",
    "email": "john@example.com",
    "age": 30
  },
  "transformations": {
    "age": "string -> integer"
  },
  "warnings": [],
  "processing_time": 0.012
}
```

### Validation Errors
```json
{
  "success": true,
  "valid": false,
  "errors": [
    {
      "path": "email",
      "message": "Invalid email format",
      "value": "invalid-email",
      "expected": "email format"
    },
    {
      "path": "age",
      "message": "Value must be greater than or equal to 18",
      "value": 15,
      "expected": ">= 18"
    }
  ],
  "data": {
    "name": "John Doe",
    "email": "invalid-email",
    "age": 15
  },
  "suggestions": [
    "Fix email format to include @ and domain",
    "Age must be at least 18"
  ]
}
```

## Built-in Validators

### Format Validators
- **email**: Email address validation
- **uri**: URL validation
- **date**: Date format validation
- **date-time**: DateTime format validation
- **ipv4**: IPv4 address validation
- **ipv6**: IPv6 address validation
- **uuid**: UUID format validation

### Type Validators
- **string**: String validation
- **integer**: Integer validation
- **number**: Number validation
- **boolean**: Boolean validation
- **array**: Array validation
- **object**: Object validation

### Custom Validators
```json
{
  "config": {
    "custom_validators": {
      "strong_password": {
        "min_length": 8,
        "require_uppercase": true,
        "require_lowercase": true,
        "require_digit": true,
        "require_special": true
      },
      "phone_number": {
        "pattern": "^\\+?[1-9]\\d{1,14}$",
        "message": "Invalid phone number format"
      }
    }
  }
}
```

## Integration Examples

### With HTTP Client
```json
{
  "steps": [
    {
      "name": "fetch_data",
      "tool": "http_client",
      "config": {
        "method": "GET",
        "url": "https://api.example.com/users"
      }
    },
    {
      "name": "validate_response",
      "tool": "json_validator",
      "input": {
        "source": "step_output",
        "step": "fetch_data",
        "field": "data"
      },
      "config": {
        "schema": {
          "type": "object",
          "properties": {
            "users": {
              "type": "array",
              "items": {
                "type": "object",
                "properties": {
                  "id": {"type": "integer"},
                  "name": {"type": "string"},
                  "email": {"type": "string", "format": "email"}
                }
              }
            }
          }
        }
      }
    }
  ]
}
```

### With Data Extractor
```json
{
  "steps": [
    {
      "name": "extract_data",
      "tool": "data_extractor",
      "config": {
        "source": "text",
        "patterns": {
          "emails": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"
        }
      }
    },
    {
      "name": "validate_emails",
      "tool": "json_validator",
      "input": {
        "source": "step_output",
        "step": "extract_data",
        "field": "emails"
      },
      "config": {
        "format_validation": {
          "emails": "email"
        }
      }
    }
  ]
}
```

## Best Practices

### 1. Schema Design
- Use descriptive property names
- Include proper type definitions
- Add format validators where appropriate
- Define required fields explicitly

### 2. Error Handling
```json
{
  "config": {
    "options": {
      "collect_all_errors": true,
      "detailed_error_messages": true,
      "suggest_fixes": true
    }
  }
}
```

### 3. Performance Optimization
- Use specific schemas rather than generic ones
- Cache frequently used schemas
- Limit validation depth for large objects

### 4. Data Transformation
```json
{
  "config": {
    "transformations": {
      "string_to_integer": ["id", "count"],
      "string_to_float": ["price", "rating"],
      "string_to_boolean": ["active", "enabled"]
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **Schema Validation Failures**
   - Check schema syntax
   - Verify data types match
   - Review required field definitions

2. **Format Validation Errors**
   - Ensure proper format strings
   - Check for leading/trailing whitespace
   - Verify format requirements

3. **Type Conversion Issues**
   - Handle null/undefined values
   - Check for invalid number formats
   - Validate boolean string values

4. **Performance Issues**
   - Optimize schema complexity
   - Use caching for repeated validations
   - Limit validation scope

### Debug Mode
Enable debug mode for detailed validation information:
```json
{
  "config": {
    "options": {
      "debug": true,
      "verbose_logging": true,
      "show_validation_steps": true
    }
  }
}
```

## Advanced Features

### Conditional Validation
```json
{
  "config": {
    "schema": {
      "type": "object",
      "properties": {
        "type": {"type": "string", "enum": ["individual", "company"]},
        "ssn": {"type": "string"},
        "ein": {"type": "string"}
      },
      "if": {
        "properties": {"type": {"const": "individual"}}
      },
      "then": {
        "required": ["ssn"]
      },
      "else": {
        "required": ["ein"]
      }
    }
  }
}
```

### Custom Error Messages
```json
{
  "config": {
    "custom_messages": {
      "email": "Please provide a valid email address",
      "password": "Password must be at least 8 characters with uppercase, lowercase, and digit",
      "age": "Age must be between 18 and 120"
    }
  }
}
```

### Data Sanitization
```json
{
  "config": {
    "sanitization": {
      "trim_whitespace": true,
      "remove_null_values": true,
      "normalize_case": "lowercase",
      "escape_html": true
    }
  }
}
```

---

*For more information about JSON validation patterns and examples, see the [Agent Tooling Examples](AGENT_TOOLING_EXAMPLES.md) or explore [workflow examples](../workflows/).* 