import requests; login_url = "http://127.0.0.1:8000/api/auth/login/"; me_url = "http://127.0.0.1:8000/api/auth/me/"; compliance_url = "http://127.0.0.1:8000/api/compliance/dashboard/"; payload = {"email": "admin@hms.test", "password": "Admin@123456"}; 
try:
    login_resp = requests.post(login_url, json=payload); 
    login_data = login_resp.json(); 
    print("Login Status:", login_resp.status_code); 
    print("Keys:", list(login_data.keys())); 
    token = login_data.get("access") or login_data.get("token"); 
    if not token: 
        print("No token"); 
    else: 
        headers = {"Authorization": "Bearer " + token}; 
        me_resp = requests.get(me_url, headers=headers); 
        print("Me Status:", me_resp.status_code); 
        print("Me Body:", me_resp.text[:300]); 
        try: print("Role:", me_resp.json().get("role", "N/A")); 
        except: pass; 
        comp_resp = requests.get(compliance_url, headers=headers); 
        print("Comp Status:", comp_resp.status_code); 
        print("Comp Body:", comp_resp.text[:300]); 
except Exception as e: print("Error:", e)
