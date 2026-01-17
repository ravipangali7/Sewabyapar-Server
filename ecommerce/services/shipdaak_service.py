"""
Shipdaak Logistics API Service
Handles all Shipdaak API interactions for warehouse and shipment management
"""
import requests
import re
import base64
import json
import traceback
import sys
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta, timezone as dt_timezone


class ShipdaakService:
    """Service class for interacting with Shipdaak API"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'SHIPDAAK_API_BASE_URL', '').rstrip('/')
        self.email = getattr(settings, 'SHIPDAAK_API_EMAIL', '')
        self.password = getattr(settings, 'SHIPDAAK_API_PASSWORD', '')
        self.token_cache_key = getattr(settings, 'SHIPDAAK_TOKEN_CACHE_KEY', 'shipdaak_access_token')
        self.token_expiry_cache_key = getattr(settings, 'SHIPDAAK_TOKEN_EXPIRY_CACHE_KEY', 'shipdaak_token_expiry')
        
        if not self.base_url:
            print("[WARNING] SHIPDAAK_API_BASE_URL not configured in settings")
            sys.stdout.flush()
        if not self.email or not self.password:
            print("[WARNING] SHIPDAAK_API_EMAIL or SHIPDAAK_API_PASSWORD not configured in settings")
            sys.stdout.flush()
    
    def _decode_jwt_expiry(self, token: str) -> Optional[datetime]:
        """
        Decode JWT token to get expiry time
        
        Args:
            token: JWT token string
            
        Returns:
            Datetime of token expiry or None if decoding fails
        """
        try:
            # JWT format: header.payload.signature
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            # Decode payload (base64url)
            payload = parts[1]
            # Add padding if needed
            padding = len(payload) % 4
            if padding:
                payload += '=' * (4 - padding)
            
            decoded = base64.urlsafe_b64decode(payload)
            data = json.loads(decoded)
            
            # Get expiry (exp is Unix timestamp)
            exp = data.get('exp')
            if exp:
                return datetime.fromtimestamp(exp, tz=dt_timezone.utc)
            return None
        except Exception as e:
            print(f"[WARNING] Failed to decode JWT expiry: {str(e)}")
            sys.stdout.flush()
            return None
    
    def _get_access_token(self, force_refresh: bool = False) -> Optional[str]:
        """
        Get access token from cache or generate new one
        Returns None if authentication fails
        """
        # Check cache first (unless forcing refresh)
        if not force_refresh:
            token = cache.get(self.token_cache_key)
            expiry = cache.get(self.token_expiry_cache_key)
            
            if token and expiry:
                # Check if token is still valid (with 5 minute buffer)
                if timezone.now() < expiry - timedelta(minutes=5):
                    return token
        
        # Generate new token
        try:
            url = f"{self.base_url}/v1/auth/token"
            payload = {
                "email": self.email,
                "password": self.password
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Check for error response first
            if 'error' in data:
                print(f"[ERROR] Shipdaak authentication failed: {data.get('error')}")
                sys.stdout.flush()
                # Clear any cached token
                cache.delete(self.token_cache_key)
                cache.delete(self.token_expiry_cache_key)
                return None
            
            access_token = data.get('access_token')
            
            if access_token:
                # Decode JWT to get actual expiry
                expiry_datetime = self._decode_jwt_expiry(access_token)
                
                if expiry_datetime:
                    # Cache until expiry (with 5 min buffer)
                    cache_until = expiry_datetime - timedelta(minutes=5)
                    cache_seconds = int((cache_until - timezone.now()).total_seconds())
                    
                    if cache_seconds > 0:
                        cache.set(self.token_cache_key, access_token, cache_seconds)
                        cache.set(self.token_expiry_cache_key, expiry_datetime, cache_seconds)
                        print(f"[INFO] Successfully obtained Shipdaak access token, expires at {expiry_datetime}")
                        sys.stdout.flush()
                    else:
                        print("[WARNING] Token already expired, not caching")
                        sys.stdout.flush()
                else:
                    # Fallback: cache for 12 hours if can't decode expiry
                    print("[WARNING] Could not decode JWT expiry, using 12 hour cache")
                    sys.stdout.flush()
                    cache.set(self.token_cache_key, access_token, 60 * 60 * 12)
                    cache.set(self.token_expiry_cache_key, timezone.now() + timedelta(hours=12), 60 * 60 * 12)
                
                return access_token
            else:
                print(f"[ERROR] Shipdaak token response missing access_token: {data}")
                sys.stdout.flush()
                # Clear cache on error
                cache.delete(self.token_cache_key)
                cache.delete(self.token_expiry_cache_key)
                return None
                
        except requests.exceptions.HTTPError as e:
            print(f"[ERROR] Shipdaak token HTTP error: {e.response.status_code} - {e.response.text if hasattr(e, 'response') else str(e)}")
            sys.stdout.flush()
            cache.delete(self.token_cache_key)
            cache.delete(self.token_expiry_cache_key)
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Failed to get Shipdaak access token: {str(e)}")
            sys.stdout.flush()
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error getting Shipdaak access token: {str(e)}")
            sys.stdout.flush()
            return None
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                      params: Optional[Dict] = None, retry_on_401: bool = True) -> Optional[Dict]:
        """
        Make authenticated request to Shipdaak API
        
        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            endpoint: API endpoint (without base URL)
            data: Request body data (for POST/PUT)
            params: Query parameters (for GET)
            retry_on_401: Whether to retry on 401 errors (prevents infinite loops)
        
        Returns:
            Response JSON data or None if request fails
        """
        token = self._get_access_token()
        if not token:
            print("[ERROR] Cannot make request: No access token available")
            sys.stdout.flush()
            return None
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                print(f"[ERROR] Unsupported HTTP method: {method}")
                sys.stdout.flush()
                return None
            
            # Handle 401 Unauthorized - token might be expired
            if response.status_code == 401 and retry_on_401:
                print(f"[WARNING] Received 401 Unauthorized, clearing token cache and retrying once")
                sys.stdout.flush()
                # Clear cached token
                cache.delete(self.token_cache_key)
                cache.delete(self.token_expiry_cache_key)
                # Retry once with fresh token
                return self._make_request(method, endpoint, data, params, retry_on_401=False)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                print(f"[ERROR] Shipdaak API authentication failed ({method} {endpoint}): 401 Unauthorized")
            else:
                print(f"[ERROR] Shipdaak API HTTP error ({method} {endpoint}): {e.response.status_code} - {e.response.text if hasattr(e, 'response') else str(e)}")
            sys.stdout.flush()
            return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Shipdaak API request error ({method} {endpoint}): {str(e)}")
            sys.stdout.flush()
            return None
        except Exception as e:
            print(f"[ERROR] Unexpected error in Shipdaak API request ({method} {endpoint}): {str(e)}")
            sys.stdout.flush()
            return None
    
    def create_warehouse(self, store) -> Optional[Dict[str, int]]:
        """
        Create warehouse in Shipdaak from store data
        
        Args:
            store: Store model instance
        
        Returns:
            Dict with 'pickup_warehouse_id' and 'rto_warehouse_id' or None if fails
        """
        try:
            # Extract pincode from address - improved extraction
            pincode = "110001"  # Default pincode
            if store.address:
                # Try multiple methods to extract pincode
                # Method 1: Look for 6-digit number at the end of address (most common)
                pincode_match = re.search(r'\b(\d{6})\b', store.address)
                if pincode_match:
                    pincode = pincode_match.group(1)
                else:
                    # Method 2: Look in address lines (split by newline or comma)
                    address_parts = re.split(r'[,\n]', store.address)
                    for part in reversed(address_parts):
                        part = part.strip()
                        pincode_match = re.search(r'\b(\d{6})\b', part)
                        if pincode_match:
                            pincode = pincode_match.group(1)
                            break
            
            # Normalize phone number to exactly 10 digits for exact matching
            # Remove all non-digit characters
            phone_digits = re.sub(r'\D', '', str(store.phone))
            # Take last 10 digits if longer, pad with 0 if shorter
            if len(phone_digits) > 10:
                phone_digits = phone_digits[-10:]
            elif len(phone_digits) < 10:
                phone_digits = phone_digits.zfill(10)
            normalized_phone = phone_digits if phone_digits else store.phone
            
            # Prepare warehouse data
            warehouse_data = {
                "pickup_location": {
                    "warehouse_name": store.name,
                    "contact_name": store.owner.name if store.owner else "Store Owner",
                    "address_line_1": store.address or "Address not provided",
                    "address_line_2": "",
                    "pincode": pincode,
                    "phone": normalized_phone,  # Use normalized phone for exact matching
                    "gst_number": ""  # GST number not in store model, can be added later
                },
                "has_different_rto": False,  # Using same address for RTO
                "rto_location": {
                    "warehouse_name": f"{store.name} - RTO",
                    "contact_name": store.owner.name if store.owner else "Store Owner",
                    "address_line_1": store.address or "Address not provided",
                    "address_line_2": "",
                    "pincode": pincode,
                    "phone": normalized_phone,  # Use normalized phone for exact matching
                    "gst_number": ""
                }
            }
            
            response = self._make_request('POST', '/v1/warehouse/create-warehouse', data=warehouse_data)
            
            if response and response.get('status') and response.get('data'):
                data = response['data']
                return {
                    'pickup_warehouse_id': data.get('pickup_warehouse_id'),
                    'rto_warehouse_id': data.get('rto_warehouse_id')
                }
            else:
                print(f"[ERROR] Shipdaak warehouse creation failed: {response}")
                sys.stdout.flush()
                return None
                
        except Exception as e:
            print(f"[ERROR] Error creating Shipdaak warehouse for store {store.id}: {str(e)}")
            traceback.print_exc()
            return None
    
    def update_warehouse(self, store) -> bool:
        """
        Update warehouse in Shipdaak from store data
        
        Uses the create-warehouse endpoint which is idempotent and can update existing warehouses.
        The endpoint response says "created/verified successfully" indicating it handles both scenarios.
        
        Args:
            store: Store model instance with existing shipdaak_pickup_warehouse_id
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if not store.shipdaak_pickup_warehouse_id:
                print(f"[WARNING] Store {store.id} has no Shipdaak warehouse ID. Cannot update. Creating new warehouse instead.")
                sys.stdout.flush()
                # Fallback to create if warehouse doesn't exist
                warehouse_data = self.create_warehouse(store)
                if warehouse_data:
                    store.shipdaak_pickup_warehouse_id = warehouse_data.get('pickup_warehouse_id')
                    store.shipdaak_rto_warehouse_id = warehouse_data.get('rto_warehouse_id')
                    store.shipdaak_warehouse_created_at = timezone.now()
                    store.save(update_fields=['shipdaak_pickup_warehouse_id', 
                                            'shipdaak_rto_warehouse_id', 
                                            'shipdaak_warehouse_created_at'])
                    return True
                return False
            
            # Extract pincode from address - improved extraction
            pincode = "110001"  # Default pincode
            if store.address:
                # Try multiple methods to extract pincode
                # Method 1: Look for 6-digit number at the end of address (most common)
                pincode_match = re.search(r'\b(\d{6})\b', store.address)
                if pincode_match:
                    pincode = pincode_match.group(1)
                else:
                    # Method 2: Look in address lines (split by newline or comma)
                    address_parts = re.split(r'[,\n]', store.address)
                    for part in reversed(address_parts):
                        part = part.strip()
                        pincode_match = re.search(r'\b(\d{6})\b', part)
                        if pincode_match:
                            pincode = pincode_match.group(1)
                            break
            
            # Normalize phone number to exactly 10 digits for exact matching
            # Remove all non-digit characters
            phone_digits = re.sub(r'\D', '', str(store.phone))
            # Take last 10 digits if longer, pad with 0 if shorter
            if len(phone_digits) > 10:
                phone_digits = phone_digits[-10:]
            elif len(phone_digits) < 10:
                phone_digits = phone_digits.zfill(10)
            normalized_phone = phone_digits if phone_digits else store.phone
            
            # Prepare warehouse data - include warehouse IDs to help Shipdaak identify existing warehouses
            warehouse_data = {
                "pickup_warehouse_id": store.shipdaak_pickup_warehouse_id,  # Include existing ID
                "pickup_location": {
                    "warehouse_name": store.name,
                    "contact_name": store.owner.name if store.owner else "Store Owner",
                    "address_line_1": store.address or "Address not provided",
                    "address_line_2": "",
                    "pincode": pincode,
                    "phone": normalized_phone,  # Use normalized phone for exact matching
                    "gst_number": ""  # GST number not in store model, can be added later
                },
                "has_different_rto": False,  # Using same address for RTO
                "rto_warehouse_id": store.shipdaak_rto_warehouse_id,  # Include existing RTO ID
                "rto_location": {
                    "warehouse_name": f"{store.name} - RTO",
                    "contact_name": store.owner.name if store.owner else "Store Owner",
                    "address_line_1": store.address or "Address not provided",
                    "address_line_2": "",
                    "pincode": pincode,
                    "phone": normalized_phone,  # Use normalized phone for exact matching
                    "gst_number": ""
                }
            }
            
            # Use POST to create-warehouse endpoint (idempotent - updates existing warehouses)
            response = self._make_request('POST', '/v1/warehouse/create-warehouse', data=warehouse_data)
            
            if response and response.get('status'):
                response_data = response.get('data', {})
                # Verify that warehouse IDs match (should be same if updating existing)
                returned_pickup_id = response_data.get('pickup_warehouse_id')
                returned_rto_id = response_data.get('rto_warehouse_id')
                
                if returned_pickup_id and returned_pickup_id != store.shipdaak_pickup_warehouse_id:
                    # Warehouse IDs changed - update our records
                    print(f"[INFO] Shipdaak returned different warehouse IDs. Updating store {store.id} warehouse IDs.")
                    sys.stdout.flush()
                    store.shipdaak_pickup_warehouse_id = returned_pickup_id
                    store.shipdaak_rto_warehouse_id = returned_rto_id
                    store.save(update_fields=['shipdaak_pickup_warehouse_id', 'shipdaak_rto_warehouse_id'])
                
                print(f"[INFO] Successfully updated Shipdaak warehouse for store {store.id} (warehouse IDs: pickup={returned_pickup_id or store.shipdaak_pickup_warehouse_id}, rto={returned_rto_id or store.shipdaak_rto_warehouse_id})")
                sys.stdout.flush()
                return True
            else:
                print(f"[ERROR] Shipdaak warehouse update failed for store {store.id}: {response}")
                sys.stdout.flush()
                return False
                
        except Exception as e:
            print(f"[ERROR] Error updating Shipdaak warehouse for store {store.id}: {str(e)}")
            traceback.print_exc()
            return False
    
    def create_shipment(self, order, courier_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Create shipment in Shipdaak from order data with automatic courier fallback
        
        Args:
            order: Order model instance
            courier_id: Optional courier ID to use. If not provided, uses store's default courier.
                       If the selected courier fails due to "Pincode not serviceable", 
                       automatically tries other configured couriers.
        
        Returns:
            Dict with shipment data (awb_number, shipment_id, label_url, etc.) or None if fails
        """
        try:
            from ecommerce.models import GlobalCourier
            
            store = order.merchant
            if not store:
                print(f"[ERROR] Order {order.id} has no merchant/store")
                sys.stdout.flush()
                return None
            
            if not store.shipdaak_pickup_warehouse_id:
                print(f"[ERROR] Store {store.id} has no Shipdaak warehouse ID")
                sys.stdout.flush()
                return None
            
            # Get all active global couriers, ordered by priority
            all_courier_configs = GlobalCourier.objects.filter(
                is_active=True
            ).order_by('priority', 'courier_name')
            
            if not all_courier_configs.exists():
                print(f"[WARNING] No active global couriers configured, shipment creation may fail")
                sys.stdout.flush()
                # Continue anyway - might work without courier or fail gracefully
            
            # Build list of couriers to try
            couriers_to_try = []
            
            if courier_id:
                # Find the requested courier and add it first
                requested_courier = all_courier_configs.filter(courier_id=courier_id).first()
                if requested_courier:
                    couriers_to_try.append(requested_courier)
                    # Add other couriers after the requested one
                    for config in all_courier_configs:
                        if config.courier_id != courier_id:
                            couriers_to_try.append(config)
                else:
                    print(f"[WARNING] Courier ID {courier_id} not found or inactive, trying all available couriers")
                    sys.stdout.flush()
                    couriers_to_try = list(all_courier_configs)
            else:
                # No specific courier requested - use all couriers in priority order
                couriers_to_try = list(all_courier_configs)
            
            if not couriers_to_try:
                print(f"[ERROR] No active global couriers found. Cannot create shipment without a courier.")
                sys.stdout.flush()
                return None
            
            # Validate package dimensions exist
            if not order.package_length or not order.package_breadth or not order.package_height or not order.package_weight:
                print(f"[ERROR] Order {order.id} is missing package dimensions. Package dimensions must be set when merchant accepts order.")
                sys.stdout.flush()
                return None
            
            # Use package dimensions from order
            weight = float(order.package_weight)
            package_length = float(order.package_length)
            package_breadth = float(order.package_breadth)
            package_height = float(order.package_height)
            
            # Get shipping address
            shipping_address = order.shipping_address
            if not shipping_address:
                print(f"[ERROR] Order {order.id} has no shipping address")
                sys.stdout.flush()
                return None
            
            # Extract and validate pincode from address
            pincode = shipping_address.zip_code if hasattr(shipping_address, 'zip_code') else None
            
            # Clean and validate pincode
            if pincode:
                # Remove all non-digit characters
                pincode = re.sub(r'\D', '', str(pincode))
                # Take only first 6 digits
                if len(pincode) >= 6:
                    pincode = pincode[:6]
                elif len(pincode) > 0:
                    # Pad with zeros if less than 6 digits
                    pincode = pincode.zfill(6)
                else:
                    pincode = None
            
            # Validate pincode is exactly 6 digits
            if not pincode or len(pincode) != 6 or not pincode.isdigit():
                print(f"[ERROR] Order {order.id} has invalid or missing pincode in shipping address. Pincode: {shipping_address.zip_code if hasattr(shipping_address, 'zip_code') else 'None'}")
                sys.stdout.flush()
                return None
            
            # Fix phone number - ensure exactly 10 digits
            phone = order.phone
            # Remove all non-digit characters
            phone_digits = re.sub(r'\D', '', phone)
            # Take last 10 digits if longer, pad with 0 if shorter
            if len(phone_digits) > 10:
                phone_digits = phone_digits[-10:]
            elif len(phone_digits) < 10:
                phone_digits = phone_digits.zfill(10)
            
            # Prepare order items
            order_items = []
            for item in order.items.all():
                order_items.append({
                    "name": item.product.name,
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "sku": f"SKU{item.product.id}"  # Using product ID as SKU if not available
                })
            
            # Always use prepaid payment type for Shipdaak (regardless of order payment method)
            pay_type = "prepaid"
            cod_fee = 0  # No COD fee since always prepaid
            
            # Prepare base shipment data (without courier - will be added per attempt)
            base_shipment_data = {
                "order_no": order.order_number,
                "pay_type": pay_type,
                "weight": weight,
                "dimensions": {
                    "length": package_length,  # Package dimensions from order (in cm)
                    "breadth": package_breadth,
                    "height": package_height
                },
                "shipping_fee": float(order.shipping_cost),
                "cod_fee": cod_fee,
                "discount_amount": 0,  # Can be calculated from coupons if needed
                "total_amount": float(order.total_amount),
                "pickup_warehouse": store.shipdaak_pickup_warehouse_id,
                "rto_warehouse": store.shipdaak_rto_warehouse_id or store.shipdaak_pickup_warehouse_id,
                "tags": "",
                "label_format": "thermal",
                "auto_pickup": "yes",
                "is_shipment_created": "yes",
                "consignee": {
                    "name": shipping_address.full_name if hasattr(shipping_address, 'full_name') else order.user.name,
                    "company": "",
                    "address1": shipping_address.address if hasattr(shipping_address, 'address') else str(shipping_address),
                    "address2": "",
                    "city": shipping_address.city if hasattr(shipping_address, 'city') else "",
                    "state": shipping_address.state if hasattr(shipping_address, 'state') else "",
                    "pincode": pincode,
                    "phone": phone_digits,  # Use normalized phone number
                    "shipping_gst_number": ""
                },
                "order_items": order_items
            }
            
            # Try each courier in order until one succeeds
            last_error_message = None
            last_error_response = None
            
            for courier_config in couriers_to_try:
                current_courier_id = courier_config.courier_id
                current_courier_name = courier_config.courier_name
                
                print(f"[INFO] Trying to create Shipdaak shipment for order {order.id}: pincode={pincode}, courier_id={current_courier_id}, courier_name={current_courier_name}, store={store.id}")
                sys.stdout.flush()
                
                # Add courier to shipment data
                shipment_data = base_shipment_data.copy()
                shipment_data["courier"] = current_courier_id
                
                response = self._make_request('POST', '/v1/shipments/generate-shipment', data=shipment_data)
                
                if response and response.get('status') and response.get('data'):
                    data = response['data']
                    print(f"[INFO] Successfully created Shipdaak shipment for order {order.id} with courier {current_courier_name} (ID: {current_courier_id}), AWB: {data.get('awb_number')}")
                    sys.stdout.flush()
                    return {
                        'awb_number': data.get('awb_number'),
                        'shipment_id': data.get('shipment_id'),
                        'order_id': data.get('order_id'),
                        'label': data.get('label'),
                        'manifest': data.get('manifest'),
                        'status': data.get('status'),
                        'courier_id': data.get('courier_id'),
                        'courier_name': data.get('courier_name')
                    }
                else:
                    # Check if error is "Pincode not serviceable" - if so, try next courier
                    error_message = response.get('message', 'Unknown error') if response else 'No response from API'
                    last_error_message = error_message
                    last_error_response = response
                    
                    # Check if this is a serviceability issue
                    is_serviceability_error = (
                        'pincode' in error_message.lower() and 
                        ('not serviceable' in error_message.lower() or 'not serviced' in error_message.lower())
                    )
                    
                    if is_serviceability_error:
                        print(f"[WARNING] Courier {current_courier_name} (ID: {current_courier_id}) does not service pincode {pincode}. Trying next courier...")
                        sys.stdout.flush()
                        continue  # Try next courier
                    else:
                        # Non-serviceability error - log and try next courier anyway (might be temporary issue)
                        print(f"[WARNING] Courier {current_courier_name} (ID: {current_courier_id}) failed with error: {error_message}. Trying next courier...")
                        sys.stdout.flush()
                        continue
            
            # All couriers failed
            print(
                f"[ERROR] Shipdaak shipment creation failed for order {order.id} with all {len(couriers_to_try)} courier(s). "
                f"Last error: {last_error_message}. "
                f"Pincode: {pincode}, Store: {store.name} (ID: {store.id}), "
                f"Tried couriers: {[f'{c.courier_name} (ID: {c.courier_id})' for c in couriers_to_try]}, "
                f"Last response: {last_error_response}"
            )
            sys.stdout.flush()
            return None
                
        except Exception as e:
            print(f"[ERROR] Error creating Shipdaak shipment for order {order.id}: {str(e)}")
            traceback.print_exc()
            return None
    
    def cancel_shipment(self, awb_number: str) -> bool:
        """
        Cancel a shipment by AWB number
        
        Args:
            awb_number: AWB/Tracking number
        
        Returns:
            True if successful, False otherwise
        """
        try:
            response = self._make_request('POST', '/v1/shipments/cancel-shipment', data={"awb_number": awb_number})
            
            if response and response.get('status'):
                print(f"[INFO] Successfully cancelled Shipdaak shipment {awb_number}")
                sys.stdout.flush()
                return True
            else:
                print(f"[ERROR] Failed to cancel Shipdaak shipment {awb_number}: {response}")
                sys.stdout.flush()
                return False
                
        except Exception as e:
            print(f"[ERROR] Error cancelling Shipdaak shipment {awb_number}: {str(e)}")
            traceback.print_exc()
            return False
    
    def track_shipment(self, awb_number: str) -> Optional[Dict[str, Any]]:
        """
        Track a shipment by AWB number
        
        Args:
            awb_number: AWB/Tracking number
        
        Returns:
            Dict with tracking data or None if fails
        """
        try:
            response = self._make_request('GET', f'/v1/shipments/track-shipment/{awb_number}')
            
            if response and response.get('status') and response.get('data'):
                return response['data']
            else:
                print(f"[ERROR] Failed to track Shipdaak shipment {awb_number}: {response}")
                sys.stdout.flush()
                return None
                
        except Exception as e:
            print(f"[ERROR] Error tracking Shipdaak shipment {awb_number}: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_couriers(self) -> Optional[List[Dict[str, Any]]]:
        """
        Get list of available couriers
        
        Returns:
            List of courier dicts with 'id' and 'name' or None if fails
        """
        try:
            response = self._make_request('GET', '/v1/courier/get-courier')
            
            if response and response.get('status') and response.get('data'):
                return response['data']
            else:
                print(f"[ERROR] Failed to get Shipdaak couriers: {response}")
                sys.stdout.flush()
                return None
                
        except Exception as e:
            print(f"[ERROR] Error getting Shipdaak couriers: {str(e)}")
            traceback.print_exc()
            return None
    
    def generate_bulk_label(self, awb_numbers: List[str], label_format: str = "standard") -> Optional[str]:
        """
        Generate bulk labels for multiple shipments
        
        Args:
            awb_numbers: List of AWB numbers
            label_format: Label format ('standard' or 'thermal')
        
        Returns:
            URL to PDF label or None if fails
        """
        try:
            response = self._make_request('POST', '/v1/shipments/bulk-label-shipment', data={
                "awb_nos": awb_numbers,
                "label_format": label_format
            })
            
            if response and response.get('status') and response.get('data'):
                return response['data']  # URL string
            else:
                print(f"[ERROR] Failed to generate bulk labels: {response}")
                sys.stdout.flush()
                return None
                
        except Exception as e:
            print(f"[ERROR] Error generating bulk labels: {str(e)}")
            traceback.print_exc()
            return None
    
    def generate_bulk_manifest(self, awb_numbers: List[str]) -> Optional[str]:
        """
        Generate bulk manifest for multiple shipments
        
        Args:
            awb_numbers: List of AWB numbers
        
        Returns:
            URL to PDF manifest or None if fails
        """
        try:
            response = self._make_request('POST', '/v1/shipments/bulk-manifest-shipment', data={
                "awb_nos": awb_numbers
            })
            
            if response and response.get('status') and response.get('data'):
                return response['data']  # URL string
            else:
                print(f"[ERROR] Failed to generate bulk manifest: {response}")
                sys.stdout.flush()
                return None
                
        except Exception as e:
            print(f"[ERROR] Error generating bulk manifest: {str(e)}")
            traceback.print_exc()
            return None
    
    def get_rate_serviceability(
        self,
        origin_pincode: str,
        destination_pincode: str,
        weight: float,
        length: float,
        breadth: float,
        height: float,
        order_amount: float,
        payment_type: str = "prepaid",
        filter_type: str = "rate"
    ) -> Optional[Dict[str, Any]]:
        """
        Get courier rates and serviceability for given parameters
        
        Args:
            origin_pincode: Origin pincode (6 digits)
            destination_pincode: Destination pincode (6 digits)
            weight: Package weight in grams
            length: Package length in cm
            breadth: Package breadth in cm
            height: Package height in cm
            order_amount: Order amount
            payment_type: Payment type ('cod' or 'prepaid')
            filter_type: Filter type ('rate' or 'serviceability')
        
        Returns:
            Dict with courier rates and serviceability data or None if fails
        """
        try:
            # Validate and normalize pincodes
            origin_pincode = re.sub(r'\D', '', str(origin_pincode))
            if len(origin_pincode) >= 6:
                origin_pincode = origin_pincode[:6]
            elif len(origin_pincode) > 0:
                origin_pincode = origin_pincode.zfill(6)
            else:
                print(f"[ERROR] Invalid origin pincode: {origin_pincode}")
                sys.stdout.flush()
                return None
            
            destination_pincode = re.sub(r'\D', '', str(destination_pincode))
            if len(destination_pincode) >= 6:
                destination_pincode = destination_pincode[:6]
            elif len(destination_pincode) > 0:
                destination_pincode = destination_pincode.zfill(6)
            else:
                print(f"[ERROR] Invalid destination pincode: {destination_pincode}")
                sys.stdout.flush()
                return None
            
            # Prepare request data
            request_data = {
                "filterType": filter_type,
                "origin": int(origin_pincode),
                "destination": int(destination_pincode),
                "paymentType": payment_type,
                "weight": float(weight),
                "length": float(length),
                "breadth": float(breadth),
                "height": float(height),
                "orderAmount": float(order_amount)
            }
            
            print(f"[INFO] Shipdaak API Request - get-rate-serviceability:")
            print(f"[INFO] Request Data: {json.dumps(request_data, indent=2)}")
            sys.stdout.flush()
            
            response = self._make_request('POST', '/v1/courier/get-rate-serviceability', data=request_data)
            
            if response:
                print(f"[INFO] Shipdaak API Response (raw): {json.dumps(response, indent=2, default=str)}")
                sys.stdout.flush()
                print(f"[INFO] Successfully fetched courier rates: origin={origin_pincode}, destination={destination_pincode}")
                sys.stdout.flush()
                return response
            else:
                print(f"[ERROR] Failed to get courier rates from Shipdaak API")
                sys.stdout.flush()
                return None
                
        except Exception as e:
            print(f"[ERROR] Error getting courier rates: {str(e)}")
            traceback.print_exc()
            return None

