# Technical Documentation

## GoPro Max .360 File Format

GoPro Max cameras record 360° videos in .360 files using EAC (Equi-Angular Cubemap) projection:

- **Projection**: EAC maps the 360° sphere onto 6 cube faces arranged in a specific layout
- **Advantage**: More uniform pixel distribution than equirectangular
- **Disadvantage**: Requires conversion for most VR players and editing software

## Conversion Pipeline

### Two-Step Process

1. **EAC → Equirectangular**
   - Converts from cubemap to standard 360° format
   - Intermediate step for maximum compatibility
   - Resolution: 3840x1920 (standard equirectangular ratio)

2. **Equirectangular → Dual Fisheye**
   - Projects two 190° fisheye views
   - Left eye: yaw=-90° (rotated left)
   - Right eye: yaw=90° (rotated right)
   - Final resolution: 1408x704 (2:1 aspect ratio)

### FFmpeg Filter Chain

```bash
# Combined filter for efficiency
[0:v]v360=eac:e:ih_fov=360:iv_fov=180,scale=3840x1920[equirect];
[equirect]v360=e:fisheye:ih_fov=360:iv_fov=180:h_fov=190:v_fov=190:w=704:h=704:yaw=-90[left_eye];
[equirect]v360=e:fisheye:ih_fov=360:iv_fov=180:h_fov=190:v_fov=190:w=704:h=704:yaw=90[right_eye];
[left_eye][right_eye]hstack=inputs=2[dual_fisheye]
```

## Circular Masking Algorithm

### Parameters (matching make_transparent.py)

- **Circle Radius**: 45% of video height
- **Padding**: 20 pixels around each circle
- **Left Circle Center**: (width/4, height/2)
- **Right Circle Center**: (3*width/4, height/2)

### Implementation

1. **Create Mask Image** (PIL)
   ```python
   # White circles on black background
   circle_radius = int(height * 0.45) + 20
   left_center = (width // 4, height // 2)
   right_center = (3 * width // 4, height // 2)
   ```

2. **Apply Mask** (FFmpeg)
   ```bash
   [1:v]format=gray[mask];
   [0:v][mask]alphamerge[masked];
   color=black:size=WxH[bg];
   [bg][masked]overlay=0:0[final]
   ```

## Performance Optimization

### Encoding Settings

| Setting | Fast | Balanced | Quality |
|---------|------|----------|---------|
| Preset | ultrafast | medium | slow |
| CRF | 28 | 23 | 18 |
| Speed | 4x realtime | 1x realtime | 0.3x realtime |

### Memory Management

- **Intermediate Files**: Avoided by using filter chains
- **Streaming**: FFmpeg processes video in chunks
- **Parallel**: Batch processing uses ThreadPoolExecutor

### Hardware Acceleration

For supported systems, add hardware encoding:
```bash
# NVIDIA (if available)
-c:v h264_nvenc

# Intel QuickSync (if available)  
-c:v h264_qsv

# Apple VideoToolbox (macOS)
-c:v h264_videotoolbox
```

## Quality Analysis

### Projection Accuracy

The dual fisheye output maintains:
- **Spatial Accuracy**: Correct geometric relationships
- **Temporal Accuracy**: Perfect frame synchronization
- **Color Accuracy**: No color space conversion artifacts

### Comparison with GoPro LRV

| Aspect | Our Output | GoPro LRV | Match |
|--------|------------|-----------|-------|
| Resolution | 1408x704 | 1408x704 | ✅ |
| FOV | 190° | 190° | ✅ |
| Aspect Ratio | 2:1 | 2:1 | ✅ |
| Circle Positioning | Calculated | Empirical | ✅ |
| Masking Style | Black borders | Black borders | ✅ |

## Error Handling

### Common Issues

1. **FFmpeg Not Found**
   - Solution: Install FFmpeg with v360 filter support
   - Check: `ffmpeg -filters | grep v360`

2. **Memory Errors**
   - Solution: Use faster presets, lower resolution
   - Alternative: Process in segments

3. **Slow Performance**
   - Solution: Hardware acceleration, parallel processing
   - Monitor: CPU/GPU usage during conversion

4. **Audio Sync Issues**
   - Solution: Copy audio streams without re-encoding
   - Flag: `-c:a copy`

### Validation

Each conversion includes automatic validation:
- Input file format verification
- Output dimension checking
- Audio stream preservation
- File integrity verification

## Development Notes

### Dependencies

- **FFmpeg**: Core conversion engine
- **Python 3.6+**: Script runtime
- **Pillow**: Circular mask generation
- **ThreadPoolExecutor**: Parallel processing

### Testing

Test with various input formats:
- Different GoPro Max recording modes
- Various durations (30s to 60min+)
- Different lighting conditions
- Audio-only vs video+audio files

### Future Enhancements

Potential improvements:
- GPU acceleration integration
- Real-time preview
- Custom FOV settings
- Stereo audio processing
- Metadata preservation
