"""
Unit tests for ImmediateResponse.py
"""
import os
import unittest
from unittest.mock import patch

os.environ["SlackAppId"] = "APIID123456"
os.environ["SlackChannelIds"] = "C1111111111,C2222222222"
os.environ["SlackCommand"] = "/slack-unittest"
os.environ["SlackDomains"] = "companya,companyb"
os.environ["SlackTeamIds"] = "T1111111111,T2222222222"
os.environ["SlackVerificationTokenParameterKey"] = "/apps/slack_app/dummy/token"
os.environ["AsyncWorkerLambdaFunctionName"] = "Dummy-AsyncWorker"
os.environ["SyncWorkerLambdaFunctionName"] = "Dummy-SyncWorker"

func = __import__("ImmediateResponse")


def mock_input_data(custom_data={}):
    data = {
        "api_app_id": ["APIID123456"],
        "channel_id": ["C1111111111"],
        "channel_name": ["dummy-channel-a"],
        "command": ["/slack-unittest"],
        "response_url": ["dummy-url"],
        "team_domain": ["companya"],
        "team_id": ["T1111111111"],
        "text": ["help"],
        "token": ["dummy-token"],
        "user_id": ["dummy-user-id-a"],
        "user_name": ["dummy-user-name-a"],
    }
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
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "dummy-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs, \
             patch("ImmediateResponse.lambda_client.invoke") as mock_lambda_invoke:

            mock_parse_qs.return_value = mock_input_data(custom_data={"text": ["async"]})
            mock_lambda_invoke.return_value = MOCK_LAMBDA_INVOKE_RESPONSE

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("Processing request from <@dummy-user-id-a> on dummy-channel-a: /slack-unittest async"))

    def test_lambda_handler_failed_no_token(self):
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "dummy-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs:

            mock_parse_qs.return_value = mock_input_data({"token": [None]})

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("Sorry <@dummy-user-id-a>, an authentication error occurred. Please contact your admin."))

    def test_lambda_handler_failed_invalid_team_domain(self):
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "dummy-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs:

            mock_parse_qs.return_value = mock_input_data({"team_domain": ["companyc"]})

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("Sorry <@dummy-user-id-a>, this app does not support this team domain companyc."))

    def test_lambda_handler_failed_invalid_team_id(self):
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "dummy-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs:

            mock_parse_qs.return_value = mock_input_data({"team_id": ["TA3333333"]})

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("Sorry <@dummy-user-id-a>, this app does not support this team ID TA3333333."))

    def test_lambda_handler_failed_invalid_channel_id(self):
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "dummy-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs:

            mock_parse_qs.return_value = mock_input_data({"channel_id": ["CCCCCCCCCCC"]})

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("Sorry <@dummy-user-id-a>, this app does not support this channel ID CCCCCCCCCCC."))

    def test_lambda_handler_failed_invalid_command(self):
        with patch("ImmediateResponse.ssm_client.get_parameter", return_value={"Parameter": {"Value": "dummy-token"}}), \
             patch("ImmediateResponse.parse_qs") as mock_parse_qs:

            mock_parse_qs.return_value = mock_input_data({"command": ["/dummy-invalid-command"]})

            ret = func.lambda_handler(mock_event(), None)

            self.assertDictEqual(ret, mock_response("<@dummy-user-id-a>, this app does not support `/dummy-invalid-command help`."))


if __name__ == "__main__":
    unittest.main()
