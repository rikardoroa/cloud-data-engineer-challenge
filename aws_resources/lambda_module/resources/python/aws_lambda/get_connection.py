import boto3
import json
import pandas as pd
from botocore.exceptions import ClientError
import psycopg2
import logging
from utils import UtilsComponents

logger = logging.getLogger()
logger.setLevel(logging.INFO)

secret_utils = UtilsComponents()


class GetDbConnection:

    def __init__(self):
        """
        Initializes the AWS Secrets Manager client to retrieve PostgreSQL credentials.
        """
        self.secrets = secret_utils.get_secret()

    def get_connection(self):
        """
        Creates a PostGIS-enabled database (if not exists) and sets up a crime_incidents table.
        """
        try:
            #rds_credentials = self.get_secret()
            logger.info(self.secrets)

            host = self.secrets['host'].split(":")[0]
            db_name = self.secrets['dbname']
            user = self.secrets['username']
            password = self.secrets['password']
            port = self.secrets['port']
            new_dbname = "geospatialinfo"

            # Connect to main DB and create geospatial DB if needed
            conn = psycopg2.connect(
                host=host,
                database=db_name,
                user=user,
                password=password,
                port=port
            )
            conn.autocommit = True
            cur = conn.cursor()

            logger.info(f"Checking if database '{new_dbname}' exists...")
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (new_dbname,))
            exists = cur.fetchone()

            if not exists:
                cur.execute(f"CREATE DATABASE {new_dbname};")
                logger.info(f"Database '{new_dbname}' created successfully.")
            else:
                logger.info(f"ℹ️ Database '{new_dbname}' already exists.")

            cur.close()
            conn.close()

            # Connect to the new DB to enable PostGIS and create table
            conn2 = psycopg2.connect(
                host=host,
                database=new_dbname,
                user=user,
                password=password,
                port=port
            )
            cur2 = conn2.cursor()

            cur2.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            cur2.execute("CREATE EXTENSION IF NOT EXISTS postgis_topology;")

            cur2.execute("""
                CREATE TABLE IF NOT EXISTS crime_incidents (
                    id SERIAL PRIMARY KEY,
                    ccn TEXT,
                    report_date TIMESTAMPTZ,
                    shift TEXT,
                    method TEXT,
                    offense TEXT,
                    block TEXT,
                    ward TEXT,
                    district TEXT,
                    psa TEXT,
                    neighborhood_cluster TEXT,
                    latitude DOUBLE PRECISION,
                    longitude DOUBLE PRECISION,
                    geom GEOMETRY(Point, 4326)
                );
            """)

            cur2.execute("""
                CREATE INDEX IF NOT EXISTS idx_crime_geom
                ON crime_incidents USING GIST (geom);
            """)

            conn2.commit()

            cur2.execute("SELECT postgis_full_version();")
            postgis_version = cur2.fetchone()[0]
            logger.info(f"PostGIS enabled successfully in '{new_dbname}': {postgis_version}")

            cur2.close()
            conn2.close()

            return {
                "database_created": new_dbname,
                "postgis_version": postgis_version
            }

        except Exception as e:
            logger.error(f"[ERROR] cannot connect to the database: {str(e)}")
            return {"error": str(e)}