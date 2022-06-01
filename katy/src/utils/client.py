from weaviate import Client
import uuid
import json

def json_print(s: str):
  print(json.dumps({'data': s}, indent=4))
def update_schema(client: Client, class_name: str, new_schema: dict):
  client.schema.update_config(class_name, new_schema)

def create_content(client: Client, class_name: str, upload: dict):
  return client.data_object.create(upload, class_name, uuid.uuid4())

def add_property(client: Client, class_name: str, property: str):
  client.schema.property.create(class_name, property)

def clear_schema_content(client: Client):
  obj = client.data_object.get()
  for o in obj["objects"]:
    client.data_object.delete(o["id"])