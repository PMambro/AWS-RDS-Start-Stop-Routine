
import boto3

def _off_schedule_yes(tags):
    """
    Retorna True se existir tag OffSchedule com valor '1' (case-insensível).
    """
    for t in tags or []:
        if t.get('Key') == 'OffSchedule' and str(t.get('Value', '')).strip().lower() == '1':
            return True
    return False

def _list_tags(rds, arn, cache):
    """
    Faz cache de ListTagsForResource por ARN.
    """
    if not arn:
        return []
    if arn in cache:
        return cache[arn]
    try:
        resp = rds.list_tags_for_resource(ResourceName=arn)
        cache[arn] = resp.get('TagList', [])
    except Exception as e:
        print(f"[WARN] Falha ao listar tags para {arn}: {e}")
        cache[arn] = []
    return cache[arn]

def lambda_handler(event, context):
    action = (event.get("action") or "").lower()
    if action not in ("start", "stop"):
        return {"error": "missing action (start|stop)"}

    rds = boto3.client("rds")
    affected = {"instances": [], "clusters": []}
    tag_cache = {}  # cache de tags por ARN
    off_schedule_instance_ids = set()  # instâncias (de qualquer engine) com OffSchedule="1"

    # --- Instâncias RDS (inclui Aurora, mas só atuamos nas não-Aurora) ---
    paginator = rds.get_paginator("describe_db_instances")
    for page in paginator.paginate():
        for db in page.get("DBInstances", []):
            dbid = db["DBInstanceIdentifier"]
            engine = (db.get("Engine") or "").lower()
            status = db["DBInstanceStatus"]

            # Verifica tag OffSchedule no nível da instância
            inst_tags = _list_tags(rds, db.get("DBInstanceArn"), tag_cache)
            if _off_schedule_yes(inst_tags):
                off_schedule_instance_ids.add(dbid)
                print(f"[SKIP] Instance {dbid} possui tag OffSchedule=1")
                # Se não for Aurora, também não agir
                if "aurora" not in engine:
                    continue

            # Para Aurora, não agir aqui (será tratado via cluster)
            if "aurora" in engine:
                # Mesmo que não tenha OffSchedule, não atuamos em instância Aurora aqui.
                continue

            # Ação para instâncias não-Aurora
            try:
                if action == "stop" and status == "available":
                    rds.stop_db_instance(DBInstanceIdentifier=dbid)
                    affected["instances"].append({"id": dbid, "action": "stopped"})
                elif action == "start" and status == "stopped":
                    rds.start_db_instance(DBInstanceIdentifier=dbid)
                    affected["instances"].append({"id": dbid, "action": "started"})
                else:
                    print(f"[NO-OP] Instance {dbid} status={status} não elegível para {action}")
            except Exception as e:
                print(f"[ERROR] Instance {dbid}: {e}")

    # --- Clusters Aurora ---
    paginator = rds.get_paginator("describe_db_clusters")
    for page in paginator.paginate():
        for cl in page.get("DBClusters", []):
            cluster_id = cl["DBClusterIdentifier"]
            status = cl["Status"]
            engine = (cl.get("Engine") or "").lower()
            if not engine.startswith("aurora"):
                continue

            # Verifica tag OffSchedule no cluster
            cluster_tags = _list_tags(rds, cl.get("DBClusterArn"), tag_cache)
            cluster_has_off_schedule = _off_schedule_yes(cluster_tags)

            # Se qualquer instância membro tiver OffSchedule=1, também pular o cluster
            member_ids = [m.get("DBInstanceIdentifier") for m in cl.get("DBClusterMembers", [])]
            member_has_off_schedule = any(m_id in off_schedule_instance_ids for m_id in member_ids)

            if cluster_has_off_schedule or member_has_off_schedule:
                print(f"[SKIP] Cluster {cluster_id} marcado OffSchedule (cluster={cluster_has_off_schedule}, member={member_has_off_schedule})")
                continue

            # Ação no cluster
            try:
                if action == "stop" and status == "available":
                    rds.stop_db_cluster(DBClusterIdentifier=cluster_id)
                    affected["clusters"].append({
                        "id": cluster_id,
                        "action": "stopped",
                        "instances": member_ids
                    })
                elif action == "start" and status == "stopped":
                    rds.start_db_cluster(DBClusterIdentifier=cluster_id)
                    affected["clusters"].append({
                        "id": cluster_id,
                        "action": "started",
                        "instances": member_ids
                    })
                else:
                    print(f"[NO-OP] Cluster {cluster_id} status={status} não elegível para {action}")
            except Exception as e:
                print(f"[ERROR] Cluster {cluster_id}: {e}")

    print({"action": action, "affected": affected})
    return {"action": action, "affected": affected}