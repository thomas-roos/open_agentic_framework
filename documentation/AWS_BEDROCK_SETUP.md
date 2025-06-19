# AWS Bedrock Setup Guide

This guide explains how to configure and use AWS Bedrock as an LLM provider in the Open Agentic Framework.

## Overview

AWS Bedrock provides access to multiple foundation models including:
- **Anthropic Claude** models (Claude 3 Sonnet, Haiku, Opus)
- **Amazon Titan** models (Text Express, Text Lite)
- **Meta Llama** models (Llama 2, Llama 3)

## Prerequisites

1. **AWS Account** with Bedrock access
2. **AWS Credentials** configured
3. **boto3** Python package installed
4. **Bedrock permissions** enabled for your AWS account

## Installation

### 1. Install boto3

The framework automatically includes boto3 in requirements.txt:

```bash
pip install boto3==1.34.0
```

### 2. Configure AWS Credentials

You have several options for AWS authentication:

#### Option A: AWS CLI Configuration
```bash
aws configure
# Enter your AWS Access Key ID, Secret Access Key, and region
```

#### Option B: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

#### Option C: IAM Roles (for EC2/ECS)
If running on AWS infrastructure, use IAM roles for automatic authentication.

## Configuration

### Environment Variables

Add these to your `.env` file or environment:

```bash
# Bedrock Provider Configuration
BEDROCK_ENABLED=true
BEDROCK_REGION=us-east-1
BEDROCK_ACCESS_KEY_ID=your_access_key
BEDROCK_SECRET_ACCESS_KEY=your_secret_key
BEDROCK_DEFAULT_MODEL=anthropic.claude-3-sonnet-20240229-v1:0

# Optional: Add to fallback order
LLM_FALLBACK_ORDER=ollama,bedrock,openai
```

### Framework Configuration

Update your framework configuration to include Bedrock:

```python
# config.py or main configuration
LLM_PROVIDERS = {
    "ollama": {
        "enabled": True,
        "url": "http://localhost:11434",
        "default_model": "granite3.2:2b"
    },
    "bedrock": {
        "enabled": True,
        "region_name": "us-east-1",
        "aws_access_key_id": "your_access_key",  # Optional if using AWS CLI
        "aws_secret_access_key": "your_secret_key",  # Optional if using AWS CLI
        "default_model": "anthropic.claude-3-sonnet-20240229-v1:0"
    },
    "openai": {
        "enabled": False,
        "api_key": "your_openai_key"
    }
}
```

## Available Models

### Anthropic Claude Models
- `anthropic.claude-3-sonnet-20240229-v1:0` - Balanced performance and speed
- `anthropic.claude-3-haiku-20240307-v1:0` - Fast and efficient
- `anthropic.claude-3-opus-20240229-v1:0` - Most capable model

### Amazon Titan Models
- `amazon.titan-text-express-v1` - General purpose text generation
- `amazon.titan-text-lite-v1` - Lightweight text generation

### Meta Llama Models
- `meta.llama2-13b-chat-v1` - Llama 2 13B Chat
- `meta.llama2-70b-chat-v1` - Llama 2 70B Chat
- `meta.llama3-8b-instruct-v1:0` - Llama 3 8B Instruct
- `meta.llama3-70b-instruct-v1:0` - Llama 3 70B Instruct

## Usage Examples

### 1. Create an Agent with Bedrock

```bash
curl -X POST "http://localhost:8000/agents" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bedrock_assistant",
    "role": "AI Assistant powered by Claude",
    "goals": "Provide intelligent assistance using Claude 3",
    "backstory": "You are a helpful AI assistant powered by Anthropic Claude 3. You provide clear, accurate, and helpful responses.",
    "tools": ["http_client", "data_extractor"],
    "bedrock_model": "anthropic.claude-3-sonnet-20240229-v1:0",
    "enabled": true
  }'
```

### 2. Execute Tasks with Bedrock

```bash
curl -X POST "http://localhost:8000/agents/bedrock_assistant/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Analyze the following text and provide insights: The rapid advancement of artificial intelligence has transformed various industries, from healthcare to finance, creating both opportunities and challenges for society.",
    "context": {}
  }'
```

### 3. Use Bedrock in Workflows

```bash
curl -X POST "http://localhost:8000/workflows" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "bedrock_analysis_workflow",
    "description": "Use Claude 3 for advanced text analysis",
    "input_schema": {
      "type": "object",
      "properties": {
        "text": {
          "type": "string",
          "description": "Text to analyze"
        }
      },
      "required": ["text"]
    },
    "output_spec": {
      "extractions": [
        {
          "name": "analysis",
          "type": "path",
          "query": "analysis_result",
          "default": "",
          "format": "text"
        }
      ]
    },
    "steps": [
      {
        "type": "agent",
        "name": "bedrock_assistant",
        "task": "Analyze the following text and provide detailed insights including key themes, sentiment, and recommendations: {{text}}",
        "context_key": "analysis_result"
      }
    ],
    "enabled": true
  }'
```

### 4. Test Bedrock Provider

```bash
# Check provider status
curl http://localhost:8000/providers

# List available models
curl http://localhost:8000/models

# Test specific model
curl -X POST "http://localhost:8000/models/test/anthropic.claude-3-sonnet-20240229-v1:0" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Hello, how are you?",
    "max_tokens": 100
  }'
```

## Model-Specific Features

### Claude Models
- **Tool Support**: Yes (function calling)
- **Streaming**: Yes
- **Context Length**: 200,000 tokens
- **Best For**: Complex reasoning, analysis, coding

### Titan Models
- **Tool Support**: No
- **Streaming**: No
- **Context Length**: 8,192 tokens
- **Best For**: General text generation, summarization

### Llama Models
- **Tool Support**: No
- **Streaming**: Yes
- **Context Length**: 4,096-8,192 tokens
- **Best For**: Chat, instruction following

## Cost Considerations

### Pricing (as of 2024)
- **Claude 3 Sonnet**: $3.00 per 1M input tokens, $15.00 per 1M output tokens
- **Claude 3 Haiku**: $0.25 per 1M input tokens, $1.25 per 1M output tokens
- **Claude 3 Opus**: $15.00 per 1M input tokens, $75.00 per 1M output tokens
- **Titan Text Express**: $0.0008 per 1K input tokens, $0.0016 per 1K output tokens

### Cost Optimization Tips
1. **Use Haiku** for simple tasks to reduce costs
2. **Limit max_tokens** to control output length
3. **Cache responses** for repeated queries
4. **Monitor usage** through AWS CloudWatch

## Troubleshooting

### Common Issues

#### 1. Authentication Errors
```
Error: Bedrock API error: An error occurred (AccessDeniedException)
```
**Solution**: Check AWS credentials and Bedrock permissions

#### 2. Model Access Errors
```
Error: Bedrock API error: An error occurred (AccessDeniedException) when calling the InvokeModel operation
```
**Solution**: Enable model access in AWS Bedrock console

#### 3. Region Issues
```
Error: Bedrock API error: An error occurred (ValidationException)
```
**Solution**: Ensure you're using a region where Bedrock is available

### Debug Steps

1. **Check AWS Credentials**:
```bash
aws sts get-caller-identity
```

2. **Test Bedrock Access**:
```bash
aws bedrock list-foundation-models --region us-east-1
```

3. **Verify Model Access**:
```bash
aws bedrock get-foundation-model --modelIdentifier anthropic.claude-3-sonnet-20240229-v1:0 --region us-east-1
```

4. **Check Framework Logs**:
```bash
docker-compose logs agentic-ai-framework | grep bedrock
```

## Security Best Practices

1. **Use IAM Roles** instead of access keys when possible
2. **Limit Permissions** to only Bedrock access
3. **Rotate Credentials** regularly
4. **Monitor Usage** through CloudWatch
5. **Use VPC Endpoints** for enhanced security

## Performance Optimization

1. **Model Selection**: Choose appropriate model for task complexity
2. **Caching**: Cache responses for repeated queries
3. **Batch Processing**: Group similar requests
4. **Connection Pooling**: Reuse HTTP connections
5. **Timeout Configuration**: Set appropriate timeouts

## Integration Examples

### With Existing Providers

```python
# Multi-provider configuration
config = {
    "default_provider": "bedrock",
    "fallback_enabled": True,
    "fallback_order": ["bedrock", "ollama", "openai"],
    "providers": {
        "bedrock": {
            "enabled": True,
            "region_name": "us-east-1",
            "default_model": "anthropic.claude-3-sonnet-20240229-v1:0"
        },
        "ollama": {
            "enabled": True,
            "url": "http://localhost:11434",
            "default_model": "granite3.2:2b"
        }
    }
}
```

### Advanced Usage

```python
# Custom generation parameters
response = await llm_manager.generate_response(
    prompt="Analyze this complex problem...",
    model="anthropic.claude-3-opus-20240229-v1:0",
    temperature=0.3,
    max_tokens=2000,
    top_p=0.9
)
```

This setup guide provides everything needed to integrate AWS Bedrock into your Open Agentic Framework deployment. 