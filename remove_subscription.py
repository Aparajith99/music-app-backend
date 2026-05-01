import boto3
import json

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
subscriptions_table = dynamodb.Table("subscriptions")

def lambda_handler(event, context):
    email = event["pathParameters"]["email"]
    title_year = event["pathParameters"]["title_year"]
    
    subscriptions_table.delete_item(
        Key={
            "email": email,
            "title_year": title_year
        }
    )
    
    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"success": True})
    }
