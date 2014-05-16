import json
import os


__config_directory = os.path.join(os.path.dirname(__file__), "config")


def set_config_directory(directory):
    '''Default config directory is "config" located in the project root'''
    global __config_directory
    __config_directory = directory


def read_config(filename):
    '''Reads a configuration file from the config file directory'''
    config_file = os.path.join(__config_directory, filename)
    with open(config_file, "r") as f:
        content = '\n'.join(
            [line for line in f if not line.strip().startswith('#')])
        try:
            # TODO: validate using jsonschema?
            return json.loads(content)
        except ValueError as detail:
            print "unable to parse %s\n%s" % (filename, str(detail))
            raise
