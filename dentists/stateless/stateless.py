import json
import os

from aws_cdk import Fn, RemovalPolicy, Stack
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda
from aws_cdk import aws_logs as logs
from aws_cdk import aws_pipes as pipes
from aws_cdk import aws_sqs as sqs
from constructs import Construct

DIRNAME = os.path.dirname(__file__)

class DentistsStatelessStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # import dynamodb table props from the first stack
        dynamodb_table_name = Fn.import_value('DentistDynamoDBTableName')
        contacts_dynamodb_table_name = Fn.import_value('DentistContactDynamoDBTableName')
        stream_arn = Fn.import_value('DentistDynamoDBTableStreamArn')
        
        # create the lambda function for creating an appointment
        create_appointment_lambda = aws_lambda.Function(
            self, 'CreateAppointment',
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler='create_appointment.handler',
            code=aws_lambda.Code.from_asset(os.path.join(DIRNAME, 'src')),
            function_name='CreateAppointment',
            environment={
                'dynamodb_table': dynamodb_table_name,
            },
        )
        
        # create the lambda function for retrieving contact details
        get_contact_details = aws_lambda.Function(
            self, 'GetContactDetails',
            runtime=aws_lambda.Runtime.PYTHON_3_12,
            handler='get_contact_details.handler',
            code=aws_lambda.Code.from_asset(os.path.join(DIRNAME, 'src')),
            function_name='GetContactDetails',
            environment={
                'contacts_dynamodb_table': contacts_dynamodb_table_name,
            },
        )
        
        # get a reference to the tables in the other stack
        dynamodb_table = dynamodb.Table.from_table_name(self, 'DentistDynamoDBTable', dynamodb_table_name)
        contacts_dynamodb_table = dynamodb.Table.from_table_name(self, 'DentistContactsDynamoDBTable', contacts_dynamodb_table_name)
        
        # create the sqs queue which are pipes will send messages too (the target)
        sqs_queue = sqs.Queue(
            self, 'AppointmentsQueue',
            queue_name='AppointmentsQueue',
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # create the pipe policy and role for the source (dynamodb streams)
        pipe_source_policy = iam.PolicyStatement(
            actions=[
                'dynamodb:DescribeStream',
                'dynamodb:GetRecords',
                'dynamodb:GetShardIterator',
                'dynamodb:ListStreams'
            ],
            resources=[stream_arn],
            effect=iam.Effect.ALLOW
        )
        
        # create the target policy to allow the pipe to publish messages to sqs (target)
        pipe_target_policy = iam.PolicyStatement(
            actions=['sqs:SendMessage'],
            resources=[sqs_queue.queue_arn],
            effect=iam.Effect.ALLOW
        )
        
        # create the policy to allow the pipe to invoke our lambda (enrichment)
        pipe_enrichment_policy = iam.PolicyStatement(
            actions=['lambda:InvokeFunction'],
            resources=[get_contact_details.function_arn],
            effect=iam.Effect.ALLOW
        )

        # create the pipe role
        pipe_role = iam.Role(self, 'PipeRole',
            assumed_by=iam.ServicePrincipal('pipes.amazonaws.com'),
        )
        
        # add the three policies to the role
        pipe_role.add_to_policy(pipe_source_policy)
        pipe_role.add_to_policy(pipe_target_policy)
        pipe_role.add_to_policy(pipe_enrichment_policy)
        
        # create a log group for pipes
        log_group = logs.LogGroup(
            self, 'PipesLogGroup',
            log_group_name='PipesLogGroup',
            removal_policy=RemovalPolicy.DESTROY
        )
        
        # create the eventbridge pipe that has a filter just for new items in dynamodb
        pipe = pipes.CfnPipe(self, 'Pipe',
            role_arn=pipe_role.role_arn,
            source=stream_arn,
            log_configuration=pipes.CfnPipe.PipeLogConfigurationProperty(
                cloudwatch_logs_log_destination=pipes.CfnPipe.CloudwatchLogsLogDestinationProperty(
                    log_group_arn=log_group.log_group_arn
                ),
                level='INFO',
            ),
            name='DentistPipe',
            source_parameters=pipes.CfnPipe.PipeSourceParametersProperty(
                dynamo_db_stream_parameters=pipes.CfnPipe.PipeSourceDynamoDBStreamParametersProperty(
                    starting_position='LATEST',
                ),
                filter_criteria=pipes.CfnPipe.FilterCriteriaProperty(
                    filters=[pipes.CfnPipe.FilterProperty(
                        pattern=json.dumps({'eventName': [ { 'prefix': 'INSERT' } ]})
                    )]
                ),
            ),
            enrichment=get_contact_details.function_arn,
            target=sqs_queue.queue_arn,
        )
        pipe.apply_removal_policy(RemovalPolicy.DESTROY)

        # create the rest api for adding new appointments
        api = apigw.RestApi(self, 'DentistApi', rest_api_name='DentistApi')
        
        # resource and method for /appointments/
        appointments_resource = api.root.add_resource('appointments')
        appointments_resource.add_method('POST', apigw.LambdaIntegration(create_appointment_lambda))
        
        # ensure the lambda functions have access to the database
        dynamodb_table.grant_write_data(create_appointment_lambda)
        contacts_dynamodb_table.grant_read_data(get_contact_details)