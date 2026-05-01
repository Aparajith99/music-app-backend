import boto3
import json

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
login_table = dynamodb.Table("login")

def lambda_handler(event, context):
    body = json.loads(event["body"])
    email = body.get("email")
    username = body.get("username")
    password = body.get("password")
    
    response = login_table.get_item(Key={"email": email})
    item = response.get("Item")
    
    if item:
        return {
            "statusCode": 400,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"success": False, "message": "The email already exists"})
        }
    
    login_table.put_item(Item={
        "email": email,
        "user_name": username,
        "password": password
    })
    
    return {
        "statusCode": 201,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"success": True})
    }

