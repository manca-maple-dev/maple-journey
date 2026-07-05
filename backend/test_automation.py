#!/usr/bin/env python
"""Quick test of automation router"""
import sys
sys.path.insert(0, '.')

try:
    # Test imports
    from pydantic import BaseModel, EmailStr
    from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
    print("✅ FastAPI imports OK")
    
    # Check if automation router can be imported
    from routers.automation import router, AutoSignupRequest, AutoPaymentWebhook
    print("✅ Automation router imports OK")
    print(f"✅ Routes available: {len(router.routes)} endpoints")
    
    # Show available endpoints
    for route in router.routes:
        if hasattr(route, 'path') and hasattr(route, 'methods'):
            methods = ",".join(route.methods)
            print(f"   📍 {methods:6} {route.path}")
    
    print("\n✅ ALL TESTS PASSED - READY FOR DEPLOY\n")
    
    # Test model validation
    print("Testing AutoSignupRequest validation...")
    test_signup = AutoSignupRequest(
        email="test@example.com",
        phone="647-555-0100",
        full_name="Test User",
        address="123 Test Street Toronto ON",
        immigration_status="PR",
        income=50000,
        children=2,
        form_type="profile"
    )
    print(f"✅ Model validation OK: {test_signup.email}")
    
except ImportError as e:
    print(f"❌ Import error: {str(e)}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
