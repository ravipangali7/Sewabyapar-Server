"""
Shipdaak Logistics API Service
Handles all Shipdaak API interactions for warehouse and shipment management
"""
import requests
import logging
import re
import base64
import json
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ShipdaakService:
    """Service class for interacting with Shipdaak API"""
    
    def __init__(self):
        self.base_url = getattr(settings, 'SHIPDAAK_API_BASE_URL', '').rstrip('/')
        self.email = getattr(settings, 'SHIPDAAK_API_EMAIL', '')
        self.password = getattr(settings, 'SHIPDAAK_API_PASSWORD', '')
        self.token_cache_key = getattr(settings, 'SHIPDAAK_TOKEN_CACHE_KEY', 'shipdaak_access_token')
        self.token_expiry_cache_key = getattr(settings, 'SHIPDAAK_TOKEN_EXPIRY_CACHE_KEY', 'shipdaak_token_expiry')
        
        if not self.base_url:
            logger.warning("SHIPDAAK_API_BASE_URL not configured in settings")
        if not self.email or not self.password:
            logger.warning("SHIPDAAK_API_EMAIL or SHIPDAAK_API_PASSWORD not configured in settings")
    
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
                return datetime.fromtimestamp(exp, tz=timezone.utc)
            return None
        except Exception as e:
            logger.warning(f"Failed to decode JWT expiry: {str(e)}")
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
                logger.error(f"Shipdaak authentication failed: {data.get('error')}")
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
                        logger.info(f"Successfully obtained Shipdaak access token, expires at {expiry_datetime}")
                    else:
                        logger.warning("Token already expired, not caching")
                else:
                    # Fallback: cache for 12 hours if can't decode expiry
                    logger.warning("Could not decode JWT expiry, using 12 hour cache")
                    cache.set(self.token_cache_key, access_token, 60 * 60 * 12)
                    cache.set(self.token_expiry_cache_key, timezone.now() + timedelta(hours=12), 60 * 60 * 12)
                
                return access_token
            else:
                logger.error(f"Shipdaak token response missing access_token: {data}")
                # Clear cache on error
                cache.delete(self.token_cache_key)
                cache.delete(self.token_expiry_cache_key)
                return None
                
        except requests.exceptions.HTTPError as e:
            logger.error(f"Shipdaak token HTTP error: {e.response.status_code} - {e.response.text if hasattr(e, 'response') else str(e)}")
            cache.delete(self.token_cache_key)
            cache.delete(self.token_expiry_cache_key)
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get Shipdaak access token: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting Shipdaak access token: {str(e)}")
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
            logger.error("Cannot make request: No access token available")
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
                logger.error(f"Unsupported HTTP method: {method}")
                return None
            
            # Handle 401 Unauthorized - token might be expired
            if response.status_code == 401 and retry_on_401:
                logger.warning(f"Received 401 Unauthorized, clearing token cache and retrying once")
                # Clear cached token
                cache.delete(self.token_cache_key)
                cache.delete(self.token_expiry_cache_key)
                # Retry once with fresh token
                return self._make_request(method, endpoint, data, params, retry_on_401=False)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                logger.error(f"Shipdaak API authentication failed ({method} {endpoint}): 401 Unauthorized")
            else:
                logger.error(f"Shipdaak API HTTP error ({method} {endpoint}): {e.response.status_code} - {e.response.text if hasattr(e, 'response') else str(e)}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Shipdaak API request error ({method} {endpoint}): {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Shipdaak API request ({method} {endpoint}): {str(e)}")
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
            # Extract pincode from address (simple extraction - assumes pincode is at end)
            # You may need to adjust this based on your address format
            pincode = "110001"  # Default pincode
            address_lines = store.address.split('\n') if store.address else []
            for line in reversed(address_lines):
                # Try to find 6-digit number (Indian pincode format)
                pincode_match = re.search(r'\b\d{6}\b', line)
                if pincode_match:
                    pincode = pincode_match.group()
                    break
            
            # Prepare warehouse data
            warehouse_data = {
                "pickup_location": {
                    "warehouse_name": store.name,
                    "contact_name": store.owner.name if store.owner else "Store Owner",
                    "address_line_1": store.address or "Address not provided",
                    "address_line_2": "",
                    "pincode": pincode,
                    "phone": store.phone,
                    "gst_number": ""  # GST number not in store model, can be added later
                },
                "has_different_rto": False,  # Using same address for RTO
                "rto_location": {
                    "warehouse_name": f"{store.name} - RTO",
                    "contact_name": store.owner.name if store.owner else "Store Owner",
                    "address_line_1": store.address or "Address not provided",
                    "address_line_2": "",
                    "pincode": pincode,
                    "phone": store.phone,
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
                logger.error(f"Shipdaak warehouse creation failed: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Shipdaak warehouse for store {store.id}: {str(e)}", exc_info=True)
            return None
    
    def create_shipment(self, order) -> Optional[Dict[str, Any]]:
        """
        Create shipment in Shipdaak from order data
        
        Args:
            order: Order model instance
        
        Returns:
            Dict with shipment data (awb_number, shipment_id, label_url, etc.) or None if fails
        """
        try:
            store = order.merchant
            if not store:
                logger.error(f"Order {order.id} has no merchant/store")
                return None
            
            if not store.shipdaak_pickup_warehouse_id:
                logger.error(f"Store {store.id} has no Shipdaak warehouse ID")
                return None
            
            # Get courier configuration for this store
            courier_id = None
            courier_name = None
            try:
                courier_config = store.courier_config
                if courier_config and courier_config.is_active:
                    courier_id = courier_config.default_courier_id
                    courier_name = courier_config.default_courier_name
            except:
                pass  # No courier config, will use default or fail
            
            if not courier_id:
                logger.warning(f"No courier configured for store {store.id}, shipment creation may fail")
                # You might want to get a default courier or raise an error
            
            # Calculate weight from order items (default 500g if not available)
            # In real implementation, you might store weight per product
            weight = 500  # Default weight in grams
            total_items = sum(item.quantity for item in order.items.all())
            weight = max(500, total_items * 200)  # Rough estimate: 200g per item, minimum 500g
            
            # Get shipping address
            shipping_address = order.shipping_address
            if not shipping_address:
                logger.error(f"Order {order.id} has no shipping address")
                return None
            
            # Extract pincode from address
            pincode = shipping_address.zip_code if hasattr(shipping_address, 'zip_code') else "110001"
            
            # Prepare order items
            order_items = []
            for item in order.items.all():
                order_items.append({
                    "name": item.product.name,
                    "quantity": item.quantity,
                    "price": float(item.price),
                    "sku": f"SKU{item.product.id}"  # Using product ID as SKU if not available
                })
            
            # Map payment method
            pay_type = "cod" if order.payment_method == "cod" else "prepaid"
            
            # Calculate COD fee (typically 2% of order value for COD)
            cod_fee = 0
            if pay_type == "cod":
                cod_fee = float(order.total_amount) * 0.02  # 2% COD fee
            
            # Prepare shipment data
            shipment_data = {
                "order_no": order.order_number,
                "pay_type": pay_type,
                "weight": weight,
                "dimensions": {
                    "length": 40,  # Default dimensions in cm
                    "breadth": 30,
                    "height": 20
                },
                "shipping_fee": float(order.shipping_cost),
                "cod_fee": cod_fee,
                "discount_amount": 0,  # Can be calculated from coupons if needed
                "total_amount": float(order.total_amount),
                "courier": courier_id,
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
                    "phone": order.phone,
                    "shipping_gst_number": ""
                },
                "order_items": order_items
            }
            
            response = self._make_request('POST', '/v1/shipments/generate-shipment', data=shipment_data)
            
            if response and response.get('status') and response.get('data'):
                data = response['data']
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
                logger.error(f"Shipdaak shipment creation failed for order {order.id}: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating Shipdaak shipment for order {order.id}: {str(e)}", exc_info=True)
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
                logger.info(f"Successfully cancelled Shipdaak shipment {awb_number}")
                return True
            else:
                logger.error(f"Failed to cancel Shipdaak shipment {awb_number}: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Error cancelling Shipdaak shipment {awb_number}: {str(e)}", exc_info=True)
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
                logger.error(f"Failed to track Shipdaak shipment {awb_number}: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error tracking Shipdaak shipment {awb_number}: {str(e)}", exc_info=True)
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
                logger.error(f"Failed to get Shipdaak couriers: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting Shipdaak couriers: {str(e)}", exc_info=True)
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
                logger.error(f"Failed to generate bulk labels: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating bulk labels: {str(e)}", exc_info=True)
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
                logger.error(f"Failed to generate bulk manifest: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating bulk manifest: {str(e)}", exc_info=True)
            return None

