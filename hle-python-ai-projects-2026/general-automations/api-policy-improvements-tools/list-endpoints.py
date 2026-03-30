import xml.etree.ElementTree as ET
import re
import os

def list_pathsuffix_endpoints(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        endpoints = []

        # Iterate through all XML elements
        for elem in root.iter():
            if elem.text:
                # Extract only the endpoint inside double quotes
                found = re.findall(r'proxy\.pathsuffix\s+MatchesPath\s+"([^"]+)"', elem.text)
                endpoints.extend(found)

        if endpoints:
            print("Endpoints found in 'proxy.pathsuffix MatchesPath':")
            for i, ep in enumerate(endpoints, 1):
                print(f"{i}. {ep}")
        else:
            print("No endpoints found.")

    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
    except FileNotFoundError:
        print("XML file not found.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    # Assumes the XML file is named 'example.xml' in the same directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    xml_file_path = os.path.join(current_dir, "example.xml")
    
    list_pathsuffix_endpoints(xml_file_path)
