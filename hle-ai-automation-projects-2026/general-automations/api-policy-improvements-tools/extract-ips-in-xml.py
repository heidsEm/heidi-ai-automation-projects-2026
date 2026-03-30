#!/usr/bin/env python3
import re


def extract_unique_cidrs(text):
    """
    Extract unique IP/mask pairs from lines like:
    <SourceAddress mask="32">52.252.84.193</SourceAddress>
    Returns sorted unique IP/CIDR strings.
    """
    pattern = re.compile(r'<SourceAddress\s+mask="(\d{1,2})">([\d.]+)</SourceAddress>')
    cidrs = {f"{ip}/{mask}" for mask, ip in pattern.findall(text)}
    return sorted(cidrs)

if __name__ == "__main__":
    # Read from a file (e.g., input.xml)
    with open("list-of-ips.xml", "r", encoding="utf-8") as f:
        content = f.read()

    results = extract_unique_cidrs(content)

    # Output the unique IP/mask entries
    for cidr in results:
        print(cidr)
