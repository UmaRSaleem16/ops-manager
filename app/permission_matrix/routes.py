import logging
import json

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask.json import jsonify
from flask_login import login_required

from app import utility
from app import logger, database
from app.permission_matrix.forms import PermissionMatrixForm
from app.decorators import validate_route_access

permission_matrix = Blueprint('permission_matrix', __name__)


@permission_matrix.route("/permission-matrix", methods=['GET', 'POST'])
@login_required
@validate_route_access
def get_permission_matrix():
    logger.Log('FUNCTION CALL: get_permission_matrix()', logging.DEBUG)
    permission_matrix = database.get_all_permission_matrix()
    form = PermissionMatrixForm()
    form.security_group.choices = database.get_all_groups_for_form()
    form.environment.choices = database.get_all_environments_for_form()
    form.datacenter.choices = database.get_all_datacenters_for_form()

    if request.method == 'POST':
        try:
            if(database.is_valid_permission(form.security_group.data, form.environment.data, form.datacenter.data)):
                database.create_permission_matrix(form.security_group.data, form.environment.data, form.datacenter.data)
                flash("Permission matrix added successfully!", 'success')
            else:
                flash("Permission matrix already exist.", 'danger')
        except Exception as e:
            logger.Log('Exception occurred while adding permission matrix: %s' %e, logging.ERROR)
            flash("Error occurred while adding permission matrix.", 'danger')

        return redirect(url_for('permission_matrix.get_permission_matrix'))

    if permission_matrix:
        groups = database.group_get_all()
        environments = database.environment_get_all()
        dataCenters = database.datacenter_get_all()

        for permission in permission_matrix:
            for group in groups:
                if permission['ops_man_ldap_group_id'] == group['id']:
                    permission['group'] = group
                    break
                else:
                    # If no matching group is found, set group to an empty object
                    permission['group'] = {}
            for environment in environments:
                if permission['ops_man_environment_id'] == environment['id']:
                    permission['environment'] = environment
                    break
                else:
                    # If no matching group is found, set group to an empty object
                    permission['environment'] = {}
            for dataCenter in dataCenters:
                if permission['ops_man_datacenter_id'] == dataCenter['id']:
                    permission['dataCenter'] = dataCenter
                    break
                else:
                    # If no matching group is found, set group to an empty object
                    permission['dataCenter'] = {}

    search_type, search_filter = utility.search_filter()
    
    return render_template('permission_matrix.html', title='Permission Matrix', permission_matrix=permission_matrix, form=form
    ,search_type=search_type, search_filter=search_filter)


@permission_matrix.route("/delete-permission/<id>", methods=['DELETE'])
@login_required
@validate_route_access
def delete_permission(id):
    logger.Log('FUNCTION CALL: delete_permission()', logging.DEBUG)

    try:
        database.permission_matrix_delete(id)
        flash("permission deleted successfully!", 'success')
        return json.dumps({'success': True}), 200
    except Exception as e:
        logger.Log('Error at delete_permission: %s' %e, logging.ERROR)
        return json.dumps({'success': False, 'error': repr(e)}), 500
