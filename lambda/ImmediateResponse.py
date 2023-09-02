"""
ImmediateResponse aims to do
- authentication and authorization,
- invoke AsyncWorker or SyncWorker
- return an immedate response to caller within 3 seconds
"""
import json
import logging
import os
from urllib.parse import parse_qs

import boto3

logging.getLogger().setLevel(logging.INFO)

SLACK_APP_ID = os.environ.get("SlackAppId")
SLACK_CHANNEL_IDS = list(map(str.strip, os.environ.get("SlackChannelIds", "").split(",")))
SLACK_COMMAND = os.environ.get("SlackCommand")
SLACK_TEAM_IDS = list(map(str.strip, os.environ.get("SlackTeamIds", "").split(",")))
SLACK_TEAM_DOMAINS = list(map(str.strip, os.environ.get("SlackDomains", "").split(",")))
SLACK_VERIFICATION_TOKEN_SSM_PARAMETER_KEY = os.environ.get("SlackVerificationTokenParameterKey")

CHILD_ASYNC_FUNCTION_NAME = os.environ.get("AsyncWorkerLambdaFunctionName", "AsyncWorker")
CHILD_SYNC_FUNCTION_NAME = os.environ.get("SyncWorkerLambdaFunctionName", "SyncWorker")
IS_AWS_SAM_LOCAL = os.environ.get("AWS_SAM_LOCAL") == "true"
TARGET_REGION = os.environ.get("AWS_REGION", "ap-southeast-2")

lambda_client = boto3.client("lambda", region_name=TARGET_REGION)
ssm_client = boto3.client("ssm", region_name=TARGET_REGION)


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
        expected_token = ssm_client.get_parameter(
            Name=SLACK_VERIFICATION_TOKEN_SSM_PARAMETER_KEY, WithDecryption=True
        )["Parameter"]["Value"]
    except Exception as e:
        logging.error(f"Unable to retrieve data from parameter store: {e}")
        return False

    if token != expected_token:
        logging.error(f"Request token ({token}) does not match expected")
        return False

    return True


def authorize(app_id, channel_id, team_id, team_domain):
    """Just double check if this app is invoked from the expected app/channel/team"""

    if app_id != SLACK_APP_ID:
        return f"app ID {app_id}"

    if team_id not in SLACK_TEAM_IDS:
        return f"team ID {team_id}"

    if team_domain not in SLACK_TEAM_DOMAINS:
        return f"team domain {team_domain}"

    if channel_id not in SLACK_CHANNEL_IDS:
        return f"channel ID {channel_id}"


def invoke_lambda(function_namme, payload_json, is_async):
    payload_str = json.dumps(payload_json)
    payload_bytes_arr = bytes(payload_str, encoding="utf8")
    return lambda_client.invoke(
        FunctionName=function_namme,
        InvocationType="Event" if is_async else "RequestResponse",
        Payload=payload_bytes_arr,
    )


def lambda_handler(event, context):
    event_body = event.get("body")
    logging.info(f"Received event[body]: {event_body}")

    params = parse_qs(event_body)
    app_id = params["api_app_id"][0]
    channel_id = params["channel_id"][0]
    team_domain = params["team_domain"][0]
    team_id = params["team_id"][0]
    user_id = params["user_id"][0]

    if authenticate(params["token"][0]) is False:
        return respond(
            f"Sorry <@{user_id}>, an authentication error occurred. Please contact your admin."
        )

    result = authorize(app_id, channel_id, team_id, team_domain)
    if result is not None:
        return respond(f"Sorry <@{user_id}>, this app does not support this {result}.")

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
                message = (
                    f"Processing request from <@{user_id}> on {channel}: {command} {command_text}"
                )
            else:
                try:
                    payload = json.loads(resp["Payload"].read().decode("utf-8"))["body"]
                    message = f"<@{user_id}>: {command} {command_text}\n{payload}"
                except Exception as e:
                    logging.error(
                        f"Failed to retrieve response from sync lambda {function_name}: {e}"
                    )

        if message is None:
            logging.error(resp)
            message = (
                f"<@{user_id}>, your request on {channel} `{command} {command_text}` cannot be"
                + " processed at the moment. Please try again later."
            )

    if message is None:
        message = f"<@{user_id}>, this app does not support `{command} {command_text}`."

    return respond(message)
