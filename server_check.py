#===IMPORTS===
import random
import time
from datetime import datetime
from colorama import init, Fore, Style
init(autoreset=True)


#===CONFIG KNOBS===
CHECK_INTERVAL = 5
CPU_WARN_THRESHOLD = 80
DISK_WARN_THRESHOLD = 85
LOG_FILE = "server_check_log.txt"

servers = ["web01", "db01", "cache01", "auth01", "auth02"]
hardcode_env = {"web01":"prod", "db01":"prod", "cache01":"dev", "auth01":"stage"}

#===HElPER FUNCTIONS===
def health_eval(is_up, cpu, disk):
    if not is_up:
        return "CRITICAL"
    elif cpu > CPU_WARN_THRESHOLD or disk > DISK_WARN_THRESHOLD:
        return "WARNING"
    else:
        return "GOOD"

def simulate_metrics():
    is_up = random.choice([True, True, False, True])
    cpu = random.randint(0, 100)
    disk = random.randint(0, 100)
    return is_up, cpu, disk


def check_server(server_name):
    server_env = hardcode_env.get(server_name, "dev")

    is_up, cpu, disk = simulate_metrics()
    status = health_eval(is_up, cpu, disk)
    if status == "GOOD":
        status_color = Fore.GREEN
    elif status == "WARNING":
        status_color = Fore.YELLOW
    else:
        status_color = Fore.RED
    if not is_up:
        cpu = "N/A"
        disk = "N/A"

    timestamp = datetime.now().isoformat()
    log_line = (f'{timestamp}, {server_name}, {server_env}, {is_up}, {cpu}, {disk}, {status}\n')

    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_line)

    print(f"=== Summary for {server_name} /// Type: {server_env} ===\n"
            f"Status:{status_color}!!!{status}!!!\n"
            f"Up: {is_up}\n"
            f"CPU Usage Percentage: {cpu}\n"
            f"Disk Usage Percentage: {disk}\n")

def run_cycle():
    for server in servers:
        print(f"\n--- Checking {server} ---")
        check_server(server)

#===ENTRY POINT W/ MAIN GUARD===
def main():
    try:
        while True:
            print('++++Server Health Checker++++')
            print(datetime.now().isoformat())
            run_cycle()
            print("++++Cycle Complete++++\n*** STOP with Ctrl + C ***")
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("Stopped by user via Key-press")

if __name__ == "__main__":
    main()