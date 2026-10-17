import time
import pandas as pd
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

# ============================================================
# RESOURCEFLOW DASHBOARD
# ============================================================

st.set_page_config(
    page_title="Predictive traffic Dashboard",
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


# ============================================================
# HEADER AND STYLING
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
    '<div class="subtitle">'
    'Predictive Traffic Management System'
    '</div>',
    unsafe_allow_html=True,
)

st.write("")

st.info(
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
    ).strip().rstrip("/")

    st.divider()

    st.subheader("Backend Servers")

    server_urls = {}

    for server_id, default_url in DEFAULT_SERVERS.items():
        server_urls[server_id] = st.text_input(
            f"Server {server_id} URL",
            value=default_url,
            key=f"server_{server_id}",
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
        """
    )

    st.divider()

    st.caption(
        "Start all three backend servers and the Flask load balancer "
        "before running tests."
    )


# ============================================================
# HTTP HELPER FUNCTIONS
# ============================================================

def get_json(url, timeout=5):
    """Send a GET request and return JSON data or an error."""

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        return response.json(), None

    except requests.RequestException as error:
        return None, str(error)

    except ValueError:
        return None, "The server returned invalid JSON."


def call_test_endpoint(url, timeout=300):
    """Call a test endpoint and return its result."""

    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()

        return response.json(), None

    except requests.HTTPError as error:
        response = error.response

        if response is not None:
            details = response.text[:2000]
        else:
            details = str(error)

        return None, details

    except requests.RequestException as error:
        return None, str(error)

    except ValueError:
        return None, "The load balancer returned invalid JSON."


def get_backend_status(server_id, url):
    """Retrieve the status of one backend server."""

    data, error = get_json(
        f"{url}/status",
        timeout=3,
    )

    if error:
        return {
            "Server": f"Server {server_id}",
            "Status": "OFFLINE",
            "Port": url.rsplit(":", 1)[-1],
            "Active Requests": None,
            "Details": error,
        }

    return {
        "Server": f"Server {data.get('server_id', server_id)}",
        "Status": data.get("status", "UNKNOWN"),
        "Port": data.get(
            "server_port",
            url.rsplit(":", 1)[-1],
        ),
        "Active Requests": data.get("active_requests", 0),
        "Details": "Connected",
    }


# ============================================================
# SYSTEM STATUS
# ============================================================
# Automatically refresh only when no test is running.
if not st.session_state.get("test_running", False):
    st_autorefresh(
        interval=1000,
        limit=None,
        key="resourceflow_auto_refresh"
    )
st.divider()

st.markdown(
    '<div class="section-title">🖥️ System Status</div>',
    unsafe_allow_html=True,
)

if st.button("🔄 Refresh Server Status"):
    st.rerun()


balancer_data, balancer_error = get_json(
    balancer_url,
    timeout=3,
)

server_statuses = []

for server_id, url in server_urls.items():
    server_statuses.append(
        get_backend_status(server_id, url)
    )


# Status cards

status_columns = st.columns(4)

with status_columns[0]:
    st.metric(
        "Load Balancer",
        "ONLINE" if balancer_error is None else "OFFLINE",
    )

for index, server in enumerate(server_statuses, start=1):
    with status_columns[index]:
        st.metric(
            server["Server"],
            server["Status"],
        )


if balancer_error:
    st.error(
        "Cannot connect to the load balancer.\n\n"
        f"URL: {balancer_url}\n\n"
        f"Error: {balancer_error}"
    )
else:
    st.success(
        balancer_data.get(
            "message",
            "Load balancer connected successfully.",
        )
    )


# Backend table

st.subheader("Backend Server Details")

status_df = pd.DataFrame(server_statuses)

st.dataframe(
    status_df,
    use_container_width=True,
    hide_index=True,
)


# Summary metrics

online_servers = sum(
    1
    for server in server_statuses
    if server["Status"] == "UP"
)

active_requests = [
    server["Active Requests"]
    for server in server_statuses
    if isinstance(server["Active Requests"], (int, float))
]

total_active_requests = (
    sum(active_requests)
    if active_requests
    else 0
)

metric_columns = st.columns(3)

metric_columns[0].metric(
    "Online Servers",
    f"{online_servers}/3",
)

metric_columns[1].metric(
    "Active Requests",
    total_active_requests,
)

metric_columns[2].metric(
    "Routing Algorithms",
    "2",
)


# ============================================================
# SEQUENTIAL REQUEST TEST
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">🔄 Sequential Request Testing</div>',
    unsafe_allow_html=True,
)

st.write(
    "Send requests one after another and observe how "
    "the load balancer distributes them."
)

with st.container(border=True):

    sequential_method = st.selectbox(
        "Select Routing Algorithm",
        [
            "round_robin",
            "resource_aware",
        ],
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
    st.session_state["test_running"] = True

    endpoint = (
        f"{balancer_url}/test"
        f"?count={sequential_count}"
        f"&method={sequential_method}"
    )

    try:
        with st.spinner("Sending requests..."):
            data, error = call_test_endpoint(
                endpoint,
                timeout=180,
            )

        if error:
            st.error("Sequential test failed.")
            st.code(error)

        elif data.get("error"):
            st.error(data["error"])
            st.json(data)

        else:
            st.session_state["sequential_results"] = data

    finally:
        st.session_state["test_running"] = False

    st.rerun()


if "sequential_results" in st.session_state:

    data = st.session_state["sequential_results"]

    st.success("Sequential test completed.")

    results = data.get("results", [])

    if results:

        results_df = pd.DataFrame(results)

        st.subheader("Request Results")

        st.dataframe(
            results_df,
            use_container_width=True,
            hide_index=True,
        )

        if "server" in results_df.columns:

            distribution = (
                results_df["server"]
                .value_counts()
                .sort_index()
            )

            st.subheader("📊 Request Distribution")

            st.bar_chart(distribution)

        if "response_time" in results_df.columns:

            results_df["response_time"] = pd.to_numeric(
                results_df["response_time"],
                errors="coerce",
            )

            valid_times = results_df["response_time"].dropna()

            if not valid_times.empty:

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Average Response Time",
                    f"{valid_times.mean():.4f} seconds",
                )

                c2.metric(
                    "Minimum Response Time",
                    f"{valid_times.min():.4f} seconds",
                )

                c3.metric(
                    "Maximum Response Time",
                    f"{valid_times.max():.4f} seconds",
                )

                if "request" in results_df.columns:

                    st.subheader("Response Time Comparison")

                    chart_df = results_df[
                        ["request", "response_time"]
                    ].dropna()

                    st.line_chart(
                        chart_df.set_index("request")
                    )

        st.download_button(
            "📥 Download Sequential Results",
            data=results_df.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="sequential_results.csv",
            mime="text/csv",
        )

    else:
        st.warning("No request results were returned.")


# ============================================================
# CONCURRENT REQUEST TEST
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">⚡ Concurrent Request Testing</div>',
    unsafe_allow_html=True,
)

st.write(
    "Send multiple requests simultaneously to observe "
    "how the servers handle concurrent traffic."
)

with st.container(border=True):

    concurrent_method = st.selectbox(
        "Concurrent Routing Algorithm",
        [
            "round_robin",
            "resource_aware",
        ],
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
    st.session_state["test_running"] = True

    endpoint = (
        f"{balancer_url}/concurrent-test"
        f"?count={concurrent_count}"
        f"&method={concurrent_method}"
    )

    try:
        with st.spinner("Running concurrent requests..."):
            data, error = call_test_endpoint(
                endpoint,
                timeout=180,
            )

        if error:
            st.error("Concurrent test failed.")
            st.code(error)

        elif data.get("error"):
            st.error(data["error"])
            st.json(data)

        else:
            st.session_state["concurrent_results"] = data

    finally:
        st.session_state["test_running"] = False

    st.rerun()


if "concurrent_results" in st.session_state:

    data = st.session_state["concurrent_results"]

    st.success("Concurrent test completed.")

    results = data.get("results", [])

    if results:

        concurrent_df = pd.DataFrame(results)

        st.subheader("Concurrent Request Results")

        st.dataframe(
            concurrent_df,
            use_container_width=True,
            hide_index=True,
        )

        if "server" in concurrent_df.columns:

            distribution = (
                concurrent_df["server"]
                .value_counts()
                .sort_index()
            )

            st.subheader("📊 Server Request Distribution")

            st.bar_chart(distribution)

        if "response_time" in concurrent_df.columns:

            concurrent_df["response_time"] = pd.to_numeric(
                concurrent_df["response_time"],
                errors="coerce",
            )

            valid_times = concurrent_df[
                "response_time"
            ].dropna()

            if not valid_times.empty:

                c1, c2, c3 = st.columns(3)

                c1.metric(
                    "Average Response Time",
                    f"{valid_times.mean():.4f} seconds",
                )

                c2.metric(
                    "Minimum Response Time",
                    f"{valid_times.min():.4f} seconds",
                )

                c3.metric(
                    "Maximum Response Time",
                    f"{valid_times.max():.4f} seconds",
                )

        st.download_button(
            "📥 Download Concurrent Results",
            data=concurrent_df.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="concurrent_results.csv",
            mime="text/csv",
        )

    else:
        st.warning(
            "No request results were returned. "
            "Check the load balancer terminal."
        )


# ============================================================
# TIME-QUANTUM SCHEDULING DEMONSTRATION
# ============================================================

st.divider()

st.markdown(
    '<div class="section-title">⏱️ Time-Quantum Scheduling</div>',
    unsafe_allow_html=True,
)

st.write(
    "Demonstrate cooperative time-sliced scheduling. "
    "Each unfinished job returns to the queue after one time slice."
)

st.warning(
    "This is an application-level simulation using /process-chunk. "
    "It does not interrupt or resume real operating-system processes."
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

    endpoint = (
        f"{balancer_url}/quantum-test"
        f"?count={quantum_jobs}"
        f"&quantum={quantum_value}"
    )

    with st.spinner(
        "Running time-quantum simulation. Please wait..."
    ):

        data, error = call_test_endpoint(
            endpoint,
            timeout=300,
        )

    if error:
        st.error("Time-quantum test failed.")
        st.code(error)

    elif data.get("error"):
        st.error(data["error"])

        if data.get("details"):
            st.code(data["details"])

        if data.get("results"):
            st.dataframe(
                pd.DataFrame(data["results"]),
                use_container_width=True,
                hide_index=True,
            )

    else:
        st.session_state["quantum_results"] = data


if "quantum_results" in st.session_state:

    data = st.session_state["quantum_results"]

    st.success("Time-quantum demonstration completed.")

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Time Quantum",
        f"{data.get('time_quantum', 0)} seconds",
    )

    c2.metric(
        "Total Jobs",
        data.get("total_jobs", 0),
    )

    c3.metric(
        "Scheduling Turns",
        data.get("total_turns", 0),
    )

    quantum_df = pd.DataFrame(
        data.get("results", [])
    )

    if not quantum_df.empty:

        st.subheader("Scheduling Timeline")

        st.dataframe(
            quantum_df,
            use_container_width=True,
            hide_index=True,
        )

        if {
            "turn",
            "execution_time",
        }.issubset(quantum_df.columns):

            st.subheader("Execution Time per Turn")

            chart_df = quantum_df[
                ["turn", "execution_time"]
            ].copy()

            chart_df["execution_time"] = pd.to_numeric(
                chart_df["execution_time"],
                errors="coerce",
            )

            st.line_chart(
                chart_df.dropna().set_index("turn")
            )

        st.download_button(
            "📥 Download Quantum Results",
            data=quantum_df.to_csv(
                index=False
            ).encode("utf-8"),
            file_name="quantum_results.csv",
            mime="text/csv",
        )

