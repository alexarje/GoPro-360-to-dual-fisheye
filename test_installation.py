#!/usr/bin/env python3
"""
Test script to verify GoPro Max converter installation and dependencies.

Usage:
    python3 test_installation.py
"""

import sys
import subprocess
import importlib.util
from pathlib import Path


def test_python_version():
    """Test Python version compatibility."""
    print("Testing Python version...")
    
    if sys.version_info < (3, 6):
        print("❌ Python 3.6+ required, found:", sys.version)
        return False
    else:
        print(f"✅ Python {sys.version.split()[0]} (compatible)")
        return True


def test_ffmpeg():
    """Test FFmpeg installation and v360 filter support."""
    print("\nTesting FFmpeg...")
    
    try:
        # Test FFmpeg availability
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("❌ FFmpeg not found or not working")
            return False
        
        version_line = result.stdout.split('\n')[0]
        print(f"✅ {version_line}")
        
        # Test v360 filter availability
        result = subprocess.run(['ffmpeg', '-filters'], 
                              capture_output=True, text=True, timeout=10)
        if 'v360' not in result.stdout:
            print("❌ v360 filter not available in FFmpeg")
            print("   Please install a recent version of FFmpeg with v360 support")
            return False
        
        print("✅ v360 filter available")
        return True
        
    except FileNotFoundError:
        print("❌ FFmpeg not found in PATH")
        print("   Please install FFmpeg: https://ffmpeg.org/download.html")
        return False
    except subprocess.TimeoutExpired:
        print("❌ FFmpeg test timed out")
        return False
    except Exception as e:
        print(f"❌ FFmpeg test failed: {e}")
        return False


def test_pillow():
    """Test Pillow (PIL) installation for circular masking."""
    print("\nTesting Pillow (for circular masking)...")
    
    try:
        from PIL import Image, ImageDraw
        print("✅ Pillow available")
        
        # Test basic functionality
        img = Image.new('RGB', (100, 100), 'black')
        draw = ImageDraw.Draw(img)
        draw.ellipse([10, 10, 90, 90], fill='white')
        print("✅ Pillow image operations working")
        return True
        
    except ImportError:
        print("⚠️  Pillow not available")
        print("   Circular masking will use fallback rectangular masking")
        print("   Install with: pip install Pillow")
        return False
    except Exception as e:
        print(f"❌ Pillow test failed: {e}")
        return False


def test_scripts():
    """Test that converter scripts are present and importable."""
    print("\nTesting converter scripts...")
    
    script_dir = Path(__file__).parent
    scripts = ['convert_gopro_360.py', 'add_circular_masking.py', 'batch_convert.py']
    
    all_present = True
    for script in scripts:
        script_path = script_dir / script
        if script_path.exists():
            print(f"✅ {script} found")
        else:
            print(f"❌ {script} missing")
            all_present = False
    
    return all_present


def run_all_tests():
    """Run all installation tests."""
    print("=" * 60)
    print("GOPRO MAX CONVERTER INSTALLATION TEST")
    print("=" * 60)
    
    tests = [
        ("Python Version", test_python_version),
        ("FFmpeg", test_ffmpeg),
        ("Pillow", test_pillow),
        ("Scripts", test_scripts)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The converter is ready to use.")
        print("\nNext steps:")
        print("• Convert a .360 file: python3 convert_gopro_360.py input.360 output.mp4")
        print("• Add masking: python3 add_circular_masking.py dual_fisheye.mp4")
        print("• Batch convert: python3 batch_convert.py input_dir/ output_dir/")
        return 0
    elif passed >= 2:  # Python and FFmpeg are essential
        print("\n⚠️  Basic functionality available with some limitations.")
        print("Consider installing missing dependencies for full functionality.")
        return 0
    else:
        print("\n❌ Critical dependencies missing. Please install required software.")
        return 1


if __name__ == '__main__':
    exit(run_all_tests())
