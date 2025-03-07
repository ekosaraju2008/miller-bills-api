from fastapi import FastAPI
import requests
import sqlite3

app = FastAPI()

API_KEY = "YOUR_API_KEY"  # Replace with your Congress.gov API key
BASE_URL = "https://api.congress.gov/v3"
BIOS_GUIDE_ID = "M001222"  # Max L. Miller's Bioguide ID
DB_PATH = "bills.db"

# Initialize the database
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bills (
            id INTEGER PRIMARY KEY,
            title TEXT,
            congress INTEGER,
            bill_type TEXT,
            bill_number TEXT,
            latest_action TEXT,
            url TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

@app.get("/update_bills")
def update_bills():
    """Fetch cosponsored bills and store them in the database."""
    url = f"{BASE_URL}/member/{BIOS_GUIDE_ID}/cosponsored-legislation?api_key={API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": f"API request failed with status {response.status_code}"}

    data = response.json().get("cosponsoredLegislation", [])

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for bill in data:
        cursor.execute(
            "INSERT OR IGNORE INTO bills (title, congress, bill_type, bill_number, latest_action, url) VALUES (?, ?, ?, ?, ?, ?)",
            (
                bill.get("title", "N/A"),
                bill.get("congress", "N/A"),
                bill.get("type", "N/A"),
                bill.get("number", "N/A"),
                bill.get("latestAction", {}).get("text", "N/A"),
                bill.get("url", "N/A")
            )
        )

    conn.commit()
    conn.close()

    return {"message": f"Updated {len(data)} bills"}

@app.get("/bills")
def get_bills():
    """Return stored bills from the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT title, congress, bill_type, bill_number, latest_action, url FROM bills")
    bills = cursor.fetchall()
    conn.close()

    return [{"title": b[0], "congress": b[1], "bill_type": b[2], "bill_number": b[3], "latest_action": b[4], "url": b[5]} for b in bills]
