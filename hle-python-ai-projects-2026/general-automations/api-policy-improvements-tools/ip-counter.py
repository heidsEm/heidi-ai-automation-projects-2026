from collections import Counter

# List of IPs (replace this list with your actual data)
ip_list = [
	"0.0.0.0"

]
def count_ips(ip_addresses):
    counter = Counter(ip_addresses)
    total_unique = len(counter)
    total_ips = sum(counter.values())

    print(f"Total unique IPs: {total_unique}")
    print(f"Total IP occurrences: {total_ips}\n")
    print(f"{'IP Address':<20} {'Count':>5}")
    print("-" * 26)
    for ip, count in counter.most_common():
        print(f"{ip:<20} {count:>5}")

if __name__ == "__main__":
    count_ips(ip_list)
