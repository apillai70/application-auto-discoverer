#!/usr/bin/env python3
"""
Test script for LucidChart and PDF generation endpoints
Run this script to systematically test your diagram generation
"""

import requests
import json
import time
from pathlib import Path

class EndpointTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
    
    def test_service_status(self):
        """Test if the service is running"""
        print("🔍 Testing service status...")
        try:
            response = self.session.get(f"{self.base_url}/api/v1/archetype/health")
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Service is running - Status: {data.get('status')}")
                print(f"   Services available: {data.get('services', {})}")
                return True
            else:
                print(f"❌ Service health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Cannot connect to service: {e}")
            return False
    
    def test_lucid_generation(self, archetype="three_tier", app_name="TestBankingApp"):
        """Test LucidChart file generation"""
        print(f"\n🎨 Testing LucidChart generation for {archetype}...")
        
        try:
            # Test using the main diagram endpoint
            payload = {
                "archetype": archetype,
                "output_formats": ["lucid"],
                "application_data": {
                    "applications": [
                        {"id": "web1", "name": f"{app_name} Frontend", "type": "web"},
                        {"id": "api1", "name": f"{app_name} API", "type": "api"},
                        {"id": "db1", "name": f"{app_name} DB", "type": "database"}
                    ]
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/archetype/generate-diagram",
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                print(f"✅ LucidChart generation started - Job ID: {job_id}")
                
                # Wait for completion
                return self.wait_for_job_completion(job_id, "LucidChart")
            else:
                print(f"❌ LucidChart generation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ LucidChart test error: {e}")
            return False
    
    def test_pdf_generation(self, archetype="microservices", app_name="TestBankingApp"):
        """Test PDF file generation"""
        print(f"\n📄 Testing PDF generation for {archetype}...")
        
        try:
            # Test using practical diagrams endpoint
            params = {
                "archetype": archetype,
                "app_name": app_name
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/archetype/generate-practical-diagrams",
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                print(f"✅ PDF generation started - Job ID: {job_id}")
                
                # Wait for completion
                return self.wait_for_job_completion(job_id, "PDF")
            else:
                print(f"❌ PDF generation failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ PDF test error: {e}")
            return False
    
    def test_simple_lucid_endpoint(self, archetype="three_tier"):
        """Test the simple LucidChart test endpoint if available"""
        print(f"\n🧪 Testing simple LucidChart endpoint for {archetype}...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/archetype/test-lucid/{archetype}",
                params={"app_name": "SimpleTestApp"}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    print(f"✅ Simple LucidChart test successful")
                    print(f"   File: {data.get('filename')}")
                    print(f"   Size: {data.get('file_size')} bytes")
                    
                    # Try to download the file
                    return self.test_file_download(data.get('filename'))
                else:
                    print(f"❌ Simple LucidChart test failed: {data.get('error')}")
                    return False
            else:
                print(f"⚠️  Simple LucidChart endpoint not available: {response.status_code}")
                return None  # Endpoint doesn't exist
                
        except Exception as e:
            print(f"❌ Simple LucidChart test error: {e}")
            return False
    
    def wait_for_job_completion(self, job_id, job_type, max_wait=60):
        """Wait for a job to complete"""
        print(f"   Waiting for {job_type} job {job_id} to complete...")
        
        for i in range(max_wait):
            try:
                response = self.session.get(
                    f"{self.base_url}/api/v1/archetype/jobs/{job_id}"
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    progress = data.get("progress", 0)
                    
                    if status == "completed":
                        print(f"✅ {job_type} job completed successfully!")
                        files = data.get("result", {}).get("files", [])
                        for file_info in files:
                            print(f"   Generated: {file_info.get('filename')} ({file_info.get('file_size')} bytes)")
                            
                            # Test downloading the first file
                            if files:
                                return self.test_file_download(files[0].get('filename'))
                        return True
                        
                    elif status == "error":
                        print(f"❌ {job_type} job failed: {data.get('error')}")
                        return False
                        
                    elif status in ["processing", "queued"]:
                        print(f"   Progress: {progress}% - {data.get('message', 'Processing...')}")
                        time.sleep(1)
                        continue
                        
                else:
                    print(f"❌ Cannot check job status: {response.status_code}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error checking job status: {e}")
                return False
        
        print(f"❌ {job_type} job timed out after {max_wait} seconds")
        return False
    
    def test_file_download(self, filename):
        """Test downloading a generated file"""
        if not filename:
            return False
            
        print(f"   Testing download of {filename}...")
        try:
            response = self.session.get(
                f"{self.base_url}/api/v1/archetype/download/{filename}"
            )
            
            if response.status_code == 200:
                file_size = len(response.content)
                print(f"✅ File downloaded successfully ({file_size} bytes)")
                
                # Save to downloads directory for inspection
                downloads_dir = Path("downloads")
                downloads_dir.mkdir(exist_ok=True)
                
                file_path = downloads_dir / filename
                file_path.write_bytes(response.content)
                print(f"   Saved to: {file_path}")
                
                # Basic content validation
                return self.validate_file_content(file_path)
                
            else:
                print(f"❌ File download failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Download error: {e}")
            return False
    
    def validate_file_content(self, file_path):
        """Basic validation of generated file content"""
        try:
            if file_path.suffix == '.lucid':
                # Check if it's valid XML-like content
                content = file_path.read_text()
                if '<?xml' in content and '<lucidchart' in content:
                    print(f"✅ LucidChart file appears valid (XML structure found)")
                    return True
                else:
                    print(f"⚠️  LucidChart file may be invalid (no XML structure)")
                    return False
                    
            elif file_path.suffix == '.pdf':
                # Check if it starts with PDF header
                content = file_path.read_bytes()
                if content.startswith(b'%PDF'):
                    print(f"✅ PDF file appears valid (PDF header found)")
                    return True
                else:
                    print(f"⚠️  PDF file may be invalid (no PDF header)")
                    return False
                    
            else:
                print(f"✅ File saved (content validation not implemented for {file_path.suffix})")
                return True
                
        except Exception as e:
            print(f"⚠️  Could not validate file content: {e}")
            return False
    
    def test_all_archetypes(self):
        """Test generation for all archetype types"""
        archetypes = [
            "three_tier", "microservices", "monolithic", 
            "event_driven", "serverless", "client_server"
        ]
        
        print(f"\n🔄 Testing all archetypes...")
        results = {}
        
        for archetype in archetypes:
            print(f"\n--- Testing {archetype} ---")
            lucid_result = self.test_lucid_generation(archetype, f"Test{archetype.title()}App")
            time.sleep(2)  # Brief pause between tests
            
            results[archetype] = {
                "lucid": lucid_result
            }
        
        return results
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 Starting comprehensive endpoint testing...\n")
        
        # Check service status
        if not self.test_service_status():
            print("❌ Service is not available. Please start your FastAPI server first.")
            return False
        
        time.sleep(1)
        
        # Test individual endpoints
        lucid_result = self.test_lucid_generation()
        time.sleep(2)
        
        pdf_result = self.test_pdf_generation() 
        time.sleep(2)
        
        # Test simple endpoint if available
        simple_result = self.test_simple_lucid_endpoint()
        
        # Summary
        print(f"\n📊 Test Summary:")
        print(f"   LucidChart Generation: {'✅ PASS' if lucid_result else '❌ FAIL'}")
        print(f"   PDF Generation: {'✅ PASS' if pdf_result else '❌ FAIL'}")
        print(f"   Simple Test Endpoint: {'✅ PASS' if simple_result else '⚠️  NOT AVAILABLE' if simple_result is None else '❌ FAIL'}")
        
        success_count = sum([lucid_result, pdf_result, bool(simple_result)])
        total_tests = 2 + (1 if simple_result is not None else 0)
        
        print(f"\n🎯 Overall Result: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("🎉 All tests passed! Your endpoints are working correctly.")
        else:
            print("🔧 Some tests failed. Check the error messages above for troubleshooting.")
            
        return success_count == total_tests

if __name__ == "__main__":
    tester = EndpointTester()
    tester.run_comprehensive_test()