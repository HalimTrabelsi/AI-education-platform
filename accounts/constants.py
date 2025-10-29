ROLE_CHOICES = [
    ("student", "Etudiant"),
    ("teacher", "Enseignant"),
    ("moderator", "Moderateur"),
    ("admin", "Administrateur"),
]

ROLE_LABELS = {value: label for value, label in ROLE_CHOICES}

DEFAULT_DASHBOARD_ROUTE = "dashboards:student"

ROLE_DASHBOARD_ROUTE = {
    "student": "dashboards:student",
    "teacher": "dashboards:teacher",
    "moderator": "dashboards:moderator",
    "admin": "dashboards:admin",
}


def get_dashboard_route(role: str | None) -> str:
    """Return the named URL for the dashboard associated with a role."""
    return ROLE_DASHBOARD_ROUTE.get(role or "", DEFAULT_DASHBOARD_ROUTE)
