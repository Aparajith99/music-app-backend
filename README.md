# Music App Backend - COSC2626/2640 Assignment 2

## Backend URLs
- EC2: http://54.198.82.175
- ECS: http://44.192.57.176:5000
- Lambda: https://imum9rqox0.execute-api.us-east-1.amazonaws.com/prod

## API Endpoints
- POST /login
- POST /register
- GET /query
- GET /subscriptions/{email}
- POST /subscriptions
- DELETE /subscriptions/{email}/{title_year}

## AWS Resources
- DynamoDB tables: login, music, subscriptions
- S3 bucket: music-app-images-816553836520
- ECS cluster: music-app-cluster
- ECR: 816553836520.dkr.ecr.us-east-1.amazonaws.com/music-app-backend
- API Gateway ID: imum9rqox0
