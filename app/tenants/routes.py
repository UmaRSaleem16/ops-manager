import logging
import json
from flask import Blueprint, render_template, request, session, redirect, url_for, flash, jsonify
from flask_login import login_required

from app import utility
from app import logger, database
from app.database import validate_tenant_on_creation
from app.tenants.forms import TenantForm, TenantAttributeValueForm, TenantAttributeSSHValueForm
from app.utility import generate_linux_username_for_tenant, \
    generate_linux_user_id_for_tenant, validate_ssh_key, search_filter  # , generate_linux_user_id_for_tenant
from app.decorators import validate_route_access

tenants = Blueprint('tenants', __name__)


@tenants.route("/get-tenants")
@login_required
@validate_route_access
def get_ajax_tenants():
    logger.Log('FUNCTION CALL: all_tenants()', logging.DEBUG)

    try:
        tenants = database.tenant_get_all()

        draw = int(request.args.get('draw', 0))
        start = int(request.args.get('start', 0))
        length = int(request.args.get('length', 10))
        search_value = request.args.get('search[value]', '')
        order_column_index = int(request.args.get('order[0][column]', 0))
        order_direction = request.args.get('order[0][dir]', 'asc')  

        filtered_data = [record for record in tenants if search_value.lower() in str(record).lower()]
        sorted_data = sorted(filtered_data, key=lambda x: x.get('name'), reverse=(order_direction == 'desc'))
        # Apply pagination
        paginated_data = sorted_data[start:start + length]

        # Prepare response
        response = {
            "draw": draw,
            "recordsTotal": len(tenants),
            "recordsFiltered": len(filtered_data),
            "data": paginated_data
        }
    except Exception as e:
        logger.Log('Error while getting tenants: %s' %e, logging.ERROR)
        return jsonify({'success': False, 'error': repr(e)}), 500

    return jsonify(response)


@tenants.route("/tenants", methods=['GET', 'POST'])
@login_required
@validate_route_access
def all_tenants():
    logger.Log('FUNCTION CALL: all_tenants()', logging.DEBUG)
    tenants = database.tenant_get_all()
    form = TenantForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            tenant_name = form.name.data
            service_id = form.service_id.data
            linux_username = generate_linux_username_for_tenant(tenant_name=tenant_name)
            linux_user_id = generate_linux_user_id_for_tenant(service_id=service_id)
            tenant_not_exists, msg = validate_tenant_on_creation(service_id=service_id,
                                                             linux_uid=linux_user_id,
                                                             linux_username=linux_username,
                                                             name=tenant_name)
            if tenant_not_exists:
                database.tenant_create(form.service_id.data,
                                       form.name.data,
                                       linux_username,
                                       linux_user_id,
                                       is_disabled=1)
                flash('Tenant created for %s!' % (form.name.data), 'success')
                return redirect(url_for('tenants.all_tenants'))
            else:
                flash(msg, 'error')
                return redirect(url_for('tenants.all_tenants'))
        else:
            for key, value in form.errors.items():
                flash(f'An error occurred for {str(key)}, {str(value[0])}', 'danger')
            return redirect(url_for('tenants.all_tenants'))
    search_type, search_filter = utility.search_filter()

    return render_template('tenants.html', title='Tenants', form=form, #tenants=tenants,
                           search_filter=search_filter,
                           search_type=search_type)


def is_tenant_limit_reached(tenant_id, attribute_id):
    logger.Log('FUNCTION CALL: validate_tenant_attribute_limit()', logging.DEBUG)
    tenant_attribute_count = database.get_tenant_attribute_count(tenant_id,attribute_id)
    tenant_attributes_type = database.get_tenant_attribute_type_by_id(attribute_id)

    # print("limit ====>>> ", limit)
    # print("tenant_attribute ===>>> ", tenant_attribute)
    if tenant_attributes_type:
        if tenant_attribute_count['tenant_attribute_count'] >= tenant_attributes_type['limit']:
            return True
    return False


@tenants.route("/edit-tenant-attribute", methods=['POST'])
@login_required
@validate_route_access
def edit_tenant_attribute():
    logger.Log("FUNCTION CALL: edit_tenant_attribute()", logging.DEBUG)
    # if not session['site_admin']:
    #     if (int(session['id']) != int(id)):
    #         abort(403)

    data = dict(request.json)
    try:
        value = data.get('value') if(data.get('value').strip()) else 'NULL'
        tenant_attribute_detail = database.get_tenant_attribute_by_id(data.get('id'))
        is_valid = True
        if(tenant_attribute_detail and tenant_attribute_detail.get('attribute_name') == 'ssh_key'):
            is_valid, msg = validate_ssh_key(ssh_key=value)
        
        if is_valid:
            database.update_tenant_attributes_by_id(data.get('id'), value)
            flash("Value updated successfully!", 'success')
            return json.dumps({'success': True}), 200
        else:
            # flash("invalid attribute value provided", 'success')
            return json.dumps({'success': False, 'error': msg}), 200

    except Exception as e:
        logger.Log('Error while updating value: %s' %e, logging.ERROR)
        return json.dumps({'success': False, 'error': repr(e)}), 500


@tenants.route("/delete-tenant-attribute/<id>", methods=['DELETE'])
@login_required
@validate_route_access
def delete_tenant_attribute(id):
    logger.Log("FUNCTION CALL: delete_tenant_attribute()", logging.DEBUG)

    try:
        database.delete_tenant_attributes_by_id(id)

        flash("Tenant Attribute deleted successfully!", 'success')
        return json.dumps({'success': True}), 200

    except Exception as e:
        logger.Log('Error while deleting attribute: %s' %e, logging.ERROR)
        flash("Error deleting attribute.", 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500

@tenants.route("/tenant/<name>", methods=['GET', 'POST'])
@login_required
@validate_route_access
def tenant(name):
    logger.Log('FUNCTION CALL: tenant()', logging.DEBUG)
    form = TenantAttributeSSHValueForm()
    other_form = TenantAttributeValueForm()
    form.tenant_attribute_type.choices = database.get_ssh_tenant_attribute_types_for_form()
    other_form.tenant_attribute_type.choices = database.get_all_tenant_attribute_types_for_form()
    tenant = database.get_tenant(name)[0]
    tenant_attributes = database.get_tenant_attributes(tenant_id=tenant['id'])
    if(tenant_attributes and len(tenant_attributes) > 0):
        ssh_attr = database.get_ssh_attribute_type_id()
        if(ssh_attr):
            ssh_attribute_id = ssh_attr['id']
        else:
            ssh_attribute_id = 0

        ssh_attributes = list(filter(lambda attr: attr['ops_man_tenant_attribute_type_id'] == ssh_attribute_id, tenant_attributes))
        other_attributes = list(filter(lambda attr: attr['ops_man_tenant_attribute_type_id'] != ssh_attribute_id, tenant_attributes))
    else:
        ssh_attributes = []
        other_attributes = []

    # tenant_attributes = database.get_tenant_attributes(tenant_id=tenant['id'])
    if request.method == 'POST':
        #Start Add SSH KEY
        if(int(request.form.get('is_ssh_key')) > 0):
            form.tenant_attribute_type.data = int(form.tenant_attribute_type.data)
            if form.validate_on_submit():
                if is_tenant_limit_reached(tenant['id'],form.tenant_attribute_type.data):
                    flash('Limit reached for this attribute, you can not add more attribute of this type.', 'danger')
                    return redirect(url_for('tenants.tenant', name=name))
                
                is_ssh_valid, msg = validate_ssh_key(ssh_key=form.value.data)
                if is_ssh_valid:
                    database.tenant_attribute_create(tenant['id'], form.tenant_attribute_type.data, form.value.data)
                    flash('Tenant Attribute created.', 'success')
                    return redirect(url_for('tenants.tenant', name=name))
                flash(msg, 'danger')
                return redirect(url_for('tenants.tenant', name=name))
            else:
                for key, value in form.errors.items():
                    flash(f'An error occurred while adding SSH Key: {str(key)}, {str(value[0])}', 'danger')
                return redirect(url_for('tenants.tenant', name=name))
        else:
            other_form.tenant_attribute_type.data = int(other_form.tenant_attribute_type.data)
            if other_form.validate_on_submit():
                if is_tenant_limit_reached(tenant['id'],other_form.tenant_attribute_type.data):
                    flash('Limit reached for this attribute, you can not add more attribute of this type.', 'danger')
                    return redirect(url_for('tenants.tenant', name=name))
                
                database.tenant_attribute_create(tenant['id'], form.tenant_attribute_type.data, form.value.data)
                flash('Tenant Attribute created.', 'success')
                return redirect(url_for('tenants.tenant', name=name))
            else:
                for key, value in other_form.errors.items():
                    flash(f'An error occurred for {str(key)}, {str(value[0])}', 'danger')
                return redirect(url_for('tenants.tenant', name=name))

    search_type, search_filter = utility.search_filter()
    return render_template('tenant.html', form=form, other_form=other_form,
                           ssh_attributes=ssh_attributes, other_attributes=other_attributes, title="Tenants", tenant=tenant,
                           search_type=search_type,
                        search_filter=search_filter)


@tenants.route("/tenant-set-is-disable", methods=['POST'])
@login_required
@validate_route_access
def tenant_set_active():
    logger.Log("FUNCTION CALL: tenant_set_active()", logging.DEBUG)

    data = dict(request.json)
    try:
        is_disabled = data.get('is_disable') if(data.get('is_disable')) else 0
        database.Update_tenant_is_disable(data.get('id'), is_disabled)

        if int(is_disabled) > 0:
            flash("Tenant marked as active.")
        else:
            flash("Tenant marked as in-active.")
        
        return json.dumps({'success': True}), 200

    except Exception as e:
        logger.Log('Error while updating tenant status : %s' %e, logging.ERROR)
        flash("Error updating tenant status.", 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500


@tenants.route("/tenant-set-is-sftp/<tenant_id>", methods=['POST'])
@login_required
@validate_route_access
def tenant_set_sftp(tenant_id):
    logger.Log("FUNCTION CALL: group_set_admin()", logging.DEBUG)

    data = dict(request.json)
    try:
        is_sftp = data.get('is_sftp') if(data.get('is_sftp')) else 0
        database.Update_tenant_sftp_status(tenant_id, is_sftp)
        flash("Tenant SFTP status updated.")
        
        return json.dumps({'success': True}), 200

    except Exception as e:
        logger.Log('Error while updating tenant SFTP status : %s' %e, logging.ERROR)
        flash("Error updating tenant SFTP status.", 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500