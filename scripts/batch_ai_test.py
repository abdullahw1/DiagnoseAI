#!/usr/bin/env python3
"""
Batch AI Testing Script for Liver Pathology Images

This script helps you test multiple images from your liver pathology folder
and generates a comprehensive report of AI accuracy.

Usage:
    python batch_ai_test.py /path/to/liver_pathology_folder
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from app import create_app
from app.ai_service import generate_draft_report, AIServiceError

# Load environment variables
load_dotenv()

def analyze_image(image_path, view_type, expected_pathology):
    """Analyze a single image and return results."""
    try:
        # Create clinical context
        clinical_notes = f"AI TESTING MODE - Batch Analysis\n"
        clinical_notes += f"Image Type: {view_type}\n"
        clinical_notes += f"Expected Pathology: {expected_pathology}\n"
        clinical_notes += "Please analyze this liver ultrasound image and provide detailed findings."
        
        # Generate AI analysis
        raw_response, formatted_text = generate_draft_report(
            image_path=str(image_path),
            clinical_notes=clinical_notes
        )
        
        return {
            'success': True,
            'analysis': formatted_text,
            'raw_response': raw_response,
            'error': None
        }
        
    except AIServiceError as e:
        return {
            'success': False,
            'analysis': None,
            'raw_response': None,
            'error': f"AI Service Error: {str(e)}"
        }
    except Exception as e:
        return {
            'success': False,
            'analysis': None,
            'raw_response': None,
            'error': f"Unexpected Error: {str(e)}"
        }

def extract_pathology_from_filename(filename):
    """Extract expected pathology from filename."""
    # Remove file extension
    name = Path(filename).stem
    
    # Common pathology mappings
    pathology_map = {
        'dilated hepatic veins': 'Dilated hepatic veins',
        'passive heaptic congestion': 'Passive hepatic congestion',
        'coarse liver': 'Coarse liver texture',
        'multiple hepatic cysts': 'Multiple hepatic cysts',
        'cavernuos transformation': 'Cavernous transformation',
        'dilated pv': 'Dilated portal vein',
        'portal vein view normal': 'Normal portal vein',
        'pv thrumbus': 'Portal vein thrombosis',
        'ascities': 'Ascites',
        'fatty liver': 'Fatty liver',
        'hemengioma': 'Hemangioma',
        'hepatic abscess': 'Hepatic abscess',
        'hepatic edema': 'Hepatic edema',
        'acute hepatitis': 'Acute hepatitis',
        'hepatic simple cyst': 'Simple hepatic cyst',
        'hepatic soft tissue mass': 'Hepatic soft tissue mass',
        'liver size': 'Liver size assessment',
        'metastatic focal nodule': 'Metastatic focal nodule',
        'pleural effusion': 'Pleural effusion'
    }
    
    name_lower = name.lower()
    for key, value in pathology_map.items():
        if key in name_lower:
            return value
    
    return name  # Return original if no match found

def main():
    """Main batch testing function."""
    if len(sys.argv) != 2:
        print("Usage: python batch_ai_test.py /path/to/liver_pathology_folder")
        sys.exit(1)
    
    base_folder = Path(sys.argv[1])
    if not base_folder.exists():
        print(f"Error: Folder {base_folder} does not exist")
        sys.exit(1)
    
    # Define folder structure
    folders = {
        'left lobe tr view': 'Left Lobe TR View',
        'portal vein view': 'Portal Vein View', 
        'right lobe log view': 'Right Lobe Log View'
    }
    
    # Supported image extensions
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
    
    # Results storage
    results = {
        'test_date': datetime.now().isoformat(),
        'base_folder': str(base_folder),
        'total_images': 0,
        'successful_analyses': 0,
        'failed_analyses': 0,
        'results_by_folder': {},
        'summary': {}
    }
    
    print("🏥 DiagnoseAI - Batch Liver Pathology Testing")
    print("=" * 60)
    print(f"Testing images in: {base_folder}")
    print()
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        # Process each folder
        for folder_name, view_type in folders.items():
            folder_path = base_folder / folder_name
            
            if not folder_path.exists():
                print(f"⚠️  Folder not found: {folder_path}")
                continue
            
            print(f"📁 Processing: {view_type}")
            print("-" * 40)
            
            folder_results = {
                'view_type': view_type,
                'images': [],
                'success_count': 0,
                'error_count': 0
            }
            
            # Get all image files in folder
            image_files = [f for f in folder_path.iterdir() 
                          if f.is_file() and f.suffix.lower() in image_extensions]
            
            for image_file in sorted(image_files):
                print(f"  🔍 Analyzing: {image_file.name}")
                
                # Extract expected pathology from filename
                expected_pathology = extract_pathology_from_filename(image_file.name)
                
                # Analyze image
                result = analyze_image(image_file, view_type, expected_pathology)
                
                # Store result
                image_result = {
                    'filename': image_file.name,
                    'expected_pathology': expected_pathology,
                    'success': result['success'],
                    'analysis': result['analysis'],
                    'error': result['error'],
                    'timestamp': datetime.now().isoformat()
                }
                
                folder_results['images'].append(image_result)
                results['total_images'] += 1
                
                if result['success']:
                    folder_results['success_count'] += 1
                    results['successful_analyses'] += 1
                    print(f"    ✅ Success")
                else:
                    folder_results['error_count'] += 1
                    results['failed_analyses'] += 1
                    print(f"    ❌ Failed: {result['error']}")
            
            results['results_by_folder'][folder_name] = folder_results
            print(f"  📊 Folder Summary: {folder_results['success_count']}/{len(image_files)} successful")
            print()
    
    # Generate summary
    success_rate = (results['successful_analyses'] / results['total_images'] * 100) if results['total_images'] > 0 else 0
    
    results['summary'] = {
        'success_rate_percent': round(success_rate, 2),
        'total_images': results['total_images'],
        'successful_analyses': results['successful_analyses'],
        'failed_analyses': results['failed_analyses']
    }
    
    # Save results to file
    output_file = f"ai_batch_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Print final summary
    print("📊 FINAL SUMMARY")
    print("=" * 60)
    print(f"Total Images Tested: {results['total_images']}")
    print(f"Successful Analyses: {results['successful_analyses']}")
    print(f"Failed Analyses: {results['failed_analyses']}")
    print(f"Success Rate: {success_rate:.2f}%")
    print()
    print(f"📄 Detailed results saved to: {output_file}")
    print()
    
    # Print per-folder breakdown
    for folder_name, folder_data in results['results_by_folder'].items():
        folder_success_rate = (folder_data['success_count'] / len(folder_data['images']) * 100) if folder_data['images'] else 0
        print(f"  {folder_data['view_type']}: {folder_data['success_count']}/{len(folder_data['images'])} ({folder_success_rate:.1f}%)")

if __name__ == '__main__':
    main()