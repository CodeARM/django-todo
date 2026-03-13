from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import TodoItem, DynamoDBManager, S3Manager
from .serializers import TodoSerializer

db_manager = DynamoDBManager()
s3_manager = S3Manager()


@api_view(['GET', 'POST'])
def todo_list(request):
    """
    GET: Retrieve all todos or filter by context
    POST: Create a new todo
    """
    if request.method == 'GET':
        context = request.query_params.get('context')
        
        if context:
            todos = db_manager.get_todos_by_context(context)
        else:
            todos = db_manager.get_all_todos()
        
        serializer = TodoSerializer([todo for todo in todos], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'POST':
        serializer = TodoSerializer(data=request.data)
        
        if serializer.is_valid():
            # Create todo item
            todo = TodoItem(
                task=serializer.validated_data['task'],
                context=serializer.validated_data.get('context', ''),
                aof=serializer.validated_data.get('aof', ''),
                date=serializer.validated_data.get('date', ''),
                done=serializer.validated_data.get('done', False)
            )
            
            # Handle file upload
            if 'file' in request.FILES:
                file = request.FILES['file']
                file_url = s3_manager.upload_file(file, todo.id)
                todo.file_url = file_url
            
            # Save to DynamoDB
            db_manager.create_todo(todo)
            
            response_serializer = TodoSerializer(todo)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def todo_detail(request, todo_id):
    """
    GET: Retrieve a specific todo
    PUT: Update a specific todo
    DELETE: Delete a specific todo
    """
    todo = db_manager.get_todo(todo_id)
    
    if not todo:
        return Response({'error': 'Todo not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = TodoSerializer(todo)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = TodoSerializer(data=request.data, partial=True)
        
        if serializer.is_valid():
            updates = {}
            
            if 'task' in serializer.validated_data:
                updates['task'] = serializer.validated_data['task']
            if 'context' in serializer.validated_data:
                updates['context'] = serializer.validated_data['context']
            if 'aof' in serializer.validated_data:
                updates['aof'] = serializer.validated_data['aof']
            if 'date' in serializer.validated_data:
                updates['date'] = serializer.validated_data['date']
            if 'done' in serializer.validated_data:
                updates['done'] = serializer.validated_data['done']
            
            # Handle file upload
            if 'file' in request.FILES:
                file = request.FILES['file']
                file_url = s3_manager.upload_file(file, todo_id)
                updates['file_url'] = file_url
            
            updated_todo = db_manager.update_todo(todo_id, updates)
            response_serializer = TodoSerializer(updated_todo)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Delete file from S3 if exists
        if todo.file_url:
            s3_manager.delete_file(todo.file_url)
        
        db_manager.delete_todo(todo_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def todo_contexts(request):
    """
    GET: Retrieve all unique contexts
    """
    todos = db_manager.get_all_todos()
    contexts = sorted(list(set([todo.context for todo in todos if todo.context])))
    return Response({'contexts': contexts}, status=status.HTTP_200_OK)