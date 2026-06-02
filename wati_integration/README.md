# WATI Integration for Frappe

Send WhatsApp messages via [WATI](https://wati.io) from any Frappe/ERPNext document.

**Compatible with Frappe / ERPNext v15 and v16.**

> Originally created for v14 by Bhavesh Maheshwari. Ported and maintained for v15/v16 by Yasir Shaikh.

## Features

- Send WhatsApp template messages automatically on document events (New, Save, Submit, Cancel, Value Change)
- Rule-based message routing with conditions
- Bulk send to All Customers, Suppliers, Employees, Leads, or custom Groups
- Schedule messages for a future date/time
- Full message log with request/response details

## Requirements

| | Frappe v15 | Frappe v16 |
|---|---|---|
| Python | 3.10 – 3.12 | 3.14+ |
| Node.js | 18+ | 24+ |

## Installation

```bash
cd /path/to/frappe-bench

# Fetch the app
bench get-app https://github.com/YasirShaikh/wati_integration.git

# Install on your site
bench --site your-site.com install-app wati_integration

# Apply schema
bench --site your-site.com migrate
```

For a specific branch:

```bash
bench get-app --branch main https://github.com/YasirShaikh/wati_integration.git
```

## Configuration

1. Go to **Wati Integration → Wati Setting**
2. Enter your WATI **API URL** (e.g. `https://live-server-XXXXX.wati.io`)
3. Enter your **WhatsApp Number** (registered in WATI)
4. Enter your **Bearer Token** (from the WATI API panel)

## Usage

### Message Templates
Create a **Message Template** matching the template name approved in your WATI account.
Use `{variable_name}` placeholders in the message — they are auto-detected into the
**Template Variables** field.

### Wati Message Rule
Create a **Wati Message Rule** to auto-send messages on document events:

- Select the **Document Type** (e.g. Sales Order)
- Pick the **Mobile No Field** from that doctype
- Choose the trigger: New / Save / Submit / Cancel / Value Change
- Optionally add **Conditions** (e.g. `doc.status == "Open"`)
- Map template variables to document fields

### Send Wati Message (Bulk)
Use **Send Wati Message** to broadcast to All Customers, Suppliers, Employees, Leads,
or a custom **Wati Group** — immediately or on a schedule.

## Uninstall

```bash
bench --site your-site.com uninstall-app wati_integration
```

## License

MIT — Copyright (c) 2024, Yasir Shaikh. See [license.txt](license.txt).
