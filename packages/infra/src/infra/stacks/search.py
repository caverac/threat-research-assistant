"""Search stack for OpenSearch Serverless vector search."""

from typing import Any

from aws_cdk import Stack
from aws_cdk import aws_opensearchserverless as oss
from constructs import Construct


class SearchStack(Stack):
    """OpenSearch Serverless collection for vector search."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.encryption_policy = oss.CfnSecurityPolicy(
            self,
            "EncryptionPolicy",
            name="tra-encryption",
            type="encryption",
            policy='{"Rules":[{"ResourceType":"collection","Resource":["collection/tra-threats"]}],"AWSOwnedKey":true}',
        )

        self.network_policy = oss.CfnSecurityPolicy(
            self,
            "NetworkPolicy",
            name="tra-network",
            type="network",
            policy=(
                '[{"Rules":[{"ResourceType":"collection","Resource":["collection/tra-threats"]},'
                '{"ResourceType":"dashboard","Resource":["collection/tra-threats"]}],'
                '"AllowFromPublic":true}]'
            ),
        )

        self.collection = oss.CfnCollection(
            self,
            "ThreatCollection",
            name="tra-threats",
            type="VECTORSEARCH",
            description="OT threat intelligence vector search collection",
        )
        self.collection.add_dependency(self.encryption_policy)
        self.collection.add_dependency(self.network_policy)
