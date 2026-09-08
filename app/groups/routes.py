import logging
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required

from app import logger, database
from app import utility
from app.groups.forms import GroupForm
from app.decorators import validate_route_access

groups = Blueprint('groups', __name__)


@groups.route("/groups", methods=['GET', 'POST'])
@login_required
@validate_route_access
def groups_all():
    logger.Log('FUNCTION CALL: all_tenants()', logging.DEBUG)
    form = GroupForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            database.group_create(form.name.data, form.linux_group_id.data, form.linux_group_name.data, form.is_admin.data, form.is_admin_tenant.data)
            flash('Group created for %s!' % (form.name.data), 'success')
            return redirect(url_for('groups.groups_all'))
        else:
            for key, value in form.errors.items():
                flash(f'{str(key)}, {str(value[0])}', 'error')
            return redirect(url_for('groups.groups_all'))
    groups = database.group_get_all()

    search_type, search_filter = utility.search_filter()

    return render_template('groups.html', title='Groups',
                           groups=groups, form=form,
                           search_type=search_type,
                          search_filter=search_filter)


@groups.route("/group-set-admin", methods=['POST'])
@login_required
@validate_route_access
def group_set_admin():
    logger.Log("FUNCTION CALL: group_set_admin()", logging.DEBUG)
    # if not session['site_admin']:
    #     if (int(session['id']) != int(id)):
    #         abort(403)

    data = dict(request.json)
    try:
        is_admin = data.get('is_admin') if(data.get('is_admin')) else 0
        database.Update_group_privilege(data.get('id'), is_admin)

        flash("user privilege updated successfully", 'success')
        return json.dumps({'success': True}), 200

    except Exception as e:
        logger.Log('Error while updating user privilege : %s' %e, logging.ERROR)
        flash("Error updating user privilege.", 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500

@groups.route("/group-set-tenant-admin", methods=['POST'])
@login_required
@validate_route_access
def group_set_tenant_admin():
    logger.Log("FUNCTION CALL: group_set_tenant_admin()", logging.DEBUG)
    # if not session['site_admin']:
    #     if (int(session['id']) != int(id)):
    #         abort(403)

    data = dict(request.json)
    try:
        is_admin_tenant = data.get('is_admin_tenant') if(data.get('is_admin_tenant')) else 0
        database.Update_group_is_admin_tenant(data.get('id'), is_admin_tenant)

        flash("user privilege updated successfully", 'success')
        return json.dumps({'success': True}), 200

    except Exception as e:
        logger.Log('Error while updating user privilege : %s' %e, logging.ERROR)
        flash("Error updating user privilege.", 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500



@groups.route("/group-members/<id>", methods=['GET'])
@login_required
@validate_route_access
def groups_by_id(id):
    logger.Log('FUNCTION CALL: groups_by_id()', logging.DEBUG)
    try:
        group = database.group_get_by_id(id)
        users = database.users_get_by_group_id(id)
        if(len(users)> 0):
            user_attributes = database.get_all_user_attribute_by_group_id(id)           
            
            # group['users'] = users
            #To Get User Attributes along with users
            group['users'] = {user['id']: {**user, 'attributes': []} for user in users}
            for attribute in user_attributes:
                user_id = attribute['user_id']
                if user_id in group['users']:
                    group['users'][user_id]['attributes'].append(attribute)
        else:
            group['users'] = []
        
        return json.dumps({'success': True, 'data': group}, default=utility.serialize_datetime), 200
    except Exception as e:
        logger.Log('Exception at groups_by_id: %s' %e, logging.ERROR)
        return json.dumps({'success': False, 'error': repr(e)}), 500
    
   

@groups.route("/group/<name>", methods=['GET'])
@login_required
@validate_route_access
def groups_by_name(name):
    logger.Log('FUNCTION CALL: all_tenants()', logging.DEBUG)
    
    groups = database.group_get_by_name(name)

    search_type, search_filter = utility.search_filter()
    
    return render_template('group.html', title='Groups',
                           groups=groups, form=form,search_type=search_type, search_filter=search_filter)

@groups.route("/delete-group/<id>", methods=['DELETE'])
@login_required
@validate_route_access
def delete_group(id):
    logger.Log('FUNCTION CALL: delete_group()', logging.DEBUG)

    try:
        database.group_delete(id)
        return json.dumps({'success': True}), 200
    except Exception as e:
        logger.Log('Error at delete_user_attribute_type: %s' %e, logging.ERROR)
        return json.dumps({'success': False, 'error': repr(e)}), 500


@groups.route("/edit-group", methods=['POST'])
@login_required
@validate_route_access
def edit_group():
    logger.Log("FUNCTION CALL: edit_group()", logging.DEBUG)
    # if not session['site_admin']:
    #     if (int(session['id']) != int(id)):
    #         abort(403)

    data = dict(request.json)
    try:
        group_name = data.get('name') if(data.get('name')) else 'NULL'
        linux_group_name = data.get('linux_group_name') if(data.get('linux_group_name')) else 'NULL'
        linux_group_id = data.get('linux_group_id') if(data.get('linux_group_id')) else 'NULL'
        database.group_update(data.get('id'), group_name, linux_group_name, linux_group_id)

        flash("Group edited successfully", 'success')
        return json.dumps({'success': True}), 200

    except Exception as e:
        logger.Log('Error while editing group: %s' %e, logging.ERROR)
        flash("Error editing group.", 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500