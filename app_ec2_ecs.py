from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}},
     supports_credentials=False,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
login_table = dynamodb.Table("login")
music_table = dynamodb.Table("music")
subscriptions_table = dynamodb.Table("subscriptions")

s3 = boto3.client("s3", region_name="us-east-1")
BUCKET = "music-app-images-816553836520"

@app.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    response = login_table.get_item(Key={"email": email})
    item = response.get("Item")
    if not item:
        return jsonify({"success": False, "message": "email or password is invalid"}), 401
    if item["password"] != password:
        return jsonify({"success": False, "message": "email or password is invalid"}), 401
    return jsonify({"success": True, "user_name": item["user_name"], "email": email}), 200

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    username = data.get("username")
    password = data.get("password")
    response = login_table.get_item(Key={"email": email})
    item = response.get("Item")
    if item:
        return jsonify({"success": False, "message": "The email already exists"}), 400
    login_table.put_item(Item={
        "email": email,
        "user_name": username,
        "password": password
    })
    return jsonify({"success": True}), 201

@app.route("/query", methods=["GET"])
def query():
    title = request.args.get("title")
    artist = request.args.get("artist")
    year = request.args.get("year")
    album = request.args.get("album")
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
        return jsonify({"success": False, "message": "No result is retrieved. Please query again"}), 400
    filter_str = " AND ".join(filter_expression)
    response = music_table.scan(
        FilterExpression=filter_str,
        ExpressionAttributeValues=expression_values,
        ExpressionAttributeNames=expression_names
    )
    items = response.get("Items", [])
    if not items:
        return jsonify({"success": False, "message": "No result is retrieved. Please query again"}), 404
    for item in items:
        filename = item["image_url"].split("/")[-1]
        item["image_url"] = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": filename},
            ExpiresIn=3600
        )
    return jsonify({"success": True, "items": items}), 200

from boto3.dynamodb.conditions import Key
import urllib.parse

@app.route("/subscriptions/<email>", methods=["GET"])
def get_subscriptions(email):
    email = urllib.parse.unquote(email)
    response = subscriptions_table.query(
        KeyConditionExpression=Key("email").eq(email)
    )
    items = response.get("Items", [])
    for item in items:
        filename = item["image_url"].split("/")[-1]
        item["image_url"] = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET, "Key": filename},
            ExpiresIn=3600
        )
    return jsonify({"success": True, "items": items}), 200

@app.route("/subscriptions", methods=["POST"])
def add_subscription():
    data = request.get_json()
    email = data.get("email")
    artist = data.get("artist")
    title = data.get("title")
    year = data.get("year")
    album = data.get("album")
    image_url = data.get("image_url")
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
    return jsonify({"success": True}), 201

@app.route("/subscriptions/<email>/<path:title_year>", methods=["DELETE"])
def remove_subscription(email, title_year):
    email = urllib.parse.unquote(email)
    title_year = urllib.parse.unquote(title_year)
    subscriptions_table.delete_item(
        Key={
            "email": email,
            "title_year": title_year
        }
    )
    return jsonify({"success": True}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80, debug=False)
