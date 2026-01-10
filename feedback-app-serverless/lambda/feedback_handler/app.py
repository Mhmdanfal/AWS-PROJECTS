import boto3
import json
import os
import uuid
from datetime import datetime, timezone


from botocore.exceptions import ClientError

def lambda_handler(event, context):
    """Main Lambda handler for receiving feedback."""

    # Initialize AWS clients INSIDE handler
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["TABLE_NAME"])

    sns = boto3.client("sns")
    SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

    try:
        body_str = event.get("body", "")
        data = json.loads(body_str or "{}") if isinstance(body_str, str) else body_str
    except json.JSONDecodeError:
        return build_response(400, {"error": "Invalid JSON"})

    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    if not name or not email or not message:
        return build_response(400, {"error": "name, email, and message are required"})

    item_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    item = {
        "id": item_id,
        "name": name,
        "email": email,
        "message": message,
        "created_at": created_at,
    }

    try:
        table.put_item(Item=item)

        sns_message = (
            f"New feedback received:\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Message: {message}\n"
            f"Time: {created_at}\n"
            f"ID: {item_id}"
        )

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="New Feedback Submission",
            Message=sns_message,
        )

        return build_response(200, {"status": "ok", "id": item_id})

    except ClientError as e:
        print("Error:", e)
        return build_response(500, {"error": "Internal server error"})
