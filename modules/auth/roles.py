
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Set

class Permission(Enum):
    """Define system permissions"""
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    APPROVE = "approve"
    ADMIN = "admin"

class Resource(Enum):
    """Define protected resources"""
    CUSTOMER = "customer"
    RISK = "risk"
    ALERT = "alert"
    TRANSACTION = "transaction"
    AUDIT = "audit"
    USER = "user"
    SYSTEM = "system"

@dataclass
class Role:
    """Role definition with permissions"""
    name: str
    description: str
    permissions: Dict[Resource, Set[Permission]]

# Define system roles
ROLES = {
    "admin": Role(
        name="Admin",
        description="Full system access",
        permissions={resource: set(Permission) for resource in Resource}
    ),
    
    "compliance_officer": Role(
        name="Compliance Officer",
        description="Compliance monitoring and approval",
        permissions={
            Resource.CUSTOMER: {Permission.READ, Permission.WRITE, Permission.APPROVE},
            Resource.RISK: {Permission.READ, Permission.WRITE, Permission.APPROVE},
            Resource.ALERT: {Permission.READ, Permission.WRITE, Permission.APPROVE},
            Resource.TRANSACTION: {Permission.READ, Permission.WRITE},
            Resource.AUDIT: {Permission.READ}
        }
    ),
    
    "kyc_analyst": Role(
        name="KYC Analyst",
        description="Customer onboarding and verification",
        permissions={
            Resource.CUSTOMER: {Permission.READ, Permission.WRITE},
            Resource.RISK: {Permission.READ},
            Resource.ALERT: {Permission.READ, Permission.WRITE},
            Resource.TRANSACTION: {Permission.READ}
        }
    ),
    
    "risk_officer": Role(
        name="Risk Officer",
        description="Risk assessment and monitoring",
        permissions={
            Resource.CUSTOMER: {Permission.READ},
            Resource.RISK: {Permission.READ, Permission.WRITE, Permission.APPROVE},
            Resource.ALERT: {Permission.READ, Permission.WRITE},
            Resource.TRANSACTION: {Permission.READ, Permission.WRITE}
        }
    ),
    
    "supervisor": Role(
        name="Supervisor",
        description="Team supervision and task management",
        permissions={
            Resource.CUSTOMER: {Permission.READ},
            Resource.RISK: {Permission.READ},
            Resource.ALERT: {Permission.READ, Permission.APPROVE},
            Resource.TRANSACTION: {Permission.READ},
            Resource.AUDIT: {Permission.READ}
        }
    )
}

def has_permission(role_name: str, resource: Resource, permission: Permission) -> bool:
    """Check if role has specific permission on resource"""
    if role_name not in ROLES:
        return False
    
    role = ROLES[role_name]
    if resource not in role.permissions:
        return False
        
    return permission in role.permissions[resource]

def get_role_permissions(role_name: str) -> Dict[Resource, Set[Permission]]:
    """Get all permissions for a role"""
    return ROLES[role_name].permissions if role_name in ROLES else {}

def check_access(user_role: str, resource: Resource, required_permission: Permission) -> bool:
    """Verify user access to resource"""
    try:
        return has_permission(user_role, resource, required_permission)
    except Exception:
        return False
