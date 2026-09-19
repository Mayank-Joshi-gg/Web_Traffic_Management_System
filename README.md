# Resource-Aware Predictive Web Traffic Management System

## About the Project

This project is a prototype load-balancing system that distributes web
requests among multiple simulated servers.

Traditional Round Robin distributes requests sequentially without checking
the current condition of the servers. Our system monitors server resources
and uses this information to make better routing decisions.

## Objectives

- Simulate multiple web servers using Python.
- Implement Round Robin load balancing for comparison.
- Monitor CPU, memory, processes and active requests.
- Develop resource-aware request routing.
- Store and analyze traffic data using MySQL.

## System Workflow

Client Request
→ Load Balancer
→ Resource Monitoring
→ Server Selection
→ Web Server
→ Response
→ Database Logging

## Technologies Used

- Python
- Flask / FastAPI
- MySQL
- psutil
- Pandas
- Scikit-learn
- Streamlit
- Git & GitHub

## Main Modules

1. Request Handler
2. Load Balancer
3. Resource Monitor
4. Simulated Web Servers
5. MySQL Database
6. Traffic Prediction
7. Performance Dashboard

## Load Balancing Methods

### Round Robin
Requests are distributed sequentially among the available servers.

### Resource-Aware Load Balancing
The system checks server resources such as CPU and memory before
selecting a server.

## Performance Metrics

- Response Time
- CPU Utilization
- Memory Utilization
- Request Distribution
- Server Load

## Project Status

Phase-I: System design and planning completed.

Development and integration are planned for the next phase.

## Team

Team: ResourceFlow

Team ID: OSDBMS-V-2026-T155

Graphic Era (Deemed to be University), Dehradun
