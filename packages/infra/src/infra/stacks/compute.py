"""ECS Fargate and Lambda compute stack."""

from pathlib import Path
from typing import Any

from aws_cdk import Duration, Fn, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_ssm as ssm
from constructs import Construct

# Resolve repo root: compute.py -> stacks -> infra -> src -> infra -> packages -> repo root
_REPO_ROOT = str(Path(__file__).resolve().parents[5])


class ComputeStack(Stack):
    """Lambda functions for ingestion and ECS/Fargate for the API service."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        raw_data_bucket: s3.IBucket,
        models_bucket: s3.IBucket,
        api_role: iam.IRole,
        lambda_role: iam.IRole,
        **kwargs: Any,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Build S3 ARNs from bucket names to avoid cross-stack token refs that
        # cause cyclic dependencies when combined with event notifications.
        raw_bucket_arn = Fn.join("", ["arn:aws:s3:::", raw_data_bucket.bucket_name])
        models_bucket_arn = Fn.join("", ["arn:aws:s3:::", models_bucket.bucket_name])

        iam.Policy(
            self,
            "LambdaS3Policy",
            roles=[lambda_role],
            statements=[
                iam.PolicyStatement(
                    actions=["s3:GetObject", "s3:GetBucketLocation"],
                    resources=[raw_bucket_arn, Fn.join("", [raw_bucket_arn, "/*"])],
                ),
                iam.PolicyStatement(
                    actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
                    resources=[models_bucket_arn, Fn.join("", [models_bucket_arn, "/*"])],
                ),
            ],
        )

        iam.Policy(
            self,
            "ApiS3Policy",
            roles=[api_role],
            statements=[
                iam.PolicyStatement(
                    actions=["s3:GetObject", "s3:ListBucket"],
                    resources=[models_bucket_arn, Fn.join("", [models_bucket_arn, "/*"])],
                ),
            ],
        )

        self.ingestion_function = lambda_.DockerImageFunction(
            self,
            "IngestionFunction",
            function_name="tra-ingestion",
            code=lambda_.DockerImageCode.from_image_asset(
                directory=_REPO_ROOT,
                file="lambda/ingestion/Dockerfile",
            ),
            timeout=Duration.minutes(5),
            memory_size=1024,
            role=lambda_role,
            environment={
                "TRA_AWS_REGION": self.region,
                "TRA_S3_INDEX_BUCKET": models_bucket.bucket_name,
                "TRA_S3_INDEX_PREFIX": "faiss_index",
                "TRA_S3_MODELS_BUCKET": models_bucket.bucket_name,
                "TRA_S3_MODELS_PREFIX": "models",
                "TRA_BEDROCK_EMBEDDING_MODEL_ID": "amazon.titan-embed-text-v2:0",
            },
        )

        # Use EventBridge rule instead of S3 native notifications to avoid
        # cyclic cross-stack references (bucket in StorageStack, Lambda here).
        # Requires event_bridge_enabled=True on the bucket.
        events.Rule(
            self,
            "RawDataIngestionRule",
            event_pattern=events.EventPattern(
                source=["aws.s3"],
                detail_type=["Object Created"],
                detail={
                    "bucket": {"name": [raw_data_bucket.bucket_name]},
                    "object": {"key": [{"suffix": ".json"}]},
                },
            ),
            targets=[targets.LambdaFunction(self.ingestion_function)],
        )

        self.vpc = ec2.Vpc(
            self,
            "ApiVpc",
            max_azs=2,
            nat_gateways=1,
        )

        self.cluster = ecs.Cluster(
            self,
            "ApiCluster",
            cluster_name="tra-api",
            vpc=self.vpc,
        )

        self.api_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "ApiService",
            cluster=self.cluster,
            cpu=512,
            memory_limit_mib=1024,
            desired_count=1,
            min_healthy_percent=100,
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_asset(_REPO_ROOT),
                container_port=8000,
                task_role=api_role,
                environment={
                    "TRA_API_HOST": "0.0.0.0",
                    "TRA_API_PORT": "8000",
                    "TRA_AWS_REGION": self.region,
                    "TRA_S3_INDEX_BUCKET": models_bucket.bucket_name,
                    "TRA_S3_INDEX_PREFIX": "faiss_index",
                    "TRA_S3_MODELS_BUCKET": models_bucket.bucket_name,
                    "TRA_S3_MODELS_PREFIX": "models",
                    "TRA_FAISS_INDEX_PATH": "/tmp/faiss_index",
                    "TRA_RECOMMENDER_MODEL_PATH": "/tmp/recommender.joblib",
                    "TRA_BEDROCK_EMBEDDING_MODEL_ID": "amazon.titan-embed-text-v2:0",
                    "TRA_BEDROCK_LLM_MODEL_ID": "us.anthropic.claude-opus-4-5-20251101-v1:0",
                },
            ),
        )

        self.api_service.target_group.configure_health_check(path="/health")

        ssm.StringParameter(
            self,
            "AlbDnsParam",
            parameter_name="/tra/alb-dns",
            string_value=self.api_service.load_balancer.load_balancer_dns_name,
        )
