import sys
import json

sys.path.append("feedback-app-serverless/lambda/feedback_handler")

from app import lambda_handler


def test_missing_fields():
    event = {"body": "{}"}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
