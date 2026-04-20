"""CloudFormation custom resource: idempotent Route53 CNAME for huginn → CloudFront.

- If the name does not exist: UPSERT CNAME to the CloudFront domain.
- If a CNAME exists and its value equals the target (case-insensitive, trailing-dot agnostic): no-op.
- If a CNAME exists with a different value: UPSERT to the target.

On Delete: remove the CNAME only if it still points at the target we manage (avoids deleting unrelated records).
"""

from __future__ import annotations

import copy
from typing import Any

import boto3

route53 = boto3.client("route53")


def on_event(event: dict[str, Any], _context: object) -> dict[str, Any]:
    props = event["ResourceProperties"]
    zone_id = props["HostedZoneId"]
    record_name = _ensure_trailing_dot(props["RecordName"])
    target = props["TargetDomain"].rstrip(".")
    ttl = int(props.get("Ttl", "300"))

    request_type = event["RequestType"]
    physical_id = f"{zone_id}|{record_name}"

    if request_type == "Delete":
        return _on_delete(event, zone_id, record_name, target, physical_id)

    return _on_create_or_update(zone_id, record_name, target, ttl, physical_id)


def _on_delete(
    event: dict[str, Any],
    zone_id: str,
    record_name: str,
    target: str,
    physical_id: str,
) -> dict[str, Any]:
    """Remove the CNAME only if it still points at our CloudFront (or matches target)."""
    props = event.get("ResourceProperties") or {}
    expected = props.get("TargetDomain", target or "").rstrip(".").lower()

    existing = _find_cname(zone_id, record_name)
    if not existing:
        return {"PhysicalResourceId": physical_id}

    current_val = _cname_value(existing).rstrip(".").lower()

    safe_to_remove = False
    if expected and current_val == expected:
        safe_to_remove = True
    elif not expected and current_val.endswith(".cloudfront.net"):
        # Delete can arrive with empty ResourceProperties (rollback). If the
        # record points at CloudFront, assume we own it for this subdomain.
        safe_to_remove = True

    if not safe_to_remove:
        return {"PhysicalResourceId": physical_id}

    rrs = copy.deepcopy(existing)
    route53.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={"Changes": [{"Action": "DELETE", "ResourceRecordSet": rrs}]},
    )
    return {"PhysicalResourceId": physical_id}


def _on_create_or_update(
    zone_id: str,
    record_name: str,
    target: str,
    ttl: int,
    physical_id: str,
) -> dict[str, Any]:
    existing = _find_cname(zone_id, record_name)
    if existing:
        if _cname_value(existing).rstrip(".").lower() == target.lower():
            return {
                "PhysicalResourceId": physical_id,
                "Data": {"Status": "UNCHANGED"},
            }

    route53.change_resource_record_sets(
        HostedZoneId=zone_id,
        ChangeBatch={
            "Changes": [
                {
                    "Action": "UPSERT",
                    "ResourceRecordSet": {
                        "Name": record_name,
                        "Type": "CNAME",
                        "TTL": ttl,
                        "ResourceRecords": [{"Value": _cname_rdata_value(target)}],
                    },
                }
            ]
        },
    )
    return {"PhysicalResourceId": physical_id, "Data": {"Status": "UPSERTED"}}


def _find_cname(zone_id: str, record_name: str) -> dict[str, Any] | None:
    """Return the full ResourceRecordSet dict for a CNAME at record_name, or None."""
    paginator = route53.get_paginator("list_resource_record_sets")
    want = record_name.lower()
    for page in paginator.paginate(HostedZoneId=zone_id):
        for rec in page["ResourceRecordSets"]:
            if rec["Type"] == "CNAME" and rec["Name"].lower() == want:
                return rec
    return None


def _cname_value(rec: dict[str, Any]) -> str:
    return rec["ResourceRecords"][0]["Value"]


def _cname_rdata_value(target: str) -> str:
    """Route53 CNAME RDATA is a single DNS name; use trailing dot."""
    t = target.rstrip(".")
    return f"{t}."


def _ensure_trailing_dot(name: str) -> str:
    return name if name.endswith(".") else f"{name}."
