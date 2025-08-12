#!/usr/bin/env python3
"""
Execute Azure SQL Fix using REST API
This script uses Azure REST API to execute SQL commands
"""

import os
import json
import subprocess
import requests
import sys

def get_access_token():
    """Get Azure access token using Azure CLI"""
    try:
        result = subprocess.run([
            'az', 'account', 'get-access-token', 
            '--resource', 'https://database.windows.net/', 
            '--query', 'accessToken', 
            '--output', 'tsv'
        ], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to get access token: {e}")
        return None

def execute_sql_via_api():
    """Execute SQL using Azure REST API"""
    
    # Configuration
    subscription_id = "005abb87-af15-4e7d-8bd4-e7a43d7cdb8c"  # From az account show
    resource_group = "DefaultResourceGroup-CUS"
    server_name = "ai-learning-sql-centralus"
    database_name = "ai-learning-db"
    
    # Get access token
    print("🔄 Getting Azure access token...")
    token = get_access_token()
    if not token:
        return False
    
    print("✅ Access token obtained")
    
    # SQL to execute
    sql_commands = [
        """CREATE OR ALTER VIEW dbo.courses_app AS 
           SELECT id, title, description, 
                  COALESCE(difficulty, level) AS difficulty,
                  TRY_CONVERT(float, duration) AS duration_hours,
                  url,
                  CAST(NULL AS nvarchar(100)) AS category,
                  level,
                  created_at
           FROM dbo.courses""",
        "SELECT COUNT(*) as course_count FROM dbo.courses_app",
        "SELECT TOP 3 id, title, difficulty FROM dbo.courses_app ORDER BY created_at DESC"
    ]
    
    # REST API endpoint for executing queries
    url = f"https://management.azure.com/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.Sql/servers/{server_name}/databases/{database_name}/query"
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    for i, sql in enumerate(sql_commands, 1):
        print(f"\n🔄 Executing SQL command {i}/{len(sql_commands)}...")
        print(f"SQL: {sql[:60]}...")
        
        data = {
            'query': sql
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Command executed successfully")
                if 'results' in result:
                    print(f"📋 Results: {result['results']}")
            else:
                print(f"❌ Command failed: {response.status_code}")
                print(f"Response: {response.text}")
                
        except requests.RequestException as e:
            print(f"❌ Request error: {e}")
    
    print("\n🎉 Azure SQL fix attempts completed!")
    return True

if __name__ == "__main__":
    print("=== Azure SQL Fix using REST API ===")
    success = execute_sql_via_api()
    sys.exit(0 if success else 1)
