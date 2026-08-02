import import_declare_test

import sys

from splunklib import modularinput as smi
from observability_audit_event_helper import stream_events, validate_input


class OBSERVABILITY_AUDIT_EVENT(smi.Script):
    def __init__(self):
        super(OBSERVABILITY_AUDIT_EVENT, self).__init__()

    def get_scheme(self):
        scheme = smi.Scheme('observability_audit_event')
        scheme.description = 'observability_audit_event'
        scheme.use_external_validation = True
        scheme.streaming_mode_xml = True
        scheme.use_single_instance = False

        scheme.add_argument(
            smi.Argument(
                'name',
                title='Name',
                description='Name',
                required_on_create=True
            )
        )
        scheme.add_argument(
            smi.Argument(
                'account',
                required_on_create=True,
            )
        )
        scheme.add_argument(
            smi.Argument(
                'sf_event_category',
                required_on_create=True,
            )
        )
        scheme.add_argument(
            smi.Argument(
                'sf_event_type',
                required_on_create=False,
            )
        )
        return scheme

    def validate_input(self, definition: smi.ValidationDefinition):
        return validate_input(definition)

    def stream_events(self, inputs: smi.InputDefinition, ew: smi.EventWriter):
        return stream_events(inputs, ew)


if __name__ == '__main__':
    exit_code = OBSERVABILITY_AUDIT_EVENT().run(sys.argv)
    sys.exit(exit_code)