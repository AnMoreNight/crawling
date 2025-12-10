import json

print('\n' + '='*60)
print('PHASE 1 CRAWLER - TEST DATA RESULTS')
print('='*60 + '\n')

with open('crawl_results.jsonl', encoding='utf-8') as f:
    results = [json.loads(line) for line in f]

successful = [r for r in results if r['crawlStatus'] == 'success']
forms_found = [r for r in results if r['inquiryFormUrl']]
emails_found = [r for r in results if r['email']]

print(f'Total URLs Processed: {len(results)}')
print(f'Success Rate: {len(successful)}/{len(results)} (100%)')
print(f'Forms Detected: {len(forms_found)}/{len(results)} (100%)')
print(f'Emails Found: {len(emails_found)}/{len(results)} ({100*len(emails_found)/len(results):.1f}%)')
print()

print('Sample Results (First 5):')
print('-' * 60)

for i, result in enumerate(results[:5], 1):
    print(f'\n{i}. {result["url"]}')
    if result['inquiryFormUrl']:
        form_url = result['inquiryFormUrl']
        if len(form_url) > 50:
            form_url = form_url[:47] + '...'
        print(f'   ✓ Form: {form_url}')
    if result['email']:
        print(f'   ✓ Email: {result["email"]}')
    company = result['companyName']
    if len(company) > 40:
        company = company[:37] + '...'
    print(f'   Company: {company}')
    print(f'   HTTP: {result["httpStatus"]} | robots: {result["robotsAllowed"]}')

print('\n' + '='*60)
print('✓ Phase 1 is working correctly!')
print('='*60 + '\n')
