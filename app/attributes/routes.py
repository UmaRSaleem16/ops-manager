import logging
import json

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask.json import jsonify
from flask_login import login_required

from app import utility
from app import logger, database
from app.attributes.forms import TenantAttributeForm, UserAttributeSetupForm
from app.decorators import validate_route_access

attributes = Blueprint('attributes', __name__)


@attributes.route("/attributes", methods=['GET', 'POST'])
@login_required
@validate_route_access
def all_attributes():
    logger.Log('FUNCTION CALL: all_tenants()', logging.DEBUG)
    tenant_attributes = database.tenant_attributes_types_get_all()
    user_attributes = database.user_attributes_types_get_all()
    tenant_form = TenantAttributeForm()
    user_form = UserAttributeSetupForm()

    if request.method == 'POST':
        if request.form['attribute_type'] == "tenant":
            if database.check_if_tenant_attribute_type_already_exists(tenant_form.name.data):
                flash('Attribute name already exists. ', 'info')
                return redirect(url_for('attributes.all_attributes'))
            if tenant_form.validate_on_submit():
                database.tenant_attributes_type_create(tenant_form.name.data, tenant_form.limit.data)
                flash('Attributed created for %s!' % (tenant_form.name.data), 'success')
                return redirect(url_for('attributes.all_attributes'))
            else:
                for key, value in tenant_form.errors.items():
                    flash(f'An error occurred for {str(key)}, {str(value[0])}', 'error')
                return redirect(url_for('attributes.all_attributes'))
        if request.form['attribute_type'] == "user":
            if user_form.validate_on_submit():
                if database.check_if_user_attribute_type_already_exists(user_form.name.data):
                    flash('Attribute name already exists. ', 'info')
                    return redirect(url_for('attributes.all_attributes'))
                database.user_attributes_type_create(user_form.name.data, user_form.limit.data)
                flash('User Attribute created for %s!' % (user_form.name.data), 'success')
                return redirect(url_for('attributes.all_attributes'))
            else:
                for key, value in user_form.errors.items():
                    flash(f'An error occurred for {str(key)}, {str(value[0])}', 'error')
                return redirect(url_for('attributes.all_attributes'))

    search_type, search_filter = utility.search_filter()
    return render_template('attributes_setup.html', title='Attributes',
                            user_attributes=user_attributes,tenant_attributes=tenant_attributes,
                            tenant_form=tenant_form,user_form=user_form,
                            search_type=search_type, search_filter=search_filter)


@attributes.route("/delete_tenant_attribute_type/<int:id>", methods=['DELETE'])
@login_required
@validate_route_access
def delete_tenant_attribute_type(id):
    logger.Log('FUNCTION CALL: delete_tenant_attribute_type()', logging.DEBUG)
    try:
        if database.check_if_tenant_attribute_type_already_exists_using_id(id):
            database.delete_tenant_attribute_type(id=id)
            flash('Attribute type deleted successfully!', 'success')
            return jsonify({'success': True}), 200
        flash('Attribute type not found.', 'error')
        return jsonify({'success': False, 'error': 'Attribute type not found.'}), 400
    except Exception as e:
        logger.Log('Error at delete_tenant_attribute_type: %s' %e, logging.ERROR)
        return json.dumps({'success': False, 'error': repr(e)}), 500

@attributes.route("/edit-tenant-attribute-type", methods=['POST'])
@login_required
@validate_route_access
def edit_tenant_attribute_type():
    logger.Log('FUNCTION CALL: edit_tenant_attribute_type()', logging.DEBUG)

    try:
        data = dict(request.json)
        database.tenant_attributes_type_update(data.get('attribute_id'),data.get('limit'),data.get('attribute_name'))
        flash("Tenant attribute Update.", 'success')
        return json.dumps({'success': True}), 200
    except Exception as e:
        logger.Log('Error at edit_tenant_attribute_type: %s' %e, logging.ERROR)
        return json.dumps({'success': False, 'error': repr(e)}), 500

@attributes.route("/edit-user-attribute-type", methods=['POST'])
@login_required
@validate_route_access
def edit_user_attribute_type():
    logger.Log('FUNCTION CALL: edit_user_attribute()', logging.DEBUG)

    try:
        data = dict(request.json)
        database.user_attributes_type_update(data.get('attribute_id'),data.get('limit'),data.get('attribute_name') )
        flash("User attribute updated.", 'success')
        return json.dumps({'success': True}), 200
    except Exception as e:
        logger.Log('Error at edit_user_attribute: %s' %e, logging.ERROR)
        return json.dumps({'success': False, 'error': repr(e)}), 500


@attributes.route("/delete_user_attribute_setup_type/<int:id>", methods=['DELETE'])
@login_required
@validate_route_access
def delete_user_attribute_type(id):
    logger.Log('FUNCTION CALL: delete_user_attribute_type()', logging.DEBUG)
    if database.check_if_user_attribute_type_already_exists_using_id(id):
        database.delete_user_attribute_type(id=id)
        flash('Attribute type deleted successfully!', 'success')
        return jsonify({'success': True}), 200
    flash('Attribute type not found.', 'error')
    return jsonify({'not found': False}), 400
