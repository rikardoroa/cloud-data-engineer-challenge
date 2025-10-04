import pandas as pd
import boto3
import json
from utils import UtilsComponents

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secret_utils = UtilsComponents()

class CreateS3Metric:


    def __init__(self):
        self.secrets = secret_utils.get_secret()

    
    def get_event(self,event):

        """
        Reads a CSV file from an S3 event and loads its crime incident data 
        into a PostGIS-enabled PostgreSQL table.

        The method extracts the S3 bucket and key from the event, reads the file 
        into a pandas DataFrame, and inserts each record into the `crime_incidents` 
        table with a geometry point created from latitude and longitude.

        Args:
            event (dict): S3 event payload containing bucket and object key.

        Returns:
            dict: Number of rows successfully inserted, e.g. {"rows_inserted": 542}.
        """

        try:

            # extracting key and bucket data
            bucket = event['Records'][0]['s3']['bucket']['name']
            key = event['Records'][0]['s3']['object']['key']


            # reading the bucket info
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            df = pd.read_csv(response['Body'])


            host = self.secrets['host'].split(":")[0]
            db_name = 'geospatialinfo'
            user = self.secrets['username']
            password = self.secrets['password']
            port = self.secrets['port']
           

            # Connect to PostGIS database
            conn = psycopg2.connect(
                host=host,
                database=db_name,
                user=user,
                password=password,
                port=port
            )
            cur = conn.cursor()

            # Insert each record
            for _, row in df.iterrows():
                cur.execute("""
                    INSERT INTO crime_incidents (
                        ccn, report_date, shift, method, offense, block,
                        ward, district, psa, neighborhood_cluster,
                        latitude, longitude, geom
                    )
                    VALUES (
                        %s, %s, %s, %s, %s, %s,
                        %s, %s, %s, %s,
                        %s, %s,
                        ST_SetSRID(ST_MakePoint(%s, %s), 4326)
                    );
                """, (
                    row.get('CCN'), row.get('REPORT_DAT'), row.get('SHIFT'),
                    row.get('METHOD'), row.get('OFFENSE'), row.get('BLOCK'),
                    row.get('WARD'), row.get('DISTRICT'), row.get('PSA'),
                    row.get('NEIGHBORHOOD_CLUSTER'),
                    row.get('LATITUDE'), row.get('LONGITUDE'),
                    row.get('LONGITUDE'), row.get('LATITUDE')
                ))

            conn.commit()
            cur.close()
            conn.close()

            logger.info("Crime data loaded successfully into PostGIS.")
            return {"rows_inserted": len(df)}


        except Exception  as e:
            logger.error(f'[ERROR] can not insert dataset into the table: {str(e)}')