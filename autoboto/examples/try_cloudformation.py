from autoboto.services import cloudformation as cf

cf_client = cf.Client()

for stack in cf_client.list_stacks().stack_summaries:
    print(stack.stack_name)
    print(cf_client.describe_stacks(stack_name=stack.stack_name))
