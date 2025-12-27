# =============================================================================
# SERVER LOG ANALYTICS + REPORTING (Module 6)
# =============================================================================
# THE PIPELINE OF THIS SCRIPT:
#
# 1) Raw log lines are read from a file (server_check_log.txt)
# 2) Each line is parsed into a clean dictionary by parse_log_line()
# 3) All dictionaries are collected into a list by load_log_file()
# 4) That list is grouped into dictionaries (server/env/status buckets) by
#    summarize_by_server(), summarize_by_env(), summarize_health()
# 5) For each bucket (ex: one server), compute_server_metrics() calculates:
#    - total checks, uptime %, warnings, critical downs
#    - avg/max CPU and avg/max disk (skipping None values safely)
# 6) Report functions render human-readable output:
#    - Printed to terminal
#    - Written to a .txt report file (optional via file handle)
#
# WHY IT'S CODED THIS WAY:
# - Separation of concerns: parse vs group vs compute vs report
# - Reusability: one metrics function works for server buckets AND env buckets
# - Safety: guards prevent crashes (empty lists, N/A values, division by zero)
# - Clean output: write_and_print centralizes "print + optional file write"
# =============================================================================

REPORT_FILE_SERV = "server_analytics_report.txt"
REPORT_FILE_ENV = "environment_analytics_report.txt"

# =============================================================================
# --- CLEANUP PHASE
# =============================================================================
def parse_log_line(line):
    # PURPOSE: Convert one raw CSV log line into a clean dictionary (or None).
    # WHY: We want structured data (dicts) instead of raw strings for analysis.
    # SAFETY: Returns None for empty lines so they don't break the pipeline.

    line = line.strip()  # removes whitespace/newlines at both ends
    if line == "":
        return None  # guard: skip empty lines

    parts = line.split(",")  # split CSV into pieces

    # PURPOSE: strip extra spaces from each CSV field
    # WHY: log lines often contain spaces after commas -> " web01" not "web01"
    clean_parts = []
    for p in parts:
        clean_parts.append(p.strip())

    # EXPECTED FORMAT:
    # 0 timestamp, 1 server, 2 env, 3 True/False, 4 cpu, 5 disk, 6 status
    timestamp_text = clean_parts[0]
    server_name = clean_parts[1]
    server_env = clean_parts[2]
    is_up_text = clean_parts[3]
    cpu_text = clean_parts[4]
    disk_text = clean_parts[5]
    status_text = clean_parts[6]

    # PURPOSE: Convert "True"/"False" strings into real booleans.
    is_up = True if is_up_text == "True" else False

    # PURPOSE: Convert numeric strings into ints; "N/A" becomes None.
    # WHY: None represents "missing metric" and prevents math errors later.
    if cpu_text == "N/A":
        cpu = None
    else:
        cpu = int(cpu_text)

    if disk_text == "N/A":
        disk = None
    else:
        disk = int(disk_text)

    # PURPOSE: Store all cleaned values in a single "record" dict.
    # WHY: Dicts give named fields so downstream code is readable:
    #      entry["cpu"], entry["server"], entry["status"], etc.
    record = {
        "timestamp": timestamp_text,
        "server": server_name,
        "env": server_env,
        "is_up": is_up,
        "cpu": cpu,
        "disk": disk,
        "status": status_text,
    }
    return record


def load_log_file(file_path):
    # PURPOSE: Read the whole file and return a list of parsed dictionaries.
    # WHY: A list of dicts is the "raw dataset" that all summaries build from.

    entries = []

    # WHY "with open(...) as f":
    # - Opens the file safely
    # - Automatically closes the file when the block ends (even if errors occur)
    with open(file_path, "r") as f:
        for line in f:
            entry = parse_log_line(line)  # parse ONE line -> dict or None
            if entry is None:
                continue  # skip bad/empty lines
            entries.append(entry)  # collect the good parsed record

    return entries


# =============================================================================
# --- SUMMARY AND GROUPING PHASE
# =============================================================================
def summarize_by_server(entries):
    # PURPOSE: Group entries by server.
    # RETURNS: dict where key=server and value=list of entry dicts
    # WHY: Makes per-server reporting easy:
    #      summary_serv["web01"] -> list of all web01 entries

    summary_serv = {}

    for entry in entries:
        server = entry["server"]  # server name like "web01"

        # PATTERN: "create bucket if missing"
        if server not in summary_serv:
            summary_serv[server] = []

        # add the entire entry dict into that server's bucket
        summary_serv[server].append(entry)

    return summary_serv


def summarize_by_env(entries):
    # PURPOSE: Group entries by environment (prod/dev/stage).
    # WHY: Lets you report environment-wide health across all servers in that env.

    summary_env = {}

    for entry in entries:
        env = entry["env"]

        if env not in summary_env:
            summary_env[env] = []

        summary_env[env].append(entry)

    return summary_env


def summarize_health(entries):
    # PURPOSE: Group entries by status (GOOD/WARNING/CRITICAL).
    # WHY: Useful if you want a "status report" by category.

    summary_status = {}

    for entry in entries:
        status = entry["status"]

        if status not in summary_status:
            summary_status[status] = []

        summary_status[status].append(entry)

    return summary_status


# =============================================================================
# --- REPORTING AND ANALYTICS PHASE
# =============================================================================
def write_and_print(text, file_handle):
    # PURPOSE: Print to terminal AND (optionally) write to a report file.
    # WHY: Avoid duplicating "print()" and "file.write()" everywhere.
    # DESIGN: report functions open/close file; this helper only writes lines.

    print(text)
    if file_handle:
        file_handle.write(text + "\n")


def generate_server_report(summary_serv, report_file_path=None):
    # PURPOSE: For each server bucket, compute metrics and output a report.
    #
    # KEY DESIGN CHOICE:
    # f = open(...) if report_file_path else None
    # - If a path is provided -> write report to file
    # - If no path -> f is None, so write_and_print prints only

    # NOTE: We open the file ONCE (outside the loop) for correctness & efficiency.
    # If you open with "w" inside the loop, it would overwrite the file repeatedly.
    f = open(report_file_path, "w") if report_file_path else None

    for server in summary_serv:
        # EEE:
        # summary_serv -> dict mapping server -> list of entries
        # [server] -> pull the list for this server key
        entries_for_server = summary_serv[server]

        # PURPOSE: derive env label for the server (usually constant)
        # SAFETY: guard prevents IndexError when list is empty
        if entries_for_server:
            # EEE: entries_for_server[0] is first dict; ["env"] pulls env string
            env = entries_for_server[0]["env"]
        else:
            env = "unknown"

        # Compute metrics using the list of entries for this server
        metrics = compute_server_metrics(entries_for_server)

        # Render output: same lines go to terminal and file (if f is not None)
        write_and_print("========================================", f)
        write_and_print(f"SERVER: {server} (env: {env})", f)
        write_and_print(f"Total checks: {metrics['total_checks']}", f)
        write_and_print(
            f"Uptime: {metrics['up_count']}/{metrics['total_checks']} ({metrics['uptime_pct']:.1f}%)",
            f,
        )
        write_and_print(f"Warnings: {metrics['warning_count']}", f)
        write_and_print(f"Critical (down): {metrics['critical_count']}", f)
        write_and_print(
            f"Avg CPU: {metrics['avg_cpu']:.1f}% | Max CPU: {metrics['max_cpu']}%",
            f,
        )
        write_and_print(
            f"Avg Disk: {metrics['avg_disk']:.1f}% | Max Disk: {metrics['max_disk']}%",
            f,
        )
        write_and_print("========================================", f)
        write_and_print("", f)

    # Always close the file if we opened it (resource cleanup)
    if f:
        f.close()


def generate_env_report(summary_env, report_file_path=None):
    # PURPOSE: Report metrics by environment (prod/dev/stage).
    # DIFFERENCE vs server report:
    # - An environment can contain multiple servers, so we also list server names.

    f = open(report_file_path, "w") if report_file_path else None

    for env in summary_env:
        entries_for_env = summary_env[env]

        # env itself is already the label from the dict key
        env_name = env if entries_for_env else "unknown"

        # PURPOSE: show which servers belong to this environment (unique + sorted)
        # WHY: env groups are many-to-one (many servers inside one env)
        # EEE:
        # {entry["server"] for entry in entries_for_env} -> set of server names (unique)
        # sorted(...) -> sorted list for clean printing
        servers_in_env = sorted({entry["server"] for entry in entries_for_env})

        metrics = compute_server_metrics(entries_for_env)

        write_and_print("========================================", f)
        write_and_print(f"ENVIRONMENT: {env_name}", f)
        write_and_print(f"Servers in this env: {', '.join(servers_in_env)}", f)
        write_and_print(f"Total checks: {metrics['total_checks']}", f)
        write_and_print(
            f"Uptime: {metrics['up_count']}/{metrics['total_checks']} ({metrics['uptime_pct']:.1f}%)",
            f,
        )
        write_and_print(f"Warnings: {metrics['warning_count']}", f)
        write_and_print(f"Critical (down): {metrics['critical_count']}", f)
        write_and_print(
            f"Avg CPU: {metrics['avg_cpu']:.1f}% | Max CPU: {metrics['max_cpu']}%",
            f,
        )
        write_and_print(
            f"Avg Disk: {metrics['avg_disk']:.1f}% | Max Disk: {metrics['max_disk']}%",
            f,
        )
        write_and_print("========================================", f)
        write_and_print("", f)

    if f:
        f.close()


# =============================================================================
# --- METRICS COMPUTATION PHASE
# =============================================================================
def compute_server_metrics(entries_for_server):
    # PURPOSE: Compute summary metrics for ANY group of entries.
    # IMPORTANT DESIGN:
    # - Works for server buckets AND env buckets (reusable analytics engine)
    # - Handles None CPU/Disk safely (skips missing values)
    # - Uses guards to avoid division by zero

    total_checks = len(entries_for_server)
    up_count = 0
    warning_count = 0
    critical_count = 0

    cpu_values = []
    disk_values = []

    for entry in entries_for_server:
        # Uptime / critical tracking is based on is_up (source of truth for down)
        if entry["is_up"]:
            up_count += 1
        else:
            critical_count += 1

        # WARNING is separate because it means "up but degraded"
        if entry["status"] == "WARNING":
            warning_count += 1

        # SAFETY: Only include real numbers in averages/max calculations
        if entry["cpu"] is not None:
            cpu_values.append(entry["cpu"])
        if entry["disk"] is not None:
            disk_values.append(entry["disk"])

    # WHY compute after the loop:
    # - Need all values collected first
    # - Avoid repeated recalculation inside the loop
    if cpu_values:
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)
    else:
        avg_cpu = 0
        max_cpu = 0

    if disk_values:
        avg_disk = sum(disk_values) / len(disk_values)
        max_disk = max(disk_values)
    else:
        avg_disk = 0
        max_disk = 0

    # SAFETY: Guard against divide-by-zero if there are no checks
    if total_checks > 0:
        uptime_pct = (up_count / total_checks) * 100
    else:
        uptime_pct = 0

    return {
        "total_checks": total_checks,
        "up_count": up_count,
        "warning_count": warning_count,
        "critical_count": critical_count,
        "avg_cpu": avg_cpu,
        "max_cpu": max_cpu,
        "avg_disk": avg_disk,
        "max_disk": max_disk,
        "uptime_pct": uptime_pct,
    }


# =============================================================================
# --- MAIN (PROGRAM CONTROL / ORCHESTRATION)
# =============================================================================
def main():
    # PURPOSE: main() is the conductor.
    # WHY: Keeps "execution order" in one place and avoids messy global flow.

    # 1) Load all entries from the log file
    entries = load_log_file("server_check_log.txt")

    # 2) Group entries into server buckets and env buckets
    summary_serv = summarize_by_server(entries)
    summary_env = summarize_by_env(entries)

    # 3) Generate reports (printed + written to files)
    generate_server_report(summary_serv, REPORT_FILE_SERV)
    generate_env_report(summary_env, REPORT_FILE_ENV)


# Standard Python entrypoint:
# - When you run this file directly, main() runs.
# - When you import this file elsewhere, main() does NOT auto-run.
if __name__ == "__main__":
    main()
