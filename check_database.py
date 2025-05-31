#!/usr/bin/env python3
"""
Script to check database status and statistics
"""

from database import HistoryDatabase
import json

def main():
    print("🗄️  Checking database status...")
    print()
    
    # Initialize database
    db = HistoryDatabase()
    
    # Get statistics
    stats = db.get_database_stats()
    
    print("=== DATABASE STATISTICS ===")
    print(f"📊 Total snapshots: {stats.get('total_snapshots', 0)}")
    print(f"📈 Total player records: {stats.get('total_player_records', 0)}")
    print(f"👥 Unique players tracked: {stats.get('unique_players', 0)}")
    print(f"🏆 Total team records: {stats.get('total_team_records', 0)}")
    print()
    
    # Date range
    date_range = stats.get('snapshot_date_range', {})
    if date_range.get('earliest'):
        print(f"📅 Data range: {date_range['earliest']} to {date_range['latest']}")
    else:
        print("📅 No data available yet")
    print()
    
    # Source breakdown
    sources = stats.get('snapshots_by_source', {})
    if sources:
        print("📍 Snapshots by source:")
        for source, count in sources.items():
            print(f"   {source}: {count}")
    print()
    
    # Recent activity
    recent = stats.get('snapshots_last_24h', 0)
    print(f"🕐 Snapshots in last 24 hours: {recent}")
    
    if recent == 0:
        print("⚠️  No recent activity - database may be stale")
    elif recent < 24:
        print("⚠️  Less than expected activity (should be ~96 snapshots per day)")
    else:
        print("✅ Good activity level")
    
    print()
    
    # Check latest snapshot
    latest = db.get_latest_snapshot()
    if latest:
        teams_count = len(latest.get('teams', {}))
        total_players = latest.get('overall_stats', {}).get('total_players', 0)
        print(f"🎯 Latest snapshot: {teams_count} teams, {total_players} players")
        
        # Show team standings from latest data
        standings = latest.get('overall_stats', {}).get('team_standings', [])
        if standings:
            print("\n🏆 Current team standings:")
            for i, team in enumerate(standings[:3], 1):
                print(f"   {i}. {team['name']}: {team['total_xp']:,} XP")
    else:
        print("❌ No snapshot data available")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    main() 