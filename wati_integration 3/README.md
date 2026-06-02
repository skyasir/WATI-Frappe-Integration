# WATI Integration for Frappe

Send WhatsApp messages via [WATI](https://wati.io) from any Frappe/ERPNext document.

**Compatible with Frappe v15 and v16.**

## Features

- Send WhatsApp template messages automatically on document events (New, Save, Submit, Cancel, Value Change)
- Rule-based message routing with conditions
- Bulk send to All Customers, Suppliers, Employees, Leads, or custom Groups
- Schedule messages for a future date/time
- Full message log with request/response details

## Installation

```bash
cd /path/to/frappe-bench
bench get-app https://github.com/YasirShaikh/wati_integration.git
bench --site your-site.com install-app wati_integration
bench migrate
```

## Configuration

1. Go to **Wati Integration → Wati Setting**
2. Enter your WATI **API URL** (e.g. `https://live-server-XXXXX.wati.io`)
3. Enter your **WhatsApp Number** (registered in WATI)
4. Enter your **Bearer Token** (from WATI API panel)

## Usage

### Message Templates
Create a **Message Template** matching the template name approved in your WATI account. Use `{variable_name}` placeholders — they are auto-detected.

### Message Rules
Create a **Wati Message Rule** to auto-send messages on document events:
- Select the **Document Type** (e.g. Sales Order)
- Pick the **Mobile No Field** from that doctype
- Choose the trigger: New / Save / Submit / Cancel / Value Change
- Optionally add **Conditions** (e.g. `doc.status == "Open"`)
- Map template variables to document fields

### Send Message (Bulk)
Use **Send Wati Message** to broadcast to All Customers, Suppliers, Employees, Leads, or a custom Group — immediately or on a schedule.

## License

MIT — Copyright (c) 2024, Yasir Shaikh
