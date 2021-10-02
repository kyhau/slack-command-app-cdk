"""
Unit tests for ImmediateResponse.py
"""
import os
import unittest
from unittest.mock import patch

os.environ["SlackChannelIds"] = "AAAAAAAAAAA,BBBBBBBBBBB"
os.environ["SlackDomains"] = "companya,companyb"
os.environ["SlackTeamIds"] = "TA1111111,TA2222222"
os.environ["SlackAppTokenParameterKey"] = "/apps/slack_app/dummy/token"
os.environ["AsyncWorkerLambdaFunctionName"] = "Dummy-AsyncWorker"
os.environ["SlackCommand"] = "/slack-unittest"

func = __import__("ImmediateResponse")


def mock_input_data(custom_data=None):
    data = {
        "channel_id": ["AAAAAAAAAAA"],
        "channel_name": ["test-channel-a"],
        "command": ["/slack-unittest"],
        "team_domain": ["companya"],
        "team_id": ["TA1111111"],
        "text": ["help"],
        "token": ["test-token"],
        "user_id": ["test-user-id-a"],
        "user_name": ["test-user-name-a"],
    }
    if custom_data:
        data.update(custom_data)
    return data


def mock_event():
    return {
        "body": mock_input_data()
    }


MOCK_LAMBDA_INVOKE_RESPONSE = {
    "ResponseMetadata": {
        "HTTPStatusCode": 200,
    }
}


def mock_response(message):
    return {
        "body": '{"response_type": "in_channel", "text": "' + message + '"}',
        "headers": {"Content-Type": "application/json"},
        "statusCode": "200",
    }


class TestFunction(unittest.TestCase):

    def test_lambda_handler_async_all_good(self):
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "test-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs, \
             patch("ImmediateResponse.lambda_client.invoke") as mock_lambda_invoke:

            mock_parse_qs.return_value = mock_input_data(custom_data={"text": ["async"]})
            mock_lambda_invoke.return_value = MOCK_LAMBDA_INVOKE_RESPONSE

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("Processing request from <@test-user-id-a> on test-channel-a: /slack-unittest async"))

    def test_lambda_handler_failed_no_token(self):
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "test-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs:

            mock_parse_qs.return_value = mock_input_data({"token": [None]})

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("Sorry <@test-user-id-a>, an authentication error occurred. Please contact your admin."))

    def test_lambda_handler_failed_invalid_team_domain(self):
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "test-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs:

            mock_parse_qs.return_value = mock_input_data({"team_domain": ["companyc"]})

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("Sorry <@test-user-id-a>, this app does not support the domain companyc TA1111111."))

    def test_lambda_handler_failed_invalid_team_id(self):
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "test-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs:

            mock_parse_qs.return_value = mock_input_data({"team_id": ["TA3333333"]})

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("Sorry <@test-user-id-a>, this app does not support the domain companya TA3333333."))

    def test_lambda_handler_failed_invalid_channel_id(self):
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "test-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs:

            mock_parse_qs.return_value = mock_input_data({"channel_id": ["CCCCCCCCCCC"]})

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("Sorry <@test-user-id-a>, this app does not support the test-channel-a channel."))

    def test_lambda_handler_failed_invalid_command(self):
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "test-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs:

            mock_parse_qs.return_value = mock_input_data({"command": ["/test-invalid-command"]})

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("<@test-user-id-a>, this app does not support `/test-invalid-command help`."))


if __name__ == "__main__":
    unittest.main()
