"""
For processing requests that will take longer than 3 seconds to process.
"""
import json
import logging

import urllib3

logging.getLogger().setLevel(logging.INFO)

http = urllib3.PoolManager()


def post_response_to_slack(response_url, message):
    data = {
        "replace_original": "false",
        "response_type": "in_channel",    # visible to all channel members
        "text": message,
    }
    encoded_data = json.dumps(data).encode("utf-8")
    resp = http.request("POST", response_url, body=encoded_data, headers={"Content-Type": "application/json"})
    logging.info(resp.read())


def lambda_handler(event, context):
    logging.info(json.dumps(event, indent=2))
    user_id = event["user_id"][0]
    command = event["command"][0]
    channel = event["channel_name"][0]
    command_text = event.get("text", [None])[0]
    response_url = event.get("response_url")[0]

    message = f"<@{user_id}> invoked `{command}` in {channel} with the following text: `{command_text}`"
    logging.info(message)

    post_response_to_slack(response_url, message)

    return {
        "statusCode": 200,
    }
