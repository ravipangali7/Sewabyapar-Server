# PhonePe Mobile SDK Deployment Notes

## Important: Server Restart Required

After updating the PhonePe mobile SDK implementation, **you must restart the server** for the changes to take effect.

## Changes Made

1. **Updated `create_order_for_mobile_sdk()` function** to use the correct mobile SDK order token API endpoint instead of web checkout
2. **Added O-Bearer authentication** for mobile SDK API calls
3. **Updated authentication function** to support both sandbox and production environments

## Server Restart Instructions

### For Gunicorn (Production Server)

```bash
# SSH into your server
ssh user@your-server

# Navigate to your project directory
cd /path/to/ecommerce_backend

# Restart Gunicorn
# Option 1: If using systemd service
sudo systemctl restart gunicorn
# OR
sudo systemctl restart your-app-name

# Option 2: If using supervisor
sudo supervisorctl restart gunicorn
# OR
sudo supervisorctl restart your-app-name

# Option 3: If running manually, find and kill the process, then restart
# Find the process
ps aux | grep gunicorn

# Kill the process (replace PID with actual process ID)
kill -HUP <PID>
# OR for graceful restart
kill -USR2 <PID>

# Then restart gunicorn
gunicorn ecommerce_backend.wsgi:application --bind 0.0.0.0:8000
```

### Verify the Changes

After restarting, check the logs to verify the new code is running. You should see:

**NEW logs (correct implementation):**
```
[INFO] Using mobile SDK API URL: https://api.phonepe.com/apis/pg/checkout/v2/sdk/order
[INFO] Getting O-Bearer merchant auth token
[INFO] Making POST request to https://api.phonepe.com/apis/pg/checkout/v2/sdk/order
```

**OLD logs (if server not restarted - WRONG):**
```
[INFO] Calling PhonePe client.pay()
[INFO] PhonePe client.pay() completed successfully
```

## Testing

After restarting the server:

1. Make a test payment from the Flutter app
2. Check backend logs to confirm new code is running
3. Verify the mobile SDK receives the correct order token
4. The PR004 error should be resolved if the token is from the mobile SDK API

## Configuration Check

Ensure these settings are correct in `settings.py`:

- `PHONEPE_ENV = 'PRODUCTION'` (or 'SANDBOX' for testing)
- `PHONEPE_CLIENT_ID` - Your PhonePe client ID
- `PHONEPE_CLIENT_SECRET` - Your PhonePe client secret
- `PHONEPE_MERCHANT_ID` - Your PhonePe merchant ID
- `PHONEPE_MOBILE_SDK_ORDER_API_URL` - Automatically set based on environment

## Troubleshooting

If you still see PR004 errors after restarting:

1. **Verify merchant account**: Ensure your PhonePe merchant account is activated for mobile SDK payments
2. **Check environment**: Ensure `PHONEPE_ENV` matches your merchant account environment (PRODUCTION vs SANDBOX)
3. **Verify credentials**: Double-check CLIENT_ID, CLIENT_SECRET, and MERCHANT_ID are correct
4. **Check permissions**: Ensure your merchant account has mobile SDK permissions enabled
5. **Contact PhonePe support**: If issues persist, contact PhonePe support with your merchant ID and error code PR004

