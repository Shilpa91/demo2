from jsonschema import validate
import json

use_case = json.load(open('../use_case.json'))
schema = json.load(open('../json_schema.json'))

# schema = {
#      "type": "object",
#      "properties": {
#          "price": {"type": "number"},
#          "name": {"type": "string"},
#      },
# }
#
# use_case = {"name" : "Eggs", "price" : "34.99"}

print(use_case.keys())
print(schema['properties']['planCostShares'])

print(validate(instance=use_case, schema=schema))