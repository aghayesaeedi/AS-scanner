import os
import sys
import time
import asyncio
import ipaddress
import random
import pyfiglet
import questionary
import urllib.parse
import base64
import json
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.align import Align
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.live import Live

# ==========================================
#               Constants
# ==========================================
APP_NAME = "Aghaye Saeedi"
CREATOR = "Aghaye Saeedi"
GITHUB_URL = "https://github.com/YourUsername"  # Replace with your own GitHub URL

# Official Cloudflare IP ranges
CF_IP_RANGES = [
    "173.245.48.0/20", "103.21.244.0/22", "103.22.200.0/22",
    "103.31.4.0/22",   "141.101.64.0/18", "108.162.192.0/18",
    "190.93.240.0/20", "188.114.96.0/20", "197.234.240.0/22",
    "198.41.128.0/17", "162.158.0.0/15",  "104.16.0.0/13",
    "104.24.0.0/14",   "172.64.0.0/13",   "131.0.72.0/22"
]

# Pre-compute network objects once for fast random IP generation
CF_NETWORKS = [ipaddress.IPv4Network(cidr) for cidr in CF_IP_RANGES]

console = Console()

# ==========================================
#   Custom Style for questionary Menus
# ==========================================
CUSTOM_STYLE = Style.from_dict({
    "qmark":        "fg:#00ffff bold",
    "question":     "bold",
    "answer":       "fg:#00ff00 bold",
    "pointer":      "fg:#ff00ff bold",
    "highlighted":  "fg:#ffff00 bold",
    "selected":     "fg:#00ff00",
    "separator":    "fg:#cc5454",
    "instruction":  "fg:#888888 italic",
    "text":         "",
    "disabled":     "fg:#858585 italic",
})


# ==========================================
#           Terminal Helpers
# ==========================================
def clear_screen():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")


def print_banner():
    """Print the centered ASCII banner with branding."""
    clear_screen()
    fig = pyfiglet.Figlet(font="slant")
    banner = fig.renderText(APP_NAME)
    console.print(Align.center(f"[bold cyan]{banner}[/bold cyan]"))
    console.print(Align.center(Text(
        f"Scanner & Config Generator  |  Created by {CREATOR}",
        style="bold bright_magenta"
    )))
    console.print(Align.center(Text(
        f"GitHub: {GITHUB_URL}",
        style="bold bright_blue underline"
    )))
    console.print(Align.center("[bold black]" + "━" * 55 + "[/bold black]"))
    console.print("")


def get_vpad():
    """Calculate vertical padding to center content in the terminal."""
    term_height = console.size.height
    return "\n" * max(0, (term_height - 15) // 2)


def print_footer():
    """Print the footer with creator credit and GitHub link."""
    console.print("")
    console.print(Align.center("[bold black]" + "━" * 55 + "[/bold black]"))
    console.print(Align.center(Text(
        f"  Created by {CREATOR}  ",
        style="bold bright_magenta"
    )))
    console.print(Align.center(Text(
        f"  GitHub: {GITHUB_URL}  ",
        style="bold bright_blue underline"
    )))
    console.print(Align.center("[bold black]" + "━" * 55 + "[/bold black]"))
    console.print("")


def centered_select(message, choices):
    """Display a vertically and horizontally centered selection menu."""
    print_banner()
    console.print(get_vpad())
    return questionary.select(
        message,
        choices=choices,
        instruction="(Use arrow keys to navigate, Enter to select)",
        qmark=">",
        style=CUSTOM_STYLE,
    ).ask()


def centered_text(message, default=""):
    """Display a vertically and horizontally centered text input."""
    print_banner()
    console.print(get_vpad())
    return questionary.text(
        message,
        default=default,
        qmark=">",
        style=CUSTOM_STYLE,
    ).ask()


def show_message(msg_text, style="bold green"):
    """Print a centered message WITHOUT clearing the screen."""
    console.print("")
    console.print(Align.center(f"[{style}]{msg_text}[/{style}]"))
    console.print("")


def centered_pause():
    """Show a centered pause prompt and wait for Enter."""
    console.print("")
    console.print(Align.center("[bold dim]Press Enter to continue...[/bold dim]"))
    input()


# ==========================================
#      Config Parser & Generator
# ==========================================
def parse_proxy_config(config_str):
    """
    Extract the port, protocol, and parsed data
    from vmess, vless, or trojan config strings.
    Returns (port, protocol, parsed_data) or (None, None, None).
    """
    try:
        # ---- VMess ----
        if config_str.startswith("vmess://"):
            raw_b64 = config_str[8:]
            # Fix missing base64 padding
            padding = len(raw_b64) % 4
            if padding:
                raw_b64 += "=" * (4 - padding)
            decoded = base64.b64decode(raw_b64).decode("utf-8")
            data = json.loads(decoded)
            port = int(data.get("port", 443))
            return port, "vmess", data

        # ---- VLESS / Trojan ----
        elif config_str.startswith("vless://") or config_str.startswith("trojan://"):
            parsed = urllib.parse.urlparse(config_str)
            port = int(parsed.port) if parsed.port else 443
            protocol = parsed.scheme  # "vless" or "trojan"
            return port, protocol, parsed

    except Exception:
        pass

    return None, None, None


def generate_proxy_config(ip, protocol, parsed_data):
    """
    Generate a new config string replacing the address
    with the given clean IP.
    """
    try:
        # ---- VMess ----
        if protocol == "vmess":
            data = parsed_data.copy()
            data["add"] = ip
            encoded = base64.b64encode(
                json.dumps(data).encode("utf-8")
            ).decode("utf-8")
            return f"vmess://{encoded}"

        # ---- VLESS / Trojan ----
        else:
            userinfo = parsed_data.username or ""
            if parsed_data.password:
                userinfo += f":{parsed_data.password}"

            if userinfo:
                new_netloc = f"{userinfo}@{ip}:{parsed_data.port}"
            else:
                new_netloc = f"{ip}:{parsed_data.port}"

            new_parsed = parsed_data._replace(netloc=new_netloc)
            return urllib.parse.urlunparse(new_parsed)

    except Exception:
        return None


def generate_random_cf_ips(count):
    """Generate random IPs from the pre-computed Cloudflare networks."""
    ips = []
    for _ in range(count):
        network = random.choice(CF_NETWORKS)
        ip = str(network[random.randint(1, network.num_addresses - 2)])
        ips.append(ip)
    return ips


# ==========================================
#           Async Scanner Core
# ==========================================
async def check_ip(ip, port, timeout):
    """
    Attempt a TCP connection to (ip, port).
    Returns (ip_str, ping_ms) on success, (ip_str, None) on failure.
    """
    start_time = time.time()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(str(ip), port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        ping = (time.time() - start_time) * 1000
        return str(ip), ping
    except Exception:
        return str(ip), None


async def run_scanner(ips_to_scan, port, max_ping, target_clean):
    """
    Scan a list of IPs on the given port.
    Returns a list of (ip_str, ping_ms) tuples for clean IPs.
    """
    print_banner()
    console.print(Align.center(
        f"[bold yellow]Scanning Port {port}  |  "
        f"Max Ping: {max_ping}ms  |  "
        f"Target: {target_clean} IPs[/bold yellow]"
    ))
    console.print("")

    clean_ips = []
    timeout = max(1.5, max_ping / 1000.0)

    # Build the live results table
    table = Table(
        show_header=True,
        header_style="bold magenta",
        title="[bold cyan]Live Scan Results[/bold cyan]",
    )
    table.add_column("No.", style="dim", width=6, justify="center")
    table.add_column("IP Address", justify="center", style="green")
    table.add_column("Ping (ms)", justify="center", style="yellow")

    with Live(Align.center(table), refresh_per_second=4, console=console) as live:
        # Process IPs in batches of 50
        batch_size = 50
        idx = 0

        while idx < len(ips_to_scan) and len(clean_ips) < target_clean:
            batch = ips_to_scan[idx : idx + batch_size]
            idx += batch_size

            tasks = [
                asyncio.create_task(check_ip(ip, port, timeout))
                for ip in batch
            ]

            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED
            )

            # Process completed tasks immediately
            for task in done:
                if len(clean_ips) >= target_clean:
                    break
                ip_str, ping = task.result()
                if ping is not None and ping <= max_ping:
                    clean_ips.append((ip_str, ping))
                    table.add_row(
                        str(len(clean_ips)),
                        ip_str,
                        f"{ping:.0f} ms",
                    )

            # Cancel remaining pending tasks in this batch
            # once we have enough results
            if len(clean_ips) >= target_clean:
                for task in pending:
                    task.cancel()
                await asyncio.gather(*pending, return_exceptions=True)
            else:
                # Wait for remaining tasks in this batch to finish
                results = await asyncio.gather(*pending, return_exceptions=True)
                for result in results:
                    if len(clean_ips) >= target_clean:
                        break
                    if isinstance(result, tuple):
                        ip_str, ping = result
                        if ping is not None and ping <= max_ping:
                            clean_ips.append((ip_str, ping))
                            table.add_row(
                                str(len(clean_ips)),
                                ip_str,
                                f"{ping:.0f} ms",
                            )

    # ---- Final Results Display ----
    clear_screen()
    print_banner()

    final_table = Table(show_header=True, header_style="bold magenta")
    final_table.add_column("No.", style="dim", width=6, justify="center")
    final_table.add_column("Clean IP Address", justify="center", style="bold green")
    final_table.add_column("Ping (ms)", justify="center", style="bold yellow")

    for num, (ip_str, ping) in enumerate(clean_ips, 1):
        final_table.add_row(str(num), ip_str, f"{ping:.0f} ms")

    console.print(get_vpad())
    console.print(Align.center(Panel(
        final_table,
        title="[bold cyan]Scan Completed[/bold cyan]",
        border_style="green",
        expand=False,
    )))

    if not clean_ips:
        console.print(Align.center(
            "[bold red]No clean IPs found matching your criteria.[/bold red]"
        ))

    print_footer()
    return clean_ips


# ==========================================
#        Main Interactive Menu
# ==========================================
def interactive_menu():
    """Main menu loop with arrow-key navigation."""
    while True:
        choice = centered_select(
            "Select an option:",
            choices=[
                questionary.Choice(
                    "  Config Scanner & Generator  (Auto-extract port)", "1"
                ),
                questionary.Choice(
                    "  Basic IP Scanner  (Manual port)", "2"
                ),
                questionary.Choice(
                    "  About", "3"
                ),
                questionary.Choice(
                    "  Exit", "0"
                ),
            ],
        )

        # ---- Exit ----
        if choice is None or choice == "0":
            clear_screen()
            console.print(Align.center("\n[bold green]Goodbye![/bold green]\n"))
            break

        # ---- About ----
        if choice == "3":
            print_banner()
            console.print(get_vpad())
            about_text = Text()
            about_text.append(f"  {APP_NAME}\n", style="bold cyan")
            about_text.append("  A fast async scanner for working Cloudflare IPs.\n")
            about_text.append("  Supports vless, vmess, and trojan config generation.\n\n")
            about_text.append(f"  Created by {CREATOR}\n", style="bold bright_magenta")
            about_text.append(f"  {GITHUB_URL}\n", style="bold bright_blue underline")
            console.print(Align.center(Panel(
                about_text,
                title="About",
                border_style="cyan",
                padding=(1, 4),
            )))
            print_footer()
            centered_pause()
            continue

        try:
            port = None
            protocol = None
            parsed_data = None
            base_config = None
            config_mode = False

            # ==== Option 1: Config Scanner & Generator ====
            if choice == "1":
                config_mode = True
                raw = centered_text(
                    "Paste your VLESS / Trojan / VMess config:"
                )
                if not raw or not raw.strip():
                    show_message("Config cannot be empty!", "bold red")
                    centered_pause()
                    continue

                base_config = raw.strip()
                port, protocol, parsed_data = parse_proxy_config(base_config)

                if port is None:
                    show_message(
                        "Invalid config format or could not extract port!",
                        "bold red",
                    )
                    centered_pause()
                    continue

                # Let the user confirm or override the extracted port
                port_str = centered_text(
                    f"Extracted port is {port}. "
                    f"Press Enter to confirm or type a new one:",
                    default=str(port),
                )
                port = int(port_str) if port_str and port_str.strip().isdigit() else port

            # ==== Option 2: Basic IP Scanner ====
            elif choice == "2":
                port_str = centered_text("Enter target port:", default="443")
                port = int(port_str) if port_str and port_str.strip().isdigit() else 443

            # ==== Shared parameters ====
            max_ping_str = centered_text(
                "Enter max acceptable ping (ms):", default="500"
            )
            max_ping = int(max_ping_str) if max_ping_str and max_ping_str.strip().isdigit() else 500

            target_clean_str = centered_text(
                "Enter number of clean IPs to find:", default="10"
            )
            target_clean = int(target_clean_str) if target_clean_str and target_clean_str.strip().isdigit() else 10

            ip_source = centered_select(
                "Choose IP Source:",
                choices=[
                    questionary.Choice(
                        "  Default Cloudflare Ranges", "cf"
                    ),
                    questionary.Choice(
                        "  Load from ips.txt", "file"
                    ),
                ],
            )

            if ip_source is None:
                continue

            # ==== Load IPs ====
            ips_to_scan = []

            if ip_source == "cf":
                show_message(
                    "Generating random IPs from Cloudflare ranges...",
                    "bold yellow",
                )
                ips_to_scan = generate_random_cf_ips(max(5000, target_clean * 50))

            elif ip_source == "file":
                if os.path.exists("ips.txt"):
                    with open("ips.txt", "r") as f:
                        ips_to_scan = [
                            line.strip() for line in f if line.strip()
                        ]
                else:
                    show_message("Error: 'ips.txt' not found!", "bold red")
                    centered_pause()
                    continue

            if not ips_to_scan:
                show_message(
                    "No IPs loaded. Please check your source.",
                    "bold red",
                )
                centered_pause()
                continue

            # ==== Run the scanner ====
            clean_ips = asyncio.run(
                run_scanner(ips_to_scan, port, max_ping, target_clean)
            )

            # ==== Post-scan actions ====
            if clean_ips:
                if config_mode:
                    # Generate new configs with clean IPs
                    configs = []
                    for ip_str, ping_val in clean_ips:
                        new_conf = generate_proxy_config(
                            ip_str, protocol, parsed_data
                        )
                        if new_conf:
                            configs.append(new_conf)

                    if configs:
                        with open("clean_configs.txt", "w", encoding="utf-8") as f:
                            for conf in configs:
                                f.write(f"{conf}\n")
                        show_message(
                            f"Generated {len(configs)} configs "
                            f"-> saved to 'clean_configs.txt'",
                            "bold green",
                        )
                    else:
                        show_message(
                            "Failed to generate new configs.",
                            "bold red",
                        )

                else:
                    # Save clean IPs only (no config)
                    with open("clean_ips.txt", "w") as f:
                        for ip_str, _ in clean_ips:
                            f.write(f"{ip_str}\n")
                    show_message(
                        f"Saved {len(clean_ips)} IPs -> 'clean_ips.txt'",
                        "bold green",
                    )

            centered_pause()

        except ValueError:
            show_message(
                "Invalid input. Please enter numbers only.",
                "bold red",
            )
            centered_pause()
        except KeyboardInterrupt:
            continue


# ==========================================
#             Entry Point
# ==========================================
if __name__ == "__main__":
    try:
        if os.name == "nt":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        interactive_menu()
    except KeyboardInterrupt:
        clear_screen()
        console.print(Align.center(
            "\n[bold red]Program terminated by user.[/bold red]\n"
        ))
        sys.exit(0)
    except Exception as e:
        clear_screen()
        console.print(Align.center(
            f"\n[bold red]An unexpected error occurred:[/bold red] {e}"
        ))
        console.print_exception()
        centered_pause()
        sys.exit(1)