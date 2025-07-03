# Workflow Output Filtering Guide

Control what data is returned from workflow execution using the `output_spec` field. This powerful feature allows you to extract specific fields from the workflow context instead of returning all data, making your workflows more efficient and easier to integrate.

## Overview

By default, workflow execution returns the complete context and all step results. With output filtering, you can specify exactly which data to extract and return, resulting in:

- **Cleaner responses** - Only relevant data
- **Smaller payloads** - Reduced bandwidth usage
- **Better integration** - Easier to consume in other systems
- **Focused results** - No need to parse through full context

## Basic Usage

### Simple Field Extraction

Extract a single field from the workflow context:

```json
{
  "name": "license_assessment_workflow",
  "output_spec": {
    "extractions": [
      {
        "name": "risk_assessment",
        "type": "path",
        "query": "risk_assessment",
        "default": "",
        "format": "text"
      }
    ]
  }
}
```

**Result:**
```json
{
  "workflow_name": "license_assessment_workflow",
  "status": "completed",
  "steps_executed": 3,
  "output": {
    "risk_assessment": {
      "OVERALL RISK LEVEL": "MEDIUM",
      "LICENSE ANALYSIS": { ... },
      "SECURITY ASSESSMENT": { ... }
    }
  },
  "message": "Extracted 1 values"
}
```

### Multiple Field Extraction

Extract multiple specific fields:

```json
{
  "name": "comprehensive_monitoring",
  "output_spec": {
    "extractions": [
      {
        "name": "overall_risk",
        "type": "path",
        "query": "risk_assessment.OVERALL RISK LEVEL",
        "default": "UNKNOWN",
        "format": "text"
      },
      {
        "name": "security_score",
        "type": "path", 
        "query": "risk_assessment.SECURITY ASSESSMENT.ClearlyDefined Score",
        "default": "0",
        "format": "number"
      },
      {
        "name": "license_breakdown",
        "type": "path",
        "query": "risk_assessment.LICENSE ANALYSIS.License Breakdown",
        "default": "{}",
        "format": "text"
      }
    ]
  }
}
```

## Extraction Types

### 1. Path Extraction (`type: "path"`)

Extract data using dot notation to navigate nested objects:

```json
{
  "name": "status_summary",
  "type": "path",
  "query": "website_status.status",
  "default": "unknown",
  "format": "text"
}
```

**Supported Path Features:**
- **Dot notation**: `"user.profile.name"`
- **Array indexing**: `"results.0.status"`
- **Nested arrays**: `"data.items.0.metadata.tags"`

### 2. Regex Extraction (`type: "regex"`)

Extract data using regular expressions:

```json
{
  "name": "version_number",
  "type": "regex",
  "query": "v(\\d+\\.\\d+\\.\\d+)",
  "default": "0.0.0",
  "format": "text"
}
```

### 3. Literal Extraction (`type: "literal"`)

Return a literal value:

```json
{
  "name": "workflow_type",
  "type": "literal",
  "query": "license_assessment",
  "default": "",
  "format": "text"
}
```

### 4. Find Extraction (`type: "find"`)

Find data in arrays using criteria:

```json
{
  "name": "high_risk_license",
  "type": "find",
  "query": "",
  "default": "",
  "format": "text",
  "find_criteria": {
    "array_path": "risk_assessment.LICENSE ANALYSIS.License Breakdown",
    "match_field": "risk_level",
    "match_value": "HIGH",
    "extract_field": "license_name"
  }
}
```

### 5. Join Field Extraction (`type: "join_field"`)

Extract an array at a given path and join all values of a specified field with a separator:

```json
{
  "name": "all_purls",
  "type": "join_field",
  "query": "components",
  "field": "purl",
  "separator": ",",
  "default": "",
  "format": "text"
}
```

**Parameters:**
- **`query`** - Array path (e.g., `"components"`, `"dependencies"`)
- **`field`** - Field name to extract from each array item (e.g., `"purl"`, `"name"`)
- **`separator`** - String to join values with (default: `","`)

**Example Usage:**
```json
{
  "name": "sbom_purls",
  "type": "join_field",
  "query": "components",
  "field": "purl",
  "separator": " ",
  "default": "",
  "format": "text"
}
```

This would extract all PURLs from a components array and join them with spaces.

## Format Options

### Text Format (`format: "text"`)

Returns data as-is, preserving JSON objects and arrays:

```json
{
  "name": "full_assessment",
  "type": "path",
  "query": "risk_assessment",
  "default": "{}",
  "format": "text"
}
```

**Result:** `{"OVERALL RISK LEVEL": "MEDIUM", "LICENSE ANALYSIS": {...}}`

### Number Format (`format: "number"`)

Converts to number if possible:

```json
{
  "name": "score",
  "type": "path",
  "query": "security_assessment.score",
  "default": "0",
  "format": "number"
}
```

**Result:** `85` (number, not string)

### Boolean Format (`format: "boolean"`)

Converts to boolean:

```json
{
  "name": "is_secure",
  "type": "path",
  "query": "security_assessment.is_secure",
  "default": "false",
  "format": "boolean"
}
```

**Result:** `true` (boolean, not string)

## Advanced Examples

### License Assessment Workflow

```json
{
  "name": "license_assessment_workflow",
  "description": "Comprehensive license and security assessment",
  "input_schema": {
    "type": "object",
    "properties": {
      "package_name": {
        "type": "string",
        "description": "Package name to analyze"
      },
      "analysis_depth": {
        "type": "string",
        "enum": ["basic", "comprehensive"],
        "default": "comprehensive"
      }
    },
    "required": ["package_name"]
  },
  "output_spec": {
    "extractions": [
      {
        "name": "overall_risk",
        "type": "path",
        "query": "risk_assessment.OVERALL RISK LEVEL",
        "default": "UNKNOWN",
        "format": "text"
      },
      {
        "name": "security_score",
        "type": "path",
        "query": "risk_assessment.SECURITY ASSESSMENT.ClearlyDefined Score",
        "default": "0",
        "format": "number"
      },
      {
        "name": "license_count",
        "type": "path",
        "query": "risk_assessment.LICENSE ANALYSIS.Declared Licenses",
        "default": "[]",
        "format": "text"
      },
      {
        "name": "recommendations",
        "type": "path",
        "query": "risk_assessment.LEGAL RECOMMENDATIONS.Specific Actions Needed",
        "default": "[]",
        "format": "text"
      }
    ]
  },
  "steps": [
    {
      "type": "tool",
      "name": "purl_parser",
      "parameters": {"purl": "{{package_name}}"},
      "context_key": "parsed_purl"
    },
    {
      "type": "agent",
      "name": "license_assessor",
      "task": "Analyze the package {{package_name}} with depth {{analysis_depth}}. Provide comprehensive risk assessment including license analysis, security assessment, and legal recommendations.",
      "context_key": "risk_assessment"
    }
  ]
}
```

### Website Monitoring with Alerts

```json
{
  "name": "website_monitoring_workflow",
  "description": "Monitor website health with intelligent alerts",
  "input_schema": {
    "type": "object",
    "properties": {
      "target_url": {
        "type": "string",
        "description": "URL to monitor"
      },
      "alert_email": {
        "type": "string",
        "description": "Email for alerts"
      },
      "timeout": {
        "type": "integer",
        "description": "Timeout in seconds",
        "default": 10
      }
    },
    "required": ["target_url", "alert_email"]
  },
  "output_spec": {
    "extractions": [
      {
        "name": "status",
        "type": "path",
        "query": "website_status.status",
        "default": "unknown",
        "format": "text"
      },
      {
        "name": "response_time",
        "type": "path",
        "query": "website_status.response_time_ms",
        "default": "0",
        "format": "number"
      },
      {
        "name": "alert_sent",
        "type": "path",
        "query": "alert_result.status",
        "default": "not_sent",
        "format": "text"
      }
    ]
  },
  "steps": [
    {
      "type": "tool",
      "name": "website_monitor",
      "parameters": {
        "url": "{{target_url}}",
        "timeout": "{{timeout}}"
      },
      "context_key": "website_status"
    },
    {
      "type": "agent",
      "name": "website_guardian",
      "task": "Analyze website status: {{website_status}}. If there are issues, send email alert to {{alert_email}} with detailed analysis.",
      "context_key": "alert_result"
    }
  ]
}
```

## Using the Web UI

The web interface provides both simple and advanced editors for configuring output specs:

### Simple JSON Editor
- Edit the entire `output_spec` as JSON
- Good for advanced users who know the exact format
- Full control over the specification

### Advanced Form Editor
- Add extractions one by one with form fields
- Guided interface for each extraction type
- Real-time validation and preview

### Steps to Configure Output Spec:
1. **Create/Edit Workflow** → Scroll to "Workflow Output Spec" section
2. **Choose Editor** → Simple JSON or Advanced Form
3. **Add Extractions** → Configure name, type, query, format
4. **Test** → Execute workflow to see filtered output

## Best Practices

### 1. Use Descriptive Names
```json
{
  "name": "overall_risk_level",  // Good
  "name": "risk",               // Less descriptive
}
```

### 2. Provide Meaningful Defaults
```json
{
  "default": "UNKNOWN",         // Good
  "default": "",               // Less informative
}
```

### 3. Choose Appropriate Formats
```json
{
  "query": "score",
  "format": "number"           // Good for numeric data
}
```

### 4. Use Path Extraction for Most Cases
Path extraction is the most common and flexible option for extracting data from workflow context.

### 5. Test Your Extractions
Always test your output spec to ensure it extracts the expected data.

## Error Handling

If an extraction fails:
- The default value is returned
- The workflow continues to execute
- Error details are logged for debugging
- The extraction is marked as failed in the response

## Integration Examples

### API Integration
```python
import requests

# Execute workflow with output filtering
response = requests.post(
    "http://localhost:8000/workflows/license_assessment/execute",
    json={"context": {"package_name": "lodash@4.17.21"}}
)

# Get only the filtered output
filtered_data = response.json()["output"]
print(f"Risk Level: {filtered_data['overall_risk']}")
print(f"Security Score: {filtered_data['security_score']}")
```

### Webhook Integration
```json
{
  "output_spec": {
    "extractions": [
      {
        "name": "webhook_payload",
        "type": "path",
        "query": "risk_assessment",
        "default": "{}",
        "format": "text"
      }
    ]
  }
}
```

The filtered output can be directly sent to webhooks or other systems without additional processing.

## Troubleshooting

### Common Issues

1. **Extraction returns default value**
   - Check if the path exists in the workflow context
   - Verify the context_key names in workflow steps
   - Use the full workflow output to debug

2. **JSON objects returned as strings**
   - Use `"format": "text"` to preserve JSON structure
   - Check if the data is being converted elsewhere

3. **Array access not working**
   - Use numeric indices: `"query": "results.0.status"`
   - Ensure the array exists and has the expected structure

### Debug Mode
To see the full workflow context for debugging, temporarily remove the `output_spec` field from your workflow definition.

## Migration Guide

### From Full Output to Filtered Output

**Before (Full Output):**
```json
{
  "workflow_name": "my_workflow",
  "results": [...],
  "final_context": {
    "step1_result": {...},
    "step2_result": {...},
    "final_analysis": "..."
  }
}
```

**After (Filtered Output):**
```json
{
  "workflow_name": "my_workflow", 
  "output": {
    "key_metric": "value",
    "summary": "..."
  }
}
```

Add `output_spec` to your workflow definition to start filtering output immediately. 