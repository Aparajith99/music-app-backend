import boto3
import json

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
music_table = dynamodb.Table("music")
s3 = boto3.client("s3", region_name="us-east-1")
BUCKET = "music-app-images-816553836520"

def lambda_handler(event, context):
    params = event.get("queryStringParameters") or {}
    title = params.get("title")
    artist = params.get("artist")
    year = params.get("year")
    album = params.get("album")
    filter_expression = []
    expression_values = {}
    expression_names = {}
    if title:
        filter_expression.append("contains(#t, :title)")
        expression_values[":title"] = title
        expression_names["#t"] = "title"
    if artist:
        filter_expression.append("contains(#a, :artist)")
        expression_values[":artist"] = artist
        expression_names["#a"] = "artist"
    if year:
        filter_expression.append("#y = :year")
        expression_values[":year"] = year
        expression_names["#y"] = "year"
    if album:
        filter_expression.append("contains(#al, :album)")
        expression_values[":album"] = album
        expression_names["#al"] = "album"
    if not filter_expression:
        return {
            "statusCode": 400,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"success": False, "message": "No result is retrieved. Please query again"})
        }
    filter_str = " AND ".join(filter_expression)
    response = music_table.scan(
        FilterExpression=filter_str,
        ExpressionAttributeValues=expression_values,
        ExpressionAttributeNames=expression_names
    )
    items = response.get("Items", [])
    if not items:
        return {
            "statusCode": 404,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"success": False, "message": "No result is retrieved. Please query again"})
        }
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
