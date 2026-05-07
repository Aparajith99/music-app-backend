import boto3
import json

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
subscriptions_table = dynamodb.Table("subscriptions")

def lambda_handler(event, context):
    body = json.loads(event["body"])
    email = body.get("email")
    artist = body.get("artist")
    title = body.get("title")
    year = body.get("year")
    album = body.get("album")
    image_url = body.get("image_url")
    title_year = f"{title}#{year}"
    
    subscriptions_table.put_item(Item={
        "email": email,
        "title_year": title_year,
        "artist": artist,
        "title": title,
        "year": year,
        "album": album,
        "image_url": image_url
    })
    
    return {
        "statusCode": 201,
        "headers": {"Access-Control-Allow-Origin": "*"},
        "body": json.dumps({"success": True})
    }
