"""Helpers for identifying the currently logged-in admin.

Auth is HTTP Basic (see ``dash_auth.BasicAuth`` in ``app.py``), so the browser
resends credentials on every request -- including Dash callback POSTs. That lets
any protected callback learn who is acting via ``flask.request.authorization``,
which we use to stamp an ``author`` on the events/badges they create.
"""
import flask


def current_username():
    """Return the logged-in admin's username, or None if unauthenticated.

    Safe to call outside a request context (returns None) so imports and unit
    use don't blow up.
    """
    try:
        auth = flask.request.authorization
    except RuntimeError:
        return None
    if auth and auth.username:
        return auth.username
    return None
