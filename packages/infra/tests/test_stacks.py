"""Tests for CDK infrastructure stacks."""

import aws_cdk as cdk
from aws_cdk import assertions

from infra.stacks.bedrock import BedrockStack
from infra.stacks.compute import ComputeStack
from infra.stacks.storage import StorageStack


class TestStorageStack:
    """Tests for the StorageStack."""

    def test_s3_buckets_created(self, app: cdk.App) -> None:
        """Verify three S3 buckets are created."""
        stack = StorageStack(app, "TestStorage")
        template = assertions.Template.from_stack(stack)
        template.resource_count_is("AWS::S3::Bucket", 3)

    def test_no_dynamodb_tables(self, app: cdk.App) -> None:
        """Verify no DynamoDB tables are created."""
        stack = StorageStack(app, "TestStorage")
        template = assertions.Template.from_stack(stack)
        template.resource_count_is("AWS::DynamoDB::Table", 0)

    def test_raw_data_bucket_versioned(self, app: cdk.App) -> None:
        """Verify raw data bucket has versioning enabled."""
        stack = StorageStack(app, "TestStorage")
        template = assertions.Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::S3::Bucket",
            assertions.Match.object_like({"VersioningConfiguration": {"Status": "Enabled"}}),
        )


class TestBedrockStack:
    """Tests for the BedrockStack."""

    def test_iam_roles_created(self, app: cdk.App) -> None:
        """Verify two IAM roles are created (API and Lambda)."""
        stack = BedrockStack(app, "TestBedrock")
        template = assertions.Template.from_stack(stack)
        template.resource_count_is("AWS::IAM::Role", 2)

    def test_managed_policy_created(self, app: cdk.App) -> None:
        """Verify one managed policy is created for Bedrock access."""
        stack = BedrockStack(app, "TestBedrock")
        template = assertions.Template.from_stack(stack)
        template.resource_count_is("AWS::IAM::ManagedPolicy", 1)

    def test_inference_profile_arn_in_policy(self, app: cdk.App) -> None:
        """Verify inference profile ARN is included in the Bedrock policy."""
        stack = BedrockStack(app, "TestBedrock")
        template = assertions.Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::IAM::ManagedPolicy",
            assertions.Match.object_like(
                {
                    "PolicyDocument": assertions.Match.object_like(
                        {
                            "Statement": assertions.Match.array_with(
                                [
                                    assertions.Match.object_like(
                                        {
                                            "Sid": "BedrockInvokeModel",
                                            "Resource": assertions.Match.array_with(
                                                [
                                                    assertions.Match.object_like(
                                                        {
                                                            "Fn::Join": assertions.Match.array_with(
                                                                [
                                                                    "",
                                                                    assertions.Match.array_with(
                                                                        [
                                                                            assertions.Match.string_like_regexp(".*inference-profile.*"),
                                                                        ]
                                                                    ),
                                                                ]
                                                            )
                                                        }
                                                    )
                                                ]
                                            ),
                                        }
                                    )
                                ]
                            )
                        }
                    )
                }
            ),
        )


class TestComputeStack:
    """Tests for the ComputeStack."""

    def _create_compute_stack(self, app: cdk.App) -> ComputeStack:
        """Create a ComputeStack with all required cross-stack dependencies."""
        storage = StorageStack(app, "TestStorage")
        bedrock = BedrockStack(app, "TestBedrock")
        return ComputeStack(
            app,
            "TestCompute",
            raw_data_bucket=storage.raw_data_bucket,
            models_bucket=storage.models_bucket,
            api_role=bedrock.api_role,
            lambda_role=bedrock.lambda_role,
        )

    def test_lambda_is_docker_image_function(self, app: cdk.App) -> None:
        """Verify Lambda is a Docker image function named tra-ingestion."""
        stack = self._create_compute_stack(app)
        template = assertions.Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::Lambda::Function",
            assertions.Match.object_like(
                {
                    "FunctionName": "tra-ingestion",
                    "PackageType": "Image",
                }
            ),
        )

    def test_eventbridge_rule_created(self, app: cdk.App) -> None:
        """Verify an EventBridge rule is created for S3 notifications."""
        stack = self._create_compute_stack(app)
        template = assertions.Template.from_stack(stack)
        template.resource_count_is("AWS::Events::Rule", 1)

    def test_ecs_service_created(self, app: cdk.App) -> None:
        """Verify an ECS service is created."""
        stack = self._create_compute_stack(app)
        template = assertions.Template.from_stack(stack)
        template.resource_count_is("AWS::ECS::Service", 1)

    def test_ecs_task_has_environment_variables(self, app: cdk.App) -> None:
        """Verify ECS task definition has required TRA_ environment variables."""
        stack = self._create_compute_stack(app)
        template = assertions.Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::ECS::TaskDefinition",
            assertions.Match.object_like(
                {
                    "ContainerDefinitions": assertions.Match.array_with(
                        [
                            assertions.Match.object_like(
                                {
                                    "Environment": assertions.Match.array_with(
                                        [
                                            assertions.Match.object_like({"Name": "TRA_API_HOST"}),
                                            assertions.Match.object_like({"Name": "TRA_FAISS_INDEX_PATH"}),
                                        ]
                                    )
                                }
                            )
                        ]
                    )
                }
            ),
        )

    def test_alb_health_check(self, app: cdk.App) -> None:
        """Verify ALB target group has /health health check path."""
        stack = self._create_compute_stack(app)
        template = assertions.Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::ElasticLoadBalancingV2::TargetGroup",
            assertions.Match.object_like({"HealthCheckPath": "/health"}),
        )

    def test_s3_policies_created(self, app: cdk.App) -> None:
        """Verify IAM policies for S3 access are created."""
        stack = self._create_compute_stack(app)
        template = assertions.Template.from_stack(stack)
        # 2 explicit S3 policies + 1 auto-generated by EventBridge Lambda target
        template.resource_count_is("AWS::IAM::Policy", 3)

    def test_ssm_parameter_for_alb_dns(self, app: cdk.App) -> None:
        """Verify SSM parameter is created for the ALB DNS name."""
        stack = self._create_compute_stack(app)
        template = assertions.Template.from_stack(stack)
        template.has_resource_properties(
            "AWS::SSM::Parameter",
            assertions.Match.object_like({"Name": "/tra/alb-dns"}),
        )
