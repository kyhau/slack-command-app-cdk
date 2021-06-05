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

ssm_client = boto3.client("ssm")
CLIENT_ID = ssm_client.get_parameter(Name=CLIENT_ID_PARAMETER_KEY, WithDecryption=True)["Parameter"]["Value"]
CLIENT_SECRET = ssm_client.get_parameter(Name=CLIENT_SECRET_PARAMETER_KEY, WithDecryption=True)["Parameter"]["Value"]

SLACK_OAUTH_V2_URL = "https://slack.com/api/oauth.v2.access"

table = boto3.resource("dynamodb").Table(DDB_TABLE_NAME)
http = urllib3.PoolManager()


def put_data_to_dynamodb(response_data):
    try:
        data = {"request_utc": datetime.utcnow().isoformat()}
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
        data = {
            "code": auth_code,
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
        }
        encoded_args = urlencode(data)
        url = f"{SLACK_OAUTH_V2_URL}?{encoded_args}"
        resp = http.request("POST", url, headers={"Content-Type": "application/x-www-form-urlencoded"})

        status = resp.status
        resp_data = json.loads(resp.data.decode("utf-8"))
        logging.info(resp_data)

        if resp_data.get("ok", False):
            message = "succeeded"
            put_data_to_dynamodb(resp_data)
        else:
            status = 500
            message = resp_data.get("error")

    else:
        status = 500
        message = "Error: Looks like we are not getting code."

    return {
        "statusCode": status,
        "body": json.dumps(message),
    }
