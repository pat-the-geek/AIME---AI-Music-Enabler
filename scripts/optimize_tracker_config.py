#!/usr/bin/env python3
"""Optimiser la configuration du tracker avec l'IA Euria."""
import requests
import json

# Configuration Euria
url = "https://api.euria.fr/v1/chat/completion"
bearer = "sk-b9fcc8ad-42f4-4bdd-8476-ae28c79829c5"

prompt = """En tant qu'expert en tracking de musique et optimisation de systèmes, analyse cette situation :

**Contexte** : Application de suivi d'écoute musicale connectée à Last.fm
**Données actuelles** :
- 200 écoutes historiques enregistrées
- Intervalle de polling : 120 secondes (2 minutes)
- Plage horaire : 6h-23h (17h d'activité)
- Utilisateur typique : écoute active de musique pendant la journée

**Question** : Quelle est la configuration optimale pour maximiser la capture d'écoutes tout en minimisant les appels API ?

Analyse les aspects suivants :
1. **Fréquence de polling optimale** : Balance entre réactivité et charge API (Last.fm recommande max 5 req/sec)
2. **Plage horaire intelligente** : Basée sur les habitudes d'écoute moyennes (travail, loisirs)
3. **Stratégie adaptative** : Ajustements selon les patterns détectés

Réponds au format JSON suivant :
{
  "interval_seconds": <valeur optimale entre 60 et 300>,
  "listen_start_hour": <heure de début 0-23>,
  "listen_end_hour": <heure de fin 0-23>,
  "reasoning": "<explication détaillée de 3-4 phrases>",
  "alternative_strategy": "<suggestion avancée optionnelle pour améliorer le système>"
}"""

headers = {
    "Authorization": f"Bearer {bearer}",
    "Content-Type": "application/json"
}

payload = {
    "model": "gpt-4o-2024-08-06",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.3,
    "max_tokens": 600
}

try:
    print("🤖 Consultation de l'IA Euria pour optimiser la configuration...\n")
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    content = result['choices'][0]['message']['content']
    
    # Extraire le JSON de la réponse
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0].strip()
    elif '```' in content:
        content = content.split('```')[1].split('```')[0].strip()
    
    config = json.loads(content)
    
    print("✅ Configuration optimale recommandée par l'IA :\n")
    print(f"🔄 Intervalle de polling : {config['interval_seconds']} secondes ({config['interval_seconds']/60:.1f} minutes)")
    print(f"🕐 Plage horaire : {config['listen_start_hour']}h - {config['listen_end_hour']}h")
    print(f"\n📊 Raisonnement :")
    print(f"   {config['reasoning']}")
    
    if 'alternative_strategy' in config and config['alternative_strategy']:
        print(f"\n💡 Stratégie avancée suggérée :")
        print(f"   {config['alternative_strategy']}")
    
    print(f"\n📝 Configuration JSON complète :")
    print(json.dumps(config, indent=2, ensure_ascii=False))
    
except Exception as e:
    print(f"❌ Erreur : {str(e)}")
    import traceback
    traceback.print_exc()
