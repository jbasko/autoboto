from autoboto.services.cloudformation.client import Client

cf = Client()

for stack in cf.list_stacks().stack_summaries:
    print(stack.stack_name)
    print(cf.describe_stacks(stack_name=stack.stack_name))
