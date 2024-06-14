import aws_cdk as core
import aws_cdk.assertions as assertions

from connect_llm.connect_llm_stack import ConnectLlmStack

# example tests. To run these tests, uncomment this file along with the example
# resource in connect_llm/connect_llm_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = ConnectLlmStack(app, "connect-llm")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
