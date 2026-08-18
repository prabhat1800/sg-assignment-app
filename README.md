# sg-assignment-app
App Repo for Assignment
# Assignment Task Tracker

A small full-stack task tracker used to demonstrate a containerized FastAPI backend, a static frontend served by Nginx, automated testing and security checks, and Kubernetes deployment with Helm.

## Features

- Create tasks with a title.
- List all tasks.
- Mark tasks as complete or incomplete.
- Backend health endpoint for containers and Kubernetes probes.
- CORS configuration for the browser frontend.
- Docker Compose support for local container-based development.
- Helm chart for deploying the backend and frontend separately.
- GitHub Actions pipeline for tests, dependency checks, filesystem scanning, image builds, and image scanning.
- SonarCloud analysis prepared in CI but currently commented out.

## Architecture

```text
Browser
    |
    | http://localhost:8080
    v
Nginx frontend --------------------+
                                    |
                                    | HTTP API requests
                                    v
                             FastAPI backend
                             http://localhost:8000
                                    |
                                    v
                            In-memory TaskStore
```

The backend stores tasks in process memory. Data is lost when the backend process or container restarts, and multiple backend replicas do not share state. A persistent database is required for production use.

## Repository Layout

```text
.
|-- backend/
|   |-- app/
|   |   |-- main.py              # FastAPI application and routes
|   |   `-- store.py             # Thread-safe in-memory task store
|   |-- tests/test_api.py        # API tests
|   |-- Dockerfile               # Multi-stage backend image
|   `-- requirements.txt
|-- frontend/
|   |-- index.html               # Browser UI and API client
|   |-- config.js                # Runtime API base URL
|   `-- Dockerfile               # Nginx frontend image
|-- helm/assignment/             # Helm chart for Kubernetes
|-- .github/workflows/ci.yml     # CI pipeline
|-- dockercompose.yml            # Local Docker Compose definition
|-- pytest.ini
`-- sonar-project.properties
```

> Note: A Continuous Deployment workflow (`cd.yml`) that automates Helm-based
> deployment to GKE has been designed and reviewed, but has not yet been
> merged into `main`. See "Future Scope" below for details on the planned
> design.

## Prerequisites

For local Python development:

- Python 3.12
- pip

For container development:

- Docker Engine or Docker Desktop
- Docker Compose v2 (`docker compose`)

For Kubernetes deployment:

- Kubernetes cluster and `kubectl`
- Helm 3
- Container images available to the cluster
- A registry configuration appropriate for the target cluster

## Run Locally Without Docker

Create and activate a virtual environment, then install the backend dependencies:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

Start the API from the repository root:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`. Interactive API documentation is available at:

- Swagger UI: `http://localhost:8000/docs`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

The plain HTML frontend is configured to call `http://localhost:8000` by default. Serve the `frontend` directory with any static HTTP server, for example:

```bash
python -m http.server 8080 --directory frontend
```

Open `http://localhost:8080` in a browser.

To use another backend URL, edit `frontend/config.js`:

```javascript
window.APP_CONFIG = {
    API_BASE_URL: "http://localhost:8000"
};
```

The backend allows these browser origins by default:

```text
http://localhost:8080,http://127.0.0.1:8080
```

Set `ALLOWED_ORIGINS` to a comma-separated list when starting the backend if the frontend uses another origin:

```bash
ALLOWED_ORIGINS=http://localhost:8080,http://localhost:3000 \
  uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## Run With Docker Compose

The Compose file is named `dockercompose.yml`, so pass it explicitly:

```bash
docker compose -f dockercompose.yml up --build
```

Services:

| Service | Container port | Host URL |
| --- | ---: | --- |
| `frontend` | 80 | `http://localhost:8080` |
| `api` | 8000 | `http://localhost:8000` |

Open `http://localhost:8080` to use the application. Check the API directly with:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```

Stop and remove the containers with:

```bash
docker compose -f dockercompose.yml down
```

## API Reference

### Health check

```http
GET /health
```

Response:

```json
{"status":"ok"}
```

### List tasks

```http
GET /api/tasks
```

Response:

```json
{
  "items": [
    {
      "id": 1,
      "title": "Write documentation",
      "completed": false
    }
  ]
}
```

### Create a task

```http
POST /api/tasks
Content-Type: application/json
```

Request:

```json
{"title":"Deploy the application"}
```

The title is trimmed and must contain between 1 and 120 characters. A successful request returns `201 Created`:

```json
{
  "id": 1,
  "title": "Deploy the application",
  "completed": false
}
```

Example:

```bash
curl -X POST http://localhost:8000/api/tasks \
  -H 'Content-Type: application/json' \
  -d '{"title":"Deploy the application"}'
```

### Update task completion

```http
PATCH /api/tasks/{task_id}
Content-Type: application/json
```

Request:

```json
{"completed":true}
```

Example:

```bash
curl -X PATCH http://localhost:8000/api/tasks/1 \
  -H 'Content-Type: application/json' \
  -d '{"completed":true}'
```

Returns `404 Not Found` when the task ID does not exist.

## Testing

Install the backend dependencies, then run:

```bash
pytest -q backend/tests
```

The tests cover:

- API health checks.
- Task creation and listing.
- Updating task completion status.

The test configuration in `pytest.ini` adds the repository and backend directories to Python's import path.

## Docker Images

Build the images manually:

```bash
docker build -t assignment-api:local ./backend
docker build -t assignment-frontend:local ./frontend
```

Run the backend image:

```bash
docker run --rm -p 8000:8000 \
  -e ALLOWED_ORIGINS=http://localhost:8080 \
  assignment-api:local
```

Run the frontend image:

```bash
docker run --rm -p 8080:80 assignment-frontend:local
```

The backend image uses a multi-stage build. Dependencies are installed into a virtual environment in the builder stage, and only the virtual environment plus application code are copied into the runtime stage. The image exposes port `8000` and includes a Docker health check for `/health`.

The frontend image uses Nginx and copies `index.html` and `config.js` into the Nginx document root. Its container port is `80`.

## Kubernetes Deployment With Helm

The chart is located at `helm/assignment` and creates backend/frontend Deployments and Services. The frontend configuration is supplied through a ConfigMap. When enabled, an Ingress routes `/api` to the backend and `/` to the frontend.

Inspect the rendered manifests before installing:

```bash
helm lint helm/assignment
helm template assignment-prod helm/assignment \
  -f helm/assignment/values-prod.yaml
```

Install or upgrade the chart:

```bash
helm upgrade --install assignment helm/assignment \
  -f helm/assignment/values-prod.yaml \
  --set backend.image.repository=REGION-docker.pkg.dev/PROJECT/REPOSITORY/assignment-api-prod \
  --set backend.image.tag=IMAGE_TAG \
  --set frontend.image.repository=REGION-docker.pkg.dev/PROJECT/REPOSITORY/assignment-frontend-prod \
  --set frontend.image.tag=IMAGE_TAG
```

Check the deployment:

```bash
kubectl get deployments,pods,services
kubectl get ingress
kubectl describe deployment assignment-backend
```

This manual `helm upgrade --install` flow is the current supported deployment
method. See "Future Scope" for the planned automated CD workflow that will
perform these same steps from GitHub Actions.

### Helm values

The chart uses a common template set with environment-specific overlays:

| File | Environment | Intended use |
| --- | --- | --- |
| `values-dev.yaml` | `dev` | One replica, local API access, no ingress |
| `values-staging.yaml` | `staging` | Two replicas, GCE ingress, staging hostname |
| `values-prod.yaml` | `prod` | Three replicas, GCE ingress, production hostname |

The default values in `helm/assignment/values.yaml` provide the `dev` fallback configuration, so existing commands that do not select an environment continue to target development. The environment files override replicas, resources, image tags, origins, ingress settings, and frontend API configuration.

Important values include:

| Value | Purpose |
| --- | --- |
| `backend.image.repository` | Backend container image repository |
| `backend.image.tag` | Backend image tag |
| `backend.allowedOrigins` | Comma-separated browser origins accepted by the API |
| `frontend.image.repository` | Frontend container image repository |
| `frontend.image.tag` | Frontend image tag |
| `frontend.apiBaseUrl` | API base URL written to the frontend ConfigMap |
| `ingress.enabled` | Enables the Kubernetes Ingress |
| `ingress.className` | Ingress controller class, such as `gce` |
| `ingress.host` | Optional hostname for the Ingress rule |

For an Ingress that routes frontend and API traffic through the same host, set `frontend.apiBaseUrl` to an empty string. The browser then uses relative API paths such as `/api/tasks`.

Use a unique Helm release name per environment so resources do not collide:

```bash
helm upgrade --install assignment-dev helm/assignment -f helm/assignment/values-dev.yaml
helm upgrade --install assignment-staging helm/assignment -f helm/assignment/values-staging.yaml
helm upgrade --install assignment-prod helm/assignment -f helm/assignment/values-prod.yaml
```

The example hostnames in the staging and production overlays (`staging.example.com` and `example.com`) are placeholders and must be replaced with real DNS names before deployment. Supply image repositories and immutable commit-SHA tags through `--set` or a private values file.

Before using multiple backend replicas, add shared persistent storage or a database. The current in-memory store will give each replica a different task list.

## CI Pipeline

The workflow is defined in `.github/workflows/ci.yml`.

It runs for pushes to `develop`, `staging`, and `main`, and for pull requests targeting those branches (opened, reopened, or synchronized). The active jobs run for pushes to those environment branches and for pull requests from any source branch.

Branch-to-environment mapping:

| Branch | Environment | Repository suffix | Image tag |
| --- | --- | --- | --- |
| `develop` | `dev` | `-dev` | `<sha>` |
| `staging` | `staging` | `-staging` | `<sha>` |
| `main` | `prod` | `-prod` | `<sha>` |

### Job flow

```text
backend-tests-and-security      helm-validation
            |                          |
            +-----------+--------------+
                        |
                        v
                  build-images
                        |
                        v
             push-images-ar       (environment branch pushes only)
```

`helm-validation` lints and renders all three Helm overlays (`dev`, `staging`, `prod`) on every eligible push and pull request, independent of which branch triggered the run. `build-images` waits on both `backend-tests-and-security` and `helm-validation` before building and scanning images.

### Backend tests and security

This job:

1. Checks out the repository.
2. Installs Python 3.12.
3. Installs backend requirements and `pip-audit`.
4. Runs `pytest -q backend/tests`.
5. Runs `pip-audit -r backend/requirements.txt`.
6. Runs Trivy filesystem scanning for HIGH and CRITICAL vulnerabilities.

The Trivy scan uses `ignore-unfixed: true` and `exit-code: "1"`. The job fails when a matching vulnerability with an available fix is found.

### Build and scan images

This job runs only after `backend-tests-and-security` and `helm-validation` both succeed. It builds:

- `assignment-api:ci`
- `assignment-frontend:ci`

Trivy then scans both images for HIGH and CRITICAL vulnerabilities. A non-zero Trivy exit code fails the job.

### Push images to Google Artifact Registry

This job runs only after a successful push to an environment branch and a successful image build. It:

1. Validates Artifact Registry variables and Google Cloud secrets.
2. Authenticates with Google Cloud using Workload Identity Federation.
3. Configures Docker authentication for Artifact Registry.
4. Builds and pushes both images to environment-specific repositories with the Git commit SHA as the tag, for example `assignment-frontend-staging:a1b2c3d`.

The resulting image names are:

```text
assignment-api-dev:<sha>
assignment-frontend-dev:<sha>
assignment-api-staging:<sha>
assignment-frontend-staging:<sha>
assignment-api-prod:<sha>
assignment-frontend-prod:<sha>
```

The workflow validates all three Helm overlays on eligible pushes and pull requests. It currently only builds and publishes images; it does not deploy them to a cluster. Deployment today is performed manually with `helm upgrade --install` and the matching values file, as described in "Kubernetes Deployment With Helm" above, after the images are available in Artifact Registry. See "Future Scope" for the planned automated deployment workflow.

Required GitHub configuration:

The CI image-publishing job selects a GitHub Environment from the branch and reads its configuration:

| Branch | GitHub Environment |
| --- | --- |
| `develop` | `dev` |
| `staging` | `staging` |
| `main` | `prod` |

Create these three environments under **Repository settings > Environments**. Add the following **environment variables** to each environment for use by the CI image-publishing job:

| Name | Purpose |
| --- | --- |
| `GCP_PROJECT_ID` | Google Cloud project ID for that environment |
| `AR_LOCATION` | Artifact Registry location |
| `AR_REPOSITORY` | Artifact Registry repository |

Add these **environment secrets** to each environment:

| Name | Purpose |
| --- | --- |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | Workload Identity provider resource |
| `GCP_SERVICE_ACCOUNT` | Google service account email |

Do not store passwords, service-account keys, tokens, or other sensitive values in variables. Put sensitive values in environment secrets. This workflow uses Workload Identity Federation, so a long-lived Google service-account JSON key is not required.

### Sonar analysis

A SonarCloud job is present in the workflow as commented YAML. It is disabled currently and does not affect CI. To enable it:

1. Uncomment the `sonar-analysis` job in `.github/workflows/ci.yml`.
2. Add the `SONAR_TOKEN` repository secret.
3. Add `SONAR_PROJECT_KEY` and `SONAR_ORGANIZATION` repository variables.
4. Confirm the settings in `sonar-project.properties` match the SonarCloud project.

## Future Scope

### Planned: Continuous Deployment workflow

A `cd.yml` GitHub Actions workflow has been designed to automate the manual
Helm steps described above, but it has not yet been merged into `main`. Once
added, it is intended to work as follows:

- Triggered manually via `workflow_dispatch`, with inputs for the target
  environment (`dev`, `staging`, or `prod`) and an optional image tag
  (defaulting to the triggering commit SHA).
- Reuses the same three GitHub Environments (`dev`, `staging`, `prod`) created
  for CI, authenticating with the same Workload Identity Federation setup.
- Retags a previously published image to the current commit SHA when
  deploying an older build, then runs `helm upgrade --install` against the
  selected environment's values file and GKE cluster, and verifies the
  rollout with `kubectl rollout status`.
- Will require these **additional** environment variables/secrets beyond the
  ones already listed for CI, once merged:

  | Name | Purpose |
  | --- | --- |
  | `GKE_CLUSTER` | GKE cluster name used by CD |
  | `GKE_LOCATION` | GKE cluster region or zone |
  | `APP_HOST` | Ingress hostname |
  | `APP_URL` | Optional environment URL shown on the Actions job |
  | `INGRESS_CLASS_NAME` | Ingress class, usually `gce` |
  | `BACKEND_ALLOWED_ORIGINS` | Comma-separated browser origins |
  | `FRONTEND_API_BASE_URL` | Frontend API URL; empty for same-host ingress routing |

- Is expected to support environment protection rules such as required
  reviewers and deployment branch policies (for example, restricting the
  `prod` environment to deploys triggered from `main`, with required
  reviewers enabled).

Until this workflow is merged, deployments must be performed manually using
the `helm upgrade --install` commands documented above.

## Production Readiness Gaps

This repository is suitable as an assignment or demonstration application, but it is not production-ready without additional work. The main gaps are:

### Data and scaling

- `TaskStore` keeps all data in process memory. Tasks disappear after a restart, deployment, or crash.
- Multiple backend replicas do not share task state. The GKE values configure two replicas, so requests can return different task lists depending on which pod receives the request.
- There are no database migrations, backups, restore procedures, retention policies, or data-at-rest controls.
- There is no optimistic locking or transaction handling for concurrent updates.

Recommended work: replace the in-memory store with a managed database, add a repository/data-access layer, define migrations, configure backups, and test failure and recovery scenarios.

### Authentication and API security

- The API has no authentication or authorization. Anyone who can reach it can list, create, and update tasks.
- There is no rate limiting, request tracing ID, abuse protection, or API gateway policy.
- CORS is configurable, but the application should use an explicit production allowlist and review whether credentialed cross-origin requests are necessary.
- There is no documented TLS configuration. Production traffic should use HTTPS, with certificates managed by the ingress or a cloud load balancer.
- There are no security headers, access logs policy, or documented sensitive-data handling rules.

Recommended work: add identity-based access control, enforce HTTPS, apply least-privilege authorization, add rate limits and security headers, and place the service behind an authenticated gateway where appropriate.

### Planned: Enable SonarQube / SonarCloud analysis

A `sonar-analysis` job already exists in `.github/workflows/ci.yml` as
commented-out YAML and is not yet active. Enabling it is planned future work
and will involve:

1. Uncommenting the `sonar-analysis` job in `.github/workflows/ci.yml`.
2. Adding the `SONAR_TOKEN` repository secret.
3. Adding `SONAR_PROJECT_KEY` and `SONAR_ORGANIZATION` repository variables.
4. Confirming the settings in `sonar-project.properties` match the SonarCloud
   (or self-hosted SonarQube) project configuration.
5. Optionally configuring a quality gate that blocks merges to `develop`,
   `staging`, or `main` when code coverage, duplication, or maintainability
   thresholds are not met.

Until this is enabled, code-quality analysis is not part of the automated
pipeline, and reviewers should rely on manual code review, `pytest`,
`pip-audit`, and Trivy results.

### Planned: DNS and TLS certificate provisioning

The `staging` and `production` Helm overlays currently reference placeholder
hostnames (`staging.example.com` and `example.com`) with no real DNS records
or TLS certificates behind them, and the Ingress resource has no TLS block
configured. Planned work includes:

1. Registering or delegating real DNS records (A or CNAME) for the staging
   and production hostnames, pointed at the static IP address reserved for
   the GKE Ingress in each environment.
2. Provisioning TLS certificates using one of:
   - A Google-managed certificate via a `ManagedCertificate` resource,
     referenced from the Ingress annotations (GKE-native approach), or
   - `cert-manager` with a Let's Encrypt `ClusterIssuer`, if certificate
     management needs to be portable across non-GKE clusters.
3. Updating `ingress.host` in `values-staging.yaml` and `values-prod.yaml`
   with the real hostnames once DNS is live and verified.
4. Enabling HTTPS redirection and TLS termination at the Ingress once
   certificates are issued and validated, and confirming `frontend.apiBaseUrl`
   and `backend.allowedOrigins` are updated to use `https://` where
   applicable.

Until this is completed, staging and production Ingress hosts should be
treated as placeholders, and the application should not be exposed on the
public internet under those hostnames.

### Application behavior and reliability

- Error handling is minimal and there is no consistent error response schema for clients.
- There are no pagination, filtering, deletion, audit history, or idempotency features.
- The API has no explicit timeouts or safeguards for future external dependencies.
- There are no background-job, retry, or dead-letter patterns if asynchronous work is introduced.
- The frontend has no user authentication flow, offline behavior, accessibility audit, end-to-end tests, or production error reporting.

Recommended work: define the API contract, add validation and consistent errors, introduce pagination as data grows, and add browser-level tests for the critical user journeys.

### Observability and operations

- The application exposes only a basic health endpoint. It does not expose metrics, distributed traces, or structured application logs.
- There are no dashboards, alerts, SLOs, runbooks, or documented incident procedures.
- Kubernetes probes verify process availability but do not verify database or dependency readiness.
- There is no graceful shutdown or documented rollout strategy for schema and application changes.

Recommended work: emit structured logs, add metrics and tracing, define alerts for errors and latency, add dependency-aware readiness checks, and document rollback and incident procedures.

### Container and Kubernetes hardening

- The backend container does not declare a non-root user. Container processes should run as an unprivileged user where possible.
- Kubernetes manifests do not define security contexts, network policies, pod disruption budgets, autoscaling, or a service account strategy.
- The default Helm values contain a concrete Artifact Registry repository and use `latest` as the image tag. Environment overlays provide environment-specific repositories, but immutable commit-SHA tags should still be supplied during deployment.
- Ingress TLS, authentication, WAF policy, and HTTP security configuration are not defined in the chart.
- Resource requests and limits exist, but there is no Horizontal Pod Autoscaler or capacity plan.

Recommended work: run containers as non-root, add Kubernetes security contexts and network policies, pin images by immutable digest or commit SHA, configure TLS and ingress controls, and establish autoscaling and disruption policies.

### CI/CD and supply-chain controls

- The active CI pipeline runs unit tests, `pip-audit`, Trivy scans, image builds, and image scans, but the SonarCloud job is currently commented out.
- Automated deployment (CD) is designed but not yet merged into `main`; deployments are currently manual. See "Future Scope" above.
- Test coverage is small and currently focuses on health, creation/listing, and completion updates. There are no integration, contract, end-to-end, load, or resilience tests.
- Dependencies use a mixture of ranges and exact versions, and there is no lockfile or automated dependency update policy.
- The workflow pushes images for `develop`, `staging`, and `main`, but it does not deploy them, verify a deployed environment, or require an approval gate for production.
- There is no signed-image, provenance, SBOM publication, or registry retention policy documented.

Recommended work: merge and enable the planned CD workflow with staged rollout and approval controls, enable and enforce code-quality analysis, expand test coverage, use reproducible dependency locking, publish SBOMs and provenance, and scan dependencies continuously.

## Security Notes

- Keep cloud credentials in GitHub Actions secrets or workload identity configuration, never in source files.
- Keep `ALLOWED_ORIGINS` restricted to the frontend origins that need access.
- Review Trivy and `pip-audit` findings before changing failure thresholds.
- Update base images and dependencies regularly.
- The current API has no authentication or authorization and should not be exposed publicly without an access-control layer.
- The current in-memory store is not durable and is not suitable for production data.

## Troubleshooting

### The frontend cannot reach the API

Confirm that the API is running on port `8000`, that `frontend/config.js` points to the correct URL, and that the API's `ALLOWED_ORIGINS` includes the frontend origin.

For Compose, use:

```bash
docker compose -f dockercompose.yml logs api
docker compose -f dockercompose.yml ps
```

### Trivy fails the pipeline

Read the affected image, package, vulnerability ID, installed version, and fixed version in the Trivy output. Update the Docker base image or system/application dependency, rebuild the image, and scan it again. `ignore-unfixed: true` does not ignore vulnerabilities that already have a published fix.

### Tasks disappear

This is expected after a backend restart because tasks are stored only in memory. Use a shared database and update `TaskStore` or introduce a repository abstraction before relying on the application for durable data.

### Helm pods are not ready

Inspect pod events and logs:

```bash
kubectl get pods
kubectl describe pod POD_NAME
kubectl logs deployment/RELEASE_NAME-backend
kubectl logs deployment/RELEASE_NAME-frontend
```

The backend readiness and liveness probes call `/health` on port `8000`; the frontend probes `/` on port `80`.

## License

No license file is currently included in this repository.
