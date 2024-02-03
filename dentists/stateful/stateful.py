from aws_cdk import CfnOutput, RemovalPolicy, Stack
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct


class DentistsStatefulStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # add the dynamodb table for storing appointments which has streams enabled
        table = dynamodb.Table(
            self, 'DentistTable',
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_name='DentistTable',
            stream=dynamodb.StreamViewType.NEW_IMAGE,
            removal_policy=RemovalPolicy.DESTROY,
            partition_key=dynamodb.Attribute(
                name='id',
                type=dynamodb.AttributeType.STRING
            )
        )
        
        # add the contact preferences dynamodb table which id is the email address
        contact_table = dynamodb.Table(
            self, 'DentistContactsTable',
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            table_name='DentistContactsTable',
            removal_policy=RemovalPolicy.DESTROY,
            partition_key=dynamodb.Attribute(
                name='id',
                type=dynamodb.AttributeType.STRING
            )
        )
        
        # add a stack output for the table name
        CfnOutput(
            self, 'DentistDynamoDBTableName',
            value=table.table_name,
            description='Name of the DynamoDB table',
            export_name='DentistDynamoDBTableName'
        )
        
        # add a stack output for the contact table name
        CfnOutput(
            self, 'DentistContactDynamoDBTableName',
            value=contact_table.table_name,
            description='Name of the Contact Preferences DynamoDB table',
            export_name='DentistContactDynamoDBTableName'
        )
        
        # add a stack output for the table stream arn of the appointments table
        CfnOutput(
            self, 'DentistDynamoDBTableStreamArn',
            value=table.table_stream_arn,
            description='DynamoDB table stream ARN',
            export_name='DentistDynamoDBTableStreamArn'
        )