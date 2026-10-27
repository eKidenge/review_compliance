import csv
from urllib.parse import urlparse

def parse_and_validate_csv(file):
    # Decode file
    decoded_file = file.read().decode('utf-8').splitlines()
    reader = csv.reader(decoded_file)
    
    valid_urls = []
    invalid_urls = []
    
    # Skip header if necessary (e.g., next(reader))
    for row in reader:
        if not row: continue
        url = row[0].strip()
        
        # Basic validation (Section 11)
        parsed = urlparse(url)
        if parsed.scheme in ['http', 'https'] and 'google' in parsed.netloc:
            valid_urls.append(url)
        else:
            invalid_urls.append(url)
            
    return valid_urls, invalid_urls