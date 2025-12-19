
#!/usr/bin/env bash
set -euo pipefail

PROFILE="${1:-default}"
TS() { date +"%Y-%m-%d %H:%M:%S"; }

echo "[$(TS)] Using AWS profile: $PROFILE"

# Get all enabled regions
REGIONS=$(aws ec2 describe-regions \
  --profile "$PROFILE" \
  --query 'Regions[].RegionName' \
  --output text)

if [[ -z "$REGIONS" ]]; then
  echo "[$(TS)] No regions found for this account/profile. Exiting."
  exit 0
fi

total_instances_started=0
total_clusters_started=0

for region in $REGIONS; do
  echo ""
  echo "=== [$(TS)] Region: $region ==="

  # -------------------------------------------
  # Start stopped RDS DB Instances (non-Aurora)
  # -------------------------------------------
  echo "[$(TS)] Checking stopped RDS DB instances in $region..."
  # Filter for instances with status 'stopped'
  mapfile -t stopped_instances < <(aws rds describe-db-instances \
    --region "$region" \
    --profile "$PROFILE" \
    --query 'DBInstances[?DBInstanceStatus==`stopped`].DBInstanceIdentifier' \
    --output text | tr '\t' '\n')

  if [[ ${#stopped_instances[@]} -eq 0 || -z "${stopped_instances[0]:-}" ]]; then
    echo "[$(TS)] No stopped RDS DB instances found in $region."
  else
    echo "[$(TS)] Found ${#stopped_instances[@]} stopped RDS instance(s): ${stopped_instances[*]}"
    for dbid in "${stopped_instances[@]}"; do
      echo "[$(TS)] Starting RDS instance: $dbid"
      if aws rds start-db-instance \
          --region "$region" \
          --profile "$PROFILE" \
          --db-instance-identifier "$dbid" >/dev/null; then
        echo "[$(TS)] Start initiated for RDS instance: $dbid"
        echo "[$(TS)] Waiting until instance is available: $dbid"
        aws rds wait db-instance-available \
          --region "$region" \
          --profile "$PROFILE" \
          --db-instance-identifier "$dbid"
        echo "[$(TS)] RDS instance is available: $dbid"
        ((total_instances_started++))
      else
        echo "[$(TS)] WARNING: Failed to start RDS instance: $dbid (check permissions, support for stop/start, or state)"
      fi
    done
  fi

  # -------------------------------------------
  # Start stopped Aurora DB Clusters
  # -------------------------------------------
  echo "[$(TS)] Checking stopped Aurora DB clusters in $region..."
  # Filter for clusters with status 'stopped'
  mapfile -t stopped_clusters < <(aws rds describe-db-clusters \
    --region "$region" \
    --profile "$PROFILE" \
    --query 'DBClusters[?Status==`stopped`].DBClusterIdentifier' \
    --output text | tr '\t' '\n')

  if [[ ${#stopped_clusters[@]} -eq 0 || -z "${stopped_clusters[0]:-}" ]]; then
    echo "[$(TS)] No stopped Aurora DB clusters found in $region."
  else
    echo "[$(TS)] Found ${#stopped_clusters[@]} stopped Aurora cluster(s): ${stopped_clusters[*]}"
    for cluster_id in "${stopped_clusters[@]}"; do
      echo "[$(TS)] Starting Aurora cluster: $cluster_id"
      if aws rds start-db-cluster \
          --region "$region" \
          --profile "$PROFILE" \
          --db-cluster-identifier "$cluster_id" >/dev/null; then
        echo "[$(TS)] Start initiated for Aurora cluster: $cluster_id"
        echo "[$(TS)] Waiting until cluster is available: $cluster_id"
        aws rds wait db-cluster-available \
          --region "$region" \
          --profile "$PROFILE" \
          --db-cluster-identifier "$cluster_id"
        echo "[$(TS)] Aurora cluster is available: $cluster_id"
        ((total_clusters_started++))
      else
        echo "[$(TS)] WARNING: Failed to start Aurora cluster: $cluster_id (check permissions, engine/edition support, or state)"
      fi
    done
  fi
done

echo ""
echo "=== SUMMARY ==="
echo "[$(TS)] Total RDS instances started : $total_instances_started"
echo "[$(TS)] Total Aurora clusters started: $total_clusters_started"
echo "[$(TS)] Done."
    