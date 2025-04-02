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

## How to Run Tests

CloudCode includes a set of automated tests for four main components: the client, the server, code security checks, and integration scenarios.

### Testing the Code Security Checker Module (`python_security_checker.py`)

These tests verify the detection and removal of dangerous code:

```sh
python -m behave tests/features/security_checker.feature
```

### Testing the Server Component

These tests verify the server functionality for processing requests: 

```sh
python -m behave tests/features/server.feature
```

### Testing the Client Component

These tests verify the client functionality for sending tasks: 

```sh
python -m behave tests/features/client.feature
```

### Testing the Integration Component

These tests verify the seamless interaction between the client and server components, ensuring tasks are processed efficiently and connections are maintained:

```sh
python -m behave tests/features/integration.feature
```

### Running All Tests Together

To run all tests at once, execute:

```sh
python -m behave tests/features/
```

## Task Execution

-   Submitted scripts are saved in a unique directory.
-   The script runs in a controlled environment with a timeout.
-   Output, errors, and any created files are returned to the client.

## Notes

-   Ensure `config.py` is properly set up before running the server.
-   The execution timeout is enforced to prevent infinite loops.
-   Logs and error handling are included to capture execution failures.
