from diagrams import Diagram, Cluster, Edge
from diagrams.azure.network import ApplicationGateway
from diagrams.azure.identity import ActiveDirectory
from diagrams.azure.integration import APIManagement
from diagrams.onprem.client import Client
from diagrams.onprem.network import Internet
from diagrams.generic.compute import Rack, Servers
from diagrams.azure.monitor import Monitor, LogAnalytics, ApplicationInsights
from diagrams.azure.database import SqlDatabase

with Diagram("Azure APIM Architecture (Internal Mode with App Gateway)",
             show=True,
             filename="azure_apim_architecture_clean",
             direction="LR"):

    # --- Clients and Entry Point ---
    clients = [Client("Web App"), Client("Mobile App")]
    internet = Internet("Public Internet")
    app_gateway_waf = ApplicationGateway("App Gateway with WAF (Public IP)")

    # --- Virtual Network (represented as a cluster only) ---
    with Cluster("Azure Virtual Network"):
        # Subnets (represented with labels only)
        app_gateway_subnet = Servers("App Gateway Subnet")
        apim_subnet = Servers("APIM Subnet")
        backend_subnet = Servers("Backend Subnet")

        # # NSGs
        # nsg_apim = NetworkSecurityGroups("NSG (APIM)")
        # nsg_backend = NetworkSecurityGroups("NSG (Backend)")

        # --- Azure API Management ---
        with Cluster("Azure API Management (Internal Mode)"):
            apim_gateway = APIManagement("API Gateway")
            apim_mgmt = APIManagement("Mgmt Plane")
            apim_dev_portal = APIManagement("Dev Portal")

            # --- API Policies ---
            with Cluster("API Policies"):
                ldap = Servers("LDAP Auth")
                ip_whitelist = Servers("IP Whitelist")
                subs_key = Servers("Subscription Key")
                ssl_validation = Servers("SSL Validation")
                jwt_auth = ActiveDirectory("JWT Auth")

                quota = Servers("Quota")
                spike = Servers("Spike Arrest")
                rate_limit = Servers("Req/Res Limit")

                # Policy flows
                apim_gateway >> Edge(label="Applies policies") >> [ldap, ip_whitelist, subs_key, ssl_validation, jwt_auth]
                apim_gateway >> Edge(label="Applies policies") >> [quota, spike, rate_limit]

        # --- Backend Systems ---
        with Cluster("Backend Systems"):
            sap = Rack("SAP System")
            boomi = Servers("Boomi Integration")
            microservices = Servers("Other Microservices")
            database = SqlDatabase("Backend DB")

            apim_gateway >> Edge(label="Calls Backends") >> [sap, boomi, microservices, database]

    # --- Monitoring & Analytics ---
    with Cluster("Monitoring & Analytics"):
        monitor = Monitor("Azure Monitor")
        log_ws = LogAnalytics("Log Analytics")
        app_insights = ApplicationInsights("App Insights")

    # --- Connections ---

    # External flow
    clients >> internet >> app_gateway_waf
    app_gateway_waf >> Edge(label="TLS Termination & WAF") >> app_gateway_subnet
    app_gateway_subnet >> Edge(label="Internal Traffic") >> apim_subnet
    apim_subnet >> nsg_apim >> apim_gateway

    # Dev Portal and Mgmt Plane
    clients >> internet >> Edge(label="Access Dev Docs") >> apim_dev_portal
    apim_dev_portal >> Edge(label="Try APIs") >> apim_gateway
    apim_mgmt >> Edge(style="dotted", label="Mgmt Access") >> apim_gateway

    # Backend connectivity
    apim_gateway >> Edge(label="Private Endpoint / Peering") >> nsg_backend >> backend_subnet
    backend_subnet >> [sap, boomi, microservices, database]

    # Monitoring and logging
    apim_gateway >> Edge(label="Sends Logs") >> monitor >> log_ws
    apim_gateway >> Edge(label="Telemetry") >> app_insights