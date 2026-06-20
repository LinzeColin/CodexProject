from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb


class RepositoryError(RuntimeError):
    pass


class NotFoundError(RepositoryError):
    pass


class ConflictError(RepositoryError):
    def __init__(self, detail: dict[str, Any]) -> None:
        super().__init__(str(detail))
        self.detail = detail


def _jsonable(value: Any) -> Any:
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, datetime):
        serialized = value.isoformat()
        if value.utcoffset() == timedelta(0) and serialized.endswith("+00:00"):
            return f"{serialized[:-6]}Z"
        return serialized
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [_jsonable(item) for item in value]
    return value


def _now() -> datetime:
    return datetime.now(tz=UTC)


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


ROOT = Path(__file__).resolve().parents[3]
EXPLORATION_STATE_VERSION = "exploration-state-v1"
SAVED_VIEW_SCHEMA_VERSION = "saved-view-v1"
DEFAULT_GRAPH_BUDGET = {"max_nodes": 42, "max_edges": 64, "expand_nodes": 12}
GRAPH_HARD_LIMITS = {"max_hops": 2, "max_nodes": 500, "max_edges": 2000, "max_path_length": 8}
PATH_RESULT_LIMIT = 8
GRAPH_QUERY_VERSION = "bounded-recursive-graph-v1"
SCORING_SERVICE_VERSION = "candidate-score-explanation-v1"
CANDIDATE_SOURCE_THRESHOLD_MIN = 2
ACTIVE_REFRESH_MODULES = [
    "business_empire",
    "group_structure",
    "business_segments",
    "supply_chain",
    "capital_network",
    "ma_transactions",
    "control_relationships",
    "policy_environment",
    "strategic_signals",
    "watchlist",
    "evidence_center",
    "model_center",
    "data_center",
]
RELATIONSHIP_FAMILIES = {
    "corporate_structure",
    "ownership_control",
    "supply_chain_operations",
    "capital_financing",
    "mergers_acquisitions",
    "governance_people",
    "commercial_dependency",
    "technology_data_ip",
    "government_policy",
    "strategic_signal",
}
LAYER_RELATIONSHIP_FAMILY_MAP = {
    "all": RELATIONSHIP_FAMILIES,
    "business_segments": {"corporate_structure", "commercial_dependency"},
    "capital_control": {"ownership_control", "capital_financing", "mergers_acquisitions"},
    "capital_transactions": {"capital_financing", "mergers_acquisitions"},
    "commercial_dependency": {"commercial_dependency"},
    "corporate_structure": {"corporate_structure"},
    "governance_people": {"governance_people"},
    "ownership_control": {"ownership_control"},
    "policy_regulatory": {"government_policy"},
    "strategic_signal": {"strategic_signal"},
    "supply_chain_operations": {"supply_chain_operations"},
    "technology_data_ip": {"technology_data_ip"},
}
DOSSIER_LAYER_DEFINITIONS = {
    "business": {
        "label": "Business context",
        "families": {"corporate_structure", "commercial_dependency"},
        "gap": "No business-segment or commercial-dependency fixture records are loaded.",
    },
    "group": {
        "label": "Group and control context",
        "families": {"corporate_structure", "ownership_control"},
        "gap": "No group, ownership, or control fixture records are loaded.",
    },
    "dependencies": {
        "label": "Supply-chain and platform dependencies",
        "families": {"supply_chain_operations", "commercial_dependency", "technology_data_ip"},
        "gap": "No supply-chain, commercial-dependency, or technology fixture records are loaded.",
    },
    "capital": {
        "label": "Capital and M&A context",
        "families": {"capital_financing", "mergers_acquisitions", "ownership_control"},
        "gap": "No direct capital, M&A, or ownership-control fixture records are loaded.",
    },
    "policy": {
        "label": "Policy and government context",
        "families": {"government_policy"},
        "gap": (
            "No direct policy, government contract, subsidy, or regulatory fixture "
            "records are loaded."
        ),
    },
    "signals": {
        "label": "Strategic signals",
        "families": {"strategic_signal", "technology_data_ip"},
        "gap": "No strategic-signal or technology fixture records are loaded.",
    },
}
EMPIRE_WORKSPACE_LAYERS = (
    {
        "key": "group_structure",
        "label_zh": "集团结构",
        "label_en": "Group Structure",
        "description": "Legal group, parent, subsidiary and operating-entity structure.",
    },
    {
        "key": "business_segments",
        "label_zh": "业务板块",
        "label_en": "Business Segments",
        "description": "Business segments, product lines, platforms and markets.",
    },
    {
        "key": "supply_chain",
        "label_zh": "供应链",
        "label_en": "Supply Chain",
        "description": "Upstream, downstream, stage and dependency relationships.",
    },
    {
        "key": "capital_network",
        "label_zh": "资本网络",
        "label_en": "Capital Network",
        "description": "Financing, investment, funds, buybacks and capex.",
    },
    {
        "key": "ma_transactions",
        "label_zh": "并购交易",
        "label_en": "M&A Transactions",
        "description": "Acquisitions, divestitures, splits, mergers and strategic investments.",
    },
    {
        "key": "control_relationships",
        "label_zh": "控制关系",
        "label_en": "Control Relationships",
        "description": "Voting rights, economic interest, board seats and actual control paths.",
    },
    {
        "key": "policy_environment",
        "label_zh": "政策环境",
        "label_en": "Policy Environment",
        "description": "Subsidies, contracts, regulations, export controls and lobbying.",
    },
    {
        "key": "strategic_signals",
        "label_zh": "战略信号",
        "label_en": "Strategic Signals",
        "description": "Hiring, capex, patents, partnerships and management statements.",
    },
)
EMPIRE_STRUCTURE_SECTIONS = {
    "legal_group": {
        "label": "Legal group",
        "gap": "No parent, subsidiary or legal-control relationship is loaded.",
    },
    "business_segments": {
        "label": "Business segments",
        "gap": "No business-segment relationship is loaded.",
    },
    "brands": {
        "label": "Brands",
        "gap": "No brand relationship is loaded.",
    },
    "products": {
        "label": "Products",
        "gap": "No product relationship is loaded.",
    },
    "facilities": {
        "label": "Facilities",
        "gap": "No direct facility operation or ownership relationship is loaded.",
    },
}
PATH_TYPE_RELATIONSHIP_FAMILY_MAP = {
    "shortest": RELATIONSHIP_FAMILIES,
    "upstream": {"supply_chain_operations"},
    "downstream": {"supply_chain_operations"},
    "control": {"ownership_control"},
    "capital": {"capital_financing", "mergers_acquisitions"},
    "policy": {"government_policy"},
    "bottleneck": {"supply_chain_operations"},
}
ENTITY_TYPES = (
    "legal_entity",
    "brand",
    "security",
    "fund",
    "government_body",
    "person",
    "theme",
    "facility",
    "product",
    "business_segment",
    "industry",
    "contract",
    "standard",
    "asset",
)


def _relationship_families_for_layers(layers: list[str]) -> list[str]:
    families: set[str] = set()
    for layer in layers:
        families.update(LAYER_RELATIONSHIP_FAMILY_MAP.get(layer, {layer}))
    return sorted(family for family in families if family in RELATIONSHIP_FAMILIES)


def _relationship_family_filter(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list | tuple | set):
        return [str(item) for item in value]
    return [str(value)]


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _catalog_key(path: str) -> str:
    return Path(path).stem.replace("_catalog", "").replace("_taxonomy", "").replace("_", "-")


@dataclass(frozen=True)
class CatalogRepository:
    root: Path = ROOT

    object_scope_paths: tuple[str, ...] = (
        "data/relationship_family_catalog.csv",
        "data/relationship_taxonomy.csv",
        "data/supply_chain_stage_taxonomy.csv",
        "data/upstream_downstream_role_catalog.csv",
        "data/industry_taxonomy.csv",
        "data/sector_taxonomy.csv",
        "data/business_segment_taxonomy.csv",
        "data/capital_object_taxonomy.csv",
        "data/domain_object_catalog.csv",
        "data/company_catalog.csv",
    )

    def _content_inventory(self) -> list[dict[str, str]]:
        return _read_csv(self.root / "data/content_inventory.csv")

    def _manifest_by_path(self) -> dict[str, dict[str, str]]:
        return {
            row["catalog_path"]: row
            for row in _read_csv(self.root / "data/data_catalog_manifest.csv")
        }

    def list_catalogs(self) -> dict[str, Any]:
        manifest = self._manifest_by_path()
        catalogs = [
            self._catalog_summary(row, manifest.get(row["path"], {}))
            for row in self._content_inventory()
        ]
        return {
            "as_of": _now().isoformat(),
            "catalog_version": "v4.2.0",
            "catalog_count": len(catalogs),
            "source_of_truth_count": sum(1 for row in catalogs if row["source_of_truth"]),
            "total_declared_rows": sum(row["row_count"] for row in catalogs),
            "catalogs": catalogs,
        }

    def get_catalog(self, catalog_key: str) -> dict[str, Any]:
        manifest = self._manifest_by_path()
        for row in self._content_inventory():
            summary = self._catalog_summary(row, manifest.get(row["path"], {}))
            if summary["catalog_key"] == catalog_key:
                csv_path = self.root / row["path"]
                records = _read_csv(csv_path)
                return {
                    **summary,
                    "as_of": _now().isoformat(),
                    "fields": list(records[0].keys()) if records else [],
                    "records": records,
                    "actual_row_count": len(records),
                }
        raise NotFoundError(f"Catalog not found: {catalog_key}")

    def csv_path_for_key(self, catalog_key: str) -> Path:
        for row in self._content_inventory():
            if _catalog_key(row["path"]) == catalog_key:
                path = (self.root / row["path"]).resolve()
                if not path.is_relative_to(self.root):
                    raise NotFoundError(f"Catalog not found: {catalog_key}")
                return path
        raise NotFoundError(f"Catalog not found: {catalog_key}")

    def object_scope(self) -> dict[str, Any]:
        catalog_map = {row["path"]: row for row in self._content_inventory()}
        manifest = self._manifest_by_path()
        catalogs = [
            self._catalog_summary(catalog_map[path], manifest.get(path, {}))
            for path in self.object_scope_paths
        ]
        counts = {row["catalog_key"]: row["row_count"] for row in catalogs}
        return {
            "as_of": _now().isoformat(),
            "catalog_version": "v4.2.0",
            "navigation_module": {
                "name_zh": "对象与范围",
                "name_en": "Objects and Scope",
                "visible": True,
                "route": "/objects-scope",
                "api_paths": [
                    "/v1/system/object-scope",
                    "/v1/catalogs",
                    "/v1/catalogs/{catalogKey}",
                ],
                "source_doc": "docs/31_DOMAIN_OBJECT_SCOPE_CATALOG.md",
                "acceptance_ids": ["A169", "A170"],
            },
            "coverage": {
                "required_catalogs_present": True,
                "object_scope_catalog_count": len(catalogs),
                "total_declared_rows": sum(row["row_count"] for row in catalogs),
                "relationship_families": counts["relationship-family"],
                "relationship_types": counts["relationship"],
                "upstream_downstream_roles": counts["upstream-downstream-role"],
                "supply_chain_stages": counts["supply-chain-stage"],
                "industries": counts["industry"],
                "sectors": counts["sector"],
                "business_segments": counts["business-segment"],
                "capital_objects": counts["capital-object"],
                "domain_objects": counts["domain-object"],
                "companies": counts["company"],
            },
            "catalogs": catalogs,
        }

    def _catalog_summary(self, row: dict[str, str], manifest: dict[str, str]) -> dict[str, Any]:
        path = row["path"]
        row_count = int(manifest.get("row_count") or row["row_count"])
        catalog_key = _catalog_key(path)
        return {
            "catalog_id": row["catalog_id"],
            "catalog_key": catalog_key,
            "name_zh": row["name_zh"],
            "path": path,
            "primary_key": manifest.get("primary_key") or row["primary_key"],
            "row_count": row_count,
            "owner": manifest.get("owner") or row["owner"],
            "ui_surfaces": row["ui_surfaces"],
            "scope": row["scope"],
            "status": row["status"],
            "source_of_truth": (manifest.get("source_of_truth") or row["source_of_truth"]).lower()
            in {"yes", "true"},
            "export_links": {
                "json": f"/v1/catalogs/{catalog_key}",
                "csv": f"/v1/catalogs/{catalog_key}?format=csv",
                "source": path,
            },
        }


@dataclass(frozen=True)
class DomainRepository:
    database_url: str

    def connect(self) -> psycopg.Connection[dict[str, Any]]:
        return psycopg.connect(self.database_url, connect_timeout=5, row_factory=dict_row)

    def search_entities(
        self,
        query: str | None,
        entity_type: str | None,
        limit: int,
    ) -> list[dict[str, Any]]:
        search_term = (query or "").strip()
        pattern = f"%{_escape_like(search_term)}%"
        with self.connect() as connection:
            rows = connection.execute(
                """
                WITH matches AS (
                  SELECT
                    e.id,
                    e.canonical_name,
                    e.entity_type,
                    fen.fixture_notice,
                    COALESCE(fen.synthetic, false) AS synthetic,
                    'canonical' AS match_type,
                    e.canonical_name AS matched_value,
                    1 AS rank
                  FROM entities e
                  LEFT JOIN fixture_entity_notices fen ON fen.entity_id = e.id
                  WHERE (
                    %(entity_type)s::entity_type IS NULL
                    OR e.entity_type = %(entity_type)s::entity_type
                  )
                    AND (
                      %(query)s = ''
                      OR e.canonical_name ILIKE %(pattern)s ESCAPE '\\'
                    )
                  UNION ALL
                  SELECT
                    e.id,
                    e.canonical_name,
                    e.entity_type,
                    fen.fixture_notice,
                    COALESCE(fen.synthetic, false) AS synthetic,
                    lower(ei.scheme) AS match_type,
                    ei.value AS matched_value,
                    2 AS rank
                  FROM entities e
                  JOIN entity_identifiers ei ON ei.entity_id = e.id
                  LEFT JOIN fixture_entity_notices fen ON fen.entity_id = e.id
                  WHERE (
                    %(entity_type)s::entity_type IS NULL
                    OR e.entity_type = %(entity_type)s::entity_type
                  )
                    AND (%(query)s = '' OR ei.value ILIKE %(pattern)s ESCAPE '\\')
                  UNION ALL
                  SELECT
                    e.id,
                    e.canonical_name,
                    e.entity_type,
                    fen.fixture_notice,
                    COALESCE(fen.synthetic, false) AS synthetic,
                    'alias:' || ea.alias_type AS match_type,
                    ea.alias AS matched_value,
                    3 AS rank
                  FROM entities e
                  JOIN entity_aliases ea ON ea.entity_id = e.id
                  LEFT JOIN fixture_entity_notices fen ON fen.entity_id = e.id
                  WHERE (
                    %(entity_type)s::entity_type IS NULL
                    OR e.entity_type = %(entity_type)s::entity_type
                  )
                    AND (%(query)s = '' OR ea.alias ILIKE %(pattern)s ESCAPE '\\')
                ),
                ranked AS (
                  SELECT DISTINCT ON (id)
                    id, canonical_name, entity_type, fixture_notice, synthetic,
                    match_type, matched_value, rank
                  FROM matches
                  ORDER BY id, rank, length(matched_value), matched_value
                )
                SELECT id, canonical_name, entity_type, fixture_notice, synthetic,
                       match_type, matched_value
                FROM ranked
                ORDER BY rank, canonical_name
                LIMIT %(limit)s
                """,
                {
                    "query": search_term,
                    "pattern": pattern,
                    "entity_type": entity_type,
                    "limit": limit,
                },
            ).fetchall()
            return self._with_primary_identifiers(connection, rows)

    def entity_summary(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        entity_id: UUID,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT e.id, e.canonical_name, e.entity_type, fen.fixture_notice, fen.synthetic
            FROM entities e
            LEFT JOIN fixture_entity_notices fen ON fen.entity_id = e.id
            WHERE e.id = %s
            """,
            (entity_id,),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"Entity not found: {entity_id}")
        identifier_rows = connection.execute(
            """
            SELECT scheme, value
            FROM entity_identifiers
            WHERE entity_id = %s
            ORDER BY scheme
            """,
            (entity_id,),
        ).fetchall()
        payload = dict(row)
        payload["primary_identifiers"] = {
            item["scheme"]: item["value"] for item in identifier_rows
        }
        return _jsonable(payload)

    def get_entity(self, entity_id: UUID) -> dict[str, Any]:
        with self.connect() as connection:
            entity = self.entity_summary(connection, entity_id)
            aliases = self.aliases_for_entity(connection, entity_id)
            industries = self.industry_memberships_for_entities(
                connection,
                [entity_id],
            ).get(entity_id, [])
            relationships = self.relationship_summaries_for_entities(
                connection,
                [entity_id],
                families=sorted(RELATIONSHIP_FAMILIES),
                limit=80,
            )
            recent_events = self.event_summaries_for_entity(connection, entity_id, limit=8)
            dossier_layers = self.entity_dossier_layers(
                relationships=relationships,
                industries=industries,
            )
            relationships_summary = self.relationship_family_counts(relationships)
            freshness = self.entity_dossier_freshness(
                entity=entity,
                relationships=relationships,
                events=recent_events,
            )
            coverage = self.entity_dossier_coverage(
                relationships=relationships,
                industries=industries,
                events=recent_events,
                layers=dossier_layers,
            )
            human_summary = self.entity_human_summary(
                entity=entity,
                industries=industries,
                events=recent_events,
                layers=dossier_layers,
            )
            return _jsonable(
                {
                    **entity,
                    "aliases": aliases,
                    "industries": industries,
                    "relationships_summary": relationships_summary,
                    "dossier_layers": dossier_layers,
                    "recent_events": recent_events,
                    "freshness": freshness,
                    "coverage": coverage,
                    "human_summary": human_summary,
                    "focus_route": f"/v1/entities/{entity_id}",
                    "ui_route": f"/?focus=entity:{entity_id}",
                    "data_mode": freshness["data_mode"],
                }
            )

    def get_entity_empire(
        self,
        *,
        entity_id: UUID,
        as_of: datetime | None = None,
        profile_id: UUID | None = None,
    ) -> dict[str, Any]:
        with self.connect() as connection:
            focus = self.entity_summary(connection, entity_id)
            direct_relationships = self.corporate_structure_relationships_for_entity(
                connection,
                entity_id,
                as_of=as_of,
            )
            adjacent_facilities = self.adjacent_facility_relationships_for_entity(
                connection,
                entity_id,
                as_of=as_of,
            )
            structure = self.entity_empire_structure(
                focus=focus,
                direct_relationships=direct_relationships,
                adjacent_facilities=adjacent_facilities,
            )
            return _jsonable(
                {
                    "as_of": as_of or _now(),
                    "profile_id": profile_id,
                    "focus": focus,
                    "workspace_layers": list(EMPIRE_WORKSPACE_LAYERS),
                    "structure": structure,
                    "content_rules": {
                        "commercial_empire_is_legal_control": False,
                        "commercial_empire_label": (
                            "Commercial empire is an ecosystem relationship view, "
                            "not a legal-control assertion."
                        ),
                        "legal_control_requires": [
                            "legal_parent",
                            "ownership_control",
                            "voting_right",
                            "board_control",
                        ],
                        "facility_policy": (
                            "Adjacent facilities may indicate ecosystem exposure; they do "
                            "not imply ownership or operation by the focus entity."
                        ),
                    },
                    "coverage": {
                        "required_workspace_layer_count": len(EMPIRE_WORKSPACE_LAYERS),
                        "required_workspace_layers_present": True,
                        "separated_structure_types": list(EMPIRE_STRUCTURE_SECTIONS),
                        "separates_legal_group_segment_brand_product_facility": True,
                        "commercial_empire_control_claim": False,
                        "direct_structure_relationship_count": len(direct_relationships),
                        "adjacent_facility_relationship_count": len(adjacent_facilities),
                    },
                    "data_mode": "synthetic_fixture" if focus.get("synthetic") else "database",
                    "fixture_notice": focus.get("fixture_notice"),
                }
            )

    def list_industries(self, parent: UUID | None = None) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return self.list_industries_for_connection(connection, parent=parent)

    def list_industries_for_connection(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        *,
        parent: UUID | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        where = "i.active = true"
        params: list[Any] = []
        if parent is not None:
            where = f"{where} AND i.parent_id = %s"
            params.append(parent)
        limit_clause = ""
        if limit is not None:
            limit_clause = "LIMIT %s"
            params.append(limit)
        rows = connection.execute(
            f"""
            SELECT
              i.id, i.external_id, i.slug, i.name_zh, i.name_en, i.parent_id, i.kind,
              i.taxonomy_version,
              count(DISTINCT eim.entity_id)::int AS entity_count,
              count(DISTINCT CASE WHEN eim.role = 'primary' THEN eim.entity_id END)::int
                AS primary_entity_count,
              count(DISTINCT CASE WHEN eim.role = 'secondary' THEN eim.entity_id END)::int
                AS secondary_entity_count,
              count(DISTINCT c.id)::int AS recent_change_count
            FROM industries i
            LEFT JOIN entity_industry_memberships eim ON eim.industry_id = i.id
            LEFT JOIN changes c ON c.object_type = 'industry' AND c.object_id = i.id
            WHERE {where}
            GROUP BY i.id
            ORDER BY
              CASE i.kind WHEN 'industry' THEN 0 ELSE 1 END,
              i.slug
            {limit_clause}
            """,
            params,
        ).fetchall()
        return _jsonable(rows)

    def industry_summary(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        industry_id: UUID,
    ) -> dict[str, Any]:
        rows = connection.execute(
            """
            SELECT
              i.id, i.external_id, i.slug, i.name_zh, i.name_en, i.parent_id, i.kind,
              i.taxonomy_version,
              count(DISTINCT eim.entity_id)::int AS entity_count,
              count(DISTINCT CASE WHEN eim.role = 'primary' THEN eim.entity_id END)::int
                AS primary_entity_count,
              count(DISTINCT CASE WHEN eim.role = 'secondary' THEN eim.entity_id END)::int
                AS secondary_entity_count,
              count(DISTINCT c.id)::int AS recent_change_count
            FROM industries i
            LEFT JOIN entity_industry_memberships eim ON eim.industry_id = i.id
            LEFT JOIN changes c ON c.object_type = 'industry' AND c.object_id = i.id
            WHERE i.id = %s AND i.active = true
            GROUP BY i.id
            """,
            (industry_id,),
        ).fetchall()
        if not rows:
            raise NotFoundError(f"Industry not found: {industry_id}")
        return _jsonable(rows[0])

    def industry_memberships_for_entities(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        entity_ids: list[UUID],
    ) -> dict[UUID, list[dict[str, Any]]]:
        if not entity_ids:
            return {}
        rows = connection.execute(
            """
            SELECT
              eim.entity_id, eim.role, eim.confidence, eim.valid_from, eim.valid_to,
              i.id AS industry_id, i.external_id, i.slug, i.name_zh, i.name_en,
              i.kind, i.parent_id, i.taxonomy_version
            FROM entity_industry_memberships eim
            JOIN industries i ON i.id = eim.industry_id
            WHERE eim.entity_id = ANY(%s)
            ORDER BY
              CASE eim.role WHEN 'primary' THEN 0 WHEN 'secondary' THEN 1 ELSE 2 END,
              i.slug
            """,
            (entity_ids,),
        ).fetchall()
        memberships: dict[UUID, list[dict[str, Any]]] = {}
        for row in rows:
            memberships.setdefault(row["entity_id"], []).append(
                _jsonable(
                    {
                        "industry_id": row["industry_id"],
                        "external_id": row["external_id"],
                        "slug": row["slug"],
                        "name_zh": row["name_zh"],
                        "name_en": row["name_en"],
                        "kind": row["kind"],
                        "parent_id": row["parent_id"],
                        "taxonomy_version": row["taxonomy_version"],
                        "role": row["role"],
                        "confidence": row["confidence"],
                        "valid_from": row["valid_from"],
                        "valid_to": row["valid_to"],
                    }
                )
            )
        return memberships

    def get_industry_landscape(
        self,
        *,
        industry_id: UUID,
        as_of: datetime | None = None,
        profile_id: UUID | None = None,
    ) -> dict[str, Any]:
        with self.connect() as connection:
            industry = self.industry_summary(connection, industry_id)
            selected_rows = connection.execute(
                """
                WITH RECURSIVE selected AS (
                  SELECT id FROM industries WHERE id = %s AND active = true
                  UNION ALL
                  SELECT child.id
                  FROM industries child
                  JOIN selected parent ON child.parent_id = parent.id
                  WHERE child.active = true
                )
                SELECT id FROM selected
                """,
                (industry_id,),
            ).fetchall()
            selected_ids = [row["id"] for row in selected_rows]
            subindustries = self.list_industries_for_connection(
                connection,
                parent=industry_id,
            )
            entity_rows = connection.execute(
                """
                SELECT
                  e.id, e.canonical_name, e.entity_type, fen.fixture_notice,
                  COALESCE(fen.synthetic, false) AS synthetic,
                  min(
                    CASE eim.role WHEN 'primary' THEN 0 WHEN 'secondary' THEN 1 ELSE 2 END
                  ) AS membership_rank,
                  max(eim.confidence) AS membership_confidence,
                  array_agg(DISTINCT eim.role ORDER BY eim.role) AS membership_roles
                FROM entity_industry_memberships eim
                JOIN entities e ON e.id = eim.entity_id
                LEFT JOIN fixture_entity_notices fen ON fen.entity_id = e.id
                WHERE eim.industry_id = ANY(%s)
                GROUP BY e.id, fen.fixture_notice, fen.synthetic
                ORDER BY membership_rank, membership_confidence DESC NULLS LAST, e.canonical_name
                LIMIT 80
                """,
                (selected_ids,),
            ).fetchall()
            entity_ids = [row["id"] for row in entity_rows]
            memberships = self.industry_memberships_for_entities(connection, entity_ids)
            selected_id_strings = {str(item) for item in selected_ids}
            entities = []
            for row in entity_rows:
                entity_memberships = memberships.get(row["id"], [])
                primary = next(
                    (
                        item
                        for item in entity_memberships
                        if item["role"] == "primary"
                    ),
                    None,
                )
                secondary_ids = [
                    item["industry_id"]
                    for item in entity_memberships
                    if item["role"] == "secondary"
                ]
                cross_industry = any(
                    item["industry_id"] not in selected_id_strings
                    for item in entity_memberships
                )
                entities.append(
                    _jsonable(
                        {
                            **dict(row),
                            "industries": entity_memberships,
                            "primary_industry_id": primary["industry_id"] if primary else None,
                            "secondary_industry_ids": secondary_ids,
                            "cross_industry": cross_industry,
                        }
                    )
                )
            stage_rows = self.industry_chain_stages(connection, entity_ids)
            bottlenecks = self.industry_bottlenecks(connection, entity_ids)
            capital = self.relationship_summaries_for_entities(
                connection,
                entity_ids,
                families=["capital_financing"],
                limit=12,
            )
            policy = self.relationship_summaries_for_entities(
                connection,
                entity_ids,
                families=["government_policy"],
                limit=12,
            )
            cross_links = self.cross_industry_links(
                connection,
                member_ids=entity_ids,
                selected_industry_ids=selected_ids,
            )
            return _jsonable(
                {
                    "as_of": as_of or _now(),
                    "profile_id": profile_id,
                    "industry": industry,
                    "taxonomy_version": industry["taxonomy_version"],
                    "subindustries": subindustries,
                    "chain_stages": stage_rows,
                    "entities": entities,
                    "bottlenecks": bottlenecks,
                    "capital": capital,
                    "policy": policy,
                    "changes": self.list_changes_for_connection(connection, limit=8),
                    "cross_industry_links": cross_links,
                    "navigation": {
                        "cross_industry_allowed": True,
                        "indicator": "cross_industry",
                    },
                    "coverage": {
                        "selected_industry_count": len(selected_ids),
                        "entity_count": len(entities),
                        "chain_stage_count": len(stage_rows),
                        "bottleneck_count": len(bottlenecks),
                        "capital_relationship_count": len(capital),
                        "policy_relationship_count": len(policy),
                        "cross_industry_link_count": len(cross_links),
                    },
                    "data_mode": "synthetic_fixture" if any(row["synthetic"] for row in entities)
                    else "catalog_only",
                    "fixture_notice": (
                        "Synthetic fixtures are explicitly marked and not live facts."
                    ),
                }
            )

    def industry_chain_stages(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        entity_ids: list[UUID],
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT
              sc.stage_id, sc.slug, sc.name_zh, sc.name_en, sc.default_direction,
              sc.stage_order,
              count(DISTINCT r.id)::int AS relationship_count,
              count(DISTINCT r.id) FILTER (
                WHERE sca.materiality IN ('critical', 'high')
              )::int AS bottleneck_count
            FROM supply_chain_stages sc
            LEFT JOIN supply_chain_relationship_attributes sca
              ON sc.stage_id IN (sca.stage_from, sca.stage_to)
            LEFT JOIN relationships r
              ON r.id = sca.relationship_id
             AND r.status NOT IN ('superseded', 'revoked')
             AND (
               r.subject_entity_id = ANY(%s)
               OR r.object_entity_id = ANY(%s)
             )
            GROUP BY sc.stage_id, sc.slug, sc.name_zh, sc.name_en,
                     sc.default_direction, sc.stage_order
            ORDER BY sc.stage_order
            """,
            (entity_ids, entity_ids),
        ).fetchall()
        return _jsonable(rows)

    def industry_bottlenecks(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        entity_ids: list[UUID],
    ) -> list[dict[str, Any]]:
        if not entity_ids:
            return []
        rows = connection.execute(
            """
            SELECT
              r.id, r.relationship_type, r.relationship_family, r.confidence,
              r.status, r.observed_at, r.qualifiers,
              sca.stage_from, sca.stage_to, sca.tier, sca.materiality,
              subject.id AS subject_id, subject.canonical_name AS subject_name,
              object.id AS object_id, object.canonical_name AS object_name,
              frn.fixture_notice, COALESCE(frn.synthetic, false) AS synthetic
            FROM relationships r
            JOIN supply_chain_relationship_attributes sca ON sca.relationship_id = r.id
            JOIN entities subject ON subject.id = r.subject_entity_id
            JOIN entities object ON object.id = r.object_entity_id
            LEFT JOIN fixture_relationship_notices frn ON frn.relationship_id = r.id
            WHERE r.status NOT IN ('superseded', 'revoked')
              AND sca.materiality IN ('critical', 'high')
              AND (
                r.subject_entity_id = ANY(%s)
                OR r.object_entity_id = ANY(%s)
              )
            ORDER BY
              CASE sca.materiality WHEN 'critical' THEN 0 WHEN 'high' THEN 1 ELSE 2 END,
              r.confidence DESC NULLS LAST,
              r.observed_at DESC
            LIMIT 12
            """,
            (entity_ids, entity_ids),
        ).fetchall()
        return _jsonable(rows)

    def relationship_summaries_for_entities(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        entity_ids: list[UUID],
        *,
        families: list[str],
        limit: int,
    ) -> list[dict[str, Any]]:
        if not entity_ids:
            return []
        rows = connection.execute(
            """
            SELECT
              r.id, r.relationship_type, r.relationship_family, r.confidence,
              r.status, r.observed_at, r.amount, r.currency, r.amount_kind,
              r.qualifiers,
              subject.id AS subject_id, subject.canonical_name AS subject_name,
              object.id AS object_id, object.canonical_name AS object_name,
              frn.fixture_notice, COALESCE(frn.synthetic, false) AS synthetic
            FROM relationships r
            JOIN entities subject ON subject.id = r.subject_entity_id
            JOIN entities object ON object.id = r.object_entity_id
            LEFT JOIN fixture_relationship_notices frn ON frn.relationship_id = r.id
            WHERE r.status NOT IN ('superseded', 'revoked')
              AND r.relationship_family = ANY(%s)
              AND (
                r.subject_entity_id = ANY(%s)
                OR r.object_entity_id = ANY(%s)
              )
            ORDER BY r.confidence DESC NULLS LAST, r.observed_at DESC, r.id
            LIMIT %s
            """,
            (families, entity_ids, entity_ids, limit),
        ).fetchall()
        return _jsonable(rows)

    def aliases_for_entity(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        entity_id: UUID,
    ) -> list[str]:
        rows = connection.execute(
            """
            SELECT alias
            FROM entity_aliases
            WHERE entity_id = %s
            ORDER BY alias_type, alias
            """,
            (entity_id,),
        ).fetchall()
        return [row["alias"] for row in rows]

    def event_summaries_for_entity(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        entity_id: UUID,
        *,
        limit: int,
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT
              ev.id, ev.event_type, ev.title, ev.status, ev.announced_at,
              ev.effective_at, ev.period_start, ev.period_end, ev.observed_at,
              ev.amount, ev.currency, ev.amount_kind, ev.description, ev.qualifiers,
              (
                SELECT count(*)::int
                FROM event_evidence ee
                WHERE ee.event_id = ev.id
              ) AS evidence_count,
              (
                SELECT COALESCE(
                  jsonb_agg(
                    jsonb_build_object(
                      'entity_id', ep.entity_id,
                      'role', ep.role,
                      'direction', ep.direction
                    )
                    ORDER BY ep.role, ep.entity_id
                  ),
                  '[]'::jsonb
                )
                FROM event_participants ep
                WHERE ep.event_id = ev.id
              ) AS participants
            FROM events ev
            WHERE ev.status NOT IN ('superseded', 'revoked')
              AND EXISTS (
                SELECT 1
                FROM event_participants focus_ep
                WHERE focus_ep.event_id = ev.id
                  AND focus_ep.entity_id = %s
              )
            ORDER BY ev.observed_at DESC, ev.announced_at DESC NULLS LAST, ev.id
            LIMIT %s
            """,
            (entity_id, limit),
        ).fetchall()
        return _jsonable(rows)

    def corporate_structure_relationships_for_entity(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        entity_id: UUID,
        *,
        as_of: datetime | None,
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT
              r.id, r.subject_entity_id AS subject_id, r.object_entity_id AS object_id,
              r.relationship_type, r.relationship_family, r.status, r.confidence,
              r.valid_from, r.valid_to, r.observed_at, r.qualifiers,
              subject.canonical_name AS subject_name, subject.entity_type AS subject_type,
              object.canonical_name AS object_name, object.entity_type AS object_type,
              (
                SELECT count(*)::int
                FROM relationship_evidence re
                WHERE re.relationship_id = r.id
              ) AS evidence_count,
              frn.fixture_notice, COALESCE(frn.synthetic, false) AS synthetic
            FROM relationships r
            JOIN entities subject ON subject.id = r.subject_entity_id
            JOIN entities object ON object.id = r.object_entity_id
            LEFT JOIN fixture_relationship_notices frn ON frn.relationship_id = r.id
            WHERE r.status NOT IN ('superseded', 'revoked')
              AND r.relationship_family = 'corporate_structure'
              AND (r.subject_entity_id = %(entity_id)s OR r.object_entity_id = %(entity_id)s)
              AND (
                %(as_of)s::timestamptz IS NULL
                OR (
                  (r.valid_from IS NULL OR r.valid_from <= %(as_of)s::timestamptz)
                  AND (r.valid_to IS NULL OR r.valid_to >= %(as_of)s::timestamptz)
                )
              )
            ORDER BY r.confidence DESC NULLS LAST, r.observed_at DESC, r.id
            LIMIT 80
            """,
            {"entity_id": entity_id, "as_of": as_of},
        ).fetchall()
        return _jsonable(rows)

    def adjacent_facility_relationships_for_entity(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        entity_id: UUID,
        *,
        as_of: datetime | None,
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            WITH first_hop AS (
              SELECT DISTINCT
                CASE
                  WHEN r.subject_entity_id = %(entity_id)s THEN r.object_entity_id
                  ELSE r.subject_entity_id
                END AS entity_id
              FROM relationships r
              WHERE r.status NOT IN ('superseded', 'revoked')
                AND (r.subject_entity_id = %(entity_id)s OR r.object_entity_id = %(entity_id)s)
            )
            SELECT
              r.id, r.subject_entity_id AS subject_id, r.object_entity_id AS object_id,
              r.relationship_type, r.relationship_family, r.status, r.confidence,
              r.valid_from, r.valid_to, r.observed_at, r.qualifiers,
              subject.canonical_name AS subject_name, subject.entity_type AS subject_type,
              object.canonical_name AS object_name, object.entity_type AS object_type,
              (
                SELECT count(*)::int
                FROM relationship_evidence re
                WHERE re.relationship_id = r.id
              ) AS evidence_count,
              frn.fixture_notice, COALESCE(frn.synthetic, false) AS synthetic
            FROM relationships r
            JOIN entities subject ON subject.id = r.subject_entity_id
            JOIN entities object ON object.id = r.object_entity_id
            LEFT JOIN fixture_relationship_notices frn ON frn.relationship_id = r.id
            WHERE r.status NOT IN ('superseded', 'revoked')
              AND r.relationship_family = 'corporate_structure'
              AND r.relationship_type IN ('operates_facility', 'owns_facility')
              AND (subject.entity_type = 'facility' OR object.entity_type = 'facility')
              AND NOT (
                r.subject_entity_id = %(entity_id)s
                OR r.object_entity_id = %(entity_id)s
              )
              AND (
                r.subject_entity_id IN (SELECT entity_id FROM first_hop)
                OR r.object_entity_id IN (SELECT entity_id FROM first_hop)
              )
              AND (
                %(as_of)s::timestamptz IS NULL
                OR (
                  (r.valid_from IS NULL OR r.valid_from <= %(as_of)s::timestamptz)
                  AND (r.valid_to IS NULL OR r.valid_to >= %(as_of)s::timestamptz)
                )
              )
            ORDER BY r.confidence DESC NULLS LAST, r.observed_at DESC, r.id
            LIMIT 24
            """,
            {"entity_id": entity_id, "as_of": as_of},
        ).fetchall()
        return _jsonable(rows)

    @staticmethod
    def relationship_family_counts(relationships: list[dict[str, Any]]) -> dict[str, int]:
        counts = {family: 0 for family in sorted(RELATIONSHIP_FAMILIES)}
        for relationship in relationships:
            family = relationship["relationship_family"]
            counts[family] = counts.get(family, 0) + 1
        return {family: count for family, count in counts.items() if count > 0}

    @staticmethod
    def entity_dossier_layers(
        *,
        relationships: list[dict[str, Any]],
        industries: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        layers: dict[str, dict[str, Any]] = {}
        for layer_key, definition in DOSSIER_LAYER_DEFINITIONS.items():
            families = definition["families"]
            layer_relationships = [
                relationship
                for relationship in relationships
                if relationship["relationship_family"] in families
            ][:12]
            has_context = bool(layer_relationships or (layer_key == "business" and industries))
            layer: dict[str, Any] = {
                "label": definition["label"],
                "relationship_families": sorted(families),
                "relationship_count": len(layer_relationships),
                "relationships": layer_relationships,
                "data_status": "covered" if has_context else "missing",
                "data_gap": None if has_context else definition["gap"],
            }
            if layer_key == "business":
                layer["industries"] = industries
                layer["industry_count"] = len(industries)
            layers[layer_key] = layer
        return layers

    @staticmethod
    def entity_dossier_freshness(
        *,
        entity: dict[str, Any],
        relationships: list[dict[str, Any]],
        events: list[dict[str, Any]],
    ) -> dict[str, Any]:
        relationship_observed = [
            relationship["observed_at"]
            for relationship in relationships
            if relationship.get("observed_at")
        ]
        event_observed = [event["observed_at"] for event in events if event.get("observed_at")]
        observed_values = relationship_observed + event_observed
        synthetic = bool(entity.get("synthetic")) or any(
            relationship.get("synthetic") for relationship in relationships
        )
        return {
            "as_of": _now(),
            "data_mode": "synthetic_fixture" if synthetic else "database",
            "latest_observed_at": max(observed_values) if observed_values else None,
            "oldest_observed_at": min(observed_values) if observed_values else None,
            "relationship_observation_count": len(relationship_observed),
            "event_observation_count": len(event_observed),
            "fixture_disclosure": (
                "Synthetic fixture records are explicitly marked and are not live facts."
                if synthetic
                else None
            ),
        }

    @staticmethod
    def entity_dossier_coverage(
        *,
        relationships: list[dict[str, Any]],
        industries: list[dict[str, Any]],
        events: list[dict[str, Any]],
        layers: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        data_available = {
            layer_key: layer["data_status"] == "covered"
            for layer_key, layer in layers.items()
        }
        return {
            "entity_focus_page_openable": True,
            "required_human_summary_dimensions": [
                "business",
                "group",
                "dependencies",
                "capital",
                "policy",
                "signals",
                "data_gaps",
            ],
            "human_summary_dimensions_present": {
                "business": True,
                "group": True,
                "dependencies": True,
                "capital": True,
                "policy": True,
                "signals": True,
                "data_gaps": True,
            },
            "data_available_dimensions": data_available,
            "relationship_count": len(relationships),
            "relationship_family_count": len({row["relationship_family"] for row in relationships}),
            "industry_membership_count": len(industries),
            "recent_event_count": len(events),
        }

    @staticmethod
    def entity_human_summary(
        *,
        entity: dict[str, Any],
        industries: list[dict[str, Any]],
        events: list[dict[str, Any]],
        layers: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        entity_name = entity["canonical_name"]
        industry_names = [
            f"{industry['name_en']} ({industry['role']})" for industry in industries[:4]
        ]
        data_gaps = []
        for layer_key in ("group", "dependencies", "capital", "policy", "signals"):
            layer = layers[layer_key]
            if layer["data_status"] == "missing":
                data_gaps.append(
                    {
                        "dimension": layer_key,
                        "message": f"{layer['data_gap']} Treat this as unknown, not zero.",
                    }
                )
        if not industries:
            data_gaps.append(
                {
                    "dimension": "business",
                    "message": (
                        "No industry membership is loaded; treat business context "
                        "as unknown."
                    ),
                }
            )
        if not events:
            data_gaps.append(
                {
                    "dimension": "events",
                    "message": "No direct event records are loaded for this entity.",
                }
            )

        return {
            "headline": (
                f"{entity_name} has an entity dossier with "
                f"{sum(layer['relationship_count'] for layer in layers.values())} "
                "dimension-linked relationship references."
            ),
            "business": DomainRepository.layer_sentence(
                entity_name,
                layers["business"],
                prefix=(
                    "Industry memberships: "
                    + (", ".join(industry_names) if industry_names else "not loaded")
                    + "."
                ),
            ),
            "group": DomainRepository.layer_sentence(entity_name, layers["group"]),
            "dependencies": DomainRepository.layer_sentence(entity_name, layers["dependencies"]),
            "capital": DomainRepository.layer_sentence(entity_name, layers["capital"]),
            "policy": DomainRepository.layer_sentence(entity_name, layers["policy"]),
            "signals": DomainRepository.layer_sentence(entity_name, layers["signals"]),
            "recent_events": (
                f"{len(events)} direct event record(s) are loaded."
                if events
                else "No direct event records are loaded."
            ),
            "data_gaps": data_gaps,
            "fixture_disclosure": entity.get("fixture_notice"),
        }

    @staticmethod
    def layer_sentence(
        entity_name: str,
        layer: dict[str, Any],
        *,
        prefix: str | None = None,
    ) -> str:
        if layer["relationship_count"] == 0:
            body = f"{layer['data_gap']} Treat this as unknown, not zero."
        else:
            previews = []
            for relationship in layer["relationships"][:3]:
                previews.append(
                    f"{relationship['subject_name']} -> {relationship['object_name']} "
                    f"({relationship['relationship_type']})"
                )
            body = (
                f"{entity_name} has {layer['relationship_count']} "
                f"{layer['label'].lower()} relationship record(s): "
                + "; ".join(previews)
                + "."
            )
        if prefix:
            return f"{prefix} {body}"
        return body

    @staticmethod
    def entity_empire_structure(
        *,
        focus: dict[str, Any],
        direct_relationships: list[dict[str, Any]],
        adjacent_facilities: list[dict[str, Any]],
    ) -> dict[str, dict[str, Any]]:
        sections = {
            key: {
                "label": definition["label"],
                "items": [],
                "data_status": "missing",
                "data_gap": definition["gap"],
            }
            for key, definition in EMPIRE_STRUCTURE_SECTIONS.items()
        }
        sections["legal_group"]["items"].append(
            {
                "entity": {
                    "id": focus["id"],
                    "canonical_name": focus["canonical_name"],
                    "entity_type": focus["entity_type"],
                },
                "relationship": {
                    "relationship_type": "focus_entity",
                    "relationship_family": "corporate_structure",
                    "status": "reported",
                },
                "relationship_scope": "focus",
                "relationship_direction": "current_subject",
                "control_semantics": "Current legal entity only; no parent or subsidiary claim.",
                "fixture_notice": focus.get("fixture_notice"),
            }
        )
        for relationship in direct_relationships:
            category = DomainRepository.structure_category(relationship)
            if category not in sections:
                continue
            sections[category]["items"].append(
                DomainRepository.structure_item(
                    focus_id=str(focus["id"]),
                    relationship=relationship,
                    relationship_scope="direct_to_focus",
                )
            )
        for relationship in adjacent_facilities:
            sections["facilities"]["items"].append(
                DomainRepository.structure_item(
                    focus_id=str(focus["id"]),
                    relationship=relationship,
                    relationship_scope="adjacent_ecosystem",
                )
            )
        for section in sections.values():
            section["item_count"] = len(section["items"])
            if section["items"]:
                section["data_status"] = "covered"
                section["data_gap"] = None
        return sections

    @staticmethod
    def structure_category(relationship: dict[str, Any]) -> str:
        relationship_type = relationship["relationship_type"]
        related_types = {relationship["subject_type"], relationship["object_type"]}
        if relationship_type in {"segment_of"} or "business_segment" in related_types:
            return "business_segments"
        if relationship_type in {"brand_of"} or "brand" in related_types:
            return "brands"
        if relationship_type in {"product_of"} or "product" in related_types:
            return "products"
        if (
            relationship_type in {"operates_facility", "owns_facility"}
            or "facility" in related_types
        ):
            return "facilities"
        return "legal_group"

    @staticmethod
    def structure_item(
        *,
        focus_id: str,
        relationship: dict[str, Any],
        relationship_scope: str,
    ) -> dict[str, Any]:
        related = DomainRepository.related_structure_entity(focus_id, relationship)
        return {
            "entity": related,
            "relationship": {
                "id": relationship["id"],
                "relationship_type": relationship["relationship_type"],
                "relationship_family": relationship["relationship_family"],
                "status": relationship["status"],
                "confidence": relationship["confidence"],
                "observed_at": relationship["observed_at"],
                "evidence_count": relationship["evidence_count"],
                "qualifiers": relationship["qualifiers"],
            },
            "relationship_scope": relationship_scope,
            "relationship_direction": DomainRepository.structure_direction(
                focus_id,
                relationship,
            ),
            "control_semantics": DomainRepository.structure_control_semantics(
                relationship,
                relationship_scope,
            ),
            "fixture_notice": relationship["fixture_notice"],
            "synthetic": relationship["synthetic"],
        }

    @staticmethod
    def related_structure_entity(focus_id: str, relationship: dict[str, Any]) -> dict[str, Any]:
        subject = {
            "id": relationship["subject_id"],
            "canonical_name": relationship["subject_name"],
            "entity_type": relationship["subject_type"],
        }
        object_entity = {
            "id": relationship["object_id"],
            "canonical_name": relationship["object_name"],
            "entity_type": relationship["object_type"],
        }
        if relationship["subject_id"] == focus_id:
            return object_entity
        if relationship["object_id"] == focus_id:
            return subject
        if subject["entity_type"] == "facility":
            return subject
        if object_entity["entity_type"] == "facility":
            return object_entity
        return object_entity

    @staticmethod
    def structure_direction(focus_id: str, relationship: dict[str, Any]) -> str:
        if relationship["subject_id"] == focus_id:
            return "outbound_from_focus"
        if relationship["object_id"] == focus_id:
            return "inbound_to_focus"
        return "adjacent_to_focus_ecosystem"

    @staticmethod
    def structure_control_semantics(
        relationship: dict[str, Any],
        relationship_scope: str,
    ) -> str:
        relationship_type = relationship["relationship_type"]
        if relationship_scope == "adjacent_ecosystem":
            return "Adjacent ecosystem facility exposure; no focus ownership or operation claim."
        if relationship_type == "legal_parent":
            return "Legal parent or legal-group relationship; verify current control separately."
        if relationship_type in {"segment_of", "brand_of", "product_of"}:
            return "Business mapping; not a legal-control assertion."
        if relationship_type in {"operates_facility", "owns_facility"}:
            return "Facility operation or ownership only for the stated subject entity."
        return "Commercial empire context; not a legal-control assertion."

    def cross_industry_links(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        *,
        member_ids: list[UUID],
        selected_industry_ids: list[UUID],
    ) -> list[dict[str, Any]]:
        if not member_ids:
            return []
        rows = connection.execute(
            """
            SELECT
              r.id, r.relationship_type, r.relationship_family, r.confidence,
              r.status, r.observed_at,
              subject.id AS subject_id, subject.canonical_name AS subject_name,
              object.id AS object_id, object.canonical_name AS object_name,
              frn.fixture_notice, COALESCE(frn.synthetic, false) AS synthetic,
              true AS navigation_allowed,
              'cross_industry' AS indicator
            FROM relationships r
            JOIN entities subject ON subject.id = r.subject_entity_id
            JOIN entities object ON object.id = r.object_entity_id
            LEFT JOIN fixture_relationship_notices frn ON frn.relationship_id = r.id
            WHERE r.status NOT IN ('superseded', 'revoked')
              AND (
                r.subject_entity_id = ANY(%s)
                OR r.object_entity_id = ANY(%s)
              )
              AND (
                NOT (r.subject_entity_id = ANY(%s) AND r.object_entity_id = ANY(%s))
                OR EXISTS (
                  SELECT 1
                  FROM entity_industry_memberships eim
                  WHERE eim.entity_id IN (r.subject_entity_id, r.object_entity_id)
                    AND NOT (eim.industry_id = ANY(%s))
                )
              )
            ORDER BY r.confidence DESC NULLS LAST, r.observed_at DESC, r.id
            LIMIT 12
            """,
            (member_ids, member_ids, member_ids, member_ids, selected_industry_ids),
        ).fetchall()
        return _jsonable(rows)

    def _with_primary_identifiers(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        entity_rows: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if not entity_rows:
            return []
        entity_ids = [row["id"] for row in entity_rows]
        identifier_rows = connection.execute(
            """
            SELECT entity_id, scheme, value
            FROM entity_identifiers
            WHERE entity_id = ANY(%s)
            ORDER BY scheme
            """,
            (entity_ids,),
        ).fetchall()
        identifiers: dict[UUID, dict[str, str]] = {}
        for row in identifier_rows:
            identifiers.setdefault(row["entity_id"], {})[row["scheme"]] = row["value"]
        return [
            _jsonable(
                {
                    **dict(row),
                    "primary_identifiers": identifiers.get(row["id"], {}),
                }
            )
            for row in entity_rows
        ]

    def active_scoring_profile(
        self,
        connection: psycopg.Connection[dict[str, Any]],
    ) -> dict[str, Any] | None:
        row = connection.execute(
            """
            SELECT
              spv.id,
              sp.profile_key,
              sp.name,
              spv.version,
              sm.model_key,
              sm.formula,
              spv.weights,
              spv.thresholds,
              spv.half_lives,
              spv.missing_value_policy,
              spv.reason,
              spv.active
            FROM scoring_profile_versions spv
            JOIN scoring_profiles sp ON sp.id = spv.profile_id
            JOIN scoring_models sm ON sm.id = spv.model_id
            WHERE spv.active = true
            ORDER BY sp.is_system_default DESC, spv.created_at DESC
            LIMIT 1
            """
        ).fetchone()
        if row is None:
            return None
        return self.scoring_profile_payload(row)

    def scoring_profile_by_id(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        profile_id: UUID,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT
              spv.id,
              sp.profile_key,
              sp.name,
              spv.version,
              sm.model_key,
              sm.formula,
              spv.weights,
              spv.thresholds,
              spv.half_lives,
              spv.missing_value_policy,
              spv.reason,
              spv.active
            FROM scoring_profile_versions spv
            JOIN scoring_profiles sp ON sp.id = spv.profile_id
            JOIN scoring_models sm ON sm.id = spv.model_id
            WHERE spv.id = %s
            """,
            (profile_id,),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"Scoring profile version not found: {profile_id}")
        return self.scoring_profile_payload(row)

    @staticmethod
    def scoring_profile_payload(row: dict[str, Any]) -> dict[str, Any]:
        formula = row.get("formula") or {}
        return _jsonable(
            {
                "id": row["id"],
                "profile_key": row["profile_key"],
                "name": row["name"],
                "version": row["version"],
                "model_key": row["model_key"],
                "weights": row["weights"],
                "quality_factor": formula.get("quality_adjustment", {}),
                "half_lives_days": row["half_lives"],
                "thresholds": row["thresholds"],
                "missing_value_policy": row["missing_value_policy"],
                "reason": row["reason"],
                "active": row["active"],
            }
        )

    def active_analysis_context_payload(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        *,
        client_refresh_token: str | None = None,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT
              aac.context_key,
              aac.active_scoring_profile_version_id,
              aac.active_data_snapshot_id,
              ds.snapshot_key AS active_data_snapshot_key,
              aac.active_scoring_run_id,
              aac.refresh_token,
              aac.refresh_generation,
              aac.status,
              aac.activated_at,
              aac.activated_by,
              aac.affected_modules,
              aac.metadata,
              sp.profile_key,
              spv.version AS profile_version_number,
              sm.model_key,
              sm.version AS model_version_number
            FROM active_analysis_contexts aac
            JOIN scoring_profile_versions spv
              ON spv.id = aac.active_scoring_profile_version_id
            JOIN scoring_profiles sp ON sp.id = spv.profile_id
            JOIN scoring_models sm ON sm.id = spv.model_id
            LEFT JOIN data_snapshots ds ON ds.id = aac.active_data_snapshot_id
            WHERE aac.context_key = 'global'
            """
        ).fetchone()
        if row is None:
            raise RepositoryError("No active analysis context is available")

        refresh_token = str(row["refresh_token"])
        client_state = "current"
        if client_refresh_token is not None and client_refresh_token != refresh_token:
            client_state = "stale"
        return _jsonable(
            {
                "schema_version": "active-analysis-context-v1",
                "context_key": row["context_key"],
                "active_scoring_profile_version_id": row[
                    "active_scoring_profile_version_id"
                ],
                "active_data_snapshot_id": row["active_data_snapshot_id"],
                "active_data_snapshot_key": row["active_data_snapshot_key"],
                "active_scoring_run_id": row["active_scoring_run_id"],
                "refresh_token": row["refresh_token"],
                "refresh_generation": row["refresh_generation"],
                "status": row["status"],
                "activated_at": row["activated_at"],
                "activated_by": row["activated_by"],
                "affected_modules": row["affected_modules"],
                "model_version": f"{row['model_key']}@{row['model_version_number']}",
                "profile_version": (
                    f"{row['profile_key']}@{row['profile_version_number']}"
                ),
                "client_state": client_state,
                "stale_client_semantics": (
                    "Clients with a different refresh_token must discard cached "
                    "graph, score, model and module state and refetch the active context."
                ),
                "metadata": row["metadata"],
            }
        )

    def get_active_analysis_context(
        self,
        *,
        client_refresh_token: str | None = None,
    ) -> dict[str, Any]:
        with self.connect() as connection:
            return self.active_analysis_context_payload(
                connection,
                client_refresh_token=client_refresh_token,
            )

    def _active_scoring_profile_for_update(
        self,
        connection: psycopg.Connection[dict[str, Any]],
    ) -> dict[str, Any] | None:
        row = connection.execute(
            """
            SELECT
              spv.id,
              sp.profile_key,
              sp.name,
              spv.version,
              sm.model_key,
              sm.formula,
              spv.weights,
              spv.thresholds,
              spv.half_lives,
              spv.missing_value_policy,
              spv.reason,
              spv.active
            FROM scoring_profile_versions spv
            JOIN scoring_profiles sp ON sp.id = spv.profile_id
            JOIN scoring_models sm ON sm.id = spv.model_id
            WHERE spv.active = true
            ORDER BY sp.is_system_default DESC, spv.created_at DESC
            LIMIT 1
            FOR UPDATE OF spv
            """
        ).fetchone()
        if row is None:
            return None
        return self.scoring_profile_payload(row)

    def _scoring_profile_activation_target(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        profile_version_id: UUID,
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT
              spv.id,
              spv.profile_id,
              spv.model_id,
              sp.profile_key,
              sp.name,
              spv.version,
              sm.model_key,
              sm.version AS model_version_number,
              sm.formula,
              spv.weights,
              spv.thresholds,
              spv.half_lives,
              spv.missing_value_policy,
              spv.reason,
              spv.active
            FROM scoring_profile_versions spv
            JOIN scoring_profiles sp ON sp.id = spv.profile_id
            JOIN scoring_models sm ON sm.id = spv.model_id
            WHERE spv.id = %s
            FOR UPDATE OF spv
            """,
            (profile_version_id,),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"Scoring profile version not found: {profile_version_id}")
        return dict(row)

    def activate_scoring_profile_version(
        self,
        *,
        profile_version_id: UUID,
        expected_active_profile_version_id: UUID | None,
        client_refresh_token: str | None,
        reason: str,
        actor: str = "local_user",
        action_type: str = "activate_scoring_profile",
    ) -> dict[str, Any]:
        conflict_detail: dict[str, Any] | None = None
        activation_payload: dict[str, Any] | None = None
        with self.connect() as connection:
            previous_profile = self._active_scoring_profile_for_update(connection)
            target_row = self._scoring_profile_activation_target(connection, profile_version_id)
            target_profile_before = self.scoring_profile_payload(target_row)
            previous_profile_id = (
                UUID(previous_profile["id"]) if previous_profile is not None else None
            )
            if (
                expected_active_profile_version_id is not None
                and previous_profile_id != expected_active_profile_version_id
            ):
                conflict_detail = {
                    "schema_version": "model-activation-conflict-v1",
                    "status": "conflict",
                    "reason": "stale_active_profile_version",
                    "expected_active_profile_version_id": expected_active_profile_version_id,
                    "actual_active_profile_version_id": previous_profile_id,
                    "target_profile_version_id": profile_version_id,
                    "client_refresh_token": client_refresh_token,
                }
                self.log_operation(
                    connection,
                    actor=actor,
                    action_type=action_type,
                    object_type="scoring_profile_version",
                    object_id=profile_version_id,
                    old_value=previous_profile,
                    new_value=target_profile_before,
                    diff=conflict_detail,
                    reason=reason,
                    result_status="conflict",
                    model_version=target_row["model_key"],
                    profile_version=(
                        f"{target_row['profile_key']}@{target_row['version']}"
                    ),
                )
            else:
                context_row = connection.execute(
                    """
                    SELECT refresh_token, refresh_generation
                    FROM active_analysis_contexts
                    WHERE context_key = 'global'
                    FOR UPDATE
                    """
                ).fetchone()
                previous_refresh_token = (
                    str(context_row["refresh_token"]) if context_row is not None else None
                )
                previous_generation = (
                    int(context_row["refresh_generation"]) if context_row is not None else 0
                )
                next_generation = previous_generation + 1
                active_snapshot = connection.execute(
                    """
                    SELECT id, as_of
                    FROM data_snapshots
                    WHERE status = 'active'
                    ORDER BY activated_at DESC, created_at DESC
                    LIMIT 1
                    """
                ).fetchone()
                data_snapshot_id = active_snapshot["id"] if active_snapshot else None
                data_snapshot_at = active_snapshot["as_of"] if active_snapshot else _now()
                scoring_run = connection.execute(
                    """
                    INSERT INTO scoring_runs(
                      model_id, profile_version_id, data_snapshot_at, parameters,
                      status, started_at, finished_at, content_hash
                    )
                    VALUES (%s, %s, %s, %s, 'completed', now(), now(), %s)
                    RETURNING id
                    """,
                    (
                        target_row["model_id"],
                        profile_version_id,
                        data_snapshot_at,
                        Jsonb(
                            {
                                "activation_reason": reason,
                                "activation_action_type": action_type,
                                "refresh_generation": next_generation,
                                "refresh_policy": "atomic-global-switch",
                            }
                        ),
                        f"model-activation:{profile_version_id}:{next_generation}",
                    ),
                ).fetchone()
                connection.execute("UPDATE scoring_profile_versions SET active = false")
                connection.execute(
                    "UPDATE scoring_profile_versions SET active = true WHERE id = %s",
                    (profile_version_id,),
                )
                context = connection.execute(
                    """
                    INSERT INTO active_analysis_contexts(
                      context_key, active_scoring_profile_version_id,
                      active_data_snapshot_id, active_scoring_run_id,
                      refresh_generation, status, activated_at, activated_by,
                      affected_modules, metadata, updated_at
                    )
                    VALUES (
                      'global', %s, %s, %s, %s, 'active', now(), %s, %s, %s, now()
                    )
                    ON CONFLICT (context_key) DO UPDATE SET
                      active_scoring_profile_version_id =
                        EXCLUDED.active_scoring_profile_version_id,
                      active_data_snapshot_id = EXCLUDED.active_data_snapshot_id,
                      active_scoring_run_id = EXCLUDED.active_scoring_run_id,
                      refresh_token = gen_random_uuid(),
                      refresh_generation = EXCLUDED.refresh_generation,
                      status = 'active',
                      activated_at = EXCLUDED.activated_at,
                      activated_by = EXCLUDED.activated_by,
                      affected_modules = EXCLUDED.affected_modules,
                      metadata = EXCLUDED.metadata,
                      updated_at = now()
                    RETURNING refresh_token
                    """,
                    (
                        profile_version_id,
                        data_snapshot_id,
                        scoring_run["id"],
                        next_generation,
                        actor,
                        Jsonb(ACTIVE_REFRESH_MODULES),
                        Jsonb(
                            {
                                "activation_reason": reason,
                                "previous_scoring_profile_version_id": (
                                    str(previous_profile_id)
                                    if previous_profile_id is not None
                                    else None
                                ),
                                "cache_policy": (
                                    "clients compare refresh_token and refresh_generation"
                                ),
                            }
                        ),
                    ),
                ).fetchone()
                target_profile_after = self.scoring_profile_by_id(
                    connection,
                    profile_version_id,
                )
                active_context = self.active_analysis_context_payload(
                    connection,
                    client_refresh_token=client_refresh_token,
                )
                diff = {
                    "previous_active_profile_version_id": previous_profile_id,
                    "new_active_profile_version_id": profile_version_id,
                    "previous_refresh_token": previous_refresh_token,
                    "refresh_token": str(context["refresh_token"]),
                    "refresh_generation": next_generation,
                    "affected_modules": ACTIVE_REFRESH_MODULES,
                }
                self.log_operation(
                    connection,
                    actor=actor,
                    action_type=action_type,
                    object_type="scoring_profile_version",
                    object_id=profile_version_id,
                    old_value=previous_profile,
                    new_value=target_profile_after,
                    diff=diff,
                    reason=reason,
                    result_status="success",
                    model_version=target_row["model_key"],
                    profile_version=(
                        f"{target_row['profile_key']}@{target_row['version']}"
                    ),
                )
                activation_payload = _jsonable(
                    {
                        "schema_version": "model-activation-v1",
                        "status": "activated",
                        "previous_profile": previous_profile,
                        "activated_profile": target_profile_after,
                        "active_context": active_context,
                        "cache_invalidation": {
                            "previous_refresh_token": previous_refresh_token,
                            "refresh_token": context["refresh_token"],
                            "refresh_generation": next_generation,
                            "stale_client_semantics": (
                                "clients with the previous refresh_token must refetch all "
                                "graph, score, model and module state before presenting "
                                "fresh results"
                            ),
                        },
                    }
                )
        if conflict_detail is not None:
            raise ConflictError(_jsonable(conflict_detail))
        if activation_payload is None:  # pragma: no cover - defensive invariant.
            raise RepositoryError("Scoring profile activation produced no payload")
        return activation_payload

    def rollback_scoring_profile_version(
        self,
        *,
        profile_version_id: UUID,
        expected_active_profile_version_id: UUID | None,
        client_refresh_token: str | None,
        reason: str,
        actor: str = "local_user",
    ) -> dict[str, Any]:
        return self.activate_scoring_profile_version(
            profile_version_id=profile_version_id,
            expected_active_profile_version_id=expected_active_profile_version_id,
            client_refresh_token=client_refresh_token,
            reason=reason,
            actor=actor,
            action_type="rollback_scoring_profile",
        )

    def enqueue_score_recompute(
        self,
        *,
        expected_active_profile_version_id: UUID | None,
        client_refresh_token: str | None,
        scope: str,
        reason: str,
        actor: str = "local_user",
    ) -> dict[str, Any]:
        conflict_detail: dict[str, Any] | None = None
        response_payload: dict[str, Any] | None = None
        with self.connect() as connection:
            context_row = connection.execute(
                """
                SELECT
                  aac.active_scoring_profile_version_id,
                  aac.active_data_snapshot_id,
                  aac.active_scoring_run_id,
                  aac.refresh_token::text AS refresh_token,
                  aac.refresh_generation,
                  aac.status,
                  sp.profile_key,
                  spv.version AS profile_version_number,
                  sm.model_key,
                  sm.version AS model_version_number
                FROM active_analysis_contexts aac
                JOIN scoring_profile_versions spv
                  ON spv.id = aac.active_scoring_profile_version_id
                JOIN scoring_profiles sp ON sp.id = spv.profile_id
                JOIN scoring_models sm ON sm.id = spv.model_id
                WHERE aac.context_key = 'global'
                FOR UPDATE OF aac
                """
            ).fetchone()
            if context_row is None:
                raise RepositoryError("No active analysis context is available")

            active_profile_id = context_row["active_scoring_profile_version_id"]
            active_context = self.active_analysis_context_payload(
                connection,
                client_refresh_token=client_refresh_token,
            )
            active_profile = self.scoring_profile_by_id(connection, active_profile_id)
            actual_refresh_token = str(context_row["refresh_token"])
            conflict_reason: str | None = None
            if (
                expected_active_profile_version_id is not None
                and expected_active_profile_version_id != active_profile_id
            ):
                conflict_reason = "stale_active_profile_version"
            elif client_refresh_token is not None and client_refresh_token != actual_refresh_token:
                conflict_reason = "stale_client_refresh_token"

            if conflict_reason is not None:
                conflict_detail = {
                    "schema_version": "score-recompute-conflict-v1",
                    "status": "conflict",
                    "reason": conflict_reason,
                    "expected_active_profile_version_id": expected_active_profile_version_id,
                    "actual_active_profile_version_id": active_profile_id,
                    "client_refresh_token": client_refresh_token,
                    "actual_refresh_token": actual_refresh_token,
                    "scope": scope,
                    "active_context": active_context,
                }
                self.log_operation(
                    connection,
                    actor=actor,
                    action_type="enqueue_score_recompute",
                    object_type="active_analysis_context",
                    object_id=active_profile_id,
                    old_value=active_context,
                    new_value=None,
                    diff=conflict_detail,
                    reason=reason,
                    result_status="conflict",
                    model_version=active_context["model_version"],
                    profile_version=active_context["profile_version"],
                )
            else:
                data_snapshot_id = context_row["active_data_snapshot_id"]
                scoring_run_id = context_row["active_scoring_run_id"]
                refresh_generation = int(context_row["refresh_generation"])
                idempotency_key = ":".join(
                    [
                        "score-recompute",
                        scope,
                        str(active_profile_id),
                        str(data_snapshot_id or "no-data-snapshot"),
                        str(scoring_run_id or "no-scoring-run"),
                        str(refresh_generation),
                    ]
                )
                job_payload = {
                    "schema_version": "score-recompute-job-v1",
                    "scope": scope,
                    "reason": reason,
                    "active_scoring_profile_version_id": active_profile_id,
                    "active_data_snapshot_id": data_snapshot_id,
                    "active_scoring_run_id": scoring_run_id,
                    "refresh_token": actual_refresh_token,
                    "refresh_generation": refresh_generation,
                    "affected_modules": ACTIVE_REFRESH_MODULES,
                    "model_version": active_context["model_version"],
                    "profile_version": active_context["profile_version"],
                    "requested_by": actor,
                    "requested_at": _now(),
                }
                job_metadata = {
                    "task_ids": ["T1303", "T1304"],
                    "acceptance_ids": ["A204", "A205", "A206"],
                    "contract": "transactional-score-recompute-enqueue-v1",
                    "handler_status": "queued_handler_not_closed",
                }
                job_row = connection.execute(
                    """
                    INSERT INTO background_jobs(
                      job_type, idempotency_key, payload, priority, status,
                      max_attempts, dead_letter_after_attempts, metadata
                    )
                    VALUES (
                      'score_recompute', %s, %s, 40, 'queued', 5, 5, %s
                    )
                    ON CONFLICT (job_type, idempotency_key) DO UPDATE SET
                      idempotency_key = EXCLUDED.idempotency_key
                    RETURNING
                      id, job_type, idempotency_key, payload, priority, status,
                      scheduled_for, attempt_count, max_attempts,
                      dead_letter_after_attempts, created_at, updated_at, metadata
                    """,
                    (
                        idempotency_key,
                        Jsonb(_jsonable(job_payload)),
                        Jsonb(job_metadata),
                    ),
                ).fetchone()
                job_payload_json = _jsonable(dict(job_row))
                self.log_operation(
                    connection,
                    actor=actor,
                    action_type="enqueue_score_recompute",
                    object_type="background_job",
                    object_id=job_row["id"],
                    old_value=active_context,
                    new_value=job_payload_json,
                    diff={
                        "idempotency_key": idempotency_key,
                        "active_scoring_profile_version_id": active_profile_id,
                        "refresh_generation": refresh_generation,
                        "scope": scope,
                    },
                    reason=reason,
                    result_status="success",
                    model_version=active_context["model_version"],
                    profile_version=active_context["profile_version"],
                )
                response_payload = _jsonable(
                    {
                        "schema_version": "score-recompute-request-v1",
                        "status": job_row["status"],
                        "job": job_payload_json,
                        "idempotency_key": idempotency_key,
                        "active_profile": active_profile,
                        "active_context": active_context,
                        "cache_policy": {
                            "refresh_token": actual_refresh_token,
                            "refresh_generation": refresh_generation,
                            "stale_client_semantics": (
                                "clients must include the latest refresh_token before "
                                "requesting a global score recompute"
                            ),
                        },
                    }
                )
        if conflict_detail is not None:
            raise ConflictError(_jsonable(conflict_detail))
        if response_payload is None:  # pragma: no cover - defensive invariant.
            raise RepositoryError("Score recompute enqueue produced no payload")
        return response_payload

    def list_scoring_profiles(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT
                  spv.id,
                  sp.profile_key,
                  sp.name,
                  spv.version,
                  sm.model_key,
                  sm.formula,
                  spv.weights,
                  spv.thresholds,
                  spv.half_lives,
                  spv.missing_value_policy,
                  spv.reason,
                  spv.active
                FROM scoring_profile_versions spv
                JOIN scoring_profiles sp ON sp.id = spv.profile_id
                JOIN scoring_models sm ON sm.id = spv.model_id
                ORDER BY
                  spv.active DESC,
                  sp.is_system_default DESC,
                  sp.profile_key,
                  spv.version DESC
                """
            ).fetchall()
        profiles: list[dict[str, Any]] = []
        for row in rows:
            profiles.append(self.scoring_profile_payload(row))
        return profiles

    def list_watchlists(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            watchlists = connection.execute(
                """
                SELECT id, namespace, name, description, default_scoring_profile_version_id
                FROM watchlists
                ORDER BY updated_at DESC, name
                """
            ).fetchall()
            items = connection.execute(
                """
                SELECT watchlist_id, object_type, object_id, labels, note, saved_state
                FROM watchlist_items
                WHERE removed_at IS NULL
                ORDER BY added_at DESC
                """
            ).fetchall()
            change_counts = connection.execute(
                """
                SELECT wi.watchlist_id, count(c.id)::int AS unread_change_count
                FROM watchlist_items wi
                LEFT JOIN changes c
                  ON c.object_id = wi.object_id AND c.review_required = true
                WHERE wi.removed_at IS NULL
                GROUP BY wi.watchlist_id
                """
            ).fetchall()
        item_map: dict[UUID, list[dict[str, Any]]] = {}
        for item in items:
            item_map.setdefault(item["watchlist_id"], []).append(
                _jsonable(
                    {
                        "object_type": item["object_type"],
                        "object_id": item["object_id"],
                        "labels": item["labels"],
                        "note": item["note"],
                        "saved_state": item["saved_state"],
                    }
                )
            )
        unread_map = {row["watchlist_id"]: row["unread_change_count"] for row in change_counts}
        return [
            _jsonable(
                {
                    "id": row["id"],
                    "namespace": row["namespace"],
                    "name": row["name"],
                    "description": row["description"],
                    "default_scoring_profile_version_id": row[
                        "default_scoring_profile_version_id"
                    ],
                    "items": item_map.get(row["id"], []),
                    "unread_change_count": unread_map.get(row["id"], 0),
                }
            )
            for row in watchlists
        ]

    def create_watchlist(
        self,
        *,
        name: str,
        description: str | None,
        default_scoring_profile_version_id: UUID | None,
    ) -> dict[str, Any]:
        with self.connect() as connection:
            row = connection.execute(
                """
                INSERT INTO watchlists(name, description, default_scoring_profile_version_id)
                VALUES (%s, %s, %s)
                ON CONFLICT (namespace, name) DO UPDATE SET
                  description = EXCLUDED.description,
                  default_scoring_profile_version_id = EXCLUDED.default_scoring_profile_version_id,
                  updated_at = now()
                RETURNING id, namespace, name, description, default_scoring_profile_version_id
                """,
                (name, description, default_scoring_profile_version_id),
            ).fetchone()
            self.log_operation(
                connection,
                actor="local_user",
                action_type="create_watchlist",
                object_type="watchlist",
                object_id=row["id"],
                old_value=None,
                new_value=dict(row),
                reason="API create or restore watchlist",
            )
        return self.get_watchlist(row["id"])

    def get_watchlist(self, watchlist_id: UUID) -> dict[str, Any]:
        watchlist = next(
            (
                watchlist
                for watchlist in self.list_watchlists()
                if watchlist["id"] == str(watchlist_id)
            ),
            None,
        )
        if watchlist is None:
            raise NotFoundError(f"Watchlist not found: {watchlist_id}")
        return watchlist

    def add_watchlist_item(
        self,
        watchlist_id: UUID,
        *,
        object_type: str,
        object_id: UUID,
        labels: list[str],
        note: str | None,
        saved_state: dict[str, Any],
    ) -> dict[str, Any]:
        with self.connect() as connection:
            self.ensure_watchlist_exists(connection, watchlist_id)
            self.ensure_watchlist_object_exists(connection, object_type, object_id)
            old_row = connection.execute(
                """
                SELECT object_type, object_id, labels, note, saved_state, removed_at
                FROM watchlist_items
                WHERE watchlist_id = %s AND object_type = %s AND object_id = %s
                """,
                (watchlist_id, object_type, object_id),
            ).fetchone()
            row = connection.execute(
                """
                INSERT INTO watchlist_items(
                  watchlist_id, object_type, object_id, labels, note, saved_state, removed_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, NULL)
                ON CONFLICT (watchlist_id, object_type, object_id) DO UPDATE SET
                  labels = EXCLUDED.labels,
                  note = EXCLUDED.note,
                  saved_state = EXCLUDED.saved_state,
                  removed_at = NULL,
                  added_at = now()
                RETURNING object_type, object_id, labels, note, saved_state
                """,
                (watchlist_id, object_type, object_id, labels, note, Jsonb(saved_state)),
            ).fetchone()
            connection.execute(
                "UPDATE watchlists SET updated_at = now() WHERE id = %s",
                (watchlist_id,),
            )
            self.log_operation(
                connection,
                actor="local_user",
                action_type="add_watchlist_item",
                object_type="watchlist_item",
                object_id=object_id,
                old_value=old_row,
                new_value=dict(row),
                diff={"watchlist_id": str(watchlist_id), "restored": old_row is not None},
                reason="API add watchlist item",
            )
        return _jsonable(row)

    def ensure_watchlist_object_exists(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        object_type: str,
        object_id: UUID,
    ) -> None:
        if object_type == "industry":
            row = connection.execute(
                "SELECT id FROM industries WHERE id = %s AND active = true",
                (object_id,),
            ).fetchone()
        elif object_type == "entity":
            row = connection.execute(
                "SELECT id FROM entities WHERE id = %s",
                (object_id,),
            ).fetchone()
        elif object_type in {"theme", "facility"}:
            row = connection.execute(
                "SELECT id FROM entities WHERE id = %s AND entity_type = %s",
                (object_id, object_type),
            ).fetchone()
        else:
            raise RepositoryError(f"Unsupported watchlist object type: {object_type}")
        if row is None:
            raise NotFoundError(f"Watchlist object not found: {object_type}:{object_id}")

    def remove_watchlist_item(
        self,
        watchlist_id: UUID,
        *,
        object_type: str,
        object_id: UUID,
    ) -> None:
        with self.connect() as connection:
            old_row = connection.execute(
                """
                SELECT object_type, object_id, labels, note, saved_state, removed_at
                FROM watchlist_items
                WHERE watchlist_id = %s AND object_type = %s AND object_id = %s
                """,
                (watchlist_id, object_type, object_id),
            ).fetchone()
            if old_row is None:
                raise NotFoundError("Watchlist item not found")
            connection.execute(
                """
                UPDATE watchlist_items
                SET removed_at = now()
                WHERE watchlist_id = %s AND object_type = %s AND object_id = %s
                """,
                (watchlist_id, object_type, object_id),
            )
            connection.execute(
                "UPDATE watchlists SET updated_at = now() WHERE id = %s",
                (watchlist_id,),
            )
            self.log_operation(
                connection,
                actor="local_user",
                action_type="remove_watchlist_item",
                object_type="watchlist_item",
                object_id=object_id,
                old_value=old_row,
                new_value={"removed_at": _now().isoformat()},
                diff={"watchlist_id": str(watchlist_id), "removed": True},
                reason="API soft remove watchlist item",
            )

    def ensure_watchlist_exists(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        watchlist_id: UUID,
    ) -> None:
        row = connection.execute(
            "SELECT id FROM watchlists WHERE id = %s",
            (watchlist_id,),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"Watchlist not found: {watchlist_id}")

    def saved_view_payload(
        self,
        row: dict[str, Any],
        *,
        versions: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "id": row["id"],
            "namespace": row["namespace"],
            "workspace_key": row["workspace_key"],
            "name": row["name"],
            "description": row["description"],
            "state": row["state"],
            "schema_version": row["schema_version"],
            "current_version": row["current_version"],
            "active": row["active"],
            "created_by": row["created_by"],
            "updated_by": row["updated_by"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "last_restored_at": row["last_restored_at"],
            "metadata": row["metadata"],
            "version_count": row.get("version_count"),
        }
        if versions is not None:
            payload["versions"] = versions
            payload["version_count"] = len(versions)
        return _jsonable(payload)

    def saved_view_version_payload(self, row: dict[str, Any]) -> dict[str, Any]:
        return _jsonable(
            {
                "id": row["id"],
                "saved_view_id": row["saved_view_id"],
                "version_no": row["version_no"],
                "state": row["state"],
                "schema_version": row["schema_version"],
                "action_type": row["action_type"],
                "restored_from_version_no": row["restored_from_version_no"],
                "change_note": row["change_note"],
                "created_by": row["created_by"],
                "created_at": row["created_at"],
                "metadata": row["metadata"],
            }
        )

    def list_saved_views(
        self,
        *,
        namespace: str = "local_user",
        workspace_key: str = "default",
        include_inactive: bool = False,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT sv.*,
                       (
                         SELECT count(*)::int
                         FROM saved_view_versions svv
                         WHERE svv.saved_view_id = sv.id
                       ) AS version_count
                FROM saved_views sv
                WHERE sv.namespace = %s
                  AND sv.workspace_key = %s
                  AND (%s = true OR sv.active = true)
                ORDER BY sv.updated_at DESC, sv.name
                """,
                (namespace, workspace_key, include_inactive),
            ).fetchall()
        return [self.saved_view_payload(row) for row in rows]

    def get_saved_view(self, saved_view_id: UUID) -> dict[str, Any]:
        with self.connect() as connection:
            row = self._saved_view_row(connection, saved_view_id, for_update=False)
            versions = self._saved_view_versions(connection, saved_view_id)
        return self.saved_view_payload(row, versions=versions)

    def create_saved_view(
        self,
        *,
        name: str,
        state: dict[str, Any],
        description: str | None = None,
        workspace_key: str = "default",
        schema_version: str = SAVED_VIEW_SCHEMA_VERSION,
        change_note: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "local_user",
    ) -> dict[str, Any]:
        conflict_detail: dict[str, Any] | None = None
        saved_view_id: UUID | None = None
        with self.connect() as connection:
            existing = connection.execute(
                """
                SELECT id, current_version
                FROM saved_views
                WHERE namespace = %s AND workspace_key = %s AND name = %s
                """,
                (actor, workspace_key, name),
            ).fetchone()
            if existing is not None:
                conflict_detail = {
                    "schema_version": "saved-view-conflict-v1",
                    "status": "conflict",
                    "reason": "saved_view_name_exists",
                    "saved_view_id": existing["id"],
                    "actual_version": existing["current_version"],
                    "workspace_key": workspace_key,
                    "name": name,
                }
                conflict_detail = _jsonable(conflict_detail)
                self.log_operation(
                    connection,
                    actor=actor,
                    action_type="create_saved_view",
                    object_type="saved_view",
                    object_id=existing["id"],
                    old_value=dict(existing),
                    new_value=None,
                    diff=conflict_detail,
                    reason="Saved view create rejected because name already exists",
                    result_status="conflict",
                )
            else:
                row = connection.execute(
                    """
                    INSERT INTO saved_views(
                      namespace, workspace_key, name, description, state, schema_version,
                      current_version, created_by, updated_by, metadata
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, 1, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        actor,
                        workspace_key,
                        name,
                        description,
                        Jsonb(state),
                        schema_version,
                        actor,
                        actor,
                        Jsonb(metadata or {}),
                    ),
                ).fetchone()
                saved_view_id = row["id"]
                version_row = connection.execute(
                    """
                    INSERT INTO saved_view_versions(
                      saved_view_id, version_no, state, schema_version, action_type,
                      change_note, created_by, metadata
                    )
                    VALUES (%s, 1, %s, %s, 'create', %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        saved_view_id,
                        Jsonb(state),
                        schema_version,
                        change_note,
                        actor,
                        Jsonb(metadata or {}),
                    ),
                ).fetchone()
                self.log_operation(
                    connection,
                    actor=actor,
                    action_type="create_saved_view",
                    object_type="saved_view",
                    object_id=saved_view_id,
                    old_value=None,
                    new_value=self.saved_view_payload(row, versions=[version_row]),
                    diff={"version_no": 1, "schema_version": schema_version},
                    reason=change_note or "API create saved view",
                )
        if conflict_detail is not None:
            raise ConflictError(conflict_detail)
        if saved_view_id is None:
            raise RepositoryError("Saved view create did not return an id")
        return self.get_saved_view(saved_view_id)

    def update_saved_view(
        self,
        saved_view_id: UUID,
        *,
        expected_version: int,
        state: dict[str, Any],
        name: str | None = None,
        description: str | None = None,
        schema_version: str = SAVED_VIEW_SCHEMA_VERSION,
        change_note: str | None = None,
        metadata: dict[str, Any] | None = None,
        actor: str = "local_user",
    ) -> dict[str, Any]:
        conflict_detail: dict[str, Any] | None = None
        with self.connect() as connection:
            current = self._saved_view_row(connection, saved_view_id, for_update=True)
            actual_version = int(current["current_version"])
            if actual_version != expected_version:
                conflict_detail = self._saved_view_conflict_detail(
                    saved_view_id=saved_view_id,
                    reason="stale_saved_view_version",
                    expected_version=expected_version,
                    actual_version=actual_version,
                )
                self.log_operation(
                    connection,
                    actor=actor,
                    action_type="update_saved_view",
                    object_type="saved_view",
                    object_id=saved_view_id,
                    old_value=dict(current),
                    new_value={"state": state, "schema_version": schema_version},
                    diff=conflict_detail,
                    reason=change_note or "Saved view update rejected by optimistic lock",
                    result_status="conflict",
                )
            else:
                next_version = actual_version + 1
                row = connection.execute(
                    """
                    UPDATE saved_views
                    SET name = COALESCE(%s, name),
                        description = COALESCE(%s, description),
                        state = %s,
                        schema_version = %s,
                        current_version = %s,
                        updated_by = %s,
                        updated_at = now(),
                        metadata = %s
                    WHERE id = %s
                    RETURNING *
                    """,
                    (
                        name,
                        description,
                        Jsonb(state),
                        schema_version,
                        next_version,
                        actor,
                        Jsonb(metadata or current["metadata"] or {}),
                        saved_view_id,
                    ),
                ).fetchone()
                version_row = connection.execute(
                    """
                    INSERT INTO saved_view_versions(
                      saved_view_id, version_no, state, schema_version, action_type,
                      change_note, created_by, metadata
                    )
                    VALUES (%s, %s, %s, %s, 'update', %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        saved_view_id,
                        next_version,
                        Jsonb(state),
                        schema_version,
                        change_note,
                        actor,
                        Jsonb(metadata or {}),
                    ),
                ).fetchone()
                self.log_operation(
                    connection,
                    actor=actor,
                    action_type="update_saved_view",
                    object_type="saved_view",
                    object_id=saved_view_id,
                    old_value=dict(current),
                    new_value=self.saved_view_payload(row, versions=[version_row]),
                    diff={"expected_version": expected_version, "next_version": next_version},
                    reason=change_note or "API update saved view",
                )
        if conflict_detail is not None:
            raise ConflictError(conflict_detail)
        return self.get_saved_view(saved_view_id)

    def restore_saved_view(
        self,
        saved_view_id: UUID,
        *,
        target_version: int,
        expected_version: int,
        change_note: str | None = None,
        actor: str = "local_user",
    ) -> dict[str, Any]:
        conflict_detail: dict[str, Any] | None = None
        with self.connect() as connection:
            current = self._saved_view_row(connection, saved_view_id, for_update=True)
            target = connection.execute(
                """
                SELECT *
                FROM saved_view_versions
                WHERE saved_view_id = %s AND version_no = %s
                """,
                (saved_view_id, target_version),
            ).fetchone()
            if target is None:
                raise NotFoundError(
                    f"Saved view version not found: {saved_view_id}:{target_version}"
                )
            actual_version = int(current["current_version"])
            if actual_version != expected_version:
                conflict_detail = self._saved_view_conflict_detail(
                    saved_view_id=saved_view_id,
                    reason="stale_saved_view_version",
                    expected_version=expected_version,
                    actual_version=actual_version,
                    target_version=target_version,
                )
                self.log_operation(
                    connection,
                    actor=actor,
                    action_type="restore_saved_view",
                    object_type="saved_view",
                    object_id=saved_view_id,
                    old_value=dict(current),
                    new_value=dict(target),
                    diff=conflict_detail,
                    reason=change_note or "Saved view restore rejected by optimistic lock",
                    result_status="conflict",
                )
            else:
                next_version = actual_version + 1
                row = connection.execute(
                    """
                    UPDATE saved_views
                    SET state = %s,
                        schema_version = %s,
                        current_version = %s,
                        updated_by = %s,
                        updated_at = now(),
                        last_restored_at = now()
                    WHERE id = %s
                    RETURNING *
                    """,
                    (
                        Jsonb(target["state"]),
                        target["schema_version"],
                        next_version,
                        actor,
                        saved_view_id,
                    ),
                ).fetchone()
                version_row = connection.execute(
                    """
                    INSERT INTO saved_view_versions(
                      saved_view_id, version_no, state, schema_version, action_type,
                      restored_from_version_no, change_note, created_by, metadata
                    )
                    VALUES (%s, %s, %s, %s, 'restore', %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        saved_view_id,
                        next_version,
                        Jsonb(target["state"]),
                        target["schema_version"],
                        target_version,
                        change_note,
                        actor,
                        Jsonb(
                            {
                                "restored_from_version_id": str(target["id"]),
                                "previous_version_no": actual_version,
                            }
                        ),
                    ),
                ).fetchone()
                self.log_operation(
                    connection,
                    actor=actor,
                    action_type="restore_saved_view",
                    object_type="saved_view",
                    object_id=saved_view_id,
                    old_value=dict(current),
                    new_value=self.saved_view_payload(row, versions=[version_row]),
                    diff={
                        "expected_version": expected_version,
                        "target_version": target_version,
                        "next_version": next_version,
                    },
                    reason=change_note or "API restore saved view version",
                )
        if conflict_detail is not None:
            raise ConflictError(conflict_detail)
        return self.get_saved_view(saved_view_id)

    def list_saved_view_versions(self, saved_view_id: UUID) -> list[dict[str, Any]]:
        with self.connect() as connection:
            self._saved_view_row(connection, saved_view_id, for_update=False)
            return self._saved_view_versions(connection, saved_view_id)

    def _saved_view_row(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        saved_view_id: UUID,
        *,
        for_update: bool,
    ) -> dict[str, Any]:
        lock_clause = "FOR UPDATE" if for_update else ""
        row = connection.execute(
            f"""
            SELECT sv.*,
                   (
                     SELECT count(*)::int
                     FROM saved_view_versions svv
                     WHERE svv.saved_view_id = sv.id
                   ) AS version_count
            FROM saved_views sv
            WHERE sv.id = %s
            {lock_clause}
            """,
            (saved_view_id,),
        ).fetchone()
        if row is None:
            raise NotFoundError(f"Saved view not found: {saved_view_id}")
        return dict(row)

    def _saved_view_versions(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        saved_view_id: UUID,
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT *
            FROM saved_view_versions
            WHERE saved_view_id = %s
            ORDER BY version_no DESC
            """,
            (saved_view_id,),
        ).fetchall()
        return [self.saved_view_version_payload(row) for row in rows]

    def _saved_view_conflict_detail(
        self,
        *,
        saved_view_id: UUID,
        reason: str,
        expected_version: int,
        actual_version: int,
        target_version: int | None = None,
    ) -> dict[str, Any]:
        detail: dict[str, Any] = {
            "schema_version": "saved-view-conflict-v1",
            "status": "conflict",
            "reason": reason,
            "saved_view_id": saved_view_id,
            "expected_version": expected_version,
            "actual_version": actual_version,
            "recovery": "fetch_latest_saved_view_or_restore_from_versions",
        }
        if target_version is not None:
            detail["target_version"] = target_version
        return _jsonable(detail)

    def list_home(self) -> dict[str, Any]:
        with self.connect() as connection:
            industries = connection.execute(
                """
                SELECT
                  i.id, i.slug, i.name_zh, i.name_en, i.parent_id, i.kind, i.taxonomy_version,
                  count(eim.entity_id)::int AS entity_count,
                  0 AS recent_change_count
                FROM industries i
                LEFT JOIN entity_industry_memberships eim ON eim.industry_id = i.id
                WHERE i.active = true
                GROUP BY i.id
                ORDER BY i.kind, i.slug
                LIMIT 12
                """
            ).fetchall()
            sessions = connection.execute(
                """
                SELECT
                  es.id, es.title, es.current_focus_entity_id, e.canonical_name, es.updated_at,
                  es.active_layers, es.direction, es.hops, es.budget, es.as_of,
                  es.scoring_profile_version_id, es.filters, es.state_version
                FROM exploration_sessions es
                LEFT JOIN entities e ON e.id = es.current_focus_entity_id
                ORDER BY es.updated_at DESC
                LIMIT 8
                """
            ).fetchall()
            changes = self.list_changes_for_connection(connection, limit=8)
            active_profile = self.active_scoring_profile(connection)
            calibration = connection.execute(
                """
                SELECT id, status, data_snapshot_at, scheduled_for, cadence_days,
                       proposal_status, finished_at
                FROM calibration_runs
                ORDER BY COALESCE(started_at, scheduled_for, data_snapshot_at) DESC
                LIMIT 1
                """
            ).fetchone()
            entity_count = connection.execute(
                "SELECT count(*)::int AS count FROM entities"
            ).fetchone()
            relationship_count = connection.execute(
                "SELECT count(*)::int AS count FROM relationships"
            ).fetchone()
            freshness = self.home_freshness(connection)
            active_context = self.active_analysis_context_payload(connection)
        return _jsonable(
            {
                "as_of": _now(),
                "global_search": {
                    "endpoint": "/v1/entities",
                    "query_param": "q",
                    "type_filter_param": "type",
                    "default_limit": 20,
                    "supported_entity_types": ENTITY_TYPES,
                    "example": {"q": "NVDA", "type": "legal_entity"},
                },
                "industries": industries,
                "watchlists": self.list_watchlists(),
                "recent_explorations": sessions,
                "changes": changes,
                "freshness": freshness,
                "model_status": {
                    "active_profile": active_profile,
                    "active_context": active_context,
                    "latest_calibration": calibration,
                    "calibration": self.home_calibration_status(calibration),
                    "fixture_policy": (
                        "Synthetic fixtures are explicitly marked and not live facts."
                    ),
                    "entity_count": entity_count["count"],
                    "relationship_count": relationship_count["count"],
                },
            }
        )

    def home_freshness(self, connection: psycopg.Connection[dict[str, Any]]) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT
              (SELECT count(*)::int FROM source_documents) AS source_document_count,
              (SELECT max(observed_at) FROM source_documents) AS latest_source_observed_at,
              (SELECT max(retrieved_at) FROM source_documents) AS latest_source_retrieved_at,
              (SELECT max(observed_at) FROM relationships) AS latest_relationship_observed_at,
              (SELECT max(observed_at) FROM events) AS latest_event_observed_at,
              (SELECT max(finished_at) FROM ingestion_runs) AS latest_ingestion_finished_at,
              (
                SELECT status
                FROM ingestion_runs
                ORDER BY started_at DESC
                LIMIT 1
              ) AS latest_ingestion_status,
              (
                SELECT count(*)::int
                FROM ingestion_runs
                WHERE status IN ('failed', 'error')
              ) AS failed_ingestion_count,
              (SELECT count(*)::int FROM fixture_entity_notices) AS synthetic_fixture_entities
            """
        ).fetchone()
        data_mode = (
            "synthetic_fixture"
            if row["synthetic_fixture_entities"] > 0
            else "live_or_seed"
        )
        if row["source_document_count"] == 0:
            status_value = "missing"
        elif row["failed_ingestion_count"] > 0:
            status_value = "ingestion_failed"
        elif data_mode == "synthetic_fixture":
            status_value = "synthetic_fixture"
        else:
            status_value = "available"
        return _jsonable(
            {
                **dict(row),
                "status": status_value,
                "data_mode": data_mode,
                "source_mode": (
                    "fixture_evidence"
                    if data_mode == "synthetic_fixture"
                    else "configured_sources"
                ),
            }
        )

    def home_calibration_status(self, calibration: dict[str, Any] | None) -> dict[str, Any]:
        cadence_days = 14
        if calibration is None:
            return {
                "latest_status": "not_scheduled",
                "cadence_days": cadence_days,
                "next_scheduled_for": None,
                "proposal_status": None,
            }
        cadence_days = int(calibration.get("cadence_days") or cadence_days)
        scheduled_for = calibration.get("scheduled_for")
        data_snapshot_at = calibration.get("data_snapshot_at")
        next_scheduled_for = scheduled_for
        if calibration["status"] in {"passed", "warning", "failed", "cancelled"}:
            anchor = data_snapshot_at or calibration.get("finished_at") or scheduled_for
            next_scheduled_for = anchor + timedelta(days=cadence_days) if anchor else None
        return _jsonable(
            {
                "latest_status": calibration["status"],
                "cadence_days": cadence_days,
                "latest_calibration_id": calibration["id"],
                "next_scheduled_for": next_scheduled_for,
                "proposal_status": calibration.get("proposal_status"),
            }
        )

    def normalize_graph_budget(self, budget: dict[str, Any] | None) -> dict[str, int]:
        raw_budget = budget or {}
        return {
            "max_nodes": min(
                int(raw_budget.get("max_nodes", DEFAULT_GRAPH_BUDGET["max_nodes"])),
                500,
            ),
            "max_edges": min(
                int(raw_budget.get("max_edges", DEFAULT_GRAPH_BUDGET["max_edges"])),
                2000,
            ),
            "expand_nodes": min(
                int(raw_budget.get("expand_nodes", DEFAULT_GRAPH_BUDGET["expand_nodes"])),
                100,
            ),
        }

    def normalize_exploration_state(
        self,
        *,
        session_id: UUID,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        focus = request.get("focus") or {}
        return {
            "version": EXPLORATION_STATE_VERSION,
            "session_id": str(session_id),
            "focus": {
                "object_type": focus.get("object_type", "entity"),
                "object_id": str(focus.get("object_id")),
            },
            "active_layers": request.get("active_layers") or ["supply_chain_operations"],
            "direction": request.get("direction") or "both",
            "hops": min(int(request.get("hops") or 1), GRAPH_HARD_LIMITS["max_hops"]),
            "as_of": _jsonable(request.get("as_of")),
            "scoring_profile_version_id": (
                str(request["scoring_profile_version_id"])
                if request.get("scoring_profile_version_id")
                else None
            ),
            "filters": request.get("filters") or {},
            "budget": self.normalize_graph_budget(request.get("budget")),
        }

    def exploration_url_state(self, state: dict[str, Any]) -> dict[str, Any]:
        filters_json = json.dumps(
            _jsonable(state["filters"]),
            sort_keys=True,
            separators=(",", ":"),
        )
        query: dict[str, str] = {
            "session": state["session_id"],
            "focus": f"{state['focus']['object_type']}:{state['focus']['object_id']}",
            "layers": ",".join(state["active_layers"]),
            "direction": state["direction"],
            "hops": str(state["hops"]),
            "filters": filters_json,
        }
        if state.get("as_of"):
            query["as_of"] = str(state["as_of"])
        if state.get("scoring_profile_version_id"):
            query["profile"] = str(state["scoring_profile_version_id"])
        restore_payload = {
            "session_id": state["session_id"],
            "focus": state["focus"],
            "active_layers": state["active_layers"],
            "direction": state["direction"],
            "hops": state["hops"],
            "as_of": state["as_of"],
            "scoring_profile_version_id": state["scoring_profile_version_id"],
            "filters": state["filters"],
            "budget": state["budget"],
        }
        return {
            "version": "exploration-url-state-v1",
            "route": "/",
            "query": query,
            "query_string": urlencode(query),
            "restore_payload": restore_payload,
        }

    def production_context_for_connection(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        *,
        as_of: datetime | str | None,
        active_profile: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        snapshot = connection.execute(
            """
            SELECT id, snapshot_key, scope, record_mode, status, as_of, activated_at, metadata
            FROM data_snapshots
            WHERE status = 'active'
            ORDER BY activated_at DESC NULLS LAST, created_at DESC
            LIMIT 1
            """
        ).fetchone()
        relationship_modes = connection.execute(
            """
            SELECT
              count(r.id)::int AS total,
              count(r.id) FILTER (WHERE frn.synthetic = true)::int AS synthetic_fixture,
              count(r.id) FILTER (WHERE frn.synthetic IS DISTINCT FROM true)::int AS database
            FROM relationships r
            LEFT JOIN fixture_relationship_notices frn ON frn.relationship_id = r.id
            WHERE r.status NOT IN ('superseded', 'revoked')
            """
        ).fetchone()
        candidate_modes = connection.execute(
            """
            SELECT
              COALESCE(
                jsonb_object_agg(record_mode, row_count ORDER BY record_mode),
                '{}'::jsonb
              ) AS record_modes
            FROM (
              SELECT record_mode, count(*)::int AS row_count
              FROM relationship_fact_candidates
              GROUP BY record_mode
            ) counts
            """
        ).fetchone()
        candidate_status = connection.execute(
            """
            SELECT
              count(*)::int AS total,
              count(*) FILTER (WHERE publication_status = 'published')::int AS published,
              count(*) FILTER (WHERE publication_status <> 'published')::int AS unpublished,
              count(*) FILTER (WHERE source_threshold_met = false)::int
                AS source_threshold_open,
              count(*) FILTER (WHERE review_status <> 'human_verified')::int
                AS review_open
            FROM relationship_fact_candidates
            """
        ).fetchone()
        candidate_samples = connection.execute(
            """
            SELECT
              id,
              candidate_key,
              relationship_type,
              relationship_family,
              publication_status,
              review_status,
              independent_source_count,
              source_threshold_met
            FROM relationship_fact_candidates
            ORDER BY
              (publication_status = 'published') DESC,
              source_threshold_met DESC,
              candidate_key
            LIMIT 3
            """
        ).fetchall()
        candidate_fact_summary = {
            **dict(candidate_status),
            "sample_candidates": [dict(row) for row in candidate_samples],
        }
        profile = (
            active_profile
            if active_profile is not None
            else self.active_scoring_profile(connection)
        )
        active_context = self.active_analysis_context_payload(connection)
        return _jsonable(
            {
                "schema_version": "production-context-v1",
                "request_as_of": as_of,
                "data_snapshot": dict(snapshot) if snapshot else None,
                "active_scoring_profile_version_id": (
                    profile["id"] if profile else None
                ),
                "active_scoring_profile": {
                    "profile_key": profile["profile_key"],
                    "version": profile["version"],
                    "model_key": profile["model_key"],
                }
                if profile
                else None,
                "active_analysis_context": active_context,
                "graph_query_version": GRAPH_QUERY_VERSION,
                "scoring_service_version": SCORING_SERVICE_VERSION,
                "record_modes": {
                    "published_relationships": {
                        "database": relationship_modes["database"],
                        "fixture": relationship_modes["synthetic_fixture"],
                        "total": relationship_modes["total"],
                    },
                    "relationship_fact_candidates": candidate_modes["record_modes"],
                },
                "candidate_fact_summary": candidate_fact_summary,
                "publication_policy": {
                    "published_relationship_table": "relationships",
                    "candidate_fact_table": "relationship_fact_candidates",
                    "relationship_fact_candidates_in_graph_edges": False,
                    "publish_requires_source_threshold": True,
                    "publish_requires_human_review": True,
                    "minimum_independent_sources": CANDIDATE_SOURCE_THRESHOLD_MIN,
                },
            }
        )

    def candidate_fact_summary_for_focus(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        *,
        focus_entity_id: UUID,
        relationship_families: list[str],
    ) -> dict[str, Any]:
        row = connection.execute(
            """
            SELECT
              count(*)::int AS total,
              count(*) FILTER (WHERE rfc.publication_status = 'published')::int AS published,
              count(*) FILTER (WHERE rfc.publication_status <> 'published')::int
                AS excluded_unpublished,
              count(*) FILTER (WHERE rfc.source_threshold_met = false)::int
                AS source_threshold_open,
              count(*) FILTER (WHERE rfc.review_status <> 'human_verified')::int
                AS review_open
            FROM relationship_fact_candidates rfc
            JOIN entity_resolution_candidates subject
              ON subject.id = rfc.subject_resolution_id
            JOIN entity_resolution_candidates object
              ON object.id = rfc.object_resolution_id
            WHERE rfc.relationship_family = ANY(%(relationship_families)s::text[])
              AND (
                subject.matched_entity_id = %(focus_entity_id)s
                OR object.matched_entity_id = %(focus_entity_id)s
              )
            """,
            {
                "focus_entity_id": focus_entity_id,
                "relationship_families": relationship_families,
            },
        ).fetchone()
        return _jsonable(
            {
                **dict(row),
                "excluded_from_graph_edges": row["excluded_unpublished"],
                "reason": (
                    "Relationship fact candidates remain outside graph edges until "
                    "source threshold and human review publication gates pass."
                ),
            }
        )

    def explain_score(
        self,
        *,
        object_type: str,
        object_id: UUID,
        profile_id: UUID | None = None,
    ) -> dict[str, Any]:
        if object_type != "relationship_fact_candidate":
            raise RepositoryError(
                "Only relationship_fact_candidate score explanations are implemented "
                "in the T1302/A203 API contract slice"
            )
        with self.connect() as connection:
            profile = (
                self.scoring_profile_by_id(connection, profile_id)
                if profile_id
                else self.active_scoring_profile(connection)
            )
            if profile is None:
                raise RepositoryError("No active scoring profile is available")
            row = connection.execute(
                """
                SELECT
                  rfc.id,
                  rfc.candidate_key,
                  rfc.relationship_type,
                  rfc.relationship_family,
                  rfc.record_mode,
                  rfc.fact_status,
                  rfc.publication_status,
                  rfc.confidence,
                  rfc.independent_source_count,
                  rfc.source_threshold_met,
                  rfc.review_status,
                  rfc.parser_version,
                  rfc.structured_fact,
                  rfc.counter_evidence,
                  subject.id AS subject_resolution_id,
                  subject.candidate_name AS subject_candidate_name,
                  subject.matched_entity_id AS subject_entity_id,
                  subject.matched_research_id AS subject_research_id,
                  subject.confidence AS subject_resolution_confidence,
                  object.id AS object_resolution_id,
                  object.candidate_name AS object_candidate_name,
                  object.matched_entity_id AS object_entity_id,
                  object.matched_research_id AS object_research_id,
                  object.confidence AS object_resolution_confidence,
                  COALESCE(
                    (
                      SELECT jsonb_agg(
                        jsonb_build_object(
                          'source_document_id', sd.id,
                          'source_tier', s.source_tier,
                          'publisher', sd.publisher,
                          'title', sd.title,
                          'url', sd.url,
                          'document_date', sd.document_date,
                          'observed_at', sd.observed_at,
                          'retrieved_at', sd.retrieved_at,
                          'content_hash', sd.content_hash,
                          'role', rfce.role,
                          'locator', rfce.locator,
                          'support_excerpt', rfce.support_excerpt
                        )
                        ORDER BY rfce.role, sd.publisher, sd.url
                      )
                      FROM relationship_fact_candidate_evidence rfce
                      JOIN source_documents sd ON sd.id = rfce.source_document_id
                      JOIN sources s ON s.id = sd.source_id
                      WHERE rfce.candidate_id = rfc.id
                    ),
                    '[]'::jsonb
                  ) AS evidence,
                  COALESCE(
                    (
                      SELECT jsonb_agg(
                        jsonb_build_object(
                          'queue_key', mrq.queue_key,
                          'priority', mrq.priority,
                          'status', mrq.status,
                          'reason', mrq.reason,
                          'requested_by', mrq.requested_by,
                          'created_at', mrq.created_at
                        )
                        ORDER BY mrq.priority, mrq.created_at
                      )
                      FROM manual_review_queue mrq
                      WHERE mrq.object_type = 'relationship_fact_candidate'
                        AND mrq.object_id = rfc.id
                    ),
                    '[]'::jsonb
                  ) AS review_queue
                FROM relationship_fact_candidates rfc
                JOIN entity_resolution_candidates subject
                  ON subject.id = rfc.subject_resolution_id
                JOIN entity_resolution_candidates object
                  ON object.id = rfc.object_resolution_id
                WHERE rfc.id = %s
                """,
                (object_id,),
            ).fetchone()
            if row is None:
                raise NotFoundError(f"Relationship fact candidate not found: {object_id}")
            return self.score_explanation_payload(
                row=row,
                profile=profile,
                production_context=self.production_context_for_connection(
                    connection,
                    as_of=None,
                    active_profile=profile,
                ),
            )

    @staticmethod
    def score_explanation_payload(
        *,
        row: dict[str, Any],
        profile: dict[str, Any],
        production_context: dict[str, Any],
    ) -> dict[str, Any]:
        confidence = float(row["confidence"])
        source_count = int(row["independent_source_count"])
        evidence = row["evidence"] or []
        source_threshold_ratio = min(
            source_count / CANDIDATE_SOURCE_THRESHOLD_MIN,
            1,
        )
        raw_score = round(confidence * 100, 2)
        evidence_quality = round(source_threshold_ratio * 100, 2)
        adjusted_score = round(raw_score * (evidence_quality / 100), 2)
        present_inputs = [
            row["confidence"] is not None,
            row["independent_source_count"] is not None,
            row["parser_version"] is not None,
            row["review_status"] is not None,
            bool(evidence),
        ]
        coverage = round((sum(1 for item in present_inputs if item) / len(present_inputs)) * 100, 2)
        missing_inputs: list[str] = []
        if not row["source_threshold_met"]:
            missing_inputs.append(
                f"independent_source_threshold>={CANDIDATE_SOURCE_THRESHOLD_MIN}"
            )
        if row["review_status"] != "human_verified":
            missing_inputs.append("human_review_verification")
        if row["publication_status"] != "published":
            missing_inputs.append("published_relationship_version")
        if not evidence:
            missing_inputs.append("evidence_chain")
        return _jsonable(
            {
                "object_type": "relationship_fact_candidate",
                "object_id": row["id"],
                "candidate_key": row["candidate_key"],
                "relationship_type": row["relationship_type"],
                "relationship_family": row["relationship_family"],
                "record_mode": row["record_mode"],
                "fact_status": row["fact_status"],
                "publication_status": row["publication_status"],
                "source_threshold": {
                    "minimum_independent_sources": CANDIDATE_SOURCE_THRESHOLD_MIN,
                    "independent_source_count": source_count,
                    "met": row["source_threshold_met"],
                },
                "review_status": row["review_status"],
                "parser_version": row["parser_version"],
                "raw_score": raw_score,
                "evidence_quality": evidence_quality,
                "adjusted_score": adjusted_score,
                "coverage": coverage,
                "contributions": [
                    {
                        "input": "candidate_confidence",
                        "value": confidence,
                        "score_points": raw_score,
                    },
                    {
                        "input": "independent_source_count",
                        "value": source_count,
                        "score_multiplier": source_threshold_ratio,
                    },
                    {
                        "input": "review_status",
                        "value": row["review_status"],
                        "publication_gate_passed": row["review_status"] == "human_verified",
                    },
                    {
                        "input": "publication_status",
                        "value": row["publication_status"],
                        "included_in_graph_edges": row["publication_status"] == "published",
                    },
                ],
                "missing_inputs": missing_inputs,
                "model_version": f"{profile['model_key']}@{profile['version']}",
                "profile_version": f"{profile['profile_key']}@{profile['version']}",
                "profile_version_id": profile["id"],
                "structured_fact": row["structured_fact"],
                "counter_evidence": row["counter_evidence"],
                "subject": {
                    "resolution_id": row["subject_resolution_id"],
                    "candidate_name": row["subject_candidate_name"],
                    "entity_id": row["subject_entity_id"],
                    "research_id": row["subject_research_id"],
                    "resolution_confidence": row["subject_resolution_confidence"],
                },
                "object": {
                    "resolution_id": row["object_resolution_id"],
                    "candidate_name": row["object_candidate_name"],
                    "entity_id": row["object_entity_id"],
                    "research_id": row["object_research_id"],
                    "resolution_confidence": row["object_resolution_confidence"],
                },
                "evidence": evidence,
                "review_queue": row["review_queue"] or [],
                "production_context": production_context,
                "scoring_service_version": SCORING_SERVICE_VERSION,
            }
        )

    def evidence_detail(
        self,
        *,
        object_type: str,
        object_id: UUID,
        limit: int = 20,
    ) -> dict[str, Any]:
        bounded_limit = max(1, min(limit, 50))
        with self.connect() as connection:
            if object_type == "relationship_fact_candidate":
                return self.relationship_fact_candidate_evidence_detail(
                    connection=connection,
                    object_id=object_id,
                    limit=bounded_limit,
                )
            if object_type == "relationship":
                return self.relationship_evidence_detail(
                    connection=connection,
                    object_id=object_id,
                    limit=bounded_limit,
                )
        raise RepositoryError(
            "Only relationship_fact_candidate and relationship evidence details are implemented "
            "for the MVP evidence center"
        )

    def relationship_fact_candidate_evidence_detail(
        self,
        *,
        connection: psycopg.Connection[dict[str, Any]],
        object_id: UUID,
        limit: int,
    ) -> dict[str, Any]:
        candidate = connection.execute(
            """
            SELECT
              id, candidate_key, relationship_type, relationship_family, record_mode,
              fact_status, publication_status, confidence, independent_source_count,
              source_threshold_met, review_status, parser_version, structured_fact,
              counter_evidence, created_at, updated_at
            FROM relationship_fact_candidates
            WHERE id = %s
            """,
            (object_id,),
        ).fetchone()
        if candidate is None:
            raise NotFoundError(f"Relationship fact candidate not found: {object_id}")
        total_count = int(
            connection.execute(
                """
                SELECT count(*) AS count
                FROM relationship_fact_candidate_evidence
                WHERE candidate_id = %s
                """,
                (object_id,),
            ).fetchone()["count"]
        )
        evidence_rows = connection.execute(
            """
            SELECT
              rfce.ingestion_evidence_chain_id,
              rfce.source_document_id,
              rfce.role,
              rfce.locator,
              rfce.support_excerpt,
              rfce.created_at,
              iec.evidence_role,
              COALESCE(iec.structured_fact, '{}'::jsonb) AS structured_fact,
              COALESCE(iec.counter_evidence, '[]'::jsonb) AS counter_evidence,
              iec.parser_version,
              iec.confidence,
              iec.review_status AS chain_review_status,
              iec.created_at AS chain_created_at,
              s.code AS source_code,
              s.name AS source_name,
              s.source_tier,
              sd.url,
              sd.title,
              sd.publisher,
              sd.document_date,
              sd.observed_at,
              sd.retrieved_at,
              sd.media_type,
              sd.content_hash
            FROM relationship_fact_candidate_evidence rfce
            JOIN ingestion_evidence_chain iec ON iec.id = rfce.ingestion_evidence_chain_id
            JOIN source_documents sd ON sd.id = rfce.source_document_id
            JOIN sources s ON s.id = sd.source_id
            WHERE rfce.candidate_id = %s
            ORDER BY
              CASE rfce.role WHEN 'supports' THEN 0 WHEN 'context' THEN 1 ELSE 2 END,
              sd.observed_at DESC,
              rfce.source_document_id
            LIMIT %s
            """,
            (object_id, limit),
        ).fetchall()
        return self.evidence_detail_payload(
            object_type="relationship_fact_candidate",
            object_id=object_id,
            object_summary=candidate,
            evidence_rows=evidence_rows,
            total_count=total_count,
            limit=limit,
            production_context=self.production_context_for_connection(connection, as_of=None),
        )

    def relationship_evidence_detail(
        self,
        *,
        connection: psycopg.Connection[dict[str, Any]],
        object_id: UUID,
        limit: int,
    ) -> dict[str, Any]:
        relationship = connection.execute(
            """
            SELECT
              r.id, r.subject_entity_id, r.object_entity_id, r.relationship_type,
              r.relationship_family, r.status, r.confidence, r.valid_from, r.valid_to,
              r.observed_at, r.qualifiers, COALESCE(frn.synthetic, false) AS synthetic,
              frn.fixture_notice
            FROM relationships r
            LEFT JOIN fixture_relationship_notices frn ON frn.relationship_id = r.id
            WHERE r.id = %s
            """,
            (object_id,),
        ).fetchone()
        if relationship is None:
            raise NotFoundError(f"Relationship not found: {object_id}")
        total_count = int(
            connection.execute(
                """
                SELECT count(*) AS count
                FROM relationship_evidence
                WHERE relationship_id = %s
                """,
                (object_id,),
            ).fetchone()["count"]
        )
        evidence_rows = connection.execute(
            """
            SELECT
              NULL::uuid AS ingestion_evidence_chain_id,
              re.source_document_id,
              re.role,
              re.locator,
              re.support_excerpt,
              re.created_at,
              re.role AS evidence_role,
              COALESCE(re.structured_fact, '{}'::jsonb) AS structured_fact,
              '[]'::jsonb AS counter_evidence,
              sd.parser_version,
              r.confidence,
              'published' AS chain_review_status,
              re.created_at AS chain_created_at,
              s.code AS source_code,
              s.name AS source_name,
              s.source_tier,
              sd.url,
              sd.title,
              sd.publisher,
              sd.document_date,
              sd.observed_at,
              sd.retrieved_at,
              sd.media_type,
              sd.content_hash
            FROM relationship_evidence re
            JOIN relationships r ON r.id = re.relationship_id
            JOIN source_documents sd ON sd.id = re.source_document_id
            JOIN sources s ON s.id = sd.source_id
            WHERE re.relationship_id = %s
            ORDER BY
              CASE re.role WHEN 'supports' THEN 0 WHEN 'context' THEN 1 ELSE 2 END,
              sd.observed_at DESC,
              re.source_document_id
            LIMIT %s
            """,
            (object_id, limit),
        ).fetchall()
        return self.evidence_detail_payload(
            object_type="relationship",
            object_id=object_id,
            object_summary=relationship,
            evidence_rows=evidence_rows,
            total_count=total_count,
            limit=limit,
            production_context=self.production_context_for_connection(connection, as_of=None),
        )

    @staticmethod
    def evidence_detail_payload(
        *,
        object_type: str,
        object_id: UUID,
        object_summary: dict[str, Any],
        evidence_rows: list[dict[str, Any]],
        total_count: int,
        limit: int,
        production_context: dict[str, Any],
    ) -> dict[str, Any]:
        source_documents: dict[UUID, dict[str, Any]] = {}
        evidence: list[dict[str, Any]] = []
        for row in evidence_rows:
            source_document_id = row["source_document_id"]
            support_excerpt = row["support_excerpt"] or ""
            structured_fact = row["structured_fact"] or {}
            counter_evidence = row["counter_evidence"] or []
            source_document = {
                "id": source_document_id,
                "source_code": row["source_code"],
                "source_name": row["source_name"],
                "source_tier": row["source_tier"],
                "publisher": row["publisher"],
                "title": row["title"],
                "url": row["url"],
                "document_date": row["document_date"],
                "observed_at": row["observed_at"],
                "retrieved_at": row["retrieved_at"],
                "media_type": row["media_type"],
                "content_hash": row["content_hash"],
            }
            source_documents[source_document_id] = source_document
            ingestion_evidence_chain_id = row["ingestion_evidence_chain_id"]
            evidence_id = (
                ingestion_evidence_chain_id
                if ingestion_evidence_chain_id is not None
                else f"{object_id}:{source_document_id}:{row['role']}"
            )
            evidence.append(
                {
                    "evidence_id": evidence_id,
                    "source_document_id": source_document_id,
                    "ingestion_evidence_chain_id": ingestion_evidence_chain_id,
                    "role": row["role"],
                    "source_tier": row["source_tier"],
                    "publisher": row["publisher"],
                    "title": row["title"],
                    "url": row["url"],
                    "document_date": row["document_date"],
                    "observed_at": row["observed_at"],
                    "retrieved_at": row["retrieved_at"],
                    "media_type": row["media_type"],
                    "content_hash": row["content_hash"],
                    "locator": row["locator"],
                    "support_excerpt": support_excerpt,
                    "snippet": {
                        "text": support_excerpt,
                        "locator": row["locator"],
                        "redaction_status": "none",
                    },
                    "structured_fact": structured_fact,
                    "counter_evidence": counter_evidence,
                    "parser_version": row["parser_version"],
                    "confidence": row["confidence"],
                    "review_status": row["chain_review_status"],
                    "created_at": row["created_at"],
                    "chain_created_at": row["chain_created_at"],
                    "source_document": source_document,
                }
            )
        return _jsonable(
            {
                "schema_version": "evidence-detail-v1",
                "object_type": object_type,
                "object_id": object_id,
                "object_summary": object_summary,
                "evidence_count": total_count,
                "returned_evidence_count": len(evidence),
                "source_document_count": len(source_documents),
                "limit": limit,
                "truncated": total_count > len(evidence),
                "source_documents": list(source_documents.values()),
                "evidence": evidence,
                "production_context": production_context,
            }
        )

    def start_exploration(self, request: dict[str, Any]) -> dict[str, Any]:
        focus = request["focus"]
        if focus["object_type"] != "entity":
            raise RepositoryError("Only entity focus is supported in the G2 API anchor")
        focus_entity_id = UUID(str(focus["object_id"]))
        as_of = request.get("as_of")
        direction = request.get("direction") or "both"
        hops = min(int(request.get("hops") or 1), GRAPH_HARD_LIMITS["max_hops"])
        budget = self.normalize_graph_budget(request.get("budget"))
        with self.connect() as connection:
            self.entity_summary(connection, focus_entity_id)
            session_id = request.get("session_id")
            if session_id:
                row = connection.execute(
                    """
                    UPDATE exploration_sessions
                    SET current_focus_entity_id = %s,
                        active_layers = %s,
                        direction = %s,
                        hops = %s,
                        budget = %s,
                        as_of = %s,
                        scoring_profile_version_id = %s,
                        filters = %s,
                        updated_at = now()
                    WHERE id = %s
                    RETURNING id
                    """,
                    (
                        focus_entity_id,
                        request["active_layers"],
                        direction,
                        hops,
                        Jsonb(budget),
                        as_of,
                        request.get("scoring_profile_version_id"),
                        Jsonb(request.get("filters") or {}),
                        UUID(str(session_id)),
                    ),
                ).fetchone()
                if row is None:
                    raise NotFoundError(f"Exploration session not found: {session_id}")
                session_uuid = row["id"]
            else:
                row = connection.execute(
                    """
                    INSERT INTO exploration_sessions(
                      title, current_focus_entity_id, active_layers, direction, hops, budget,
                      as_of, scoring_profile_version_id, filters
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        f"Exploration: {focus_entity_id}",
                        focus_entity_id,
                        request["active_layers"],
                        direction,
                        hops,
                        Jsonb(budget),
                        as_of,
                        request.get("scoring_profile_version_id"),
                        Jsonb(request.get("filters") or {}),
                    ),
                ).fetchone()
                session_uuid = row["id"]
            self.append_exploration_step(
                connection,
                session_uuid,
                from_entity_id=None,
                to_entity_id=focus_entity_id,
                action="start",
                inherited_state={"direction": direction, "hops": hops, "budget": budget},
            )
            return self.exploration_response_for_connection(connection, session_uuid, request)

    def reroot_exploration(self, request: dict[str, Any]) -> dict[str, Any]:
        session_id = UUID(str(request["session_id"]))
        new_focus = UUID(str(request["new_focus_entity_id"]))
        with self.connect() as connection:
            self.entity_summary(connection, new_focus)
            session = connection.execute(
                """
                SELECT id, current_focus_entity_id, active_layers, as_of,
                       scoring_profile_version_id, filters, direction, hops, budget
                FROM exploration_sessions
                WHERE id = %s
                """,
                (session_id,),
            ).fetchone()
            if session is None:
                raise NotFoundError(f"Exploration session not found: {session_id}")
            inherit_state = bool(request.get("inherit_state", True))
            if inherit_state:
                next_state = {
                    "active_layers": session["active_layers"],
                    "direction": session["direction"],
                    "hops": session["hops"],
                    "as_of": session["as_of"],
                    "scoring_profile_version_id": session["scoring_profile_version_id"],
                    "filters": session["filters"],
                    "budget": self.normalize_graph_budget(session["budget"]),
                }
            else:
                next_state = {
                    "active_layers": ["supply_chain_operations"],
                    "direction": "both",
                    "hops": 1,
                    "as_of": None,
                    "scoring_profile_version_id": None,
                    "filters": {},
                    "budget": DEFAULT_GRAPH_BUDGET,
                }
            target_session_id = session_id
            if request.get("open_in_new_workspace"):
                row = connection.execute(
                    """
                    INSERT INTO exploration_sessions(
                      title, current_focus_entity_id, active_layers, direction, hops, budget,
                      as_of, scoring_profile_version_id, filters
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                    """,
                    (
                        f"Reroot: {new_focus}",
                        new_focus,
                        next_state["active_layers"],
                        next_state["direction"],
                        next_state["hops"],
                        Jsonb(next_state["budget"]),
                        next_state["as_of"],
                        next_state["scoring_profile_version_id"],
                        Jsonb(next_state["filters"]),
                    ),
                ).fetchone()
                target_session_id = row["id"]
            else:
                connection.execute(
                    """
                    UPDATE exploration_sessions
                    SET current_focus_entity_id = %s,
                        active_layers = %s,
                        direction = %s,
                        hops = %s,
                        budget = %s,
                        as_of = %s,
                        scoring_profile_version_id = %s,
                        filters = %s,
                        updated_at = now()
                    WHERE id = %s
                    """,
                    (
                        new_focus,
                        next_state["active_layers"],
                        next_state["direction"],
                        next_state["hops"],
                        Jsonb(next_state["budget"]),
                        next_state["as_of"],
                        next_state["scoring_profile_version_id"],
                        Jsonb(next_state["filters"]),
                        session_id,
                    ),
                )
            self.append_exploration_step(
                connection,
                target_session_id,
                from_entity_id=session["current_focus_entity_id"],
                to_entity_id=new_focus,
                action="reroot",
                inherited_state={
                    "inherit_state": inherit_state,
                    "active_layers": next_state["active_layers"],
                    "direction": next_state["direction"],
                    "hops": next_state["hops"],
                    "budget": next_state["budget"],
                },
            )
            session_request = {
                "focus": {"object_type": "entity", "object_id": str(new_focus)},
                **next_state,
            }
            return self.exploration_response_for_connection(
                connection,
                target_session_id,
                session_request,
            )

    def expand_exploration(self, request: dict[str, Any]) -> dict[str, Any]:
        session_id = UUID(str(request["session_id"]))
        anchor_entity_id = UUID(str(request["anchor_entity_id"]))
        with self.connect() as connection:
            self.entity_summary(connection, anchor_entity_id)
            session = connection.execute(
                """
                SELECT id, current_focus_entity_id, active_layers, as_of,
                       scoring_profile_version_id, filters, direction, hops, budget
                FROM exploration_sessions
                WHERE id = %s
                """,
                (session_id,),
            ).fetchone()
            if session is None:
                raise NotFoundError(f"Exploration session not found: {session_id}")
            expand_request = {
                "session_id": str(session_id),
                "focus": {"object_type": "entity", "object_id": str(anchor_entity_id)},
                "active_layers": request.get("layers") or session["active_layers"],
                "direction": request.get("direction") or session["direction"],
                "hops": 1,
                "as_of": session["as_of"],
                "scoring_profile_version_id": session["scoring_profile_version_id"],
                "filters": session["filters"] or {},
                "budget": self.normalize_graph_budget(request.get("budget")),
                "expand_mode": True,
            }
            return self.exploration_response_for_connection(
                connection,
                session_id,
                expand_request,
            )

    def append_exploration_step(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        session_id: UUID,
        *,
        from_entity_id: UUID | None,
        to_entity_id: UUID,
        action: str,
        inherited_state: dict[str, Any],
    ) -> None:
        next_sequence = connection.execute(
            """
            SELECT COALESCE(max(sequence_no), -1) + 1 AS sequence_no
            FROM exploration_steps
            WHERE session_id = %s
            """,
            (session_id,),
        ).fetchone()["sequence_no"]
        connection.execute(
            """
            INSERT INTO exploration_steps(
              session_id, sequence_no, from_entity_id, to_entity_id, action, inherited_state
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                session_id,
                next_sequence,
                from_entity_id,
                to_entity_id,
                action,
                Jsonb(inherited_state),
            ),
        )

    def exploration_response_for_connection(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        session_id: UUID,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        focus_entity_id = UUID(str(request["focus"]["object_id"]))
        focus = self.entity_summary(connection, focus_entity_id)
        graph = self.graph_for_focus(connection, focus_entity_id, request)
        state = self.normalize_exploration_state(session_id=session_id, request=request)
        url_state = self.exploration_url_state(state)
        active_profile = self.active_scoring_profile(connection) or {}
        history = connection.execute(
            """
            SELECT sequence_no, from_entity_id, to_entity_id, action, inherited_state, created_at
            FROM exploration_steps
            WHERE session_id = %s
            ORDER BY sequence_no
            """,
            (session_id,),
        ).fetchall()
        return _jsonable(
            {
                **graph,
                "session_id": session_id,
                "focus": focus,
                "state": {**state, "url_state": url_state},
                "history": history,
                "active_profile": active_profile,
                "coverage": graph["coverage"],
                "human_summary": {
                    "fixture_disclosure": "Synthetic fixture records are explicitly marked.",
                    "relationship_count": len(graph["edges"]),
                    "node_count": len(graph["nodes"]),
                },
            }
        )

    def graph_for_focus(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        focus_entity_id: UUID,
        request: dict[str, Any],
    ) -> dict[str, Any]:
        budget = self.normalize_graph_budget(request.get("budget"))
        max_nodes = budget["max_nodes"]
        max_edges = budget["max_edges"]
        expand_nodes = budget["expand_nodes"]
        if request.get("expand_mode"):
            max_nodes = min(max_nodes, expand_nodes + 1)
            max_edges = min(max_edges, expand_nodes)
        direction = request.get("direction") or "both"
        hops = min(int(request.get("hops") or 1), GRAPH_HARD_LIMITS["max_hops"])
        as_of = request.get("as_of")
        active_layers = request.get("active_layers") or ["supply_chain_operations"]
        filters = request.get("filters") or {}
        relationship_families = _relationship_families_for_layers(active_layers)
        requested_families = _relationship_family_filter(filters.get("relationship_family"))
        if requested_families:
            relationship_families = [
                family for family in relationship_families if family in requested_families
            ]
        truncation_reasons: list[str] = []
        if direction in {"upstream", "in"}:
            direction_clause = "r.object_entity_id = %(focus)s"
        elif direction in {"downstream", "out"}:
            direction_clause = "r.subject_entity_id = %(focus)s"
        else:
            direction_clause = "(r.subject_entity_id = %(focus)s OR r.object_entity_id = %(focus)s)"
        rows = connection.execute(
            f"""
            SELECT
              r.id, r.subject_entity_id, r.object_entity_id, r.relationship_type,
              r.relationship_family, r.status, r.confidence, r.valid_from, r.valid_to,
              r.amount, r.currency, r.amount_kind, r.qualifiers,
              count(re.source_document_id)::int AS evidence_count,
              frn.fixture_notice, COALESCE(frn.synthetic, false) AS synthetic
            FROM relationships r
            LEFT JOIN relationship_evidence re ON re.relationship_id = r.id
            LEFT JOIN fixture_relationship_notices frn ON frn.relationship_id = r.id
            WHERE {direction_clause}
              AND r.status NOT IN ('superseded', 'revoked')
              AND r.relationship_family = ANY(%(relationship_families)s::text[])
              AND (
                %(as_of)s::timestamptz IS NULL
                OR (
                  (r.valid_from IS NULL OR r.valid_from <= %(as_of)s::timestamptz)
                  AND (r.valid_to IS NULL OR r.valid_to >= %(as_of)s::timestamptz)
                )
              )
            GROUP BY r.id, frn.fixture_notice, frn.synthetic
            ORDER BY r.confidence DESC NULLS LAST, r.observed_at DESC, r.id
            LIMIT %(limit)s
            """,
            {
                "focus": focus_entity_id,
                "as_of": as_of,
                "relationship_families": relationship_families,
                "limit": max_edges + 1,
            },
        ).fetchall()
        fetched_edge_count = len(rows)
        truncated = fetched_edge_count > max_edges
        if truncated:
            truncation_reasons.append("edge_budget")
        rows = rows[:max_edges]
        ordered_node_ids: list[UUID] = [focus_entity_id]
        for row in rows:
            for key in ("subject_entity_id", "object_entity_id"):
                if row[key] not in ordered_node_ids:
                    ordered_node_ids.append(row[key])
        if len(ordered_node_ids) > max_nodes:
            truncated = True
            truncation_reasons.append("node_budget")
            ordered_node_ids = ordered_node_ids[:max_nodes]
        node_set = set(ordered_node_ids)
        rows = [
            row
            for row in rows
            if row["subject_entity_id"] in node_set and row["object_entity_id"] in node_set
        ]
        node_rows = connection.execute(
            """
            SELECT e.id, e.canonical_name, e.entity_type, fen.fixture_notice, fen.synthetic
            FROM entities e
            LEFT JOIN fixture_entity_notices fen ON fen.entity_id = e.id
            WHERE e.id = ANY(%s)
            """,
            (ordered_node_ids,),
        ).fetchall()
        node_map = {row["id"]: row for row in node_rows}
        nodes = [
            _jsonable(node_map[node_id])
            for node_id in ordered_node_ids
            if node_id in node_map
        ]
        source_count = 0
        if rows:
            source_count = connection.execute(
                """
                SELECT count(DISTINCT re.source_document_id)::int AS count
                FROM relationship_evidence re
                WHERE re.relationship_id = ANY(%s)
                """,
                ([row["id"] for row in rows],),
            ).fetchone()["count"]
        candidate_fact_summary = self.candidate_fact_summary_for_focus(
            connection,
            focus_entity_id=focus_entity_id,
            relationship_families=relationship_families,
        )
        production_context = self.production_context_for_connection(
            connection,
            as_of=as_of,
        )
        edges = [
            _jsonable(
                {
                    "id": row["id"],
                    "subject_id": row["subject_entity_id"],
                    "object_id": row["object_entity_id"],
                    "relationship_type": row["relationship_type"],
                    "relationship_family": row["relationship_family"],
                    "status": row["status"],
                    "confidence": row["confidence"],
                    "valid_from": row["valid_from"],
                    "valid_to": row["valid_to"],
                    "amount": row["amount"],
                    "currency": row["currency"],
                    "amount_kind": row["amount_kind"],
                    "evidence_count": row["evidence_count"],
                    "qualifiers": row["qualifiers"],
                    "synthetic": row["synthetic"],
                    "fixture_notice": row["fixture_notice"],
                }
            )
            for row in rows
        ]
        return _jsonable(
            {
                "as_of": as_of or _now(),
                "query": {
                    "focus": request.get(
                        "focus",
                        {"object_type": "entity", "object_id": str(focus_entity_id)},
                    ),
                    "focus_entity_id": focus_entity_id,
                    "direction": direction,
                    "hops": hops,
                    "as_of": as_of,
                    "scoring_profile_version_id": request.get("scoring_profile_version_id"),
                    "active_layers": active_layers,
                    "filters": filters,
                    "budget": budget,
                    "hard_limits": GRAPH_HARD_LIMITS,
                },
                "nodes": nodes,
                "edges": edges,
                "truncated": truncated,
                "truncation": {
                    "applied": truncated,
                    "reasons": truncation_reasons,
                    "message": (
                        "Graph response was truncated by the bounded graph budget."
                        if truncated
                        else "Graph response is within the bounded graph budget."
                    ),
                    "fetched_edge_count": fetched_edge_count,
                    "returned_edge_count": len(edges),
                    "returned_node_count": len(nodes),
                },
                "continuation": {
                    "available": truncated,
                    "expand_endpoint": "/v1/explore/expand" if truncated else None,
                    "anchor_entity_id": focus_entity_id if truncated else None,
                    "direction": direction if truncated else None,
                    "expand_nodes": expand_nodes if truncated else None,
                },
                "warnings": (
                    [f"bounded_graph_budget_applied:{reason}" for reason in truncation_reasons]
                    if truncated
                    else []
                ),
                "coverage": {
                    "visible_nodes": len(nodes),
                    "visible_edges": len(edges),
                    "source_count": source_count,
                    "relationship_family_count": len(
                        {edge["relationship_family"] for edge in edges}
                    ),
                    "synthetic_fixture_edges": sum(1 for edge in edges if edge["synthetic"]),
                    "relationship_fact_candidates": candidate_fact_summary,
                },
                "production_context": production_context,
            }
        )

    def find_relationship_paths(
        self,
        *,
        from_entity_id: UUID,
        to_entity_id: UUID,
        path_type: str,
        max_length: int,
        as_of: datetime | None = None,
    ) -> dict[str, Any]:
        if path_type not in PATH_TYPE_RELATIONSHIP_FAMILY_MAP:
            raise RepositoryError(f"Unsupported path_type: {path_type}")
        bounded_length = min(max_length, GRAPH_HARD_LIMITS["max_path_length"])
        relationship_families = sorted(PATH_TYPE_RELATIONSHIP_FAMILY_MAP[path_type])
        bottleneck_only = path_type == "bottleneck"
        with self.connect() as connection:
            from_entity = self.entity_summary(connection, from_entity_id)
            to_entity = self.entity_summary(connection, to_entity_id)
            if from_entity_id == to_entity_id:
                return _jsonable(
                    {
                        "as_of": as_of or _now(),
                        "query": {
                            "from": from_entity_id,
                            "to": to_entity_id,
                            "path_type": path_type,
                            "max_length": bounded_length,
                            "relationship_families": relationship_families,
                            "hard_limits": GRAPH_HARD_LIMITS,
                            "max_paths": PATH_RESULT_LIMIT,
                        },
                        "from": from_entity,
                        "to": to_entity,
                        "paths": [
                            {
                                "path_index": 0,
                                "length": 0,
                                "node_ids": [from_entity_id],
                                "relationship_ids": [],
                                "edges": [],
                                "evidence": [],
                            }
                        ],
                        "truncated": False,
                        "coverage": {
                            "path_count": 1,
                            "edge_count": 0,
                            "source_count": 0,
                            "all_edges_have_evidence": True,
                        },
                        "production_context": self.production_context_for_connection(
                            connection,
                            as_of=as_of,
                        ),
                    }
                )
            path_rows = connection.execute(
                """
                WITH RECURSIVE candidate_edges AS (
                  SELECT
                    r.id, r.subject_entity_id, r.object_entity_id, r.confidence,
                    r.observed_at, sca.materiality,
                    count(re.source_document_id)::int AS evidence_count
                  FROM relationships r
                  JOIN relationship_evidence re ON re.relationship_id = r.id
                  LEFT JOIN supply_chain_relationship_attributes sca
                    ON sca.relationship_id = r.id
                  WHERE r.status NOT IN ('superseded', 'revoked')
                    AND r.relationship_family = ANY(%(relationship_families)s::text[])
                    AND (
                      %(as_of)s::timestamptz IS NULL
                      OR (
                        (r.valid_from IS NULL OR r.valid_from <= %(as_of)s::timestamptz)
                        AND (r.valid_to IS NULL OR r.valid_to >= %(as_of)s::timestamptz)
                      )
                    )
                    AND (
                      %(bottleneck_only)s = false
                      OR sca.materiality IN ('critical', 'high')
                    )
                  GROUP BY r.id, sca.materiality
                ),
                walk AS (
                  SELECT
                    ARRAY[%(from_entity_id)s::uuid, step.next_node]::uuid[] AS node_ids,
                    ARRAY[ce.id]::uuid[] AS relationship_ids,
                    ARRAY[step.traversal_direction]::text[] AS traversal_directions,
                    step.next_node AS current_node,
                    1 AS path_length,
                    COALESCE(ce.confidence, 0) AS min_confidence
                  FROM candidate_edges ce
                  JOIN LATERAL (
                    SELECT
                      CASE
                        WHEN ce.subject_entity_id = %(from_entity_id)s::uuid
                        THEN ce.object_entity_id
                        ELSE ce.subject_entity_id
                      END AS next_node,
                      CASE
                        WHEN ce.subject_entity_id = %(from_entity_id)s::uuid
                        THEN 'forward'
                        ELSE 'reverse'
                      END AS traversal_direction
                  ) step ON true
                  WHERE %(from_entity_id)s::uuid IN (ce.subject_entity_id, ce.object_entity_id)
                  UNION ALL
                  SELECT
                    w.node_ids || step.next_node,
                    w.relationship_ids || ce.id,
                    w.traversal_directions || step.traversal_direction,
                    step.next_node,
                    w.path_length + 1,
                    LEAST(w.min_confidence, COALESCE(ce.confidence, 0))
                  FROM walk w
                  JOIN candidate_edges ce
                    ON w.current_node IN (ce.subject_entity_id, ce.object_entity_id)
                  JOIN LATERAL (
                    SELECT
                      CASE
                        WHEN ce.subject_entity_id = w.current_node
                        THEN ce.object_entity_id
                        ELSE ce.subject_entity_id
                      END AS next_node,
                      CASE
                        WHEN ce.subject_entity_id = w.current_node
                        THEN 'forward'
                        ELSE 'reverse'
                      END AS traversal_direction
                  ) step ON true
                  WHERE w.path_length < %(max_length)s
                    AND NOT step.next_node = ANY(w.node_ids)
                )
                SELECT node_ids, relationship_ids, traversal_directions, path_length
                FROM walk
                WHERE current_node = %(to_entity_id)s::uuid
                ORDER BY path_length, min_confidence DESC, relationship_ids::text
                LIMIT %(path_limit)s
                """,
                {
                    "from_entity_id": from_entity_id,
                    "to_entity_id": to_entity_id,
                    "relationship_families": relationship_families,
                    "as_of": as_of,
                    "bottleneck_only": bottleneck_only,
                    "max_length": bounded_length,
                    "path_limit": PATH_RESULT_LIMIT + 1,
                },
            ).fetchall()
            truncated = len(path_rows) > PATH_RESULT_LIMIT
            path_rows = path_rows[:PATH_RESULT_LIMIT]
            relationship_ids = list(
                dict.fromkeys(
                    relationship_id
                    for row in path_rows
                    for relationship_id in row["relationship_ids"]
                )
            )
            node_ids = list(
                dict.fromkeys(node_id for row in path_rows for node_id in row["node_ids"])
            )
            relationship_map = self.relationship_detail_map(connection, relationship_ids)
            evidence_map = self.relationship_evidence_map(connection, relationship_ids)
            node_map = self.entity_detail_map(connection, node_ids)
            paths = []
            for index, row in enumerate(path_rows):
                path_node_ids = row["node_ids"]
                path_relationship_ids = row["relationship_ids"]
                traversal_directions = row["traversal_directions"]
                edges = []
                path_evidence = []
                for edge_index, relationship_id in enumerate(path_relationship_ids):
                    relationship = relationship_map[relationship_id]
                    edge_evidence = evidence_map.get(relationship_id, [])
                    path_evidence.extend(edge_evidence)
                    edges.append(
                        {
                            **relationship,
                            "edge_index": edge_index,
                            "evidence_count": len(edge_evidence),
                            "traversal_direction": traversal_directions[edge_index],
                            "traversal_from_id": path_node_ids[edge_index],
                            "traversal_to_id": path_node_ids[edge_index + 1],
                            "evidence": edge_evidence,
                        }
                    )
                paths.append(
                    _jsonable(
                        {
                            "path_index": index,
                            "length": row["path_length"],
                            "node_ids": path_node_ids,
                            "nodes": [node_map[node_id] for node_id in path_node_ids],
                            "relationship_ids": path_relationship_ids,
                            "edges": edges,
                            "evidence": path_evidence,
                        }
                    )
                )
            production_context = self.production_context_for_connection(
                connection,
                as_of=as_of,
            )
        source_ids = {
            evidence["source_document_id"]
            for path in paths
            for evidence in path["evidence"]
        }
        all_edges_have_evidence = all(
            bool(edge["evidence"]) for path in paths for edge in path["edges"]
        )
        return _jsonable(
            {
                "as_of": as_of or _now(),
                "query": {
                    "from": from_entity_id,
                    "to": to_entity_id,
                    "path_type": path_type,
                    "max_length": bounded_length,
                    "relationship_families": relationship_families,
                    "bottleneck_only": bottleneck_only,
                    "hard_limits": GRAPH_HARD_LIMITS,
                    "max_paths": PATH_RESULT_LIMIT,
                },
                "from": from_entity,
                "to": to_entity,
                "paths": paths,
                "truncated": truncated,
                "coverage": {
                    "path_count": len(paths),
                    "edge_count": len(relationship_ids),
                    "source_count": len(source_ids),
                    "all_edges_have_evidence": all_edges_have_evidence,
                },
                "warnings": (
                    ["bounded_path_result_limit_applied"] if truncated else []
                ),
                "production_context": production_context,
            }
        )

    def entity_detail_map(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        entity_ids: list[UUID],
    ) -> dict[UUID, dict[str, Any]]:
        if not entity_ids:
            return {}
        rows = connection.execute(
            """
            SELECT e.id, e.canonical_name, e.entity_type, fen.fixture_notice, fen.synthetic
            FROM entities e
            LEFT JOIN fixture_entity_notices fen ON fen.entity_id = e.id
            WHERE e.id = ANY(%s)
            """,
            (entity_ids,),
        ).fetchall()
        return {row["id"]: _jsonable(row) for row in rows}

    def relationship_detail_map(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        relationship_ids: list[UUID],
    ) -> dict[UUID, dict[str, Any]]:
        if not relationship_ids:
            return {}
        rows = connection.execute(
            """
            SELECT
              r.id, r.subject_entity_id, r.object_entity_id, r.relationship_type,
              r.relationship_family, r.status, r.confidence, r.valid_from, r.valid_to,
              r.amount, r.currency, r.amount_kind, r.qualifiers, sca.materiality,
              frn.fixture_notice, COALESCE(frn.synthetic, false) AS synthetic
            FROM relationships r
            LEFT JOIN supply_chain_relationship_attributes sca ON sca.relationship_id = r.id
            LEFT JOIN fixture_relationship_notices frn ON frn.relationship_id = r.id
            WHERE r.id = ANY(%s)
            """,
            (relationship_ids,),
        ).fetchall()
        return {
            row["id"]: _jsonable(
                {
                    "id": row["id"],
                    "subject_id": row["subject_entity_id"],
                    "object_id": row["object_entity_id"],
                    "relationship_type": row["relationship_type"],
                    "relationship_family": row["relationship_family"],
                    "status": row["status"],
                    "confidence": row["confidence"],
                    "valid_from": row["valid_from"],
                    "valid_to": row["valid_to"],
                    "amount": row["amount"],
                    "currency": row["currency"],
                    "amount_kind": row["amount_kind"],
                    "qualifiers": row["qualifiers"],
                    "materiality": row["materiality"],
                    "synthetic": row["synthetic"],
                    "fixture_notice": row["fixture_notice"],
                }
            )
            for row in rows
        }

    def relationship_evidence_map(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        relationship_ids: list[UUID],
    ) -> dict[UUID, list[dict[str, Any]]]:
        if not relationship_ids:
            return {}
        rows = connection.execute(
            """
            SELECT
              re.relationship_id, re.source_document_id, re.role, re.locator,
              re.support_excerpt, re.structured_fact,
              s.source_tier,
              sd.url, sd.title, sd.publisher, sd.document_date, sd.observed_at,
              sd.retrieved_at, sd.media_type
            FROM relationship_evidence re
            JOIN source_documents sd ON sd.id = re.source_document_id
            JOIN sources s ON s.id = sd.source_id
            WHERE re.relationship_id = ANY(%s)
            ORDER BY
              re.relationship_id,
              CASE re.role WHEN 'supports' THEN 0 WHEN 'context' THEN 1 ELSE 2 END,
              sd.observed_at DESC,
              re.source_document_id
            """,
            (relationship_ids,),
        ).fetchall()
        evidence: dict[UUID, list[dict[str, Any]]] = {}
        for row in rows:
            evidence.setdefault(row["relationship_id"], []).append(
                _jsonable(
                    {
                        "source_document_id": row["source_document_id"],
                        "role": row["role"],
                        "source_tier": row["source_tier"],
                        "locator": row["locator"],
                        "support_excerpt": row["support_excerpt"],
                        "structured_fact": row["structured_fact"],
                        "url": row["url"],
                        "title": row["title"],
                        "publisher": row["publisher"],
                        "document_date": row["document_date"],
                        "observed_at": row["observed_at"],
                        "retrieved_at": row["retrieved_at"],
                        "media_type": row["media_type"],
                    }
                )
            )
        return evidence

    def list_changes(
        self,
        *,
        since: datetime | None = None,
        change_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            return self.list_changes_for_connection(
                connection,
                since=since,
                change_type=change_type,
                limit=limit,
            )

    def list_changes_for_connection(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        *,
        since: datetime | None = None,
        change_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        rows = connection.execute(
            """
            SELECT id, change_type, object_type, object_id, old_value, new_value,
                   review_required, created_at
            FROM changes
            WHERE (%s::timestamptz IS NULL OR created_at >= %s::timestamptz)
              AND (%s::text IS NULL OR change_type = %s)
            ORDER BY created_at DESC, id DESC
            LIMIT %s
            """,
            (since, since, change_type, change_type, limit),
        ).fetchall()
        return _jsonable(rows)

    def list_audit_logs(
        self,
        *,
        object_type: str | None = None,
        object_id: UUID | None = None,
        since: datetime | None = None,
    ) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, occurred_at, actor, action_type, object_type, object_id,
                       old_value, new_value, diff, reason, result_status, error
                FROM operation_logs
                WHERE (%s::text IS NULL OR object_type = %s)
                  AND (%s::uuid IS NULL OR object_id = %s)
                  AND (%s::timestamptz IS NULL OR occurred_at >= %s::timestamptz)
                ORDER BY occurred_at DESC, id DESC
                LIMIT 200
                """,
                (object_type, object_type, object_id, object_id, since, since),
            ).fetchall()
        return _jsonable(rows)

    def list_calibrations(self) -> list[dict[str, Any]]:
        with self.connect() as connection:
            rows = connection.execute(
                """
                SELECT id, scheduled_for, cadence_days, data_snapshot_at, status, metrics,
                       drift_report, proposal_status, started_at, finished_at, error
                FROM calibration_runs
                ORDER BY COALESCE(started_at, scheduled_for, data_snapshot_at) DESC
                LIMIT 100
                """
            ).fetchall()
        return _jsonable(rows)

    def queue_calibration(self) -> dict[str, Any]:
        with self.connect() as connection:
            active_profile = self.active_scoring_profile(connection)
            profile_version_id = UUID(active_profile["id"]) if active_profile else None
            row = connection.execute(
                """
                INSERT INTO calibration_runs(
                  scheduled_for, data_snapshot_at, profile_version_id, status,
                  proposal_status, metrics, drift_report
                )
                VALUES (now(), now(), %s, 'scheduled', 'none', '{}'::jsonb, '{}'::jsonb)
                RETURNING id, scheduled_for, cadence_days, data_snapshot_at, status,
                          metrics, drift_report, proposal_status
                """,
                (profile_version_id,),
            ).fetchone()
            self.log_operation(
                connection,
                actor="local_user",
                action_type="queue_calibration",
                object_type="calibration_run",
                object_id=row["id"],
                old_value=None,
                new_value=dict(row),
                reason="Manual API calibration queue; auto activation disabled",
            )
        return _jsonable(row)

    def log_operation(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        *,
        actor: str,
        action_type: str,
        object_type: str,
        object_id: UUID | None,
        old_value: dict[str, Any] | None,
        new_value: dict[str, Any] | None,
        reason: str,
        diff: dict[str, Any] | None = None,
        result_status: str = "success",
        model_version: str | None = None,
        profile_version: str | None = None,
    ) -> None:
        connection.execute(
            """
            INSERT INTO operation_logs(
              actor, action_type, object_type, object_id, old_value, new_value,
              diff, reason, model_version, profile_version, result_status
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                actor,
                action_type,
                object_type,
                object_id,
                Jsonb(_jsonable(old_value)) if old_value is not None else None,
                Jsonb(_jsonable(new_value)) if new_value is not None else None,
                Jsonb(_jsonable(diff or {})),
                reason,
                model_version,
                profile_version,
                result_status,
            ),
        )

    def record_relationship_supersession(
        self,
        *,
        supersedes_id: UUID,
        new_relationship_id: UUID,
        observed_at: datetime,
        confidence: Decimal | float,
        reason: str,
    ) -> dict[str, Any]:
        with self.connect() as connection:
            old = connection.execute(
                """
                SELECT *
                FROM relationships
                WHERE id = %s
                FOR UPDATE
                """,
                (supersedes_id,),
            ).fetchone()
            if old is None:
                raise NotFoundError(f"Relationship not found: {supersedes_id}")
            connection.execute(
                """
                UPDATE relationships
                SET status = 'superseded'
                WHERE id = %s
                """,
                (supersedes_id,),
            )
            new_row = connection.execute(
                """
                INSERT INTO relationships(
                  id, subject_entity_id, object_entity_id, relationship_type,
                  relationship_family, status, confidence, valid_from, valid_to,
                  announced_at, filed_at, observed_at, percentage, amount, currency,
                  amount_kind, qualifiers, derivation_rule, derivation_version, supersedes_id
                )
                VALUES (
                  %s, %s, %s, %s, %s, 'reported', %s, %s, %s, %s, %s, %s, %s,
                  %s, %s, %s, %s, %s, %s, %s
                )
                RETURNING *
                """,
                (
                    new_relationship_id,
                    old["subject_entity_id"],
                    old["object_entity_id"],
                    old["relationship_type"],
                    old["relationship_family"],
                    confidence,
                    old["valid_from"],
                    old["valid_to"],
                    old["announced_at"],
                    old["filed_at"],
                    observed_at,
                    old["percentage"],
                    old["amount"],
                    old["currency"],
                    old["amount_kind"],
                    Jsonb(old["qualifiers"]),
                    old["derivation_rule"],
                    old["derivation_version"],
                    supersedes_id,
                ),
            ).fetchone()
            self.copy_relationship_evidence(connection, supersedes_id, new_relationship_id)
            connection.execute(
                """
                INSERT INTO changes(change_type, object_type, object_id, old_value, new_value)
                VALUES ('superseded', 'relationship', %s, %s, %s)
                """,
                (
                    new_relationship_id,
                    Jsonb(_jsonable(old)),
                    Jsonb(_jsonable(dict(new_row) | {"reason": reason})),
                ),
            )
        return _jsonable(new_row)

    def copy_relationship_evidence(
        self,
        connection: psycopg.Connection[dict[str, Any]],
        old_relationship_id: UUID,
        new_relationship_id: UUID,
    ) -> None:
        connection.execute(
            """
            INSERT INTO relationship_evidence(
              relationship_id, source_document_id, role, locator, support_excerpt, structured_fact
            )
            SELECT %s, source_document_id, role, locator, support_excerpt, structured_fact
            FROM relationship_evidence
            WHERE relationship_id = %s
            ON CONFLICT (relationship_id, source_document_id, role) DO NOTHING
            """,
            (new_relationship_id, old_relationship_id),
        )

    def record_relationship_conflict(
        self,
        *,
        relationship_id: UUID,
        reason: str,
    ) -> dict[str, Any]:
        with self.connect() as connection:
            relationship = connection.execute(
                "SELECT * FROM relationships WHERE id = %s",
                (relationship_id,),
            ).fetchone()
            if relationship is None:
                raise NotFoundError(f"Relationship not found: {relationship_id}")
            row = connection.execute(
                """
                INSERT INTO changes(
                  change_type, object_type, object_id, old_value, new_value, review_required
                )
                VALUES ('conflict_detected', 'relationship', %s, %s, %s, true)
                RETURNING id, change_type, object_type, object_id, old_value, new_value,
                          review_required, created_at
                """,
                (
                    relationship_id,
                    Jsonb(_jsonable(relationship)),
                    Jsonb(
                        {
                            "reason": reason,
                            "preserve_relationship_status": relationship["status"],
                        }
                    ),
                ),
            ).fetchone()
        return _jsonable(row)
