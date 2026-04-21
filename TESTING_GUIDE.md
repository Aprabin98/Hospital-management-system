# Hospital Management System - Quick Testing Guide

## 🚀 Quick Start

### Prerequisites
- Django backend running on `http://localhost:8000`
- Next.js frontend running on `http://localhost:3000`
- User logged in with valid JWT token

---

## 🧪 Testing Workflow

### 1. Start Backend Server
```bash
cd backend
python manage.py runserver
# Server runs on http://localhost:8000
```

### 2. Start Frontend Server
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:3000
```

### 3. Login to System
1. Navigate to `http://localhost:3000/login`
2. Enter credentials (doctor/admin/patient email and password)
3. Click "Sign In"
4. JWT token is stored in localStorage

---

## 📋 Testing Checklist

### Dashboard Page (/dashboard)
- [ ] Page loads with all stats cards
- [ ] No console errors
- [ ] All 8 feature cards are visible
- [ ] Cards have proper icons and colors
- [ ] Clicking cards navigates to respective pages

### Lab Reports (/lab-reports)
- [ ] Page loads and displays test bookings
- [ ] Search functionality works
- [ ] Pagination controls appear if >10 items
- [ ] Status badges are color-coded
- [ ] "Book New Test" button is visible
- [ ] Clicking booking shows details

**API Test:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/lab/bookings/
```

### Prescriptions (/prescriptions)
- [ ] Page loads with active prescriptions
- [ ] Prescription details show medicine list
- [ ] Refill status is displayed
- [ ] "Request Refill" button works
- [ ] Expiry dates are visible
- [ ] Pagination works if >10 items

**API Test:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/prescriptions/
```

### Rooms (/rooms)
- [ ] Page loads and shows available rooms
- [ ] Room type filter dropdown works
- [ ] Bed count displays correctly (e.g., "3/5 beds occupied")
- [ ] Current patient assignments visible
- [ ] "Admit Patient" and "Discharge" buttons appear
- [ ] Room details load on expansion

**API Test:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/rooms/available/
```

### Heart Risk (/ai-health/heart-risk)
- [ ] Page loads with risk assessment
- [ ] Risk gauge displays with correct color (Green/Yellow/Red)
- [ ] Risk score percentage shows
- [ ] Risk factors checklist is visible
- [ ] AI recommendations are displayed
- [ ] "Calculate New" button works

**API Test:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/heart-risk/latest/
```

### Profile (/profile)
- [ ] Current profile information displays
- [ ] Form fields are editable
- [ ] Photo preview shows
- [ ] "Save Changes" button works
- [ ] Success toast appears on save
- [ ] Validation errors display correctly

**API Test:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/profile/
```

### Doctors (/doctors)
- [ ] Page loads with doctor list
- [ ] Search by name works
- [ ] Filter by specialization works
- [ ] Doctor cards show: name, specialization, experience, fee
- [ ] Photos display correctly
- [ ] "Book Appointment" button visible
- [ ] Pagination works if >20 doctors

**API Test:**
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/api/doctors/
```

### Sidebar Navigation
- [ ] All menu items appear based on user role (admin/doctor/patient)
- [ ] Active menu item is highlighted
- [ ] Links navigate to correct pages
- [ ] Icons display correctly
- [ ] Menu collapses/expands properly

---

## 🐛 Troubleshooting

### Issue: 401 Unauthorized on API calls
**Solution:**
- Check if user is logged in
- Verify JWT token exists in localStorage
- Check token expiry time
- Try logging in again

### Issue: Page shows "Loading..." indefinitely
**Solution:**
- Check browser console for errors (F12)
- Verify backend server is running
- Check network tab in DevTools to see API calls
- Look for CORS errors

### Issue: Data not loading on page
**Solution:**
- Open browser DevTools (F12)
- Check Network tab for API response status
- Check Console tab for JavaScript errors
- Verify API endpoint URL is correct

### Issue: CORS errors
**Solution:**
- Ensure backend CORS headers are set correctly
- Frontend should be on `http://localhost:3000`
- Backend should be on `http://localhost:8000`
- Check `settings.py` for CORS_ALLOWED_ORIGINS

### Issue: Sidebar not showing new items
**Solution:**
- Clear browser cache (Ctrl+Shift+Delete)
- Refresh frontend page (Ctrl+Shift+R)
- Verify user role has permission for the item
- Check sidebar.tsx roles configuration

---

## 🔍 Manual API Testing

### Using cURL
```bash
# Get JWT Token
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.access_token')

# Test Hospital endpoints
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/lab/bookings/?page=1&page_size=10

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/prescriptions/

curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8000/api/rooms/available/
```

### Using Postman
1. Create new request
2. Set method to GET
3. Set URL: `http://localhost:8000/api/endpoint/`
4. Go to Headers tab
5. Add header: `Authorization: Bearer YOUR_JWT_TOKEN`
6. Click Send

---

## 📊 Expected Response Examples

### Lab Bookings Response
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "patient": {"id": 1, "user": {"username": "john"}},
      "test_template": {"id": 1, "name": "Blood Test"},
      "booking_date": "2024-01-15",
      "status": "PENDING"
    }
  ]
}
```

### Prescriptions Response
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "patient": {"id": 1},
      "doctor": {"id": 1},
      "items": [
        {
          "id": 1,
          "medicine_name": "Aspirin",
          "dosage": "500mg",
          "frequency": "Twice daily",
          "duration_days": 5
        }
      ],
      "status": "ACTIVE"
    }
  ]
}
```

### Heart Risk Response
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "patient": {"id": 1},
      "risk_score": 35.5,
      "risk_level": "LOW",
      "age": 45,
      "blood_pressure_systolic": 120,
      "blood_pressure_diastolic": 80,
      "total_cholesterol": 200,
      "fasting_glucose": 95,
      "bmi": 24.5,
      "is_smoker": false,
      "is_diabetic": false,
      "has_family_history": false,
      "recommendations": "Continue current lifestyle..."
    }
  ]
}
```

---

## 🎯 Performance Testing

### Check Load Times
1. Open DevTools (F12)
2. Go to Network tab
3. Navigate to each page
4. Note load times for:
   - Page initial load
   - API calls
   - Image/resource loading

### Expected Performance
- Page load: < 2 seconds
- API calls: < 1 second
- Dashboard: < 3 seconds (with stats)

---

## 📝 Test Results Template

```markdown
## Test Results - [Date]

### Dashboard
- [x] Loads successfully
- [x] Stats display correctly
- [x] Feature cards visible
- [ ] Performance acceptable

### Lab Reports
- [x] Pagination works
- [x] Search functional
- [ ] All bookings display

### Prescriptions
- [x] Active prescriptions shown
- [ ] Refill workflow tested

### Rooms
- [x] Bed availability accurate
- [ ] Assignment creation works

### Heart Risk
- [x] Risk calculation correct
- [ ] Recommendations displayed

### Profile
- [x] Profile info loads
- [ ] Edit functionality works

### Doctors
- [x] Doctor list displays
- [ ] Specializations filtered

### Issues Found
- None at this time

### Sign-off
Tested by: [Name]
Date: [Date]
Status: READY FOR PRODUCTION
```

---

## ✅ Sign-off Checklist

- [ ] All pages load without errors
- [ ] All API endpoints respond with correct data
- [ ] Search and filter functionality works
- [ ] Pagination operates correctly
- [ ] Error handling displays helpful messages
- [ ] Success toast notifications appear
- [ ] Responsive design works on mobile
- [ ] JWT authentication is working
- [ ] CORS headers are correct
- [ ] Database is properly seeded with test data
- [ ] Performance is acceptable
- [ ] Security (no sensitive data in logs)
- [ ] User experience is smooth and intuitive

---

**Ready for Testing!** ✅

Start with running both servers and login to begin testing the fully integrated Hospital Management System.
