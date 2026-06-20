# V2ray IP Scanner & Config Generator 🚀

A practical and fast Python tool to find clean IPs and automatically generate V2ray configs.

## ✨ Features

*   **Two Operational Modes:**
    1.  **Config Scanner & Generator:** Takes your config (VMess, VLESS, Trojan), automatically extracts the port, finds a working/clean IP, and generates a new working config.
    2.  **Basic IP Scanner:** Simple IP scanning by just taking your desired port.
*   **Multi-Protocol Support:** Fully compatible with VMess, VLESS, and Trojan links.
*   **Clean Console UI:** Automatically clears the console environment after each operation for a better user experience.
*   **Auto-Save Results:** Saves clean IPs and generated configs into separate text files (`clean_ips.txt` and `clean_configs.txt`).

## 📥 How to Use

### Method 1: Using the Executable (Recommended for Windows Users)
1. Go to the [Releases](../../releases) section on the right side of this repository.
2. Download the latest `.exe` file.
3. Run the application and select your desired option from the menu.

### Method 2: Running the Python Source Code
If you prefer to run the script directly, make sure you have Python installed, then install the required dependencies:
```bash
pip install pyfiglet requests
Then, run the script:
bash
python scanner.py

## ⚠️ Disclaimer
This tool is developed solely for the purpose of finding IPs with good latency/ping.

!
