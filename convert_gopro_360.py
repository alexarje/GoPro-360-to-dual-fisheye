#!/usr/bin/env python3
"""
GoPro Max .360 to Dual Fisheye Converter

Converts GoPro Max .360 files to dual fisheye format with exact projection mapping
and dimensions matching GoPro LRV format (1408x704).

Usage:
    python3 convert_gopro_360.py input.360 output.mp4 [options]

Examples:
    python3 convert_gopro_360.py GS010123.360 converted.mp4
    python3 convert_gopro_360.py input.360 output.mp4 --quality 18 --preset medium
"""

import os
import sys
import subprocess
import argparse
import json
from pathlib import Path


def get_video_info(input_file):
    """Get video information using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-show_format', input_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Find video stream
        video_stream = None
        for stream in data['streams']:
            if stream['codec_type'] == 'video':
                video_stream = stream
                break
        
        if not video_stream:
            raise ValueError("No video stream found")
        
        width = int(video_stream['width'])
        height = int(video_stream['height'])
        duration = float(video_stream.get('duration', data['format'].get('duration', 0)))
        
        return width, height, duration
        
    except Exception as e:
        raise ValueError(f"Could not get video info: {e}")


def convert_gopro_360_to_dual_fisheye(input_file, output_file, quality=23, preset='medium', verbose=False):
    """
    Convert GoPro Max .360 file to dual fisheye format.
    
    Two-step process:
    1. EAC (input) → Equirectangular 
    2. Equirectangular → Dual Fisheye (1408x704)
    """
    
    print(f"Converting {input_file} to dual fisheye format...")
    
    # Get input video info
    try:
        width, height, duration = get_video_info(input_file)
        print(f"Input: {width}x{height}, Duration: {duration:.1f}s")
    except Exception as e:
        print(f"Warning: Could not get input info: {e}")
        duration = 0
    
    # Step 1: EAC → Equirectangular (intermediate)
    # Step 2: Equirectangular → Dual Fisheye (final output)
    
    # Combined filter chain for efficiency
    filter_complex = (
        # Step 1: Convert EAC to Equirectangular
        "[0:v]v360=eac:e:ih_fov=360:iv_fov=180,scale=3840x1920[equirect];"
        
        # Step 2: Convert Equirectangular to Dual Fisheye
        # Left fisheye (190° FOV)
        "[equirect]v360=e:fisheye:ih_fov=360:iv_fov=180:h_fov=190:v_fov=190:w=704:h=704:yaw=-90[left_eye];"
        
        # Right fisheye (190° FOV) 
        "[equirect]v360=e:fisheye:ih_fov=360:iv_fov=180:h_fov=190:v_fov=190:w=704:h=704:yaw=90[right_eye];"
        
        # Combine side by side to create 1408x704 dual fisheye
        "[left_eye][right_eye]hstack=inputs=2[dual_fisheye]"
    )
    
    # Build FFmpeg command
    cmd = [
        'ffmpeg', '-y',
        '-i', input_file,
        '-filter_complex', filter_complex,
        '-map', '[dual_fisheye]',
        '-map', '0:a?',  # Copy all audio streams if present
        '-c:v', 'libx264',
        '-crf', str(quality),
        '-preset', preset,
        '-c:a', 'copy',  # Copy audio without re-encoding
        '-movflags', '+faststart',  # Enable fast start for web playback
        output_file
    ]
    
    if verbose:
        print("FFmpeg command:")
        print(' '.join(cmd[:6]) + " ... [filters] ... " + output_file)
        print()
    
    print("Converting (this may take a while)...")
    
    try:
        if verbose:
            # Show FFmpeg output for debugging
            result = subprocess.run(cmd, check=True)
        else:
            # Hide FFmpeg output for clean interface
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        print(f"✓ Conversion completed successfully!")
        print(f"Output: {output_file}")
        
        # Get output file info
        if os.path.exists(output_file):
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print(f"File size: {size_mb:.1f} MB")
            
            try:
                out_width, out_height, out_duration = get_video_info(output_file)
                print(f"Output format: {out_width}x{out_height}, Duration: {out_duration:.1f}s")
            except:
                pass
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error occurred:")
        if hasattr(e, 'stderr') and e.stderr:
            print(e.stderr)
        else:
            print(f"Return code: {e.returncode}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Convert GoPro Max .360 files to dual fisheye format',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s GS010123.360 converted.mp4
  %(prog)s input.360 output.mp4 --quality 18 --preset medium
  %(prog)s input.360 output.mp4 --verbose
        """
    )
    
    parser.add_argument('input_file', help='Input GoPro Max .360 file')
    parser.add_argument('output_file', help='Output dual fisheye MP4 file')
    parser.add_argument('--quality', '-q', type=int, default=23, 
                       help='Video quality (CRF value, lower = better quality, default: 23)')
    parser.add_argument('--preset', '-p', default='medium',
                       choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 
                               'medium', 'slow', 'slower', 'veryslow'],
                       help='Encoding preset (default: medium)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed FFmpeg output')
    
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        return 1
    
    # Check if input is likely a .360 file
    if not args.input_file.lower().endswith('.360'):
        print(f"Warning: Input file doesn't have .360 extension")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return 1
    
    # Validate output directory
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        print(f"Creating output directory: {output_dir}")
        os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("GOPRO MAX .360 TO DUAL FISHEYE CONVERTER")
    print("=" * 60)
    print(f"Input:    {args.input_file}")
    print(f"Output:   {args.output_file}")
    print(f"Quality:  CRF {args.quality}")
    print(f"Preset:   {args.preset}")
    print()
    
    # Perform conversion
    success = convert_gopro_360_to_dual_fisheye(
        args.input_file,
        args.output_file,
        quality=args.quality,
        preset=args.preset,
        verbose=args.verbose
    )
    
    print("\n" + "=" * 60)
    if success:
        print("✅ CONVERSION COMPLETED SUCCESSFULLY")
        print(f"Your dual fisheye video is ready: {args.output_file}")
        print("\nNext steps:")
        print("• Add circular masking: python3 add_circular_masking.py output.mp4")
        print("• View in VR player or video editing software")
    else:
        print("❌ CONVERSION FAILED")
        print("Please check the error messages above and try again.")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
