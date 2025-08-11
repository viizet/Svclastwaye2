import io
import json
import gzip
import base64
import logging
import tempfile
import os
from xml.etree import ElementTree as ET
from typing import Tuple, Optional
import cairosvg
from PIL import Image
from converter import SVGToTGSConverter

logger = logging.getLogger(__name__)

class SVGValidator:
    """Validates SVG files for conversion requirements"""
    
    def __init__(self):
        self.required_width = 512
        self.required_height = 512
    
    def validate_svg(self, svg_content: bytes) -> Tuple[bool, str]:
        """
        Validate SVG content for dimension requirements
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        try:
            # Parse SVG XML
            svg_string = svg_content.decode('utf-8')
            root = ET.fromstring(svg_string)
            
            # Get SVG dimensions
            width = root.get('width')
            height = root.get('height')
            viewbox = root.get('viewBox')
            
            # Extract numeric dimensions
            actual_width, actual_height = self._extract_dimensions(width, height, viewbox)
            
            if actual_width is None or actual_height is None:
                return False, "Cannot determine SVG dimensions. Please ensure your SVG has width and height attributes."
            
            # Check dimensions
            if actual_width != self.required_width or actual_height != self.required_height:
                return False, f"SVG must be exactly {self.required_width}×{self.required_height} pixels. Current: {actual_width}×{actual_height}px"
            
            return True, "Valid SVG"
            
        except ET.ParseError as e:
            return False, "Invalid SVG file format"
        except UnicodeDecodeError:
            return False, "Unable to read SVG file"
        except Exception as e:
            logger.error(f"SVG validation error: {e}")
            return False, "SVG validation failed"
    
    def _extract_dimensions(self, width: str, height: str, viewbox: str) -> Tuple[Optional[int], Optional[int]]:
        """Extract numeric width and height from SVG attributes"""
        try:
            # Try direct width/height attributes first
            if width and height:
                w = self._parse_dimension(width)
                h = self._parse_dimension(height)
                if w is not None and h is not None:
                    return w, h
            
            # Fall back to viewBox if available
            if viewbox:
                parts = viewbox.split()
                if len(parts) == 4:
                    try:
                        return int(float(parts[2])), int(float(parts[3]))
                    except (ValueError, IndexError):
                        pass
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error extracting dimensions: {e}")
            return None, None
    
    def _parse_dimension(self, dim_str: str) -> Optional[int]:
        """Parse dimension string and return numeric value"""
        if not dim_str:
            return None
        
        try:
            # Remove common units
            dim_clean = dim_str.replace('px', '').replace('pt', '').replace('em', '').strip()
            return int(float(dim_clean))
        except (ValueError, AttributeError):
            return None

class TGSConverter:
    """Converts SVG files to TGS format"""
    
    def __init__(self):
        self.target_size = (512, 512)
        self.real_converter = SVGToTGSConverter()
    
    async def convert_svg_to_tgs(self, svg_content: bytes) -> Optional[bytes]:
        """
        Convert SVG content to TGS format using proper python-lottie converter
        
        Args:
            svg_content: SVG file content as bytes
            
        Returns:
            TGS file content as bytes, or None if conversion failed
        """
        try:
            # Save SVG to temporary file
            svg_fd, svg_path = tempfile.mkstemp(suffix='.svg')
            try:
                with os.fdopen(svg_fd, 'wb') as svg_file:
                    svg_file.write(svg_content)
                
                # Use the real converter
                tgs_path = await self.real_converter.convert(svg_path)
                
                # Read the generated TGS file
                with open(tgs_path, 'rb') as tgs_file:
                    tgs_content = tgs_file.read()
                
                # Clean up temporary files
                os.unlink(tgs_path)
                
                logger.info(f"Successfully converted SVG to TGS using python-lottie")
                return tgs_content
                
            finally:
                # Clean up SVG temp file
                if os.path.exists(svg_path):
                    os.unlink(svg_path)
            
        except Exception as e:
            logger.error(f"Real TGS conversion error: {e}")
            # Fallback to old method if real converter fails
            return await self._fallback_convert_svg_to_tgs(svg_content)
    
    async def _fallback_convert_svg_to_tgs(self, svg_content: bytes) -> Optional[bytes]:
        """Fallback conversion method if python-lottie fails"""
        try:
            # Create Lottie animation from SVG
            lottie_json = self._create_lottie_from_svg(svg_content)
            
            if not lottie_json:
                return None
            
            # Convert to TGS (compressed Lottie)
            tgs_content = self._create_tgs_from_lottie(lottie_json)
            
            return tgs_content
            
        except Exception as e:
            logger.error(f"Fallback TGS conversion error: {e}")
            return None
    
    def _create_lottie_from_svg(self, svg_content: bytes) -> Optional[dict]:
        """
        Create a Lottie animation JSON from SVG
        
        This creates a proper TGS by embedding the SVG as rasterized image
        Since proper SVG-to-Lottie vector conversion is complex, we use a hybrid approach
        """
        try:
            # Convert SVG to PNG for embedding (this ensures we preserve the actual SVG content)
            png_data = cairosvg.svg2png(
                bytestring=svg_content,
                output_width=512,
                output_height=512,
                background_color='white'  # Use white background to ensure visibility
            )
            
            # Convert PNG to base64 for embedding
            png_base64 = base64.b64encode(png_data).decode('utf-8')
            
            # Create proper Lottie JSON structure for TGS
            lottie_json = {
                "v": "5.7.4",       # Lottie version
                "fr": 30,           # Frame rate
                "ip": 0,            # In point
                "op": 60,           # Out point (2 seconds animation)
                "w": 512,           # Width
                "h": 512,           # Height
                "nm": "SVG Sticker",
                "ddd": 0,
                "assets": [
                    {
                        "id": "image_0",
                        "w": 512,
                        "h": 512,
                        "u": "",
                        "p": f"data:image/png;base64,{png_base64}",
                        "e": 1
                    }
                ],
                "layers": [
                    {
                        "ddd": 0,
                        "ind": 1,
                        "ty": 2,        # Image layer
                        "nm": "SVG Image",
                        "refId": "image_0",
                        "sr": 1,
                        "ks": {
                            "o": {"a": 0, "k": 100, "ix": 11},  # Keep fully opaque
                            "r": {"a": 0, "k": 0, "ix": 10},   # No rotation to keep image clear
                            "p": {"a": 0, "k": [256, 256, 0], "ix": 2},  # Centered position
                            "a": {"a": 0, "k": [256, 256, 0], "ix": 1},  # Centered anchor
                            "s": {"a": 0, "k": [100, 100, 100], "ix": 6} # Normal scale
                        },
                        "ao": 0,
                        "ip": 0,
                        "op": 60,
                        "st": 0,
                        "bm": 0
                    }
                ],
                "markers": []
            }
            
            return lottie_json
            
        except Exception as e:
            logger.error(f"Error creating Lottie from SVG: {e}")
            return None
    
    def _create_tgs_from_lottie(self, lottie_json: dict) -> bytes:
        """
        Create TGS file from Lottie JSON
        
        TGS is just a gzipped Lottie JSON file
        """
        try:
            # Convert to JSON string
            json_str = json.dumps(lottie_json, separators=(',', ':'), ensure_ascii=False)
            json_bytes = json_str.encode('utf-8')
            
            # Compress with gzip
            compressed_data = gzip.compress(json_bytes)
            
            return compressed_data
            
        except Exception as e:
            logger.error(f"Error creating TGS from Lottie: {e}")
            raise

class FileManager:
    """Manages temporary file operations"""
    
    @staticmethod
    def create_temp_file(content: bytes, suffix: str = '') -> str:
        """Create temporary file with content"""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_file.write(content)
                return temp_file.name
        except Exception as e:
            logger.error(f"Error creating temp file: {e}")
            raise
    
    @staticmethod
    def cleanup_temp_file(file_path: str):
        """Clean up temporary file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            logger.error(f"Error cleaning up temp file {file_path}: {e}")

class MessageFormatter:
    """Formats messages for the bot"""
    
    @staticmethod
    def format_error_message(filename: str, error: str) -> str:
        """Format error message for file processing"""
        return f"❌ **{filename}**: {error}"
    
    @staticmethod
    def format_processing_message(current: int, total: int) -> str:
        """Format processing progress message"""
        return f"🔄 Processing {current}/{total} file{'s' if total > 1 else ''}..."
    
    @staticmethod
    def format_completion_message(success_count: int, total_count: int) -> str:
        """Format completion message"""
        if success_count == total_count and success_count > 0:
            return f"✅ Done! Successfully converted {success_count}/{total_count} file{'s' if total_count > 1 else ''}."
        elif success_count > 0:
            return f"⚠️ Partially completed: {success_count}/{total_count} file{'s' if total_count > 1 else ''} converted."
        else:
            return "❌ No files were successfully converted."

class ValidationHelper:
    """Helper functions for validation"""
    
    @staticmethod
    def is_valid_file_size(file_size: int, max_size: int = 5242880) -> bool:
        """Check if file size is within limits"""
        return file_size <= max_size
    
    @staticmethod
    def is_svg_file(filename: str) -> bool:
        """Check if filename has SVG extension"""
        return filename.lower().endswith('.svg')
    
    @staticmethod
    def generate_tgs_filename(original_filename: str) -> str:
        """Generate TGS filename from original filename"""
        base_name = original_filename.rsplit('.', 1)[0]
        return f"{base_name}.tgs"
import json
import gzip
import tempfile
from io import BytesIO
from xml.etree import ElementTree as ET
import cairosvg
from PIL import Image

class SVGValidator:
    def __init__(self, required_width=512, required_height=512):
        self.required_width = required_width
        self.required_height = required_height
    
    def validate_svg(self, svg_content):
        """Validate SVG dimensions"""
        try:
            # Parse SVG
            root = ET.fromstring(svg_content)
            
            # Get dimensions
            width = root.get('width')
            height = root.get('height')
            
            if not width or not height:
                return False, "SVG missing width or height attributes"
            
            # Parse dimensions (remove 'px' if present)
            try:
                width_val = float(width.replace('px', ''))
                height_val = float(height.replace('px', ''))
            except ValueError:
                return False, "Invalid width or height values"
            
            # Check dimensions
            if width_val != self.required_width or height_val != self.required_height:
                return False, f"SVG must be exactly {self.required_width}×{self.required_height} pixels (got {width_val}×{height_val})"
            
            return True, "Valid"
            
        except ET.ParseError:
            return False, "Invalid SVG file format"
        except Exception as e:
            return False, f"SVG validation error: {str(e)}"

class TGSConverter:
    def __init__(self):
        pass
    
    async def convert_svg_to_tgs(self, svg_content):
        """Convert SVG to TGS format"""
        try:
            # Convert SVG to PNG
            png_data = cairosvg.svg2png(bytestring=svg_content, output_width=512, output_height=512)
            
            # Convert PNG to base64
            import base64
            png_base64 = base64.b64encode(png_data).decode('utf-8')
            
            # Create Lottie JSON structure
            lottie_json = {
                "v": "5.7.1",
                "fr": 60,
                "ip": 0,
                "op": 60,
                "w": 512,
                "h": 512,
                "nm": "SVG Animation",
                "ddd": 0,
                "assets": [
                    {
                        "id": "image_0",
                        "w": 512,
                        "h": 512,
                        "u": "",
                        "p": f"data:image/png;base64,{png_base64}",
                        "e": 1
                    }
                ],
                "layers": [
                    {
                        "ddd": 0,
                        "ind": 1,
                        "ty": 2,
                        "nm": "SVG Layer",
                        "refId": "image_0",
                        "sr": 1,
                        "ks": {
                            "o": {"a": 0, "k": 100, "ix": 11},
                            "r": {"a": 0, "k": 0, "ix": 10},
                            "p": {"a": 0, "k": [256, 256, 0], "ix": 2},
                            "a": {"a": 0, "k": [256, 256, 0], "ix": 1},
                            "s": {"a": 0, "k": [100, 100, 100], "ix": 6}
                        },
                        "ao": 0,
                        "ip": 0,
                        "op": 60,
                        "st": 0,
                        "bm": 0
                    }
                ],
                "markers": []
            }
            
            # Convert to JSON string
            json_string = json.dumps(lottie_json, separators=(',', ':'))
            
            # Compress with gzip
            compressed_data = gzip.compress(json_string.encode('utf-8'))
            
            return compressed_data
            
        except Exception as e:
            print(f"Conversion error: {e}")
            return None
