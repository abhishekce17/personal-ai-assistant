from enum import Enum


class ConversationType(Enum):
    STREAM = "Stream"
    NON_STREAM = "NonStream"

class IdentityScope(Enum):
    PERSONAL = "Personal"
    ORGANIZATION = "Organization"
    ENTERPRISE = "Enterprise"
    OTHER = "Other"

class ArtifactFormat(Enum):
    JSON = "application/json"
    MARKDOWN = "text/markdown"
    TEXT = "text/plain"
    HTML = "text/html"