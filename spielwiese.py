#https://pynative.com/python-serialize-datetime-into-json/
# -- pip install python-dateutil --

import json
import datetime
from json import JSONEncoder

sonnenschutz = {
    "ein": False,
    "runter": datetime.time,
    "hoch": datetime.time
}

rollozeit = {
    "early": datetime.time,
    "late": datetime.time
}

employee = {
    "morgens": rollozeit,
    "abends": rollozeit,
    "luftreduziert": True,
    "sonne": sonnenschutz
}

# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):
        #Override the default method
        def default(self, obj):
            if isinstance(obj, (datetime.date, datetime.datetime)):
                return obj.isoformat()

# custom Decoder
def DecodeDateTime(empDict):
   if 'joindate' in empDict:
      empDict["joindate"] = dateutil.parser.parse(empDict["joindate"])
      return empDict



print("Printing to check how it will look like")
print(DateTimeEncoder().encode(employee))

print("Encode DateTime Object into JSON using custom JSONEncoder")
employeeJSONData = json.dumps(employee, indent=4, cls=DateTimeEncoder)
print(employeeJSONData)

path_regeln = '/var/www/html/RolloPi/spielwiese.json'

with open(path_regeln, 'w', encoding='utf-8') as f:
    json.dump(employee, f, ensure_ascii=False, indent=4, cls=DateTimeEncoder)