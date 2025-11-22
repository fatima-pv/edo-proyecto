import json
import boto3

stepfunctions = boto3.client('stepfunctions')

def update_order_step(event, context):
    # TODO: Validate user role is STAFF
    body = json.loads(event['body'])
    task_token = body.get('taskToken')
    output = body.get('output', {'status': 'Step Completed'})

    try:
        stepfunctions.send_task_success(
            taskToken=task_token,
            output=json.dumps(output)
        )
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Step updated successfully'})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
