🚀 SwiftDeploy CLI


🧠 Project Overview

SwiftDeploy is a declarative deployment tool that automates infrastructure setup using a single configuration file (manifest.yaml).

The system eliminates manual configuration by generating all required deployment artifacts, including Docker Compose and Nginx configurations, and managing the full lifecycle of the application through a CLI interface.

The manifest acts as the single source of truth, ensuring consistency, reproducibility, and controlled system behavior.

🎯 Objectives

This project was built to achieve the following:

1. Define infrastructure using a declarative YAML manifest
2. Build a CLI tool to manage infrastructure lifecycle
3. Automatically generate Nginx and Docker Compose configurations
4. Run a containerized API service with health checks
5. Implement canary and stable deployment modes
6. Enforce a single entry point through Nginx
7. Provide structured logging for observability
8. Ensure deployments are reproducible and validated

⚙️ What Was Implemented

- A CLI tool (swiftdeploy) with multiple subcommands
- Manifest parsing using YAML as the system configuration
- Template-based generation of docker-compose.yml & nginx.conf
- A containerized API service with:
   1. / endpoint for responses
   2. /healthz endpoint for health checks
   3. /chaos endpoint for simulated failures (canary mode)
- Environment-based mode switching (stable and canary)
-  Docker networking and container lifecycle management
- Health check integration for service readiness
- Nginx reverse proxy configuration with:
   1. request forwarding
   2. timeout control
   3. structured access logging
   4. JSON error responses
   5. Volume management for logs
- Security practices with non-root container execution and dropped Linux capabilities
- Validation checks before deployment to prevent misconfiguration


📦 Project Structure
swiftdeploy/
├── manifest.yaml        # only file you edit
├── swiftdeploy          # CLI tool
├── app/                 # API service (FastAPI)
├── templates/           # config templates
├── Dockerfile
├── nginx.conf           # generated
├── docker-compose.yml   # generated
└── README.md


🧰 CLI Workflow

The CLI manages the full lifecycle of the system:

1. Make it executable `chmod +x swiftdeploy`

1. Init `./swiftdeploy init`: it generates all required configuration files from the manifest
2. Validate `./swiftdeploy validate`: performs pre-deployment checks to ensure system correctness
3. Deploy `./swiftdeploy deploy`: builds and starts the full stack, ensuring services are healthy
4. Promote `./swiftdeploy promote canary` or `./swiftdeploy promote stable`: switches between deployment modes (stable ↔ canary) with controlled restart
5. Teardown `./swiftdeploy teardown`: stops and removes all containers, networks, and generated resources

🐤 Canary vs Stable

The system supports two deployment modes controlled via the MODE environment variable:

- Stable: this is the default production behavior where all responses reflect the standard application state.
- Canary: this is a controlled test mode used to simulate and validate behavior before full rollout.

Canary is just a safe way to test changes before fully committing. Think of it as “try it first before giving it to everyone”

🌐 System Behavior

1. All traffic is routed through Nginx as the only exposed entry point
2. The API service runs inside a container and is not directly exposed
3. Nginx forwards requests to the service over a Docker network
4. Health checks ensure service availability before traffic is served
5. Logs are generated for every request to provide visibility into system activity

🌐 Accessing the Service 

- Service Access

All requests are routed through Nginx which acts as the single entry point.

The service is available on:

http://localhost:8080/

- Health Check Endpoint

Service health can be verified using:

http://localhost:8080/healthz

This endpoint is used by the system to determine service readiness and uptime.

🧪 Testing the Deployment

To verify the system is running correctly:

curl http://localhost:8080/
curl http://localhost:8080/healthz

The root endpoint (/) returns application response data
The health endpoint (/healthz) confirms the service is operational

🏁 Conclusion

This project demonstrates how infrastructure can be fully defined and managed through code. By shifting from manual configuration to a declarative approach, SwiftDeploy ensures consistent deployments, reduces errors and simplifies system management.

It reflects real-world DevOps practices such as Infrastructure as Code, automated validation and controlled deployment strategies, providing a foundation for building reliable and scalable systems.
