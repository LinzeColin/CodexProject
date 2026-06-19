import sqlite3
from typing import Dict, List, Tuple


WORLD_CUP_2026_TEAMS: List[Tuple[str, str, str]] = [
    ("Canada", "Canada", "Concacaf"),
    ("Mexico", "Mexico", "Concacaf"),
    ("USA", "United States", "Concacaf"),
    ("Australia", "Australia", "AFC"),
    ("Iraq", "Iraq", "AFC"),
    ("IR Iran", "Iran", "AFC"),
    ("Japan", "Japan", "AFC"),
    ("Jordan", "Jordan", "AFC"),
    ("Korea Republic", "South Korea", "AFC"),
    ("Qatar", "Qatar", "AFC"),
    ("Saudi Arabia", "Saudi Arabia", "AFC"),
    ("Uzbekistan", "Uzbekistan", "AFC"),
    ("Algeria", "Algeria", "CAF"),
    ("Cabo Verde", "Cape Verde", "CAF"),
    ("Congo DR", "Democratic Republic of the Congo", "CAF"),
    ("Cote d'Ivoire", "Cote d'Ivoire", "CAF"),
    ("Egypt", "Egypt", "CAF"),
    ("Ghana", "Ghana", "CAF"),
    ("Morocco", "Morocco", "CAF"),
    ("Senegal", "Senegal", "CAF"),
    ("South Africa", "South Africa", "CAF"),
    ("Tunisia", "Tunisia", "CAF"),
    ("Curacao", "Curacao", "Concacaf"),
    ("Haiti", "Haiti", "Concacaf"),
    ("Panama", "Panama", "Concacaf"),
    ("Argentina", "Argentina", "CONMEBOL"),
    ("Brazil", "Brazil", "CONMEBOL"),
    ("Colombia", "Colombia", "CONMEBOL"),
    ("Ecuador", "Ecuador", "CONMEBOL"),
    ("Paraguay", "Paraguay", "CONMEBOL"),
    ("Uruguay", "Uruguay", "CONMEBOL"),
    ("New Zealand", "New Zealand", "OFC"),
    ("Austria", "Austria", "UEFA"),
    ("Belgium", "Belgium", "UEFA"),
    ("Bosnia and Herzegovina", "Bosnia and Herzegovina", "UEFA"),
    ("Croatia", "Croatia", "UEFA"),
    ("Czechia", "Czechia", "UEFA"),
    ("England", "England", "UEFA"),
    ("France", "France", "UEFA"),
    ("Germany", "Germany", "UEFA"),
    ("Netherlands", "Netherlands", "UEFA"),
    ("Norway", "Norway", "UEFA"),
    ("Portugal", "Portugal", "UEFA"),
    ("Scotland", "Scotland", "UEFA"),
    ("Spain", "Spain", "UEFA"),
    ("Sweden", "Sweden", "UEFA"),
    ("Switzerland", "Switzerland", "UEFA"),
    ("Türkiye", "Turkey", "UEFA"),
]


DEFAULT_SOURCES: List[Dict[str, str]] = [
    {
        "name": "FIFA World Cup 2026 Teams",
        "base_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/teams/",
        "source_type": "webpage",
        "terms_note": "Official FIFA public teams page; used as tournament context source.",
    },
    {
        "name": "FIFA World Cup 2026 Qualified Teams",
        "base_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/world-cup-2026-who-has-qualified",
        "source_type": "webpage",
        "terms_note": "Official FIFA public qualified teams article; used as qualification context source.",
    },
    {
        "name": "FIFA World Cup 2026 News",
        "base_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
        "source_type": "webpage",
        "terms_note": "Official FIFA public tournament page; no login or paywall bypass.",
    },
    {
        "name": "BBC Football RSS",
        "base_url": "http://feeds.bbci.co.uk/sport/football/rss.xml",
        "source_type": "rss",
        "terms_note": "Public RSS feed; review publisher terms before production/commercial use.",
    },
]


def seed_world_cup_2026(conn: sqlite3.Connection) -> Dict[str, int]:
    competition_cur = conn.execute(
        """
        INSERT OR IGNORE INTO competitions(name, season, region)
        VALUES ('FIFA World Cup 2026', '2026', 'Canada Mexico USA')
        """
    )
    teams_before = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    sources_before = conn.execute("SELECT COUNT(*) FROM crawl_sources").fetchone()[0]

    for name, country, confederation in WORLD_CUP_2026_TEAMS:
        conn.execute(
            """
            INSERT OR IGNORE INTO teams(name, country, team_type, fifa_rank)
            VALUES (?, ?, 'national', NULL)
            """,
            (name, country),
        )
        conn.execute(
            """
            INSERT INTO news_articles(title, url, source, sentiment, published_at)
            SELECT ?, ?, 'system_seed', 0, '2026-06-03'
            WHERE NOT EXISTS (
                SELECT 1 FROM news_articles WHERE title = ? AND source = 'system_seed'
            )
            """,
            (
                f"{name} qualified for FIFA World Cup 2026 ({confederation})",
                "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/articles/world-cup-2026-who-has-qualified",
                f"{name} qualified for FIFA World Cup 2026 ({confederation})",
            ),
        )

    for source in DEFAULT_SOURCES:
        conn.execute(
            """
            INSERT OR IGNORE INTO crawl_sources(name, base_url, source_type, terms_note, enabled)
            VALUES (?, ?, ?, ?, 1)
            """,
            (source["name"], source["base_url"], source["source_type"], source["terms_note"]),
        )

    teams_after = conn.execute("SELECT COUNT(*) FROM teams").fetchone()[0]
    sources_after = conn.execute("SELECT COUNT(*) FROM crawl_sources").fetchone()[0]
    return {
        "competition_inserted": 1 if competition_cur.rowcount else 0,
        "teams_total": teams_after,
        "teams_inserted": teams_after - teams_before,
        "sources_total": sources_after,
        "sources_inserted": sources_after - sources_before,
    }
