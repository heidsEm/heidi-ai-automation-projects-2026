import json
import os
import xml.etree.ElementTree as ET


def extract_from_xml(file_path):
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()

        content = root.find('.//Content')
        if content is not None and content.text:
            try:
                content_json = json.loads(content.text.strip())

                carrier_id = content_json.get('carrier_id')      # May be None
                tenant_name = content_json.get('tenant_name')    # May be None

                return carrier_id, tenant_name
            except json.JSONDecodeError:
                print(f"[Error] Invalid JSON in <Content> of file: {file_path}")
        return None, None
    except ET.ParseError:
        print(f"[Error] Failed to parse XML: {file_path}")
        return None, None
    except Exception as e:
        print(f"[Error] {e} in file: {file_path}")
        return None, None

def extract_all_from_folder(folder_path):
    carrier_ids = set()
    tenant_names = set()

    for filename in os.listdir(folder_path):
        if filename.endswith('.xml'):
            full_path = os.path.join(folder_path, filename)
            carrier_id, tenant_name = extract_from_xml(full_path)

            if carrier_id:
                carrier_ids.add(carrier_id)
            if tenant_name:
                tenant_names.add(tenant_name)

    return carrier_ids, tenant_names

if __name__ == "__main__":
    folder_path = r"C:\Users\heidi.embat\OneDrive - Accenture\Desktop\Python\mix-proxypath\traces"  # Your folder path

    if not os.path.isdir(folder_path):
        print(f"[Error] Not a directory: {folder_path}")
    else:
        carrier_ids, tenant_names = extract_all_from_folder(folder_path)

        print("\nUnique carrier_id values:")
        for cid in sorted(carrier_ids):
            print(f"- {cid}")

        print("\nUnique tenant_name values:")
        for tname in sorted(tenant_names):
            print(f"- {tname}")