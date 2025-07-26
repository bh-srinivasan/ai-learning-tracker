# Azure Excel Upload Troubleshooting Guide

## 🚨 Current Issue
The Azure app is running but Excel upload is not working. The debug script shows the app is accessible but authentication is required.

## 🔍 Step-by-Step Debugging Process

### Phase 1: Browser-Based Debugging (IMMEDIATE ACTION)

1. **Open Azure App in Browser**
   ```
   https://ai-learning-tracker-bharath.azurewebsites.net
   ```

2. **Log in as Admin**
   - Username: `admin`
   - Password: `[your environment password]`

3. **Navigate to Manage Courses**
   - Go to Admin → Manage Courses

4. **Open Browser Developer Tools**
   - Press F12 or right-click → Inspect Element
   - Go to the **Console** tab

5. **Load Debug Script**
   - Copy the contents of `browser_debug_excel.js`
   - Paste into the console and press Enter
   - You should see: "🔧 Debug script loaded. Try uploading an Excel file now..."

6. **Test Upload with Debug**
   - Click "Upload Excel" button
   - Select the `test_azure_upload.xlsx` file (created by the debug script)
   - Click submit and watch the console for detailed output

### Phase 2: Network Analysis

7. **Check Network Tab**
   - In Developer Tools, go to **Network** tab
   - Clear existing entries (trash icon)
   - Try the upload again
   - Look for the POST request to `/admin/upload_excel_courses`

8. **Analyze the Request/Response**
   - Click on the POST request in Network tab
   - Check **Headers** tab for request details
   - Check **Response** tab for server response
   - Check **Payload** tab to verify file was sent

### Phase 3: Common Issue Checks

9. **File Size Limit**
   - Azure has file upload limits
   - Check if your Excel file is under 10MB
   - Try with the minimal test file first

10. **Session/Authentication**
    - If you see login redirects, you may have been logged out
    - Try logging in again and repeat the upload

11. **Python Dependencies**
    - The error might be server-side (pandas/openpyxl issues)
    - Check the response for dependency-related errors

### Phase 4: Server-Side Logs

12. **Azure App Service Logs**
    ```bash
    # Enable logging (if not already enabled)
    az webapp log config --name ai-learning-tracker-bharath --resource-group ai-learning-rg --application-logging filesystem

    # Get real-time logs
    az webapp log tail --name ai-learning-tracker-bharath --resource-group ai-learning-rg
    ```

13. **Check for Python Errors**
    - Look for import errors (pandas, openpyxl)
    - Look for file processing errors
    - Look for database connection issues

## 🔧 Expected Debug Output

### Successful Upload
```
🔍 Starting Excel Upload Debug...
✅ Upload form found
✅ File input found
📁 File details:
  Name: test_azure_upload.xlsx
  Size: 8234 bytes
📡 Sending request to: /admin/upload_excel_courses
📥 Response received:
  Status: 200
📊 Parsed JSON response: {success: true, message: "Successfully uploaded 1 courses"}
✅ Upload successful!
```

### Failed Upload Examples
```
❌ Server error detected - check Azure app logs
❌ Upload endpoint not found
❌ Authentication required - you may have been logged out
❌ Upload failed: pandas library is required for Excel processing
```

## 🎯 Common Solutions

### If Authentication Issues:
- Clear browser cookies for the Azure site
- Log out and log back in
- Check if session timeout occurred

### If File Processing Issues:
- Ensure the Excel file has required columns: title, url, source, level
- Check file format is .xlsx (not .xls)
- Try with the minimal test file first

### If Server Errors:
- Check Azure app logs for Python exceptions
- Verify all dependencies are installed in requirements.txt
- Check if there are Azure-specific file upload limits

### If Upload Endpoint Not Found:
- Verify the route is deployed correctly
- Check if the Azure deployment included the latest code
- Restart the Azure app service

## 📋 Information to Collect

When reporting issues, please provide:

1. **Console Output** from the debug script
2. **Network Response** from the POST request
3. **Any Error Messages** shown in the browser
4. **File Details** (name, size, format)
5. **Browser Type** and version

## 🚀 Next Steps

Based on the debug output, we can:
- Fix server-side Python issues
- Adjust file upload limits
- Update authentication handling
- Improve error messages
- Fix routing problems

Run the browser debug first and share the console output!
