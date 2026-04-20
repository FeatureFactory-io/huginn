import aws_cdk as cdk
import pytest
from aws_cdk import aws_route53 as route53
from aws_cdk.assertions import Match, Template

from infra.stacks.cdn_stack import CdnStack

ENV = cdk.Environment(account="123456789012", region="us-east-1")
DOMAIN = "featurefactory.io"


def _make_stack() -> tuple[cdk.Stack, Template]:
    """Build a CdnStack with a mocked hosted zone (no AWS lookup call)."""
    app = cdk.App()
    # Provide a dummy scope for the mock zone reference
    helper = cdk.Stack(app, "Helper", env=ENV)
    mock_zone = route53.HostedZone.from_hosted_zone_attributes(
        helper,
        "MockZone",
        hosted_zone_id="Z02538982P10I9062HOIE",
        zone_name=f"{DOMAIN}.",
    )
    stack = CdnStack(app, "TestCdn", domain=DOMAIN, hosted_zone=mock_zone, env=ENV)
    return stack, Template.from_stack(stack)


@pytest.fixture(scope="module")
def template() -> Template:
    _, tmpl = _make_stack()
    return tmpl


def test_one_cloudfront_distribution(template: Template) -> None:
    template.resource_count_is("AWS::CloudFront::Distribution", 1)


def test_one_response_headers_policy_for_hsts(template: Template) -> None:
    template.resource_count_is("AWS::CloudFront::ResponseHeadersPolicy", 1)


def test_hsts_response_headers_match_production_starter(template: Template) -> None:
    template.has_resource_properties(
        "AWS::CloudFront::ResponseHeadersPolicy",
        {
            "ResponseHeadersPolicyConfig": Match.object_like(
                {
                    "SecurityHeadersConfig": Match.object_like(
                        {
                            "StrictTransportSecurity": {
                                "AccessControlMaxAgeSec": 3600,
                                "IncludeSubdomains": True,
                                "Override": True,
                            }
                        }
                    )
                }
            )
        },
    )


def test_one_acm_certificate(template: Template) -> None:
    template.resource_count_is("AWS::CertificateManager::Certificate", 1)


def test_certificate_covers_apex_and_wildcard(template: Template) -> None:
    template.has_resource_properties(
        "AWS::CertificateManager::Certificate",
        {
            "DomainName": DOMAIN,
            "SubjectAlternativeNames": [f"*.{DOMAIN}"],
        },
    )


def test_certificate_uses_dns_validation(template: Template) -> None:
    template.has_resource_properties(
        "AWS::CertificateManager::Certificate",
        {"ValidationMethod": "DNS"},
    )


def test_cname_is_custom_resource_not_raw_recordset(template: Template) -> None:
    """CNAME is applied by a Lambda custom resource (idempotent UPSERT), not AWS::Route53::RecordSet."""
    template.resource_count_is("AWS::Route53::RecordSet", 0)
    template.resource_count_is("AWS::CloudFormation::CustomResource", 1)


def test_cname_custom_resource_properties(template: Template) -> None:
    template.has_resource_properties(
        "AWS::CloudFormation::CustomResource",
        {
            "RecordName": f"huginn.{DOMAIN}.",
            "Ttl": "300",
            "HostedZoneId": "Z02538982P10I9062HOIE",
        },
    )


def test_cloudfront_redirects_http_to_https(template: Template) -> None:
    template.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": Match.object_like(
                {"DefaultCacheBehavior": Match.object_like({"ViewerProtocolPolicy": "redirect-to-https"})}
            )
        },
    )


def test_cloudfront_origin_is_eb_prod_cname(template: Template) -> None:
    template.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": Match.object_like(
                {
                    "Origins": Match.array_with(
                        [
                            Match.object_like(
                                {
                                    "DomainName": "huginn-prod.us-east-1.elasticbeanstalk.com",
                                }
                            )
                        ]
                    )
                }
            )
        },
    )
