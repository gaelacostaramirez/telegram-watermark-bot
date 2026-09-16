import os
import io
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

TOKEN = os.environ["BOT_TOKEN"]

WATERMARK_TEXT = "777 PICKS"


async def procesar_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.channel_post

    if not mensaje or not mensaje.photo:
        return

    try:
        foto = mensaje.photo[-1]

        archivo = await context.bot.get_file(foto.file_id)

        contenido = io.BytesIO()
        await archivo.download_to_memory(contenido)
        contenido.seek(0)

        imagen = Image.open(contenido).convert("RGBA")

        capa = Image.new("RGBA", imagen.size, (0, 0, 0, 0))
        dibujo = ImageDraw.Draw(capa)

        try:
            fuente = ImageFont.truetype(
                "DejaVuSans-Bold.ttf",
                max(20, imagen.width // 30)
            )
        except:
            fuente = ImageFont.load_default()

        caja = dibujo.textbbox(
            (0, 0),
            WATERMARK_TEXT,
            font=fuente
        )

        ancho = caja[2] - caja[0]
        alto = caja[3] - caja[1]

        margen = max(20, imagen.width // 40)

        x = imagen.width - ancho - margen
        y = imagen.height - alto - margen

        dibujo.text(
            (x, y),
            WATERMARK_TEXT,
            font=fuente,
            fill=(255, 255, 255, 150),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 120)
        )

        resultado = Image.alpha_composite(imagen, capa)

        salida = io.BytesIO()

        resultado.convert("RGB").save(
            salida,
            format="JPEG",
            quality=95
        )

        salida.seek(0)

        caption = mensaje.caption or ""

        # Primero publicamos la imagen modificada
        # y solamente después eliminamos la original.
        nueva_publicacion = await context.bot.send_photo(
            chat_id=mensaje.chat_id,
            photo=salida,
            caption=caption
        )

        if nueva_publicacion:
            await context.bot.delete_message(
                chat_id=mensaje.chat_id,
                message_id=mensaje.message_id
            )

        print("Imagen procesada correctamente.")

    except Exception as error:
        print("ERROR:", error)


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot funcionando")

    def log_message(self, format, *args):
        return


def iniciar_servidor():
    puerto = int(os.environ.get("PORT", 10000))

    servidor = HTTPServer(
        ("0.0.0.0", puerto),
        HealthHandler
    )

    servidor.serve_forever()


def main():
    servidor = threading.Thread(
        target=iniciar_servidor,
        daemon=True
    )

    servidor.start()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.PHOTO,
            procesar_imagen
        )
    )

    print("Bot iniciado correctamente.")

    app.run_polling(
        allowed_updates=["channel_post"]
    )


if __name__ == "__main__":
    main()
