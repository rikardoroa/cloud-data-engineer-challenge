import json
from set_transformation import CreateS3Metric

def lambda_handler(event, context):



    get_metric = CreateS3Metric()
    curated_df = get_metric.get_event(event)
    print(curated_df)
    

    print('hola')
    print(event)
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }