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

### Step 2: Create Volume

Before starting the server for the first time, create a Docker volume for uploads:

```sh
docker volume create --name cloudcode_uploads
```

### Step 3: Start the Server

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

### Step 4: Access the Web Interface

After starting the server, you can access the web interface at:

```
http://localhost:5000
```

The web interface allows you to:
- Upload Python code files
- Enter an API key (required for code execution)
- Execute the code and view the results
- Download files that were created during execution

### Step 5: Stop and Restart the Server

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

## Running Tests

The project includes three types of tests to ensure quality and functionality:

### Test Structure

- **Server Tests** (`Tests/server/`)
  - Unit Tests - Tests for individual server components
  - Integration Tests - Tests for server component interactions
  - Functional Tests (Behave) - BDD-style tests for server functionality

- **Client Tests** (`Tests/client/`)
  - Unit Tests - Tests for individual client components
  - Integration Tests - Tests for client component interactions
  - Functional Tests (Behave) - BDD-style tests for client functionality

- **Common Tests** (`Tests/common/`)
  - Integration Tests - Tests for client-server interactions
  - Functional Tests (Behave) - BDD-style tests for end-to-end functionality

### Prerequisites

- Docker must be installed and running (for server tests)
- Docker Compose must be installed (for server tests)
- Python 3.6+ (for client and common tests)
- Behave package installed (for BDD tests): `pip install behave`

### Running Server Tests with Docker Compose

Server tests are configured to run in Docker containers:

```sh
# Run all server tests
docker compose run --rm tests-server

# Run only server unit tests
docker compose run --rm tests-server-unit

# Run only server integration tests
docker compose run --rm tests-server-integration

# Run only server behavior tests
docker compose run --rm tests-server-behave
```

### Running Client Tests

To run client tests locally:

```sh
# Run all client tests
python Tests/run_client_tests.py

# Run specific client tests
python -m unittest discover -s Tests/client/unit
python -m unittest discover -s Tests/client/integration
python -m behave Tests/client/features
```

### Running Common Tests

To run common tests (requires server to be running):

```sh
# Run all common tests
python Tests/run_common_tests.py

# Run specific common tests
python -m unittest Tests/common/test_integration.py
python -m behave Tests/common/features
```

### Cleanup After Testing

After running Docker tests, clean up containers with:

```sh
docker compose --profile testing down
```

To remove orphan containers:

```sh
docker compose --profile testing down --remove-orphans
```

### Interpreting Test Results

- A successful test run will display "OK" at the end of the output
- Failed tests will display "FAILED" along with details about the failures
- For functional tests, you'll see a summary of scenarios that passed or failed

## Notes

- The server tests are designed to run in Docker containers for isolation
- Client tests run locally and can be executed without Docker
- Common tests verify the interaction between client and server
- If behave is not installed, the test runner scripts will skip behavior tests with a warning
- Ensure `config.py` is properly set up before running the server.
- The execution timeout is enforced to prevent infinite loops.
- Logs and error handling are included to capture execution failures.
