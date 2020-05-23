import json

with open("/flash/config.json",'r') as ymlfile:
    json_out = json.load(ymlfile)

print(json_out)
print(json_out['configMode'])
print(json_out['acc-threshold (g)']) 
