import boto3
import json

dynamodb = boto3.resource("dynamodb", region_name= "us-east-1")

login_table = dynamodb.Table("login")

def lambda_handler(event, context):
    body = json.loads(event["body"])
    email = body.get("email")
    password = body.get("password")

    response = login_table.get_item(Key={"email": email})
    item = response.get("Item")

    if not item:
        return {
            "statusCode": 401,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"success": False, "message": "email or password is invalid"})
        }
    
    if item["password"] != password:
        return {
            "statusCode": 401,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"success": False, "message": "email or password is invalid"})
        }
    
    return {
        "statusCode": 200,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"success": True, "user_name": item["user_name"], "email": email})
    }



