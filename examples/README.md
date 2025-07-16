# Examples and Usage

This directory contains example usage scenarios and sample outputs.

## Example Commands

### Basic Conversion
```bash
# Convert a single .360 file
python3 convert_gopro_360.py GS010123.360 output_fisheye.mp4

# Convert with high quality
python3 convert_gopro_360.py input.360 output.mp4 --quality 18 --preset slow
```

### Adding Circular Masking
```bash
# Add circular masking to dual fisheye video
python3 add_circular_masking.py dual_fisheye.mp4 masked_output.mp4

# Test masking on first 30 seconds
python3 add_circular_masking.py input.mp4 test_output.mp4 --test

# High quality masking
python3 add_circular_masking.py input.mp4 output.mp4 --quality 18 --preset slow
```

### Batch Processing
```bash
# Convert all .360 files in a directory
python3 batch_convert.py ./360_files/ ./output/

# Batch convert with masking
python3 batch_convert.py ./input/ ./output/ --add-masking

# Parallel processing with 4 workers
python3 batch_convert.py ./input/ ./output/ --workers 4 --quality 20
```

## Expected Output Formats

### Input: GoPro Max .360
- **Format**: EAC (Equi-Angular Cubemap) projection
- **Typical Resolution**: 5760x2880 or similar
- **File Size**: 1-4 GB per minute

### Output: Dual Fisheye
- **Format**: Side-by-side fisheye projection
- **Resolution**: 1408x704 (matching GoPro LRV format)
- **FOV**: 190° per eye
- **File Size**: ~70% of original

### Output: Dual Fisheye with Masking
- **Format**: Same as above with black circular borders
- **Masking**: Circles positioned at 1/4 and 3/4 width
- **Circle Radius**: 45% of video height + 20px padding

## Performance Examples

Based on typical hardware (mid-range desktop):

| Input Duration | Input Size | Output Size | Conversion Time | With Masking |
|---------------|------------|-------------|-----------------|--------------|
| 30 seconds    | 200 MB     | 140 MB      | 45 seconds      | +15 seconds  |
| 2 minutes     | 800 MB     | 560 MB      | 3 minutes       | +1 minute    |
| 10 minutes    | 4 GB       | 2.8 GB      | 15 minutes      | +5 minutes   |

## Quality Settings

| CRF Value | Quality Level | File Size | Use Case |
|-----------|---------------|-----------|----------|
| 18        | Very High     | Large     | Archival, editing |
| 23        | High (default)| Medium    | General use |
| 28        | Medium        | Small     | Streaming, preview |
| 32        | Low           | Very Small| Quick tests |

## Troubleshooting Examples

### Memory Issues
```bash
# Use faster preset to reduce memory usage
python3 convert_gopro_360.py input.360 output.mp4 --preset faster

# Lower quality for large files
python3 convert_gopro_360.py input.360 output.mp4 --quality 28
```

### Slow Processing
```bash
# Use fastest preset
python3 convert_gopro_360.py input.360 output.mp4 --preset ultrafast

# Parallel batch processing
python3 batch_convert.py ./input/ ./output/ --workers 4 --preset fast
```

### Testing Before Full Conversion
```bash
# Test masking on short clip
python3 add_circular_masking.py input.mp4 test.mp4 --test

# Quick conversion test
python3 convert_gopro_360.py input.360 test.mp4 --preset ultrafast --quality 32
```
