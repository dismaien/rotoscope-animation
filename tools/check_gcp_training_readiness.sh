#!/usr/bin/env bash
set -euo pipefail

required_apis=(
  serviceusage.googleapis.com
  compute.googleapis.com
  aiplatform.googleapis.com
)

echo "== GCP Training Readiness =="

if ! command -v gcloud >/dev/null 2>&1; then
  echo "gcloud: missing"
  exit 1
fi

account="$(gcloud auth list --filter=status:ACTIVE --format='value(account)' 2>/dev/null || true)"
project="$(gcloud config get-value project 2>/dev/null || true)"

echo "active_account=${account:-<none>}"
echo "active_project=${project:-<none>}"

if [[ -z "${account}" ]]; then
  echo "status=blocked"
  echo "reason=no_active_gcloud_account"
  exit 0
fi

if [[ -z "${project}" || "${project}" == "(unset)" ]]; then
  echo "status=blocked"
  echo "reason=no_active_gcloud_project"
  exit 0
fi

echo "apis:"
enabled="$(gcloud services list --enabled --project "${project}" --format='value(config.name)' 2>/dev/null || true)"

missing=0
for api in "${required_apis[@]}"; do
  if grep -qx "${api}" <<<"${enabled}"; then
    echo "  ${api}=enabled"
  else
    echo "  ${api}=missing"
    missing=1
  fi
done

if [[ "${missing}" -eq 1 ]]; then
  echo "status=blocked"
  echo "reason=missing_required_apis"
  exit 0
fi

echo "status=ready_for_next_step"
