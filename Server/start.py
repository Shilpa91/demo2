from flask import Flask, request, Response
import redis
import json
from jsonschema import validate, exceptions

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, db=0, charset="utf-8", decode_responses=True)
# r = redis.Redis(host='redis-11032.c93.us-east-1-3.ec2.cloud.redislabs.com', port=11032, password='AuOMuWvzvz9YtJChL9c1yC1f0ZGAoaKl', charset="utf-8", decode_responses=True)

@app.route("/")
def hello_world():
    return "Hello, World!"

# Read
@app.route("/v1/<type>/<id>",methods=["GET"])
def readData(type,id):
    try:
        client_match_id = request.headers.get('If-None-Match')

        data = {}
        for key in r.scan_iter(type+'_'+id+'..*'):
            data[key.split(type+'_'+id+'..')[-1]] = json.loads(r.get(key))

        response = Response(json.dumps(data))
        response.add_etag()
        (etag,is_weak) = response.get_etag()

        print(etag,client_match_id)

        if etag == client_match_id:
            return Response(status=304, mimetype='application/json')
        else:
            return Response(json.dumps(data),status=200, mimetype='application/json')
    except Exception as e:
        return Response(json.dumps("Data not present in database"),status=400, mimetype='application/json')

# Validate
@app.route("/v1/jsonvalidate",methods=["POST"])
def valInput():
    content = request.json
    schema = json.load(open('../json_schema.json'))
    # Mark status code based on the status of validation
    try:
        validate(instance=content, schema=schema)
        # Extract ObjectId, ObjectType
        return Response(json.dumps({'Message': 'Object is valid', 'objectId': content['objectId'],'objectType': content['objectType']}), status=200, mimetype='application/json')
    except Exception as e:
        return Response(e.message, status=400, mimetype='text/plain')

# Create
@app.route("/v1/jsonvalpost",methods=["POST"])
def readInput():
    content = request.json
    schema = json.load(open('../json_schema.json'))
    # Mark status code based on the status of validation
    try:
        validate(instance=content, schema=schema)

        # Extract ObjectId, ObjectType and generate key
        key_prefix = content['objectType']+'_'+content['objectId']

        for key in content.keys():
            # print(key, key_prefix+'..'+key, content[key])
            r.set(key_prefix+'..'+key,json.dumps(content[key]))

        data = {}
        for key in r.scan_iter(key_prefix+'..*'):
            data[key.split(key_prefix+'..')[-1]] = json.loads(r.get(key))

        # response = Response(json.dumps({'Message': 'Valid object found, stored in redis', 'redis-key': key, 'objectId': content['objectId'],'objectType': content['objectType']}), status=200, mimetype='application/json')
        response = Response(json.dumps(data), status=200, mimetype='application/json')
        response.add_etag()
        print(response.get_etag())

        return response

    except Exception as e:
        return Response(e.message, status=400, mimetype='text/plain')

# Put
@app.route("/v1/<type>/<id>",methods=["PUT"])
def readPutInput(type,id):
    content = request.json
    schema = json.load(open('../json_schema.json'))
    # Mark status code based on the status of validation
    try:

        client_match_id = request.headers.get('If-Match')

        # Extract ObjectId, ObjectType and generate key
        key_prefix = type+'_'+id

        data = {}
        for key in r.scan_iter(key_prefix + '..*'):
            data[key.split(key_prefix + '..')[-1]] = json.loads(r.get(key))

        response = Response(json.dumps(data), status=200, mimetype='application/json')
        response.add_etag()
        (etag, weak) = response.get_etag()

        if client_match_id == etag:

            validate(instance=content, schema=schema)

            for key in content.keys():
                r.set(key_prefix+'..'+key,json.dumps(content[key]))

            data = {}
            for key in r.scan_iter(key_prefix + '..*'):
                data[key.split(key_prefix + '..')[-1]] = json.loads(r.get(key))

            # response = Response(json.dumps({'Message': 'Valid object found, stored in redis', 'redis-key': key, 'objectId': content['objectId'],'objectType': content['objectType']}), status=200, mimetype='application/json')
            response = Response(json.dumps(data), status=200, mimetype='application/json')
            response.add_etag()
            (etag,weak) = response.get_etag()
            # print(etag)
            return response

        else:

            response = Response(status=412, mimetype='application/json')
            return response

    except Exception as e:
        return Response(e.message, status=400, mimetype='text/plain')

# Patch
@app.route("/v1/<type>/<id>",methods=["PATCH"])
def readPatchInput(type,id):
    content = request.json
    schema = json.load(open('../json_schema.json'))
    # Mark status code based on the status of validation
    try:

        client_match_id = request.headers.get('If-Match')

        # Extract ObjectId, ObjectType and generate key
        key_prefix = type+'_'+id

        data = {}
        for key in r.scan_iter(key_prefix + '..*'):
            data[key.split(key_prefix + '..')[-1]] = json.loads(r.get(key))

        response = Response(json.dumps(data), status=200, mimetype='application/json')
        response.add_etag()
        (etag, weak) = response.get_etag()

        if client_match_id == etag:

            data = {}
            for key in r.scan_iter(key_prefix+'..*'):
                data[key.split(key_prefix+'..')[-1]] = json.loads(r.get(key))

            key = list(content.keys())[0]
            for item in content[key]:
                if item not in data[key]:
                    data[key].append(item)

            validate(instance=data, schema=schema)

            for key in content.keys():
                r.set(key_prefix+'..'+key,json.dumps(data[key]))

            # response = Response(json.dumps({'Message': 'Valid object found, stored in redis', 'redis-key': key, 'objectId': content['objectId'],'objectType': content['objectType']}), status=200, mimetype='application/json')
            response = Response(json.dumps(data), status=200, mimetype='application/json')
            response.add_etag()
            (etag, weak) = response.get_etag()
            # print(etag)

            return response

        else:

            response = Response(status=412, mimetype='application/json')
            return response

    except Exception as e:
        return Response(e.message, status=400, mimetype='text/plain')

# Delete
@app.route("/v1/del/<type>/<id>",methods=["DELETE"])
def delData(type,id):
    if any([type+'_'+id in x for x in list(r.keys())]):
        print('Signatures found, initiating delete...')
        for key in r.scan_iter(type + '_' + id + '..*'):
            r.delete(key)
        return Response(json.dumps("Delete successful"), status=200, mimetype='application/json')
    else:
        return Response(json.dumps("Key not present or already deleted"), status=400, mimetype='application/json')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)