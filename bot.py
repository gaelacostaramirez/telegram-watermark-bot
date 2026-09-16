import os
import io
from PIL import Image, ImageEnhance
from telegram import Update
from telegram.ext import Application, MessageHandler, ContextTypes, filters

TOKEN = os.environ["BOT_TOKEN"]

# Texto que aparecerá como marca de agua.
# Más adelante lo podemos cambiar por tu logo.
WATERMARK_TEXT = "777 PICKS"


async def procesar_imagen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = update.channel_post

    if not mensaje or not mensaje.photo:
        return

    try:
        # Obtener la foto con mayor resolución
        foto = mensaje.photo[-1]

        archivo = await context.bot.get_file(foto.file_id)

        contenido = io.BytesIO()
        await archivo.download_to_memory(contenido)
        contenido.seek(0)

        # Abrir imagen
        imagen = Image.open(contenido).convert("RGBA")

        # Crear capa para la marca de agua
        capa = Image.new("RGBA", imagen.size, (0, 0, 0, 0))

        # Crear marca de agua de texto
        from PIL import ImageDraw, ImageFont

        dibujo = ImageDraw.Draw(capa)

        try:
            fuente = ImageFont.truetype("DejaVuSans-Bold.ttf", max(20, imagen.width // 30))
        except:
            fuente = ImageFont.load_default()

        # Tamaño del texto
        caja = dibujo.textbbox((0, 0), WATERMARK_TEXT, font=fuente)
        ancho = caja[2] - caja[0]
        alto = caja[3] - caja[1]

        # Posición: esquina inferior derecha
        margen = max(20, imagen.width // 40)

        x = imagen.width - ancho - margen
        y = imagen.height - alto - margen

        # Marca de agua semitransparente
        dibujo.text(
            (x, y),
            WATERMARK_TEXT,
            font=fuente,
            fill=(255, 255, 255, 150),
            stroke_width=2,
            stroke_fill=(0, 0, 0, 120)
        )

        # Combinar imagen y marca
        resultado = Image.alpha_composite(imagen, capa)

        # Convertir a JPEG
        salida = io.BytesIO()
        resultado.convert("RGB").save(
            salida,
            format="JPEG",
            quality=95
        )
        salida.seek(0)

        # Obtener caption original
        caption = mensaje.caption or ""

        # Eliminar publicación original
        await context.bot.delete_message(
            chat_id=mensaje.chat_id,
            message_id=mensaje.message_id
        )

        # Publicar imagen modificada
        await context.bot.send_photo(
            chat_id=mensaje.chat_id,
            photo=salida,
            caption=caption
        )

    except Exception as error:
        print("ERROR:", error)


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        MessageHandler(
            filters.UpdateType.CHANNEL_POST & filters.PHOTO,
            procesar_imagen
        )
    )

    print("Bot iniciado correctamente.")

    app.run_polling(
        allowed_updates=["channel_post"]
    )


if __name__ == "__main__":
    main()
