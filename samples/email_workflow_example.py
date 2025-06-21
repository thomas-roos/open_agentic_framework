#!/usr/bin/env python3
"""
email_workflow_example.py - Email Tools Workflow Example

This example demonstrates how the email tools work together:
1. EmailCheckerTool - Check and retrieve emails
2. EmailParserTool - Parse email content and metadata
3. AttachmentDownloaderTool - Download attachments to temp location

This shows the modular approach where tools work together but remain separate.
"""

import asyncio
import sys
import os

# Add the parent directory to the path so we can import the tools
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agentic_ai_framework.tools.email_checker import EmailCheckerTool
from agentic_ai_framework.tools.email_parser import EmailParserTool
from agentic_ai_framework.tools.attachment_downloader import AttachmentDownloaderTool

async def email_workflow_example():
    """Demonstrate the complete email workflow"""
    print("Email Tools Workflow Example")
    print("=" * 50)
    print("This example shows how email tools work together:")
    print("1. Check emails (EmailCheckerTool)")
    print("2. Parse email content (EmailParserTool)")
    print("3. Download attachments (AttachmentDownloaderTool)")
    print()
    
    # Step 1: Set up email checker
    print("Step 1: Setting up Email Checker...")
    email_checker = EmailCheckerTool()
    email_checker.set_config({
        "imap_host": "imap.gmail.com",
        "imap_port": 993,
        "imap_username": "your-email@gmail.com",  # Update this
        "imap_password": "your-app-password",     # Update this
        "imap_use_ssl": True
    })
    
    # Step 2: Check for recent emails
    print("\nStep 2: Checking for recent emails...")
    try:
        emails_result = await email_checker.execute({
            "action": "check_emails",
            "protocol": "imap",
            "folder": "INBOX",
            "limit": 3,
            "unread_only": False
        })
        
        print(f"✅ Found {len(emails_result['emails'])} emails")
        
        if not emails_result['emails']:
            print("No emails found. Please check your configuration.")
            return
        
        # Step 3: Process each email
        for i, email_summary in enumerate(emails_result['emails']):
            print(f"\n--- Processing Email {i+1}: {email_summary['subject']} ---")
            
            # Get full email content
            email_detail = await email_checker.execute({
                "action": "read_email",
                "protocol": "imap",
                "email_id": email_summary['id'],
                "include_attachments": True
            })
            
            # Step 4: Parse email content
            print("Step 4: Parsing email content...")
            email_parser = EmailParserTool()
            parsed_result = await email_parser.execute({
                "email_data": email_detail,
                "parse_headers": True,
                "parse_body": True,
                "parse_attachments": True,
                "extract_links": True,
                "extract_emails": True
            })
            
            parsed_email = parsed_result['parsed_email']
            print(f"✅ Parsed email: {parsed_email.get('headers', {}).get('subject', 'No subject')}")
            
            # Display parsed information
            headers = parsed_email.get('headers', {})
            recipients = parsed_email.get('recipients', {})
            
            print(f"From: {headers.get('from', 'Unknown')}")
            print(f"To: {', '.join([r['email'] for r in recipients.get('to', [])])}")
            print(f"Date: {headers.get('date', 'Unknown')}")
            print(f"Body text length: {len(parsed_email.get('body_text', ''))} characters")
            print(f"Body HTML length: {len(parsed_email.get('body_html', ''))} characters")
            print(f"Attachments: {parsed_email.get('attachment_count', 0)}")
            
            # Show extracted links and emails
            if parsed_email.get('extracted_links'):
                print(f"Links found: {len(parsed_email['extracted_links'])}")
                for link in parsed_email['extracted_links'][:3]:  # Show first 3
                    print(f"  - {link}")
            
            if parsed_email.get('extracted_emails'):
                print(f"Email addresses found: {len(parsed_email['extracted_emails'])}")
                for email in parsed_email['extracted_emails'][:3]:  # Show first 3
                    print(f"  - {email}")
            
            # Step 5: Download attachments if any
            if parsed_email.get('has_attachments'):
                print("\nStep 5: Downloading attachments...")
                attachment_downloader = AttachmentDownloaderTool()
                download_result = await attachment_downloader.execute({
                    "email_data": email_detail,
                    "attachment_filenames": [],  # Download all attachments
                    "create_subdirectories": True,
                    "sanitize_filenames": True,
                    "max_file_size": 10 * 1024 * 1024  # 10MB limit
                })
                
                print(f"✅ Downloaded {download_result['total_files']} attachments")
                print(f"Download path: {download_result['download_path']}")
                print(f"Total size: {download_result['total_size']} bytes")
                
                # Show downloaded files
                for file_info in download_result['downloaded_files']:
                    print(f"  - {file_info['original_filename']} -> {file_info['file_path']}")
                    print(f"    Size: {file_info['size']} bytes, Type: {file_info['content_type']}")
                
                # Clean up example (in real usage, you'd keep files as needed)
                print("\nCleaning up downloaded files...")
                attachment_downloader.cleanup_temp_files(download_result['download_path'])
                print("✅ Cleaned up temporary files")
            else:
                print("No attachments to download.")
            
            print(f"\n--- Completed processing Email {i+1} ---")
        
        print("\n🎉 Email workflow completed successfully!")
        print("\nKey benefits of this modular approach:")
        print("1. Each tool has a single responsibility")
        print("2. Tools can be used independently or together")
        print("3. Easy to test and maintain each component")
        print("4. Flexible configuration for different use cases")
        print("5. Reusable across different agents and workflows")
        
    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your email credentials")
        print("2. Ensure IMAP is enabled in your email provider")
        print("3. Verify SSL settings are correct")

async def demonstrate_tool_independence():
    """Demonstrate that tools can be used independently"""
    print("\n" + "=" * 50)
    print("Tool Independence Demonstration")
    print("=" * 50)
    
    print("\nExample 1: Using Email Parser with existing email data...")
    # You could use the parser with email data from other sources
    sample_email_data = {
        "id": "sample_123",
        "protocol": "imap",
        "email": {
            "Subject": "Test Email",
            "From": "sender@example.com",
            "To": "recipient@example.com",
            "Date": "Mon, 1 Jan 2024 12:00:00 +0000"
        }
    }
    
    parser = EmailParserTool()
    result = await parser.execute({
        "email_data": sample_email_data,
        "parse_headers": True,
        "parse_body": False,
        "parse_attachments": False
    })
    
    print(f"✅ Parsed sample email: {result['parsed_email'].get('headers', {}).get('subject', 'No subject')}")
    
    print("\nExample 2: Using Attachment Downloader with parsed email data...")
    # You could use the downloader with email data that has attachments
    print("(This would work with actual email data containing attachments)")
    
    print("\n✅ Tools can be used independently or in combination!")

if __name__ == "__main__":
    # Check if credentials are configured
    print("⚠️  IMPORTANT: Update the email credentials in this script before running!")
    print("Look for 'your-email@gmail.com' and 'your-app-password' in the code.")
    print()
    
    response = input("Have you updated the credentials? (y/N): ")
    if response.lower() != 'y':
        print("Please update the credentials and run the script again.")
        sys.exit(1)
    
    # Run the workflow example
    asyncio.run(email_workflow_example())
    
    # Demonstrate tool independence
    asyncio.run(demonstrate_tool_independence()) 