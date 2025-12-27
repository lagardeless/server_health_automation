import argparse
# =============================================================================
# Configuration
# =============================================================================

REPORT_FILE_SERV = "server_analytics_report.txt"
REPORT_FILE_ENV = "environment_analytics_report.txt"


# =============================================================================
# Parsing & Cleanup Helpers
# =============================================================================

def parse_log_line(line):
    line = line.strip()
    if line == "":
        return None

    parts = line.split(",")
    clean_parts = [p.strip() for p in parts]

    timestamp_text = clean_parts[0]
    server_name = clean_parts[1]
    server_env = clean_parts[2]
    is_up_text = clean_parts[3]
    cpu_text = clean_parts[4]
    disk_text = clean_parts[5]
    status_text = clean_parts[6]

    is_up = True if is_up_text == "True" else False

    cpu = None if cpu_text == "N/A" else int(cpu_text)
    disk = None if disk_text == "N/A" else int(disk_text)

    return {
        "timestamp": timestamp_text,
        "server": server_name,
        "env": server_env,
        "is_up": is_up,
        "cpu": cpu,
        "disk": disk,
        "status": status_text,
    }


def load_log_file(file_path):
    entries = []

    with open(file_path, "r") as f:
        for line in f:
            entry = parse_log_line(line)
            if entry is not None:
                entries.append(entry)

    return entries


# =============================================================================
# Grouping / Summarization Helpers
# =============================================================================

def summarize_by_server(entries):
    summary_serv = {}

    for entry in entries:
        server = entry["server"]
        if server not in summary_serv:
            summary_serv[server] = []
        summary_serv[server].append(entry)

    return summary_serv


def summarize_by_env(entries):
    summary_env = {}

    for entry in entries:
        env = entry["env"]
        if env not in summary_env:
            summary_env[env] = []
        summary_env[env].append(entry)

    return summary_env


def summarize_health(entries):
    summary_status = {}

    for entry in entries:
        status = entry["status"]
        if status not in summary_status:
            summary_status[status] = []
        summary_status[status].append(entry)

    return summary_status


# =============================================================================
# Metrics / Analytics Helpers
# =============================================================================

def compute_server_metrics(entries_for_server):
    total_checks = len(entries_for_server)
    up_count = 0
    warning_count = 0
    critical_count = 0

    cpu_values = []
    disk_values = []

    for entry in entries_for_server:
        if entry["is_up"]:
            up_count += 1
        else:
            critical_count += 1

        if entry["status"] == "WARNING":
            warning_count += 1

        if entry["cpu"] is not None:
            cpu_values.append(entry["cpu"])

        if entry["disk"] is not None:
            disk_values.append(entry["disk"])

    avg_cpu = sum(cpu_values) / len(cpu_values) if cpu_values else 0
    max_cpu = max(cpu_values) if cpu_values else 0

    avg_disk = sum(disk_values) / len(disk_values) if disk_values else 0
    max_disk = max(disk_values) if disk_values else 0

    uptime_pct = (up_count / total_checks) * 100 if total_checks > 0 else 0

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
# Reporting Helpers
# =============================================================================

def write_and_print(text, file_handle):
    print(text)
    if file_handle:
        file_handle.write(text + "\n")

def build_server_report_text(summary_serv):
    lines = []
    lines.append("===Server Report===")
    for server_name, stats in summary_serv.items():

def generate_server_report(summary_serv, report_file_path=None):
    f = open(report_file_path, "w") if report_file_path else None

    for server, entries_for_server in summary_serv.items():
        env = entries_for_server[0]["env"] if entries_for_server else "unknown"
        metrics = compute_server_metrics(entries_for_server)

        write_and_print("========================================", f)
        write_and_print(f"SERVER: {server} (env: {env})", f)
        write_and_print(f"Total checks: {metrics['total_checks']}", f)
        write_and_print(
            f"Uptime: {metrics['up_count']}/{metrics['total_checks']} "
            f"({metrics['uptime_pct']:.1f}%)",
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


def generate_env_report(summary_env, report_file_path=None):
    f = open(report_file_path, "w") if report_file_path else None

    for env, entries_for_env in summary_env.items():
        env_name = env if entries_for_env else "unknown"
        servers_in_env = sorted({entry["server"] for entry in entries_for_env})
        metrics = compute_server_metrics(entries_for_env)

        write_and_print("========================================", f)
        write_and_print(f"ENVIRONMENT: {env_name}", f)
        write_and_print(f"Servers in this env: {', '.join(servers_in_env)}", f)
        write_and_print(f"Total checks: {metrics['total_checks']}", f)
        write_and_print(
            f"Uptime: {metrics['up_count']}/{metrics['total_checks']} "
            f"({metrics['uptime_pct']:.1f}%)",
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
# Entry Point (Main Guard)
# =============================================================================

def main():

    parser = argparse.ArgumentParser(
        description="Generate analytics reports from server heath logs."
    )
    parser.add_argument(
        "--input",
        default="server_check_log.txt",
        help="Path to the input log file (default: server_check_log.txt).",
    )

    parser.add_argument(
        "--output",
        default="analytics_report.txt:",
        help="Path to the output report files (default: analytics_report.txt).",
    )

    parser.add_argument(
        "--report",
        choices=["server", "env", "both"],
        default="both",
        help="Which report(s) to generate: server, env, or both (default: both).",
    )

    parser.add_argument(
        "--no-file",
        action="store_true",
        help="Print report(s) to terminal instead of writing output files.",

    )

    args = parser.parse_args()

    entries = load_log_file(args.input)

    summary_serv = summarize_by_server(entries)
    summary_env = summarize_by_env(entries)

    server_report_path = f"server_{args.output}.txt"
    env_report_path =  f"env_{args.output}.txt"

    generate_server_report(summary_serv, server_report_path)
    generate_env_report(summary_env,env_report_path)


if __name__ == "__main__":
    main()
