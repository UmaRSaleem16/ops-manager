import logging
import json

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required

from app.decorators import validate_route_access
from app import logger, database
from app import utility

history = Blueprint('history', __name__)



@history.route("/get-history")
@login_required
@validate_route_access
def get_history_ajax():
    logger.Log('FUNCTION CALL: get_history_ajax()', logging.DEBUG)
    try:
        history_data = database.get_history_data()        


        draw = int(request.args.get('draw', 0))
        start = int(request.args.get('start', 0))
        length = int(request.args.get('length', 10))
        search_value = request.args.get('search[value]', '')
        order_column_index = int(request.args.get('order[0][column]', 0))
        order_direction = request.args.get('order[0][dir]', 'asc')  

        filtered_data = [record for record in history_data if search_value.lower() in str(record).lower()]
        sorted_data = sorted(filtered_data, key=lambda x: x.get('id'), reverse=(True))
        # Apply pagination
        paginated_data = sorted_data[start:start + length]

        # Prepare response
        response = {
            "draw": draw,
            "recordsTotal": len(history_data),
            "recordsFiltered": len(filtered_data),
            "data": paginated_data
        }
    except Exception as e:
        logger.Log('Error while getting history: %s' %e, logging.ERROR)
        return jsonify({'success': False, 'error': repr(e)}), 500

    return jsonify(response)



@history.route("/history")
@login_required
@validate_route_access
def get_history():
    logger.Log('FUNCTION CALL: get_history()', logging.DEBUG)
    search_type, search_filter = utility.search_filter()
    return render_template('history.html', title='History', search_type=search_type, search_filter=search_filter)


@history.route("/history/<id>")
@login_required
@validate_route_access
def get_history_by_id(id):
    logger.Log('FUNCTION CALL: get_history_by_id()', logging.DEBUG)
    history_details = database.get_history_data_by_id(id)

    before_data = json.loads(history_details.get('data_json')).get('before')
    after_data = json.loads(history_details.get('data_json')).get('after')
    
    search_type, search_filter = utility.search_filter()

    return render_template('history_details.html', title='History Details',id=id, before_data=before_data, after_data=after_data, search_type=search_type, search_filter=search_filter)