# ⚖️ ResourceFlow – Resource-Aware Predictive Web Traffic Management System

## 📌 Project Overview

**ResourceFlow** is a web traffic management system developed using Python, Flask, MySQL, and Streamlit. It distributes incoming web requests across multiple backend servers using different load-balancing techniques.

The project implements two routing algorithms:

1. **Round Robin:** Distributes incoming requests sequentially among available backend servers.
2. **Resource-Aware Load Balancing:** Selects a server based on its CPU usage, memory usage, and active requests.

The system also includes resource monitoring, concurrent request testing, a time-quantum scheduling demonstration, traffic prediction, and a Streamlit dashboard for visualization.

The main objective is to compare traditional Round Robin routing with resource-aware routing and understand how server resource utilization affects request distribution.

---

## 🎯 Project Objectives

- Develop a web application with multiple backend servers.
- Implement Round Robin load balancing.
- Implement Resource-Aware load balancing.
- Monitor CPU and memory utilization.
- Track active requests on backend servers.
- Store traffic logs and resource metrics in MySQL.
- Compare routing algorithms using response-time measurements.
- Demonstrate concurrent request processing.
- Implement a time-quantum-based Round Robin scheduling simulation.
- Predict future web traffic using historical request data.
- Visualize system performance through a Streamlit dashboard.

---

## 🛠️ Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Flask | Backend servers and load balancer |
| MySQL | Database management |
| MySQL Connector | Python-MySQL connectivity |
| Streamlit | Interactive dashboard |
| Pandas | Data processing and analysis |
| Requests | HTTP communication |
| Psutil | System resource monitoring |
| Scikit-learn | Listed dependency for machine learning extensions |

---

## 📂 Project Structure

```text
OSDBMS/
│
├── dashboard/
│   └── dashboard.py
│
├── database/
│   ├── database.py
│   ├── db_config.py
│   └── schema.sql
│
├── load_balancer/
│   └── app.py
│
├── monitoring/
│   ├── resource_monitor.py
│   └── __init__.py
│
├── prediction/
│   └── traffic_prediction.py
│
├── servers/
│   ├── server.py
│   ├── server1.py
│   ├── server2.py
│   └── server3.py
│
├── requirements.txt
└── run_all.py
```

---

## ⚙️ System Architecture

The project consists of one Flask load balancer and three backend servers.

```text
                  Incoming Requests
                         |
                         v
                +------------------+
                |  Load Balancer   |
                |   Port: 5000     |
                +------------------+
                         |
               +---------+---------+
               |                   |
               v                   v
        Round Robin          Resource-Aware
          Routing               Routing
               |                   |
               +---------+---------+
                         |
             +-----------+-----------+
             |           |           |
             v           v           v
         Server 1    Server 2    Server 3
         Port 5001   Port 5002   Port 5003
             |           |           |
             +-----------+-----------+
                         |
                         v
                Resource Monitoring
                         |
                         v
                  MySQL Database
                         |
                         v
                Streamlit Dashboard
                         |
                         v
                 Traffic Prediction
```

---

## 🔄 Load Balancing Algorithms

### 1. Round Robin

Round Robin is a traditional load-balancing algorithm.

It distributes incoming requests sequentially among available servers.

**Example:**

| Request | Selected Server |
|---|---|
| Request 1 | Server 1 |
| Request 2 | Server 2 |
| Request 3 | Server 3 |
| Request 4 | Server 1 |
| Request 5 | Server 2 |
| Request 6 | Server 3 |

After reaching the last server, the algorithm starts again from the first server.

### 2. Resource-Aware Load Balancing

This algorithm selects a backend server based on its current resource utilization.

It considers three parameters:

- CPU Usage – 50% weight
- Memory Usage – 30% weight
- Active Requests – 20% weight

The load score is calculated using:

**Load Score = (0.5 × CPU) + (0.3 × Memory) + (0.2 × Active Request Score)**

The active request score is normalized between 0 and 100.

The server with the lowest calculated load score is selected.

**Lower load score = Lower estimated server load.**

---

## 📊 Resource Monitoring

The project uses the Python `psutil` library to monitor system resources.

The monitoring module collects:

- CPU utilization percentage.
- Memory utilization percentage.
- Total system process count.
- Active requests handled by each backend server.

These metrics are used by the resource-aware load-balancing algorithm to make routing decisions.

---

## 🗄️ Database Design

The project uses MySQL as its database.

Database Name:

```sql
web_traffic_management
```

### 1. Servers Table

Stores information about backend servers.

| Column | Description |
|---|---|
| server_id | Unique server ID |
| server_name | Server name |
| port | Server port |
| status | Server status |

### 2. Resource Metrics Table

Stores resource utilization information.

| Column | Description |
|---|---|
| metric_id | Unique metric ID |
| server_id | Backend server ID |
| cpu_usage | CPU utilization |
| memory_usage | Memory utilization |
| active_processes | Total system processes |
| active_requests | Active server requests |
| recorded_at | Metric timestamp |

### 3. Traffic Logs Table

Stores request-processing information.

| Column | Description |
|---|---|
| request_id | Unique request ID |
| server_id | Server handling the request |
| response_time | Request response time |
| routing_method | Routing algorithm used |
| created_at | Request timestamp |

---

## ⏱️ Time-Quantum Scheduling Demonstration

The project includes an application-level Round Robin scheduling simulation.

Each job receives a fixed time quantum for processing.

If a job is not completed within its allocated quantum, its remaining work is placed at the end of the ready queue.

The simulation continues until all jobs are completed.

**Note:** This is a cooperative application-level simulation and does not perform actual operating-system process preemption.

---

## 🔮 Traffic Prediction

The project includes a traffic prediction module that uses historical request logs stored in MySQL.

It uses a Moving Average approach to estimate the number of requests in the next minute.

Main features:

- Retrieves historical traffic data.
- Groups requests into one-minute intervals.
- Uses the latest five minutes of traffic history.
- Calculates predicted request volume.
- Calculates Mean Absolute Error (MAE) when sufficient historical data is available.

Prediction formula:

**Predicted Traffic = (Sum of Latest 5 Minute Request Counts) / 5**

---

## 📈 Streamlit Dashboard

The project includes an interactive dashboard for monitoring and testing the system.

Dashboard features:

- Load balancer connection status.
- Backend server status.
- CPU and memory utilization.
- Active request monitoring.
- Sequential request testing.
- Concurrent request testing.
- Round Robin vs Resource-Aware comparison.
- Response-time analysis.
- Server request distribution.
- Time-quantum scheduling demonstration.
- Traffic prediction.
- CSV result downloads.

---

## 🚀 Installation and Setup

### Step 1: Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

Navigate to the project directory:

```bash
cd OSDBMS
```

### Step 2: Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure MySQL

Make sure MySQL Server is installed and running.

Open MySQL and execute the SQL file:

```sql
SOURCE path/to/OSDBMS/database/schema.sql;
```

This creates the database:

```sql
web_traffic_management
```

It also creates the required tables and inserts three backend server records.

### Step 5: Configure Database Connection

Open:

```text
database/db_config.py
```

Update the MySQL credentials:

```python
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "web_traffic_management"
}
```

Replace `YOUR_MYSQL_PASSWORD` with your actual MySQL password.

---

## ▶️ Running the Project

Open multiple terminals from the project root directory.

### Terminal 1: Start Backend Servers

```bash
python run_all.py
```

This starts three backend servers:

- Server 1: http://127.0.0.1:5001
- Server 2: http://127.0.0.1:5002
- Server 3: http://127.0.0.1:5003

### Terminal 2: Start Load Balancer

```bash
python -m load_balancer.app
```

Load balancer runs at:

http://127.0.0.1:5000

### Terminal 3: Start Streamlit Dashboard

```bash
streamlit run dashboard/dashboard.py
```

Dashboard runs at:

http://localhost:8501

---

## 🔗 API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Check load balancer status |
| `/request` | GET | Process a single request |
| `/test` | GET | Perform sequential request testing |
| `/concurrent-test` | GET | Perform concurrent request testing |
| `/quantum-test` | GET | Run time-quantum scheduling simulation |
| `/prediction` | GET | Generate traffic prediction |

### Example API Requests

**1. Check Load Balancer**

```text
http://127.0.0.1:5000/
```

**2. Round Robin Routing**

```text
http://127.0.0.1:5000/request?method=round_robin
```

**3. Resource-Aware Routing**

```text
http://127.0.0.1:5000/request?method=resource_aware
```

**4. Sequential Testing**

```text
http://127.0.0.1:5000/test?count=10&method=round_robin
```

**5. Concurrent Testing**

```text
http://127.0.0.1:5000/concurrent-test?count=10&method=resource_aware
```

**6. Time-Quantum Simulation**

```text
http://127.0.0.1:5000/quantum-test?count=3&quantum=2
```

**7. Traffic Prediction**

```text
http://127.0.0.1:5000/prediction
```

---

## 📌 Expected Outcomes

- Successful distribution of requests across three backend servers.
- Comparison between Round Robin and Resource-Aware routing.
- Monitoring of CPU and memory utilization.
- Measurement of backend response times.
- Storage of request logs in MySQL.
- Demonstration of concurrent request handling.
- Application-level time-quantum scheduling.
- Estimation of future traffic using historical request data.
- Visualization of system performance through a dashboard.

---

## 🔮 Future Scope

- Improve resource monitoring with server-specific metrics.
- Implement advanced traffic prediction models.
- Introduce dynamic server scaling.
- Improve fault tolerance and server recovery.
- Add more backend servers.
- Implement advanced load-balancing algorithms.
- Improve performance analysis and visualization.

---

## 👨‍💻 Contributors

- Mayank Joshi
- Prince Yadav
- Sammer Pal Singh
- Aniket Raj

---

## 📄 License

This project is developed for academic and educational purposes as part of an Operating Systems and Database Management Systems project.
