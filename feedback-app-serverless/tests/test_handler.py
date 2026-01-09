import json
from lambda.feedback_handler.app import lambda_handler

def test_lambda_handler_success():
    event = {
        "body": json.dumps({
            "name": "Test",
            "email": "test@test.com",
            "message": "Hello"
        })
    }

    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
