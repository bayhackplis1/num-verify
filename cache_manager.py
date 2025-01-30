from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import json
import hashlib
from pathlib import Path
import threading
import logging

class CacheManager:
    """
    Gestor de caché para resultados de análisis de números telefónicos.
    Implementa un sistema de caché multinivel con persistencia en disco.
    """
    
    def __init__(self, cache_dir: str = ".cache"):
        self._memory_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_dir = Path(cache_dir)
        self._cache_dir.mkdir(exist_ok=True)
        self._lock = threading.Lock()
        self._setup_logging()

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger("CacheManager")

    def get(self, key: str, max_age: Optional[timedelta] = None) -> Optional[Dict[str, Any]]:
        """
        Obtiene un resultado cacheado si existe y no ha expirado.
        
        Args:
            key: Clave única para el resultado (normalmente el número de teléfono hasheado)
            max_age: Tiempo máximo de validez del caché
            
        Returns:
            Dict con los resultados o None si no existe o expiró
        """
        try:
            # Primero buscar en memoria
            with self._lock:
                if key in self._memory_cache:
                    cached_data = self._memory_cache[key]
                    if self._is_cache_valid(cached_data, max_age):
                        self.logger.info(f"Cache hit (memory) for key: {key}")
                        return cached_data["data"]

            # Si no está en memoria, buscar en disco
            cache_file = self._get_cache_file_path(key)
            if cache_file.exists():
                cached_data = self._read_cache_file(cache_file)
                if cached_data and self._is_cache_valid(cached_data, max_age):
                    # Actualizar caché en memoria
                    with self._lock:
                        self._memory_cache[key] = cached_data
                    self.logger.info(f"Cache hit (disk) for key: {key}")
                    return cached_data["data"]

        except Exception as e:
            self.logger.error(f"Error retrieving from cache: {str(e)}")
        
        return None

    def set(self, key: str, data: Dict[str, Any], ttl: Optional[timedelta] = None) -> None:
        """
        Almacena un resultado en el caché.
        
        Args:
            key: Clave única para el resultado
            data: Datos a cachear
            ttl: Tiempo de vida del caché
        """
        try:
            cache_entry = {
                "timestamp": datetime.now().isoformat(),
                "ttl": ttl.total_seconds() if ttl else None,
                "data": data
            }

            # Actualizar caché en memoria
            with self._lock:
                self._memory_cache[key] = cache_entry

            # Persistir en disco
            cache_file = self._get_cache_file_path(key)
            self._write_cache_file(cache_file, cache_entry)
            
            self.logger.info(f"Successfully cached data for key: {key}")

        except Exception as e:
            self.logger.error(f"Error setting cache: {str(e)}")

    def invalidate(self, key: str) -> None:
        """Invalida una entrada específica del caché"""
        try:
            # Eliminar de memoria
            with self._lock:
                self._memory_cache.pop(key, None)

            # Eliminar de disco
            cache_file = self._get_cache_file_path(key)
            if cache_file.exists():
                cache_file.unlink()
            
            self.logger.info(f"Cache invalidated for key: {key}")

        except Exception as e:
            self.logger.error(f"Error invalidating cache: {str(e)}")

    def clear(self) -> None:
        """Limpia todo el caché"""
        try:
            # Limpiar memoria
            with self._lock:
                self._memory_cache.clear()

            # Limpiar disco
            for cache_file in self._cache_dir.glob("*.cache"):
                cache_file.unlink()
            
            self.logger.info("Cache cleared successfully")

        except Exception as e:
            self.logger.error(f"Error clearing cache: {str(e)}")

    def _get_cache_file_path(self, key: str) -> Path:
        """Genera la ruta del archivo de caché para una clave"""
        hashed_key = hashlib.sha256(key.encode()).hexdigest()
        return self._cache_dir / f"{hashed_key}.cache"

    def _is_cache_valid(self, cache_entry: Dict[str, Any], max_age: Optional[timedelta]) -> bool:
        """Verifica si una entrada de caché sigue siendo válida"""
        if not max_age:
            return True

        cached_time = datetime.fromisoformat(cache_entry["timestamp"])
        age = datetime.now() - cached_time
        
        if cache_entry["ttl"]:
            return age.total_seconds() < cache_entry["ttl"]
        
        return age < max_age

    def _read_cache_file(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """Lee una entrada de caché desde disco"""
        try:
            with cache_file.open('r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error reading cache file: {str(e)}")
            return None

    def _write_cache_file(self, cache_file: Path, data: Dict[str, Any]) -> None:
        """Escribe una entrada de caché a disco"""
        try:
            with cache_file.open('w') as f:
                json.dump(data, f)
        except Exception as e:
            self.logger.error(f"Error writing cache file: {str(e)}")

    def cleanup(self, max_age: Optional[timedelta] = None) -> None:
        """Limpia entradas de caché expiradas"""
        try:
            # Limpiar memoria
            with self._lock:
                for key in list(self._memory_cache.keys()):
                    if not self._is_cache_valid(self._memory_cache[key], max_age):
                        del self._memory_cache[key]

            # Limpiar disco
            for cache_file in self._cache_dir.glob("*.cache"):
                cached_data = self._read_cache_file(cache_file)
                if cached_data and not self._is_cache_valid(cached_data, max_age):
                    cache_file.unlink()
            
            self.logger.info("Cache cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during cache cleanup: {str(e)}")
