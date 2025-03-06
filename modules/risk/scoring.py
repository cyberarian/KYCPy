from enum import Enum
from typing import Dict, List

class RiskFactor(Enum):
    """Risk factor categories"""
    OCCUPATION = "occupation"
    INCOME = "income"
    PEP_STATUS = "pep_status"
    ACTIVITY = "activity"
    TRANSACTION = "transaction"
    LOCATION = "location"
    DOCUMENTS = "documents"

RISK_WEIGHTS = {
    RiskFactor.OCCUPATION: 0.25,
    RiskFactor.INCOME: 0.10,
    RiskFactor.PEP_STATUS: 0.30,
    RiskFactor.ACTIVITY: 0.20,
    RiskFactor.TRANSACTION: 0.10,
    RiskFactor.LOCATION: 0.05,
    RiskFactor.DOCUMENTS: 0.05
}

OCCUPATION_RISK = {
    "Business Owner": 0.8,
    "Real Estate Developer": 0.8,
    "Politician": 1.0,
    "Lawyer": 0.6,
    "Doctor": 0.4,
    "Government Employee": 0.5,
    "Private Sector Employee": 0.3,
    "Teacher": 0.2,
    "Student": 0.1,
    "Retired": 0.2,
    "Military/Police": 0.4,
    "Other": 0.3
}

def calculate_risk_score(customer_data: Dict) -> float:
    """
    Calculate comprehensive risk score based on multiple factors
    
    Risk Score = Σ (Factor Score × Factor Weight)
    Where:
    - Each factor is normalized to 0-1 scale
    - Weights sum to 1.0
    - Final score is between 0-1
    """
    score = 0.0
    
    # Occupation risk (0.25)
    occupation_score = OCCUPATION_RISK.get(customer_data["occupation"], 0.3)
    score += occupation_score * RISK_WEIGHTS[RiskFactor.OCCUPATION]
    
    # Income level risk (0.10)
    income_score = {"Low": 0.2, "Medium": 0.5, "High": 0.8}.get(customer_data["income_level"], 0.5)
    score += income_score * RISK_WEIGHTS[RiskFactor.INCOME]
    
    # PEP status risk (0.30)
    pep_score = 1.0 if customer_data["pep_status"] else 0.0
    score += pep_score * RISK_WEIGHTS[RiskFactor.PEP_STATUS]
    
    # Suspicious activity risk (0.20)
    activity_score = 1.0 if customer_data["suspicious_activity"] else 0.0
    score += activity_score * RISK_WEIGHTS[RiskFactor.ACTIVITY]
    
    # Transaction profile risk (0.10)
    tx_profile = customer_data["transaction_profile"].lower()
    tx_score = 0.0
    if "high-value" in tx_profile:
        tx_score = 0.8
    elif "regular" in tx_profile:
        tx_score = 0.3
    score += tx_score * RISK_WEIGHTS[RiskFactor.TRANSACTION]
    
    return round(min(score, 1.0), 2)

def get_risk_category(score: float) -> str:
    """
    Determine risk category based on score
    
    Categories:
    - Low: 0.00 - 0.29
    - Medium: 0.30 - 0.69
    - High: 0.70 - 1.00
    """
    if score < 0.3:
        return "Low"
    elif score < 0.7:
        return "Medium"
    else:
        return "High"

def get_risk_factors(customer_data: Dict) -> Dict[str, float]:
    """Get individual risk factor scores"""
    return {
        "occupation": OCCUPATION_RISK.get(customer_data["occupation"], 0.3),
        "income": {"Low": 0.2, "Medium": 0.5, "High": 0.8}.get(customer_data["income_level"], 0.5),
        "pep_status": 1.0 if customer_data["pep_status"] else 0.0,
        "activity": 1.0 if customer_data["suspicious_activity"] else 0.0,
        "transaction": 0.8 if "high-value" in customer_data["transaction_profile"].lower() else 0.3
    }

def explain_risk_score(customer_data: Dict) -> List[str]:
    """Provide explanation for risk score components"""
    factors = []
    risk_scores = get_risk_factors(customer_data)
    
    if risk_scores["occupation"] >= 0.7:
        factors.append(f"High-risk occupation: {customer_data['occupation']}")
    
    if risk_scores["income"] >= 0.7:
        factors.append("High income level requires enhanced monitoring")
    
    if risk_scores["pep_status"]:
        factors.append("Politically Exposed Person (PEP)")
    
    if risk_scores["activity"]:
        factors.append("Suspicious activity detected")
    
    if risk_scores["transaction"] >= 0.7:
        factors.append("High-value transaction profile")
    
    return factors
