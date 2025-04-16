# CloudCode

_Created for the course "Methods and technologies for ensuring the quality of software products" V. N. Karazin Kharkiv National University_

Client-server application of cloud computing Python 3.10.6 code.

**[Docker Hub](https://hub.docker.com/r/card1nal/cloud_code_server)**

---

## Description

This project provides a secure environment for executing Python scripts in a separate directory in a separate Docker container, making code execution safe for the host compared to executing directly. The server receives the script file, executes it in a separate folder in the container and returns the result, errors and all generated files.

## Technologies Used

-   **Python 3.10.6** (for server-side execution)
-   **Flask** (for the API server)
-   **subprocess** (for running scripts securely)
-   **Threading** (to handle output buffering efficiently)
-   **Docker** (for easy server deployment and secure code execution)

## Project Structure

-   `Server/` - Contains the backend code for executing scripts.
-   `config.py` - Stores (server/client) configuration settings.
-   `Tasks/` - Directory where submitted scripts are stored and executed.
-   `Client/` - Example client-side implementation to send scripts to the server.
-   `Tests/` - Contains various tests for the application.

## Configuration

### **Server Configuration (`Config` class)**

The `Config` class defines the server's settings and configurations.

-   `UPLOAD_FOLDER = "/uploads"` – Directory where uploaded files (code scripts) will be stored temporarily related to volumes 'uploads' in docker-compose.yaml.
-   `PORT = 5000` – Port on which the server runs.
-   `DEBUG` – Variable indicates whether debugging mode is enabled for development purposes, defaults to `false`.
-   `EXECUTION_TIMEOUT = 10` – Maximum execution time for a script (in seconds).
-   `init()` – A static method that ensures the `UPLOAD_FOLDER` exists before execution.

### **Client Configuration (`Config` class)**

The `Config` class defines the client-side settings.

-   `API_URL = "http://localhost:5000/execute"` – The endpoint where the client sends code execution requests.
-   `API_KEY = "my_secret_key"` – A placeholder for an API key (not used for authentication but can be extended for security).
-   `TASKS_FOLDER = "Tasks"` – Directory where task files (code scripts) are stored before sending them to the server.

## How to Run the Server

### Step 1: Build the Image (Optional)

If you skip this step, the image `card1nal/cloud_code_server:latest` from Docker Hub will be used.

To build the image locally, use the following command:

```sh
docker build -t <YOUR-USER-NAME>/cloud_code_server:latest -t <YOUR-USER-NAME>/cloud_code_server:X --build-arg VERSION=X .
```

-   Replace `X` with your desired version.
-   Update the `image` field in `docker-compose.yaml` to:
    ```yaml
    image: <YOUR-USER-NAME>/cloud_code_server:latest
    ```

### Step 2: Start the Server

To run the server in different modes, use:

-   **Production (release) mode**
    ```sh
    docker compose up -d
    ```
-   **Development mode**
    ```sh
    docker compose up develop
    ```

The `-d` flag runs the containers in the background.

### Step 3: Stop and Restart the Server

-   Stop all running containers:
    ```sh
    docker compose down
    ```
-   Restart the server container:
    ```sh
    docker compose restart server
    ```
-   Restart the development container:
    ```sh
    docker compose restart develop
    ```
-   **Fully remove all containers, volumes, and orphaned containers**:
    ```sh
    docker compose down --volumes --remove-orphans
    ```

## How to Run the Client

Run the client script to send a Python file to the server:

```sh
python run_client.py
```

## Task Execution

-   Submitted scripts are saved in a unique directory.
-   The script runs in a controlled environment with a timeout.
-   Output, errors, and any created files are returned to the client.

## How to run Prometheus

1. To run Prometheus, use
    ```sh
    docker compose up prometheus
    ```

2. Open the address `http://127.0.0.1:9090/query` on the browser to see the Prometheus window.

## How to run Grafana

1. To run Grafana, use
    ```sh
    docker compose up grafana
    ```

2. Open the address `http://127.0.0.1:3000/login` on the browser to see the Grafana login window.

3. Enter "admin" in the login and password fields, then change the password.

4. Go to connections, then to Data sources and choose "Prometheus" as the data source. After that enter `http://prometheus:9090` in Connection field and press "Save & test"

5. In the "Queries" field, enter the necessary PromQL queries.

## Running Tests

The project includes three types of tests to ensure quality and functionality:

### Test Structure

- **Unit Tests** (`Tests/unit/`) - Tests for individual components in isolation
- **Integration Tests** (`Tests/integration/`) - Tests for component interactions
- **Functional Tests** (`Tests/features/`) - BDD-style tests using Behave

### Prerequisites

- Docker must be installed and running
- Docker Compose must be installed

### Running Tests with Docker Compose

We use Docker Compose profiles to run tests. All test commands are configured directly in the `docker-compose.yml` file, eliminating the need for additional scripts.

#### First-time Setup

Before running tests for the first time, it's recommended to create the necessary Docker volume:

```sh
docker volume create cloudcode_uploads
```

#### Running All Tests

To run all tests (unit, integration, and functional):

```sh
docker-compose --profile testing up tests
```

#### Running Specific Test Types

For running only Behave functional tests:
```sh
docker-compose --profile testing up tests-behave
```

For running only unit tests:
```sh
docker-compose --profile testing up tests-unit
```

For running only integration tests:
```sh
docker-compose --profile testing up tests-integration
```

#### Running Individual Test Files

For running specific test files or feature files:

```sh
# Run a specific feature file
docker-compose --profile testing run --rm tests-behave behave Tests/features/client.feature

# Run a specific integration test
docker-compose --profile testing run --rm tests-integration python -m unittest Tests/integration/test_integration_client.py

# Run a specific unit test
docker-compose --profile testing run --rm tests-unit python -m unittest Tests/unit/test_server.py
```

### Cleanup After Testing

After running tests, you can clean up containers with:

```sh
docker-compose --profile testing down
```

To remove orphan containers (recommended occasionally):

```sh
docker-compose --profile testing down --remove-orphans
```

### Interpreting Test Results

- A successful test run will display "OK" at the end of the output
- Failed tests will display "FAILED" along with details about the failures
- For functional tests, you'll see a summary of scenarios that passed or failed

## Notes

-   Ensure `config.py` is properly set up before running the server.
-   The execution timeout is enforced to prevent infinite loops.
-   Logs and error handling are included to capture execution failures.
