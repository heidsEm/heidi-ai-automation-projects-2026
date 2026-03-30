import xml.etree.ElementTree as ET

def convert_assign_message_advanced(xml_str):
    root = ET.fromstring(xml_str)
    policies = []

    # Convert headers
    headers = root.find(".//Headers")
    if headers is not None:
        for header in headers.findall("Header"):
            name = header.get("name")
            value = header.text or ""
            policies.append(f'''<set-header name="{name}" exists-action="override">\n  <value>{value}</value>\n</set-header>''')

    # Convert query parameters
    query_params = root.find(".//QueryParams")
    if query_params is not None:
        for param in query_params.findall("QueryParam"):
            name = param.get("name")
            value = param.text or ""
            policies.append(f'''<set-query-parameter name="{name}" exists-action="override">\n  <value>{value}</value>\n</set-query-parameter>''')

    # Convert payload (if present)
    payload = root.find(".//Payload")
    if payload is not None:
        # Safely preserve formatting & CDATA
        payload_content = ET.tostring(payload, encoding="unicode", method="xml")
        inner_xml = payload_content.split(">", 1)[1].rsplit("</", 1)[0]  # Extract inside of <Payload>...</Payload>
        policies.append(f'''<set-body template="none">\n  <value><![CDATA[\n{inner_xml.strip()}\n  ]]></value>\n</set-body>''')

    return "\n\n".join(policies)

if __name__ == "__main__":
    apigee_policy_xml = """
    <AssignMessage async="false" continueOnError="false" enabled="true" name="AssignMessage-XMLPayload">
        <DisplayName>AssignMessage-XMLPayload</DisplayName>
        <Properties/>
        <Set>
            <Headers>
                <Header name="Accept">application/xml</Header>
            </Headers>
            <QueryParams>
                <QueryParam name="senderParty">{senderParty}</QueryParam>
                <QueryParam name="senderService">{senderService}</QueryParam>
                <QueryParam name="receiverParty"/>
                <QueryParam name="receiverService"/>
                <QueryParam name="interface">{queryInterface}</QueryParam>
                <QueryParam name="interfaceNamespace">{interfaceNamespace}</QueryParam>
            </QueryParams>
            <Payload content-type="application/xml">
                <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
                    <soapenv:Body>
                        {requestPayload}
                    </soapenv:Body>
                </soapenv:Envelope>
            </Payload>
        </Set>
        <IgnoreUnresolvedVariables>true</IgnoreUnresolvedVariables>
        <AssignTo createNew="false" transport="http" type="request"/>
    </AssignMessage>
    """
    converted = convert_assign_message_advanced(apigee_policy_xml)
    print("🔄 Converted Azure APIM Policy:\n")
    print(converted)
