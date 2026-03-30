import xml.etree.ElementTree as ET
import re

def extract_paths_per_rule(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()

    results = []

    for rule in root.findall('.//RouteRule'):
        name = rule.get('name', 'Unnamed Rule')
        condition_text = rule.findtext('Condition', default='')

        # Extract all paths from MatchesPath "..."
        paths = re.findall(r'MatchesPath\s+"([^"]+)"', condition_text)

        for path in paths:
            results.append((name, path))

    return results

if __name__ == "__main__":
    xml_file = 'example.xml'  # Path to your XML file
    routes = extract_paths_per_rule(xml_file)

    # Print result
    for name, path in routes:
        print(f"{name}: {path}")
