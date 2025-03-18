# CloudCode

_Created for the course "Methods and technologies for ensuring the quality of software products" V. N. Karazin Kharkiv National University_

Client-server application of cloud computing Python 3.10.6 code.

---

## Description

This project provides a secure environment for executing Python scripts in a separate directory. The server receives a script file, executes it in a separate folder, and returns the result, errors, and all generated files.

## Warning!

This project does not yet check the code before execution, so it may be unsafe to execute, it is recommended to use isolated runtime environments such as Docker to execute potentially unsafe code.

## Technologies Used

-   **Python 3.10.6** (for server-side execution)
-   **Flask** (for the API server)
-   **subprocess** (for running scripts securely)
-   **Threading** (to handle output buffering efficiently)

## Project Structure

-   `Server/` - Contains the backend code for executing scripts.
-   `config.py` - Stores (server/client) configuration settings.
-   `Tasks/` - Directory where submitted scripts are stored and executed.
-   `Client/` - Example client-side implementation to send scripts to the server.

## Configuration

### **Server Configuration (`Config` class)**

The `Config` class defines the server's settings and configurations.

-   `UPLOAD_FOLDER = "uploads"` – Directory where uploaded files (code scripts) will be stored temporarily.
-   `PORT = 5000` – Port on which the server runs.
-   `DEBUG = True` – Enables debug mode for development purposes.
-   `EXECUTION_TIMEOUT = 10` – Maximum execution time for a script (in seconds).
-   `GRACE_PERIOD = 2` – Additional time (in seconds) after reaching the execution timeout before forcefully stopping the script.
-   `init()` – A static method that ensures the `UPLOAD_FOLDER` exists before execution.

### **Client Configuration (`Config` class)**

The `Config` class defines the client-side settings.

-   `API_URL = "http://127.0.0.1:5000/execute"` – The endpoint where the client sends code execution requests.
-   `API_KEY = "my_secret_key"` – A placeholder for an API key (not used for authentication but can be extended for security).
-   `TASKS_FOLDER = "Tasks"` – Directory where task files (code scripts) are stored before sending them to the server.

## How to Run the Server

1. Install dependencies:
    ```sh
    pip install -r requirements.txt
    ```
2. Start the Flask server:
    ```sh
    python run_server.py
    ```

## How to Run Prometheus

1. Download Prometheus from the official website:
    ```sh
    https://prometheus.io/download/
    ```
2. Unzip and extract prometheus.exe from the downloaded archive to the Prometheus folder.

3. Open a terminal from the Prometheus folder and run the script:
    ```sh
    ./prometheus --config.file=prometheus.yml
    ```

4. Open the address `http://127.0.0.1:9090/query` on the browser to see the Prometheus window.

## How to Run the Client

Run the client script to send a Python file to the server:

```sh
python run_client.py
```

## How to Run Grafana

1. Download Grafana from the official website:
    ```sh
    https://grafana.com/grafana/download
    ```

2. Install the program on your computer.

3. Open the address `http://127.0.0.1:3000/login` on the browser to see the Grafana login window.

4. Enter "admin" in the login and password fields, then change the password.

5. Go to Connections, then to Data sources and choose "Prometheus" as data source. After that enter `http://127.0.0.1:9090` in Connection field and press "Save & test"

6. In the "Queries" field, enter the necessary PromQL queries.

## Task Execution

-   Submitted scripts are saved in a unique directory.
-   The script runs in a controlled environment with a timeout.
-   Output, errors, and any created files are returned to the client.

## Notes

-   Ensure `config.py` is properly set up before running the server.
-   The execution timeout is enforced to prevent infinite loops.
-   Logs and error handling are included to capture execution failures.
