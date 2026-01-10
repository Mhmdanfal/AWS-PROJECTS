import sys
import json
from pathlib import Path

# Add lambda directory to Python path
sys.path.append(str(Path(__file__).resolve().parents[1] / "lambda"))

from app import lambda_handler


def test_missing_fields():
    event = {"body": "{}"}
    response = lambda_handler(event, None)
    assert response["statusCode"] == 400
