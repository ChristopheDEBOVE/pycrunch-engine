
import io
from pathlib import Path

from flask import jsonify, Response
from flask_socketio import send

from pycrunch import runner
from pycrunch.api.shared import file_watcher
from pycrunch.discovery.simple import SimpleTestDiscovery
from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.run_test_task import RunTestTask
from pycrunch.session.state import engine
from pycrunch.shared.models import all_tests
from .serializers import serialize_test_run
from flask import Blueprint
from flask import request

import logging

logger = logging.getLogger(__name__)

pycrunch_api = Blueprint('pycrunch_api', __name__)

@pycrunch_api.route("/")
def hello():
    return "Nothing here"


@pycrunch_api.route("/discover")
def discover_tests():
    folder = request.args.get('folder')
    engine.will_start_test_discovery()


    return jsonify(dict(ack=True))


@pycrunch_api.route("/diagnostics")
def queue_diagnostics():
    engine.will_start_diagnostics_collection()


    return jsonify(dict(ack=True))



@pycrunch_api.route("/run-tests", methods=['POST'])
def run_tests():

    tests = request.json.get('tests')
    logger.info('Running tests...')
    logger.info(tests)
    fqns = set()
    for test in tests:
        fqns.add(test['fqn'])

    tests_to_run = all_tests.collect_by_fqn(fqns)

    execution_pipeline.add_task(RunTestTask(tests_to_run))
    return jsonify(tests)



@pycrunch_api.route("/file", methods=['GET'])
def download_file():
    filename = request.args.get('file')
    logger.debug('download_file ' + filename)
    my_file = io.FileIO(filename, 'r')
    content = my_file.read()
    return Response(content, mimetype='application/x-python-code')

