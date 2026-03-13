import uuid
import boto3
from django.conf import settings
from datetime import datetime

class TodoItem:
    """
    Todo model using DynamoDB as storage
    """
    
    def __init__(self, task, context=None, aof=None, date=None, done=False, file_url=None, id=None):
        self.id = id or str(uuid.uuid4())
        self.task = task
        self.context = context
        self.aof = aof
        self.date = date
        self.done = done
        self.file_url = file_url
        self.created_at = datetime.utcnow().isoformat()
    
    def to_dict(self):
        return {
            'id': self.id,
            'task': self.task,
            'context': self.context,
            'aof': self.aof,
            'date': self.date,
            'done': self.done,
            'file_url': self.file_url,
            'created_at': self.created_at,
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            task=data.get('task'),
            context=data.get('context'),
            aof=data.get('aof'),
            date=data.get('date'),
            done=data.get('done', False),
            file_url=data.get('file_url'),
            id=data.get('id'),
        )


class DynamoDBManager:
    """
    Manager class for DynamoDB operations
    """
    
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name=settings.AWS_REGION)
        self.table = self.dynamodb.Table(settings.DYNAMODB_TABLE_NAME)
    
    def create_todo(self, todo):
        """Create a new todo item"""
        self.table.put_item(Item=todo.to_dict())
        return todo
    
    def get_todo(self, todo_id):
        """Get a single todo by ID"""
        response = self.table.get_item(Key={'id': todo_id})
        if 'Item' in response:
            return TodoItem.from_dict(response['Item'])
        return None
    
    def get_all_todos(self):
        """Get all todos"""
        response = self.table.scan()
        return [TodoItem.from_dict(item) for item in response.get('Items', [])]
    
    def get_todos_by_context(self, context):
        """Get todos filtered by context"""
        response = self.table.scan(
            FilterExpression='#context = :context',
            ExpressionAttributeNames={'#context': 'context'},
            ExpressionAttributeValues={':context': context}
        )
        return [TodoItem.from_dict(item) for item in response.get('Items', [])]
    
    def update_todo(self, todo_id, updates):
        """Update a todo item"""
        update_expression = 'SET ' + ', '.join([f'{k} = :{k}' for k in updates.keys()])
        expression_values = {f':{k}': v for k, v in updates.items()}
        
        self.table.update_item(
            Key={'id': todo_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        return self.get_todo(todo_id)
    
    def delete_todo(self, todo_id):
        """Delete a todo item"""
        self.table.delete_item(Key={'id': todo_id})


class S3Manager:
    """
    Manager class for S3 operations
    """
    
    def __init__(self):
        self.s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
        self.bucket_name = settings.S3_BUCKET_NAME
    
    def upload_file(self, file, todo_id):
        """Upload file to S3 and return the URL"""
        file_key = f'todos/{todo_id}/{file.name}'
        
        self.s3_client.upload_fileobj(
            file,
            self.bucket_name,
            file_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        
        url = f'https://{self.bucket_name}.s3.amazonaws.com/{file_key}'
        return url
    
    def delete_file(self, file_url):
        """Delete file from S3"""
        try:
            file_key = file_url.replace(f'https://{self.bucket_name}.s3.amazonaws.com/', '')
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
        except Exception as e:
            print(f'Error deleting file: {e}')