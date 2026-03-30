#!/usr/bin/env python3
import ipaddress


def load_ip_list(file_path):
    """Load IPs/subnets from a file, stripping whitespace and comments."""
    with open(file_path) as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return [ipaddress.ip_network(line, strict=False) for line in lines]

def find_missing_ips(list_a, list_b):
    """Find IPs/subnets in list_b that are not covered by any in list_a."""
    missing = []
    for b_net in list_b:
        covered = any(b_net.subnet_of(a_net) or b_net == a_net for a_net in list_a)
        if not covered:
            missing.append(str(b_net))
    return missing

def main():
    # Paths to your IP lists
    file_a = "ip_list_a.txt"
    file_b = "ip_list_b.txt"

    print(f"🔹 Loading {file_a} and {file_b}...")
    list_a = load_ip_list(file_a)
    list_b = load_ip_list(file_b)

    print(f"🔹 Comparing lists...")
    missing_in_a = find_missing_ips(list_a, list_b)

    if missing_in_a:
        print(f"\n❌ The following {len(missing_in_a)} IPs/subnets are in B but missing from A:\n")
        for ip in missing_in_a:
            print(f"  - {ip}")
    else:
        print("\n✅ All IPs/subnets from list B are present (covered) in list A!")

    # Optional: also check if A has extra entries not in B
    missing_in_b = find_missing_ips(list_b, list_a)
    if missing_in_b:
        print(f"\n⚠️ The following {len(missing_in_b)} entries are in A but not covered by B (extra ranges):\n")
        for ip in missing_in_b:
            print(f"  - {ip}")

    print("\n🔍 Comparison complete.")

if __name__ == "__main__":
    main()
