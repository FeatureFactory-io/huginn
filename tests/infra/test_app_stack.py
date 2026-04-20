import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Match, Template

from infra.stacks.app_stack import EB_SOLUTION_STACK, AppStack
from infra.stacks.network_stack import NetworkStack

ENV = cdk.Environment(account="123456789012", region="us-east-1")


@pytest.fixture(scope="module")
def template() -> Template:
    app = cdk.App()
    network = NetworkStack(app, "TestNetwork", env=ENV)
    stack = AppStack(app, "TestApp", vpc=network.vpc, eb_sg=network.eb_sg, env=ENV)
    return Template.from_stack(stack)


def test_ecr_repository_exists(template: Template) -> None:
    template.resource_count_is("AWS::ECR::Repository", 1)


def test_ecr_repository_name(template: Template) -> None:
    template.has_resource_properties(
        "AWS::ECR::Repository",
        {"RepositoryName": "huginn"},
    )


def test_ecr_lifecycle_keeps_20_images(template: Template) -> None:
    template.has_resource_properties(
        "AWS::ECR::Repository",
        {"LifecyclePolicy": {"LifecyclePolicyText": Match.string_like_regexp(r".*countNumber.*20.*")}},
    )


def test_eb_application_exists(template: Template) -> None:
    template.resource_count_is("AWS::ElasticBeanstalk::Application", 1)


def test_eb_application_name(template: Template) -> None:
    template.has_resource_properties(
        "AWS::ElasticBeanstalk::Application",
        {"ApplicationName": "huginn"},
    )


def test_two_eb_environments(template: Template) -> None:
    template.resource_count_is("AWS::ElasticBeanstalk::Environment", 2)


def test_eb_environments_use_correct_platform(template: Template) -> None:
    template.has_resource_properties(
        "AWS::ElasticBeanstalk::Environment",
        {"SolutionStackName": EB_SOLUTION_STACK},
    )


def test_eb_environments_single_instance(template: Template) -> None:
    template.has_resource_properties(
        "AWS::ElasticBeanstalk::Environment",
        {
            "OptionSettings": Match.array_with(
                [
                    Match.object_like(
                        {
                            "Namespace": "aws:elasticbeanstalk:environment",
                            "OptionName": "EnvironmentType",
                            "Value": "SingleInstance",
                        }
                    )
                ]
            )
        },
    )


def test_iam_instance_role_exists(template: Template) -> None:
    template.has_resource_properties(
        "AWS::IAM::Role",
        {"RoleName": "aws-elasticbeanstalk-ec2-role"},
    )


def test_gitlab_deploy_user_exists(template: Template) -> None:
    template.has_resource_properties(
        "AWS::IAM::User",
        {"UserName": "huginn-ci"},
    )


def test_cloudwatch_alarm_exists(template: Template) -> None:
    template.resource_count_is("AWS::CloudWatch::Alarm", 1)


def test_cloudwatch_alarm_name(template: Template) -> None:
    template.has_resource_properties(
        "AWS::CloudWatch::Alarm",
        {"AlarmName": "huginn-celery-error-rate"},
    )
