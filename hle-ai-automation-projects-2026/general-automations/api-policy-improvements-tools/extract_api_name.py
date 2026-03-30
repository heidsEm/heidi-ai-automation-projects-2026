
import json

input_file = "proxies.json"      # Replace with your actual input file
output_file = "api_names.txt"   # Output file

# Read the input JSON file
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

# Extract API names from the 'proxies' list
api_names = []
if "proxies" in data and isinstance(data["proxies"], list):
    for item in data["proxies"]:
        if isinstance(item, dict) and "name" in item:
            api_names.append(item["name"])

# Prepare the output JSON structure
output_data = {"api_names": api_names}

# Write the result to the output JSON file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(output_data, f, ensure_ascii=False, indent=2)

print(f"✅ Extracted {len(api_names)} API name(s) and saved to {output_file}.")
