# Guide d'utilisation : Contrôle Roon et Playlists

## 🎵 Écouter sur Roon

Vous pouvez maintenant démarrer la lecture de n'importe quel morceau directement depuis AIME !

### Configuration initiale

1. **Activer Roon dans la configuration**
   - Ouvrez `config/app.json`
   - Vérifiez que `roon_control.enabled` est à `true`

2. **Sélectionner votre zone Roon**
   - Allez dans **Paramètres** (⚙️)
   - Section **🎛️ Contrôle Roon**
   - Sélectionnez la zone Roon où vous voulez que la musique soit jouée
   - La zone est sauvegardée automatiquement

### Utilisation

#### Dans le Journal d'Écoute
- Cliquez sur l'icône **▶️ Play** à côté du bouton ❤️
- Le morceau démarre immédiatement sur votre zone Roon

#### Dans la Timeline
- Même principe : cliquez sur **▶️** à côté de n'importe quel morceau
- Fonctionne en mode détaillé et compact

### Notifications
- ✅ **Succès** : "Lecture démarrée sur Roon"
- ❌ **Erreur** : Message d'erreur avec détails (ex: zone non sélectionnée)

---

## 📝 Créer des Playlists

Deux façons de créer des playlists :

### 1. Playlist Intelligente (IA)

Générée automatiquement selon un algorithme :

- **Top Sessions** : Pistes des sessions les plus longues
- **Corrélations Artistes** : Artistes écoutés ensemble
- **Flux d'Artistes** : Transitions naturelles entre artistes
- **Basé sur l'Heure** : Écoutes aux heures de pointe
- **Albums Complets** : Albums écoutés en entier
- **Redécouverte** : Pistes aimées mais oubliées
- **Généré par IA** : Sélection personnalisée par IA (nécessite un prompt)

**Comment faire :**
1. Allez dans **Playlists**
2. Cliquez sur **Créer une Playlist**
3. Sélectionnez "🤖 Intelligente (IA)"
4. Choisissez un algorithme
5. Définissez le nombre de tracks (10-100)
6. Cliquez sur **Créer**

### 2. Playlist Manuelle

Créez votre propre sélection de morceaux.

**Comment faire :**
1. Allez dans **Playlists**
2. Cliquez sur **Créer une Playlist**
3. Sélectionnez "✋ Manuelle"
4. Donnez un nom à votre playlist
5. *Note : Actuellement, vous devez ajouter des morceaux en notant leurs IDs*

**À venir** : Interface pour sélectionner des morceaux directement depuis le Journal ou la Timeline

---

## 🎛️ Configuration Roon

### Vérifier le statut
- Le backend vérifie automatiquement si Roon est activé et disponible
- Les boutons **▶️ Play** n'apparaissent que si Roon est accessible

### Zones multiples
Si vous avez plusieurs zones Roon :
1. Allez dans **Paramètres**
2. Section **🎛️ Contrôle Roon**
3. Sélectionnez la zone par défaut dans le menu déroulant

### Désactiver Roon
Pour désactiver temporairement les contrôles Roon :
1. Ouvrez `config/app.json`
2. Mettez `roon_control.enabled` à `false`
3. Redémarrez le backend

---

## 🐛 Dépannage

### "Aucune zone Roon sélectionnée"
→ Allez dans Paramètres et sélectionnez une zone

### Les boutons Play n'apparaissent pas
→ Vérifiez que :
- `roon_control.enabled = true` dans `config/app.json`
- Le backend est connecté au serveur Roon (voir Paramètres > Configuration Roon)
- L'extension AIME est autorisée dans Roon → Settings → Extensions

### "Erreur lors de la lecture sur Roon"
→ Vérifiez que :
- La zone Roon sélectionnée existe et est active
- Le serveur Roon Core est démarré
- Le morceau existe dans votre bibliothèque Roon

---

## 💡 Astuces

- **Écoute rapide** : Cliquez simplement sur ▶️ dans le Journal pour réécouter un morceau
- **Timeline** : Idéal pour retrouver ce que vous écoutiez à une heure précise et le rejouer
- **Playlists** : Utilisez les algorithmes IA pour découvrir des patterns dans vos écoutes
- **Zone persistante** : La zone sélectionnée est mémorisée même après fermeture du navigateur

---

## 📚 Documentation complète

Pour plus de détails techniques :
- **API Backend** : `docs/MIGRATION-ROON-PLAYLISTS.md`
- **Endpoints Roon** : `docs/API.md`
- **Architecture** : `docs/ARCHITECTURE.md`
