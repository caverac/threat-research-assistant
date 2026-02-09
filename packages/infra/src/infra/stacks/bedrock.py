"""Bedrock stack for IAM roles and model access configuration."""

from typing import Any

from aws_cdk import Stack
from aws_cdk import aws_iam as iam
from constructs import Construct


class BedrockStack(Stack):
    """IAM roles for Bedrock model access (Claude + Titan)."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.bedrock_policy = iam.ManagedPolicy(
            self,
            "BedrockAccessPolicy",
            managed_policy_name="tra-bedrock-access",
            statements=[
                iam.PolicyStatement(
                    sid="BedrockInvokeModel",
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "bedrock:InvokeModel",
                        "bedrock:InvokeModelWithResponseStream",
                    ],
                    resources=[
                        f"arn:aws:bedrock:{self.region}::foundation-model/amazon.titan-embed-text-v2:0",
                        "arn:aws:bedrock:*::foundation-model/anthropic.claude-opus-4-5-20251101-v1:0",
                        f"arn:aws:bedrock:{self.region}:{self.account}:inference-profile/us.anthropic.claude-opus-4-5-20251101-v1:0",
                    ],
                ),
                iam.PolicyStatement(
                    sid="BedrockListModels",
                    effect=iam.Effect.ALLOW,
                    actions=["bedrock:ListFoundationModels"],
                    resources=["*"],
                ),
            ],
        )

        self.api_role = iam.Role(
            self,
            "ApiBedrockRole",
            role_name="tra-api-bedrock-role",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[self.bedrock_policy],
        )

        self.lambda_role = iam.Role(
            self,
            "LambdaBedrockRole",
            role_name="tra-lambda-bedrock-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                self.bedrock_policy,
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
            ],
        )
