FROM public.ecr.aws/lambda/python:3.9

# establish the root/work directory for our lambda environment to detect
WORKDIR ${LAMBDA_TASK_ROOT}

# requirements.txt copy into our work/root directory
COPY requirements.txt .

# installing all dependecies/python packets needed
RUN pip install --no-cache-dir -r requirements.txt


# copy all the lambda root folde code into our work directory
COPY python/* .

# lambda handler definition for our lambda environment
CMD ["lambda_function.lambda_handler"]