import json
import logging
import os
from urllib.parse import parse_qs

import boto3

logging.getLogger().setLevel(logging.INFO)

CHANNEL_IDS = list(map(str.strip, os.environ.get("SlackChannelIds", "").split(",")))
TEAM_DOMAINS = list(map(str.strip, os.environ.get("SlackDomains", "").split(",")))
TEAM_IDS = list(map(str.strip, os.environ.get("SlackTeamIds", "").split(",")))

CHILD_ASYNC_FUNCTION_NAME = os.environ.get("AsyncWorkerLambdaFunctionName", "AsyncWorker")
CHILD_SYNC_FUNCTION_NAME = os.environ.get("SyncWorkerLambdaFunctionName", "SyncWorker")
PARAMETER_KEY = os.environ.get("SlackAppTokenParameterKey")
SLACK_COMMAND = os.environ.get("SlackCommand", "/testcdk")
IS_AWS_SAM_LOCAL = os.environ.get("AWS_SAM_LOCAL") == "true"

lambda_client = boto3.client("lambda", region_name=os.environ.get("AWS_REGION", "ap-southeast-2"))
ssm_client = boto3.client("ssm", region_name=os.environ.get("AWS_REGION", "ap-southeast-2"))


def respond(message):
    logging.info(message)
    resp = {
        "response_type": "in_channel",  # visible to all channel members
        "text": message,
    }
    return {
        "body": json.dumps(resp),
        "headers": {
            "Content-Type": "application/json",
        },
        "statusCode": "200",
    }


def authenticate(token):
    """Verify the token passed in"""
    if IS_AWS_SAM_LOCAL is True:
        return True

    try:
        expected_token = ssm_client.get_parameter(Name=PARAMETER_KEY, WithDecryption=True)["Parameter"]["Value"]
    except Exception as e:
        logging.error(f"Unable to retrieve data from parameter store: {e}")
        return False

    if token != expected_token:
        logging.error(f"Request token ({token}) does not match expected")
        return False

    return True


def authorize(params):
    """Just double check if this app is invoked from the expected domain channel"""

    team_domain, team_id = params["team_domain"][0], params["team_id"][0]
    if team_id not in TEAM_IDS or team_domain not in TEAM_DOMAINS:
        return f"domain {team_domain} {team_id}"

    channel_id, channel_name = params["channel_id"][0], params["channel_name"][0]
    if channel_id not in CHANNEL_IDS:
        return f"{channel_name} channel"


def invoke_lambda(function_namme, payload_json, is_async):
    payload_str = json.dumps(payload_json)
    payload_bytes_arr = bytes(payload_str, encoding="utf8")
    return lambda_client.invoke(
        FunctionName=function_namme,
        InvocationType="Event" if is_async else "RequestResponse",
        Payload=payload_bytes_arr
    )


def lambda_handler(event, context):
    logging.info(json.dumps(event.get("body", {}), indent=2))
    params = parse_qs(event["body"])
    user_id = params["user_id"][0]

    if authenticate(params["token"][0]) is False:
        return respond(f"Sorry <@{user_id}>, an authentication error occurred. Please contact your admin.")

    result = authorize(params)
    if result is not None:
        return respond(f"Sorry <@{user_id}>, this app does not support the {result}.")

    user = params["user_name"][0]
    command = params["command"][0]
    channel = params["channel_name"][0]
    command_text = params.get("text", [None])[0]
    logging.info(f"{user} invoked {command} in {channel} with the following text: {command_text}")

    message = None

    if command == SLACK_COMMAND and command_text:
        # Remove sensitive data in payload before passing to other functions
        payload = {k: v for k, v in params.items() if k not in ["token", "trigger_id"]}

        mode = command_text.split(" ")[0]
        is_async = mode.lower() == "async"

        function_name = CHILD_ASYNC_FUNCTION_NAME if is_async is True else CHILD_SYNC_FUNCTION_NAME

        resp = invoke_lambda(function_name, payload, is_async)
        if resp["ResponseMetadata"]["HTTPStatusCode"] in [200, 201, 202]:
            if is_async:
                message = f"Processing request from <@{user_id}> on {channel}: {command} {command_text}"
            else:
                try:
                    payload = json.loads(resp["Payload"].read().decode("utf-8"))["body"]
                    message = f"<@{user_id}>: {command} {command_text}\n{payload}"
                except Exception as e:
                    logging.error(f"Failed to retrieve response from sync lambda {function_name}: {e}")

        if message is None:
            logging.error(resp)
            message = f"<@{user_id}>, your request on {channel} `{command} {command_text}` cannot be" \
                      + " processed at the moment. Please try again later."

    if message is None:
        message = f"<@{user_id}>, this app does not support `{command} {command_text}`."

    return respond(message)
