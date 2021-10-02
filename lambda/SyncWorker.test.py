"""
Unit tests for SyncWorker.py
"""
import unittest

func = __import__("SyncWorker")


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
        ret = func.lambda_handler(mock_event(text_value="sync"), None)
        self.assertEqual(
            ret,
            {
                "body": "Processed <@test_user_id> `/slack-unittest sync` by SyncWorker.",
                "statusCode": 200
            }
        )


if __name__ == "__main__":
    unittest.main()
