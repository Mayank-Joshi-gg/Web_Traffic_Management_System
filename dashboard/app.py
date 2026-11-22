import pandas as pd
import requests
import streamlit as st

# ============================================================
# RESOURCEFLOW - PREDICTIVE TRAFFIC MANAGEMENT DASHBOARD
# ============================================================

st.set_page_config(
    page_title="ResourceFlow | Traffic Management",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

DEFAULT_BALANCER_URL = "http://127.0.0.1:5000"
DEFAULT_SERVERS = {
    1: "http://127.0.0.1:5001",
    2: "http://127.0.0.1:5002",
    3: "http://127.0.0.1:5003",
}

# Keep results after Streamlit reruns.
for key in (
    "sequential_results",
    "concurrent_results",
    "quantum_results",
    "prediction_results",
):
    if key not in st.session_state:
        st.session_state[key] = None


# ============================================================
# STYLING AND HEADER
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 38px;
        font-weight: 800;
        margin-bottom: 0;
    }
    .subtitle {
        font-size: 17px;
        color: #888888;
        margin-top: 5px;
    }
    .section-title {
        font-size: 23px;
        font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="main-title">⚖️ ResourceFlow</div>',
    unsafe_allow_html=True,
)
st.markdown(
    '<div class="subtitle">Predictive Traffic Management System</div>',
    unsafe_allow_html=True,
)
st.write(
    "Monitor backend servers, compare routing algorithms, "
    "and demonstrate concurrent and time-quantum scheduling."
)


# ============================================================
# SIDEBAR CONFIGURATION
# ============================================================

with st.sidebar:
    st.header("⚙️ Configuration")

    balancer_url = st.text_input(
        "Load Balancer URL",
        value=DEFAULT_BALANCER_URL,
        key="balancer_url_input",
    ).strip().rstrip("/")

    st.divider()
    st.subheader("Backend Servers")

    server_urls = {}
    for server_id, default_url in DEFAULT_SERVERS.items():
        server_urls[server_id] = st.text_input(
            f"Server {server_id} URL",
            value=default_url,
            key=f"server_url_{server_id}",
        ).strip().rstrip("/")

    st.divider()
    st.markdown("### Project Components")
    st.markdown(
        """
        - Flask backend servers
        - Round Robin routing
        - Resource-aware routing
        - Concurrent request testing
        - Time-quantum demonstration
        - Response-time analysis
        - Traffic prediction
        """
    )

    st.divider()
    st.caption(
        "Start all three backend servers and the Flask load balancer "
        "before running tests."
    )


# ============================================================
# HTTP HELPERS
# ============================================================

def get_json(url, params=None, timeout=5):
    """GET JSON from an endpoint. Return (data, error)."""
    try:
        response = requests.get(
            url,
            params=params,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json(), None
    except requests.HTTPError as error:
        body = error.response.text[:2000] if error.response is not None else str(error)
        return None, body
    except requests.RequestException as error:
        return None, str(error)
    except ValueError:
        return None, "The server returned invalid JSON."


def get_backend_status(server_id, url):
    """Get one backend's status without stopping the dashboard on errors."""
    if not url:
        return {
            "Server": f"Server {server_id}",
            "Status": "NOT CONFIGURED",
            "Port": "-",
            "CPU Usage (%)": None,
            "Memory Usage (%)": None,
            "Active Requests": None,
            "Details": "No URL configured",
        }

    data, error = get_json(f"{url}/status", timeout=3)

    if error:
        return {
            "Server": f"Server {server_id}",
            "Status": "OFFLINE",
            "Port": url.rsplit(":", 1)[-1],
            "CPU Usage (%)": None,
            "Memory Usage (%)": None,
            "Active Requests": None,
            "Details": error,
        }

    if not isinstance(data, dict):
        data = {}

    return {
        "Server": f"Server {data.get('server_id', server_id)}",
        "Status": str(data.get("status", "UNKNOWN")).upper(),
        "Port": data.get("server_port", url.rsplit(":", 1)[-1]),
        "CPU Usage (%)": data.get("cpu_usage", data.get("cpu")),
        "Memory Usage (%)": data.get("memory_usage", data.get("memory")),
        "Active Requests": data.get("active_requests", 0),
        "Details": "Connected",
    }


def call_test_endpoint(url, params=None, timeout=300):
    """Call a test endpoint and return (data, error)."""
    return get_json(url, params=params, timeout=timeout)


def show_test_error(title, error, data=None):
    st.error(title)
    if error:
        st.code(str(error))
    if isinstance(data, dict):
        details = data.get("details") or data.get("message")
        if details:
            st.write(details)
        if data.get("results"):
            st.dataframe(
                pd.DataFrame(data["results"]),
                width="stretch",
                hide_index=True,
            )


def show_response_metrics(results_df):
    """Show response-time metrics when that column exists."""
    if "response_time" not in results_df.columns:
        return

    times = pd.to_numeric(
        results_df["response_time"],
        errors="coerce",
    ).dropna()

    if times.empty:
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Average Response Time", f"{times.mean():.4f} seconds")
    c2.metric("Minimum Response Time", f"{times.min():.4f} seconds")
    c3.metric("Maximum Response Time", f"{times.max():.4f} seconds")


def show_server_distribution(results_df, title="Server Request Distribution"):
    if "server" not in results_df.columns:
        return

    distribution = (
        results_df["server"]
        .value_counts()
        .sort_index()
    )
    st.subheader(title)
    st.bar_chart(distribution)


def download_dataframe(df, label, filename):
    st.download_button(
        label,
        data=df.to_csv(index=False).encode("utf-8"),
        file_name=filename,
        mime="text/csv",
    )


# ============================================================
# SYSTEM STATUS
# ============================================================

st.divider()
st.markdown(
    '<div class="section-title">🖥️ System Status</div>',
    unsafe_allow_html=True,
)

refresh_col, note_col = st.columns([1, 4])
with refresh_col:
    refresh_status = st.button(
        "🔄 Refresh Server Status",
        key="refresh_server_status",
    )
if refresh_status:
    st.rerun()

balancer_data, balancer_error = get_json(
    balancer_url,
    timeout=3,
)

server_statuses = [
    get_backend_status(server_id, url)
    for server_id, url in server_urls.items()
]

status_columns = st.columns(4)

with status_columns[0]:
    st.metric(
        "Load Balancer",
        "ONLINE" if balancer_error is None else "OFFLINE",
    )

for index, server in enumerate(server_statuses, start=1):
    with status_columns[index]:
        st.metric(server["Server"], server["Status"])

if balancer_error:
    st.error(
        "Cannot connect to the Flask load balancer.\n\n"
        f"URL: {balancer_url}\n\nError: {balancer_error}"
    )
else:
    st.success(
        balancer_data.get(
            "message",
            "Load balancer connected successfully.",
        )
        if isinstance(balancer_data, dict)
        else "Load balancer connected successfully."
    )

st.subheader("Backend Server Details")
status_df = pd.DataFrame(server_statuses)
st.dataframe(
    status_df,
    width="stretch",
    hide_index=True,
)

online_servers = sum(
    1 for server in server_statuses
    if server["Status"] == "UP"
)
active_values = [
    server["Active Requests"]
    for server in server_statuses
    if isinstance(server["Active Requests"], (int, float))
]
total_active_requests = sum(active_values) if active_values else 0

metric_columns = st.columns(3)
metric_columns[0].metric("Online Servers", f"{online_servers}/3")
metric_columns[1].metric("Active Requests", total_active_requests)
metric_columns[2].metric("Routing Algorithms", "2")


# ============================================================
# SEQUENTIAL REQUEST TESTING
# ============================================================

st.divider()
st.markdown(
    '<div class="section-title">🔄 Sequential Request Testing</div>',
    unsafe_allow_html=True,
)
st.write(
    "Send requests one after another and observe how the load balancer "
    "distributes them."
)

with st.container(border=True):
    sequential_method = st.selectbox(
        "Select Routing Algorithm",
        ["round_robin", "resource_aware"],
        format_func=lambda value: {
            "round_robin": "Round Robin",
            "resource_aware": "Resource-Aware",
        }[value],
        key="sequential_method",
    )
    sequential_count = st.slider(
        "Number of Requests",
        min_value=1,
        max_value=100,
        value=9,
        key="sequential_count",
    )
    run_sequential = st.button(
        "▶ Run Sequential Test",
        type="primary",
        key="run_sequential",
    )

if run_sequential:
    if balancer_error:
        show_test_error(
            "Cannot run the test because the load balancer is offline.",
            balancer_error,
        )
    else:
        endpoint = f"{balancer_url}/test"
        with st.spinner("Sending sequential requests..."):
            data, error = call_test_endpoint(
                endpoint,
                params={
                    "count": sequential_count,
                    "method": sequential_method,
                },
                timeout=300,
            )

        if error:
            show_test_error("Sequential test failed.", error, data)
        elif isinstance(data, dict) and data.get("error"):
            show_test_error("Sequential test failed.", None, data)
        else:
            st.session_state["sequential_results"] = data
            st.success("Sequential test completed.")

if st.session_state["sequential_results"] is not None:
    data = st.session_state["sequential_results"]
    results = data.get("results", []) if isinstance(data, dict) else []

    if results:
        results_df = pd.DataFrame(results)
        st.subheader("Sequential Request Results")
        st.dataframe(results_df, width="stretch", hide_index=True)
        show_server_distribution(results_df)
        show_response_metrics(results_df)

        if "request" in results_df.columns and "response_time" in results_df.columns:
            chart_df = results_df[["request", "response_time"]].copy()
            chart_df["response_time"] = pd.to_numeric(
                chart_df["response_time"], errors="coerce"
            )
            st.subheader("Response Time Comparison")
            st.line_chart(
                chart_df.dropna().set_index("request")
            )

        download_dataframe(
            results_df,
            "📥 Download Sequential Results",
            "sequential_results.csv",
        )
    else:
        st.info("No sequential results are available yet.")


# ============================================================
# CONCURRENT REQUEST TESTING
# ============================================================

st.divider()
st.markdown(
    '<div class="section-title">⚡ Concurrent Request Testing</div>',
    unsafe_allow_html=True,
)
st.write(
    "Send multiple requests simultaneously to observe how the servers "
    "handle concurrent traffic."
)

with st.container(border=True):
    concurrent_method = st.selectbox(
        "Concurrent Routing Algorithm",
        ["round_robin", "resource_aware"],
        format_func=lambda value: {
            "round_robin": "Round Robin",
            "resource_aware": "Resource-Aware",
        }[value],
        key="concurrent_method",
    )
    concurrent_count = st.slider(
        "Number of Concurrent Requests",
        min_value=1,
        max_value=50,
        value=12,
        key="concurrent_count",
    )
    run_concurrent = st.button(
        "⚡ Run Concurrent Test",
        type="primary",
        key="run_concurrent",
    )

if run_concurrent:
    if balancer_error:
        show_test_error(
            "Cannot run the test because the load balancer is offline.",
            balancer_error,
        )
    else:
        endpoint = f"{balancer_url}/concurrent-test"
        with st.spinner("Running concurrent requests..."):
            data, error = call_test_endpoint(
                endpoint,
                params={
                    "count": concurrent_count,
                    "method": concurrent_method,
                },
                timeout=300,
            )

        if error:
            show_test_error("Concurrent test failed.", error, data)
        elif isinstance(data, dict) and data.get("error"):
            show_test_error("Concurrent test failed.", None, data)
        else:
            st.session_state["concurrent_results"] = data
            st.success("Concurrent test completed.")

if st.session_state["concurrent_results"] is not None:
    data = st.session_state["concurrent_results"]
    results = data.get("results", []) if isinstance(data, dict) else []

    if results:
        concurrent_df = pd.DataFrame(results)
        st.subheader("Concurrent Request Results")
        st.dataframe(
            concurrent_df,
            width="stretch",
            hide_index=True,
        )
        show_server_distribution(concurrent_df)
        show_response_metrics(concurrent_df)

        download_dataframe(
            concurrent_df,
            "📥 Download Concurrent Results",
            "concurrent_results.csv",
        )
    else:
        st.info("No concurrent results are available yet.")


# ============================================================
# TIME-QUANTUM SCHEDULING
# ============================================================

st.divider()
st.markdown(
    '<div class="section-title">⏱️ Time-Quantum Scheduling</div>',
    unsafe_allow_html=True,
)
st.write(
    "Demonstrate time-sliced scheduling. Each unfinished job returns "
    "to the queue after one time slice."
)
st.warning(
    "This is an application-level simulation using the backend "
    "/process-chunk endpoint. It does not preempt real operating-system processes."
)

with st.container(border=True):
    quantum_jobs = st.slider(
        "Number of Jobs",
        min_value=1,
        max_value=10,
        value=3,
        key="quantum_jobs",
    )
    quantum_value = st.slider(
        "Time Quantum (seconds)",
        min_value=0.5,
        max_value=5.0,
        value=2.0,
        step=0.5,
        key="quantum_value",
    )
    run_quantum = st.button(
        "▶ Run Time-Quantum Demo",
        type="primary",
        key="run_quantum",
    )

if run_quantum:
    if balancer_error:
        show_test_error(
            "Cannot run the time-quantum demo because the load balancer is offline.",
            balancer_error,
        )
    else:
        with st.spinner("Running time-quantum simulation..."):
            data, error = call_test_endpoint(
                f"{balancer_url}/quantum-test",
                params={
                    "count": quantum_jobs,
                    "quantum": quantum_value,
                },
                timeout=300,
            )

        if error:
            show_test_error("Time-quantum test failed.", error, data)
        elif isinstance(data, dict) and data.get("error"):
            show_test_error("Time-quantum test failed.", None, data)
        else:
            st.session_state["quantum_results"] = data
            st.success("Time-quantum demonstration completed.")

if st.session_state["quantum_results"] is not None:
    data = st.session_state["quantum_results"]

    if isinstance(data, dict):
        q1, q2, q3 = st.columns(3)
        q1.metric(
            "Time Quantum",
            f"{data.get('time_quantum', 0)} seconds",
        )
        q2.metric("Total Jobs", data.get("total_jobs", 0))
        q3.metric("Scheduling Turns", data.get("total_turns", 0))

        quantum_df = pd.DataFrame(data.get("results", []))

        if not quantum_df.empty:
            st.subheader("Scheduling Timeline")
            st.dataframe(
                quantum_df,
                width="stretch",
                hide_index=True,
            )

            if {"turn", "execution_time"}.issubset(quantum_df.columns):
                chart_df = quantum_df[["turn", "execution_time"]].copy()
                chart_df["execution_time"] = pd.to_numeric(
                    chart_df["execution_time"],
                    errors="coerce",
                )
                st.subheader("Execution Time per Turn")
                st.line_chart(
                    chart_df.dropna().set_index("turn")
                )

            download_dataframe(
                quantum_df,
                "📥 Download Quantum Results",
                "quantum_results.csv",
            )
        else:
            st.info("The quantum endpoint returned no scheduling results.")


# ============================================================
# TRAFFIC PREDICTION
# ============================================================

st.divider()
st.markdown(
    '<div class="section-title">📈 Traffic Prediction</div>',
    unsafe_allow_html=True,
)
st.write(
    "Generate a next-minute traffic estimate using the historical "
    "request counts stored in MySQL."
)

st.info(
    "Send requests through the load balancer first. Prediction needs "
    "traffic records in the traffic_logs table."
)

if st.button(
    "🔮 Generate Traffic Prediction",
    type="primary",
    key="generate_prediction",
):
    if balancer_error:
        show_test_error(
            "Cannot generate prediction because the load balancer is offline.",
            balancer_error,
        )
    else:
        with st.spinner("Generating traffic prediction..."):
            prediction, error = get_json(
                f"{balancer_url}/prediction",
                timeout=20,
            )

        if error:
            show_test_error("Traffic prediction failed.", error, prediction)
        elif isinstance(prediction, dict):
            st.session_state["prediction_results"] = prediction
        else:
            st.error("The prediction endpoint returned an unexpected response.")

if st.session_state["prediction_results"] is not None:
    prediction = st.session_state["prediction_results"]
    prediction_status = prediction.get("status")

    if prediction_status == "no_data":
        st.warning(
            prediction.get(
                "message",
                "No historical traffic data is available.",
            )
        )

    elif prediction_status == "success":
        predicted = prediction.get("predicted_requests")
        prediction_time = prediction.get("prediction_for")

        p1, p2 = st.columns(2)
        p1.metric(
            "Predicted Requests for Next Minute",
            predicted if predicted is not None else "N/A",
        )
        p2.metric(
            "Prediction Window",
            f"{prediction.get('window_size', 'N/A')} minute(s)",
        )

        if prediction_time:
            st.caption(f"Forecast for: {prediction_time}")

        mae = prediction.get("mae")
        if mae is not None:
            st.metric("Historical Prediction MAE", mae)
        else:
            st.info(
                "More historical traffic is needed to calculate "
                "the historical prediction error (MAE)."
            )

        history = prediction.get("actual_traffic", [])
        if history:
            history_df = pd.DataFrame(history)
            if {"minute", "requests"}.issubset(history_df.columns):
                history_df["requests"] = pd.to_numeric(
                    history_df["requests"],
                    errors="coerce",
                )
                st.subheader("Historical Traffic")
                st.line_chart(
                    history_df.dropna().set_index("minute")["requests"]
                )
                st.dataframe(
                    history_df,
                    width="stretch",
                    hide_index=True,
                )

    else:
        st.error(
            prediction.get(
                "message",
                prediction.get(
                    "details",
                    "Prediction could not be generated.",
                ),
            )
        )


# ============================================================
# FOOTER
# ============================================================

st.divider()
st.caption(
    "ResourceFlow | Predictive Traffic Management System | "
    "Round Robin baseline and resource-aware routing comparison"
)
