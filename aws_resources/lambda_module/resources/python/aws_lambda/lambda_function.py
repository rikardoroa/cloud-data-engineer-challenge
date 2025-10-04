import json
from set_transformation import CreateS3Metric
from get_connection import GetConn
import logging



logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    logger.info(event)
    get_conn  = GetConn()
    get_metric = CreateS3Metric()
    curated_df = get_metric.get_event(event)
    payload= get_conn.validate_connection()

    logger.info(curated_df)
    logger.info(payload)
    

    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }