"""Security owner: replace demo identity selection with real authentication.

A User must eventually be constructed from a verified session, never message text.
"""
from shared.models import User

DEMO_USERS = (User("C001", "Demo Customer One"), User("C002", "Demo Customer Two"))
