import boto3

AWS_REGION = "ap-southeast-2"
DATA = {
    "verification_token": None,  # Slack Verification Token
    "client_id": None,  # optional: required for deploying K-CDK-SlackCommandAppSharing for app sharing with oauth 2.0
    "client_secret": None,  # optional: required for deploying K-CDK-SlackCommandAppSharing for app sharing with oauth 2.0
}
SLACK_APP_NAME = "K-CDK-SlackCommandApp"
PARAMETER_KEY_PREFIX = "/apps/slack_app/k_cdk_slack_command_app"
# key_id = "TODO The KMS Key ID (optional)"


def create_parameter(name, value):
    resp = boto3.client("ssm", region_name=AWS_REGION).put_parameter(
        Name=f"{PARAMETER_KEY_PREFIX}/{name}",
        Description=f"{SLACK_APP_NAME} {name}",
        Value=value,
        Type="SecureString",
        # KeyId=key_id,
        Tags=[
            {
                "Key": "Billing",
                "Value": SLACK_APP_NAME,
            }
        ],
    )
    print(resp)


for key, value in DATA.items():
    if value:
        create_parameter(key, value)
