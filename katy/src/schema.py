import time
from weaviate import Client
from dotenv import load_dotenv
import os


def instantiate_schema(client: Client):
    load_dotenv()
    SCHEMA_DIR = os.getenv('SCHEMA_DIR')

    client.schema.create(SCHEMA_DIR)
    print('Instantiating new schema...')
    time.sleep(1)

    return client.schema.get()