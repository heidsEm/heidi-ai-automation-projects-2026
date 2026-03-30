from ipaddress import collapse_addresses, ip_address, ip_network

# Input IP lists
nonprod_ips = [
    "0.0.0.0"
]

prod_ips = [
    "0.0.0.0"
]

# Summarize IPs into minimal CIDRs
def summarize_ips(ip_list):
    ip_objs = sorted([ip_address(ip) for ip in ip_list])
    return list(collapse_addresses(ip_objs))

# Format CIDRs into XML-style output
def format_to_xml(cidr_list):
    lines = []
    for cidr in cidr_list:
        network = ip_network(cidr)
        for ip in network.hosts():  # You can use `network` directly to include network/broadcast
            lines.append(f'<SourceAddress mask="32">{ip}</SourceAddress>')
    return lines

# Process both lists
nonprod_cidrs = summarize_ips(nonprod_ips)
prod_cidrs = summarize_ips(prod_ips)

nonprod_xml = format_to_xml(nonprod_cidrs)
prod_xml = format_to_xml(prod_cidrs)

# Output
print("NonProd XML:")
print("\n".join(nonprod_xml))

print("\nProd XML:")
print("\n".join(prod_xml))
