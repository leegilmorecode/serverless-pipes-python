import os

import boto3
from boto3.dynamodb.types import TypeDeserializer

dynamodb_table = os.getenv('contacts_dynamodb_table')
dynamodb_client = boto3.client('dynamodb')
deserializer = TypeDeserializer()

def handler(event, context):
    try:
        # parse the request data from the stream event and grab the body
        new_image_data = event[0]['dynamodb']['NewImage']
        
        response = {k: deserializer.deserialize(v) for k,v in new_image_data.items()}
        
        # get the email address from the streams body
        email_address = response['appointment']['patient']['email']
        print('Email: ', email_address)

        # check whether or not this email address exists in the contact databases
        account = dynamodb_client.get_item(
            TableName=dynamodb_table,
            Key={'id': {'S': email_address}}
        )
        
        if 'Item' in account:
            item = account['Item']
            
            # deserialize the dynamodb item if found
            account_data = {k: deserializer.deserialize(v) for k,v in item.items()}
            print('Contact information found: ', account_data)
            
            # add the account data onto the reponse so its available on the sqs message
            response['preferredMethod'] = account_data['preferredMethod']
        else:
            # add the account data onto the reponse
            response['preferredMethod'] = 'none'
            print('Contact information not found.')
        

    except Exception as e:
        print(e)
        response = {
            'error': f'Exception={e}',
            'body': response,
        }

    print('response: ', response)
    return response
