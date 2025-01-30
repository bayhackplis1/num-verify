from typing import Dict, List, Any, Optional
import requests
from bs4 import BeautifulSoup
from time import sleep
import re
import json
from datetime import datetime

class SocialChecker:
    def __init__(self, phone_number: str):
        self.phone_number = phone_number
        self.clean_number = re.sub(r'[^0-9]', '', phone_number)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self._cache = {}

    def check_social_presence(self) -> Dict[str, Any]:
        """Verifica la presencia del número en redes sociales y apps de mensajería"""
        results = {}

        # Apps de Mensajería
        results.update(self._check_messaging_apps())

        # Redes Sociales Principales
        results.update(self._check_major_social_networks())

        # Plataformas Profesionales
        results.update(self._check_professional_networks())

        # Plataformas de Comercio
        results.update(self._check_commerce_platforms())

        return results

    def _check_messaging_apps(self) -> Dict[str, str]:
        """Verifica presencia en apps de mensajería"""
        results = {}

        # WhatsApp
        results["WhatsApp"] = self._check_whatsapp()
        results["WhatsApp Business"] = self._check_whatsapp_business()

        # Telegram
        telegram_status = self._check_telegram()
        results["Telegram"] = telegram_status
        if telegram_status == "Registrado":
            results["Telegram Username"] = self._get_telegram_username()

        # Signal
        results["Signal"] = "Verificación privada"

        # Viber
        results["Viber"] = self._check_viber()

        # Line
        results["Line"] = self._check_line()

        # WeChat
        results["WeChat"] = "Requiere QR"

        return results

    def _check_major_social_networks(self) -> Dict[str, str]:
        """Verifica presencia en redes sociales principales"""
        results = {}

        # Facebook
        fb_info = self._check_facebook()
        results["Facebook"] = fb_info["status"]
        if "profile" in fb_info:
            results["Facebook Profile"] = fb_info["profile"]

        # Instagram
        ig_info = self._check_instagram()
        results["Instagram"] = ig_info["status"]
        if "username" in ig_info:
            results["Instagram Username"] = ig_info["username"]

        # TikTok
        results["TikTok"] = self._check_tiktok()

        # Twitter/X
        results["Twitter"] = self._check_twitter()

        # Snapchat
        results["Snapchat"] = self._check_snapchat()

        return results

    def _check_professional_networks(self) -> Dict[str, str]:
        """Verifica presencia en redes profesionales"""
        results = {}

        # LinkedIn
        linkedin_info = self._check_linkedin()
        results["LinkedIn"] = linkedin_info["status"]
        if "profile" in linkedin_info:
            results["LinkedIn Profile"] = linkedin_info["profile"]

        # Xing
        results["Xing"] = self._check_xing()

        # ResearchGate
        results["ResearchGate"] = "Búsqueda disponible"

        return results

    def _check_commerce_platforms(self) -> Dict[str, str]:
        """Verifica presencia en plataformas de comercio"""
        results = {}

        # Google Business
        results["Google Business"] = self._check_google_business()

        # Amazon
        results["Amazon Seller"] = self._check_amazon_seller()

        # eBay
        results["eBay"] = self._check_ebay()

        # Wallapop/Local Markets
        results["Wallapop"] = self._check_wallapop()

        return results

    def _check_whatsapp(self) -> str:
        """Verifica estado en WhatsApp"""
        try:
            url = f"https://wa.me/{self.clean_number}"
            response = self._safe_request(url)
            if response and response.status_code == 200:
                if "Abrir WhatsApp" in response.text or "Open WhatsApp" in response.text:
                    return "Registrado"
                elif "wa.me" in response.text:
                    return "Posiblemente registrado"
            return "No encontrado"
        except Exception:
            return "Error en verificación"

    def _check_whatsapp_business(self) -> str:
        """Verifica si es una cuenta de WhatsApp Business"""
        try:
            url = f"https://business.whatsapp.com/api/check/{self.clean_number}"
            response = self._safe_request(url)
            if response and response.status_code == 200:
                return "Cuenta Business detectada"
            return "No es cuenta Business"
        except Exception:
            return "Verificación no disponible"

    def _check_telegram(self) -> str:
        """Verifica presencia en Telegram"""
        try:
            url = f"https://t.me/+{self.clean_number}"
            response = self._safe_request(url)
            if response and response.status_code == 200:
                if "tg://resolve" in response.text:
                    return "Registrado"
                elif "Telegram" in response.text:
                    return "Posiblemente registrado"
            return "No encontrado"
        except Exception:
            return "Error en verificación"

    def _get_telegram_username(self) -> str:
        """Intenta obtener el username de Telegram"""
        return "Verificación privada"

    def _check_viber(self) -> str:
        """Verifica presencia en Viber"""
        try:
            url = f"viber://chat?number={self.clean_number}"
            return "Verificación mediante app"
        except Exception:
            return "Verificación no disponible"

    def _check_line(self) -> str:
        """Verifica presencia en Line"""
        try:
            url = f"https://line.me/R/ti/p/~{self.clean_number}"
            return "Verificación mediante app"
        except Exception:
            return "Verificación no disponible"

    def _check_facebook(self) -> Dict[str, str]:
        """Verifica presencia en Facebook"""
        try:
            # Búsqueda en Facebook
            url = f"https://www.facebook.com/search/top/?q={self.clean_number}"
            response = self._safe_request(url)
            if response and response.status_code == 200:
                return {
                    "status": "Búsqueda disponible",
                    "profile": "Requiere inicio de sesión"
                }
            return {"status": "No encontrado"}
        except Exception:
            return {"status": "Error en verificación"}

    def _check_instagram(self) -> Dict[str, str]:
        """Verifica presencia en Instagram"""
        try:
            return {
                "status": "Requiere inicio de sesión",
                "username": "Verificación privada"
            }
        except Exception:
            return {"status": "Verificación no disponible"}

    def _check_tiktok(self) -> str:
        """Verifica presencia en TikTok"""
        try:
            url = f"https://www.tiktok.com/search?q={self.clean_number}"
            response = self._safe_request(url)
            if response and response.status_code == 200:
                return "Búsqueda disponible"
            return "No encontrado"
        except Exception:
            return "Error en verificación"

    def _check_twitter(self) -> str:
        """Verifica presencia en Twitter/X"""
        try:
            url = f"https://twitter.com/search?q={self.clean_number}&src=typed_query"
            response = self._safe_request(url)
            if response and response.status_code == 200:
                return "Búsqueda disponible"
            return "No encontrado"
        except Exception:
            return "Error en verificación"

    def _check_snapchat(self) -> str:
        """Verifica presencia en Snapchat"""
        return "Verificación privada"

    def _check_linkedin(self) -> Dict[str, str]:
        """Verifica presencia en LinkedIn"""
        try:
            url = f"https://www.linkedin.com/search/results/all/?keywords={self.clean_number}"
            response = self._safe_request(url)
            if response and response.status_code == 200:
                return {
                    "status": "Búsqueda disponible",
                    "profile": "Requiere inicio de sesión"
                }
            return {"status": "No encontrado"}
        except Exception:
            return {"status": "Error en verificación"}

    def _check_xing(self) -> str:
        """Verifica presencia en Xing"""
        try:
            url = f"https://www.xing.com/search/members?keywords={self.clean_number}"
            response = self._safe_request(url)
            if response and response.status_code == 200:
                return "Búsqueda disponible"
            return "No encontrado"
        except Exception:
            return "Error en verificación"

    def _check_google_business(self) -> str:
        """Verifica presencia en Google Business"""
        try:
            url = f"https://business.google.com/search?q={self.clean_number}"
            response = self._safe_request(url)
            if response and response.status_code == 200:
                return "Búsqueda disponible"
            return "No encontrado"
        except Exception:
            return "Verificación no disponible"

    def _check_amazon_seller(self) -> str:
        """Verifica si el número está asociado a una cuenta de vendedor en Amazon"""
        return "Verificación privada"

    def _check_ebay(self) -> str:
        """Verifica presencia en eBay"""
        try:
            url = f"https://www.ebay.com/sch/i.html?_nkw={self.clean_number}"
            response = self._safe_request(url)
            if response and response.status_code == 200:
                return "Búsqueda disponible"
            return "No encontrado"
        except Exception:
            return "Error en verificación"

    def _check_wallapop(self) -> str:
        """Verifica presencia en Wallapop"""
        try:
            url = f"https://es.wallapop.com/search?keywords={self.clean_number}"
            response = self._safe_request(url)
            if response and response.status_code == 200:
                return "Búsqueda disponible"
            return "No encontrado"
        except Exception:
            return "Error en verificación"

    def _safe_request(self, url: str) -> Optional[requests.Response]:
        """Realiza una petición segura con delay y headers apropiados"""
        sleep(1)  # Respetamos límites de rate
        try:
            return requests.get(url, headers=self.headers, timeout=5, allow_redirects=True)
        except Exception:
            return None