from build.services.cloudformation import Client


cf = Client()

for stack in cf.list_stacks().StackSummaries:
    print(stack.StackName)
    print(cf.describe_stacks(StackName=stack.StackName))
