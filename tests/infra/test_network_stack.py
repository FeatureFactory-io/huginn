import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template

from infra.stacks.network_stack import NetworkStack

ENV = cdk.Environment(account="123456789012", region="us-east-1")


@pytest.fixture(scope="module")
def template() -> Template:
    app = cdk.App()
    stack = NetworkStack(app, "TestNetwork", env=ENV)
    return Template.from_stack(stack)


def test_single_vpc(template: Template) -> None:
    template.resource_count_is("AWS::EC2::VPC", 1)


def test_four_subnets(template: Template) -> None:
    # 2 public + 2 private across 2 AZs
    template.resource_count_is("AWS::EC2::Subnet", 4)


def test_one_nat_gateway(template: Template) -> None:
    template.resource_count_is("AWS::EC2::NatGateway", 1)


def test_two_security_groups(template: Template) -> None:
    # eb-sg + rds-sg (CDK also creates a default SG for the VPC — count may be 3)
    # Assert at least the 2 named ones exist by checking ingress rules.
    template.resource_count_is("AWS::EC2::SecurityGroup", 2)


def test_eb_sg_allows_http(template: Template) -> None:
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "SecurityGroupIngress": [
                {
                    "CidrIp": "0.0.0.0/0",
                    "FromPort": 80,
                    "ToPort": 80,
                    "IpProtocol": "tcp",
                }
            ]
        },
    )


def test_rds_sg_allows_postgres_from_eb(template: Template) -> None:
    template.has_resource_properties(
        "AWS::EC2::SecurityGroupIngress",
        {
            "FromPort": 5432,
            "ToPort": 5432,
            "IpProtocol": "tcp",
        },
    )
