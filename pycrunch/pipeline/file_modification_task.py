import time

from pycrunch.api import shared
from pycrunch.discovery.simple import SimpleTestDiscovery
from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.pipeline.run_test_task import RunTestTask
from pycrunch.session import state
from pycrunch.session.combined_coverage import combined_coverage
from pycrunch.session.file_map import test_map


class FileModifiedNotificationTask(AbstractTask):
    def __init__(self, file):
        self.file = file
        self.timestamp = time.time()

    def run(self):
        shared.pipe.push(event_type='file_modification',
                         modified_file=self.file,
                         ts=self.timestamp,
                         )

        # todo
        # look out for new tests in changed files
        # clean up zombie tests
        # run impacted tests and newly discovered

        discovery = SimpleTestDiscovery()
        old_map = test_map.get_immutable_tests_for_file(self.file)
        possibly_new_tests = discovery.find_tests_in_folder(state.engine.folder, search_only_in=[self.file])
        state.engine.test_discovery_will_become_available(possibly_new_tests)
        new_map = test_map.get_immutable_tests_for_file(self.file)
        removed_tests = set()
        added_tests = set()
        for t in old_map:
            if t not in new_map:
                removed_tests.add(t)

        for t in new_map:
            if t not in old_map:
                added_tests.add(t)

        execution_plan = set()
        for new_test in possibly_new_tests.tests:
            if new_test.fqn in new_map:
                # todo should depend on execution mode
                execution_plan.add(new_test.fqn)



        dependencies = combined_coverage.dependencies
        if dependencies:
            impacted_tests = dependencies[self.file]

            for fqn in impacted_tests:
                if fqn not in removed_tests:
                    execution_plan.add(fqn)
                else:
                    print(f"test {fqn} removed from execution plan")
            tests_to_run = state.engine.all_tests.collect_by_fqn(execution_plan)
            execution_pipeline.add_task(RunTestTask(tests_to_run))

        pass;

# https://stackoverflow.com/questions/45369128/python-multithreading-queue
