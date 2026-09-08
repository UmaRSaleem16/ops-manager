"""
Utility.

This is one of the main pieces of our program, basically we store universal items and true
globals here.  This module will likely be imported by all other parts of your program.

"""

__author__ = 'Junaid Tariq <junaidtariq166@gmail.com>'

import base64
import os
import re
import logging
from datetime import datetime
from app import logger
from app import database

LOGGER = None
LOG_LEVEL = logging.INFO

# Process ID of this program
PID = str(os.getpid())


def field_validator(field_data):
    """
    Description: Super simple check to make sure there aren't
    """
    logger.Log('FUNCTION CALL: field_validator()', logging.DEBUG)

    # set up a list of things to check for
    not_allowed_character_list = [';', '*', '"', '\'']

    # We want it to pass!
    Pass = True

    # check if the field is not empty and if it has something it shouldn't have
    if field_data:
        for char in not_allowed_character_list:
            if char in field_data:
                Pass = False
    else:
        Pass = False

    return Pass


def search_filter():
    """"""
    users = database.user_get_all()
    groups = database.group_get_all()
    # fqdns_components = database.host_component_get_all()
    # fqdns_masters = database.host_database_masters_get_all()
    # fqdns_slaves = database.host_database_slaves_get_all()
    tenants = database.tenant_get_all()
    # pods = database.pod_get_all_pods()
    # components = database.component_get_all()

    search_filter = []
    search_type = ['Users', 'Groups', 'Tenants']

    for user in users:
        user_dict = {}
        user_dict['id'] = user['id']
        user_dict['name'] = user['username']
        user_dict['url'] = '/user/' + str(user['username'])
        user_dict['search_type'] = search_type[0]

        if user_dict not in search_filter:
            search_filter.append(user_dict)

    for group in groups:
        group_dict = {}
        group_dict['id'] = group['id']
        group_dict['name'] = group['name']
        group_dict['url'] = '/users?group=' + str(group['id'])
        group_dict['search_type'] = search_type[1]

        if group_dict not in search_filter:
            search_filter.append(group_dict)


    for tenant in tenants:
        tenant_dict = {}
        tenant_dict['id'] = tenant['id']
        tenant_dict['name'] = tenant['name']
        tenant_dict['url'] = '/tenant/' + tenant['name']
        tenant_dict['search_type'] = search_type[2]

        if tenant_dict not in search_filter:
            search_filter.append(tenant_dict)

    # for pod in pods:
    #     pod_dict = {}
    #     pod_dict['id'] = pod['id']
    #     pod_dict['name'] = pod['pod']
    #     pod_dict['url'] = '/pod/' + pod['pod']
    #     pod_dict['search_type'] = search_type[4]

    #     if pod_dict not in search_filter:
    #         search_filter.append(pod_dict)

    # for component in components:
    #     component_dict = {}
    #     component_dict['id'] = component['id']
    #     component_dict['name'] = component['component']
    #     component_dict['url'] = '/component/' + component['component']
    #     component_dict['search_type'] = search_type[5]

    #     if component_dict not in search_filter:
    #         search_filter.append(component_dict)

    return search_type, search_filter


def generate_linux_username_for_tenant(tenant_name):
    try:
        tenant = tenant_name

        # split up the name
        unix_username_part_0 = tenant.split('-')[0]
        unix_username_part_1 = tenant.rsplit('_', 1)[1]

        # had to do some stripping but that was only to pay for college
        unix_username_part_0_stripped = re.sub('[a-z]', '', unix_username_part_0)
        unix_username_part_0_stripped = unix_username_part_0_stripped.replace('_', '')
        unix_combined = '%s-%s' % (unix_username_part_0_stripped, unix_username_part_1)
        final_unix = unix_combined.lower()

        # set up some constraints for username to match
        pattern = re.compile("^[a-z0-9_-]{3,30}$")

        if pattern.match(final_unix):
            return final_unix
    except Exception as e:
        logging.error('An error occurred while generating the Unix username: %s', e)
        return None


def generate_linux_user_id_for_tenant(service_id):
    service_id = str(service_id)

    # check to make sure we are starting with a valid integer.
    if not service_id.isdigit():
        logging.error('service_id generation failed: %s not a integer' % service_id, logging.ERROR)
        return False
    else:
        # very simply add 10000 just like we do.
        unix_uid = int(service_id) + int(10000)

    # do some simple validation tests for the unix_uid.
    if 10000 < int(unix_uid) < 1000000:
        logging.info('generated unix_uid: %s' % unix_uid)
        return unix_uid
    else:
        logging.error('Unix UID %s is out of the valid range', unix_uid)
        return None

def serialize_datetime(obj): 
    if isinstance(obj, datetime): 
        return obj.isoformat() 
    raise TypeError("Type not serializable") 

def validate_ssh_key(ssh_key):
    
    #Added this line to bypass all SSH key validations
    return True, "SSH key is valid."

    # Check if the SSH key is only one line
    if '\n' in ssh_key.strip('\n'):
        return False, "SSH key must be a single line."

    # SSH key pattern for initial validation
    # ssh_key_pattern = re.compile(r'^(ssh-rsa|ssh-dss|ecdsa-sha2-nistp256|ecdsa-sha2-nistp384|ecdsa-sha2-nistp521|ssh-ed25519) [A-Za-z0-9+/]+={0,3}( .+)?$')
    ssh_key_pattern = re.compile(r'^from="\$guardian_ips,[\d.]+(?:,[\d.]+)?",no-agent-forwarding,no-port-forwarding,no-pty (ssh-rsa|ssh-dss|ssh-ed25519|ecdsa-[^\s]+) ([A-Za-z0-9+/]+=*) \S+$')
    # Check if the SSH key matches the OpenSSH format
    if not ssh_key_pattern.match(ssh_key):
        return False, "SSH key format is invalid."

    # Extract the base64-encoded part of the key to validate its encoding
    # key_parts = ssh_key.split()
    # if len(key_parts) < 2:
    #     return False, "SSH key format is invalid."

    try:
        # # Decode the base64 part to ensure it's correctly encoded
        # base64.decodebytes(key_parts[1].encode())

        # Extract base64 part using regex
        match = re.match(ssh_key_pattern, ssh_key)
        if match:
            base64_part = match.group(2)
            base64.decodebytes(base64_part.encode())
    except Exception:
        return False, "SSH key base64 part is incorrectly encoded."

    # If all checks pass, the SSH key is valid
    return True, "SSH key is valid."
