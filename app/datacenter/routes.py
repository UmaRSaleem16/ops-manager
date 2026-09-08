import logging
import json

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask.json import jsonify
from flask_login import login_required

from app import utility
from app import logger, database
from app.datacenter.forms import DataCentersForm, EnvironmentsForm
from app.decorators import validate_route_access

datacenters = Blueprint('datacenters', __name__)


@datacenters.route("/datacenters", methods=['GET', 'POST'])
@login_required
@validate_route_access
def datacenters_environments():
    logger.Log('FUNCTION CALL: all_tenants()', logging.DEBUG)
    datacenter_form = DataCentersForm()
    datacenter_form.type.data = 'dc'
    environment_form = EnvironmentsForm()
    environment_form.type.data = 'env'
    if request.method == 'POST':
        if request.form['type'] == "env":
            if database.check_if_environment_already_exists_using_name(environment_form.name.data):
                flash('Environment already exists', 'warning')
                return redirect(url_for('datacenters.datacenters_environments'))
            if environment_form.validate_on_submit():
                database.environment_create(environment_form.name.data)
                flash('Environment created for %s!' % (environment_form.name.data), 'success')
                return redirect(url_for('datacenters.datacenters_environments'))
            else:
                for key, value in environment_form.errors.items():
                    flash(f'An error occurred for {str(key)}, {str(value[0])}', 'error')
                return redirect(url_for('datacenters.datacenters_environments'))
        elif request.form['type'] == "dc":
            if database.check_if_datacenter_already_exists_using_name(datacenter_form.name.data):
                flash('Datacenter already exists', 'warning')
                return redirect(url_for('datacenters.datacenters_environments'))
            if datacenter_form.validate_on_submit():
                database.datacenter_create(datacenter_form.name.data)
                flash('Datacenter created for %s!' % (datacenter_form.name.data), 'success')
                return redirect(url_for('datacenters.datacenters_environments'))
            else:
                for key, value in datacenter_form.errors.items():
                    flash(f'An error occurred for {str(key)}, {str(value[0])}', 'error')
                return redirect(url_for('datacenters.datacenters_environments'))
    datacenters = database.datacenter_get_all()
    environments = database.environment_get_all()
    search_type, search_filter = utility.search_filter()
    return render_template('datacenters.html', title='Datacenters & Environments',
                           datacenters=datacenters, environments=environments,
                           datacenter_form=datacenter_form, environment_form=environment_form,
                           search_type=search_type, search_filter = search_filter)


@datacenters.route("/edit-datacenter", methods=['POST'])
@login_required
@validate_route_access
def edit_datacenter():
    logger.Log("FUNCTION CALL: edit_data_center()", logging.DEBUG)
    # if not session['site_admin']:
    #     if (int(session['id']) != int(id)):
    #         abort(403)

    data = dict(request.json)
    try:
        name = data.get('name') if(data.get('name').strip()) else 'NULL'
        # department = data.get('department') if(data.get('department').strip() or data.get('department') is not None) else 'NULL'
        database.Update_datacenter_by_id(data.get('id'), name)

        flash("Datacenter updated successfully!", 'success')
        return json.dumps({'success': True}), 200

    except Exception as e:
        logger.Log('Error while editing Datacenter: %s' %e, logging.ERROR)
        flash("Error editing Datacenter.", 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500


@datacenters.route("/edit-environment", methods=['POST'])
@login_required
@validate_route_access
def edit_environment():
    logger.Log("FUNCTION CALL: edit_environment()", logging.DEBUG)
    # if not session['site_admin']:
    #     if (int(session['id']) != int(id)):
    #         abort(403)

    data = dict(request.json)
    try:
        name = data.get('name') if(data.get('name').strip()) else 'NULL'
        # department = data.get('department') if(data.get('department').strip() or data.get('department') is not None) else 'NULL'
        database.Update_environment_by_id(data.get('id'), name)

        flash("Environment updated successfully!", 'success')
        return json.dumps({'success': True}), 200

    except Exception as e:
        logger.Log('Error while editing Environment: %s' %e, logging.ERROR)
        flash("Error editing Environment.", 'danger')
        return json.dumps({'success': False, 'error': repr(e)}), 500



@datacenters.route("/delete_datacenter/<int:id>", methods=['DELETE'])
@login_required
@validate_route_access
def delete_datacenter(id):
    logger.Log('FUNCTION CALL: delete_datacenter()', logging.DEBUG)
    if database.check_if_datacenter_already_exists_using_id(id):
        database.delete_datacenter(id=id)
        flash('Datacenter deleted successfully!', 'success')
        return jsonify({'success': True}), 200
    flash('Datacenter not found.', 'error')
    return jsonify({'not found': False}), 400


@datacenters.route("/delete_environment/<int:id>", methods=['DELETE'])
@login_required
@validate_route_access
def delete_environment(id):
    logger.Log('FUNCTION CALL: delete_environment()', logging.DEBUG)
    if database.check_if_environment_already_exists_using_id(id):
        database.delete_environment(id=id)
        flash('Environment deleted successfully!', 'success')
        return jsonify({'success': True}), 200
    flash('Environment not found.', 'error')
    return jsonify({'not found': False}), 400
