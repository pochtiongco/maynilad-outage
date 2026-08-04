import requests
import urllib3
from bs4 import BeautifulSoup
import json
import os

# Ignore SSL warnings (temporary workaround)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===========================
# CONFIGURATION
# ===========================

CAN = "59982918"

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

BASE_URL = "https://www.mayniladwater.com.ph/wp-json/interruptions"
STATE_FILE = "state.json"


def load_last_message():
    if not os.path.exists(STATE_FILE):
        return ""

    with open(STATE_FILE, "r") as f:
        return json.load(f).get("last_message", "")


def save_last_message(message):
    with open(STATE_FILE, "w") as f:
        json.dump({"last_message": message}, f, indent=2)
# ===========================
# DISCORD
# ===========================

def send_discord(message):
    response = requests.post(
        WEBHOOK_URL,
        json={"content": message},
        verify = False
    )

    if response.status_code == 204:
        print("✅ Discord notification sent!")
    else:
        print("❌ Failed to send Discord notification.")
        print(response.status_code)
        print(response.text)


# ===========================
# MAYNILAD CHECKER
# ===========================

def check_endpoint(endpoint):
    url = f"{BASE_URL}/{endpoint}?CAN={CAN}"

    response = requests.get(url, verify=False)

    if response.status_code != 200:
        print(f"Failed to check {endpoint}")
        return []

    html = response.text
    html = html.replace("\\/", "/")
    html = html.replace('\\"', '"')

    soup = BeautifulSoup(html, "html.parser")

    table = soup.find("table")

    if table is None:
        return []

    rows = table.find_all("tr")

    outages = []

    for row in rows:
        cells = row.find_all("td")

        if len(cells) == 0:
            continue

        outages.append({
            "type": endpoint.title(),
            "city": cells[0].get_text(strip=True),
            "barangay": cells[1].get_text(strip=True),
            "area": cells[2].get_text(strip=True),
            "from": cells[3].get_text(strip=True),
            "to": cells[4].get_text(strip=True),
            "time": cells[5].get_text(strip=True),
            "reason": cells[6].get_text(strip=True)
        })

    return outages


# ===========================
# MAIN
# ===========================

all_outages = []

for endpoint in [
    "emergency",
    "scheduled",
    "rotational"
]:
    all_outages.extend(check_endpoint(endpoint))


if len(all_outages) == 0:

    message = (
        "✅ **Maynilad Monitor**\n\n"
        "No active interruptions were found."
    )

else:

    message = "🚨 **Maynilad Interruption Detected** 🚨\n\n"

    for outage in all_outages:

        message += (
            f"**Type:** {outage['type']}\n"
            f"**City:** {outage['city']}\n"
            f"**Barangay:** {outage['barangay']}\n"
            f"**Area:** {outage['area']}\n"
            f"**From:** {outage['from']}\n"
            f"**To:** {outage['to']}\n"
            f"**Time:** {outage['time']}\n"
            f"**Reason:** {outage['reason']}\n"
            "\n-----------------------------------\n\n"
        )

last_message = load_last_message()

if message != last_message:
    print("Change detected! Sending notification...")
    send_discord(message)
    save_last_message(message)
else:
    print("No changes. Nothing sent.")