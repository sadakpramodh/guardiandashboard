# firebase_structure_analyzer.py
"""
Firebase Structure Analyzer
Analyzes Firebase Firestore structure and provides comprehensive data insights
"""

import json
import os
from datetime import datetime
from collections import defaultdict, Counter
from firebase_admin import credentials, firestore, initialize_app
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_firebase():
    """Initialize Firebase Admin SDK"""
    try:
        # Create credentials dictionary from environment variables
        firebase_config = {
            "type": os.getenv("FIREBASE_TYPE", "service_account"),
            "project_id": os.getenv("FIREBASE_PROJECT_ID"),
            "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
            "private_key": os.getenv("FIREBASE_PRIVATE_KEY", "").replace('\\n', '\n'),
            "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
            "client_id": os.getenv("FIREBASE_CLIENT_ID"),
            "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
            "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
            "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_X509_CERT_URL"),
            "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_X509_CERT_URL"),
            "universe_domain": os.getenv("FIREBASE_UNIVERSE_DOMAIN", "googleapis.com")
        }
        
        # Initialize Firebase Admin SDK
        cred = credentials.Certificate(firebase_config)
        initialize_app(cred)
        
        return firestore.client()
        
    except Exception as e:
        print(f"❌ Firebase initialization failed: {str(e)}")
        return None

def analyze_document_structure(doc_data, field_types=None, field_samples=None):
    """Analyze document structure and extract field information"""
    if field_types is None:
        field_types = defaultdict(Counter)
    if field_samples is None:
        field_samples = defaultdict(list)
    
    for field_name, field_value in doc_data.items():
        # Get field type
        field_type = type(field_value).__name__
        field_types[field_name][field_type] += 1
        
        # Store sample values (limit to 3 samples per field)
        if len(field_samples[field_name]) < 3:
            if field_type in ['str', 'int', 'float', 'bool']:
                field_samples[field_name].append(field_value)
            elif field_type == 'datetime':
                field_samples[field_name].append(field_value.isoformat())
            elif field_type == 'dict':
                field_samples[field_name].append(f"<dict with {len(field_value)} keys>")
            elif field_type == 'list':
                field_samples[field_name].append(f"<list with {len(field_value)} items>")
            else:
                field_samples[field_name].append(f"<{field_type}>")
    
    return field_types, field_samples

def analyze_collection(db, collection_path, max_docs=10):
    """Analyze a specific collection"""
    print(f"\n📁 Analyzing Collection: {collection_path}")
    print("=" * 50)
    
    try:
        # Get collection reference
        collection_ref = db.collection(collection_path)
        
        # Get document count (approximate)
        docs = list(collection_ref.limit(max_docs).stream())
        total_docs = len(docs)
        
        if total_docs == 0:
            print("   📄 No documents found")
            return {}
        
        print(f"   📊 Documents analyzed: {total_docs}")
        
        # Analyze document structures
        field_types = defaultdict(Counter)
        field_samples = defaultdict(list)
        doc_sizes = []
        timestamps = []
        
        for doc in docs:
            doc_data = doc.to_dict()
            doc_sizes.append(len(str(doc_data)))
            
            # Extract timestamps if available
            for field_name, field_value in doc_data.items():
                if 'timestamp' in field_name.lower():
                    if isinstance(field_value, (int, float)):
                        try:
                            # Convert milliseconds to datetime
                            dt = datetime.fromtimestamp(field_value / 1000.0)
                            timestamps.append(dt)
                        except:
                            pass
            
            # Analyze structure
            analyze_document_structure(doc_data, field_types, field_samples)
        
        # Print field analysis
        print(f"   🔤 Fields found: {len(field_types)}")
        print()
        
        for field_name, type_counter in field_types.items():
            print(f"   📋 {field_name}:")
            for field_type, count in type_counter.items():
                percentage = (count / total_docs) * 100
                print(f"      • {field_type}: {count}/{total_docs} ({percentage:.1f}%)")
            
            # Show sample values
            if field_name in field_samples and field_samples[field_name]:
                samples = field_samples[field_name][:3]
                print(f"      📝 Samples: {samples}")
            print()
        
        # Time range analysis
        if timestamps:
            timestamps.sort()
            print(f"   🕐 Time Range:")
            print(f"      • Earliest: {timestamps[0].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      • Latest: {timestamps[-1].strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"      • Span: {(timestamps[-1] - timestamps[0]).days} days")
            print()
        
        # Document size analysis
        if doc_sizes:
            avg_size = sum(doc_sizes) / len(doc_sizes)
            print(f"   📏 Document Size:")
            print(f"      • Average: {avg_size:.0f} characters")
            print(f"      • Min: {min(doc_sizes)} characters")
            print(f"      • Max: {max(doc_sizes)} characters")
        
        return {
            'total_docs': total_docs,
            'field_types': dict(field_types),
            'field_samples': dict(field_samples),
            'time_range': timestamps,
            'doc_sizes': doc_sizes
        }
        
    except Exception as e:
        print(f"   ❌ Error analyzing collection: {str(e)}")
        return {}

def discover_subcollections(db, parent_path, max_docs=5):
    """Discover subcollections within a document"""
    subcollections = []
    
    try:
        # Get parent collection
        parent_ref = db.collection(parent_path)
        docs = list(parent_ref.limit(max_docs).stream())
        
        for doc in docs:
            # Get subcollections for this document
            for subcoll_ref in doc.reference.collections():
                subcoll_name = subcoll_ref.id
                subcoll_path = f"{parent_path}/{doc.id}/{subcoll_name}"
                
                if subcoll_path not in subcollections:
                    subcollections.append(subcoll_path)
                    
                    # Check for sub-subcollections
                    try:
                        subdocs = list(subcoll_ref.limit(2).stream())
                        for subdoc in subdocs:
                            for subsubcoll_ref in subdoc.reference.collections():
                                subsubcoll_name = subsubcoll_ref.id
                                subsubcoll_path = f"{subcoll_path}/{subdoc.id}/{subsubcoll_name}"
                                if subsubcoll_path not in subcollections:
                                    subcollections.append(subsubcoll_path)
                    except:
                        pass
    except Exception as e:
        print(f"   ⚠️ Error discovering subcollections: {str(e)}")
    
    return subcollections

def analyze_firebase_structure(db, max_docs_per_collection=10):
    """Analyze entire Firebase structure"""
    print("🔍 FIREBASE STRUCTURE ANALYSIS")
    print("=" * 60)
    print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 Max documents per collection: {max_docs_per_collection}")
    
    structure_info = {}
    
    # Root collections
    root_collections = [
        'users',
        'user_management', 
        'audit_logs',
        'system_settings'
    ]
    
    for collection_name in root_collections:
        try:
            # Analyze root collection
            collection_info = analyze_collection(db, collection_name, max_docs_per_collection)
            structure_info[collection_name] = collection_info
            
            # Discover and analyze subcollections
            subcollections = discover_subcollections(db, collection_name, max_docs=3)
            
            if subcollections:
                print(f"\n📂 Subcollections found in '{collection_name}':")
                for subcoll_path in subcollections:
                    print(f"   └── {subcoll_path}")
                    
                    # Analyze each subcollection
                    subcoll_info = analyze_collection(db, subcoll_path, max_docs=5)
                    structure_info[subcoll_path] = subcoll_info
                    
        except Exception as e:
            print(f"❌ Error analyzing '{collection_name}': {str(e)}")
    
    return structure_info

def generate_structure_report(structure_info):
    """Generate a comprehensive structure report"""
    print("\n\n📋 FIREBASE STRUCTURE SUMMARY")
    print("=" * 60)
    
    # Collection overview
    total_collections = len(structure_info)
    total_documents = sum(info.get('total_docs', 0) for info in structure_info.values())
    
    print(f"📁 Total Collections: {total_collections}")
    print(f"📄 Total Documents Analyzed: {total_documents}")
    
    # Collection breakdown
    print("\n📊 Collection Breakdown:")
    for collection_path, info in structure_info.items():
        doc_count = info.get('total_docs', 0)
        field_count = len(info.get('field_types', {}))
        print(f"   • {collection_path}: {doc_count} docs, {field_count} fields")
    
    # Common field patterns
    print("\n🔤 Common Field Patterns:")
    all_fields = set()
    for info in structure_info.values():
        all_fields.update(info.get('field_types', {}).keys())
    
    field_frequency = Counter()
    for info in structure_info.values():
        for field_name in info.get('field_types', {}):
            field_frequency[field_name] += 1
    
    common_fields = field_frequency.most_common(10)
    for field_name, frequency in common_fields:
        print(f"   • {field_name}: appears in {frequency} collections")
    
    # Data types analysis
    print("\n📝 Data Types Used:")
    all_types = Counter()
    for info in structure_info.values():
        for field_types in info.get('field_types', {}).values():
            all_types.update(field_types.keys())
    
    for data_type, count in all_types.most_common():
        print(f"   • {data_type}: {count} occurrences")

def export_structure_to_json(structure_info, filename="firebase_structure.json"):
    """Export structure analysis to JSON file"""
    
    # Convert datetime objects to strings for JSON serialization
    def convert_datetime(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, list):
            return [convert_datetime(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: convert_datetime(v) for k, v in obj.items()}
        return obj
    
    serializable_info = convert_datetime(structure_info)
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(serializable_info, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Structure exported to: {filename}")

def main():
    """Main function to run Firebase structure analysis"""
    print("🚀 Starting Firebase Structure Analysis...")
    
    # Initialize Firebase
    db = init_firebase()
    if not db:
        print("❌ Failed to initialize Firebase. Check your credentials.")
        return
    
    try:
        # Analyze structure
        structure_info = analyze_firebase_structure(db, max_docs_per_collection=15)
        
        # Generate summary report
        generate_structure_report(structure_info)
        
        # Export to JSON
        export_structure_to_json(structure_info)
        
        print("\n✅ Analysis complete!")
        print("\n📋 What to do next:")
        print("   1. Review the structure summary above")
        print("   2. Check the exported JSON file for detailed schema")
        print("   3. Share the analysis output with your development team")
        print("   4. Use this info to optimize your dashboard queries")
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")

if __name__ == "__main__":
    main()