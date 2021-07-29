"""
Perform OAuth 2.0 flow and turn the auth code into access token then store it in a DynamoDB table.

For details of Slack OAuth 2.0 v2 see
- https://api.slack.com/authentication/oauth-v2
- https://api.slack.com/methods/oauth.v2.access
"""
import json
import logging
import os
from datetime import datetime
from urllib.parse import urlencode

import boto3
import urllib3

logging.getLogger().setLevel(logging.INFO)
logging.getLogger("botocore").setLevel(logging.CRITICAL)
logging.getLogger("boto3").setLevel(logging.CRITICAL)
logging.getLogger("urllib3.connectionpool").setLevel(logging.CRITICAL)

CLIENT_ID_PARAMETER_KEY = os.environ.get("SlackAppClientIdParameterKey")
CLIENT_SECRET_PARAMETER_KEY = os.environ.get("SlackAppClientSecretParameterKey")
DDB_TABLE_NAME = os.environ.get("SlackAppOAuthDynamoDBTable")
CHANNEL_IDS = list(map(str.strip, os.environ.get("SlackChannelIds", "").split(",")))
TEAM_IDS = list(map(str.strip, os.environ.get("SlackTeamIds", "").split(",")))
IS_AWS_SAM_LOCAL = os.environ.get("AWS_SAM_LOCAL") == "true"
SLACK_OAUTH_V2_URL = "https://slack.com/api/oauth.v2.access"

http = urllib3.PoolManager()
table = boto3.resource("dynamodb", region_name=os.environ.get("AWS_REGION", "ap-southeast-2")).Table(DDB_TABLE_NAME)


def retrieve_client_credentials():
    try:
        ssm_client = boto3.client("ssm")
        v1 = ssm_client.get_parameter(Name=CLIENT_ID_PARAMETER_KEY, WithDecryption=True)["Parameter"]["Value"]
        v2 = ssm_client.get_parameter(Name=CLIENT_SECRET_PARAMETER_KEY, WithDecryption=True)["Parameter"]["Value"]
        return v1, v2
    except Exception as e:
        if IS_AWS_SAM_LOCAL is False:
            logging.error(e)
    return None, None


CLIENT_ID, CLIENT_SECRET = retrieve_client_credentials()


def client_credentials():
    """Return CLIENT_ID, CLIENT_SECRET. Defined for mocking CLIENT_ID, CLIENT_SECRET content"""
    return CLIENT_ID, CLIENT_SECRET


def authorize(response_data):
    """Check if app is invoked from the expected domain channel"""
    try:
        team_id = response_data["team"]["id"]
        channel_id = response_data["incoming_webhook"]["channel_id"]

        if team_id in TEAM_IDS and channel_id in CHANNEL_IDS:
            return True

    except Exception as e:
        logging.error(f"Failed to do authorization check: {e}")

    return False


def put_data_to_dynamodb(response_data):
    try:
        data = {"request_utc": datetime.utcnow().isoformat()}  # Add current timestamp
        for k, v in response_data.items():
            if isinstance(v, dict):
                for k2, v2 in v.items():
                    data[f"{k}_{k2}"] = v2
            elif k not in ["ok"]:
                data[k] = v

        table.put_item(
            TableName=DDB_TABLE_NAME,
            Item=data
        )
    except Exception as e:
        logging.error(e)


def lambda_handler(event, context):
    logging.info(json.dumps(event))

    auth_code = event.get("queryStringParameters", {}).get("code")
    logging.info(auth_code)

    if auth_code:
        # Turn the auth code into access token

        client_id, client_secret = client_credentials()
        data = {
            "code": auth_code,
            "client_id": client_id,
            "client_secret": client_secret,
        }
        encoded_args = urlencode(data)
        url = f"{SLACK_OAUTH_V2_URL}?{encoded_args}"
        resp = http.request("POST", url, headers={"Content-Type": "application/x-www-form-urlencoded"})

        status = resp.status
        resp_data = json.loads(resp.data.decode("utf-8"))
        logging.info(resp_data)

        if resp_data.get("ok", False) is True:
            if authorize(resp_data):
                message = "Installation request accepted and registration completed."
                put_data_to_dynamodb(resp_data)
            else:
                status = 403  # Forbidden
                message = "Error: Installation forbidden. Please contact the app owner."
        else:
            status = 500
            message = resp_data.get("error")

    else:
        status = 500
        message = "Error: The required code is missing."

    return {
        "statusCode": status,
        "body": json.dumps(message),
    }
