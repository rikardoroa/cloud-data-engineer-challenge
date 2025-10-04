import json


class GetSTableData:

    @classmethod
    def getdata(cls, payload):
        """
        Wraps the given payload in a 200 OK JSON response.

        Args:
            payload (list or dict): Data to return as JSON.

        Returns:
            dict: HTTP response with JSON body.
        """
        
        try:

            return {
                    "statusCode": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(payload, default=str)   
            }
        except Exception as e:
            return  {
                    "statusCode": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": str(e)}, default=str)  
            }