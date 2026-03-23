# -*- coding: utf-8 -*-
"""
Test suite for Image Upload Fix - Zektrix UK
Bug: 'nu merge sa incarc poze' (image uploads not working)
Root cause: upload saved files to /backend/routes/uploads/ but static file serving was from /backend/uploads/
Fix: Changed public.py to use UPLOAD_DIR from config.py

Testing:
- POST /api/upload/image - JPEG upload should return 200 with url and filename
- POST /api/upload/image - HEIC upload should convert to JPEG and return 200
- POST /api/upload/image - Should reject files over 10MB
- POST /api/upload/image - Should reject non-image files
- GET /api/uploads/{filename} - Uploaded file should be accessible (HTTP 200)
- POST /api/upload/image without auth - should return 401/403
"""
import pytest
import requests
import os
import io
from PIL import Image

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "contact@x67digital.com"
ADMIN_PASSWORD = "Credcada1."


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get headers with admin auth"""
    return {"Authorization": f"Bearer {admin_token}"}


def create_test_jpeg():
    """Create a valid JPEG image in memory"""
    img = Image.new('RGB', (100, 100), color='red')
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=85)
    buf.seek(0)
    return buf.getvalue()


def create_test_png():
    """Create a valid PNG image in memory"""
    img = Image.new('RGBA', (100, 100), color='blue')
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()


def create_test_heic():
    """Create a valid HEIC image in memory using pillow-heif"""
    try:
        import pillow_heif
        pillow_heif.register_heif_opener()
        
        # Create RGB image and convert to HEIC
        img = Image.new('RGB', (100, 100), color='green')
        buf = io.BytesIO()
        img.save(buf, format='HEIF', quality=85)
        buf.seek(0)
        return buf.getvalue()
    except Exception as e:
        pytest.skip(f"Could not create HEIC test image: {e}")


class TestImageUploadAuth:
    """Test authentication requirements for image upload"""
    
    def test_upload_without_auth_returns_401_or_403(self):
        """POST /api/upload/image without auth - should return 401/403"""
        jpeg_data = create_test_jpeg()
        files = {'file': ('test.jpg', io.BytesIO(jpeg_data), 'image/jpeg')}
        
        response = requests.post(f"{BASE_URL}/api/upload/image", files=files)
        
        assert response.status_code in [401, 403], \
            f"Expected 401/403 for unauthenticated request, got {response.status_code}: {response.text}"
        print(f"✓ Unauthenticated upload correctly rejected with {response.status_code}")


class TestJPEGUpload:
    """Test JPEG image upload"""
    
    def test_jpeg_upload_returns_200_with_url_and_filename(self, admin_headers):
        """POST /api/upload/image - JPEG upload should return 200 with url and filename"""
        jpeg_data = create_test_jpeg()
        files = {'file': ('test_image.jpg', io.BytesIO(jpeg_data), 'image/jpeg')}
        headers = {"Authorization": admin_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 200, f"JPEG upload failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "url" in data, "Response should contain 'url'"
        assert "filename" in data, "Response should contain 'filename'"
        assert data["filename"].endswith(('.jpg', '.jpeg')), f"Filename should be JPEG: {data['filename']}"
        assert data["url"].endswith(data["filename"]), "URL should end with filename"
        
        print(f"✓ JPEG uploaded successfully: {data['url']}")
        
        # Store for accessibility test
        pytest.jpeg_upload_url = data["url"]
        pytest.jpeg_upload_filename = data["filename"]


class TestPNGUpload:
    """Test PNG image upload"""
    
    def test_png_upload_returns_200(self, admin_headers):
        """POST /api/upload/image - PNG upload should return 200"""
        png_data = create_test_png()
        files = {'file': ('test_image.png', io.BytesIO(png_data), 'image/png')}
        headers = {"Authorization": admin_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 200, f"PNG upload failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "url" in data, "Response should contain 'url'"
        assert "filename" in data, "Response should contain 'filename'"
        
        print(f"✓ PNG uploaded successfully: {data['url']}")
        
        # Store for accessibility test
        pytest.png_upload_url = data["url"]
        pytest.png_upload_filename = data["filename"]


class TestHEICUpload:
    """Test HEIC (iPhone) image upload with conversion"""
    
    def test_heic_upload_converts_to_jpeg_and_returns_200(self, admin_headers):
        """POST /api/upload/image - HEIC upload should convert to JPEG and return 200"""
        try:
            heic_data = create_test_heic()
        except Exception as e:
            pytest.skip(f"HEIC test skipped: {e}")
            return
            
        files = {'file': ('iphone_photo.heic', io.BytesIO(heic_data), 'image/heic')}
        headers = {"Authorization": admin_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 200, f"HEIC upload failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "url" in data, "Response should contain 'url'"
        assert "filename" in data, "Response should contain 'filename'"
        # HEIC should be converted to JPEG
        assert data["filename"].endswith('.jpg'), f"HEIC should be converted to JPG, got: {data['filename']}"
        
        print(f"✓ HEIC uploaded and converted to JPEG: {data['url']}")
        
        # Store for accessibility test
        pytest.heic_upload_url = data["url"]
        pytest.heic_upload_filename = data["filename"]


class TestFileSizeLimit:
    """Test file size limit (10MB max)"""
    
    def test_upload_rejects_files_over_10mb(self, admin_headers):
        """POST /api/upload/image - Should reject files over 10MB"""
        # Create a large image (>10MB)
        # 4000x4000 RGB image is about 48MB uncompressed, but JPEG will be smaller
        # We'll create raw bytes to simulate a large file
        large_data = b'x' * (11 * 1024 * 1024)  # 11MB of data
        
        files = {'file': ('large_image.jpg', io.BytesIO(large_data), 'image/jpeg')}
        headers = {"Authorization": admin_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 400, \
            f"Expected 400 for oversized file, got {response.status_code}: {response.text}"
        
        # Check error message mentions size
        error_text = response.text.lower()
        assert "large" in error_text or "10mb" in error_text or "size" in error_text, \
            f"Error should mention file size: {response.text}"
        
        print(f"✓ Large file correctly rejected with 400")


class TestInvalidFileType:
    """Test rejection of non-image files"""
    
    def test_upload_rejects_text_files(self, admin_headers):
        """POST /api/upload/image - Should reject non-image files (text)"""
        files = {'file': ('document.txt', io.BytesIO(b'This is not an image'), 'text/plain')}
        headers = {"Authorization": admin_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 400, \
            f"Expected 400 for text file, got {response.status_code}: {response.text}"
        print(f"✓ Text file correctly rejected with 400")
    
    def test_upload_rejects_pdf_files(self, admin_headers):
        """POST /api/upload/image - Should reject non-image files (PDF)"""
        # Minimal PDF header
        pdf_data = b'%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF'
        files = {'file': ('document.pdf', io.BytesIO(pdf_data), 'application/pdf')}
        headers = {"Authorization": admin_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 400, \
            f"Expected 400 for PDF file, got {response.status_code}: {response.text}"
        print(f"✓ PDF file correctly rejected with 400")
    
    def test_upload_rejects_html_files(self, admin_headers):
        """POST /api/upload/image - Should reject non-image files (HTML)"""
        html_data = b'<html><body>Not an image</body></html>'
        files = {'file': ('page.html', io.BytesIO(html_data), 'text/html')}
        headers = {"Authorization": admin_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 400, \
            f"Expected 400 for HTML file, got {response.status_code}: {response.text}"
        print(f"✓ HTML file correctly rejected with 400")


class TestUploadedFileAccessibility:
    """Test that uploaded files are accessible via GET /api/uploads/{filename}
    
    THIS IS THE CRITICAL TEST FOR THE BUG FIX:
    The bug was that files were saved to /backend/routes/uploads/ but served from /backend/uploads/
    """
    
    def test_uploaded_jpeg_is_accessible(self, admin_headers):
        """GET /api/uploads/{filename} - Uploaded JPEG file should be accessible (HTTP 200)"""
        # First upload a file
        jpeg_data = create_test_jpeg()
        files = {'file': ('accessibility_test.jpg', io.BytesIO(jpeg_data), 'image/jpeg')}
        headers = {"Authorization": admin_headers["Authorization"]}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        
        data = upload_response.json()
        filename = data["filename"]
        
        # Now try to access the uploaded file
        # The URL should be /api/uploads/{filename}
        access_url = f"{BASE_URL}/api/uploads/{filename}"
        access_response = requests.get(access_url)
        
        assert access_response.status_code == 200, \
            f"Uploaded file not accessible at {access_url}: {access_response.status_code}"
        
        # Verify it's actually an image
        content_type = access_response.headers.get('content-type', '')
        assert 'image' in content_type.lower() or len(access_response.content) > 0, \
            f"Response doesn't appear to be an image: {content_type}"
        
        print(f"✓ Uploaded file is accessible at {access_url}")
    
    def test_uploaded_png_is_accessible(self, admin_headers):
        """GET /api/uploads/{filename} - Uploaded PNG file should be accessible (HTTP 200)"""
        # First upload a file
        png_data = create_test_png()
        files = {'file': ('accessibility_test.png', io.BytesIO(png_data), 'image/png')}
        headers = {"Authorization": admin_headers["Authorization"]}
        
        upload_response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert upload_response.status_code == 200, f"Upload failed: {upload_response.text}"
        
        data = upload_response.json()
        filename = data["filename"]
        
        # Now try to access the uploaded file
        access_url = f"{BASE_URL}/api/uploads/{filename}"
        access_response = requests.get(access_url)
        
        assert access_response.status_code == 200, \
            f"Uploaded file not accessible at {access_url}: {access_response.status_code}"
        
        print(f"✓ Uploaded PNG file is accessible at {access_url}")
    
    def test_nonexistent_file_returns_404(self):
        """GET /api/uploads/{filename} - Non-existent file should return 404"""
        access_url = f"{BASE_URL}/api/uploads/nonexistent_file_12345.jpg"
        access_response = requests.get(access_url)
        
        assert access_response.status_code == 404, \
            f"Expected 404 for non-existent file, got {access_response.status_code}"
        
        print(f"✓ Non-existent file correctly returns 404")


class TestWebPAndGIFUpload:
    """Test WebP and GIF image uploads (also allowed)"""
    
    def test_webp_upload_returns_200(self, admin_headers):
        """POST /api/upload/image - WebP upload should return 200"""
        # Create a WebP image
        img = Image.new('RGB', (100, 100), color='yellow')
        buf = io.BytesIO()
        img.save(buf, format='WEBP', quality=85)
        buf.seek(0)
        webp_data = buf.getvalue()
        
        files = {'file': ('test_image.webp', io.BytesIO(webp_data), 'image/webp')}
        headers = {"Authorization": admin_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 200, f"WebP upload failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "url" in data, "Response should contain 'url'"
        assert "filename" in data, "Response should contain 'filename'"
        
        print(f"✓ WebP uploaded successfully: {data['url']}")
    
    def test_gif_upload_returns_200(self, admin_headers):
        """POST /api/upload/image - GIF upload should return 200"""
        # Create a GIF image
        img = Image.new('P', (100, 100), color=1)
        buf = io.BytesIO()
        img.save(buf, format='GIF')
        buf.seek(0)
        gif_data = buf.getvalue()
        
        files = {'file': ('test_image.gif', io.BytesIO(gif_data), 'image/gif')}
        headers = {"Authorization": admin_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 200, f"GIF upload failed: {response.status_code} - {response.text}"
        
        data = response.json()
        assert "url" in data, "Response should contain 'url'"
        assert "filename" in data, "Response should contain 'filename'"
        
        print(f"✓ GIF uploaded successfully: {data['url']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
