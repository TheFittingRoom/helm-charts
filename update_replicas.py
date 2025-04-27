#!/usr/bin/env python3
"""
Script to update replica counts in Helm chart values.yaml files.
Used by the GitHub Action triggered by tfr_env_manager.
"""

import json
import os
import re
import sys
import glob
from pathlib import Path


def update_replica_counts(payload_str=None):
    """Update replica counts in values.yaml files based on the provided payload."""
    # Get payload from environment variable or argument
    if payload_str:
        payload = json.loads(payload_str)
    else:
        payload_env = os.environ.get('PAYLOAD')
        if not payload_env:
            print("Error: No payload provided")
            return False
        payload = json.loads(payload_env)

    # Extract payload data
    chart_updates = payload.get('charts', {})
    env = payload.get('environment', 'unknown')
    action = payload.get('action', 'unknown')
    triggered_by = payload.get('triggered_by', 'unknown')
    
    print(f"Updating charts for {env} environment ({action})")
    print(f"Triggered by: {triggered_by}")
    
    # Keep track of changes
    changed_files = []
    
    # Update each chart
    for chart_name, replicas in chart_updates.items():
        # First check exact chart name match
        values_file = f"charts/{chart_name}/values.yaml"
        
        # If direct match not found, try to find it by listing directories
        if not os.path.exists(values_file):
            # List all chart directories
            chart_dirs = glob.glob("charts/*/")
            chart_matches = [d for d in chart_dirs if os.path.basename(os.path.dirname(d)).lower() == chart_name.lower()]
            
            if chart_matches:
                values_file = os.path.join(chart_matches[0], "values.yaml")
            else:
                print(f"⚠️ Chart values file not found for: {chart_name}")
                print(f"Available charts: {[os.path.basename(os.path.dirname(d)) for d in chart_dirs]}")
                continue
        
        print(f"🔄 Updating {chart_name} to {replicas} replicas")
        
        # Read current values.yaml
        with open(values_file, 'r') as f:
            content = f.read()
        
        # Parse current replica count
        current_replicas_match = re.search(r'replicaCount:\s*(\d+)', content)
        current_replicas = int(current_replicas_match.group(1)) if current_replicas_match else 0
        
        if current_replicas == replicas:
            print(f"   No change needed for {chart_name}")
            continue
        
        # Update replica count
        new_content = re.sub(
            r'replicaCount:\s*\d+', 
            f'replicaCount: {replicas}', 
            content
        )
        
        # Write updated content back
        with open(values_file, 'w') as f:
            f.write(new_content)
        
        changed_files.append(values_file)
        print(f"✅ Updated {chart_name} from {current_replicas} to {replicas} replicas")
    
    # Set output for GitHub Actions if running in a workflow
    if 'GITHUB_OUTPUT' in os.environ and changed_files:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"changed=true\n")
            f.write(f"files={' '.join(changed_files)}\n")
    elif 'GITHUB_OUTPUT' in os.environ:
        with open(os.environ['GITHUB_OUTPUT'], 'a') as f:
            f.write(f"changed=false\n")

    return bool(changed_files)


if __name__ == "__main__":
    # If called with a payload argument, use that
    if len(sys.argv) > 1:
        update_replica_counts(sys.argv[1])
    else:
        # Otherwise use environment variable
        update_replica_counts()
