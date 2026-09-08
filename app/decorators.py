import logging
import re
from functools import wraps
from flask import request, session, abort

from app import logger

from app.route_permissions import TENANT_ADMIN_ROUTES, BASIC_USER_ROUTES


def is_permitted_route(request_path_parts, route):
    route_parts = route.split('/')
    if (len(route_parts) != len(request_path_parts)):
        return False
    else:
        for i in range(len(request_path_parts)):
            if request_path_parts[i] != route_parts[i]:
                if (route_parts[i] == '*'):
                    is_valid_route = True
                    break
                if (route_parts[i].startswith("<") and route_parts[i].endswith(">")):
                    dynamic_param = route_parts[i][1:-1]
                    if (dynamic_param == 'username'):
                        is_valid_route = request_path_parts[i] == session.get('username')
                        break
                    elif (dynamic_param == 'userId'):
                        is_valid_route = request_path_parts[i] == session.get('id')
                        break
                else:
                    is_valid_route = False
                    break
            else:
                is_valid_route = True
                continue

    return is_valid_route

def validate_route_access(func):
    """.env
    Only first level routing validation is implemented yet.
    e.g. in case of "/tenant/abcd" this decorator will only validate if route is "/tenant" and ignore part after second slash
    TODO: implement dynamic routing
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        # Perform any pre-processing tasks here
        if (not session.get('is_admin')):
            request_path_parts = request.path.split('/')
            is_valid_route = False

            if session.get('is_admin_tenant'):
                for route in TENANT_ADMIN_ROUTES:
                    is_valid_route = is_permitted_route(
                        request_path_parts, route)
                    if is_valid_route:
                        break
            else:
                for route in BASIC_USER_ROUTES:
                    is_valid_route = is_permitted_route(
                        request_path_parts, route)
                    if is_valid_route:
                        break

            if not is_valid_route:
                logger.Log("Forbidden access attempt to route '%s' by user: %s" % (
                request_path_parts, session.get('username')), logging.WARNING)
                abort(403)

                # Call the view function and get its response
        response = func(*args, **kwargs)

        # Perform any post-processing tasks here
        # print("Executing custom decorator after the view function")

        return response

    return wrapper
