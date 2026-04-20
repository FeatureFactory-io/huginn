import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template

from infra.stacks.data_stack import _SSM_NEW_PARAMS, DataStack
from infra.stacks.network_stack import NetworkStack

ENV = cdk.Environment(account="123456789012", region="us-east-1")


@pytest.fixture(scope="module")
def template() -> Template:
    app = cdk.App()
    network = NetworkStack(app, "TestNetwork", env=ENV)
    stack = DataStack(app, "TestData", vpc=network.vpc, rds_sg=network.rds_sg, env=ENV)
    return Template.from_stack(stack)


def test_one_rds_instance(template: Template) -> None:
    template.resource_count_is("AWS::RDS::DBInstance", 1)


def test_rds_postgresql_16(template: Template) -> None:
    # CDK VER_16 synthesises EngineVersion as "16" (major only)
    template.has_resource_properties(
        "AWS::RDS::DBInstance",
        {
            "Engine": "postgres",
            "EngineVersion": "16",
            "DBInstanceClass": "db.t3.micro",
            "DBName": "huginn",
            "StorageEncrypted": True,
            "MultiAZ": False,
        },
    )


def test_rds_deletion_protection(template: Template) -> None:
    template.has_resource_properties(
        "AWS::RDS::DBInstance",
        {"DeletionProtection": True},
    )


def test_ssm_stubs_created(template: Template) -> None:
    template.resource_count_is("AWS::SSM::Parameter", len(_SSM_NEW_PARAMS))


def test_ssm_param_paths(template: Template) -> None:
    for name in _SSM_NEW_PARAMS:
        template.has_resource_properties(
            "AWS::SSM::Parameter",
            {"Name": f"/huginn/prod/{name}"},
        )
