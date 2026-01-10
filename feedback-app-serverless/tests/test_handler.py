import sys
import json

# Tell Python where the Lambda code is
sys.path.append("feedback-app-serverless/lambda/feedback_handler")

from app import lambda_handler


def test_lambda_handler_success():
    event = {
        "body": json.dumps({
            "name": "Test",
            "email": "test@test.com",
            "message": "Hello"
        })
    }

    response = lambda_handler(event, None)
