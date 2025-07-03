# Data Extractor Tool

The Data Extractor Tool is a powerful utility for extracting structured data from various sources including text, HTML, JSON, and other formats. It supports pattern matching, data validation, and format conversion.

## Overview

The Data Extractor Tool provides capabilities for:
- Pattern-based data extraction using regex
- HTML/XML parsing and element extraction
- JSON data extraction and transformation
- Text parsing with custom delimiters
- Data validation and cleaning
- Format conversion and normalization

## Configuration

### Basic Configuration
```json
{
  "name": "extract_data",
  "tool": "data_extractor",
  "config": {
    "source": "text",
    "patterns": {
      "email": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
      "phone": "\\b\\d{3}-\\d{3}-\\d{4}\\b"
    }
  }
}
```

### Advanced Configuration
```json
{
  "name": "complex_extraction",
  "tool": "data_extractor",
  "config": {
    "source": "html",
    "selectors": {
      "title": "h1.title",
      "content": "div.content",
      "links": "a[href]"
    },
    "patterns": {
      "dates": "\\d{4}-\\d{2}-\\d{2}",
      "prices": "\\$\\d+\\.\\d{2}"
    },
    "validation": {
      "required_fields": ["title", "content"],
      "data_types": {
        "prices": "float",
        "dates": "date"
      }
    },
    "output_format": "json"
  }
}
```

## Parameters

### Required Parameters
- **source**: Source type (text, html, json, xml, csv)

### Optional Parameters
- **patterns**: Dictionary of regex patterns for extraction
- **selectors**: CSS/XPath selectors for HTML/XML extraction
- **delimiters**: Custom delimiters for text parsing
- **validation**: Data validation rules
- **output_format**: Output format (json, csv, xml)
- **case_sensitive**: Whether pattern matching is case sensitive
- **multiline**: Whether to use multiline regex matching

## Extraction Methods

### 1. Regex Pattern Extraction
Extract data using regular expressions:

```json
{
  "config": {
    "source": "text",
    "patterns": {
      "emails": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
      "urls": "https?://[^\\s]+",
      "phone_numbers": "\\b\\d{3}[-.]?\\d{3}[-.]?\\d{4}\\b",
      "dates": "\\d{1,2}[/-]\\d{1,2}[/-]\\d{2,4}"
    }
  }
}
```

### 2. HTML/XML Element Extraction
Extract data from HTML/XML using selectors:

```json
{
  "config": {
    "source": "html",
    "selectors": {
      "title": "h1, h2, h3",
      "paragraphs": "p",
      "links": "a[href]",
      "images": "img[src]",
      "tables": "table tr"
    }
  }
}
```

### 3. JSON Data Extraction
Extract and transform JSON data:

```json
{
  "config": {
    "source": "json",
    "json_paths": {
      "user_name": "$.user.name",
      "user_email": "$.user.email",
      "posts": "$.posts[*].title",
      "metadata": "$.metadata"
    }
  }
}
```

### 4. CSV Data Extraction
Extract data from CSV files:

```json
{
  "config": {
    "source": "csv",
    "columns": ["name", "email", "phone"],
    "filters": {
      "name": "not_empty",
      "email": "valid_email"
    }
  }
}
```

## Examples

### Email Extraction
```json
{
  "name": "extract_emails",
  "tool": "data_extractor",
  "config": {
    "source": "text",
    "patterns": {
      "emails": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"
    },
    "validation": {
      "emails": "email_format"
    }
  }
}
```

### Web Scraping
```json
{
  "name": "scrape_website",
  "tool": "data_extractor",
  "config": {
    "source": "html",
    "selectors": {
      "title": "title",
      "headings": "h1, h2, h3",
      "content": "article p",
      "author": ".author",
      "date": ".date"
    },
    "patterns": {
      "dates": "\\d{4}-\\d{2}-\\d{2}",
      "tags": "#\\w+"
    }
  }
}
```

### API Response Processing
```json
{
  "name": "process_api_response",
  "tool": "data_extractor",
  "config": {
    "source": "json",
    "json_paths": {
      "items": "$.data.items[*]",
      "total_count": "$.data.total",
      "next_page": "$.data.next_page"
    },
    "filters": {
      "items": "not_null"
    }
  }
}
```

### Text Analysis
```json
{
  "name": "analyze_text",
  "tool": "data_extractor",
  "config": {
    "source": "text",
    "patterns": {
      "sentences": "[^.!?]+[.!?]+",
      "words": "\\b\\w+\\b",
      "numbers": "\\b\\d+\\b",
      "urls": "https?://[^\\s]+"
    },
    "statistics": {
      "word_count": true,
      "sentence_count": true,
      "average_word_length": true
    }
  }
}
```

## Response Format

The tool returns extracted data in a structured format:

```json
{
  "success": true,
  "extracted_data": {
    "emails": ["user@example.com", "admin@site.com"],
    "phone_numbers": ["555-123-4567", "555-987-6543"],
    "urls": ["https://example.com", "https://site.com"]
  },
  "statistics": {
    "total_extractions": 6,
    "unique_values": 5,
    "processing_time": 0.023
  },
  "validation_results": {
    "valid_emails": 2,
    "invalid_emails": 0
  }
}
```

## Data Validation

### Built-in Validators
- **email_format**: Validates email addresses
- **phone_format**: Validates phone numbers
- **url_format**: Validates URLs
- **date_format**: Validates date formats
- **not_empty**: Ensures field is not empty
- **not_null**: Ensures field is not null

### Custom Validation
```json
{
  "config": {
    "validation": {
      "custom_rules": {
        "price": {
          "type": "float",
          "min": 0,
          "max": 1000
        },
        "age": {
          "type": "integer",
          "min": 0,
          "max": 120
        }
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
      "name": "fetch_webpage",
      "tool": "http_client",
      "config": {
        "method": "GET",
        "url": "https://example.com"
      }
    },
    {
      "name": "extract_data",
      "tool": "data_extractor",
      "input": {
        "source": "step_output",
        "step": "fetch_webpage",
        "field": "data"
      },
      "config": {
        "source": "html",
        "selectors": {
          "title": "h1",
          "content": "p"
        }
      }
    }
  ]
}
```

### With File Vault
```json
{
  "steps": [
    {
      "name": "read_file",
      "tool": "file_vault",
      "config": {
        "operation": "read",
        "file_path": "data.txt"
      }
    },
    {
      "name": "extract_structured_data",
      "tool": "data_extractor",
      "input": {
        "source": "step_output",
        "step": "read_file",
        "field": "content"
      },
      "config": {
        "source": "text",
        "patterns": {
          "names": "Name: ([A-Za-z ]+)",
          "emails": "Email: ([^\\s]+)"
        }
      }
    }
  ]
}
```

## Best Practices

### 1. Pattern Design
- Use specific patterns to avoid false positives
- Test patterns with sample data
- Consider edge cases and variations

### 2. Performance Optimization
- Use efficient regex patterns
- Limit the scope of extraction when possible
- Cache frequently used patterns

### 3. Data Quality
- Always validate extracted data
- Handle missing or malformed data gracefully
- Provide fallback values when appropriate

### 4. Error Handling
```json
{
  "config": {
    "source": "text",
    "patterns": {
      "emails": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"
    },
    "error_handling": {
      "on_no_match": "return_empty",
      "on_invalid_data": "skip"
    }
  }
}
```

## Troubleshooting

### Common Issues

1. **No Data Extracted**
   - Verify source format matches configuration
   - Check pattern syntax
   - Test with sample data

2. **Incorrect Extractions**
   - Refine regex patterns
   - Add validation rules
   - Use more specific selectors

3. **Performance Issues**
   - Optimize regex patterns
   - Limit extraction scope
   - Use caching when appropriate

4. **Encoding Issues**
   - Ensure proper text encoding
   - Handle special characters
   - Use Unicode-aware patterns

### Debug Mode
Enable debug mode for detailed extraction information:
```json
{
  "config": {
    "source": "text",
    "patterns": {
      "emails": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b"
    },
    "debug": true
  }
}
```

## Advanced Features

### Conditional Extraction
```json
{
  "config": {
    "source": "text",
    "conditional_patterns": {
      "if_contains_email": {
        "condition": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
        "patterns": {
          "email": "\\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Z|a-z]{2,}\\b",
          "name": "Name: ([A-Za-z ]+)"
        }
      }
    }
  }
}
```

### Data Transformation
```json
{
  "config": {
    "source": "text",
    "patterns": {
      "dates": "\\d{2}/\\d{2}/\\d{4}"
    },
    "transformations": {
      "dates": {
        "from_format": "MM/DD/YYYY",
        "to_format": "YYYY-MM-DD"
      }
    }
  }
}
```

---

*For more information about data extraction patterns and examples, see the [Agent Tooling Examples](AGENT_TOOLING_EXAMPLES.md) or explore [workflow examples](../workflows/).* 