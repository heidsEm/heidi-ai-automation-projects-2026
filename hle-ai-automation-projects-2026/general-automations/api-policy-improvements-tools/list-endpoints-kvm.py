import os
import re
import xml.etree.ElementTree as ET


def list_kvm_endpoints(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        for flow in root.findall(".//Flow"):
            flow_name = flow.attrib.get("name", "Unnamed Flow")
            condition = flow.findtext("Condition", "")

            # Extract path from condition
            paths = re.findall(
                r'proxy\.pathsuffix\s+MatchesPath\s+"([^"]+)"', condition
            )

            # Check for KVM step inside the <Request> section
            kvm_steps = []
            request = flow.find("Request")
            if request is not None:
                for step in request.findall("Step"):
                    step_name = step.findtext("Name", "")
                    if step_name.startswith("KVM-"):
                        kvm_steps.append(step_name)

            # Output only if there is at least one KVM step
            if paths and kvm_steps:
                print(f"\nFlow : {flow_name}")
                for i, path in enumerate(paths, 1):
                    for kvm_step in kvm_steps:
                        print(f"{i}. {path} - {kvm_step}")

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

    list_kvm_endpoints(xml_file_path)
