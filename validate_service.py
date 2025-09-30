#!/usr/bin/env python3
"""
Basic validation script to test the news scraper service without external dependencies.
"""

import sys
import os
import tempfile

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all core modules can be imported."""
    print("Testing imports...")
    
    try:
        from app.core.config import settings
        print("✓ Config module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import config: {e}")
        return False
    
    try:
        from app.core.logging import get_logger
        logger = get_logger("test")
        print("✓ Logging module imported successfully")
    except Exception as e:
        print(f"✗ Failed to import logging: {e}")
        return False
    
    try:
        from app.api.schemas import ArticleCreate, ArticleResponse
        print("✓ API schemas imported successfully")
    except Exception as e:
        print(f"✗ Failed to import schemas: {e}")
        return False
    
    try:
        from app.models.article import Article, Base
        print("✓ Models imported successfully")
    except Exception as e:
        print(f"✗ Failed to import models: {e}")
        return False
    
    return True


def test_pydantic_models():
    """Test Pydantic model validation."""
    print("\nTesting Pydantic models...")
    
    try:
        from app.api.schemas import ArticleCreate
        
        # Test valid article creation
        article_data = {
            "title": "Test Article",
            "url": "https://example.com/test",
            "content": "Test content",
            "source": "Test Source"
        }
        article = ArticleCreate(**article_data)
        print("✓ ArticleCreate validation works")
        
        # Test required fields
        try:
            invalid_article = ArticleCreate(title="Test")
            print("✗ Validation should have failed for missing required fields")
            return False
        except Exception:
            print("✓ Required field validation works")
        
        return True
        
    except Exception as e:
        print(f"✗ Pydantic model test failed: {e}")
        return False


def test_configuration():
    """Test configuration loading."""
    print("\nTesting configuration...")
    
    try:
        from app.core.config import settings
        
        # Test default values
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'api_host')
        assert hasattr(settings, 'api_port')
        assert hasattr(settings, 'news_sources')
        print("✓ Configuration has all required fields")
        
        # Test that news_sources is a list
        assert isinstance(settings.news_sources, list)
        print("✓ News sources is properly configured as list")
        
        return True
        
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_logging():
    """Test logging functionality."""
    print("\nTesting logging...")
    
    try:
        from app.core.logging import get_logger
        
        logger = get_logger("test")
        logger.info("Test log message", test_field="test_value")
        print("✓ Structured logging works")
        
        return True
        
    except Exception as e:
        print(f"✗ Logging test failed: {e}")
        return False


def test_docker_config():
    """Test Docker configuration files."""
    print("\nTesting Docker configuration...")
    
    try:
        # Check if Dockerfile exists
        dockerfile_path = os.path.join(project_root, "Dockerfile")
        if not os.path.exists(dockerfile_path):
            print("✗ Dockerfile not found")
            return False
        print("✓ Dockerfile exists")
        
        # Check if docker-compose.yml exists
        compose_path = os.path.join(project_root, "docker-compose.yml")
        if not os.path.exists(compose_path):
            print("✗ docker-compose.yml not found")
            return False
        print("✓ docker-compose.yml exists")
        
        return True
        
    except Exception as e:
        print(f"✗ Docker config test failed: {e}")
        return False


def test_project_structure():
    """Test project structure."""
    print("\nTesting project structure...")
    
    required_dirs = [
        "app",
        "app/api",
        "app/core", 
        "app/db",
        "app/models",
        "app/scraper",
        "tests",
        "alembic"
    ]
    
    required_files = [
        "requirements.txt",
        "pyproject.toml",
        ".env.example",
        "README.md",
        "alembic.ini"
    ]
    
    try:
        for dir_path in required_dirs:
            full_path = os.path.join(project_root, dir_path)
            if not os.path.isdir(full_path):
                print(f"✗ Required directory missing: {dir_path}")
                return False
        print("✓ All required directories exist")
        
        for file_path in required_files:
            full_path = os.path.join(project_root, file_path)
            if not os.path.isfile(full_path):
                print(f"✗ Required file missing: {file_path}")
                return False
        print("✓ All required files exist")
        
        return True
        
    except Exception as e:
        print(f"✗ Project structure test failed: {e}")
        return False


def main():
    """Run all validation tests."""
    print("🚀 Running News Scraper Service Validation Tests\n")
    
    tests = [
        test_project_structure,
        test_imports,
        test_configuration,
        test_pydantic_models,
        test_logging,
        test_docker_config,
    ]
    
    passed = 0
    total = len(tests)
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ Test {test_func.__name__} failed\n")
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}\n")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All validation tests passed! The service structure is correct.")
        return 0
    else:
        print("❌ Some tests failed. Please check the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())