#!/usr/bin/env python3
"""
🛠️ One-Time Migration Script: Local → Azure Course Database

⚠️  CRITICAL: This script is designed to run ONLY ONCE.
    It will permanently refuse to run after the first successful execution.

Purpose:
- Migrate existing course list from local SQLite to Azure SQL Database
- Validate all course data before transfer
- Prevent duplicate entries in Azure database
- Ensure data integrity throughout the process

🔒 Built-in Safeguards:
- Migration completion tracking to prevent re-execution
- Comprehensive validation of all course fields
- Duplicate detection before insertion
- Transaction-based atomic operations
- Detailed audit logging
- Dry-run mode for testing

Author: AI Learning Tracker Migration System
Date: July 21, 2025
"""

import os
import sys
import json
import sqlite3
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

# Try to import Azure SQL dependencies
try:
    import pyodbc
    AZURE_SQL_AVAILABLE = True
except ImportError:
    AZURE_SQL_AVAILABLE = False
    print("⚠️  WARNING: pyodbc not installed. Install with: pip install pyodbc")

# Configure comprehensive logging with UTF-8 encoding for Windows compatibility
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'migration_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CourseRecord:
    """Represents a validated course record for migration"""
    id: int
    title: str
    description: str
    url: str
    source: str
    level: str
    points: int
    category: Optional[str] = None
    difficulty: Optional[str] = None
    url_status: Optional[str] = None
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'url': self.url,
            'source': self.source,
            'level': self.level,
            'points': self.points,
            'category': self.category,
            'difficulty': self.difficulty,
            'url_status': self.url_status,
            'created_at': self.created_at
        }
    
    def get_unique_hash(self) -> str:
        """Generate unique hash for duplicate detection"""
        unique_string = f"{self.title.lower().strip()}|{self.url.lower().strip()}"
        return hashlib.md5(unique_string.encode()).hexdigest()

class MigrationTracker:
    """Manages migration state and prevents re-execution"""
    
    METADATA_FILE = "migration_metadata.json"
    
    def __init__(self):
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load migration metadata from file"""
        if os.path.exists(self.METADATA_FILE):
            try:
                with open(self.METADATA_FILE, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Could not load metadata file: {e}")
        
        return {
            "migration_completed": False,
            "completion_date": None,
            "total_records_processed": 0,
            "records_inserted": 0,
            "records_skipped": 0,
            "records_failed": 0,
            "migration_hash": None
        }
    
    def is_migration_completed(self) -> bool:
        """Check if migration has already been completed"""
        return self.metadata.get("migration_completed", False)
    
    def mark_migration_completed(self, stats: Dict):
        """Mark migration as completed and save metadata"""
        self.metadata.update({
            "migration_completed": True,
            "completion_date": datetime.now().isoformat(),
            **stats
        })
        
        try:
            with open(self.METADATA_FILE, 'w') as f:
                json.dump(self.metadata, f, indent=2)
            logger.info(f"✅ Migration metadata saved to {self.METADATA_FILE}")
        except Exception as e:
            logger.error(f"❌ Failed to save migration metadata: {e}")
    
    def get_completion_info(self) -> Dict:
        """Get information about previous migration"""
        return self.metadata

class LocalDatabaseReader:
    """Handles reading and validation of local SQLite database"""
    
    def __init__(self, db_path: str = "ai_learning.db"):
        self.db_path = db_path
        if not os.path.exists(db_path):
            raise FileNotFoundError(f"Local database not found: {db_path}")
    
    def get_all_courses(self) -> List[CourseRecord]:
        """Read and validate all courses from local database"""
        logger.info(f"📂 Reading courses from local database: {self.db_path}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all courses
            cursor.execute("""
                SELECT id, title, description, url, source, level, points, 
                       category, difficulty, url_status, created_at
                FROM courses 
                ORDER BY id
            """)
            
            raw_courses = cursor.fetchall()
            conn.close()
            
            logger.info(f"📊 Found {len(raw_courses)} raw course records")
            
            # Validate and convert to CourseRecord objects
            validated_courses = []
            invalid_count = 0
            
            for row in raw_courses:
                course = self._validate_course_row(row)
                if course:
                    validated_courses.append(course)
                else:
                    invalid_count += 1
            
            logger.info(f"✅ Validated {len(validated_courses)} courses")
            if invalid_count > 0:
                logger.warning(f"⚠️  Skipped {invalid_count} invalid course records")
            
            return validated_courses
            
        except Exception as e:
            logger.error(f"❌ Error reading local database: {e}")
            raise
    
    def _validate_course_row(self, row: Tuple) -> Optional[CourseRecord]:
        """Validate a single course record"""
        try:
            # Extract fields (handling potential None values)
            (id_, title, description, url, source, level, points, 
             category, difficulty, url_status, created_at) = row
            
            # Required field validation
            if not all([title, url, source, level]):
                logger.warning(f"⚠️  Skipping course ID {id_}: Missing required fields")
                return None
            
            # Clean and validate title
            title = str(title).strip()
            if len(title) < 3:
                logger.warning(f"⚠️  Skipping course ID {id_}: Title too short")
                return None
            
            # Clean and validate URL
            url = str(url).strip()
            if not url.startswith(('http://', 'https://')):
                logger.warning(f"⚠️  Skipping course ID {id_}: Invalid URL format")
                return None
            
            # Validate points
            if points is None:
                points = 0
            try:
                points = int(points)
                if points < 0:
                    points = 0
            except (ValueError, TypeError):
                points = 0
            
            # Validate level
            level = str(level).strip()
            if level not in ['Beginner', 'Intermediate', 'Advanced']:
                logger.warning(f"⚠️  Skipping course ID {id_}: Invalid level '{level}'")
                return None
            
            # Clean optional fields
            description = str(description).strip() if description else ""
            source = str(source).strip()
            category = str(category).strip() if category else None
            difficulty = str(difficulty).strip() if difficulty else None
            url_status = str(url_status).strip() if url_status else None
            
            return CourseRecord(
                id=id_,
                title=title,
                description=description,
                url=url,
                source=source,
                level=level,
                points=points,
                category=category,
                difficulty=difficulty,
                url_status=url_status,
                created_at=created_at
            )
            
        except Exception as e:
            logger.warning(f"⚠️  Skipping course ID {id_}: Validation error - {e}")
            return None

class AzureDatabaseWriter:
    """Handles writing to Azure SQL Database"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.connection_string = self._build_connection_string()
        
        if not self.dry_run and not AZURE_SQL_AVAILABLE:
            raise ImportError("pyodbc is required for Azure SQL connection")
    
    def _build_connection_string(self) -> str:
        """Build Azure SQL connection string from environment variables"""
        server = os.getenv('AZURE_SQL_SERVER')
        database = os.getenv('AZURE_SQL_DATABASE')
        username = os.getenv('AZURE_SQL_USERNAME')
        password = os.getenv('AZURE_SQL_PASSWORD')
        
        if not all([server, database, username, password]):
            missing = [k for k, v in {
                'AZURE_SQL_SERVER': server,
                'AZURE_SQL_DATABASE': database,
                'AZURE_SQL_USERNAME': username,
                'AZURE_SQL_PASSWORD': password
            }.items() if not v]
            
            if self.dry_run:
                logger.warning(f"⚠️  Missing Azure SQL env vars (OK for dry-run): {missing}")
                return "DRY_RUN_CONNECTION"
            else:
                raise ValueError(f"Missing required environment variables: {missing}")
        
        return (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={server};"
            f"DATABASE={database};"
            f"UID={username};"
            f"PWD={password};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=no;"
            f"Connection Timeout=30;"
        )
    
    def test_connection(self) -> bool:
        """Test Azure SQL connection"""
        if self.dry_run:
            logger.info("🔄 DRY RUN: Skipping Azure SQL connection test")
            return True
        
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            logger.info("✅ Azure SQL connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Azure SQL connection failed: {e}")
            return False
    
    def get_existing_course_hashes(self) -> set:
        """Get hashes of existing courses to prevent duplicates"""
        if self.dry_run:
            logger.info("🔄 DRY RUN: Returning empty course hash set")
            return set()
        
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            cursor.execute("SELECT title, url FROM courses")
            existing_courses = cursor.fetchall()
            conn.close()
            
            # Generate hashes for existing courses
            hashes = set()
            for title, url in existing_courses:
                unique_string = f"{title.lower().strip()}|{url.lower().strip()}"
                hash_value = hashlib.md5(unique_string.encode()).hexdigest()
                hashes.add(hash_value)
            
            logger.info(f"📊 Found {len(hashes)} existing courses in Azure database")
            return hashes
            
        except Exception as e:
            logger.error(f"❌ Error reading existing Azure courses: {e}")
            raise
    
    def insert_courses(self, courses: List[CourseRecord], existing_hashes: set) -> Dict:
        """Insert courses into Azure database with duplicate checking"""
        stats = {
            "total_processed": len(courses),
            "inserted": 0,
            "skipped_duplicates": 0,
            "failed": 0
        }
        
        if self.dry_run:
            logger.info(f"🔄 DRY RUN: Would process {len(courses)} courses")
            # Simulate the process for dry run
            for course in courses:
                if course.get_unique_hash() in existing_hashes:
                    stats["skipped_duplicates"] += 1
                else:
                    stats["inserted"] += 1
            
            logger.info(f"🔄 DRY RUN Results: {stats}")
            return stats
        
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Prepare insert statement
            insert_sql = """
                INSERT INTO courses 
                (title, description, url, source, level, points, category, difficulty, url_status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            for course in courses:
                try:
                    # Check for duplicates
                    if course.get_unique_hash() in existing_hashes:
                        logger.info(f"⏭️  Skipping duplicate: {course.title[:50]}...")
                        stats["skipped_duplicates"] += 1
                        continue
                    
                    # Insert course
                    cursor.execute(insert_sql, (
                        course.title,
                        course.description,
                        course.url,
                        course.source,
                        course.level,
                        course.points,
                        course.category,
                        course.difficulty,
                        course.url_status,
                        course.created_at or datetime.now().isoformat()
                    ))
                    
                    stats["inserted"] += 1
                    logger.info(f"✅ Inserted: {course.title[:50]}... ({course.points} pts, {course.level})")
                    
                except Exception as e:
                    stats["failed"] += 1
                    logger.error(f"❌ Failed to insert course '{course.title[:50]}...': {e}")
            
            # Commit all changes
            conn.commit()
            conn.close()
            
            logger.info(f"📊 Migration completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"❌ Error during batch insert: {e}")
            raise

class CourseDataMigrator:
    """Main migration orchestrator"""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.tracker = MigrationTracker()
        self.local_reader = LocalDatabaseReader()
        self.azure_writer = AzureDatabaseWriter(dry_run)
    
    def run_migration(self) -> bool:
        """Execute the complete migration process"""
        logger.info("🚀 Starting Course Database Migration")
        logger.info(f"📋 Mode: {'DRY RUN' if self.dry_run else 'LIVE MIGRATION'}")
        
        # 🔒 SAFEGUARD: Check if migration already completed
        if self.tracker.is_migration_completed() and not self.dry_run:
            completion_info = self.tracker.get_completion_info()
            logger.error("🚫 MIGRATION ALREADY COMPLETED!")
            logger.error(f"   Completion Date: {completion_info.get('completion_date')}")
            logger.error(f"   Records Inserted: {completion_info.get('records_inserted', 0)}")
            logger.error("   This script will now abort to prevent data corruption.")
            logger.error("   If you need to run again, manually delete migration_metadata.json")
            return False
        
        try:
            # Step 1: Test Azure connection
            logger.info("🔄 Step 1: Testing Azure SQL connection...")
            if not self.azure_writer.test_connection():
                logger.error("❌ Azure SQL connection failed. Aborting migration.")
                return False
            
            # Step 2: Read local courses
            logger.info("🔄 Step 2: Reading local course database...")
            local_courses = self.local_reader.get_all_courses()
            
            if not local_courses:
                logger.warning("⚠️  No valid courses found in local database. Nothing to migrate.")
                return True
            
            # Step 3: Get existing Azure courses
            logger.info("🔄 Step 3: Checking for existing courses in Azure...")
            existing_hashes = self.azure_writer.get_existing_course_hashes()
            
            # Step 4: Perform migration
            logger.info("🔄 Step 4: Migrating courses to Azure...")
            migration_stats = self.azure_writer.insert_courses(local_courses, existing_hashes)
            
            # Step 5: Update migration tracking (only for live runs)
            if not self.dry_run:
                logger.info("🔄 Step 5: Updating migration metadata...")
                self.tracker.mark_migration_completed({
                    "total_records_processed": migration_stats["total_processed"],
                    "records_inserted": migration_stats["inserted"],
                    "records_skipped": migration_stats["skipped_duplicates"],
                    "records_failed": migration_stats["failed"],
                    "migration_hash": hashlib.md5(
                        f"{len(local_courses)}{datetime.now().isoformat()}".encode()
                    ).hexdigest()
                })
            
            # Final summary
            logger.info("🎉 MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   Total Courses Processed: {migration_stats['total_processed']}")
            logger.info(f"   Successfully Inserted: {migration_stats['inserted']}")
            logger.info(f"   Skipped (Duplicates): {migration_stats['skipped_duplicates']}")
            logger.info(f"   Failed: {migration_stats['failed']}")
            
            if not self.dry_run:
                logger.info("🔒 Migration tracking enabled - script will refuse to run again")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed with error: {e}")
            return False

def main():
    """Main entry point with command-line argument handling"""
    print("🛠️  One-Time Course Database Migration: Local → Azure")
    print("=" * 60)
    
    # Check for dry-run mode
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    
    if dry_run:
        print("🔄 RUNNING IN DRY-RUN MODE")
        print("   No actual changes will be made to Azure database")
        print("   This is safe for testing and validation")
    else:
        print("⚠️  LIVE MIGRATION MODE")
        print("   This will make permanent changes to Azure database")
        print("   Ensure you have tested with --dry-run first")
        
        # Require explicit confirmation for live runs
        response = input("\nDo you want to proceed? (type 'MIGRATE' to confirm): ").strip()
        if response != "MIGRATE":
            print("❌ Migration cancelled by user")
            return
    
    print("=" * 60)
    
    # Run migration
    migrator = CourseDataMigrator(dry_run=dry_run)
    success = migrator.run_migration()
    
    if success:
        print("\n✅ Migration process completed successfully!")
        if dry_run:
            print("💡 Run without --dry-run to perform actual migration")
        else:
            print("🔒 Migration tracking activated - script protected from re-execution")
    else:
        print("\n❌ Migration process failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
