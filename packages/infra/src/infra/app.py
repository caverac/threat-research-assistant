"""CDK App entry point."""

import aws_cdk as cdk

from infra.stacks.bedrock import BedrockStack
from infra.stacks.compute import ComputeStack
from infra.stacks.storage import StorageStack

app = cdk.App()

storage = StorageStack(app, "TRAStorage")
bedrock = BedrockStack(app, "TRABedrock")
compute = ComputeStack(
    app,
    "TRACompute",
    raw_data_bucket=storage.raw_data_bucket,
    models_bucket=storage.models_bucket,
    api_role=bedrock.api_role,
    lambda_role=bedrock.lambda_role,
)

app.synth()
