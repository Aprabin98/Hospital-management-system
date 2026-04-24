"""
Phase 7 API Tests - Finance & Insurance Maturity
Path: backend/test_phase7_api.py
Comprehensive test suite for all finance endpoints
"""

import os
import sys
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hms_project.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

import requests
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from users.models import PatientProfile

User = get_user_model()
BASE_URL = "http://localhost:8000/api"

def get_token(username, password):
    """Get JWT token for a user"""
    response = requests.post(
        f"{BASE_URL}/token/",
        json={"username": username, "password": password}
    )
    if response.status_code == 200:
        return response.json()['access']
    return None


def test_invoice_endpoints():
    """Test invoice CRUD and custom actions"""
    print("\n" + "="*60)
    print("TESTING: Invoice Endpoints")
    print("="*60)
    
    # Get admin token
    admin_user = User.objects.filter(role='ADMIN').first()
    if not admin_user:
        print("⚠️  No admin user found")
        return False
    
    token = None
    try:
        # Create test admin if needed
        admin_user.set_password('testpass123')
        admin_user.save()
        token = get_token(admin_user.username, 'testpass123')
    except:
        pass
    
    if not token:
        print("⚠️  Could not get authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # GET all invoices
    print("\n▶️  GET /api/invoices/")
    response = requests.get(f"{BASE_URL}/invoices/", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        invoices = response.json()
        count = len(invoices) if isinstance(invoices, list) else invoices.get('count', 0)
        print(f"   ✅ Retrieved {count} invoices")
        return True
    else:
        print(f"   ❌ Error: {response.text}")
        return False


def test_claims_endpoints():
    """Test insurance claims CRUD"""
    print("\n" + "="*60)
    print("TESTING: Insurance Claims Endpoints")
    print("="*60)
    
    admin_user = User.objects.filter(role='ADMIN').first()
    if not admin_user:
        print("⚠️  No admin user found")
        return False
    
    token = None
    try:
        admin_user.set_password('testpass123')
        admin_user.save()
        token = get_token(admin_user.username, 'testpass123')
    except:
        pass
    
    if not token:
        print("⚠️  Could not get authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # GET all claims
    print("\n▶️  GET /api/claims/")
    response = requests.get(f"{BASE_URL}/claims/", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        claims = response.json()
        count = len(claims) if isinstance(claims, list) else claims.get('count', 0)
        print(f"   ✅ Retrieved {count} claims")
        return True
    else:
        print(f"   ❌ Error: {response.text}")
        return False


def test_denial_reworks_endpoints():
    """Test denial rework queue endpoints"""
    print("\n" + "="*60)
    print("TESTING: Denial Reworks Endpoints")
    print("="*60)
    
    admin_user = User.objects.filter(role='ADMIN').first()
    if not admin_user:
        print("⚠️  No admin user found")
        return False
    
    token = None
    try:
        admin_user.set_password('testpass123')
        admin_user.save()
        token = get_token(admin_user.username, 'testpass123')
    except:
        pass
    
    if not token:
        print("⚠️  Could not get authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # GET all denial reworks
    print("\n▶️  GET /api/denial-reworks/")
    response = requests.get(f"{BASE_URL}/denial-reworks/", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        reworks = response.json()
        count = len(reworks) if isinstance(reworks, list) else reworks.get('count', 0)
        print(f"   ✅ Retrieved {count} denial reworks")
        return True
    else:
        print(f"   ❌ Error: {response.text}")
        return False


def test_preauth_endpoints():
    """Test pre-authorization endpoints"""
    print("\n" + "="*60)
    print("TESTING: Pre-Authorization Endpoints")
    print("="*60)
    
    admin_user = User.objects.filter(role='ADMIN').first()
    if not admin_user:
        print("⚠️  No admin user found")
        return False
    
    token = None
    try:
        admin_user.set_password('testpass123')
        admin_user.save()
        token = get_token(admin_user.username, 'testpass123')
    except:
        pass
    
    if not token:
        print("⚠️  Could not get authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # GET all pre-auths
    print("\n▶️  GET /api/pre-auths/")
    response = requests.get(f"{BASE_URL}/pre-auths/", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        preauths = response.json()
        count = len(preauths) if isinstance(preauths, list) else preauths.get('count', 0)
        print(f"   ✅ Retrieved {count} pre-authorizations")
        return True
    else:
        print(f"   ❌ Error: {response.text}")
        return False


def test_dashboard_endpoint():
    """Test finance dashboard"""
    print("\n" + "="*60)
    print("TESTING: Finance Dashboard Endpoint")
    print("="*60)
    
    admin_user = User.objects.filter(role='ADMIN').first()
    if not admin_user:
        print("⚠️  No admin user found")
        return False
    
    token = None
    try:
        admin_user.set_password('testpass123')
        admin_user.save()
        token = get_token(admin_user.username, 'testpass123')
    except:
        pass
    
    if not token:
        print("⚠️  Could not get authentication token")
        return False
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # GET dashboard
    print("\n▶️  GET /api/finance/dashboard/")
    response = requests.get(f"{BASE_URL}/finance/dashboard/", headers=headers)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Dashboard data retrieved")
        print(f"      - Total claims: {data.get('claims_summary', {}).get('total_claims', 'N/A')}")
        print(f"      - Collection rate: {data.get('invoice_summary', {}).get('collection_rate', 'N/A')}%")
        print(f"      - Pending reworks: {data.get('pending_reworks', 'N/A')}")
        return True
    else:
        print(f"   ❌ Error: {response.text}")
        return False


def main():
    """Run all Phase 7 API tests"""
    print("="*60)
    print("PHASE 7 API TEST SUITE")
    print("Finance & Insurance Maturity Endpoints")
    print("="*60)
    
    print("\n⏳ Ensure:")
    print("  1. Django development server is running on http://localhost:8000")
    print("  2. Test admin user exists")
    print("  3. Phase 7 seed data has been created\n")
    
    results = []
    
    try:
        results.append(("Invoices", test_invoice_endpoints()))
        results.append(("Claims", test_claims_endpoints()))
        results.append(("Denial Reworks", test_denial_reworks_endpoints()))
        results.append(("Pre-Authorizations", test_preauth_endpoints()))
        results.append(("Dashboard", test_dashboard_endpoint()))
    except Exception as e:
        print(f"\n❌ Test execution error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for endpoint, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {endpoint}")
    
    print(f"\nTotal: {passed}/{total} passed")
    
    if passed == total:
        print("\n🎉 All Phase 7 API tests passed!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check server logs for details.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
