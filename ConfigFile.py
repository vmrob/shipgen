import json
import jsonschema
import os
import sys

__config_directory = os.path.join(os.path.dirname(__file__), "config")
__schema_directory = os.path.join(os.path.dirname(__file__), "schema")


def set_config_directory(directory):
    '''Default config directory is "config" located in the project root'''
    global __config_directory
    __config_directory = directory


def __strip_comments(f):
    return '\n'.join([line for line in f if not line.strip().startswith('#')])


def __json_load(filename):
    with open(filename, 'r') as f:
        content = __strip_comments(f)
        try:
            return json.loads(content)
        except ValueError as detail:
            print "unable to parse file %s\n%s" % (filename, str(detail))
            sys.exit(1)


def read_config(filename):
    '''Reads a configuration file from the config file directory'''
    config_dict = __json_load(os.path.join(__config_directory, filename))
    schema_dict = __json_load(os.path.join(__schema_directory, filename))

    try:
        resolver = jsonschema.RefResolver(
            'file://' + os.path.join(__schema_directory, filename), filename)
        jsonschema.Draft4Validator(schema_dict,
                                   resolver=resolver).validate(config_dict)
    except jsonschema.ValidationError as detail:
        print ('unable to parse configuration for %s\n%s'
               % (filename, str(detail)))
        sys.exit(1)
    except jsonschema.SchemaError as detail:
        print ('unable to parse schema for %s\n%s'
               % (filename, str(detail)))
        sys.exit(1)
    except jsonschema.RefResolutionError as detail:
        print ('unable to parse schema for %s\n%s'
               % (filename, str(detail)))
        raise
        sys.exit(1)
    return config_dict
