#!/usr/bin/env python3
"""
Add Circular Masking to Dual Fisheye Videos

This script adds black circular masking around dual fisheye circles in a video,
similar to the masking logic in make_transparent.py but for video files.

The masking creates black borders around two circular regions positioned 
side-by-side, matching the appearance of GoPro LRV files.

Usage:
    python3 add_circular_masking.py input_video.mp4 [output_video.mp4] [options]

Examples:
    python3 add_circular_masking.py dual_fisheye.mp4
    python3 add_circular_masking.py input.mp4 output.mp4
    python3 add_circular_masking.py input.mp4 output.mp4 --test
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path


def get_video_info(input_file):
    """Get video dimensions and stream info."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-print_format', 'json',
            '-show_streams', '-select_streams', 'v:0', input_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        if not data['streams']:
            raise ValueError("No video stream found in input file")
        
        stream = data['streams'][0]
        width = int(stream['width'])
        height = int(stream['height'])
        
        return width, height
        
    except Exception as e:
        raise ValueError(f"Could not get video info: {e}")


def create_circular_mask_image(width, height, output_path):
    """Create a circular mask image using PIL like make_transparent.py."""
    
    try:
        from PIL import Image, ImageDraw
        
        # Create mask image (white circles on black background)
        mask = Image.new('L', (width, height), 0)  # Black background
        draw = ImageDraw.Draw(mask)
        
        # Calculate circle parameters (matching make_transparent.py logic)
        circle_radius = int(height * 0.45)  # 45% of height as radius
        padding = 20  # Small padding around circles
        
        # Circle centers
        left_x = width // 4
        left_y = height // 2
        right_x = 3 * width // 4
        right_y = height // 2
        
        print(f"Creating circular mask:")
        print(f"  Video dimensions: {width}x{height}")
        print(f"  Circle radius: {circle_radius}px (+ {padding}px padding)")
        print(f"  Left circle: ({left_x}, {left_y})")
        print(f"  Right circle: ({right_x}, {left_y})")
        
        # Draw both circles on the mask (white = keep, black = remove)
        draw.ellipse([
            left_x - circle_radius - padding, 
            left_y - circle_radius - padding,
            left_x + circle_radius + padding, 
            left_y + circle_radius + padding
        ], fill=255)
        
        draw.ellipse([
            right_x - circle_radius - padding, 
            right_y - circle_radius - padding,
            right_x + circle_radius + padding, 
            right_y + circle_radius + padding
        ], fill=255)
        
        # Save the mask
        mask.save(output_path)
        print(f"✓ Created mask image: {output_path}")
        return True
        
    except ImportError:
        print("❌ PIL not available. Install with: pip install Pillow")
        return False
    except Exception as e:
        print(f"❌ Error creating mask: {e}")
        return False


def add_circular_masking(input_file, output_file, test_mode=False, quality=23, preset='fast', verbose=False):
    """Add circular masking to dual fisheye video using a mask image."""
    
    print(f"Adding circular masking to {input_file}...")
    
    # Get video info
    width, height = get_video_info(input_file)
    
    # Validate aspect ratio (should be roughly 2:1 for dual fisheye)
    aspect_ratio = width / height
    if aspect_ratio < 1.8 or aspect_ratio > 2.2:
        print(f"Warning: Video aspect ratio ({width}x{height} = {aspect_ratio:.2f}) "
              f"doesn't match expected dual fisheye format (~2:1)")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            return False
    
    # Create temporary mask image
    mask_path = f"temp_circular_mask_{width}x{height}.png"
    
    if not create_circular_mask_image(width, height, mask_path):
        print("Falling back to simple rectangular masking...")
        return add_rectangular_masking(input_file, output_file, test_mode, quality, preset, verbose)
    
    try:
        # Build filter chain using the mask image
        filter_complex = (
            f"[1:v]format=gray[mask];"
            f"[0:v][mask]alphamerge[masked];"
            f"color=black:size={width}x{height}[bg];"
            f"[bg][masked]overlay=0:0:format=auto,format=yuv420p[final]"
        )
        
        # Build FFmpeg command
        cmd = [
            'ffmpeg', '-y',
            '-i', input_file,
            '-i', mask_path
        ]
        
        # Add test mode duration limit
        if test_mode:
            cmd.extend(['-t', '30'])
            print("Test mode: Processing first 30 seconds only")
        
        cmd.extend([
            '-filter_complex', filter_complex,
            '-map', '[final]',
            '-map', '0:a?',  # Copy audio if present
            '-c:v', 'libx264',
            '-crf', str(quality),
            '-preset', preset,
            '-c:a', 'copy',
            '-movflags', '+faststart',
            output_file
        ])
        
        if verbose:
            print("FFmpeg command:")
            print(' '.join(cmd[:8]) + " ... [filters] ... " + output_file)
            print()
        
        print("Applying circular masking...")
        if test_mode:
            print("(Test mode - 30 seconds only)")
        
        # Run FFmpeg with appropriate timeout
        timeout = 300 if not test_mode else 120
        
        if verbose:
            result = subprocess.run(cmd, timeout=timeout, check=True)
        else:
            result = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True, check=True)
        
        print(f"✓ Circular masking applied successfully!")
        print(f"Output: {output_file}")
        
        # Get output file info
        if os.path.exists(output_file):
            size_mb = os.path.getsize(output_file) / (1024 * 1024)
            print(f"File size: {size_mb:.1f} MB")
        
        return True
        
    except subprocess.TimeoutExpired:
        print(f"❌ FFmpeg timed out after {timeout} seconds")
        return False
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error occurred:")
        if hasattr(e, 'stderr') and e.stderr:
            print(e.stderr)
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    finally:
        # Clean up mask file
        if os.path.exists(mask_path):
            os.remove(mask_path)
            if verbose:
                print(f"Cleaned up temporary mask: {mask_path}")


def add_rectangular_masking(input_file, output_file, test_mode=False, quality=23, preset='fast', verbose=False):
    """Fallback rectangular masking when PIL is not available."""
    
    print("Using rectangular masking fallback...")
    
    # Get video info
    width, height = get_video_info(input_file)
    
    # Calculate rectangular regions around fisheye centers
    circle_radius = int(height * 0.45)
    padding = 20
    left_center_x = width // 4
    right_center_x = 3 * width // 4
    center_y = height // 2
    effective_radius = circle_radius + padding
    box_size = effective_radius * 2
    
    # Create filter for rectangular masking
    filter_complex = (
        f"color=black:size={width}x{height}[bg];"
        f"[0:v]crop={box_size}:{box_size}:{left_center_x-effective_radius}:{center_y-effective_radius}[left_box];"
        f"[0:v]crop={box_size}:{box_size}:{right_center_x-effective_radius}:{center_y-effective_radius}[right_box];"
        f"[bg][left_box]overlay={left_center_x-effective_radius}:{center_y-effective_radius}[with_left];"
        f"[with_left][right_box]overlay={right_center_x-effective_radius}:{center_y-effective_radius}[final]"
    )
    
    # Build FFmpeg command
    cmd = [
        'ffmpeg', '-y',
        '-i', input_file
    ]
    
    if test_mode:
        cmd.extend(['-t', '30'])
    
    cmd.extend([
        '-filter_complex', filter_complex,
        '-map', '[final]',
        '-map', '0:a?',
        '-c:v', 'libx264',
        '-crf', str(quality),
        '-preset', preset,
        '-c:a', 'copy',
        '-movflags', '+faststart',
        output_file
    ])
    
    try:
        timeout = 300 if not test_mode else 120
        
        if verbose:
            result = subprocess.run(cmd, timeout=timeout, check=True)
        else:
            result = subprocess.run(cmd, timeout=timeout, capture_output=True, text=True, check=True)
        
        print(f"✓ Rectangular masking applied successfully!")
        print(f"Output: {output_file}")
        return True
        
    except Exception as e:
        print(f"❌ Rectangular masking failed: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Add circular masking to dual fisheye videos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s dual_fisheye.mp4
  %(prog)s input.mp4 output.mp4
  %(prog)s input.mp4 output.mp4 --test --verbose
        """
    )
    
    parser.add_argument('input_file', help='Input dual fisheye video file')
    parser.add_argument('output_file', nargs='?', help='Output masked video file')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: process only first 30 seconds')
    parser.add_argument('--quality', '-q', type=int, default=23,
                       help='Video quality (CRF value, default: 23)')
    parser.add_argument('--preset', '-p', default='fast',
                       choices=['ultrafast', 'superfast', 'veryfast', 'faster', 'fast', 
                               'medium', 'slow', 'slower', 'veryslow'],
                       help='Encoding preset (default: fast)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed FFmpeg output')
    
    args = parser.parse_args()
    
    # Generate output filename if not provided
    if not args.output_file:
        input_path = Path(args.input_file)
        suffix = "_test_masked" if args.test else "_masked"
        args.output_file = str(input_path.parent / f"{input_path.stem}{suffix}.mp4")
    
    # Validate input file
    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found")
        return 1
    
    # Validate output directory
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    print("=" * 60)
    print("CIRCULAR MASKING FOR DUAL FISHEYE VIDEOS")
    print("=" * 60)
    print(f"Input:    {args.input_file}")
    print(f"Output:   {args.output_file}")
    print(f"Mode:     {'TEST (30s)' if args.test else 'FULL VIDEO'}")
    print(f"Quality:  CRF {args.quality}")
    print(f"Preset:   {args.preset}")
    print()
    
    # Apply masking
    success = add_circular_masking(
        args.input_file,
        args.output_file,
        test_mode=args.test,
        quality=args.quality,
        preset=args.preset,
        verbose=args.verbose
    )
    
    print("\n" + "=" * 60)
    if success:
        print("✅ MASKING COMPLETED SUCCESSFULLY")
        print(f"Your masked dual fisheye video is ready: {args.output_file}")
        print("\nThe video now has black circular borders around the fisheye circles,")
        print("similar to the masking logic in make_transparent.py")
        
        if args.test:
            print("\n📝 This was a test run (30 seconds).")
            print("Remove --test flag to process the full video.")
    else:
        print("❌ MASKING FAILED")
        print("Please check the error messages above and try again.")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
