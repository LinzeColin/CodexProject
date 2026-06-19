# ADR-013 - Frontend Visualization

Status: Accepted
Date: 2026-06-19

## Decision

Use Next.js App Router with TypeScript strict mode. Use Cytoscape.js for bounded relationship graphs. Use ECharts for Sankey, timeline, matrix, radar, and source/model health visuals. Every P0 visual view needs an equivalent accessible list or table path.

## Acceptance IDs

A129, A130, A131, A132, A133, A134, A135, A136, A137, A138, A139, A140, A141, A142, A143, A144, A145, A146, A147, A148, A149, A150, A151, A152, A153, A154, A155, A156, A157, A158, A159, A160, A161, A162, A163, A164, A165, A166, A167, A168, A193

## Consequences

The open graph-renderer benchmark is moved to a revisit criterion. Cytoscape.js is the MVP default unless it fails measured graph-budget tests.

