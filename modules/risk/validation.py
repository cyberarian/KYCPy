from datetime import datetime, timedelta
from typing import Dict, List, Optional

def validate_alert(alert_data: Dict) -> tuple[bool, List[str]]:
    """
    Validate alert data before saving
    Returns: (is_valid, error_messages)
    """
    errors = []
    
    # Required fields
    required_fields = [
        "id", "customer_id", "date", "type", "description",
        "status", "severity", "assigned_to"
    ]
    
    for field in required_fields:
        if not alert_data.get(field):
            errors.append(f"Missing required field: {field}")
    
    # Validate alert type
    valid_types = [
        "EDD Interview", "Document Request", "Compliance Referral",
        "Risk Escalation", "Suspicious Activity", "Document Expiry"
    ]
    if alert_data.get("type") and alert_data["type"] not in valid_types:
        errors.append(f"Invalid alert type. Must be one of: {', '.join(valid_types)}")
    
    # Validate status
    valid_statuses = [
        "New", "Scheduled", "In Progress", "Pending", 
        "Completed", "Closed", "Under Review"
    ]
    if alert_data.get("status") and alert_data["status"] not in valid_statuses:
        errors.append(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    # Validate severity
    valid_severities = ["Low", "Medium", "High", "Critical"]
    if alert_data.get("severity") and alert_data["severity"] not in valid_severities:
        errors.append(f"Invalid severity. Must be one of: {', '.join(valid_severities)}")
    
    # Validate dates
    try:
        if alert_data.get("date"):
            alert_date = datetime.strptime(alert_data["date"], "%Y-%m-%d")
            if alert_date > datetime.now():
                errors.append("Alert date cannot be in the future")
    except ValueError:
        errors.append("Invalid date format. Use YYYY-MM-DD")
    
    # Validate description length
    if alert_data.get("description") and len(alert_data["description"]) > 1000:
        errors.append("Description too long (max 1000 characters)")
    
    return len(errors) == 0, errors

def validate_edd_interview(alert_data: Dict) -> tuple[bool, List[str]]:
    """Specific validation for EDD interview alerts"""
    is_valid, errors = validate_alert(alert_data)
    
    if alert_data["type"] == "EDD Interview":
        # Extract interview date from description
        try:
            description_lines = alert_data["description"].split("\n")
            interview_line = next(line for line in description_lines if "scheduled for" in line)
            interview_date_str = interview_line.split("scheduled for")[1].split()[0]
            interview_date = datetime.strptime(interview_date_str, "%Y-%m-%d")
            
            # Validate interview date
            if interview_date < datetime.now():
                errors.append("Interview date cannot be in the past")
            if interview_date > datetime.now() + timedelta(days=30):
                errors.append("Interview cannot be scheduled more than 30 days in advance")
        except Exception:
            errors.append("Invalid interview date format in description")
    
    return len(errors) == 0, errors
