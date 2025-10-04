import json
from set_transformation import CreateS3Metric
from get_connection import GetConn
from get import GetSTableData
import logging



logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    try:
        get_conn  = GetConn()
        payload= get_conn.validate_connection()
        logger.info(payload)


        if 'Records' in event:
            get_metric = CreateS3Metric()
            response = get_metric.get_event(event)
            logger.info(response)
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "S3 data processed", "result": response})
            }

        method = event.get("httpMethod", "").upper()
        query_params = event.get("queryStringParameters") or {}
        table = query_params.get("table", "").lower() if query_params else None
        

        if method == "GET" and table:
            get_data = GetSTableData()
            result = get_metric.get_data(table)
            query =  get_data.getdata(result)
            return query

        return {
        'statusCode': 400,
        "body": json.dumps({"error": "Invalid request. Provide 'table' parameter or S3 event."})
        }

    except Exception as e:
        logger.error(f'can not deply changes in some resources:{str(e)}')
        

    