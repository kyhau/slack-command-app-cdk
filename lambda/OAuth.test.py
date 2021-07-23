"""
Unit tests for OAuth.py
"""
import json
import os
import unittest
from dataclasses import dataclass
from unittest.mock import patch

os.environ["SlackAppClientIdParameterKey"] = "/apps/slack_app/dummy/client_id"
os.environ["SlackAppClientSecretParameterKey"] = "/apps/slack_app/dummy/client_secret"
os.environ["SlackAppOAuthDynamoDBTable"] = "DummyTable"
os.environ["SlackChannelIds"] = "AAAAAAAAAAA,BBBBBBBBBBB"
os.environ["SlackTeamIds"] = "TA1111111,TA2222222"

func = __import__("OAuth")

MOCK_CLIENT_CREDENTIALS = "test-client-id", "test-client-secret"


def mock_event(code="test_code"):
    return {
        "queryStringParameters": {
            "code": code,
        }
    }


@dataclass
class HttpResponse:
    data: str = None
    status: int = 200


def mock_http_response(status=200, ok=True, team_id=None, channel_id=None):
    data = {
        "ok": ok,
        "team": {"id": team_id if team_id else "TA1111111"},
        "incoming_webhook": {"channel_id": channel_id if channel_id else "AAAAAAAAAAA"},
    }
    if ok is False:
        data["error"] = "some error"
    return HttpResponse(json.dumps(data).encode(), status)


class TestFunction(unittest.TestCase):

    def test_lambda_handler_no_auth_code(self):
        ret = func.lambda_handler(mock_event(None), None)
        self.assertEqual(ret, {'body': '"Error: The required code is missing."', 'statusCode': 500})

    def test_lambda_handler_all_good(self):
        with patch("OAuth.client_credentials", return_value=MOCK_CLIENT_CREDENTIALS), \
             patch("urllib3.PoolManager.request") as mock_http_request, \
             patch("OAuth.table.put_item") as mock_table_put_item:

            mock_http_request.return_value = mock_http_response(200)

            ret = func.lambda_handler(mock_event(), None)

            mock_http_request.assert_called_once_with(
                'POST',
                'https://slack.com/api/oauth.v2.access?code=test_code&client_id=test-client-id&client_secret=test-client-secret',
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            mock_table_put_item.assert_called_once()

            self.assertEqual(ret, {'body': '"Installation request accepted and registration completed."', 'statusCode': 200})

    def test_lambda_handler_oauth2_failed(self):
        with patch("OAuth.client_credentials", return_value=MOCK_CLIENT_CREDENTIALS), \
             patch("urllib3.PoolManager.request") as mock_http_request, \
             patch("OAuth.table.put_item") as mock_table_put_item:

            mock_http_request.return_value = mock_http_response(200, ok=False)

            ret = func.lambda_handler(mock_event(), None)

            mock_http_request.assert_called_once_with(
                'POST',
                'https://slack.com/api/oauth.v2.access?code=test_code&client_id=test-client-id&client_secret=test-client-secret',
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            mock_table_put_item.assert_not_called()

            self.assertEqual(ret, {'body': '"some error"', 'statusCode': 500})

    def test_lambda_handler_invalid_team_id(self):
        with patch("OAuth.client_credentials", return_value=MOCK_CLIENT_CREDENTIALS), \
             patch("urllib3.PoolManager.request") as mock_http_request, \
             patch("OAuth.table.put_item") as mock_table_put_item:

            mock_http_request.return_value = mock_http_response(200, team_id="TA3333333")

            ret = func.lambda_handler(mock_event(), None)

            mock_http_request.assert_called_once_with(
                'POST',
                'https://slack.com/api/oauth.v2.access?code=test_code&client_id=test-client-id&client_secret=test-client-secret',
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            mock_table_put_item.assert_not_called()

            self.assertEqual(ret, {'body': '"Error: Installation forbidden. Please contact the app owner."', 'statusCode': 403})

    def test_lambda_handler_invalid_channel_id(self):
        with patch("OAuth.client_credentials", return_value=MOCK_CLIENT_CREDENTIALS), \
             patch("urllib3.PoolManager.request") as mock_http_request, \
             patch("OAuth.table.put_item") as mock_table_put_item:

            mock_http_request.return_value = mock_http_response(200, channel_id="CCCCCCCCCCC")

            ret = func.lambda_handler(mock_event(), None)

            mock_http_request.assert_called_once_with(
                'POST',
                'https://slack.com/api/oauth.v2.access?code=test_code&client_id=test-client-id&client_secret=test-client-secret',
                headers={'Content-Type': 'application/x-www-form-urlencoded'}
            )

            mock_table_put_item.assert_not_called()

            self.assertEqual(ret, {'body': '"Error: Installation forbidden. Please contact the app owner."', 'statusCode': 403})


if __name__ == "__main__":
    unittest.main()
