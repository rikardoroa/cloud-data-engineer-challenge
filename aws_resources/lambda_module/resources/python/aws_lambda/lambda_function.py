import json
from get_transformation import GetBucketData
from get_connection import GetDbConnection
from get import GetSTableData
from get_response import GetTableResponse
import logging



logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    try:
        get_conn  = GetDbConnection()
        payload = get_conn.get_connection()
        logger.info(payload)


        if 'Records' in event:
            get_s3_metadata = GetBucketData()
            response = get_s3_metadata.get_event(event)
            logger.info(response)
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "S3 data processed", "result": response})
            }

        method = event.get("httpMethod", "").upper()
        query_params = event.get("queryStringParameters") or {}
        table = query_params.get("table", "").lower() if query_params else None
        

        if method == "GET" and table:
            get_response = GetTableResponse()
            get_payload = GetSTableData()
            result = get_response.get_table_response(table)
            query =  get_payload.get_data(result)
            return query
    
        return {
        "statusCode": 400,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "Invalid request. Provide 'table' parameter or S3 event."})
        }

    except Exception as e:
        logger.error(f'can not deply changes in some resources:{str(e)}')
        return {
        "statusCode": 500,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": str(e)})
        }
        

    