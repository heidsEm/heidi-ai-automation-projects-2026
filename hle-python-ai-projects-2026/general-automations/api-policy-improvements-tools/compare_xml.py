import xml.etree.ElementTree as ET
import sys
import re

def clean_xml_string(xml_str):
    # Remove invalid XML characters using regex
    # XML 1.0 valid chars: https://www.w3.org/TR/xml/#charsets
    # This regex keeps valid XML chars only
    RE_XML_ILLEGAL = (
        u'([\u0000-\u0008\u000B\u000C\u000E-\u001F\uFFFE\uFFFF])'
    )
    return re.sub(RE_XML_ILLEGAL, '', xml_str)

def parse_xml_file(file_path):
    try:
        tree = ET.parse(file_path)
        return tree
    except ET.ParseError as e:
        print(f"Parse error in '{file_path}': {e}")
        print("Attempting to clean XML and retry parsing...")

        with open(file_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

        cleaned_xml = clean_xml_string(xml_content)

        try:
            tree = ET.ElementTree(ET.fromstring(cleaned_xml))
            print(f"Parsing succeeded after cleaning '{file_path}'.")
            return tree
        except ET.ParseError as e2:
            print(f"Failed to parse cleaned XML in '{file_path}': {e2}")
            return None

def compare_elements(e1, e2, path=""):
    if e1.tag != e2.tag:
        print(f"Tag mismatch at {path}: {e1.tag} != {e2.tag}")
        return False

    if (e1.text or "").strip() != (e2.text or "").strip():
        print(f"Text mismatch at {path}/{e1.tag}: '{e1.text}' != '{e2.text}'")
        return False

    if e1.attrib != e2.attrib:
        print(f"Attributes mismatch at {path}/{e1.tag}: {e1.attrib} != {e2.attrib}")
        return False

    if len(e1) != len(e2):
        print(f"Children count mismatch at {path}/{e1.tag}: {len(e1)} != {len(e2)}")
        return False

    for c1, c2 in zip(e1, e2):
        if not compare_elements(c1, c2, path + "/" + e1.tag):
            return False

    return True

def compare_xml(file1, file2):
    tree1 = parse_xml_file(file1)
    tree2 = parse_xml_file(file2)

    if tree1 is None or tree2 is None:
        print("One or both XML files could not be parsed.")
        return

    root1 = tree1.getroot()
    root2 = tree2.getroot()

    if compare_elements(root1, root2):
        print("XML files are identical.")
    else:
        print("XML files differ.")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python compare_xml.py file1.xml file2.xml")
    else:
        compare_xml(sys.argv[1], sys.argv[2])
