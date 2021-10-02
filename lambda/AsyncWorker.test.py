"""
Unit tests for AsyncWorker.py
"""
import unittest
from unittest.mock import patch

func = __import__("AsyncWorker")


def mock_event(text_value=""):
    return {
        "channel_name": ["test_channel"],
        "command": ["/slack-unittest"],
        "user_name": ["test_user_namee"],
        "user_id": ["test_user_id"],
        "text": [text_value],
        "response_url": ["test_url"],
    }


class TestFunction(unittest.TestCase):
    def test_lambda_handler(self):
        with patch("AsyncWorker.post_response_to_slack") as mock_post:
            ret = func.lambda_handler(mock_event(text_value="async"), None)
            mock_post.assert_called_once_with(
                "test_url",
                "<@test_user_id> invoked `/slack-unittest` in test_channel with the following text: `async`"
            )
            self.assertEqual(ret, {"statusCode": 200})


if __name__ == "__main__":
    unittest.main()
