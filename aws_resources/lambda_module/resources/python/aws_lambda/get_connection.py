import boto3
import json
import pandas as pd
from botocore.exceptions import ClientError
import psycopg2
import logging



logger = logging.getLogger()
logger.setLevel(logging.INFO)


class GetConn:

    def __init__(self):
        """
        Initializes the AWS Secrets Manager client to retrieve Snowflake credentials.
        """

        self.session = boto3.session.Session()
        self.client = self.session.client(service_name='secretsmanager')
        self.secret = "postgresql_conn"

    def get_secret(self):
        """
        Retrieves Postgresql connection credentials from AWS Secrets Manager.

        Returns:
            dict: A dictionary containing keys such as 'user', 'password', 'endpoint',
            'port' and 'database'

        Logs:
            Logs an error message if the secret cannot be retrieved.
        """

        try:
            response = self.client.get_secret_value(SecretId=self.secret)
            credentials = json.loads(response['SecretString'])
            return credentials
        except ClientError as e:
            logger.error(f'[ERROR] can not retrieve the secret: {e.response["Error"]}')


    def validate_connection(self):
        """
        Validates the connection to the PostgreSQL database using credentials from Secrets Manager.

        Returns:
            dict: A dictionary containing the PostgreSQL server version (e.g., {"postgres_version": "15.7"}).

        Logs:
            - Logs the retrieved credentials for debugging.
            - Logs an error message if the connection cannot be established.
        """
        try:
            rds_credentials = self.get_secret()
            logger.info(rds_credentials)
            conn = psycopg2.connect(
                host=rds_credentials['host'].split(":")[0], 
                database=rds_credentials['dbname'],
                user=rds_credentials['username'],
                password=rds_credentials['password'],
                port=rds_credentials['port']
            )
            cur = conn.cursor()
            cur.execute("SELECT version();")
            result = cur.fetchone()
            return {"postgres_version": result[0]}
           
        except Exception as e:
              logger.error(f'[ERROR] can not connect to the database: {str(e)}')

