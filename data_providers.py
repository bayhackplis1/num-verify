from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import requests
import json
import logging
from datetime import datetime
import hashlib
import hmac
from enum import Enum
from dataclasses import dataclass

class DataProviderType(Enum):
    CARRIER = "carrier"
    FRAUD = "fraud"
    IDENTITY = "identity"
    LOCATION = "location"
    SOCIAL = "social"

@dataclass
class ProviderConfig:
    name: str
    base_url: str
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    timeout: int = 10
    rate_limit: int = 60

class DataProvider(ABC):
    """Clase base para proveedores de datos"""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._setup_logging()
        
    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(f"DataProvider.{self.config.name}")
        
    @abstractmethod
    async def get_data(self, phone_number: str) -> Dict[str, Any]:
        """Obtiene datos del proveedor"""
        pass
    
    def _generate_auth_headers(self) -> Dict[str, str]:
        """Genera headers de autenticación"""
        if not self.config.api_key:
            return {}
            
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "User-Agent": "PhoneAnalyzer/1.0",
            "Content-Type": "application/json"
        }
        
        if self.config.api_secret:
            timestamp = str(int(datetime.now().timestamp()))
            signature = self._generate_signature(timestamp)
            headers.update({
                "X-Timestamp": timestamp,
                "X-Signature": signature
            })
            
        return headers
        
    def _generate_signature(self, timestamp: str) -> str:
        """Genera firma HMAC para autenticación"""
        if not self.config.api_secret:
            return ""
            
        message = f"{self.config.api_key}{timestamp}"
        signature = hmac.new(
            self.config.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        )
        return signature.hexdigest()

class CarrierDataProvider(DataProvider):
    """Proveedor de datos de operadores móviles"""
    
    async def get_data(self, phone_number: str) -> Dict[str, Any]:
        try:
            headers = self._generate_auth_headers()
            response = requests.get(
                f"{self.config.base_url}/carrier/lookup",
                params={"phone": phone_number},
                headers=headers,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return self._process_carrier_data(response.json())
            else:
                self.logger.error(f"Error from carrier API: {response.status_code}")
                return self._get_fallback_data()
                
        except Exception as e:
            self.logger.error(f"Error getting carrier data: {str(e)}")
            return self._get_fallback_data()
            
    def _process_carrier_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa y normaliza datos del operador"""
        return {
            "carrier": {
                "name": raw_data.get("carrier_name"),
                "type": raw_data.get("carrier_type"),
                "country": raw_data.get("country_code"),
                "network": {
                    "mcc": raw_data.get("mcc"),
                    "mnc": raw_data.get("mnc"),
                    "technology": raw_data.get("network_type")
                }
            },
            "porting": {
                "is_ported": raw_data.get("ported", False),
                "original_carrier": raw_data.get("original_carrier"),
                "port_date": raw_data.get("port_date")
            },
            "status": {
                "active": raw_data.get("active", True),
                "roaming": raw_data.get("roaming", False),
                "last_seen": raw_data.get("last_seen")
            }
        }
        
    def _get_fallback_data(self) -> Dict[str, Any]:
        """Datos por defecto cuando falla la API"""
        return {
            "carrier": {
                "name": "Unknown",
                "type": "Unknown",
                "country": "Unknown"
            },
            "status": {
                "active": True,
                "verified": False
            }
        }

class FraudDetectionProvider(DataProvider):
    """Proveedor de datos de detección de fraude"""
    
    async def get_data(self, phone_number: str) -> Dict[str, Any]:
        try:
            headers = self._generate_auth_headers()
            response = requests.post(
                f"{self.config.base_url}/fraud/check",
                json={"phone_number": phone_number},
                headers=headers,
                timeout=self.config.timeout
            )
            
            if response.status_code == 200:
                return self._process_fraud_data(response.json())
            else:
                self.logger.error(f"Error from fraud API: {response.status_code}")
                return self._get_fallback_data()
                
        except Exception as e:
            self.logger.error(f"Error checking fraud: {str(e)}")
            return self._get_fallback_data()
            
    def _process_fraud_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa datos de fraude"""
        return {
            "risk_score": raw_data.get("risk_score", 0),
            "risk_level": raw_data.get("risk_level", "unknown"),
            "fraud_indicators": raw_data.get("indicators", []),
            "spam_reports": raw_data.get("spam_reports", 0),
            "blacklist_status": raw_data.get("blacklisted", False),
            "verification": {
                "verified": raw_data.get("verified", False),
                "method": raw_data.get("verification_method"),
                "date": raw_data.get("verification_date")
            }
        }
        
    def _get_fallback_data(self) -> Dict[str, Any]:
        return {
            "risk_score": 0,
            "risk_level": "unknown",
            "fraud_indicators": [],
            "verification": {
                "verified": False
            }
        }

class DataProviderFactory:
    """Fábrica para crear instancias de proveedores de datos"""
    
    @staticmethod
    def create_provider(provider_type: DataProviderType, config: ProviderConfig) -> DataProvider:
        providers = {
            DataProviderType.CARRIER: CarrierDataProvider,
            DataProviderType.FRAUD: FraudDetectionProvider
        }
        
        provider_class = providers.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {provider_type}")
            
        return provider_class(config)

class DataAggregator:
    """Agregador de datos de múltiples proveedores"""
    
    def __init__(self):
        self.providers: Dict[DataProviderType, DataProvider] = {}
        self._setup_logging()
        
    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("DataAggregator")
        
    def add_provider(self, provider_type: DataProviderType, provider: DataProvider) -> None:
        """Añade un proveedor de datos"""
        self.providers[provider_type] = provider
        
    async def get_aggregated_data(self, phone_number: str) -> Dict[str, Any]:
        """Obtiene y agrega datos de todos los proveedores"""
        results = {}
        
        for provider_type, provider in self.providers.items():
            try:
                data = await provider.get_data(phone_number)
                results[provider_type.value] = data
            except Exception as e:
                self.logger.error(f"Error getting data from {provider_type.value}: {str(e)}")
                results[provider_type.value] = {"error": str(e)}
                
        return self._merge_results(results)
        
    def _merge_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Combina resultados de diferentes proveedores"""
        merged = {
            "carrier_info": results.get("carrier", {}),
            "fraud_detection": results.get("fraud", {}),
            "identity_verification": results.get("identity", {}),
            "location_data": results.get("location", {}),
            "social_presence": results.get("social", {}),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "providers": list(self.providers.keys())
            }
        }
        
        return merged
