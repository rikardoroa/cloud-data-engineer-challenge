
import boto3
import json
from botocore.exceptions import ClientError
import logging
from datetime import datetime

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class UtilsComponents:

    def __init__(self):
        """
        Initializes the AWS Secrets Manager client to retrieve PostgreSQL credentials.
        """
        self.session = boto3.session.Session()
        self.client = self.session.client(service_name='secretsmanager')
        self.secret = "postgresql_conn_db"
        self.rds = boto3.client('rds')

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


    
    def create_rds_snapshot(self):
        """
        Creates an RDS snapshot if the database instance is available.

        Checks the status of the RDS instance; if it's "available", starts a snapshot 
        creation with a timestamped ID. Otherwise, returns a message indicating that 
        the instance is not ready. Safe to re-run without side effects (idempotent).

        Returns:
            dict: Snapshot creation result or waiting message.
        """
        try:
            db_instance = "dbgeospatialdev"
            snapshot_id = f"{db_instance}-snapshot-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"

            
            instance_response = self.rds.describe_db_instances(DBInstanceIdentifier=db_instance)
            status = instance_response['DBInstances'][0]['DBInstanceStatus']
            
            if status == "available":
                response = self.rds.create_db_snapshot(
                    DBSnapshotIdentifier=snapshot_id,
                    DBInstanceIdentifier=db_instance
                )
                return {
                    "status": "snapshot_started",
                    "snapshot_id": snapshot_id,
                    "response": response
                }
                
                
            if status != "available":
                return {
                    "status": "snapshot_not_started",
                    "snapshot_id": snapshot_id,
                    "response": "wait until de instance is available"
                }
                    
        except ClientError as e:
            logger.error(f'[ERROR] :{e.response["Error"]["Message"]}')