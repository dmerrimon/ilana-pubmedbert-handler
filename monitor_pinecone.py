"""
Real-time Pinecone Upload Monitor
Tracks upload progress, success rates, and index statistics
"""

import os
import time
import json
from pathlib import Path
from pinecone import Pinecone
from datetime import datetime
import threading

# Load environment variables
keys_file = Path('/Users/donmerriman/Ilana Labs/ilana-core/Keys Open Doors.txt')
if keys_file.exists():
    with open(keys_file, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

class PineconeMonitor:
    def __init__(self, index_name="protocol-intelligence-768"):
        self.pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        self.index = self.pc.Index(index_name)
        self.index_name = index_name
        self.monitoring = False
        self.start_time = None
        self.initial_count = None
        
    def get_index_stats(self):
        """Get current index statistics"""
        try:
            stats = self.index.describe_index_stats()
            return {
                'total_vectors': stats.total_vector_count,
                'dimension': stats.dimension,
                'index_fullness': stats.index_fullness,
                'namespaces': dict(stats.namespaces) if hasattr(stats, 'namespaces') else {}
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_vector_counts_by_type(self):
        """Get vector counts by type (protocol vs regulatory)"""
        try:
            # Query for different types
            types = {
                'protocols': {'type': 'protocol'},
                'regulatory': {'type': 'regulatory_guidance'},
                'feedback': {'type': 'user_feedback'}
            }
            
            counts = {}
            for type_name, filter_query in types.items():
                try:
                    results = self.index.query(
                        vector=[0.0] * 768,
                        top_k=1,
                        include_metadata=True,
                        filter=filter_query
                    )
                    # This is approximate - for exact counts we'd need to paginate
                    counts[type_name] = "~" + str(len(results.matches)) if results.matches else "0"
                except:
                    counts[type_name] = "unknown"
            
            return counts
        except Exception as e:
            return {'error': str(e)}
    
    def monitor_uploads(self, refresh_interval=5):
        """Start monitoring uploads in real-time"""
        print("🔍 STARTING PINECONE UPLOAD MONITOR")
        print("=" * 60)
        
        self.monitoring = True
        self.start_time = datetime.now()
        
        # Get initial stats
        initial_stats = self.get_index_stats()
        self.initial_count = initial_stats.get('total_vectors', 0)
        
        print(f"📊 Initial Index Stats:")
        print(f"   Index: {self.index_name}")
        print(f"   Total Vectors: {self.initial_count:,}")
        print(f"   Dimension: {initial_stats.get('dimension', 'unknown')}")
        print(f"   Index Fullness: {initial_stats.get('index_fullness', 0):.1%}")
        print(f"   Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Monitor loop
        last_count = self.initial_count
        while self.monitoring:
            try:
                current_stats = self.get_index_stats()
                current_count = current_stats.get('total_vectors', 0)
                
                # Calculate progress
                vectors_added = current_count - self.initial_count
                vectors_this_cycle = current_count - last_count
                elapsed_time = datetime.now() - self.start_time
                
                # Calculate rate
                if elapsed_time.total_seconds() > 0:
                    rate_per_minute = (vectors_added / elapsed_time.total_seconds()) * 60
                else:
                    rate_per_minute = 0
                
                # Clear screen and display stats
                os.system('clear' if os.name == 'posix' else 'cls')
                
                print("🔍 PINECONE UPLOAD MONITOR - LIVE")
                print("=" * 60)
                print(f"📊 Index: {self.index_name}")
                print(f"🕐 Monitoring Time: {elapsed_time}")
                print(f"📈 Current Vectors: {current_count:,}")
                print(f"➕ Vectors Added: {vectors_added:,}")
                print(f"🔄 This Cycle: +{vectors_this_cycle}")
                print(f"⚡ Upload Rate: {rate_per_minute:.1f} vectors/minute")
                print(f"📊 Index Fullness: {current_stats.get('index_fullness', 0):.1%}")
                print()
                
                # Show vector breakdown by type
                type_counts = self.get_vector_counts_by_type()
                if 'error' not in type_counts:
                    print("📋 Vector Breakdown:")
                    for vector_type, count in type_counts.items():
                        print(f"   {vector_type.title()}: {count}")
                    print()
                
                # Show recent activity
                if vectors_this_cycle > 0:
                    print(f"🟢 UPLOAD ACTIVE: +{vectors_this_cycle} vectors in last {refresh_interval}s")
                elif vectors_added > 0:
                    print(f"🟡 UPLOAD PAUSED: No new vectors in last {refresh_interval}s")
                else:
                    print(f"⚪ NO UPLOAD ACTIVITY: Monitoring for changes...")
                
                print()
                print("Press Ctrl+C to stop monitoring")
                print("=" * 60)
                
                last_count = current_count
                time.sleep(refresh_interval)
                
            except KeyboardInterrupt:
                print("\n\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Monitoring error: {e}")
                time.sleep(refresh_interval)
        
        self.monitoring = False
    
    def get_upload_summary(self):
        """Get a summary of the upload session"""
        if not self.start_time or not self.initial_count:
            return "No monitoring session data available"
        
        final_stats = self.get_index_stats()
        final_count = final_stats.get('total_vectors', 0)
        vectors_added = final_count - self.initial_count
        elapsed_time = datetime.now() - self.start_time
        
        summary = f"""
📊 UPLOAD SESSION SUMMARY
========================
Start Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}
End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Duration: {elapsed_time}
Initial Vectors: {self.initial_count:,}
Final Vectors: {final_count:,}
Vectors Added: {vectors_added:,}
Average Rate: {(vectors_added / elapsed_time.total_seconds() * 60):.1f} vectors/minute
"""
        return summary

def main():
    """Main monitoring interface"""
    monitor = PineconeMonitor()
    
    print("🔍 PINECONE UPLOAD MONITOR")
    print("Choose monitoring mode:")
    print("1. Real-time monitoring (live updates)")
    print("2. Quick stats check")
    print("3. Detailed index analysis")
    
    choice = input("\nEnter choice (1-3): ").strip()
    
    if choice == "1":
        print(f"\n🚀 Starting real-time monitoring...")
        print("This will refresh every 5 seconds")
        print("Press Ctrl+C to stop\n")
        time.sleep(2)
        
        try:
            monitor.monitor_uploads(refresh_interval=5)
        finally:
            print(monitor.get_upload_summary())
    
    elif choice == "2":
        print("\n📊 QUICK STATS CHECK")
        print("=" * 40)
        stats = monitor.get_index_stats()
        for key, value in stats.items():
            print(f"{key}: {value}")
        
        print("\n📋 Vector Breakdown:")
        type_counts = monitor.get_vector_counts_by_type()
        for vector_type, count in type_counts.items():
            print(f"   {vector_type.title()}: {count}")
    
    elif choice == "3":
        print("\n🔬 DETAILED INDEX ANALYSIS")
        print("=" * 40)
        
        # Get comprehensive stats
        stats = monitor.get_index_stats()
        type_counts = monitor.get_vector_counts_by_type()
        
        print(f"Index Name: {monitor.index_name}")
        print(f"Total Vectors: {stats.get('total_vectors', 0):,}")
        print(f"Dimension: {stats.get('dimension', 'unknown')}")
        print(f"Index Fullness: {stats.get('index_fullness', 0):.2%}")
        print()
        
        print("Vector Types:")
        for vector_type, count in type_counts.items():
            print(f"  - {vector_type.title()}: {count}")
        print()
        
        # Sample some recent vectors
        print("Recent Vectors (sample):")
        try:
            sample = monitor.index.query(
                vector=[0.0] * 768,
                top_k=5,
                include_metadata=True
            )
            for i, match in enumerate(sample.matches):
                metadata = match.metadata if hasattr(match, 'metadata') else {}
                print(f"  {i+1}. {match.id}")
                print(f"     Type: {metadata.get('type', 'unknown')}")
                print(f"     Title: {metadata.get('title', 'No title')[:50]}...")
        except Exception as e:
            print(f"  Error getting samples: {e}")
    
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()