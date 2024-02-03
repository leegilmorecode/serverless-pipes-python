import json
import os
import uuid
from http import HTTPStatus

import boto3
from boto3.dynamodb.types import TypeSerializer

dynamodb_table = os.getenv('dynamodb_table')
dynamodb_client = boto3.client('dynamodb')
serializer = TypeSerializer()

def handler(event, context):
    try:
        # parse the request data from the event and grab the body
        request_data = json.loads(event['body'])
        
        # add a new appointment id using uuidv4
        request_data['id'] = str(uuid.uuid4())
        
        # serialize the payload into dynamodb format
        appointment_data = {k: serializer.serialize(v) for k,v in request_data.items()}
                
        # add the item to the dynamodb table
        dynamodb_client.put_item(TableName=dynamodb_table, Item=appointment_data)

        body = {
            'message': request_data,
            'statusCode': HTTPStatus.CREATED,
        }

        # send the response back to api gateway in the correct shape
        response = {
            'statusCode': HTTPStatus.CREATED,
            'body': json.dumps(body, indent=2),
            'headers': {
                'content-type': 'application/json',
            },
        }

    except Exception as e:
        response = {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR.value,
            'body': f'Exception={e}',
        }

    return response
