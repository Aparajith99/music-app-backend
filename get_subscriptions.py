import boto3
import json

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
subscriptions_table = dynamodb.Table("subscriptions")
s3 = boto3.client("s3", region_name="us-east-1")
BUCKET = "music-app-images-816553836520"

def lambda_handler(event, context):
    email = event["pathParameters"]["email"]
    response = subscriptions_table.query(
        KeyConditionExpression="email = :email",
        ExpressionAttributeValues={":email": email}
    )
    items = response.get("Items", [])
    for item in items:
        filename = item["image_url"].split("/")[-1]
        item["image_url"] = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": filename},
            ExpiresIn=3600
        )
    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"success": True, "items": items})
    }
