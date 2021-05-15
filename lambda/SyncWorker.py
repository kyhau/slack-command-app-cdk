"""
For processing requests that will take less than 3 seconds to process.
"""
import json
import logging

logging.getLogger().setLevel(logging.INFO)


def lambda_handler(event, context):
    user_id = event["user_id"][0]
    command = event["command"][0]
    channel = event["channel_name"][0]
    command_text = event.get("text", [None])[0]
    response_url = event.get("response_url")[0]

    message = f"Processed <@{user_id}> {command} by sync worker."
    logging.info(message)

    return {
        "body": message,
        "statusCode": 200,
    }
