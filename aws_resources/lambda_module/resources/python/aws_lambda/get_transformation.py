import pandas as pd
import boto3
import json
from utils import UtilsComponents
import logging
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secret_utils = UtilsComponents()

class GetBucketData:


    def __init__(self):
        self.secrets = secret_utils.get_secret()
        self.s3_client = boto3.client('s3')
        self.host = self.secrets['host'].split(":")[0]
        self.db_name = 'geospatialinfo'
        self.user = self.secrets['username']
        self.password = self.secrets['password']
        self.port = self.secrets['port']

    
    def schema_validation(self, df):
        """
        Validates and enforces the data schema of a given pandas DataFrame
        according to a predefined column structure and data type mapping.

        This method ensures that:
        - All required columns are present in the DataFrame.
        - Each column has the expected data type.
        - If a column's data type differs, it attempts to cast it to the expected one.
        - Logs detailed information about type validation, casting, and failures.

        Args:
            df (pd.DataFrame): The input DataFrame to be validated and corrected.

        Raises:
            ValueError: If one or more required columns are missing from the DataFrame.

        Returns:
            pd.DataFrame: A validated DataFrame with corrected data types where possible.

        """
        
        schema_dict = {
            "X": "float64", "Y": "float64", "CCN": "int64",
            "REPORT_DAT": "object", "SHIFT": "object", "METHOD": "object",
            "OFFENSE": "object", "BLOCK": "object", "XBLOCK": "float64",
            "YBLOCK": "float64", "WARD": "float64", "ANC": "object",
            "DISTRICT": "float64", "PSA": "float64",
            "NEIGHBORHOOD_CLUSTER": "object", "BLOCK_GROUP": "object",
            "CENSUS_TRACT": "float64", "VOTING_PRECINCT": "object",
            "LATITUDE": "float64", "LONGITUDE": "float64",
            "BID": "object", "START_DATE": "object", "END_DATE": "object",
            "OBJECTID": "int64", "OCTO_RECORD_ID": "float64"
        }

        missing_cols = [col for col in schema_dict if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")

        for col in df.columns:
            expected_type = schema_dict.get(col)
            actual_type = str(df[col].dtype)

            if expected_type == actual_type:
                logger.info(f"Column {col} has the correct data type: {expected_type}")
            else:
                try:
                    logger.info(f"Casting {col} with {actual_type} to {expected_type}")
                    df[col] = df[col].astype(expected_type)
                except Exception as e:
                    logger.error(f"Failed to convert column {col} from {actual_type} to {expected_type}: {e}")
                    continue

        logger.info("Schema validation completed successfully.")
        return df

    
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

            validated_df = self.schema_validation(df)

            # Connect to PostGIS database
            conn = psycopg2.connect(
                host=self.host,
                database=self.db_name,
                user=self.user,
                password=self.password,
                port=self.port
            )
            cur = conn.cursor()

            records = [
            (
                row.get('CCN'), row.get('REPORT_DAT'), row.get('SHIFT'),
                row.get('METHOD'), row.get('OFFENSE'), row.get('BLOCK'),
                row.get('WARD'), row.get('DISTRICT'), row.get('PSA'),
                row.get('NEIGHBORHOOD_CLUSTER'),
                row.get('LATITUDE'), row.get('LONGITUDE'),
                row.get('LONGITUDE'), row.get('LATITUDE')
            )
            for _, row in validated_df.iterrows()
            ]

            # sql template
            template = """
            (%s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s,
            %s, %s,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326))
            """

            execute_values(cur, f"""
                INSERT INTO crime_incidents (
                    ccn, report_date, shift, method, offense, block,
                    ward, district, psa, neighborhood_cluster,
                    latitude, longitude, geom
                ) VALUES %s;
            """, records, template=template)

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