"""Harici servis entegrasyonları (Hafta 9: harita/rota API).

Bu katman yalnızca dış servisle konuşur: isteği hazırlar, gönderir, yanıtı
ayrıştırır ve hataları tek bir hata türüne çevirir. İş kuralı (rota alınamazsa
ne yapılacağı, önbellek, yetki) iş katmanındadır: backend/services/rota_servisi.py
"""
