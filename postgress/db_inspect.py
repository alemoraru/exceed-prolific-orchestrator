#!/usr/bin/env python3
import os
import sys
import argparse
import psycopg2
import psycopg2.extras
from statistics import median

# Default database URL, can be overridden by the DATABASE_URL environment variable
DEFAULT_URL = os.getenv(
    "DATABASE_URL", "postgresql://admin:admin@localhost:5432/prolific"
)

# Sections of the database to inspect
SECTIONS = ["participants", "submissions", "feedback", "events", "all"]


def q(cur, sql, params=None):
    """Executes a SQL query and returns the rows and headers."""
    cur.execute(sql, params or ())
    try:
        rows = cur.fetchall()
    except psycopg2.ProgrammingError:
        rows = []
    return rows, [desc[0] for desc in cur.description] if cur.description else []


def print_table(title, rows, headers):
    """Prints a formatted table to the console."""
    print(f"\n=== {title} ===")
    if not rows:
        print("(no rows)")
        return
    widths = [
        max(len(str(h)), *(len(str(r[i])) for r in rows)) for i, h in enumerate(headers)
    ]

    def fmt_row(row):
        return " | ".join(str(v).ljust(widths[i]) for i, v in enumerate(row))

    print(fmt_row(headers))
    print("-+-".join("-" * w for w in widths))
    for r in rows:
        print(fmt_row(r))


def participants_section(cur):
    # Totals
    rows, hdr = q(cur, "SELECT COUNT(*) AS total_participants FROM participants;")
    print_table("Total participants that started", rows, hdr)

    # By skill level
    rows, hdr = q(
        cur,
        """
                       SELECT COALESCE(skill_level, '(null)') AS skill_level, COUNT(*) AS n
                       FROM participants
                       GROUP BY 1
                       ORDER BY n DESC, skill_level;
                       """,
    )
    print_table("Participants by skill_level", rows, hdr)

    # By intervention
    rows, hdr = q(
        cur,
        """
                       SELECT COALESCE(intervention_type, '(null)') AS intervention_type, COUNT(*) AS n
                       FROM participants
                       GROUP BY 1
                       ORDER BY n DESC, intervention_type;
                       """,
    )
    print_table("Participants by intervention_type", rows, hdr)

    # By snippet
    rows, hdr = q(
        cur,
        """
                       SELECT COALESCE(snippet_id, '(null)') AS snippet_id, COUNT(*) AS n
                       FROM participants
                       GROUP BY 1
                       ORDER BY n DESC, snippet_id;
                       """,
    )
    print_table("Participants by snippet_id", rows, hdr)

    # Cross-tab: skill x intervention
    rows, hdr = q(
        cur,
        """
                       SELECT COALESCE(skill_level, '(null)')       AS skill_level,
                              COALESCE(intervention_type, '(null)') AS intervention_type,
                              COUNT(*)                              AS n
                       FROM participants
                       GROUP BY 1, 2
                       ORDER BY 1, 2;
                       """,
    )
    print_table("Participants by (skill_level, intervention_type)", rows, hdr)

    # Cross-tab: skill x snippet
    rows, hdr = q(
        cur,
        """
                       SELECT COALESCE(skill_level, '(null)') AS skill_level,
                              COALESCE(snippet_id, '(null)')  AS snippet_id,
                              COUNT(*)                        AS n
                       FROM participants
                       GROUP BY 1, 2
                       ORDER BY 1, 2;
                       """,
    )
    print_table("Participants by (skill_level, snippet_id)", rows, hdr)

    # Finished survey & durations (best effort cast)
    finished_rows, hdr = q(
        cur,
        """
                                SELECT COUNT(*) AS finished
                                FROM participants
                                WHERE started_at IS NOT NULL
                                  AND ended_at IS NOT NULL;
                                """,
    )
    print_table(
        "Participants who finished (started_at AND ended_at present)",
        finished_rows,
        hdr,
    )

    # Try to compute durations if timestamps are castable
    try:
        rows, hdr = q(
            cur,
            """
                           SELECT COUNT(*)                                                                   AS n_durations,
                                  AVG(EXTRACT(EPOCH FROM (ended_at::timestamptz - started_at::timestamptz))) AS avg_secs
                           FROM participants
                           WHERE started_at IS NOT NULL
                             AND ended_at IS NOT NULL
                             AND ended_at ~ '[:+ZT-]' AND started_at ~ '[:+ZT-]';
                           """,
        )
        print_table(
            "Duration (avg seconds) for finished (castable ISO timestamps only)",
            rows,
            hdr,
        )

        # Median (client-side, same subset)
        cur.execute(
            """
                    SELECT EXTRACT(EPOCH FROM (ended_at::timestamptz - started_at::timestamptz)) AS secs
                    FROM participants
                    WHERE started_at IS NOT NULL
                      AND ended_at IS NOT NULL
                      AND ended_at ~ '[:+ZT-]' AND started_at ~ '[:+ZT-]';
                    """
        )
        vals = [r[0] for r in cur.fetchall() if r[0] is not None]
        if vals:
            print(f"Median duration (seconds): {int(median(vals))}")
        else:
            print("Median duration (seconds): n/a")
    except Exception as e:
        print("\n(Duration stats skipped – couldn't cast timestamps)")


def submissions_section(cur):
    """Inspect the code submissions table data."""

    # Totals
    rows, hdr = q(cur, "SELECT COUNT(*) AS total_submissions FROM code_submissions;")
    print_table("Total code submissions", rows, hdr)

    # Counts by status
    rows, hdr = q(
        cur,
        """
                       SELECT COALESCE(status,'(null)') AS status, COUNT(*) AS n
                       FROM code_submissions
                       GROUP BY 1
                       ORDER BY n DESC, status;
                       """,
    )
    print_table("Submission counts by status", rows, hdr)

    # Pass rate (by tests or status)
    rows, hdr = q(
        cur,
        """
                       WITH eval AS (SELECT *,
                                            CASE
                                                WHEN tests_total IS NOT NULL AND tests_passed IS NOT NULL AND tests_total > 0
                                                    THEN (tests_passed = tests_total)
                                                WHEN status IS NOT NULL
                                                    THEN (LOWER(status) IN ('pass', 'passed', 'success', 'ok'))
                                                ELSE NULL
                                                END AS passed
                                     FROM code_submissions)
                       SELECT COUNT(*) AS total_rows,
                              COUNT(*)    FILTER (WHERE passed IS TRUE) AS passed_rows, ROUND(100.0 * COUNT(*) FILTER (WHERE passed IS TRUE) / NULLIF(COUNT(*),0), 2) AS pass_rate_percent
                       FROM eval;
                       """,
    )
    print_table("Overall submission pass rate", rows, hdr)

    # Time stats
    rows, hdr = q(
        cur,
        """
                       SELECT COUNT(time_taken_ms)      AS n_with_time,
                              ROUND(AVG(time_taken_ms)) AS avg_ms,
                              MIN(time_taken_ms)        AS min_ms,
                              MAX(time_taken_ms)        AS max_ms
                       FROM code_submissions;
                       """,
    )
    print_table("Submission time stats (ms)", rows, hdr)


def feedback_section(cur):
    """Inspect the feedback table data."""

    # Overall means
    rows, hdr = q(
        cur,
        """
                       SELECT ROUND(AVG(length)::numeric, 2)             AS avg_length,
                              ROUND(AVG(jargon)::numeric, 2)             AS avg_jargon,
                              ROUND(AVG(sentence_structure)::numeric, 2) AS avg_sentence_structure,
                              ROUND(AVG(vocabulary)::numeric, 2)         AS avg_vocabulary,
                              ROUND(AVG(intrinsic_load)::numeric, 2)     AS avg_intrinsic_load,
                              ROUND(AVG(extraneous_load)::numeric, 2)    AS avg_extraneous_load,
                              ROUND(AVG(germane_load)::numeric, 2)       AS avg_germane_load,
                              ROUND(AVG(authoritativeness)::numeric, 2)  AS avg_authoritativeness
                       FROM feedback;
                       """,
    )
    print_table("Feedback (overall means)", rows, hdr)

    # Means by intervention_type (join participants)
    rows, hdr = q(
        cur,
        """
                       SELECT COALESCE(p.intervention_type, '(null)')    AS intervention_type,
                              COUNT(*)                                   AS n,
                              ROUND(AVG(length)::numeric, 2)             AS length,
                              ROUND(AVG(jargon)::numeric, 2)             AS jargon,
                              ROUND(AVG(sentence_structure)::numeric, 2) AS sentence_structure,
                              ROUND(AVG(vocabulary)::numeric, 2)         AS vocabulary,
                              ROUND(AVG(intrinsic_load)::numeric, 2)     AS intrinsic_load,
                              ROUND(AVG(extraneous_load)::numeric, 2)    AS extraneous_load,
                              ROUND(AVG(germane_load)::numeric, 2)       AS germane_load,
                              ROUND(AVG(authoritativeness)::numeric, 2)  AS authoritativeness
                       FROM feedback f
                                LEFT JOIN participants p USING (participant_id)
                       GROUP BY 1
                       ORDER BY n DESC, intervention_type;
                       """,
    )
    print_table("Feedback means by intervention_type", rows, hdr)

    # Means by skill_level
    rows, hdr = q(
        cur,
        """
                       SELECT COALESCE(p.skill_level, '(null)')          AS skill_level,
                              COUNT(*)                                   AS n,
                              ROUND(AVG(length)::numeric, 2)             AS length,
                              ROUND(AVG(jargon)::numeric, 2)             AS jargon,
                              ROUND(AVG(sentence_structure)::numeric, 2) AS sentence_structure,
                              ROUND(AVG(vocabulary)::numeric, 2)         AS vocabulary,
                              ROUND(AVG(intrinsic_load)::numeric, 2)     AS intrinsic_load,
                              ROUND(AVG(extraneous_load)::numeric, 2)    AS extraneous_load,
                              ROUND(AVG(germane_load)::numeric, 2)       AS germane_load,
                              ROUND(AVG(authoritativeness)::numeric, 2)  AS authoritativeness
                       FROM feedback f
                                LEFT JOIN participants p USING (participant_id)
                       GROUP BY 1
                       ORDER BY n DESC, skill_level;
                       """,
    )
    print_table("Feedback means by skill_level", rows, hdr)

    # Means by snippet_id
    rows, hdr = q(
        cur,
        """
                       SELECT COALESCE(f.snippet_id, '(null)')           AS snippet_id,
                              COUNT(*)                                   AS n,
                              ROUND(AVG(length)::numeric, 2)             AS length,
                              ROUND(AVG(jargon)::numeric, 2)             AS jargon,
                              ROUND(AVG(sentence_structure)::numeric, 2) AS sentence_structure,
                              ROUND(AVG(vocabulary)::numeric, 2)         AS vocabulary,
                              ROUND(AVG(intrinsic_load)::numeric, 2)     AS intrinsic_load,
                              ROUND(AVG(extraneous_load)::numeric, 2)    AS extraneous_load,
                              ROUND(AVG(germane_load)::numeric, 2)       AS germane_load,
                              ROUND(AVG(authoritativeness)::numeric, 2)  AS authoritativeness
                       FROM feedback f
                       GROUP BY 1
                       ORDER BY n DESC, snippet_id;
                       """,
    )
    print_table("Feedback means by snippet_id", rows, hdr)


def events_section(cur):
    """Inspect the events table data."""
    # Event counts
    rows, hdr = q(
        cur,
        """
                       SELECT event_type, COUNT(*) AS n
                       FROM events
                       GROUP BY 1
                       ORDER BY n DESC, event_type;
                       """,
    )
    print_table("Events by type", rows, hdr)

    # Event counts per participant (top 50)
    rows, hdr = q(
        cur,
        """
                       SELECT participant_id, COUNT(*) AS n
                       FROM events
                       GROUP BY participant_id
                       ORDER BY n DESC, participant_id LIMIT 50;
                       """,
    )
    print_table("Top 50 participants by event count", rows, hdr)


def main():
    """Main function to parse arguments and run the inspection."""
    parser = argparse.ArgumentParser(
        description="Inspect Prolific study database stats."
    )
    parser.add_argument(
        "--db",
        "--database-url",
        dest="db_url",
        default=DEFAULT_URL,
        help=f"PostgreSQL URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--section", choices=SECTIONS, default="all", help="Which section to run"
    )
    args = parser.parse_args()

    try:
        conn = psycopg2.connect(args.db_url)
    except Exception as e:
        print(
            f"Could not connect to DB: {e}\nTried URL: {args.db_url}", file=sys.stderr
        )
        sys.exit(1)

    with conn, conn.cursor() as cur:
        if args.section in ("participants", "all"):
            participants_section(cur)
        if args.section in ("submissions", "all"):
            submissions_section(cur)
        if args.section in ("feedback", "all"):
            feedback_section(cur)
        if args.section in ("events", "all"):
            events_section(cur)

    conn.close()


if __name__ == "__main__":
    main()
