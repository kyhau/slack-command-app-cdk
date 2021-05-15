import json
import logging
import os
from urllib.parse import parse_qs

import boto3

logging.getLogger().setLevel(logging.INFO)

CHILD_ASYNC_FUNCTION_NAME = os.environ.get("AsyncWorkerLambdaFunctionName", "AsyncWorker")
CHILD_SYNC_FUNCTION_NAME = os.environ.get("SyncWorkerLambdaFunctionName", "SyncWorker")
PARAMETER_KEY = os.environ.get("SlackAppTokenParameterKey")
SLACK_COMMAND = os.environ.get("SlackCommand", "/testcdk")
IS_AWS_SAM_LOCAL = os.environ.get("AWS_SAM_LOCAL") == "true"
SLACK_TOKEN = boto3.client("ssm").get_parameter(Name=PARAMETER_KEY, WithDecryption=True)["Parameter"]["Value"]
lambda_client = boto3.client("lambda")


def respond(message):
    logging.info(message)
    resp = {
        "response_type": "in_channel",    # visible to all channel members
        "text": message,
    }
    return {
        "body": json.dumps(resp),
        "headers": {
            "Content-Type": "application/json",
        },
        "statusCode": "200",
    }


def invoke_lambda(function_namme, payload_json, is_async):
    payload_str = json.dumps(payload_json)
    payload_bytes_arr = bytes(payload_str, encoding="utf8")
    return lambda_client.invoke(
        FunctionName=function_namme,
        InvocationType="Event" if is_async else "RequestResponse",
        Payload=payload_bytes_arr
    )


def lambda_handler(event, context):
    params = parse_qs(event["body"])
    user_id = params["user_id"][0]

    # Authentication and authorization
    # Note that you may also compare api_app_id, team_domain, channel_id, channel_name etc.
    token = params["token"][0]
    if token != SLACK_TOKEN and IS_AWS_SAM_LOCAL is False:
        logging.error(f"Request token ({token}) does not match expected.")
        return respond(f"@<{user_id}> Invalid request token. Please contact your admin.")

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
            message = f"<@{user_id}>, your request on {channel} ({command} {command_text}) cannot be" \
                      + " processed at the moment. Please try again later."

    if message is None:
        message = f"@<{user_id}>, I do not support {command} {command_text}."

    return respond(message)
