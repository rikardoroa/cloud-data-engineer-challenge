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

        method = event.get("httpMethod", "").upper()
        query_params = event.get("queryStringParameters")
        table = query_params.get("table", "").lower()

        get_data = GetSTableData()

        if event['Records']:
            get_metric = CreateS3Metric()
            response = get_metric.get_event(event)
            logger.info(response)


        if query_params:
            if table:
                if method == "GET":
                    result = get_metric.get_data(table)
                    query =  get_data.getdata(result)
                    return query

        return {
        'statusCode': 200,
        'body': json.dumps('process executed successfully!')
        }
    except Exception as e:
        logger.error(f'can not deply changes in some resources:{str(e)}')
        

    