#!/usr/bin/env python
# _*_ coding: utf-8 _*_

# Makes modifications to the controlled vocabulary (implemented as
# ckanext-scheming "choices")
# HvW - 2016-06-07

"""Usage:
  ck_choices [--del] [--resource] FIELD TERM...
  ck_choices (-l | --listfields) [--labels]
  ck_choices (-h | --help)

Make modifications to the controlled vocabulary FIELD
(implemented as ckanext-scheming "choices").

Arguments:
  FIELD  the schema field to be modified
  TERM   the terms to be added (removed). Have the format
         "value,label" for adding, and "value" for removing.

Options:
  -h --help        Show this help.
  -l --listfields  List all fields.
  --labels         List also choice-labels (in addition to values).
  -d --del         Delete instead of create the term(s).
  -r --resource    Refers to resource field (default is dataset field).

"""

from pprint import pprint
from docopt import docopt
import sys
import json
import os

LOCAL_SCHEMA=("/usr/lib/ckan/default/src/ckanext-eaw_schema/ckanext/" +
               "eaw_schema/eaw_schema_dataset.json")

def listfields(schema):
    fields = schema['dataset_fields']
    if params['--labels']:
        choicerep = lambda c: (c['value'], c['label'])
    else:
        choicerep = lambda c: c['value']
    for f in ('{}, {}\n{}\n'.format(x['field_name'], x['label'],
                                    [choicerep(c) for c in x['choices']])
              for x in fields if 'choices' in x):
        print(f)

def postparse(params):
    terms = [x.split(',') for x in params['TERM']]
    if params['--del'] and not all([len(x) == 1 for x in terms]):
        print(__doc__)
        sys.exit(1)
    elif not params['--del'] and not all([len(x) == 2 for x in terms]):
        print(__doc__)
        sys.exit(1)
    terms = [x[0] if len(x) == 1 else x for x in terms]
    return(terms)
    

def load_schema(schemafile):
    try:
        with open(schemafile) as sf:
            schema = json.load(sf)
    except ValueError:
        raise(SystemExit("Schema file {} doesn't parse into JSON"
                         .format(schemafile), 1))
    except IOError:
        raise(SystemExit("Could not open schema file 'testschema'", 1))
    return(schema)

def check_unique(field, choices, terms):
    for t in [x[0] for x in terms]:
        if t in [x['value'] for x in choices]:
            raise SystemExit('{} already in {}'.format(t, field))

def update_field(schema, typ, field, remove, terms):
    " typ: 'dataset_field' or 'resource_field'"
    def _build_choices(terms):
        ch = [{'value': t[0], 'label': t[1]} for t in terms]
        return ch
        
    def _get_val_index(val, choices):
        idx = [x.get('value') for x in choices].index(val)
        return(idx)
    try:
        f = [x for x in schema[typ] if x["field_name"] == field]
    except KeyError:
        raise SystemExit('Could not find field_type "{}"'.format(typ))
    if not f:
        raise SystemExit("Could not find field \"{}\" in \"{}\""
                         .format(field, typ))
    assert(len(f) == 1)
    c = f[0]['choices']
    if not remove:
        check_unique(field, c, terms)
        c.extend(_build_choices(terms))
    else:
        try:
            rmidx = [_get_val_index(val, c) for val in terms]
        except ValueError:
            raise SystemExit('Not all terms found in ' +
                             'field "{}" in "{}"'.format(field, typ))
        if len(rmidx) < len(terms):
            raise SystemExit('Not all terms found in ' +
                 'field "{}" in "{}"'.format(field, typ))
        cnew = [x[1] for x in enumerate(c) if x[0] not in rmidx]
        f[0]['choices'] = cnew
    return(schema)

def write_schema(newschema, path):
    with open(path, 'w') as f:
        json.dump(newschema, f, indent=2)
        
def main():
    schema = load_schema(LOCAL_SCHEMA)
    terms = postparse(params)
    if params['--listfields']:
        listfields(schema)
        sys.exit()
    field = params['FIELD']
    remove = params['--del']
    typ = 'resource_fields' if params['--resource'] else 'dataset_fields'
    newschema = update_field(schema, typ, field, remove, terms)
    write_schema(newschema, LOCAL_SCHEMA)

    
if __name__ == '__main__':
    params = docopt(__doc__, sys.argv[1:])
    main()   
    



