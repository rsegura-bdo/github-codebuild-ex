import boto3
import json
import logging

from custom_encoder import CustomEncoder

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamoTableName = 'product-inventory'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(dynamoTableName)

getMethod = 'GET'
postMethod = 'POST'
patchMethod = 'PATCH'
deleteMethod = 'DELETE'

healthPath = '/health'
productPath = '/product'
productsPath = '/products'

def lambda_handler(event, context):
    logger.info(event)
    httpMethod = event['httpMethod']
    path = event['path']

    if path == healthPath:
        if httpMethod == getMethod:
            body = {
                "status": "ok"
            }
            response = buildResponse(200, body)
    
    elif path == productPath:
        if httpMethod == getMethod: 
            response = getProduct(event["queryStringParameters"]["productId"])

        elif httpMethod == postMethod: 
            response = saveProduct(json.loads(event["body"]))
        
        elif httpMethod == patchMethod:
            requestBody = json.loads(event["body"])
            response = editProduct(requestBody["productId"], requestBody["updateKey"], requestBody["updateValue"])

        elif httpMethod == deleteMethod:
            requestBody = json.loads(event["body"])
            response = deleteProduct(requestBody["productId"])

    elif path == productsPath:
        if httpMethod == getMethod: 
            response = getProducts()

    else:
        response = buildResponse(404, "Resource/Method Not Found")

    return response
        

def buildResponse(statusCode, body=None):
    response = {
        "statusCode": statusCode,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        }
    }

    if body:
        response["body"] = json.dumps(body, cls=CustomEncoder)

    return response


def saveProduct(requestBody):
    try:
        table.put_item(Item=requestBody)
        body = {
            "Operation": "SAVE",
            "Message": "SUCCESS",
            "Item": requestBody
        }
        return buildResponse(201, body)
    
    except Exception as e:
        logger.exception(f"method: saveProduct(), details: {str(e)}")


def editProduct(productId, updateKey, updateValue):
    try:
        response = table.update_item(
            Key={
                "productId": productId
            },
            UpdateExpression=f"set {updateKey}=value",
            ExpressionAttributeValues={
                ":value": updateValue
            },
            ReturnValues="UPDATE_NEW"
        )

        body = {
            "Operation": "UPDATE",
            "Message": "SUCCESS",
            "UpdatedAttributes": response
        }

        return buildResponse(200, body)
    
    except Exception as e:
        logger.exception(f"method: editProduct(), details: {str(e)}")


def deleteProduct(productId):
    try:
        response = table.delete_item(
            Key={
                "productId": productId
            },
            ReturnValues="ALL_OLD"
        )

        body = {
            "Operation": "DELETE",
            "Message": "SUCCESS",
            "DeletedItem": response
        }

        return buildResponse(200, body)
    
    except Exception as e:
        logger.exception(f"method: deleteProduct(), details: {str(e)}")


def getProduct(productId):
    try:
        response = table.get_item(
            Key = {
                "productId": productId
            }
        )

        if "Item" in response:
            return buildResponse(200, response["Item"])
        else:
            return buildResponse(404, {"Message": f"ProductId: {productId} not found"})
        
    except Exception as e:
        logger.exception(f"method: getProduct(), details: {str(e)}")


def getProducts():
    try:
        response = table.scan()
        result = response["Items"]

        while "LastEvaluatedKey" in response:
            response = table.scan(ExclusiveStartKey=response["LastEvaluatedKey"])
            result.extend(response["Items"])

        body = {
            "products": result
        }

        return buildResponse(200, body)
    
    except Exception as e:
        logger.exception(f"method: getProducts(), details: {str(e)}")