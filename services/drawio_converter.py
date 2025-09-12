"""
Draw.io to PDF Converter using Playwright
High-quality PDF generation from Draw.io files
"""

import asyncio
import logging
import tempfile
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

class DrawioPDFConverter:
    """Convert Draw.io files to PDF using headless browser"""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self._initialized = False
        self._lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize Playwright browser (thread-safe)"""
        async with self._lock:
            if self._initialized:
                return
                
            try:
                from playwright.async_api import async_playwright
                
                self.playwright = await async_playwright().start()
                # Use Chromium for better PDF generation
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox', 
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor'
                    ]
                )
                self._initialized = True
                logger.info("DrawIO PDF converter initialized successfully")
                
            except ImportError:
                logger.error("Playwright not installed. Run: pip install playwright && playwright install chromium")
                raise
            except Exception as e:
                logger.error(f"Failed to initialize Playwright: {e}")
                raise
    
    async def convert_to_pdf_direct(self, drawio_file_path: str, output_pdf_path: str = None) -> Optional[str]:
        """Convert Draw.io file directly to PDF using embedded viewer"""
        try:
            await self.initialize()
            
            drawio_path = Path(drawio_file_path)
            if not drawio_path.exists():
                raise FileNotFoundError(f"Draw.io file not found: {drawio_file_path}")
            
            if not output_pdf_path:
                output_pdf_path = str(drawio_path.with_suffix('.pdf'))
            
            # Read the Draw.io content
            drawio_content = drawio_path.read_text(encoding='utf-8')
            
            # Create HTML with embedded Draw.io viewer
            html_content = self._create_viewer_html(drawio_content, drawio_path.stem)
            
            # Create temporary HTML file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as temp_html:
                temp_html.write(html_content)
                temp_html_path = temp_html.name
            
            try:
                page = await self.browser.new_page()
                
                # Set a larger viewport for better diagram rendering
                await page.set_viewport_size({"width": 1200, "height": 900})
                
                # Navigate to the HTML file
                await page.goto(f'file://{Path(temp_html_path).absolute().as_uri()}')
                
                # Wait for diagram to render completely
                await page.wait_for_timeout(5000)  # 5 seconds for complex diagrams
                
                # Wait for the viewer to be loaded
                try:
                    await page.wait_for_selector('#diagram-container', timeout=10000)
                except:
                    logger.warning("Diagram container not found, continuing anyway...")
                
                # Generate PDF with optimized settings
                pdf_options = {
                    'path': output_pdf_path,
                    'format': 'A4',
                    'print_background': True,
                    'margin': {
                        'top': '0.5in',
                        'right': '0.5in',
                        'bottom': '0.5in',
                        'left': '0.5in'
                    },
                    'prefer_css_page_size': True
                }
                
                await page.pdf(**pdf_options)
                
                logger.info(f"Successfully created PDF: {output_pdf_path}")
                return output_pdf_path
                
            finally:
                await page.close()
                Path(temp_html_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Error in direct PDF conversion: {e}")
            return None
    
    async def convert_to_pdf_web(self, drawio_file_path: str, output_pdf_path: str = None) -> Optional[str]:
        """Convert using draw.io web app (alternative method)"""
        try:
            await self.initialize()
            
            drawio_path = Path(drawio_file_path)
            if not output_pdf_path:
                output_pdf_path = str(drawio_path.with_suffix('.pdf'))
            
            # Read Draw.io content
            drawio_content = drawio_path.read_text(encoding='utf-8')
            
            page = await self.browser.new_page()
            
            try:
                # Navigate to draw.io web app with embed mode
                await page.goto('https://app.diagrams.net/?embed=1&ui=atlas&spin=1&modified=unsavedChanges&proto=json', 
                               wait_until='networkidle', timeout=30000)
                
                # Wait for the app to load
                await page.wait_for_selector('.geEditor', timeout=15000)
                
                # Load the diagram data
                await page.evaluate(f"""
                    // Function to load diagram in draw.io
                    const data = `{drawio_content}`;
                    
                    // Try to set the diagram data
                    if (window.EditorUi && window.EditorUi.prototype.setGraphXml) {{
                        const editorUi = window.editorUi || window.app;
                        if (editorUi && editorUi.editor) {{
                            try {{
                                editorUi.editor.setGraphXml(data);
                                console.log('Diagram loaded successfully');
                            }} catch (e) {{
                                console.error('Failed to load diagram:', e);
                            }}
                        }}
                    }}
                """)
                
                # Wait for diagram to render
                await page.wait_for_timeout(3000)
                
                # Generate PDF
                await page.pdf(
                    path=output_pdf_path,
                    format='A4',
                    print_background=True,
                    margin={'top': '0.5in', 'right': '0.5in', 'bottom': '0.5in', 'left': '0.5in'}
                )
                
                logger.info(f"Successfully created web-based PDF: {output_pdf_path}")
                return output_pdf_path
                
            finally:
                await page.close()
                
        except Exception as e:
            logger.error(f"Error in web-based PDF conversion: {e}")
            return None
    
    def _create_viewer_html(self, drawio_content: str, diagram_name: str) -> str:
        """Create HTML with embedded Draw.io viewer"""
        # Escape the XML content for embedding in JavaScript
        escaped_content = drawio_content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r')
        
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{diagram_name} - Architecture Diagram</title>
    <style>
        body {{ 
            margin: 0; 
            padding: 20px; 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 20px;
            padding: 20px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            color: #2c3e50;
            margin: 0;
            font-size: 24px;
        }}
        .header p {{
            color: #7f8c8d;
            margin: 10px 0 0 0;
        }}
        #diagram-container {{ 
            width: 100%; 
            height: 800px; 
            border: 2px solid #e1e8ed;
            border-radius: 8px;
            background: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .loading {{
            display: flex;
            justify-content: center;
            align-items: center;
            height: 400px;
            font-size: 18px;
            color: #7f8c8d;
        }}
        @media print {{
            body {{ 
                margin: 0; 
                padding: 10px;
                background: white;
            }}
            .header {{ 
                box-shadow: none;
                border: none;
                margin-bottom: 10px;
            }}
            #diagram-container {{ 
                border: 1px solid #ccc;
                box-shadow: none;
                height: auto;
                min-height: 600px;
            }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>{diagram_name.replace('_', ' ').title()}</h1>
        <p>Architecture Diagram - Generated {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    
    <div id="diagram-container">
        <div class="loading">Loading diagram...</div>
    </div>
    
    <script src="https://viewer.diagrams.net/js/viewer-static.min.js"></script>
    <script>
        document.addEventListener('DOMContentLoaded', function() {{
            try {{
                const diagramData = `{escaped_content}`;
                const container = document.getElementById('diagram-container');
                
                // Clear loading message
                container.innerHTML = '';
                
                // Create the viewer
                const viewer = new GraphViewer(container);
                
                // Configure viewer options
                viewer.lightbox = false;
                viewer.editBlankUrl = 'https://app.diagrams.net/';
                viewer.xmlDocument = diagramData;
                
                // Load the diagram
                viewer.init();
                
                console.log('Diagram viewer initialized successfully');
                
                // Optional: Auto-fit the diagram
                setTimeout(() => {{
                    if (viewer.graph && viewer.graph.fit) {{
                        viewer.graph.fit();
                        viewer.graph.center();
                    }}
                }}, 1000);
                
            }} catch (error) {{
                console.error('Error loading diagram:', error);
                document.getElementById('diagram-container').innerHTML = 
                    '<div class="loading" style="color: #e74c3c;">Error loading diagram: ' + error.message + '</div>';
            }}
        }});
        
        // Handle print optimization
        window.addEventListener('beforeprint', function() {{
            document.body.style.background = 'white';
        }});
    </script>
</body>
</html>
        """
    
    async def cleanup(self):
        """Clean up browser resources"""
        async with self._lock:
            try:
                if self.browser:
                    await self.browser.close()
                if self.playwright:
                    await self.playwright.stop()
                self._initialized = False
                logger.info("DrawIO PDF converter cleaned up")
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

# Global converter instance
pdf_converter = DrawioPDFConverter()

async def convert_drawio_to_pdf_background(drawio_file_path: str, job_id: str):
    """Background task for Draw.io to PDF conversion"""
    try:
        # Import here to avoid circular imports
        import sys
        if 'routers.archetype_router' in sys.modules:
            from routers.archetype_router import job_manager
        else:
            # Fallback for testing
            logger.warning("job_manager not available, running in test mode")
            job_manager = None
        
        if job_manager:
            job_manager.update_job(job_id, status="processing", progress=30, message="Converting Draw.io to PDF...")
        
        # Try direct conversion first (usually better quality)
        output_pdf_path = await pdf_converter.convert_to_pdf_direct(drawio_file_path)
        
        # Fallback to web-based conversion if direct fails
        if not output_pdf_path:
            logger.info("Direct conversion failed, trying web-based conversion...")
            output_pdf_path = await pdf_converter.convert_to_pdf_web(drawio_file_path)
        
        if output_pdf_path and Path(output_pdf_path).exists():
            file_size = Path(output_pdf_path).stat().st_size
            if job_manager:
                job_manager.update_job(
                    job_id,
                    status="completed",
                    progress=100,
                    message="High-quality PDF conversion completed",
                    result={
                        "pdf_path": output_pdf_path, 
                        "file_size": file_size,
                        "conversion_method": "playwright"
                    }
                )
            logger.info(f"PDF conversion completed: {output_pdf_path} ({file_size} bytes)")
        else:
            raise Exception("PDF conversion failed - no output file created")
            
    except Exception as e:
        logger.error(f"Background PDF conversion failed: {e}")
        if job_manager:
            job_manager.update_job(
                job_id,
                status="error",
                error=str(e),
                message="PDF conversion failed"
            )

# Utility function for synchronous usage (for testing)
def convert_drawio_to_pdf_sync(drawio_file_path: str, output_pdf_path: str = None) -> Optional[str]:
    """Synchronous wrapper for testing"""
    async def _convert():
        return await pdf_converter.convert_to_pdf_direct(drawio_file_path, output_pdf_path)
    
    return asyncio.run(_convert())

# Cleanup function for graceful shutdown
async def cleanup_converter():
    """Cleanup the global converter"""
    await pdf_converter.cleanup()