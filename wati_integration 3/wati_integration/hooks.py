app_name = "wati_integration"
app_title = "Wati Integration"
app_publisher = "Yasir Shaikh"
app_description = "Frappe app to send WhatsApp messages via WATI"
app_email = "drmohammeddanishshaikh@gmail.com"
app_license = "MIT"

# required_apps = []

# Document Events
# ---------------
doc_events = {
    "*": {
        "on_submit": "wati_integration.wati_integration.doctype.wati_message_rule.wati_message_rule.send_message_for_event",
        "after_insert": "wati_integration.wati_integration.doctype.wati_message_rule.wati_message_rule.send_message_for_event",
        "on_cancel": "wati_integration.wati_integration.doctype.wati_message_rule.wati_message_rule.send_message_for_event",
        "after_save": "wati_integration.wati_integration.doctype.wati_message_rule.wati_message_rule.send_message_for_event",
        "on_change": "wati_integration.wati_integration.doctype.wati_message_rule.wati_message_rule.send_message_for_event",
    }
}

# Scheduled Tasks
# ---------------
scheduler_events = {
    "cron": {
        "* * * * *": [
            "wati_integration.wati_integration.doctype.send_wati_message.send_wati_message.cron_job_for_schedule_message"
        ]
    }
}
