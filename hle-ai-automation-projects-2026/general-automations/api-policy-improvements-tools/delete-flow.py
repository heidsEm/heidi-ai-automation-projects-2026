import xml.etree.ElementTree as ET
import re

# === CONFIG ===
XML_FILE_PATH = "example.xml"
WHITELISTED_FLOWS = [
    "GET /traits/**",
    "GET /health/traits",
    "GET /reference-data",
    "POST /reference-data",
    "GET /health/reference-data",
    "GET /logging-configs",
    "POST /logging-configs",
    "DELETE /logging-configs/**",
    "PATCH /logging-configs/**"
]

def extract_paths_from_condition(condition_text):
    """Extract proxy.pathsuffix MatchesPath values from a condition string."""
    return re.findall(r'proxy\.pathsuffix\s+MatchesPath\s+"([^"]+)"', condition_text or "")

def remove_path_expressions(condition_text, paths_to_keep):
    """
    Keep only expressions for paths_to_keep.
    Remove all proxy.pathsuffix MatchesPath that don't match.
    """
    if not condition_text:
        return condition_text

    # Find all path expressions in the condition
    all_paths = extract_paths_from_condition(condition_text)
    paths_to_remove = [p for p in all_paths if p not in paths_to_keep]

    for path in paths_to_remove:
        pattern = rf'\(*\s*proxy\.pathsuffix\s+MatchesPath\s+"{re.escape(path)}"\s*\)*'
        condition_text = re.sub(pattern, '', condition_text)

    # Clean up empty or broken condition strings
    condition_text = re.sub(r'\s+(or|and)\s+(?=\)|$)', '', condition_text)
    condition_text = re.sub(r'\(\s*\)', '', condition_text)
    condition_text = re.sub(r'\s+', ' ', condition_text).strip()

    if not condition_text or condition_text in ['or', 'and']:
        return None

    return condition_text

def remove_unwanted_flows_and_clean_routes(xml_path, keep_flows):
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        paths_to_keep = set()

        # === STEP 1: Filter Flows and Collect Kept Paths ===
        for flows_elem in root.findall(".//Flows"):
            for flow in list(flows_elem.findall("Flow")):
                flow_name = flow.attrib.get("name", "")
                condition_elem = flow.find("Condition")
                if flow_name in WHITELISTED_FLOWS:
                    print(f"✅ Kept Flow: {flow_name}")
                    if condition_elem is not None:
                        paths = extract_paths_from_condition(condition_elem.text)
                        paths_to_keep.update(paths)
                else:
                    print(f"❌ Removed Flow: {flow_name}")
                    flows_elem.remove(flow)

        # === STEP 2: Clean RouteRules ===
        for route_rule in root.findall(".//RouteRule"):
            condition_elem = route_rule.find("Condition")
            target_elem = route_rule.find("TargetEndpoint")

            if condition_elem is not None:
                original_condition = condition_elem.text or ""
                all_paths = extract_paths_from_condition(original_condition)
                relevant_paths = [p for p in all_paths if p in paths_to_keep]

                if not relevant_paths:
                    print(f"🧹 Removed entire <Condition> and <TargetEndpoint> from RouteRule: {route_rule.attrib.get('name')}")
                    route_rule.remove(condition_elem)
                    if target_elem is not None:
                        route_rule.remove(target_elem)
                    continue

                updated_condition = remove_path_expressions(original_condition, paths_to_keep)
                if updated_condition:
                    print(f"🧹 Updated <Condition> in RouteRule: {route_rule.attrib.get('name')}")
                    condition_elem.text = updated_condition
                else:
                    print(f"🧹 Removed <Condition> and <TargetEndpoint> due to empty result in RouteRule: {route_rule.attrib.get('name')}")
                    route_rule.remove(condition_elem)
                    if target_elem is not None:
                        route_rule.remove(target_elem)
            else:
                print(f"✅ No condition in RouteRule {route_rule.attrib.get('name')} — unchanged.")

        # === STEP 3: Save XML ===
        output_file = "filtered_" + xml_path.split("/")[-1]
        tree.write(output_file, encoding="utf-8", xml_declaration=True)
        print(f"\n✅ Filtered XML saved to: {output_file}")

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    remove_unwanted_flows_and_clean_routes(XML_FILE_PATH, WHITELISTED_FLOWS)
