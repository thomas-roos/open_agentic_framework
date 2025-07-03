# Getting Started

Welcome to the Open Agentic Framework! This section contains everything you need to get up and running quickly.

## 🚀 Quick Start

### 1. [Quick Start Guide](QUICK_START.md)
Complete setup guide for your first workflow:
- System requirements and installation
- Basic configuration
- Your first email-based workflow
- Testing and validation

## ⚙️ Configuration

### 2. [AWS Bedrock Setup](AWS_BEDROCK_SETUP.md)
Configure AWS Bedrock integration:
- AWS credentials setup
- Bedrock model configuration
- Cost optimization tips
- Troubleshooting common issues

### 3. [Backup & Restore](BACKUP_RESTORE.md)
Data management and recovery:
- Automated backup procedures
- Manual backup creation
- Restore from backup
- Disaster recovery planning

## 🎯 Next Steps

After completing the setup:

1. **Explore Tools**: Check out the [tools documentation](../tools/) to understand available capabilities
2. **Build Workflows**: Review [workflow examples](../workflows/) for inspiration
3. **Understand Architecture**: Read the [architecture documentation](../architecture/) for deeper insights
4. **Deploy to Production**: Follow the [production deployment guide](../deployment/PRODUCTION.md)

## 🔧 Common Setup Issues

### Environment Variables
Make sure all required environment variables are set:
```bash
export OPENAI_API_KEY="your-api-key"
export SMTP_SERVER="smtp.gmail.com"
export SMTP_PORT="587"
export EMAIL_USERNAME="your-email@gmail.com"
export EMAIL_PASSWORD="your-app-password"
```

### Permissions
Ensure proper file permissions:
```bash
chmod +x start-web-ui.sh
chmod +x deploy.sh
chmod +x cleanup.sh
```

### Network Access
Verify network connectivity for:
- SMTP servers (email functionality)
- API endpoints (LLM providers)
- File storage (if using cloud storage)

## 📚 Additional Resources

- **[Main Documentation Index](../README.md)** - Complete documentation overview
- **[Tools Documentation](../tools/)** - Available tools and integrations
- **[Workflow Examples](../workflows/)** - Pre-built workflow templates
- **[Architecture Overview](../architecture/)** - System design and concepts

## 🆘 Getting Help

If you encounter issues during setup:

1. Check the troubleshooting sections in each guide
2. Review the [main documentation index](../README.md)
3. Open an issue on GitHub with detailed error information
4. Check the `samples/` directory for working examples

---

*Ready to get started? Begin with the [Quick Start Guide](QUICK_START.md)!* 