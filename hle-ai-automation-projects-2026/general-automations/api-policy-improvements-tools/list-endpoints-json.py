import json
import os


def extract_endpoints_no_redundant(json_path, output_file_path):
    try:
        with open(json_path, "r", encoding="utf-8") as file:
            api_spec = json.load(file)

        paths = api_spec.get("paths", {})
        if not paths:
            print("❌ No 'paths' key found in the JSON file.")
            return

        formatted_endpoints = []
        count = 1

        for path, methods in paths.items():
            for method, details in methods.items():
                if method.lower() not in ["get", "post", "put", "delete", "patch"]:
                    continue

                method_upper = method.upper()
                parameters = details.get("parameters", [])

                query_params = [
                    param["name"] for param in parameters if param.get("in") == "query"
                ]

                if query_params:
                    query_string = "&".join([f"{param}={{{param}}}" for param in query_params])
                    formatted_url = f"{method_upper} {path}?{query_string}"
                    formatted_endpoints.append(f"{count}. {formatted_url}")
                else:
                    formatted_endpoints.append(f"{count}. {method_upper} {path}")

                count += 1

        with open(output_file_path, "w", encoding="utf-8") as out_file:
            out_file.write("\n".join(formatted_endpoints))

        print(f"✅ Saved {count - 1} endpoints (no redundant prints) to: {output_file_path}")

    except FileNotFoundError:
        print(f"❌ JSON file not found: {json_path}")
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    current_dir = os.path.dirname(os.path.abspath(__file__))
    input_file = os.path.join(current_dir, "Sales-PISystems-APSK-II-Counter-SPA-V1.4.json")
    output_file = os.path.join(current_dir, "Sales-PISystems-APSK-II-Counter-SPA-V1.4.txt")

    extract_endpoints_no_redundant(input_file, output_file)
