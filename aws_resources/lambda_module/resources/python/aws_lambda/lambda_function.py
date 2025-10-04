import json
from set_transformation import CreateS3Metric
from get_connection import GetConn
import logging



logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):

    try:
        get_conn  = GetConn()
        payload= get_conn.validate_connection()
        logger.info(payload)

        if event:
            get_metric = CreateS3Metric()
            response = get_metric.get_event(event)
            logger.info(response)

        return {
        'statusCode': 200,
        'body': json.dumps('process executed successfully!')
        }
    except Exception as e:
        logger.error(f'can not deply changes in some resources:{str(e)}')
        

    