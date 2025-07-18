# Microsoft Edge - Clear Cache and Session Data
# Follow these steps to fix the Edge-specific issues:

## Method 1: Clear All Edge Data (Recommended)
1. Open Microsoft Edge
2. Press Ctrl + Shift + Delete (or go to Settings > Privacy, search, and services)
3. Select "All time" for Time range
4. Check ALL these boxes:
   ✓ Browsing history
   ✓ Download history  
   ✓ Cookies and other site data
   ✓ Cached images and files
   ✓ Passwords
   ✓ Autofill form data
   ✓ Site permissions
   ✓ Hosted app data
5. Click "Clear now"
6. Restart Edge completely

## Method 2: Clear Site-Specific Data
1. In Edge, go to localhost:5000
2. Click the lock icon (🔒) in the address bar
3. Click "Cookies and site permissions"
4. Click "Manage and delete cookies and site data"
5. Find localhost:5000 and 127.0.0.1:5000
6. Delete both entries
7. Refresh the page

## Method 3: Reset Edge Site Settings
1. Go to edge://settings/content/all
2. Search for "localhost"
3. Delete any localhost entries
4. Search for "127.0.0.1"
5. Delete any 127.0.0.1 entries

## Method 4: Edge Developer Tools Reset
1. Open localhost:5000 in Edge
2. Press F12 to open Developer Tools
3. Right-click the refresh button
4. Select "Empty cache and hard reload"
5. Or go to Application tab > Storage > Clear storage

## Method 5: InPrivate Mode Test
1. Open Edge in InPrivate mode (Ctrl + Shift + N)
2. Navigate to localhost:5000
3. This should work properly as it has no cached data
