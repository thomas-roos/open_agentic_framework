#!/usr/bin/env python3
"""
test_email_tools.py - Test script for email tools

This script tests both the EmailSenderTool and EmailCheckerTool
to verify they work correctly with dynamic configuration.

Usage:
    python test_email_tools.py

Note: Update the configuration with your actual email credentials before running.
This demonstrates how agents can dynamically configure tools at runtime.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.email_sender import EmailSenderTool
from tools.email_checker import EmailCheckerTool

async def test_email_sender():
    """Test the email sender tool with dynamic configuration"""
    print("=== Testing Email Sender Tool (Dynamic Configuration) ===")
    
    # Create email sender instance (no configuration yet)
    sender = EmailSenderTool()
    
    # Dynamically configure the tool (this is how agents do it)
    print("Setting up dynamic configuration...")
    sender.set_config({
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "your-email@gmail.com",  # Update this
        "smtp_password": "your-app-password",     # Update this
        "smtp_use_tls": True,
        "smtp_use_ssl": False,
        "smtp_verify_ssl": True,
        "from_email": "your-email@gmail.com"      # Update this
    })
    
    try:
        # Test sending a simple email
        print("Sending test email...")
        result = await sender.execute({
            "to": "test@example.com",  # Update with a real email address
            "subject": "Test Email from Agentic AI Framework",
            "body": "This is a test email sent from the Agentic AI Framework email sender tool using dynamic configuration.",
            "html": False
        })
        
        print("✅ Email sent successfully!")
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"Connection type: {result.get('connection_type', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email sender test failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check your SMTP credentials")
        print("2. Ensure you're using an app password for Gmail")
        print("3. Verify SMTP settings are correct")
        print("4. Check if your email provider allows SMTP access")
        return False

async def test_email_checker():
    """Test the email checker tool with dynamic configuration"""
    print("\n=== Testing Email Checker Tool (Dynamic Configuration) ===")
    
    # Create email checker instance (no configuration yet)
    checker = EmailCheckerTool()
    
    # Dynamically configure the tool for IMAP
    print("Setting up IMAP configuration...")
    checker.set_config({
        # IMAP Configuration
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "imap_username": "your-email@gmail.com",  # Update this
        "imap_password": "your-app-password",     # Update this
        "imap_use_ssl": True,
        
        # POP3 Configuration (optional)
        "pop3_host": "pop.gmail.com",
        "pop3_port": 995,
        "pop3_username": "your-email@gmail.com",  # Update this
        "pop3_password": "your-app-password",     # Update this
        "pop3_use_ssl": True
    })
    
    try:
        # Test listing IMAP folders
        print("Testing IMAP folder listing...")
        result = await checker.execute({
            "action": "list_folders",
            "protocol": "imap"
        })
        
        print("✅ IMAP folder listing successful!")
        print(f"Protocol: {result['protocol']}")
        print(f"Message: {result['message']}")
        print(f"Found {len(result['folders'])} folders")
        
        # Test checking emails
        print("\nTesting email checking...")
        result = await checker.execute({
            "action": "check_emails",
            "protocol": "imap",
            "folder": "INBOX",
            "limit": 5,
            "unread_only": False
        })
        
        print("✅ Email checking successful!")
        print(f"Protocol: {result['protocol']}")
        print(f"Folder: {result['folder']}")
        print(f"Total emails: {result['total_emails']}")
        print(f"Retrieved emails: {result['retrieved_emails']}")
        print(f"Message: {result['message']}")
        
        # Show first few emails
        if result['emails']:
            print("\nFirst few emails:")
            for i, email in enumerate(result['emails'][:3]):
                print(f"  {i+1}. {email['subject']} (from: {email['from']})")
        
        # Test POP3 (if configured)
        print("\nTesting POP3...")
        result = await checker.execute({
            "action": "list_folders",
            "protocol": "pop3"
        })
        
        print("✅ POP3 test successful!")
        print(f"Protocol: {result['protocol']}")
        print(f"Message: {result['message']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Email checker test failed: {e}")
        print("\nTroubleshooting tips:")
        print("1. Check your IMAP/POP3 credentials")
        print("2. Ensure you're using an app password for Gmail")
        print("3. Verify IMAP/POP3 is enabled in your email provider settings")
        print("4. Check if your email provider allows IMAP/POP3 access")
        return False

async def demonstrate_agent_integration():
    """Demonstrate how agents would integrate these tools"""
    print("\n=== Agent Integration Example ===")
    
    # Simulate an agent setting up email tools
    print("Agent is setting up email tools...")
    
    # Agent creates tool instances
    email_sender = EmailSenderTool()
    email_checker = EmailCheckerTool()
    
    # Agent configures tools based on its needs
    print("Agent is configuring email sender...")
    email_sender.set_config({
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "smtp_username": "agent@example.com",
        "smtp_password": "agent-app-password",
        "smtp_use_tls": True
    })
    
    print("Agent is configuring email checker...")
    email_checker.set_config({
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "imap_username": "agent@example.com",
        "imap_password": "agent-app-password",
        "imap_use_ssl": True
    })
    
    # Agent would register these tools
    print("Agent would register these tools with: agent.register_tool(email_sender)")
    print("Agent would register these tools with: agent.register_tool(email_checker)")
    
    print("✅ Agent integration example completed!")
    return True

async def main():
    """Main test function"""
    print("Email Tools Test Script - Dynamic Configuration Demo")
    print("=" * 60)
    print("This script demonstrates how agents can dynamically configure")
    print("email tools at runtime without static configuration files.")
    print()
    print("Key points:")
    print("- Tools are created without configuration")
    print("- Configuration is set dynamically using set_config()")
    print("- Each agent can have different email configurations")
    print("- No static config files needed")
    print()
    
    # Check if credentials are configured
    print("⚠️  IMPORTANT: Update the email credentials in this script before running!")
    print("Look for 'your-email@gmail.com' and 'your-app-password' in the code.")
    print()
    
    response = input("Have you updated the credentials? (y/N): ")
    if response.lower() != 'y':
        print("Please update the credentials and run the script again.")
        sys.exit(1)
    
    # Test email sender
    sender_success = await test_email_sender()
    
    # Test email checker
    checker_success = await test_email_checker()
    
    # Demonstrate agent integration
    integration_success = await demonstrate_agent_integration()
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Email Sender (Dynamic Config): {'✅ PASSED' if sender_success else '❌ FAILED'}")
    print(f"Email Checker (Dynamic Config): {'✅ PASSED' if checker_success else '❌ FAILED'}")
    print(f"Agent Integration Demo: {'✅ PASSED' if integration_success else '❌ FAILED'}")
    
    if sender_success and checker_success and integration_success:
        print("\n🎉 All tests passed! Your email tools work with dynamic configuration.")
        print("Agents can now configure these tools at runtime as needed.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration and try again.")
        print("Refer to the EMAIL_TOOLS_SETUP.md documentation for troubleshooting.")

if __name__ == "__main__":
    # Run the tests
    asyncio.run(main()) 