from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    OPERATOR = "operator"


class TicketStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class TicketCategory(str, Enum):
    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AgentType(str, Enum):
    ORCHESTRATOR = "orchestrator_agent"
    BILLING_AGENT = "billing_agent"
    TECH_AGENT = "tech_agent"
    ESCALATION_AGENT = "escalation_agent"


class AgentTaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class EscalationStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    RESOLVED = "resolved"


class EventType(str, Enum):
    CREATED = "created"
    ROUTED = "routed"
    AGENT_STARTED = "agent_started"
    AGENT_RESOLVED = "agent_resolved"
    ESCALATED = "escalated"
    ASSIGNED = "assigned"
    CLOSED = "closed"
