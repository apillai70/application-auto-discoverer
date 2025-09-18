#!/usr/bin/env python3
"""
Generate updated CSV file with ideal archetypes from YAML template
"""

import pandas as pd
import numpy as np
import random
from pathlib import Path

def map_to_ideal_archetype(row):
    """
    Map original archetypes to ideal ones based on patterns
    """
    archetype = row['archetype']
    protocol = row['protocol']
    info = str(row['info'])
    behavior = row['behavior']
    
    # Mapping logic based on observed patterns
    if archetype == '3-Tier':
        if protocol == 'SQL' or 'SQL' in info:
            return 'Database-Centric'
        elif behavior == 'API' or 'API' in info:
            return 'API-Centric (General)'
        elif 'Web' in info and 'DB' in info:
            return 'N-Tier Architecture'
        else:
            return '3-Tier'
    
    elif archetype == 'Web + API Headless':
        if behavior == 'API' or 'API' in info:
            return 'API-Centric (General)'
        else:
            return 'Web + API Headless'
    
    elif archetype == 'Monolithic':
        if protocol == 'TCP' and ('3306' in info or 'SQL' in info):
            return 'Database-Centric'
        else:
            return 'Monolithic'
    
    elif archetype == 'Client-Server':
        if 'RDP' in info or '3389' in info:
            return 'Host-Terminal'
        else:
            return 'Client-Server'
    
    elif archetype == 'SOA':
        # 30% chance to map to message broker variant
        if random.random() < 0.3:
            return 'SOA with Message Broker'
        else:
            return 'SOA'
    
    elif archetype == 'Microservices':
        if protocol == 'gRPC' or 'gRPC' in info:
            return 'Cloud-Native'
        else:
            return 'Microservices'
    
    elif archetype == 'Event-Driven':
        if protocol == 'AMQP' or '5672' in info:
            return 'SOA with Message Broker'
        else:
            return 'Event-Driven'
    
    elif archetype == 'Edge+Cloud Hybrid':
        return 'Edge+Cloud Hybrid'
    
    elif archetype == 'ETL/Data Pipeline':
        return 'ETL/Data Pipeline'
    
    elif archetype == 'Serverless':
        return 'Serverless'
    
    else:
        return archetype  # Fallback to original

def main():
    """
    Main function to process the CSV file
    """
    # File paths
    input_file = 'normalized_synthetic_traffic.csv'
    output_file = 'updated_normalized_synthetic_traffic.csv'
    
    print("🔄 Starting CSV file processing...")
    
    # Check if input file exists
    if not Path(input_file).exists():
        print(f"❌ Error: {input_file} not found!")
        print("Make sure the normalized_synthetic_traffic.csv file is in the current directory.")
        return
    
    try:
        # Read the CSV file
        print(f"📖 Reading {input_file}...")
        df = pd.read_csv(input_file)
        print(f"✅ Loaded {len(df):,} rows")
        
        # Show original archetype distribution
        print("\n📊 Original Archetype Distribution:")
        original_counts = df['archetype'].value_counts()
        for archetype, count in original_counts.items():
            percentage = (count / len(df)) * 100
            print(f"  {archetype}: {count:,} rows ({percentage:.1f}%)")
        
        # Apply archetype mapping
        print("\n🔄 Applying archetype mappings...")
        df['archetype'] = df.apply(map_to_ideal_archetype, axis=1)
        
        # Show new archetype distribution
        print("\n📈 New Archetype Distribution:")
        new_counts = df['archetype'].value_counts()
        for archetype, count in new_counts.head(15).items():
            percentage = (count / len(df)) * 100
            print(f"  {archetype}: {count:,} rows ({percentage:.1f}%)")
        
        # Save the updated file
        print(f"\n💾 Saving to {output_file}...")
        df.to_csv(output_file, index=False)
        
        # File stats
        file_size = Path(output_file).stat().st_size / (1024 * 1024)  # MB
        print(f"✅ File saved successfully!")
        print(f"📁 Output file: {output_file}")
        print(f"📊 Total rows: {len(df):,}")
        print(f"📋 Total columns: {len(df.columns)}")
        print(f"💽 File size: {file_size:.2f} MB")
        
        # Show unique archetypes
        unique_archetypes = df['archetype'].nunique()
        print(f"🎯 Unique archetypes: {unique_archetypes}")
        
        # Show sample of updated data
        print("\n📄 Sample of updated data:")
        sample_data = df[['application', 'archetype', 'protocol', 'behavior']].head(5)
        for idx, row in sample_data.iterrows():
            print(f"  {idx+1}. {row['application']} | {row['archetype']} | {row['protocol']}")
        
        print("\n🎉 Processing completed successfully!")
        print(f"✅ Updated CSV file with ideal archetypes saved as: {output_file}")
        
    except Exception as e:
        print(f"❌ Error processing file: {e}")
        return

if __name__ == "__main__":
    # Set random seed for reproducible results
    random.seed(42)
    np.random.seed(42)
    
    main()