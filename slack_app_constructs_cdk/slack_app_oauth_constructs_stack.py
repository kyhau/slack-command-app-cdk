from aws_cdk import CfnParameter, Duration, RemovalPolicy, Stack
from aws_cdk import aws_apigateway as apigw_
from aws_cdk import aws_dynamodb as ddb_
from aws_cdk import aws_iam as iam_
from aws_cdk import aws_lambda as lambda_
from aws_cdk.aws_logs import LogGroup, RetentionDays
from constructs import Construct

LAMBDA_DIR = "lambda"


def get_team_ids(settings):
    return [v["team_id"] for v in settings["access"].values() if v.get("team_id")]


def get_channel_ids(settings):
    ret = []
    for v in settings["access"].values():
        if v.get("channels"):
            ret.extend(v["channels"].keys())
    return ret


class SlackAppOAuthConstructsStack(Stack):
    def __init__(self, scope: Construct, id: str, settings, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.id = id

        # cdk deploy --parameters StageName=v1
        stage = CfnParameter(
            self,
            "StageName",
            default="v1",
            description="The name of the API Gateway Stage.",
            type="String",
        ).value_as_string

        ssm_param_key_client_id = settings["ssm_parameter_key_client_id"]
        ssm_param_key_client_secret = settings["ssm_parameter_key_client_secret"]

        table_name = f"{id}-OAuth"

        # Create a dynamodb table
        oauth_table = self.create_dynamodb_table(table_name)

        # Create function and role for OAuth
        func_oauth_role = self.create_func_oauth_execution_role(
            f"{id}-OAuth",
            ssm_param_key_client_id,
            ssm_param_key_client_secret,
            oauth_table.table_arn,
        )
        func_oauth = self.create_lambda("OAuth", custom_role=func_oauth_role)
        func_oauth.add_environment("SlackAppId", settings["slack_app_id"])
        func_oauth.add_environment("SlackAppClientIdParameterKey", ssm_param_key_client_id)
        func_oauth.add_environment("SlackAppClientSecretParameterKey", ssm_param_key_client_secret)
        func_oauth.add_environment("SlackChannelIds", ",".join(get_channel_ids(settings)))
        func_oauth.add_environment("SlackTeamIds", ",".join(get_team_ids(settings)))
        func_oauth.add_environment("OAuthDynamoDBTable", table_name)

        api = apigw_.LambdaRestApi(
            self,
            f"{id}-API",
            description=f"{id} API",
            endpoint_configuration=apigw_.EndpointConfiguration(
                types=[apigw_.EndpointType.REGIONAL]
            ),
            handler=func_oauth,
            deploy=False,
            proxy=False,
        )

        item = api.root.add_resource("oauth2")
        item.add_method("ANY", apigw_.LambdaIntegration(func_oauth))

        # Create APIGW Loggroup for setting retention
        LogGroup(
            self,
            f"{id}-API-LogGroup",
            log_group_name=f"API-Gateway-Execution-Logs_{api.rest_api_id}/{stage}",
            retention=RetentionDays.ONE_DAY,
        )

        # Do a new deployment on specific stage
        new_deployment = apigw_.Deployment(self, f"{id}-API-Deployment", api=api)
        apigw_.Stage(
            self,
            f"{id}-API-Stage",
            data_trace_enabled=True,
            description=f"{stage} environment",
            deployment=new_deployment,
            logging_level=apigw_.MethodLoggingLevel.INFO,
            metrics_enabled=True,
            stage_name=stage,
            tracing_enabled=False,
        )

    def create_dynamodb_table(self, table_name: str) -> ddb_.Table:
        return ddb_.Table(
            self,
            table_name,
            billing_mode=ddb_.BillingMode.PAY_PER_REQUEST,
            partition_key=ddb_.Attribute(name="access_token", type=ddb_.AttributeType.STRING),
            removal_policy=RemovalPolicy.RETAIN,
            table_name=table_name,
        )

    def create_lambda(self, function_name: str, custom_role: iam_.Role) -> lambda_.Function:
        return lambda_.Function(
            self,
            f"{self.id}-{function_name}-Function",
            code=lambda_.Code.from_asset(
                LAMBDA_DIR,
                exclude=[
                    "*.test.py",
                    "requirements.txt",
                ],
            ),
            current_version_options=lambda_.VersionOptions(
                removal_policy=RemovalPolicy.DESTROY,
                retry_attempts=2,
            ),
            function_name=f"{self.id}-{function_name}",
            handler=f"{function_name}.lambda_handler",
            log_retention=RetentionDays.ONE_DAY,
            role=custom_role,
            runtime=lambda_.Runtime.PYTHON_3_11,
            timeout=Duration.seconds(900),
            tracing=lambda_.Tracing.DISABLED,
        )

    def create_func_oauth_execution_role(
        self, function_name: str, client_id_key: str, client_secret_key: str, table_arn: str
    ) -> iam_.Role:
        role_name = f"{function_name}-ExecutionRole"
        return iam_.Role(
            self,
            role_name,
            assumed_by=iam_.ServicePrincipal("lambda.amazonaws.com"),
            inline_policies={
                f"{function_name}-ExecutionPolicy": iam_.PolicyDocument(
                    statements=[
                        iam_.PolicyStatement(
                            actions=[
                                "dynamodb:PutItem",
                            ],
                            effect=iam_.Effect.ALLOW,
                            resources=[table_arn],
                        ),
                        iam_.PolicyStatement(
                            actions=[
                                "ssm:GetParameter",
                            ],
                            effect=iam_.Effect.ALLOW,
                            resources=[
                                f"arn:aws:ssm:{self.region}:{self.account}:parameter{client_id_key}",
                                f"arn:aws:ssm:{self.region}:{self.account}:parameter{client_secret_key}",
                            ],
                        ),
                    ]
                )
            },
            managed_policies=[
                iam_.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
                # iam_.ManagedPolicy.from_aws_managed_policy_name("AWSXrayWriteOnlyAccess"),
            ],
            role_name=role_name,
        )
