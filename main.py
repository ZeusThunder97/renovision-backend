# Imports standard en premier
import io
import os

# Imports tiers ensuite
import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY")

# Créer l'application FastAPI avec métadonnées pour la production
app = FastAPI(
    title="RenoVision AI Backend",
    description="API pour la transformation d'images d'intérieur avec l'IA",
    version="1.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc"  # ReDoc
)

# Activer CORS pour tous les domaines (utile pour tests mobiles)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "RenoVision AI Backend opérationnel ✅", "version": "1.0.0"}

@app.get("/health")
def health_check():
    """Endpoint pour tester la connectivité depuis l'app mobile"""
    # Vérifier si la clé API est configurée
    api_status = "✅ API Key configurée" if STABILITY_API_KEY else "❌ API Key manquante"
    
    return {
        "status": "ok", 
        "message": "RenoVision AI Backend is running",
        "version": "1.0.0",
        "stability_api": api_status,
        "endpoints": ["/", "/health", "/transform", "/docs"],
        "environment": os.getenv("ENVIRONMENT", "development")
    }

@app.post("/transform")
async def transform(
    style: str = Form(...),
    room: str = Form(...),
    description: str = Form(""),  # facultatif
    image: UploadFile = File(...)
):
    try:
        print(f"🎨 Transformation demandée:")
        print(f"   Style: {style}")
        print(f"   Pièce: {room}")
        print(f"   Description: {description}")
        print(f"   Image: {image.filename}")
        
        # Vérifier la clé API dès le début
        if not STABILITY_API_KEY:
            print("❌ STABILITY_API_KEY manquante")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error", 
                    "message": "Configuration serveur incomplète - STABILITY_API_KEY manquante"
                }
            )
        
        # Lire et convertir l'image
        image_bytes = await image.read()
        pil_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

        # Redimensionner si nécessaire (à 1024x1024)
        width, height = pil_image.size
        print(f"   Taille originale: {width}x{height}")
        
        if width != 1024 or height != 1024:
            pil_image = pil_image.resize((1024, 1024))
            print(f"   Redimensionnée à: 1024x1024")

        # Convertir l'image en PNG (binaire)
        buffer = io.BytesIO()
        pil_image.save(buffer, format="PNG")
        buffer.seek(0)
        final_image_bytes = buffer.read()

        # Créer le prompt
        prompt = f"{style} style for a {room}, same layout, photorealistic, high quality"
        if description.strip():
            prompt += f", {description.strip()}"
        
        print(f"   Prompt final: {prompt}")
        print("🚀 Envoi vers Stability AI...")
        
        # Appel à Stability AI avec timeout
        response = requests.post(
            "https://api.stability.ai/v2beta/stable-image/control/structure",
            headers={
                "authorization": f"Bearer {STABILITY_API_KEY}",
                "accept": "application/json"
            },
            files={"image": ("image.png", final_image_bytes, "image/png")},
            data={
                "prompt": prompt,
                "control_strength": 0.35,
                "structure_type": "canny",
                "output_format": "png"
            },
            timeout=120  # Timeout de 2 minutes pour les gros traitements
        )

        print(f"📡 Réponse Stability AI: {response.status_code}")

        # Réponse OK
        if response.status_code == 200:
            print("✅ Transformation réussie!")
            return {
                "status": "ok",
                "prompt": prompt,
                "image_base64": response.json()["image"]
            }
        else:
            # Erreur côté Stability
            print(f"❌ Erreur Stability AI: {response.text}")
            return JSONResponse(
                status_code=response.status_code,
                content={
                    "status": "error", 
                    "message": "Erreur lors de la transformation",
                    "details": response.text
                }
            )

    except requests.exceptions.Timeout:
        print("⏰ Timeout lors de l'appel à Stability AI")
        return JSONResponse(
            status_code=504,
            content={
                "status": "error",
                "message": "La transformation a pris trop de temps. Réessayez avec une image plus petite."
            }
        )
    except Exception as e:
        print(f"💥 Erreur serveur: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error", 
                "message": f"Erreur serveur: {str(e)}"
            }
        )

# Point d'entrée pour le déploiement
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print(f"🚀 Démarrage du serveur sur le port {port}")
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=port,
        log_level="info"
    )
    # Ajoutez ces lignes à la fin de votre main.py
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

    if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)