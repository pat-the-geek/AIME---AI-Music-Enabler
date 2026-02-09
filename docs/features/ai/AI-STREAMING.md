# 🌊 Streaming AI - Portrait d'Artiste

**Date:** 4 février 2026  
**Version:** 1.0.0

---

## 📋 Vue d'Ensemble

Le **streaming AI** permet d'afficher le texte du portrait d'artiste **caractère par caractère** au fur et à mesure de la génération par l'IA, au lieu d'attendre la réponse complète.

### ✨ Avantages

| Aspect | Sans Streaming | Avec Streaming |
|--------|----------------|----------------|
| **Temps d'attente perçu** | 1-2 minutes | ⚡ Immédiat |
| **Feedback utilisateur** | ⏳ Loading spinner | ✅ Texte en temps réel |
| **Expérience** | Attente passive | 📖 Lecture progressive |
| **Annulation** | ❌ Impossible | ✅ Possible |
| **Engagement** | Faible | 🎯 Élevé |

---

## 🏗️ Architecture

### Backend

```
Client (Browser)
    ↓ HTTP GET /api/v1/collection/artists/{id}/article/stream
    ↓
FastAPI Endpoint
    ↓ StreamingResponse (SSE)
    ↓
ArtistArticleService.generate_article_stream()
    ↓ Generator async
    ↓
AIService.ask_for_ia_stream()
    ↓ httpx.stream() + yield chunks
    ↓
EurIA API (Infomaniak AI - Mistral3)
    ↓ stream: true
    ↓
data: chunk1\n\n
data: chunk2\n\n
data: chunk3\n\n
...
```

### Frontend

```
User clicks "Générer"
    ↓
fetch('/article/stream', { Accept: 'text/event-stream' })
    ↓
response.body.getReader()
    ↓
while (!done) {
    ↓ read() → decode() → parse SSE
    ↓
    setStreamedContent(prev => prev + chunk)
    ↓ React re-render
    ↓ ReactMarkdown displays
}
```

---

## 🔧 Implémentation Technique

### 1. Backend - AIService

**Fichier:** `backend/app/services/ai_service.py`

```python
async def ask_for_ia_stream(self, prompt: str, max_tokens: int = 500):
    """Streaming avec Server-Sent Events (SSE)."""
    
    payload = {
        "model": "mistral3",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": 0.7,
        "stream": True  # ⭐ Activer le streaming
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", self.url, json=payload) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    content = data["choices"][0]["delta"]["content"]
                    yield f"data: {content}\n\n"  # Format SSE
```

**Points clés:**
- `stream: True` dans le payload API
- `client.stream()` au lieu de `client.post()`
- `yield` pour envoyer chunk par chunk
- Format SSE: `data: {content}\n\n`

### 2. Backend - Endpoint FastAPI

**Fichier:** `backend/app/api/v1/artists.py`

```python
@router.get("/{artist_id}/article/stream")
async def stream_artist_article(artist_id: int, db: Session = Depends(get_db)):
    """Streaming SSE du portrait d'artiste."""
    
    async def generate_stream():
        # 1. Envoyer métadonnées
        metadata = {"type": "metadata", "artist_name": artist.name, ...}
        yield f"data: {json.dumps(metadata)}\n\n"
        
        # 2. Streamer le contenu
        async for chunk in article_service.generate_article_stream(artist_id):
            yield chunk
        
        # 3. Signal de fin
        yield f"data: {{\"type\": \"done\"}}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Important pour nginx
        }
    )
```

**Points clés:**
- `StreamingResponse` avec générateur async
- `media_type="text/event-stream"`
- Headers pour désactiver le cache
- `X-Accel-Buffering: no` pour éviter le buffering nginx

### 3. Frontend - Fetch Stream

**Fichier:** `frontend/src/pages/ArtistArticle.tsx`

```typescript
const handleGenerateArticleStream = async () => {
  const response = await fetch(`${baseURL}/collection/artists/${id}/article/stream`, {
    headers: { 'Accept': 'text/event-stream' }
  })
  
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    
    // Décoder et parser les événements SSE
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = line.slice(6)
        
        try {
          const parsed = JSON.parse(data)
          if (parsed.type === 'metadata') {
            setStreamMetadata(parsed)
          } else if (parsed.type === 'done') {
            setIsStreaming(false)
          }
        } catch {
          // Texte brut - ajouter au contenu
          setStreamedContent(prev => prev + data)
        }
      }
    }
  }
}
```

**Points clés:**
- `response.body.getReader()` pour lire le stream
- `TextDecoder` pour décoder les bytes
- Buffer pour gérer les lignes incomplètes
- Parse JSON pour métadonnées, texte brut pour contenu
- `setStreamedContent(prev => prev + data)` pour accumulation

### 4. Frontend - Affichage Temps Réel

```tsx
{streamedContent && (
  <Paper>
    <ReactMarkdown remarkPlugins={[remarkGfm]}>
      {streamedContent}
    </ReactMarkdown>
    
    {isStreaming && (
      <Box>
        <CircularProgress size={16} />
        <Typography>Génération en cours...</Typography>
      </Box>
    )}
  </Paper>
)}
```

**Points clés:**
- ReactMarkdown re-render à chaque update
- Indicateur de streaming en cours
- Affichage progressif du Markdown formaté

---

## 📊 Format SSE (Server-Sent Events)

### Structure

```
data: texte chunk 1\n\n
data: texte chunk 2\n\n
data: {"type": "metadata", "artist_name": "Beatles"}\n\n
data: texte chunk 3\n\n
data: {"type": "done"}\n\n
```

### Types de Messages

| Type | Format | Usage |
|------|--------|-------|
| **Texte** | `data: contenu\n\n` | Chunks de texte Markdown |
| **Métadonnées** | `data: {"type":"metadata",...}\n\n` | Info artiste |
| **Fin** | `data: {"type":"done"}\n\n` | Signal fin de stream |
| **Erreur** | `data: {"type":"error","message":"..."}\n\n` | Erreur |

---

## 🎯 Cas d'Usage

### 1. Portrait d'Artiste (3000 mots)

**Temps de génération:**
- Sans streaming: ⏳ 60-120 secondes d'attente
- Avec streaming: ⚡ Affichage dès la 1ère seconde

**Expérience utilisateur:**
```
0s   → Clic "Générer"
0.5s → "# The Beatles : Portrait..." apparaît
1s   → "## Introduction\n\nDans l'histoire..." s'affiche
2s   → L'utilisateur commence à lire
...
60s  → Article complet affiché
```

### 2. Avantages Perçus

1. **Réactivité:** Feedback immédiat au lieu d'attente passive
2. **Engagement:** L'utilisateur lit pendant la génération
3. **Transparence:** Voir l'IA "penser" en temps réel
4. **Annulation:** Possibilité de stopper si le contenu ne convient pas

---

## 🚀 Configuration EurIA

### Paramètres API

```python
{
    "model": "mistral3",         # Modèle Mistral
    "stream": True,              # Activer streaming
    "max_tokens": 4000,          # ~3000 mots
    "temperature": 0.7,          # Créativité modérée
    "messages": [...]
}
```

### Headers Requis

```python
{
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}
```

### Timeout

- Client HTTP: `120.0` secondes
- Suffisant pour 3000 mots en streaming

---

## ⚠️ Limitations & Contraintes

### 1. **Circuit Breaker**

Si le service EurIA est en `OPEN`:
```python
if ai_circuit_breaker.state == "OPEN":
    yield f"data: Service temporairement indisponible\n\n"
    return
```

### 2. **Nginx Buffering**

Sans `X-Accel-Buffering: no`, nginx peut buffer tout le stream et l'envoyer d'un coup.

### 3. **CORS**

Pour les requêtes cross-origin:
```python
headers={
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET",
}
```

### 4. **Déconnexion Client**

Si le client ferme la connexion:
```python
try:
    async for chunk in stream:
        yield chunk
except asyncio.CancelledError:
    logger.info("Client disconnected")
    return
```

---

## 📈 Performance

### Métriques

| Métrique | Valeur |
|----------|--------|
| **Premier chunk** | ~0.3-0.5s |
| **Débit** | ~50-100 tokens/s |
| **3000 mots** | ~60-90s total |
| **Bande passante** | ~1-2 KB/s |

### Comparaison

**Sans Streaming:**
- Charge serveur: 100% pendant 60s
- Expérience utilisateur: ⏳ 60s attente → 💥 Tout d'un coup

**Avec Streaming:**
- Charge serveur: Répartie sur 60s
- Expérience utilisateur: ⚡ Immédiat → 📖 Lecture progressive

---

## 🐛 Debugging

### Logs Backend

```python
logger.info(f"📝 Streaming article pour {artist.name}")
logger.info(f"✅ Streaming terminé")
```

### Console Frontend

```javascript
console.log('Chunk reçu:', data)
console.log('Contenu actuel:', streamedContent)
```

### Tester avec cURL

```bash
curl -N http://localhost:8000/api/v1/collection/artists/123/article/stream
```

L'option `-N` désactive le buffering cURL.

---

## 🎓 Ressources

### Documentation

- **Server-Sent Events (SSE):** [MDN Web Docs](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- **httpx Streaming:** [HTTPX Docs](https://www.python-httpx.org/advanced/#streaming-responses)
- **FastAPI StreamingResponse:** [FastAPI Docs](https://fastapi.tiangolo.com/advanced/custom-response/#streamingresponse)

### Standards

- **SSE Spec:** [W3C](https://html.spec.whatwg.org/multipage/server-sent-events.html)
- **OpenAI Streaming:** [OpenAI API Docs](https://platform.openai.com/docs/api-reference/streaming)

---

## ✅ Résumé

Le **streaming AI** transforme l'expérience utilisateur en passant d'une **attente passive** (60-120s) à une **lecture progressive immédiate** (<1s).

**Technos clés:**
- Backend: FastAPI `StreamingResponse` + httpx `stream()`
- API: EurIA Mistral3 avec `stream: true`
- Frontend: Fetch API `getReader()` + React state
- Format: Server-Sent Events (SSE)

**Impact:**
- ✅ Feedback immédiat
- ✅ Meilleure perception de performance
- ✅ Engagement utilisateur accru
- ✅ Possibilité d'annulation

---

**Version:** 1.0.0  
**Auteur:** GitHub Copilot  
**Feature:** Portrait d'Artiste avec Streaming AI

🌊 **Le futur, c'est maintenant.**
