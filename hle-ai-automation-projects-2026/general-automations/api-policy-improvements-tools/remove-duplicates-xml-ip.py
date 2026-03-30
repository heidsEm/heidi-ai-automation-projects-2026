def remove_duplicates_from_list(source_lines):
    seen = set()
    unique_lines = []

    for line in source_lines:
        line = line.strip()
        if line.startswith('<SourceAddress') and line.endswith('</SourceAddress>'):
            ip = line.split('>')[1].split('<')[0]
            if ip not in seen:
                seen.add(ip)
                unique_lines.append(line)
        else:
            unique_lines.append(line)

    return unique_lines

# Paste your source addresses here
source_addresses = [
'<SourceAddress mask="29">0.0.0.0</SourceAddress>',


]

# Remove duplicates
unique_addresses = remove_duplicates_from_list(source_addresses)

# Print result
for line in unique_addresses:
    print(line)
