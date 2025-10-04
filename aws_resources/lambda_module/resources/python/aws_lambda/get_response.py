import pandas as pd
import json
from utils import UtilsComponents
import logging
import psycopg2


logger = logging.getLogger()
logger.setLevel(logging.INFO)

secret_utils = UtilsComponents()

class GetTableResponse:


    def __init__(self):
        self.secrets = secret_utils.get_secret()
        self.host = self.secrets['host'].split(":")[0]
        self.db_name = 'geospatialinfo'
        self.user = self.secrets['username']
        self.password = self.secrets['password']
        self.port = self.secrets['port']


    def get_table_response(self, table):

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
                cur2 = conn2.cursor()

                metadata = {
                        'crime_incidents': 'select * from crime_incidents',
                        'crime_summary':'select * from v_crime_summary'
                }

                query = metadata.get(table)
                if query:
                    cur2.execute(query)
                    table_results = cur2.fetchall()
                    columns = [desc[0] for desc in cur2.description]
                    df = pd.DataFrame(table_results, columns=columns)
                    all_data = json.loads(df.to_json(orient='records'))
                    return all_data
                else:
                    return [{"error": f"Invalid table '{table}' specified."}]
            except Exception  as e:
                logger.error(f'[ERROR] can not create the dataframe: {str(e)}')


