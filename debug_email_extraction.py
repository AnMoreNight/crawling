#!/usr/bin/env python3
"""
Debug why emails are not being extracted
"""
from crawler.enhanced_email_extractor import EnhancedEmailExtractor
import requests

# Test with a real URL
test_url = "https://www.konanhanbai.jp/"

print("Testing email extraction on: " + test_url)
print()

try:
    # Fetch the page
    response = requests.get(test_url, timeout=10)
    html_content = response.text
    
    print("HTML fetched successfully (" + str(len(html_content)) + " bytes)")
    print()
    
    # Try extracting emails
    emails = EnhancedEmailExtractor.extract_emails(html_content)
    
    print("Emails found: " + str(len(emails)))
    for email in emails:
        print("  - " + email)
    
    if not emails:
        print("  (none)")
        print()
        print("Checking HTML for @ symbols...")
        if '@' in html_content:
            print("  @ found in HTML")
            # Find all @ occurrences
            import re
            at_contexts = re.findall(r'.{0,30}@.{0,30}', html_content)
            print("\n  Sample @ contexts (first 5):")
            for i, context in enumerate(at_contexts[:5]):
                print("    " + str(i+1) + ". " + context.replace('\n', ' '))
        else:
            print("  NO @ symbols found in HTML at all")
    
except Exception as e:
    print("Error: " + str(e))
    import traceback
    traceback.print_exc()
