# =============================================================================
# IMPORTS
# =============================================================================
# random:
#   Used to simulate changing server conditions (up/down, CPU, disk usage).
# time:
#   Used to pause between health-check cycles (sleep).
# datetime:
#   Used to timestamp each log entry with the current date and time.
# colorama:
#   Used to color terminal output for better visual feedback (green/yellow/red).

import random
import time
from datetime import datetime
from colorama import init, Fore, Style

# Initialize colorama so colors reset automatically after each print.
# This prevents color bleed across lines.
init(autoreset=True)


# =============================================================================
# CONFIG KNOBS (TUNABLE SETTINGS)
# =============================================================================
# These are intentionally placed near the top so behavior can be changed
# without touching the program logic.

CHECK_INTERVAL = 5              # Seconds to wait between health-check cycles
CPU_WARN_THRESHOLD = 80         # CPU % above which status becomes WARNING
DISK_WARN_THRESHOLD = 85        # Disk % above which status becomes WARNING
LOG_FILE = "server_check_log.txt"  # File where raw log lines are written

# List of servers to check every cycle.
# This simulates a small fleet of infrastructure nodes.
servers = ["web01", "db01", "cache01", "auth01", "auth02"]

# Hardcoded mapping of server → environment.
# If a server is missing here, it defaults to "dev".
hardcode_env = {
    "web01": "prod",
    "db01": "prod",
    "cache01": "dev",
    "auth01": "stage"
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def health_eval(is_up, cpu, disk):
    """
    PURPOSE:
        Determine overall server health based on availability and resource usage.

    LOGIC:
        - If the server is down, it is CRITICAL regardless of metrics.
        - If CPU or disk exceeds warning thresholds, status is WARNING.
        - Otherwise, the server is GOOD.

    WHY:
        Centralizes health logic so it can be reused and adjusted easily.
    """
    if not is_up:
        return "CRITICAL"
    elif cpu > CPU_WARN_THRESHOLD or disk > DISK_WARN_THRESHOLD:
        return "WARNING"
    else:
        return "GOOD"


def simulate_metrics():
    """
    PURPOSE:
        Simulate real-world server metrics.

    RETURNS:
        - is_up (bool)
        - cpu usage percentage (int)
        - disk usage percentage (int)

    WHY:
        This allows the script to run without real monitoring systems.
        The weighted True/False choice makes servers usually up, but not always.
    """
    is_up = random.choice([True, True, False, True])
    cpu = random.randint(0, 100)
    disk = random.randint(0, 100)
    return is_up, cpu, disk


def check_server(server_name):
    """
    PURPOSE:
        Perform a single health check for one server.

    STEPS:
        1. Determine the server's environment.
        2. Simulate metrics.
        3. Evaluate health status.
        4. Write a structured log line to disk.
        5. Print a color-coded summary to the terminal.
    """

    # Determine environment, defaulting to "dev" if not found.
    server_env = hardcode_env.get(server_name, "dev")

    # Simulate metrics and evaluate health.
    is_up, cpu, disk = simulate_metrics()
    status = health_eval(is_up, cpu, disk)

    # Choose color based on health status.
    if status == "GOOD":
        status_color = Fore.GREEN
    elif status == "WARNING":
        status_color = Fore.YELLOW
    else:
        status_color = Fore.RED

    # If the server is down, metrics are not applicable.
    # We log "N/A" instead of numbers to avoid misleading data.
    if not is_up:
        cpu = "N/A"
        disk = "N/A"

    # Timestamp in ISO format for easy parsing and sorting.
    timestamp = datetime.now().isoformat()

    # Build a single CSV-style log line.
    # This format is intentionally simple for later parsing.
    log_line = (
        f"{timestamp}, {server_name}, {server_env}, "
        f"{is_up}, {cpu}, {disk}, {status}\n"
    )

    # Append the log line to the log file.
    # Using "a" mode ensures we do not overwrite previous entries.
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_line)

    # Print a readable summary to the terminal.
    # This is for humans; the log file is for machines.
    print(
        f"=== Summary for {server_name} /// Type: {server_env} ===\n"
        f"Status: {status_color}!!!{status}!!!\n"
        f"Up: {is_up}\n"
        f"CPU Usage Percentage: {cpu}\n"
        f"Disk Usage Percentage: {disk}\n"
    )


def run_cycle():
    """
    PURPOSE:
        Run one full health-check cycle across all servers.

    WHY:
        Separating this from main() keeps the control flow clean and readable.
    """
    for server in servers:
        print(f"\n--- Checking {server} ---")
        check_server(server)


# =============================================================================
# ENTRY POINT WITH MAIN GUARD
# =============================================================================

def main():
    """
    PURPOSE:
        Continuously run health-check cycles at fixed intervals.

    DESIGN:
        - Runs forever until interrupted by the user.
        - Uses try/except to exit cleanly on Ctrl+C.
    """
    try:
        while True:
            print("++++ Server Health Checker ++++")
            print(datetime.now().isoformat())
            run_cycle()
            print("++++ Cycle Complete ++++")
            print("*** STOP with Ctrl + C ***\n")

            # Pause before the next cycle.
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        # Graceful shutdown when user presses Ctrl+C.
        print("Stopped by user via key press")


# Standard Python main guard.
# Ensures main() only runs when this file is executed directly.
if __name__ == "__main__":
    main()
