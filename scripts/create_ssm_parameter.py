import logging

from boto3.session import Session

logging.getLogger().setLevel(logging.INFO)

#key_id = "TODO The KMS Key ID"
parameter_key = "/apps/slack_app/k_cdk/token"
slack_app_name = "K-CDK-SlackApp"
token = "TODO The Slack App Token"

session = Session(profile_name="default")

resp = session.client("ssm").put_parameter(
    Name=parameter_key,
    Description=f"{slack_app_name} Token",
    Value=token,
    Type="SecureString",
    #KeyId=key_id,
    Tags=[
        {
            "Key": "Billing",
            "Value": slack_app_name,
        }
    ],
)

print(resp)
