from flask import session
from dash import html

ACCESS_FORBIDDEN_COMPONENT = html.Div('403 - Access Forbidden')

def enforce_roles(allowed_roles, access_forbidden=ACCESS_FORBIDDEN_COMPONENT):
    '''Decorator to check user roles against page's allowed_roles'''
    def decorator(func):
        def wrapped_layout(*args, **kwargs):
            user_roles = session.get('user', {}).get('groups', [])
            if allowed_roles and not set(allowed_roles).intersection(user_roles):
                return access_forbidden

            return func(*args, **kwargs)        
        return wrapped_layout
    return decorator
