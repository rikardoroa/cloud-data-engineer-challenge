import pandas as pd
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class CreateS3Metric:


    def __init__(self):
        self.s3_client = boto3.client('s3')


    
    def get_event(self,event):

        """
        Read a JSON file from an S3 event and return sales totals
        grouped by category, month, and year.

        Args:
            event (dict): Lambda event containing S3 bucket and object key.

        Returns:
            pd.DataFrame: DataFrame with columns:
                category_id, month, year, total_price
        """

        try:

            # extracting key and bucket data
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']


            # reading the bucket info
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            payload = json.loads(response['Body'].read().decode('utf-8'))
            
            # creating the dataset
            df = pd.DataFrame(payload)

            # apply sales metric per month and year
            total_sales_per_month_year = df.groupby(['category_id','month','year']).agg(total_price=('price','sum')).reset_index(drop=False)

            return total_sales_per_month_year
        except ClientError as e:
            logger.error(f'[ERROR] can not apply metric for the pandas dataframe: {e.response["Error"]}')