# Open Agentic Framework Documentation

Welcome to the Open Agentic Framework (OAF) documentation. This guide is organized to help you quickly find the information you need, whether you're just getting started or looking for advanced configuration details.

## Documentation Structure

### Getting Started
Essential guides to get you up and running with OAF:

- **[Quick Start Guide](getting-started/QUICK_START.md)** - Complete setup and first workflow
- **[AWS Bedrock Setup](getting-started/AWS_BEDROCK_SETUP.md)** - Configure AWS Bedrock integration
- **[Backup & Restore](getting-started/BACKUP_RESTORE.md)** - Data backup and recovery procedures

### Architecture
Deep dive into the framework's design and concepts:

- **[Email Tools Architecture](architecture/EMAIL_TOOLS_ARCHITECTURE.md)** - Email processing system design
- **[Workflow Output Filtering](architecture/WORKFLOW_OUTPUT_FILTERING.md)** - Data processing and filtering concepts

### Tools
Comprehensive guides for all available tools and integrations:

#### Communication Tools
- **[Email Tools Setup](tools/EMAIL_TOOLS_SETUP.md)** - Email parsing, sending, and management
- **[Email Parser Tool](tools/EMAIL_TOOLS_SETUP.md#email-parser-tool)** - Parse and extract email data
- **[Email Sender Tool](tools/EMAIL_TOOLS_SETUP.md#email-sender-tool)** - Send emails with attachments
- **[Email Checker Tool](tools/EMAIL_TOOLS_SETUP.md#email-checker-tool)** - Validate email addresses
- **[Email Attachment Downloader](tools/EMAIL_TOOLS_SETUP.md#email-attachment-downloader-tool)** - Download email attachments
- **[Email Data Converter](tools/EMAIL_TOOLS_SETUP.md#email-data-converter-tool)** - Convert email data formats

#### Web & API Tools
- **[HTTP Client Tool](tools/HTTP_CLIENT_TOOL.md)** - Make HTTP requests to external APIs
- **[Website Monitor Tool](tools/WEBSITE_MONITOR_TOOL.md)** - Monitor website availability

#### Data Processing Tools
- **[File Vault Tool](tools/FILE_VAULT_TOOL.md)** - Secure file storage and retrieval
- **[Data Extractor Tool](tools/DATA_EXTRACTOR_TOOL.md)** - Extract structured data from various sources
- **[JSON Validator Tool](tools/JSON_VALIDATOR_TOOL.md)** - Validate and format JSON data

#### Utility Tools
- **[Rate Limiter Utility](tools/RATE_LIMITER_UTILITY.md)** - Manage API rate limits and throttling

#### Examples & Guides
- **[Agent Tooling Examples](tools/AGENT_TOOLING_EXAMPLES.md)** - Practical examples and use cases

### Workflows
Workflow-specific documentation and examples:

- **[Email Reply Workflow](workflows/EMAIL_REPLY_WORKFLOW.md)** - Automated email response system

### Deployment
Production deployment and operational guides:

- **[Production Deployment](deployment/PRODUCTION.md)** - Production setup and best practices

### Examples
Real-world examples and sample implementations:

*Coming soon - Sample workflows, configurations, and use cases*

### Reference
API references, configuration options, and technical details:

*Coming soon - API documentation, configuration reference, troubleshooting*

## Quick Navigation

### For New Users
1. Start with the **[Quick Start Guide](getting-started/QUICK_START.md)**
2. Review **[Email Tools Setup](tools/EMAIL_TOOLS_SETUP.md)** for email functionality
3. Explore **[Agent Tooling Examples](tools/AGENT_TOOLING_EXAMPLES.md)** for practical usage

### For Developers
1. Understand the **[Architecture](architecture/)** section
2. Review **[Workflow Output Filtering](architecture/WORKFLOW_OUTPUT_FILTERING.md)** for data processing
3. Check **[Production Deployment](deployment/PRODUCTION.md)** for deployment best practices

### For System Administrators
1. Review **[Backup & Restore](getting-started/BACKUP_RESTORE.md)** procedures
2. Follow **[Production Deployment](deployment/PRODUCTION.md)** guidelines
3. Configure **[AWS Bedrock](getting-started/AWS_BEDROCK_SETUP.md)** if using AWS services



## Contributing to Documentation

When adding new tools or features:

1. **Tools**: Add documentation to the `tools/` directory
2. **Workflows**: Add workflow examples to the `workflows/` directory
3. **Examples**: Add practical examples to the `examples/` directory
4. **Architecture**: Update architecture docs for significant changes
5. **Update this index**: Add new sections and links as needed

## Getting Help

- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join community discussions for questions and ideas
- **Examples**: Check the `samples/` directory for working examples

---

*Last updated: $(date)* 