import ipaddress

# Define the subnet
network = ipaddress.ip_network("0.0.0.0/24", strict=False)

# Generate all usable host IPs (excluding network and broadcast)
usable_hosts = list(network.hosts())

# Convert to comma-separated string
comma_separated_ips = ",".join(str(ip) for ip in usable_hosts)

# Print or save the result
print(comma_separated_ips)
