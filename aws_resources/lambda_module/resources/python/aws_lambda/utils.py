
import boto3
import json
from botocore.exceptions import ClientError
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


class UtilsComponents:

    def __init__(self):
        """
        Initializes the AWS Secrets Manager client to retrieve PostgreSQL credentials.
        """
        self.session = boto3.session.Session()
        self.client = self.session.client(service_name='secretsmanager')
        self.secret = "postgresql_conn"

    def get_secret(self):
        """
        Retrieves PostgreSQL connection credentials from AWS Secrets Manager.
        """
        try:
            response = self.client.get_secret_value(SecretId=self.secret)
            credentials = json.loads(response['SecretString'])
            return credentials
        except ClientError as e:
            logger.error(f"[ERROR] cannot retrieve the secret: {e.response['Error']}")
            raise