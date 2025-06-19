# Agent Tooling Examples

This guide provides examples of how agents can dynamically execute tools and use data extraction to analyze results. These examples demonstrate the framework's capabilities for tool chaining, data parsing, and intelligent analysis.

## Overview

Agents in the Open Agentic Framework can:
- **Execute tools dynamically** based on user requests
- **Chain multiple tools** together for complex workflows
- **Use data extraction** to parse and analyze tool results
- **Provide intelligent analysis** and recommendations
- **Handle different data formats** (JSON, HTML, text)

## Agent Setup for Dynamic Tool Execution

### Create a Dynamic Tool Executor Agent

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "dynamic_tool_executor",
    "role": "Dynamic Tool Execution Specialist",
    "goals": "Execute tools dynamically based on user requests and analyze results using data extraction",
    "backstory": "You are an expert at using tools to gather information and then analyzing that data using data extraction techniques. You can execute website monitoring, HTTP requests, and other tools, then use the data_extractor tool to parse and extract specific information from the results. You always provide clear analysis and actionable insights from the extracted data.",
    "tools": ["website_monitor", "http_client", "data_extractor"],
    "ollama_model": "deepseek-r1:1.5b",
    "enabled": true
  }'
```

### Create a Data Analysis Specialist Agent

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "data_analysis_specialist",
    "role": "Data Analysis and Extraction Specialist",
    "goals": "Analyze data from various sources using advanced extraction techniques and provide insights",
    "backstory": "You are a data scientist specializing in extracting meaningful insights from complex datasets. You excel at using data extraction tools to parse JSON, HTML, and other formats, then providing statistical analysis and actionable recommendations. You can handle large datasets and identify patterns that others might miss.",
    "tools": ["http_client", "data_extractor", "website_monitor"],
    "ollama_model": "deepseek-r1:1.5b",
    "enabled": true
  }'
```

## Website Monitoring Examples

### 1. Basic Website Health Check

```bash
curl -X POST "http://localhost:8000/agents/dynamic_tool_executor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if https://api.github.com/zen is online, then extract the response time and status code. If the response time is above 1000ms, flag it as slow performance.",
    "context": {}
  }'
```

**Expected Response:**
```json
{
  "agent_name": "dynamic_tool_executor",
  "task": "Check if https://api.github.com/zen is online...",
  "result": "I executed the website monitoring tool to check https://api.github.com/zen. The site responded with status 200 in 245ms. Using data extraction, I found:\n\n- Response Time: 245ms (Good performance)\n- Status Code: 200 (Success)\n- Performance Category: Fast (<1000ms)\n\nRecommendation: The website is performing well with excellent response times.",
  "timestamp": "2024-06-19T18:30:00Z"
}
```

### 2. Performance Analysis with Thresholds

```bash
curl -X POST "http://localhost:8000/agents/dynamic_tool_executor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Monitor https://httpbin.org/delay/2 and extract the response time. If the response time is greater than 1500ms, categorize it as slow. Also extract the status code and provide performance recommendations.",
    "context": {}
  }'
```

### 3. Multiple Website Comparison

```bash
curl -X POST "http://localhost:8000/agents/dynamic_tool_executor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Compare the performance of three websites: https://google.com, https://github.com, and https://stackoverflow.com. Extract response times and status codes for each, then provide a performance ranking and recommendations.",
    "context": {}
  }'
```

## HTTP API Integration Examples

### 1. JSON API Data Extraction

```bash
curl -X POST "http://localhost:8000/agents/dynamic_tool_executor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Make a GET request to https://jsonplaceholder.typicode.com/posts/1, then extract the title and body fields from the response. Provide a summary of the post content.",
    "context": {}
  }'
```

### 2. Complex JSON Parsing

```bash
curl -X POST "http://localhost:8000/agents/dynamic_tool_executor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Fetch data from https://jsonplaceholder.typicode.com/users and extract the following information: 1) Number of users, 2) List of company names, 3) Average user ID. Use data_extractor to parse the JSON response and provide statistical analysis.",
    "context": {}
  }'
```

### 3. Nested JSON Data Extraction

```bash
curl -X POST "http://localhost:8000/agents/dynamic_tool_executor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Make a request to https://httpbin.org/json and use the data_extractor tool to extract the following fields from the response: 1) The slideshow title, 2) The number of slides, 3) The first slide title. Provide the extracted data in a structured format.",
    "context": {}
  }'
```

## Data Extraction Testing Examples

### 1. Testing Path Extraction

```bash
curl -X POST "http://localhost:8000/agents/data_analysis_specialist/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Test the data extraction capabilities by fetching data from https://jsonplaceholder.typicode.com/posts and extracting: 1) The first post title, 2) All user IDs, 3) Posts with title containing 'qui'. Use path extraction to navigate the JSON structure.",
    "context": {}
  }'
```

### 2. Testing Regex Extraction

```bash
curl -X POST "http://localhost:8000/agents/data_analysis_specialist/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Fetch the GitHub API response from https://api.github.com/zen and use regex extraction to find any version numbers or special patterns in the response text. Extract any URLs or email addresses if present.",
    "context": {}
  }'
```

### 3. Testing Array Processing

```bash
curl -X POST "http://localhost:8000/agents/data_analysis_specialist/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Get data from https://jsonplaceholder.typicode.com/albums and extract: 1) The first 3 album titles, 2) Albums with ID greater than 50, 3) Count of albums per user. Use array processing and filtering techniques.",
    "context": {}
  }'
```

## Real-World Use Cases

### 1. API Health Monitoring

```bash
curl -X POST "http://localhost:8000/agents/dynamic_tool_executor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Monitor the health of a REST API by checking https://httpbin.org/status/200, https://httpbin.org/status/404, and https://httpbin.org/status/500. Extract status codes and response times, then provide a health assessment with recommendations for any failing endpoints.",
    "context": {}
  }'
```

### 2. Content Analysis

```bash
curl -X POST "http://localhost:8000/agents/data_analysis_specialist/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze content from https://jsonplaceholder.typicode.com/posts by extracting: 1) Most common words in titles, 2) Average post length, 3) Posts by user ID 1. Provide content insights and identify trending topics.",
    "context": {}
  }'
```

### 3. Performance Benchmarking

```bash
curl -X POST "http://localhost:8000/agents/dynamic_tool_executor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Benchmark multiple API endpoints: https://httpbin.org/delay/1, https://httpbin.org/delay/2, and https://httpbin.org/delay/3. Extract response times, calculate averages, and identify the fastest and slowest endpoints. Provide performance recommendations.",
    "context": {}
  }'
```

## Advanced Tool Chaining Examples

### 1. Multi-Step Data Analysis

```bash
curl -X POST "http://localhost:8000/agents/data_analysis_specialist/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Perform a comprehensive analysis: 1) First, check if https://jsonplaceholder.typicode.com is online, 2) If online, fetch user data and extract company information, 3) Fetch posts data and extract titles, 4) Cross-reference users with their posts to find the most active users. Provide a complete analysis report.",
    "context": {}
  }'
```

### 2. Conditional Tool Execution

```bash
curl -X POST "http://localhost:8000/agents/dynamic_tool_executor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check the status of https://httpbin.org/status/200. If it returns status 200, proceed to fetch detailed data from https://jsonplaceholder.typicode.com/users/1. If it fails, try the backup endpoint https://httpbin.org/json. Extract user information and provide a status report.",
    "context": {}
  }'
```

## Expected Agent Behavior Patterns

### Tool Execution Pattern
1. **Identify required tools** based on the task
2. **Execute tools** with appropriate parameters
3. **Extract data** using data_extractor
4. **Analyze results** and provide insights
5. **Make recommendations** based on findings

### Data Extraction Pattern
1. **Parse response data** using appropriate extraction type
2. **Navigate JSON structure** using path queries
3. **Apply filters** and transformations
4. **Aggregate results** for analysis
5. **Present findings** in structured format

### Analysis Pattern
1. **Compare data** against thresholds or benchmarks
2. **Identify patterns** and trends
3. **Calculate statistics** (averages, counts, etc.)
4. **Assess performance** or quality metrics
5. **Provide actionable recommendations**

## Testing Agent Capabilities

### Basic Functionality Test
```bash
# Test if agent can execute a simple tool
curl -X POST "http://localhost:8000/agents/dynamic_tool_executor/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Check if https://httpbin.org/get is accessible and extract the response status.",
    "context": {}
  }'
```

### Data Extraction Test
```bash
# Test if agent can use data_extractor properly
curl -X POST "http://localhost:8000/agents/data_analysis_specialist/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Fetch data from https://jsonplaceholder.typicode.com/posts/1 and extract only the title field using data_extractor.",
    "context": {}
  }'
```

### Complex Analysis Test
```bash
# Test if agent can perform multi-step analysis
curl -X POST "http://localhost:8000/agents/data_analysis_specialist/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze user activity: fetch users from https://jsonplaceholder.typicode.com/users, then fetch their posts, and determine which users have the most posts. Extract user names and post counts.",
    "context": {}
  }'
```