import boto3
import json

dynamodb = boto3.resource("dynamodb", region_name="us-east-1")

def create_login_table():
    table = dynamodb.create_table(
        TableName="login",
        KeySchema=[
            {"AttributeName": "email", "KeyType": "HASH"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "email", "AttributeType": "S"}
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    table.wait_until_exists()
    print("Login table created")
    return table

def load_login_data(table):
    users = [
        {"email": "s4118143@student.rmit.edu.au",  "user_name": "AravindAparajithKarthikeyan0", "password": "012345"},
        {"email": "s41181431@student.rmit.edu.au", "user_name": "AravindAparajithKarthikeyan1", "password": "123456"},
        {"email": "s41181432@student.rmit.edu.au", "user_name": "AravindAparajithKarthikeyan2", "password": "234567"},
        {"email": "s4103989@student.rmit.edu.au", "user_name": "BharanidharanRamadurai0", "password": "345678"},
        {"email": "s41039891@student.rmit.edu.au", "user_name": "BharanidharanRamadurai1", "password": "456789"},
        {"email": "s41039892@student.rmit.edu.au", "user_name": "BharanidharanRamadurai2", "password": "567890"},
        {"email": "s4084327@student.rmit.edu.au", "user_name": "KaveeshwarKandhasamySubbramani0", "password": "678901"},
        {"email": "s40843271@student.rmit.edu.au", "user_name": "KaveeshwarKandhasamySubbramani1", "password": "789012"},
        {"email": "s40843272@student.rmit.edu.au", "user_name": "KaveeshwarKandhasamySubbramani2", "password": "890123"},
        {"email": "s40843273@student.rmit.edu.au", "user_name": "KaveeshwarKandhasamySubbramani3", "password": "901234"},
    ]
    print(f"Loading {len(users)} users...")
    with table.batch_writer() as batch:
        for user in users:
            batch.put_item(Item=user)
    print("Login data loaded")

def create_music_table():
    table = dynamodb.create_table(
        TableName="music",
        KeySchema=[
            {"AttributeName": "artist",     "KeyType": "HASH"},
            {"AttributeName": "title_year", "KeyType": "RANGE"}
        ],
        AttributeDefinitions=[
            {"AttributeName": "artist",     "AttributeType": "S"},
            {"AttributeName": "title_year", "AttributeType": "S"},
            {"AttributeName": "year",       "AttributeType": "S"},
            {"AttributeName": "album",      "AttributeType": "S"}
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "year-artist-index",
                "KeySchema": [
                    {"AttributeName": "year",   "KeyType": "HASH"},
                    {"AttributeName": "artist", "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            }
        ],
        LocalSecondaryIndexes=[
            {
                "IndexName": "artist-album-index",
                "KeySchema": [
                    {"AttributeName": "artist", "KeyType": "HASH"},
                    {"AttributeName": "album",  "KeyType": "RANGE"}
                ],
                "Projection": {"ProjectionType": "ALL"}
            }
        ],
        BillingMode="PAY_PER_REQUEST"
    )
    table.wait_until_exists()
    print("Music table created")
    return table

def load_music_data(table):
    with open("2026a2_songs.json", "r") as f:
        data = json.load(f)
    songs = data["songs"]
    print(f"Loading {len(songs)} songs...")
    with table.batch_writer() as batch:
        for song in songs:
            title_year = f"{song['title']}#{song['year']}"
            batch.put_item(Item={
                "artist":     song["artist"],
                "title_year": title_year,
                "title":      song["title"],
                "year":       song["year"],
                "album":      song["album"],
                "image_url":  song["img_url"]
            })
    print(f"Loaded {len(songs)} songs")
    
if __name__ == "__main__":
    login_table = create_login_table()
    load_login_data(login_table)
    music_table = create_music_table()
    load_music_data(music_table)
    print("Setup complete")
