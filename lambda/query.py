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

    if not any([title, artist, year, album]):
        return {
            "statusCode": 400,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"success": False, "message": "No result is retrieved. Please query again"})
        }
    # Decide between Query and Scan based on key fields.
    # Table PK: artist  |  SK: title_year
    # GSI  "year-artist-index":  PK: year   SK: artist
    # LSI  "artist-album-index": PK: artist SK: album

    key_condition_parts = []
    filter_parts = []
    expression_values = {}
    expression_names = {}
    use_query = False
    index_name = None

    if artist and album:
        # LSI query: artist (PK) + album (SK)
        use_query = True
        index_name = "artist-album-index"

        key_condition_parts.append("#a = :artist")
        expression_values[":artist"] = artist
        expression_names["#a"] = "artist"

        key_condition_parts.append("begins_with(#al, :album)")
        expression_values[":album"] = album
        expression_names["#al"] = "album"

        # remaining fields
        if title:
            filter_parts.append("contains(#t, :title)")
            expression_values[":title"] = title
            expression_names["#t"] = "title"
        if year:
            filter_parts.append("#y = :year")
            expression_values[":year"] = year
            expression_names["#y"] = "year"

    elif artist:
        # Table query on PK (artist)
        use_query = True

        key_condition_parts.append("#a = :artist")
        expression_values[":artist"] = artist
        expression_names["#a"] = "artist"

        # remaining fields
        if title:
            filter_parts.append("contains(#t, :title)")
            expression_values[":title"] = title
            expression_names["#t"] = "title"
        if year:
            filter_parts.append("#y = :year")
            expression_values[":year"] = year
            expression_names["#y"] = "year"

    elif year:
        # GSI query on year-artist-index
        use_query = True
        index_name = "year-artist-index"

        key_condition_parts.append("#y = :year")
        expression_values[":year"] = year
        expression_names["#y"] = "year"

        # remaining fields
        if title:
            filter_parts.append("contains(#t, :title)")
            expression_values[":title"] = title
            expression_names["#t"] = "title"
        if album:
            filter_parts.append("contains(#al, :album)")
            expression_values[":album"] = album
            expression_names["#al"] = "album"

    # Query or fall back to Scan
    if use_query:
        target = index_name if index_name else "table (PK: artist)"

        query_kwargs = {
            "KeyConditionExpression": " AND ".join(key_condition_parts),
            "ExpressionAttributeValues": expression_values,
            "ExpressionAttributeNames": expression_names,
        }
        if index_name:
            query_kwargs["IndexName"] = index_name
        if filter_parts:
            query_kwargs["FilterExpression"] = " AND ".join(filter_parts)

        response = music_table.query(**query_kwargs)
    else:
        # Only when no key field (artist / year) is given
        for field, placeholder, alias, attr, use_contains in [
            (title, ":title", "#t", "title", True),
            (album, ":album", "#al", "album", True),
        ]:
            if field:
                expr = f"contains({alias}, {placeholder})" if use_contains else f"{alias} = {placeholder}"
                filter_parts.append(expr)
                expression_values[placeholder] = field
                expression_names[alias] = attr

        response = music_table.scan(
            FilterExpression=" AND ".join(filter_parts),
            ExpressionAttributeValues=expression_values,
            ExpressionAttributeNames=expression_names,
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
