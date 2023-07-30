import json

def lambda_handler(event, context):
    x = [{"a": 1, "b": 2}, 12345, {"c":6}]

    print(json.dumps(x, indent=4))
    
    print('Done x1.1')