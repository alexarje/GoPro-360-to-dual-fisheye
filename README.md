# GoPro Max .360 to Dual Fisheye Converter

A complete solution for converting GoPro Max .360 files to dual fisheye format (LRV-style) with proper projection mapping and optional circular masking.

## Features

- ✅ **Accurate Projection Conversion**: EAC → Equirectangular → Dual Fisheye
- ✅ **Exact GoPro LRV Dimensions**: 1408x704 pixels with correct FOV
- ✅ **Audio Preservation**: Maintains original audio tracks
- ✅ **Circular Masking**: Optional black circular borders around fisheye circles
- ✅ **Batch Processing**: Process multiple files at once
- ✅ **Progress Monitoring**: Real-time conversion progress

## Requirements

- **FFmpeg** (with v360 filter support)
- **Python 3.6+**
- **Pillow** (for circular masking): `pip install Pillow`

## Quick Start

### 1. Convert Single File
```bash
python3 convert_gopro_360.py input.360 output.mp4
```

### 2. Add Circular Masking
```bash
python3 add_circular_masking.py dual_fisheye.mp4 masked_output.mp4
```

### 3. Batch Convert Multiple Files
```bash
python3 batch_convert.py /path/to/360/files/ /path/to/output/
```

## Installation

1. **Clone this repository:**
   ```bash
   git clone https://github.com/yourusername/gopro-max-converter.git
   cd gopro-max-converter
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify FFmpeg installation:**
   ```bash
   ffmpeg -version
   ```

## Usage Examples

### Basic Conversion
Convert a GoPro Max .360 file to dual fisheye format:
```bash
python3 convert_gopro_360.py GS010123.360 converted_fisheye.mp4
```

### With Custom Settings
```bash
python3 convert_gopro_360.py input.360 output.mp4 --quality 18 --preset medium
```

### Add Circular Masking
Add black circular borders around the fisheye circles:
```bash
python3 add_circular_masking.py converted_fisheye.mp4 final_output.mp4
```

### Batch Processing
Convert all .360 files in a directory:
```bash
python3 batch_convert.py ./input_folder/ ./output_folder/ --add-masking
```

## Technical Details

### Projection Pipeline
1. **Input**: GoPro Max .360 (EAC projection)
2. **Step 1**: EAC → Equirectangular (360°×180°)
3. **Step 2**: Equirectangular → Dual Fisheye (2×190° FOV)
4. **Output**: 1408×704 dual fisheye video

### Circular Masking
- Uses the same logic as `make_transparent.py`
- Circle radius: 45% of video height + 20px padding
- Left circle: centered at 1/4 width
- Right circle: centered at 3/4 width

## File Structure

```
gopro-max-converter/
├── convert_gopro_360.py       # Main conversion script
├── add_circular_masking.py    # Circular masking script
├── batch_convert.py           # Batch processing script
├── requirements.txt           # Python dependencies
├── README.md                  # This file
├── examples/                  # Example files and outputs
└── docs/                      # Additional documentation
```

## Supported Formats

### Input
- `.360` files from GoPro Max cameras
- EAC (Equi-Angular Cubemap) projection

### Output
- MP4 with H.264 encoding
- Dual fisheye layout (1408×704)
- Original audio preserved
- Optional circular masking

## Performance

- **Conversion Speed**: ~1-2x real-time (depending on hardware)
- **Quality**: CRF 23 (adjustable)
- **File Size**: ~70% of original .360 file

## Troubleshooting

### FFmpeg Not Found
```bash
# Ubuntu/Debian
sudo apt update && sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

### Memory Issues
For large files, reduce quality or use hardware acceleration:
```bash
python3 convert_gopro_360.py input.360 output.mp4 --preset faster
```

### Circular Masking Issues
Install Pillow for proper circular masking:
```bash
pip install Pillow
```

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature-name`
5. Create Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Based on research into GoPro Max .360 file format
- Uses FFmpeg's excellent v360 filter for projection conversion
- Circular masking logic adapted from transparency processing workflows

## Related Projects

- [GoPro Max Official Tools](https://gopro.com/en/us/shop/softwareandapp)
- [FFmpeg v360 Documentation](https://ffmpeg.org/ffmpeg-filters.html#v360)

---

**Note**: This is an unofficial tool. GoPro Max and .360 are trademarks of GoPro, Inc.
