import pandas as pd
import boto3
import json
from utils import UtilsComponents
import logging
import psycopg2


logger = logging.getLogger()
logger.setLevel(logging.INFO)

secret_utils = UtilsComponents()

class CreateS3Metric:


    def __init__(self):
        self.secrets = secret_utils.get_secret()
        self.s3_client = boto3.client('s3')
        self.host = self.secrets['host'].split(":")[0]
        self.db_name = 'geospatialinfo'
        self.user = self.secrets['username']
        self.password = self.secrets['password']
        self.port = self.secrets['port']

    
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

           
            # Connect to PostGIS database
            conn = psycopg2.connect(
                host=self.host,
                database=self.db_name,
                user=self.user,
                password=self.password,
                port=self.port
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

            cur.execute("""
                SELECT EXISTS (
                    SELECT 1
                    FROM pg_views
                    WHERE schemaname = 'public'
                    AND viewname = 'v_crime_summary'
                );
            """)
            exists = cur.fetchone()[0]

            if not exists:
                cur.execute("""
                    CREATE VIEW v_crime_summary AS
                    SELECT
                        offense,
                        district,
                        COUNT(*) AS total,
                        ST_Collect(geom) AS geom_cluster
                    FROM crime_incidents
                    WHERE geom IS NOT NULL
                    GROUP BY offense, district;
                """)
                logger.info("View 'v_crime_summary' created successfully.")
            else:
                logger.info("View 'v_crime_summary' already exists.")

            conn.commit()
            cur.close()
            conn.close()

            logger.info("Crime data loaded successfully into PostGIS.")
            return {"rows_inserted": len(df)}


        except Exception  as e:
            logger.error(f'[ERROR] can not insert dataset into the table: {str(e)}')


    def get_data(self, table):

        """
        Fetches data from a given PostGIS table or view and returns it as JSON.

        Connects to the database, runs a predefined query based on the table name
        ('crime_incidents' or 'crime_summary'), converts results to a pandas DataFrame,
        and serializes them to JSON.

        Args:
            table (str): Target table or view name.

        Returns:
            list[dict]: Query results in JSON format.
        """

        try:
            # Connect to PostGIS database
            conn2 = psycopg2.connect(
                host=self.host,
                database=self.db_name,
                user=self.user,
                password=self.password,
                port=self.port
            )
            cur2 = conn.cursor()

            metadata = {
                    'crime_incidents': 'select * from crime_incidents',
                    'crime_summary':'select * from v_crime_summary'
            }

            query = metadata.get(table)
            if query:
                cur2.execute(query)
                table_results = cur.fetchall()
                columns = [desc[0] for desc in cur2.description]
                df = pd.DataFrame(table_results, columns=columns)
                all_data = json.loads(df.to_json(orient='records'))
                return all_data
            else:
                return [{"error": f"Invalid table '{table}' specified."}]
        except Exception  as e:
            logger.error(f'[ERROR] can not create the dataframe: {str(e)}')


