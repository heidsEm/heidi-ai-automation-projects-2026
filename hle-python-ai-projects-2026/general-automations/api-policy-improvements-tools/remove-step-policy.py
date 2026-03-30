import xml.etree.ElementTree as ET

# Set of policy names to remove
POLICIES_TO_REMOVE = {
    "JWT-GenerateJWT",
    "SC-Janrain-token-EU",
    "SC-Janrain-token-RU",
    "SC-Janrain-token-USLT",
    "SC-Janrain-token-USQA",
    "SC-Janrain-token-US"
}

def remove_matching_steps(xml_content: str) -> str:
    """
    Remove all <Step> elements whose <Name> text matches any policy in POLICIES_TO_REMOVE.

    Args:
        xml_content: XML content as a string.

    Returns:
        Modified XML content as a string.
    """
    root = ET.fromstring(xml_content)

    # Collect steps to remove (avoid modifying tree while iterating)
    steps_to_remove = []
    for step in root.findall(".//Step"):
        name = step.find("Name")
        if name is not None and name.text in POLICIES_TO_REMOVE:
            steps_to_remove.append(step)

    # Remove collected steps by finding their parent
    for step in steps_to_remove:
        # xml.etree.ElementTree does not have getparent(), so find manually
        for parent in root.iter():
            if step in list(parent):
                parent.remove(step)
                break

    return ET.tostring(root, encoding="unicode")

if __name__ == "__main__":
    with open("input.xml", "r", encoding="utf-8") as f:
        xml_data = f.read()

    cleaned_xml = remove_matching_steps(xml_data)

    with open("output.xml", "w", encoding="utf-8") as f:
        f.write(cleaned_xml)

    print("✅ Steps removed and output saved to 'output.xml'")