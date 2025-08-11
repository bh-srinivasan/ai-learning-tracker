#!/usr/bin/env python3
"""
Advanced Flask Repository Cleanup Tool with Route-Aware In-Use Detection

This tool safely cleans up repository artifacts by:
1. Loading Flask app in TESTING mode (no server required)
2. Crawling GET routes to detect in-use templates, static files, and opened files
3. Static analysis of POST/PUT routes for upload/document directories
4. Optional safe simulation of POST routes with dummy data
5. Protecting Git-tracked files and in-use assets
6. Age-gated deletion with comprehensive dry-run reports

Safety Features:
- Never deletes Git-tracked files
- DRY-RUN by default with detailed reporting
- Creates backups before deletion
- Requires explicit confirmations for destructive operations
- Protects upload/document directories discovered via static analysis

Usage:
    python tools/safe_clean.py                          # Dry-run only
    python tools/safe_clean.py --route-scan             # Include route analysis
    python tools/safe_clean.py --route-scan --apply     # Apply with route analysis
    python tools/safe_clean.py --simulate-post --post-allow "^/test-upload$" --apply
"""

import os
import re
import sys
import ast
import json
import shutil
import zipfile
import argparse
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Set, List, Dict, Optional, Tuple, Any
from contextlib import contextmanager
from dataclasses import dataclass
import builtins


@dataclass
class ScanResults:
    """Results from route scanning and static analysis."""
    routes_scanned: int = 0
    templates_found: Set[str] = None
    static_files_found: Set[str] = None
    opened_files: Set[str] = None
    upload_dirs_static: Set[str] = None
    upload_dirs_dynamic: Set[str] = None
    post_routes_simulated: int = 0
    
    def __post_init__(self):
        if self.templates_found is None:
            self.templates_found = set()
        if self.static_files_found is None:
            self.static_files_found = set()
        if self.opened_files is None:
            self.opened_files = set()
        if self.upload_dirs_static is None:
            self.upload_dirs_static = set()
        if self.upload_dirs_dynamic is None:
            self.upload_dirs_dynamic = set()


class FileOpenTracker:
    """Context manager to track file opens during Flask route crawling."""
    
    def __init__(self):
        self.opened_files: Set[str] = set()
        self.original_open = None
    
    def __enter__(self):
        self.original_open = builtins.open
        
        def tracking_open(file, mode='r', *args, **kwargs):
            try:
                # Convert to absolute path and track
                abs_path = os.path.abspath(str(file))
                self.opened_files.add(abs_path)
            except (OSError, TypeError):
                pass  # Ignore invalid paths
            return self.original_open(file, mode, *args, **kwargs)
        
        builtins.open = tracking_open
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.original_open:
            builtins.open = self.original_open


class JinjaTemplateTracker:
    """Wrapper for Jinja template loader to track template usage."""
    
    def __init__(self, original_loader):
        self.original_loader = original_loader
        self.templates_used: Set[str] = set()
    
    def get_source(self, environment, template):
        """Track template usage and delegate to original loader."""
        self.templates_used.add(template)
        return self.original_loader.get_source(environment, template)
    
    def __getattr__(self, name):
        """Delegate all other attributes to original loader."""
        return getattr(self.original_loader, name)


class FlaskAppLoader:
    """Safely load Flask app in testing mode without starting server."""
    
    @staticmethod
    def load_app(repo_root: Path) -> Optional[Any]:
        """Try multiple patterns to load Flask app."""
        sys.path.insert(0, str(repo_root))
        
        patterns = [
            ("from app import app as flask_app", "app"),
            ("from wsgi import app as flask_app", "app"),
            ("from app import create_app; flask_app = create_app(testing=True)", "create_app"),
            ("from main import app as flask_app", "app"),
        ]
        
        for import_code, pattern_type in patterns:
            try:
                local_vars = {}
                exec(import_code, {}, local_vars)
                flask_app = local_vars['flask_app']
                
                # Configure for testing
                flask_app.config.update(TESTING=True)
                print(f"✓ Loaded Flask app via {pattern_type} pattern")
                return flask_app
                
            except Exception as e:
                print(f"  Failed {pattern_type} pattern: {e}")
                continue
        
        print("⚠ WARNING: Could not load Flask app - skipping route-aware scan")
        return None


class StaticAnalyzer:
    """Static code analysis for upload/document directories."""
    
    @staticmethod
    def find_upload_dirs(repo_root: Path) -> Set[str]:
        """Find upload/document directories via static analysis."""
        upload_dirs = set()
        
        # Common directory patterns
        common_dirs = [
            "uploads", "documents", "media", "user_data", 
            "export", "reports", "files", "attachments"
        ]
        
        for dir_name in common_dirs:
            dir_path = repo_root / dir_name
            if dir_path.exists() and dir_path.is_dir():
                upload_dirs.add(str(dir_path))
        
        # AST analysis for config keys and file operations
        python_files = list(repo_root.rglob("*.py"))
        
        for py_file in python_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                tree = ast.parse(content)
                visitor = UploadDirVisitor(repo_root)
                visitor.visit(tree)
                upload_dirs.update(visitor.upload_dirs)
                
            except Exception as e:
                print(f"  AST analysis failed for {py_file}: {e}")
                continue
        
        return upload_dirs


class UploadDirVisitor(ast.NodeVisitor):
    """AST visitor to find upload/document directory patterns."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.upload_dirs: Set[str] = set()
        
        # Config keys that might contain directory paths
        self.config_keys = {
            'UPLOAD_FOLDER', 'DOCUMENTS_FOLDER', 'MEDIA_ROOT', 
            'EXPORT_DIR', 'REPORTS_DIR', 'FILES_DIR', 'ATTACHMENTS_DIR'
        }
    
    def visit_Subscript(self, node):
        """Check for config[key] patterns."""
        try:
            if (isinstance(node.value, ast.Attribute) and 
                node.value.attr == 'config' and
                isinstance(node.slice, ast.Constant) and
                node.slice.value in self.config_keys):
                
                # This is a config key access - we'd need runtime info
                # For now, just note the pattern exists
                pass
                
        except Exception:
            pass
        
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Check for file operation patterns."""
        try:
            # Look for send_file, send_from_directory calls
            if isinstance(node.func, ast.Name):
                if node.func.id in ['send_file', 'send_from_directory']:
                    # Extract directory arguments if possible
                    for arg in node.args:
                        if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                            dir_path = self.repo_root / arg.value
                            if dir_path.exists() and dir_path.is_dir():
                                self.upload_dirs.add(str(dir_path))
            
            # Look for os.path.join patterns
            if (isinstance(node.func, ast.Attribute) and 
                isinstance(node.func.value, ast.Attribute) and
                node.func.value.attr == 'path' and
                node.func.attr == 'join'):
                
                # Extract first argument as potential directory
                if node.args and isinstance(node.args[0], ast.Constant):
                    dir_path = self.repo_root / node.args[0].value
                    if dir_path.exists() and dir_path.is_dir():
                        self.upload_dirs.add(str(dir_path))
                        
        except Exception:
            pass
        
        self.generic_visit(node)


class RouteCrawler:
    """Crawl Flask routes to discover in-use assets."""
    
    def __init__(self, flask_app, repo_root: Path):
        self.flask_app = flask_app
        self.repo_root = repo_root
        self.template_tracker = None
        
    def setup_template_tracking(self):
        """Setup Jinja template usage tracking."""
        if hasattr(self.flask_app, 'jinja_loader') and self.flask_app.jinja_loader:
            self.template_tracker = JinjaTemplateTracker(self.flask_app.jinja_loader)
            self.flask_app.jinja_loader = self.template_tracker
    
    def get_safe_routes(self, include_pattern: str = None, 
                       exclude_pattern: str = r"^/(admin|debug|internal)") -> List[str]:
        """Get GET routes with no required parameters."""
        safe_routes = []
        
        include_regex = re.compile(include_pattern) if include_pattern else None
        exclude_regex = re.compile(exclude_pattern) if exclude_pattern else None
        
        for rule in self.flask_app.url_map.iter_rules():
            # Only GET routes with no arguments
            if "GET" not in rule.methods or len(rule.arguments) > 0:
                continue
            
            route_path = rule.rule
            
            # Apply include/exclude filters
            if exclude_regex and exclude_regex.match(route_path):
                continue
            if include_regex and not include_regex.match(route_path):
                continue
            
            safe_routes.append(route_path)
        
        return safe_routes
    
    def crawl_routes(self, routes: List[str], follow_redirects: bool = False) -> ScanResults:
        """Crawl routes and collect in-use assets."""
        results = ScanResults()
        
        self.setup_template_tracking()
        
        with self.flask_app.test_client() as client:
            with FileOpenTracker() as file_tracker:
                
                for route in routes:
                    try:
                        response = client.get(route, follow_redirects=follow_redirects)
                        print(f"  GET {route} -> {response.status_code}")
                        results.routes_scanned += 1
                        
                    except Exception as e:
                        print(f"  GET {route} -> ERROR: {e}")
                        continue
                
                # Collect tracked files
                results.opened_files = file_tracker.opened_files.copy()
        
        # Collect tracked templates
        if self.template_tracker:
            results.templates_found = self.template_tracker.templates_used.copy()
        
        # Resolve static files from HTML (basic implementation)
        results.static_files_found = self._find_static_references()
        
        return results
    
    def _find_static_references(self) -> Set[str]:
        """Find static file references (basic implementation)."""
        static_files = set()
        
        # This is a simplified implementation
        # In a full implementation, you'd parse HTML responses for static references
        static_folder = getattr(self.flask_app, 'static_folder', 'static')
        if static_folder and os.path.exists(static_folder):
            for root, dirs, files in os.walk(static_folder):
                for file in files:
                    static_files.add(os.path.join(root, file))
        
        return static_files
    
    def simulate_post_routes(self, post_allow_pattern: str) -> ScanResults:
        """Safely simulate POST routes with dummy data."""
        results = ScanResults()
        
        if not post_allow_pattern:
            return results
        
        allow_regex = re.compile(post_allow_pattern)
        
        post_routes = []
        for rule in self.flask_app.url_map.iter_rules():
            if ("POST" in rule.methods and len(rule.arguments) == 0 and
                allow_regex.match(rule.rule)):
                post_routes.append(rule.rule)
        
        with self.flask_app.test_client() as client:
            with FileOpenTracker() as file_tracker:
                
                for route in post_routes:
                    try:
                        # Send dummy multipart data
                        data = {'file': (None, 'dummy.txt')}
                        response = client.post(route, data=data, 
                                             content_type='multipart/form-data',
                                             follow_redirects=False)
                        print(f"  POST {route} (sim) -> {response.status_code}")
                        results.post_routes_simulated += 1
                        
                    except Exception as e:
                        print(f"  POST {route} (sim) -> ERROR: {e}")
                        continue
                
                results.upload_dirs_dynamic = file_tracker.opened_files.copy()
        
        return results


class SafeCleanup:
    """Main cleanup orchestrator with safety checks."""
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.scan_results = ScanResults()
        
        # Critical paths to always protect
        self.critical_paths = {
            'app.py', 'wsgi.py', 'main.py', 'config.py', 'requirements.txt',
            'templates/', 'static/', 'db/', 'migrations/', 'scripts/', 'tools/',
            '.vscode/', '.github/', '.devcontainer/', 'azure/', 'infra/',
            'notebooks/', 'data/', 'instance/', 'docs/', '.env', '.env.*',
            'deployment/', 'docker-compose.yml', 'Dockerfile', 'azure-pipelines.yml'
        }
        
        # Junk patterns that are safe to delete
        self.junk_patterns = {
            r'__pycache__/.*',
            r'\.pyc$',
            r'\.pyo$',
            r'\.pyd$',
            r'\.so$',
            r'\.egg-info/.*',
            r'\.pytest_cache/.*',
            r'\.coverage$',
            r'htmlcov/.*',
            r'\.tox/.*',
            r'build/.*',
            r'dist/.*',
            r'\.DS_Store$',
            r'Thumbs\.db$',
            r'desktop\.ini$',
            r'\.vscode/.*\.log$',
            r'npm-debug\.log.*',
            r'yarn-error\.log$',
            r'node_modules/.*',
            r'\.tmp/.*',
            r'temp/.*',
            r'\.log$',
            r'\.log\.\d+$',
        }
    
    def get_git_status(self) -> Tuple[Set[str], Set[str], Set[str]]:
        """Get Git file status."""
        try:
            # Tracked files
            tracked = set()
            result = subprocess.run(['git', 'ls-files'], 
                                  cwd=self.repo_root, capture_output=True, text=True)
            if result.returncode == 0:
                tracked = set(result.stdout.strip().split('\n'))
            
            # Ignored files
            ignored = set()
            result = subprocess.run(['git', 'ls-files', '--others', '-i', '--exclude-standard'], 
                                  cwd=self.repo_root, capture_output=True, text=True)
            if result.returncode == 0:
                ignored = set(result.stdout.strip().split('\n'))
            
            # Untracked files
            untracked = set()
            result = subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], 
                                  cwd=self.repo_root, capture_output=True, text=True)
            if result.returncode == 0:
                untracked = set(result.stdout.strip().split('\n'))
            
            return tracked, ignored, untracked
            
        except Exception as e:
            print(f"WARNING: Git status check failed: {e}")
            return set(), set(), set()
    
    def collect_deletion_candidates(self, age_days: int = 30,
                                  include_patterns: List[str] = None,
                                  exclude_patterns: List[str] = None) -> Dict[str, List[str]]:
        """Collect files that are candidates for deletion."""
        tracked, ignored, untracked = self.get_git_status()
        
        # Start with Git ignored and untracked files
        candidates = ignored.union(untracked)
        candidates = {f for f in candidates if f}  # Remove empty strings
        
        # Apply junk patterns
        junk_candidates = set()
        for candidate in candidates:
            candidate_path = self.repo_root / candidate
            if not candidate_path.exists():
                continue
                
            for pattern in self.junk_patterns:
                if re.search(pattern, candidate):
                    junk_candidates.add(candidate)
                    break
        
        # Age filtering
        cutoff_time = datetime.now() - timedelta(days=age_days)
        aged_candidates = set()
        
        for candidate in junk_candidates:
            candidate_path = self.repo_root / candidate
            try:
                if candidate_path.stat().st_mtime < cutoff_time.timestamp():
                    aged_candidates.add(candidate)
            except OSError:
                continue
        
        # Apply additional include/exclude patterns
        if include_patterns:
            include_regexes = [re.compile(p) for p in include_patterns]
            aged_candidates = {f for f in aged_candidates 
                             if any(regex.search(f) for regex in include_regexes)}
        
        if exclude_patterns:
            exclude_regexes = [re.compile(p) for p in exclude_patterns]
            aged_candidates = {f for f in aged_candidates 
                             if not any(regex.search(f) for regex in exclude_regexes)}
        
        # Categorize results
        results = {
            'tracked': list(tracked),
            'in_use_routes': [],
            'in_use_uploads': [],
            'critical_paths': [],
            'candidates': list(aged_candidates),
            'large_files': []
        }
        
        # Remove in-use files from candidates
        in_use_files = self._get_in_use_files()
        results['candidates'] = [f for f in results['candidates'] if f not in in_use_files]
        results['in_use_routes'] = list(in_use_files)
        
        # Remove critical paths
        critical_files = self._get_critical_files()
        results['candidates'] = [f for f in results['candidates'] if f not in critical_files]
        results['critical_paths'] = list(critical_files)
        
        # Mark large files
        large_files = []
        final_candidates = []
        for candidate in results['candidates']:
            candidate_path = self.repo_root / candidate
            try:
                if candidate_path.stat().st_size > 100 * 1024 * 1024:  # 100MB
                    large_files.append(candidate)
                else:
                    final_candidates.append(candidate)
            except OSError:
                final_candidates.append(candidate)
        
        results['candidates'] = final_candidates
        results['large_files'] = large_files
        
        return results
    
    def _get_in_use_files(self) -> Set[str]:
        """Get files that are in-use based on scan results."""
        in_use = set()
        
        # Templates
        for template in self.scan_results.templates_found:
            template_path = self.repo_root / 'templates' / template
            if template_path.exists():
                in_use.add(str(template_path.relative_to(self.repo_root)))
        
        # Static files
        for static_file in self.scan_results.static_files_found:
            try:
                rel_path = Path(static_file).relative_to(self.repo_root)
                in_use.add(str(rel_path))
            except ValueError:
                pass
        
        # Opened files
        for opened_file in self.scan_results.opened_files:
            try:
                rel_path = Path(opened_file).relative_to(self.repo_root)
                in_use.add(str(rel_path))
            except ValueError:
                pass
        
        # Upload directories
        upload_dirs = self.scan_results.upload_dirs_static.union(
            self.scan_results.upload_dirs_dynamic)
        
        for upload_dir in upload_dirs:
            try:
                rel_path = Path(upload_dir).relative_to(self.repo_root)
                # Mark entire directory as in-use
                for root, dirs, files in os.walk(upload_dir):
                    for file in files:
                        file_path = Path(root) / file
                        try:
                            rel_file_path = file_path.relative_to(self.repo_root)
                            in_use.add(str(rel_file_path))
                        except ValueError:
                            pass
            except ValueError:
                pass
        
        return in_use
    
    def _get_critical_files(self) -> Set[str]:
        """Get critical files that should never be deleted."""
        critical = set()
        
        for pattern in self.critical_paths:
            if pattern.endswith('/'):
                # Directory pattern
                dir_path = self.repo_root / pattern.rstrip('/')
                if dir_path.exists() and dir_path.is_dir():
                    for root, dirs, files in os.walk(dir_path):
                        for file in files:
                            file_path = Path(root) / file
                            try:
                                rel_path = file_path.relative_to(self.repo_root)
                                critical.add(str(rel_path))
                            except ValueError:
                                pass
            else:
                # File pattern
                if '*' in pattern:
                    # Glob pattern
                    for match in self.repo_root.glob(pattern):
                        try:
                            rel_path = match.relative_to(self.repo_root)
                            critical.add(str(rel_path))
                        except ValueError:
                            pass
                else:
                    # Direct file
                    file_path = self.repo_root / pattern
                    if file_path.exists():
                        critical.add(pattern)
        
        return critical
    
    def create_backup(self, files: List[str]) -> str:
        """Create backup zip of files to be deleted."""
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        backup_dir = self.repo_root / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f'cleanup-{timestamp}.zip'
        
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in files:
                file_path = self.repo_root / file
                if file_path.exists() and file_path.stat().st_size <= 100 * 1024 * 1024:
                    zipf.write(file_path, file)
        
        return str(backup_path)
    
    def generate_report(self, analysis: Dict[str, List[str]], 
                       output_file: str = None) -> str:
        """Generate detailed cleanup report."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if not output_file:
            report_timestamp = datetime.now().strftime("%Y%m%d-%H%M")
            output_file = f'cleanup-report-{report_timestamp}.txt'
        
        report_lines = [
            f"Flask Repository Cleanup Report",
            f"Generated: {timestamp}",
            f"Repository: {self.repo_root}",
            "=" * 80,
            "",
            f"Route Scanning Results:",
            f"  Routes scanned: {self.scan_results.routes_scanned}",
            f"  Templates found: {len(self.scan_results.templates_found)}",
            f"  Static files found: {len(self.scan_results.static_files_found)}",
            f"  Files opened: {len(self.scan_results.opened_files)}",
            f"  Upload dirs (static): {len(self.scan_results.upload_dirs_static)}",
            f"  Upload dirs (dynamic): {len(self.scan_results.upload_dirs_dynamic)}",
            f"  POST routes simulated: {self.scan_results.post_routes_simulated}",
            "",
        ]
        
        for category, files in analysis.items():
            if not files:
                continue
                
            category_title = category.replace('_', ' ').title()
            report_lines.extend([
                f"{category_title} ({len(files)} files):",
                "-" * 40,
            ])
            
            for file in sorted(files)[:50]:  # Limit to first 50
                report_lines.append(f"  {file}")
            
            if len(files) > 50:
                report_lines.append(f"  ... and {len(files) - 50} more files")
            
            report_lines.append("")
        
        report_content = '\n'.join(report_lines)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return output_file


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Safe Flask repository cleanup with route-aware detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tools/safe_clean.py                          # Dry-run only
  python tools/safe_clean.py --route-scan             # Include route analysis  
  python tools/safe_clean.py --route-scan --apply     # Apply with route analysis
  python tools/safe_clean.py --simulate-post --post-allow "^/test-upload$" --apply
        """
    )
    
    # Main operation flags
    parser.add_argument('--apply', action='store_true',
                       help='Apply deletions (default: dry-run only)')
    parser.add_argument('--age-days', type=int, default=30,
                       help='Only delete files older than N days (default: 30)')
    
    # Route scanning flags
    parser.add_argument('--route-scan', action='store_true',
                       help='Enable Flask route scanning for in-use detection')
    parser.add_argument('--follow-redirects', action='store_true',
                       help='Follow redirects during route crawling')
    parser.add_argument('--include-routes', type=str,
                       help='Regex pattern for routes to include')
    parser.add_argument('--exclude-routes', type=str, 
                       default=r"^/(admin|debug|internal)",
                       help='Regex pattern for routes to exclude')
    
    # POST simulation flags  
    parser.add_argument('--simulate-post', action='store_true',
                       help='Enable safe POST route simulation')
    parser.add_argument('--post-allow', type=str,
                       help='Regex pattern for POST routes allowed for simulation')
    
    # Pruning flags
    parser.add_argument('--prune-uploads', choices=['none', 'artifacts', 'all'],
                       default='none', help='Upload directory pruning mode')
    parser.add_argument('--prune-tests', choices=['none', 'artifacts', 'orphaned', 'all'],
                       default='none', help='Test directory pruning mode')
    
    # Pattern flags
    parser.add_argument('--include-pattern', action='append',
                       help='Additional patterns to include for deletion')
    parser.add_argument('--exclude-pattern', action='append',
                       help='Additional patterns to exclude from deletion')
    
    # Output flags
    parser.add_argument('--report', type=str,
                       help='Custom report filename')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Find repository root
    repo_root = Path.cwd()
    while repo_root != repo_root.parent:
        if (repo_root / '.git').exists():
            break
        repo_root = repo_root.parent
    else:
        print("ERROR: Not in a Git repository")
        sys.exit(3)
    
    print(f"Flask Repository Cleanup Tool")
    print(f"Repository: {repo_root}")
    print(f"Mode: {'APPLY' if args.apply else 'DRY-RUN'}")
    print()
    
    # Check for staged changes
    try:
        result = subprocess.run(['git', 'diff', '--cached', '--quiet'], 
                              cwd=repo_root, capture_output=True)
        if result.returncode != 0:
            print("WARNING: You have staged changes. Commit or stash them first.")
            if args.apply:
                sys.exit(2)
    except Exception:
        pass
    
    cleanup = SafeCleanup(repo_root)
    
    # Route scanning
    if args.route_scan:
        print("Loading Flask app...")
        flask_app = FlaskAppLoader.load_app(repo_root)
        
        if flask_app:
            crawler = RouteCrawler(flask_app, repo_root)
            
            # Static analysis for upload directories
            print("Performing static analysis...")
            upload_dirs = StaticAnalyzer.find_upload_dirs(repo_root)
            cleanup.scan_results.upload_dirs_static = upload_dirs
            print(f"  Found {len(upload_dirs)} upload/document directories")
            
            # GET route crawling
            print("Crawling GET routes...")
            safe_routes = crawler.get_safe_routes(
                args.include_routes, args.exclude_routes)
            print(f"  Found {len(safe_routes)} safe GET routes")
            
            if safe_routes:
                route_results = crawler.crawl_routes(safe_routes, args.follow_redirects)
                cleanup.scan_results.routes_scanned = route_results.routes_scanned
                cleanup.scan_results.templates_found = route_results.templates_found
                cleanup.scan_results.static_files_found = route_results.static_files_found
                cleanup.scan_results.opened_files = route_results.opened_files
            
            # POST simulation
            if args.simulate_post and args.post_allow:
                print("Simulating POST routes...")
                post_results = crawler.simulate_post_routes(args.post_allow)
                cleanup.scan_results.post_routes_simulated = post_results.post_routes_simulated
                cleanup.scan_results.upload_dirs_dynamic.update(post_results.upload_dirs_dynamic)
    
    # Collect deletion candidates
    print("Analyzing repository...")
    analysis = cleanup.collect_deletion_candidates(
        args.age_days, args.include_pattern, args.exclude_pattern)
    
    # Generate report
    report_file = cleanup.generate_report(analysis, args.report)
    print(f"Report written to: {report_file}")
    
    # Summary
    print(f"\nSummary:")
    for category, files in analysis.items():
        category_name = category.replace('_', ' ').title()
        print(f"  {category_name}: {len(files)} files")
    
    # Apply deletions if requested
    if args.apply:
        candidates = analysis['candidates']
        if not candidates:
            print("\nNo files to delete.")
            sys.exit(0)
        
        print(f"\nThis will delete {len(candidates)} files.")
        confirmation = input("Type DELETE to proceed: ")
        if confirmation != "DELETE":
            print("Aborted.")
            sys.exit(0)
        
        # Handle special pruning modes
        if args.prune_uploads == 'all':
            upload_confirmation = input("Type DELETE UPLOADS to proceed with upload deletion: ")
            if upload_confirmation != "DELETE UPLOADS":
                print("Upload deletion aborted.")
                sys.exit(0)
        
        if args.prune_tests == 'all':
            test_confirmation = input("Type DELETE TESTS to proceed with test deletion: ")
            if test_confirmation != "DELETE TESTS":
                print("Test deletion aborted.")
                sys.exit(0)
        
        # Create backup
        print("Creating backup...")
        backup_path = cleanup.create_backup(candidates)
        print(f"Backup created: {backup_path}")
        
        # Delete files
        print("Deleting files...")
        deleted_count = 0
        for file in candidates:
            file_path = repo_root / file
            try:
                if file_path.exists():
                    if file_path.is_dir():
                        shutil.rmtree(file_path)
                    else:
                        file_path.unlink()
                    deleted_count += 1
                    if args.verbose:
                        print(f"  Deleted: {file}")
            except Exception as e:
                print(f"  Failed to delete {file}: {e}")
        
        print(f"\nDeleted {deleted_count} files.")
        print(f"Backup available at: {backup_path}")
    
    sys.exit(0)


if __name__ == '__main__':
    main()
