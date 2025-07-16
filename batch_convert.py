#!/usr/bin/env python3
"""
Batch Convert GoPro Max .360 files to Dual Fisheye

This script processes multiple GoPro Max .360 files in a directory,
converting them to dual fisheye format with optional circular masking.

Usage:
    python3 batch_convert.py input_dir output_dir [options]

Examples:
    python3 batch_convert.py ./360_files/ ./fisheye_output/
    python3 batch_convert.py ./input/ ./output/ --add-masking --quality 20
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def find_360_files(input_dir):
    """Find all .360 files in the input directory."""
    input_path = Path(input_dir)
    
    if not input_path.exists():
        raise ValueError(f"Input directory '{input_dir}' does not exist")
    
    # Find .360 files (case insensitive)
    files = []
    for pattern in ['*.360', '*.360']:
        files.extend(input_path.glob(pattern))
        files.extend(input_path.glob(pattern.upper()))
    
    # Remove duplicates and sort
    files = sorted(list(set(files)))
    
    return files


def convert_single_file(input_file, output_file, quality, preset, add_masking, verbose):
    """Convert a single .360 file to dual fisheye."""
    
    start_time = time.time()
    
    try:
        print(f"🔄 Processing: {input_file.name}")
        
        # Step 1: Convert to dual fisheye
        temp_output = output_file.parent / f"temp_{output_file.name}"
        
        # Import the conversion function
        sys.path.insert(0, str(Path(__file__).parent))
        from convert_gopro_360 import convert_gopro_360_to_dual_fisheye
        
        success = convert_gopro_360_to_dual_fisheye(
            str(input_file),
            str(temp_output),
            quality=quality,
            preset=preset,
            verbose=verbose
        )
        
        if not success:
            return False, f"Conversion failed for {input_file.name}"
        
        # Step 2: Add masking if requested
        if add_masking:
            print(f"🎯 Adding circular masking: {input_file.name}")
            
            from add_circular_masking import add_circular_masking
            
            success = add_circular_masking(
                str(temp_output),
                str(output_file),
                test_mode=False,
                quality=quality,
                preset=preset,
                verbose=verbose
            )
            
            # Clean up temp file
            if temp_output.exists():
                temp_output.unlink()
            
            if not success:
                return False, f"Masking failed for {input_file.name}"
        else:
            # Move temp file to final output
            temp_output.rename(output_file)
        
        elapsed = time.time() - start_time
        size_mb = output_file.stat().st_size / (1024 * 1024)
        
        return True, f"✅ {input_file.name} → {output_file.name} ({size_mb:.1f}MB, {elapsed:.1f}s)"
        
    except Exception as e:
        # Clean up temp file if it exists
        temp_output = output_file.parent / f"temp_{output_file.name}"
        if temp_output.exists():
            temp_output.unlink()
            
        return False, f"❌ {input_file.name}: {str(e)}"


def batch_convert(input_dir, output_dir, quality=23, preset='medium', add_masking=False, 
                 max_workers=2, verbose=False):
    """Batch convert .360 files to dual fisheye format."""
    
    # Find input files
    input_files = find_360_files(input_dir)
    
    if not input_files:
        print(f"No .360 files found in {input_dir}")
        return 0, 0
    
    print(f"Found {len(input_files)} .360 files to process")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Prepare file pairs
    file_pairs = []
    for input_file in input_files:
        # Generate output filename
        if add_masking:
            output_name = f"{input_file.stem}_fisheye_masked.mp4"
        else:
            output_name = f"{input_file.stem}_fisheye.mp4"
        
        output_file = output_path / output_name
        file_pairs.append((input_file, output_file))
    
    # Process files
    successful = 0
    failed = 0
    results = []
    
    print(f"\nProcessing with {max_workers} parallel workers...")
    print(f"Settings: Quality={quality}, Preset={preset}, Masking={'Yes' if add_masking else 'No'}")
    print("-" * 60)
    
    start_time = time.time()
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all jobs
        future_to_file = {
            executor.submit(
                convert_single_file, 
                input_file, output_file, quality, preset, add_masking, verbose
            ): (input_file, output_file)
            for input_file, output_file in file_pairs
        }
        
        # Process completed jobs
        for future in as_completed(future_to_file):
            input_file, output_file = future_to_file[future]
            
            try:
                success, message = future.result()
                results.append(message)
                print(message)
                
                if success:
                    successful += 1
                else:
                    failed += 1
                    
            except Exception as e:
                failed += 1
                error_msg = f"❌ {input_file.name}: Unexpected error: {e}"
                results.append(error_msg)
                print(error_msg)
    
    total_time = time.time() - start_time
    
    # Print summary
    print("\n" + "=" * 60)
    print("BATCH CONVERSION SUMMARY")
    print("=" * 60)
    print(f"Total files processed: {len(input_files)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Total time: {total_time:.1f} seconds")
    
    if successful > 0:
        print(f"Average time per file: {total_time/len(input_files):.1f} seconds")
    
    print(f"\nOutput directory: {output_dir}")
    
    return successful, failed


def main():
    parser = argparse.ArgumentParser(
        description='Batch convert GoPro Max .360 files to dual fisheye format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s ./360_files/ ./output/
  %(prog)s ./input/ ./output/ --add-masking --quality 20
  %(prog)s ./input/ ./output/ --workers 4 --preset fast
        """
    )
    
    parser.add_argument('input_dir', help='Directory containing .360 files')
    parser.add_argument('output_dir', help='Output directory for converted files')
    parser.add_argument('--add-masking', action='store_true',
                       help='Add circular masking to output videos')
    parser.add_argument('--quality', '-q', type=int, default=23,
                       help='Video quality (CRF value, default: 23)')
    parser.add_argument('--preset', '-p', default='medium',
                       choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 
                               'medium', 'slow', 'slower', 'veryslow'],
                       help='Encoding preset (default: medium)')
    parser.add_argument('--workers', '-w', type=int, default=2,
                       help='Number of parallel workers (default: 2)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed FFmpeg output')
    
    args = parser.parse_args()
    
    # Validate directories
    if not os.path.exists(args.input_dir):
        print(f"Error: Input directory '{args.input_dir}' does not exist")
        return 1
    
    # Validate worker count
    if args.workers < 1 or args.workers > 8:
        print("Error: Number of workers must be between 1 and 8")
        return 1
    
    print("=" * 60)
    print("BATCH GOPRO MAX .360 TO DUAL FISHEYE CONVERTER")
    print("=" * 60)
    print(f"Input directory:  {args.input_dir}")
    print(f"Output directory: {args.output_dir}")
    print(f"Quality:          CRF {args.quality}")
    print(f"Preset:           {args.preset}")
    print(f"Add masking:      {'Yes' if args.add_masking else 'No'}")
    print(f"Parallel workers: {args.workers}")
    print()
    
    try:
        successful, failed = batch_convert(
            args.input_dir,
            args.output_dir,
            quality=args.quality,
            preset=args.preset,
            add_masking=args.add_masking,
            max_workers=args.workers,
            verbose=args.verbose
        )
        
        if failed == 0:
            print("\n🎉 All files converted successfully!")
            return 0
        elif successful > 0:
            print(f"\n⚠️  Partial success: {successful} succeeded, {failed} failed")
            return 1
        else:
            print("\n❌ All conversions failed")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Batch conversion interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Batch conversion failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())
